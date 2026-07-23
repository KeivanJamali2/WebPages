"""Flask multi-room Persian yes/no word guessing game.

Features (initial implementation):
 - Lobby with 5 predefined rooms (some can have passwords)
 - Join room with player name + password (if required)
 - Start game in a room (first player or any player if not started)
 - Specify question limit (shared pool) when starting
 - Ask yes/no questions answered by LLM (boolean returned)
 - Make final guess after questions exhausted (or earlier if allowed)
 - Game state polling via JSON endpoint for dynamic front-end updates
 - Prevent joining room once a game has started (until reset)

Future improvements (possible next steps):
 - WebSocket / Socket.IO real-time updates
 - Persistence (Redis / DB) for room states
 - Multiple concurrent games per room / queueing
 - Spectator mode
 - More elaborate turn-taking rules

NOTE: This file creates templates & static assets expectation:
  templates/
	layout.html, index.html, room.html
  static/
	css/style.css
	js/lobby.js
	js/room.js
Those will be added in subsequent steps.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

import os
import secrets
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from queue import SimpleQueue
import threading
import json
from logger_utils import (
	log_player_join,
	generate_game_id,
	GameFileBundle,
	log_question,
	log_guess,
	log_chat,
)

from flask import (
	Flask, render_template, request, redirect, url_for, session, jsonify, flash, abort
)
from flask import send_from_directory
"""Socket.IO removed for deployment environment lacking websocket support.
State updates now delivered by client polling /state and existing REST endpoints.
"""

# Single-round legacy logic removed; only multi-round game is supported now
import time


# ----------------------------------------------------------------------------------
# New multi-round game with chat phase
# ----------------------------------------------------------------------------------

class MultiRoundYesNoGame:
	"""Multi-round yes/no guessing game with an inter-round chat phase.

	Phases per round (except after final win/loss):
	  QUESTION -> GUESS -> (if no winner) CHAT -> next round QUESTION

	Configuration (per game start):
	  - max_rounds: total number of rounds
	  - questions_per_player: questions each player may ask per round
	  - guesses_per_player: guesses each player may make per round (default 1)
	  - chat_duration_sec: maximum chat time between rounds (can be skipped early if all ready)

	Chat phase: players can exchange free-form messages (not exposing the secret)
	and then press "ready". When all players are ready OR the timer expires the
	next round auto-starts. The target word remains the same across all rounds.
	"""

	class Phase:
		QUESTION = "QUESTION"
		GUESS = "GUESS"
		CHAT = "CHAT"
		COMPLETED = "COMPLETED"

	def __init__(self, *, players, word_picker, questions_per_player: int, guesses_per_player: int,
				 max_rounds: int, chat_duration_sec: int):
		if len(players) < 2:
			raise ValueError("حداقل دو بازیکن لازم است")
		self.players = list(players)
		self.word, self.description = word_picker()
		self.questions_per_player = max(1, questions_per_player)
		self.guesses_per_player = max(1, guesses_per_player)
		self.max_rounds = max(1, max_rounds)
		self.chat_duration_sec = max(5, chat_duration_sec)  # minimum 5 seconds
		self.round = 1
		self.phase = self.Phase.QUESTION
		# Per-round counters
		self.questions_used = {p: 0 for p in self.players}
		self.guesses_used = {p: 0 for p in self.players}
		self.winner = None
		self.is_over = False
		# Chat support
		self.chat_deadline: float | None = None
		self.ready_players: set[str] = set()
		self.chat_log: list[dict] = []  # {player, msg, ts}
		# Per-player private histories (not broadcast) each entry: {round, phase, question/guess, answer/correct, ts}
		self._question_history: dict[str, list[dict]] = {p: [] for p in self.players}
		self._guess_history: dict[str, list[dict]] = {p: [] for p in self.players}

	# ---------------- Internal helpers ----------------
	def _all_questions_done(self):
		return all(self.questions_used[p] >= self.questions_per_player for p in self.players)

	def _all_guesses_done(self):
		return all(self.guesses_used[p] >= self.guesses_per_player for p in self.players)

	def _enter_chat(self):
		if self.round >= self.max_rounds:
			# No further rounds; game ends without winner
			self.phase = self.Phase.COMPLETED
			self.is_over = True
			return
		self.phase = self.Phase.CHAT
		self.chat_deadline = time.time() + self.chat_duration_sec
		self.ready_players.clear()

	def _start_next_round(self):
		self.round += 1
		# reset per-round counters
		self.questions_used = {p: 0 for p in self.players}
		self.guesses_used = {p: 0 for p in self.players}
		self.phase = self.Phase.QUESTION
		self.chat_deadline = None
		self.ready_players.clear()

	# ---------------- Public API ----------------
	def ask(self, player: str, question: str, answer_fn) -> bool:
		if self.is_over:
			raise ValueError("بازی تمام شده است")
		if self.phase != self.Phase.QUESTION:
			raise ValueError("الان نوبت پرسیدن سوال نیست")
		if player not in self.players:
			raise ValueError("بازیکن ناشناس")
		if self.questions_used[player] >= self.questions_per_player:
			raise ValueError("سهم سوالات این دور برای شما تمام شده است")
		raw = answer_fn(question, {self.word: self.description})
		ans_bool = self._coerce_bool(raw)
		self.questions_used[player] += 1
		self._question_history[player].append({
			"round": self.round,
			"phase": self.phase,
			"question": question[:160],
			"answer": ans_bool,
			"ts": int(time.time())
		})
		if self._all_questions_done():
			# Move automatically to guess phase
			self.phase = self.Phase.GUESS
			# Edge case: players may have already used all their guesses early (allowed during QUESTION).
			# If so, we must advance immediately to CHAT (or game completion) instead of getting stuck in GUESS.
			if self._all_guesses_done() and not self.winner:
				self._enter_chat()
		return ans_bool

	def guess(self, player: str, guess_word: str) -> bool:
		if self.is_over:
			raise ValueError("بازی تمام شده است")
		if player not in self.players:
			raise ValueError("بازیکن ناشناس")
		if self.phase not in (self.Phase.GUESS, self.Phase.QUESTION):
			raise ValueError("در این فاز اجازه حدس نیست")
		if self.guesses_used[player] >= self.guesses_per_player:
			raise ValueError("سهم حدس شما تمام شده است")
		self.guesses_used[player] += 1
		correct = guess_word.strip().lower() == self.word.lower()
		self._guess_history[player].append({
			"round": self.round,
			"phase": self.phase,
			"guess": guess_word[:100],
			"correct": correct,
			"ts": int(time.time())
		})
		if correct:
			self.winner = player
			self.is_over = True
			self.phase = self.Phase.COMPLETED
		else:
			# If in QUESTION phase an early wrong guess does not change phase.
			if self.phase == self.Phase.GUESS and self._all_guesses_done() and not self.winner:
				# End round -> go to chat phase before next round
				self._enter_chat()
		return correct

	def tick_chat(self):
		"""Check if chat timer expired and advance to next round if so."""
		if self.phase != self.Phase.CHAT or self.is_over:
			return False
		if self.chat_deadline and time.time() >= self.chat_deadline:
			self._start_next_round()
			return True
		return False

	def player_ready(self, player: str):
		if self.phase != self.Phase.CHAT or self.is_over:
			return False
		if player not in self.players:
			return False
		self.ready_players.add(player)
		if len(self.ready_players) == len(self.players):
			# All ready -> next round
			self._start_next_round()
			return True
		return False

	def add_chat_message(self, player: str, msg: str):
		if self.phase != self.Phase.CHAT:
			raise ValueError("الان در فاز گفتگو نیستید")
		if player not in self.players:
			raise ValueError("بازیکن ناشناس")
		msg = msg.strip()
		if not msg:
			raise ValueError("پیام خالی است")
		entry = {"player": player, "msg": msg, "ts": int(time.time())}
		self.chat_log.append(entry)
		return entry

	def summary(self):  # mimic SimpleWordGuessGame interface for front-end
		return {
			"round": self.round,
			"phase": self.phase,
			"winner": self.winner,
			"is_over": self.is_over,
			"limits": {
				"questions_per_player": self.questions_per_player,
				"guesses_per_player": self.guesses_per_player,
			},
			"players": {
				p: {
					"questions_used": self.questions_used[p],
					"questions_left": max(0, self.questions_per_player - self.questions_used[p]),
					"guesses_used": self.guesses_used[p],
					"guesses_left": max(0, self.guesses_per_player - self.guesses_used[p]),
				} for p in self.players
			},
			"chat_deadline": int(self.chat_deadline) if self.chat_deadline else None,
			"ready_players": list(self.ready_players),
			"chat_log": self.chat_log[-30:],  # last 30 messages
		}

	def personal_history(self, player: str) -> dict:
		"""Return the private history (questions & guesses) for a player.

		Structure:
		{
		  'questions': [...],
		  'guesses': [...]
		}
		"""
		return {
			"questions": list(self._question_history.get(player, []))[-100:],
			"guesses": list(self._guess_history.get(player, []))[-100:]
		}

	@staticmethod
	def _coerce_bool(value):
		if isinstance(value, bool):
			return value
		if isinstance(value, (int, float)):
			return bool(value)
		if isinstance(value, str):
			v = value.strip().lower()
			if v in {"yes", "true", "1", "y", "بله", "درست"}:
				return True
			if v in {"no", "false", "0", "n", "خیر", "غلط"}:
				return False
		return False



# ----------------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", secrets.token_hex(16))  # for session

MAX_ROOMS = 5
INACTIVITY_TIMEOUT = int(os.getenv("INACTIVITY_TIMEOUT", "120"))  # seconds idle before auto-removal (legacy immediate removal)
INACTIVITY_SWEEP_INTERVAL = 15  # seconds between idle scans
# --- Suspension (grace reconnect) strategy ---
# Instead of removing a player immediately at INACTIVITY_TIMEOUT we now:
#   1. Mark as 'suspended' after SUSPEND_TRIGGER_SECONDS (default 15s) of no heartbeat.
#   2. Show a countdown (suspend_deadline) = last_seen + SUSPEND_GRACE_SECONDS (default equals INACTIVITY_TIMEOUT => 120s total window).
#   3. If player returns before deadline: suspension cleared and game continues seamlessly.
#   4. If deadline passes: player removed; any running game resets with reason 'suspend_timeout'.
SUSPEND_TRIGGER_SECONDS = int(os.getenv("SUSPEND_TRIGGER_SECONDS", "15"))  # when to visually suspend
SUSPEND_GRACE_SECONDS = int(os.getenv("SUSPEND_GRACE_SECONDS", str(INACTIVITY_TIMEOUT)))  # full grace window from last_seen

# Inactivity handling:
#  * Frontend periodically calls /ping/<room_id> while tab visible.
#  * Any request referencing a room also refreshes player's last_seen.
#  * When a player exceeds INACTIVITY_TIMEOUT:
#       - If a game is running, it's reset (broadcast 'reset').
#       - Player removed (broadcast 'leave'). Slot becomes free.


@dataclass
class Player:
	name: str
	joined_at: int
	last_seen: float = field(default_factory=lambda: time.time())  # epoch seconds updated by heartbeat
	persona: Optional[str] = None  # selected assistant persona (unique per room)
	# Suspension (grace reconnect) support
	suspended_at: Optional[float] = None  # when marked suspended (player temporarily left)
	suspend_deadline: Optional[float] = None  # absolute epoch seconds when removal will occur if not back


@dataclass
class Room:
	id: int
	name: str
	password: Optional[str] = None
	players: Dict[str, Player] = field(default_factory=dict)  # key: session_id
	multi_game: Optional[MultiRoundYesNoGame] = None  # active game (multi-round only)
	started: bool = False
	question_limit: Optional[int] = None
	max_players: int = 2  # default capacity
	# Post-game cooldown (players may chat for N seconds then room auto-resets)
	postgame_deadline: float | None = None
	postgame_duration: int = 60  # seconds
	# Last reset reason (e.g., 'inactive_player', 'suspend_timeout') exposed to clients for UX messaging
	last_reset_reason: Optional[str] = None

	def join(self, session_id: str, player_name: str) -> None:
		if self.started:
			raise ValueError("بازی در این اتاق شروع شده است. لطفاً منتظر پایان بمانید.")
		if len(self.players) >= self.max_players and session_id not in self.players:
			raise ValueError("ظرفیت اتاق تکمیل است.")
		if session_id in self.players:
			# update name if changed
			pl = self.players[session_id]
			pl.name = player_name
			pl.last_seen = time.time()
		else:
			self.players[session_id] = Player(name=player_name, joined_at=len(self.players)+1)
			# Log new join (only when first added)
			try:
				log_player_join(player_name, session_id, self.id, self.name)
			except Exception:
				pass

	def leave(self, session_id: str) -> None:
		self.players.pop(session_id, None)
		# If all players leave, reset room
		# (legacy attribute self.game replaced by self.multi_game)
		if not self.players and not (self.multi_game and self.multi_game.is_over is False):
			self.reset()

	def start_game(self, question_limit: int, *, rounds: int = 3,
				 questions_per_round: int | None = None, guesses_per_round: int = 1, chat_seconds: int = 300) -> None:
		"""Start a new multi-round game (only mode)."""
		if self.started:
			raise ValueError("بازی قبلاً شروع شده است.")
		if len(self.players) < 1:
			raise ValueError("حداقل یک بازیکن لازم است.")
		player_names = [p.name for p in self.players.values()]
		qp = questions_per_round if questions_per_round is not None else question_limit
		from words import get_random_word  # local import to avoid cycles
		from llm_combined.llm_game import generate_llm_reply
		self.multi_game = MultiRoundYesNoGame(
			players=player_names,
			word_picker=get_random_word,
			questions_per_player=qp,
			guesses_per_player=guesses_per_round,
			max_rounds=rounds,
			chat_duration_sec=chat_seconds,
		)
		self.question_limit = qp
		self.started = True
		# Attach unique game id & file bundle for logging
		try:
			self.game_id = generate_game_id()  # type: ignore[attr-defined]
			self.file_bundle = GameFileBundle(self.game_id, player_names, self.id, self.name, self.multi_game.word)  # type: ignore[attr-defined]
		except Exception:
			self.game_id = None  # type: ignore[attr-defined]
			self.file_bundle = None  # type: ignore[attr-defined]

	def reset(self) -> None:
		self.multi_game = None
		self.started = False
		self.question_limit = None
		self.postgame_deadline = None
		# Clear any suspension metadata when a room resets (fresh state)
		for pl in self.players.values():
			pl.suspended_at = None
			pl.suspend_deadline = None
		# Nullify file bundle so new game gets new id
		if hasattr(self, 'file_bundle'):
			self.file_bundle = None  # type: ignore[attr-defined]
		if hasattr(self, 'game_id'):
			self.game_id = None  # type: ignore[attr-defined]

	def to_public_dict(self, session_id: Optional[str] = None) -> Dict[str, Any]:
		you = None
		if session_id and session_id in self.players:
			you = self.players[session_id].name
		game_summary = self.multi_game.summary() if self.multi_game else None
		# Expose persona mapping (without revealing secret info). None if not chosen.
		personas = {p.name: p.persona for p in self.players.values()}
		# Suspension surface: list suspended players and deadlines
		suspended = {p.name: int(p.suspend_deadline) for p in self.players.values() if p.suspended_at and p.suspend_deadline}
		return {
			"id": self.id,
			"name": self.name,
			"requires_password": self.password is not None,
			"player_count": len(self.players),
			"max_players": self.max_players,
			"players": [p.name for p in self.players.values()],
			"personas": personas,
			"started": self.started,
			"question_limit": self.question_limit,
			"you": you,
			"mode": "multi" if self.multi_game else None,
			"game": game_summary,
			"game_id": getattr(self, 'game_id', None),
			"postgame_deadline": int(self.postgame_deadline) if self.postgame_deadline else None,
			"suspended_players": suspended or None,
			"last_reset_reason": self.last_reset_reason,
		}

	# ---------------- Post-game helpers ----------------
	def maybe_start_postgame(self) -> bool:
		"""If game just ended, start post-game cooldown (once). Returns True if started now."""
		if self.multi_game and self.multi_game.is_over and self.postgame_deadline is None:
			self.postgame_deadline = time.time() + self.postgame_duration
			threading.Thread(target=self._postgame_timer_worker, daemon=True).start()
			return True
		return False

	def _postgame_timer_worker(self):
		try:
			while self.postgame_deadline and time.time() < self.postgame_deadline:
				time.sleep(1)
			if self.postgame_deadline:  # timer not canceled
				self.reset()
				try:
					broadcast(self.id, "reset", {"state": self.to_public_dict(None)})
				except Exception:
					pass
		except Exception:
			pass


ROOMS: Dict[int, Room] = {}

# ----------------------------------------------------------------------------------
# Previously used Socket.IO for real-time push; replaced with client polling for environments without WebSocket support.
# ----------------------------------------------------------------------------------

def broadcast(room_id: int, event: str, payload: Dict[str, Any]):
	"""No-op broadcast placeholder (kept for code continuity).

	Front-end now polls /state/<room_id> periodically; we could store a lightweight
	room event log if incremental updates are needed later.
	"""
	return


def _inactivity_monitor():
	"""Background thread to remove idle players and reset games.

	Runs every INACTIVITY_SWEEP_INTERVAL seconds.
	"""
	while True:
		try:
			now = time.time()
			for room in list(ROOMS.values()):
				for sid, pl in list(room.players.items()):
					idle_for = now - getattr(pl, 'last_seen', now)
					# If already suspended, check deadline expiry
					if pl.suspended_at and pl.suspend_deadline:
						if now >= pl.suspend_deadline:
							# Remove player & if a game was in progress reset
							if room.started:
								room.last_reset_reason = 'suspend_timeout'
								room.reset()
								try:
									broadcast(room.id, "reset", {"state": room.to_public_dict(None), "reason": "suspend_timeout"})
								except Exception:
									pass
							room.leave(sid)
							try:
								broadcast(room.id, "leave", {"state": room.to_public_dict(None), "reason": "suspend_timeout"})
							except Exception:
								pass
						continue
					# Not yet suspended: if idle passes trigger mark as suspended
					if idle_for >= SUSPEND_TRIGGER_SECONDS and not pl.suspended_at:
						pl.suspended_at = now
						pl.suspend_deadline = pl.last_seen + SUSPEND_GRACE_SECONDS
						try:
							broadcast(room.id, "suspended", {"player": pl.name, "deadline": pl.suspend_deadline, "state": room.to_public_dict(None)})
						except Exception:
							pass
		except Exception:
			pass
		time.sleep(INACTIVITY_SWEEP_INTERVAL)


def _init_rooms():
	if ROOMS:
		return
	# All rooms share a common password (hinted in lobby for easier play)
	shared_pwd = "1234"
	ROOMS[1] = Room(id=1, name="اتاق ۱", password=shared_pwd, max_players=2)
	ROOMS[2] = Room(id=2, name="اتاق ۲", password=shared_pwd, max_players=2)
	ROOMS[3] = Room(id=3, name="اتاق ۳", password=shared_pwd, max_players=2)
	ROOMS[4] = Room(id=4, name="اتاق ۴", password=shared_pwd, max_players=2)
	# Start inactivity monitor thread once
	threading.Thread(target=_inactivity_monitor, name="idle-monitor", daemon=True).start()


@app.before_request
def ensure_session_id():
	# Provide unique session id for tracking players (not secure auth)
	if "sid" not in session:
		session["sid"] = secrets.token_hex(8)
	# Passive heartbeat: update last_seen if this request targets a room and player exists
	try:
		if request.view_args and 'room_id' in request.view_args:
			room_id = int(request.view_args['room_id'])
			room = ROOMS.get(room_id)
			if room and session.get('sid') in room.players:
				pl = room.players[session['sid']]
				pl.last_seen = time.time()
				# If player was suspended and returns before deadline -> resume
				if pl.suspended_at and (not pl.suspend_deadline or time.time() < pl.suspend_deadline):
					pl.suspended_at = None
					pl.suspend_deadline = None
					try:
						broadcast(room_id, "resumed", {"player": pl.name, "state": room.to_public_dict(None)})
					except Exception:
						pass
	except Exception:
		pass


# ----------------------------------------------------------------------------------
# Utility
# ----------------------------------------------------------------------------------

def get_room_or_404(room_id: int) -> Room:
	room = ROOMS.get(room_id)
	if not room:
		abort(404)
	return room


# ----------------------------------------------------------------------------------
# Routes: Lobby / Index
# ----------------------------------------------------------------------------------

@app.route("/")
def index():
	_init_rooms()
	room_data = [r.to_public_dict(session.get("sid")) for r in ROOMS.values()]
	return render_template("index.html", rooms=room_data)


@app.route("/brand/<path:filename>")
def brand_file(filename: str):
	"""Serve branding assets (logos) from project root directory for ease of reference.

	We keep them outside static to avoid cache conflicts while iterating; in production
	you could move them into /static and use versioned filenames.
	"""
	base_dir = os.path.dirname(__file__)
	return send_from_directory(base_dir, filename)


@app.post("/join/<int:room_id>")
def join_room(room_id: int):
	room = get_room_or_404(room_id)
	player_name = request.form.get("player_name", "بازیکن")[:32].strip() or "بازیکن"
	password = request.form.get("password") or ""
	sid = session["sid"]
	# Track current room for persona uniqueness checks later
	session['current_room_id'] = room_id
	if room.password and room.password != password:
		flash("رمز عبور نادرست است.", "error")
		return redirect(url_for("index"))
	try:
		room.join(sid, player_name)
	except ValueError as e:
		flash(str(e), "error")
		return redirect(url_for("index"))
	# Broadcast join (state without player-specific 'you')
	broadcast(room_id, "join", {"player": player_name, "state": room.to_public_dict(None)})
	return redirect(url_for("view_room", room_id=room_id))


@app.post("/join_code")
def join_by_code():
	"""Join a room using a submitted numeric code instead of predefined cards.

	Expects form fields: player_name, room_code, password
	"""
	_init_rooms()
	code_raw = request.form.get("room_code", "").strip()
	player_name = request.form.get("player_name", "بازیکن")[:32].strip() or "بازیکن"
	password = request.form.get("password", "")
	if not code_raw.isdigit():
		flash("کد اتاق نامعتبر است.", "error")
		return redirect(url_for("index"))
	room_id = int(code_raw)
	room = ROOMS.get(room_id)
	if not room:
		flash("اتاقی با این کد یافت نشد.", "error")
		return redirect(url_for("index"))
	if room.password and room.password != password:
		flash("رمز نادرست است.", "error")
		return redirect(url_for("index"))
	sid = session.get("sid")
	if not sid:
		session["sid"] = secrets.token_hex(8)
		sid = session["sid"]
	try:
		room.join(sid, player_name)
	except ValueError as e:
		flash(str(e), "error")
		return redirect(url_for("index"))
	# Save current room for persona operations
	session['current_room_id'] = room_id
	broadcast(room_id, "join", {"player": player_name, "state": room.to_public_dict(None)})
	return redirect(url_for("view_room", room_id=room_id))


@app.get("/room/<int:room_id>")
def view_room(room_id: int):
	room = get_room_or_404(room_id)
	sid = session.get("sid")
	if sid not in room.players:
		flash("ابتدا وارد اتاق شوید.", "error")
		return redirect(url_for("index"))
	return render_template("room.html", room=room.to_public_dict(sid))


@app.post("/start/<int:room_id>")
def start_game(room_id: int):
	room = get_room_or_404(room_id)
	sid = session.get("sid")
	if sid not in room.players:
		flash("ابتدا وارد اتاق شوید.", "error")
		return redirect(url_for("index"))
	if room.started:
		flash("بازی در حال اجرا است.", "info")
		return redirect(url_for("view_room", room_id=room_id))
	# Persona selection (assistant) from form
	persona = request.form.get("persona", "Sherlock Holmes")
	# Validate persona against allowed list
	ALLOWED_PERSONAS = {"Sherlock Holmes", "Hercule Poirot", "Columbo", "Miss Marple", "Mentalist"}
	if persona not in ALLOWED_PERSONAS:
		persona = "Sherlock Holmes"
	# Enforce uniqueness: if already taken by another player, reject start
	existing_personas = {pl.persona for sid2, pl in room.players.items() if sid2 != sid and pl.persona}
	if persona in existing_personas:
		flash("این شخصیت قبلاً انتخاب شده است. لطفاً شخصیت دیگری انتخاب کنید.", "error")
		return redirect(url_for("view_room", room_id=room_id))
	# Assign persona to this player record & session
	room.players[sid].persona = persona
	session["chat_persona"] = persona  # store per-user assistant choice
	# Only multi-round mode supported now
	try:
		multi_rounds = int(request.form.get("rounds", "3"))
		multi_rounds = max(1, min(20, multi_rounds))
	except ValueError:
		multi_rounds = 3
	try:
		questions_per_round = int(request.form.get("questions_per_round", "3"))
		questions_per_round = max(1, min(50, questions_per_round))
	except ValueError:
		questions_per_round = 3
	try:
		guesses_per_round = int(request.form.get("guesses_per_round", "1"))
		guesses_per_round = max(1, min(10, guesses_per_round))
	except ValueError:
		guesses_per_round = 1
	try:
		chat_seconds = int(request.form.get("chat_seconds", "300"))
		chat_seconds = max(10, min(900, chat_seconds))
	except ValueError:
		chat_seconds = 300
	try:
		# For backward UI pieces expecting question_limit, we reuse per-round value
		room.start_game(question_limit=questions_per_round, rounds=multi_rounds,
			   questions_per_round=questions_per_round, guesses_per_round=guesses_per_round,
			   chat_seconds=chat_seconds)
		flash("بازی شروع شد!", "success")
		# No broadcast for persona directly (kept personal); front-end will request it from /state
		broadcast(room_id, "start", {"question_limit": questions_per_round, "state": room.to_public_dict(None)})
	except ValueError as e:
		flash(str(e), "error")
	return redirect(url_for("view_room", room_id=room_id))


@app.post("/ask/<int:room_id>")
def ask_question(room_id: int):
	room = get_room_or_404(room_id)
	sid = session.get("sid")
	if sid not in room.players:
		return jsonify({"error": "اجازه دسترسی"}), 403
	if not room.multi_game:
		return jsonify({"error": "بازی هنوز شروع نشده"}), 400
	question = request.form.get("question", "").strip()
	if not question:
		return jsonify({"error": "سوال خالی است"}), 400
	try:
		acting_player = room.players[sid].name
		from llm_combined.llm_game import generate_llm_reply
		answer_bool = room.multi_game.ask(acting_player, question, generate_llm_reply)
		answer_text = "بله" if answer_bool else "خیر"
		# Log Q
		try:
			bundle = getattr(room, 'file_bundle', None)
			if bundle:
				log_question(bundle, room.multi_game.round, room.multi_game.phase, acting_player, question, answer_bool)
		except Exception:
			pass
		# Privacy change: do NOT broadcast the actual question / answer to everyone.
		# Only notify others that state changed (remaining counters etc.).
		broadcast(room_id, "question", {
			"player": acting_player,
			"state": room.to_public_dict(None)  # sanitized
		})
		# If game just transitioned to completed, start postgame cooldown window
		if room.maybe_start_postgame():
			broadcast(room_id, "postgame", {"state": room.to_public_dict(None)})
		# Return full info ONLY to the asking player.
		return jsonify({
			"ok": True,
			"player": acting_player,
			"question": question,
			"answer_bool": answer_bool,
			"answer_text": answer_text,
			"state": room.to_public_dict(sid)
		})
	except ValueError as e:
		return jsonify({"error": str(e)}), 400


@app.post("/guess/<int:room_id>")
def make_guess(room_id: int):
	room = get_room_or_404(room_id)
	sid = session.get("sid")
	if sid not in room.players:
		return jsonify({"error": "اجازه دسترسی"}), 403
	if not room.multi_game:
		return jsonify({"error": "بازی هنوز شروع نشده"}), 400
	guess_word = request.form.get("guess", "").strip()
	if not guess_word:
		return jsonify({"error": "حدس خالی است"}), 400
	try:
		acting_player = room.players[sid].name
		correct = room.multi_game.guess(acting_player, guess_word)
		msg = "درست بود!" if correct else "نادرست"
		# Log guess
		try:
			bundle = getattr(room, 'file_bundle', None)
			if bundle:
				log_guess(bundle, room.multi_game.round, room.multi_game.phase, acting_player, guess_word, correct)
		except Exception:
			pass
		# Privacy: broadcast only that a guess occurred + updated state, without revealing guess or correctness.
		broadcast(room_id, "guess", {
			"player": acting_player,
			"state": room.to_public_dict(None)
		})
		if room.maybe_start_postgame():
			broadcast(room_id, "postgame", {"state": room.to_public_dict(None)})
		return jsonify({
			"ok": True,
			"player": acting_player,
			"guess": guess_word,
			"correct": correct,
			"message": msg,
			"state": room.to_public_dict(sid)
		})
	except ValueError as e:
		return jsonify({"error": str(e)}), 400


@app.post("/reveal/<int:room_id>")
def reveal_word(room_id: int):
	room = get_room_or_404(room_id)
	sid = session.get("sid")
	if sid not in room.players:
		return jsonify({"error": "اجازه دسترسی"}), 403
	if not room.multi_game:
		return jsonify({"error": "بازی هنوز شروع نشده"}), 400
	# In multi-round mode we reveal only when completed or winner found
	if not room.multi_game.is_over:
		return jsonify({"error": "هنوز اجازه نمایش نیست"}), 400
	word = room.multi_game.word
	broadcast(room_id, "reveal", {"word": word, "state": room.to_public_dict(None)})
	return jsonify({"word": word, "state": room.to_public_dict(sid)})


# ---------------- Multi-round chat endpoints ----------------

@app.post("/chat/send/<int:room_id>")
def chat_send(room_id: int):
	room = get_room_or_404(room_id)
	sid = session.get("sid")
	if sid not in room.players:
		return jsonify({"error": "اجازه دسترسی"}), 403
	if not room.multi_game:
		return jsonify({"error": "بازی چند مرحله ای فعال نیست"}), 400
	# Allow chat if we are in CHAT phase or postgame cooldown
	if not (room.multi_game.phase == room.multi_game.Phase.CHAT or (room.multi_game.is_over and room.postgame_deadline)):
		return jsonify({"error": "الان امکان گفتگو نیست"}), 400
	msg = request.form.get("msg", "").strip()
	if not msg:
		return jsonify({"error": "پیام خالی است"}), 400
	try:
		entry = room.multi_game.add_chat_message(room.players[sid].name, msg)
		# Log chat message (only during active game phases or postgame chat). Round may be last known.
		try:
			bundle = getattr(room, 'file_bundle', None)
			if bundle:
				log_chat(bundle, room.multi_game.round, entry['player'], entry['msg'], False)
		except Exception:
			pass
		broadcast(room_id, "chat", {"entry": entry, "state": room.to_public_dict(None)})
		return jsonify({"ok": True, "entry": entry, "state": room.to_public_dict(sid)})
	except ValueError as e:
		return jsonify({"error": str(e)}), 400

@app.post("/chat/bot_reply/<int:room_id>")
def chat_bot_reply(room_id: int):
	"""Generate a contextual assistant reply based on recent chat log.

	Uses per-session selected persona stored under session['chat_persona'].
	Appends bot reply into chat log and broadcasts like a normal chat message.
	"""
	room = get_room_or_404(room_id)
	sid = session.get("sid")
	if sid not in room.players:
		return jsonify({"error": "اجازه دسترسی"}), 403
	if not room.multi_game:
		return jsonify({"error": "بازی چند مرحله ای فعال نیست"}), 400
	if not (room.multi_game.phase == room.multi_game.Phase.CHAT or (room.multi_game.is_over and room.postgame_deadline)):
		return jsonify({"error": "خارج از فاز گفتگو / پس از پایان"}), 400
	persona = session.get("chat_persona", "Sherlock Holmes")
	# Build structured messages mapping players + any previous ai assistant messages.
	# We treat bot messages as coming from persona name.
	full_log = room.multi_game.chat_log
	messages_for_llm = []
	for entry in full_log:
		messages_for_llm.append({"player": entry.get("player", "?"), "text": entry.get("msg", "")})
	try:
		from llm_combined.llm_client import generate_llm_reply as chat_generate  # import here to avoid startup cost
		reply_text = chat_generate(messages_for_llm, persona)
	except Exception as e:  # noqa: BLE001
		reply_text = f"(خطای تولید پاسخ: {e})"
	# Append to chat log as bot message
	bot_entry = {"player": persona, "msg": reply_text, "ts": int(time.time())}
	room.multi_game.chat_log.append(bot_entry)
	# Log bot reply
	try:
		bundle = getattr(room, 'file_bundle', None)
		if bundle:
			log_chat(bundle, room.multi_game.round, persona, reply_text, True)
	except Exception:
		pass
	broadcast(room_id, "chat", {"entry": bot_entry, "state": room.to_public_dict(None)})
	return jsonify({"ok": True, "entry": bot_entry, "state": room.to_public_dict(sid), "persona": persona})


@app.post("/chat/ready/<int:room_id>")
def chat_ready(room_id: int):
	room = get_room_or_404(room_id)
	sid = session.get("sid")
	if sid not in room.players:
		return jsonify({"error": "اجازه دسترسی"}), 403
	if not room.multi_game:
		return jsonify({"error": "بازی چند مرحله ای فعال نیست"}), 400
	changed = room.multi_game.player_ready(room.players[sid].name)
	if changed:
		# round advanced
		broadcast(room_id, "round", {"state": room.to_public_dict(None)})
	else:
		broadcast(room_id, "ready", {"player": room.players[sid].name, "state": room.to_public_dict(None)})
	return jsonify({"ok": True, "state": room.to_public_dict(sid)})


@app.get("/chat/<int:room_id>")
def chat_page(room_id: int):
	"""Dedicated chat room page shown only during CHAT phase.

	Players are redirected back to the gameplay room when phase changes.
	"""
	room = get_room_or_404(room_id)
	sid = session.get("sid")
	if sid not in room.players:
		flash("ابتدا وارد اتاق شوید.", "error")
		return redirect(url_for("index"))
	if not room.multi_game:
		flash("بازی شروع نشده است.", "error")
		return redirect(url_for("view_room", room_id=room_id))
	if not (room.multi_game.phase == room.multi_game.Phase.CHAT or (room.multi_game.is_over and room.postgame_deadline)):
		return redirect(url_for("view_room", room_id=room_id))
	player_name = room.players[sid].name
	personal = room.multi_game.personal_history(player_name)
	return render_template("chat.html", room=room.to_public_dict(sid), personal_history=personal, player_name=player_name)


@app.get("/chat/tick/<int:room_id>")
def chat_tick(room_id: int):
	room = get_room_or_404(room_id)
	if not room.multi_game:
		return jsonify({"error": "inactive"}), 400
	advanced = room.multi_game.tick_chat()
	if advanced:
		broadcast(room_id, "round", {"state": room.to_public_dict(None)})
	else:
		# broadcast timer ping (client may display countdown)
		broadcast(room_id, "timer", {"state": room.to_public_dict(None)})
	return jsonify({"ok": True, "advanced": advanced})


@app.get("/history/<int:room_id>")
def personal_history_api(room_id: int):
	"""Return the caller's personal question/guess history (multi-round only)."""
	room = get_room_or_404(room_id)
	sid = session.get("sid")
	if sid not in room.players:
		return jsonify({"error": "اجازه دسترسی"}), 403
	if not room.multi_game:
		return jsonify({"error": "بازی فعال نیست"}), 400
	player_name = room.players[sid].name
	return jsonify(room.multi_game.personal_history(player_name))


@app.post("/reset/<int:room_id>")
def reset_room(room_id: int):
	room = get_room_or_404(room_id)
	sid = session.get("sid")
	if sid not in room.players:
		flash("ابتدا وارد اتاق شوید.", "error")
		return redirect(url_for("index"))
	room.last_reset_reason = 'manual'
	room.reset()
	broadcast(room_id, "reset", {"state": room.to_public_dict(None)})
	flash("اتاق ریست شد.", "info")
	return redirect(url_for("view_room", room_id=room_id))


@app.post("/leave/<int:room_id>")
def leave_room(room_id: int):
	room = get_room_or_404(room_id)
	sid = session.get("sid")
	room.leave(sid)
	# Attempt to find player name (after leave may be gone) - simplify: broadcast state only
	broadcast(room_id, "leave", {"state": room.to_public_dict(None)})
	flash("از اتاق خارج شدید.", "info")
	return redirect(url_for("index"))


@app.get("/state/<int:room_id>")
def room_state(room_id: int):
	room = get_room_or_404(room_id)
	sid = session.get("sid")
	if sid not in room.players:
		return jsonify({"error": "اجازه دسترسی"}), 403
	return jsonify(room.to_public_dict(sid))

@app.post("/ping/<int:room_id>")
def ping(room_id: int):
	"""Heartbeat endpoint called periodically by the client to keep player active."""
	room = get_room_or_404(room_id)
	sid = session.get("sid")
	if not sid or sid not in room.players:
		return jsonify({"error": "ناشناس"}), 403
	pl = room.players[sid]
	pl.last_seen = time.time()
	if pl.suspended_at:
		# Resume if still within grace period
		if not pl.suspend_deadline or time.time() < pl.suspend_deadline:
			pl.suspended_at = None
			pl.suspend_deadline = None
			try:
				broadcast(room_id, "resumed", {"player": pl.name, "state": room.to_public_dict(None)})
			except Exception:
				pass
	return jsonify({"ok": True, "ts": int(time.time())})

@app.post("/set_persona")
def set_persona():
	persona = request.form.get("persona", "").strip()
	ALLOWED_PERSONAS = {"Sherlock Holmes", "Hercule Poirot", "Columbo", "Miss Marple", "Mentalist"}
	# Empty string means release current persona
	if persona and persona not in ALLOWED_PERSONAS:
		return jsonify({"error": "پرسانای نامعتبر"}), 400
	# Determine current room (if user joined one) to enforce uniqueness.
	room_id = session.get('current_room_id')
	if room_id and isinstance(room_id, int):
		room = ROOMS.get(room_id)
		if room and session.get('sid') in room.players:
			# Check uniqueness excluding current player's existing persona.
			sid = session['sid']
			current_player = room.players[sid]
			others = {pl.persona for sid2, pl in room.players.items() if sid2 != sid and pl.persona}
			if persona and persona in others:
				return jsonify({"error": "این شخصیت قبلاً انتخاب شده است"}), 400
			# Assign or clear
			current_player.persona = persona or None
			if persona:
				session["chat_persona"] = persona
			else:
				session.pop("chat_persona", None)
	# Also return updated personas map if room known
	personas = None
	if room_id and isinstance(room_id, int) and room_id in ROOMS:
		personas = {p.name: p.persona for p in ROOMS[room_id].players.values()}
	return jsonify({"ok": True, "persona": persona or None, "personas": personas})


@app.errorhandler(404)
def not_found(err):  # type: ignore
	return render_template("404.html"), 404


def create_app():  # factory for tests if needed
	return app


if __name__ == "__main__":
	_init_rooms()
	app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

