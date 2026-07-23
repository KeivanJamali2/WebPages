from __future__ import annotations
from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response, send_from_directory
import threading
import time
import uuid
from typing import Dict, Optional, List, Any
import os
import csv
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import importlib.util
import sys
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
"""LLM integration (kept isolated in llm_combined package)

We want reporter/chat personas to appear dynamically from the prompt files even
if the Python package import fails due to how the app is launched (CWD/paths).
Below, we try the regular package import first. If that fails, we fall back to
loading the modules directly from their file paths using importlib.
"""

def _load_prompts_with_fallback(pkg_module: str, file_basename: str):
    """Load a module's `prompts` dict via package import, else via file path.

    Returns an empty dict on failure. This keeps the app running while making
    it robust to working-directory/path nuances.
    """
    # 1) Try package import first
    try:
        module = __import__(pkg_module, fromlist=['prompts'])  # type: ignore
        prompts_obj = getattr(module, 'prompts', {})
        if isinstance(prompts_obj, dict):
            return prompts_obj
    except Exception as e:
        # fall through to file-based import
        pass
    # 2) Try file path import relative to this file
    try:
        base_dir = os.path.dirname(__file__)
        file_path = os.path.join(base_dir, 'llm_combined', f'{file_basename}.py')
        if os.path.isfile(file_path):
            spec = importlib.util.spec_from_file_location(pkg_module, file_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                # Temporarily insert base_dir to sys.path for any local relative imports
                sys_modules_key = f"__loaded_fallback__:{pkg_module}"
                try:
                    sys.modules[sys_modules_key] = mod
                    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
                finally:
                    sys.modules.pop(sys_modules_key, None)
                prompts_obj = getattr(mod, 'prompts', {})
                if isinstance(prompts_obj, dict):
                    return prompts_obj
    except Exception:
        pass
    return {}

# 1) Load prompts independently so UI remains dynamic even if LLM stack is unavailable.
REPORTER_PROMPTS = _load_prompts_with_fallback('llm_combined.prompts_reporter', 'prompts_reporter')
CHAT_PROMPTS = _load_prompts_with_fallback('llm_combined.prompts_chat', 'prompts_chat')

# 2) Import callable generators with graceful fallbacks (do NOT impact prompt availability)
try:
    from llm_combined import generate_llm_reply  # type: ignore
except Exception:
    def generate_llm_reply(messages, persona="Bot"):
        return f"LLM is not available (persona={persona})."
try:
    from llm_combined.llm_reporter import generate_reporter_reply  # type: ignore
except Exception:
    def generate_reporter_reply(messages, persona="Reporter"):
        return f"(گزارشگر غیرفعال - {persona})"
from collections import deque

app = Flask(__name__)

# ----------------------------- Config ------------------------------------- #
# Player inactivity timeout (seconds) after which the server will prune a player
# who has not polled / acted. Default 60s (can override via env GAME_INACTIVITY_TIMEOUT).
try:
    INACTIVITY_TIMEOUT = float(os.getenv('GAME_INACTIVITY_TIMEOUT', '60'))
except Exception:
    INACTIVITY_TIMEOUT = 60.0

# ----------------------------- Fonts / i18n Config ------------------------- #
# Persian (Farsi) font family can be configured via environment variable.
# Provide a sensible multi-fallback default (local variable font first if added).
"""Font configuration

We expose a curated list of locally provided Persian / decorative fonts (see
static/css/fonts.css) so users can pick their preferred one at runtime. The
selection is stored in a cookie (persian_font) and injected into templates via
CSS variable --configured-persian-font. Fallback chain keeps system fonts.
"""

# Ordered by preference (first is default). Each item should match the
# font-family name declared inside fonts.css @font-face blocks.
AVAILABLE_PERSIAN_FONTS: List[str] = [
    'Vazirmatn', 'Chamran', 'Cinema', 'DigiHilan', 'DimaArsalan', 'DimaClassic',
    'DimaMagic', 'DimaType', 'Fonoon', 'Ghalam', 'Mashti', 'Nofar', 'Omid',
    'OnvanAlt', 'Onvan', 'Ray', 'Shaparak', 'Sin', 'Yazd'
]

DEFAULT_PERSIAN_FONT = AVAILABLE_PERSIAN_FONTS[0]

# Base fallback chain (system fonts) appended after chosen font.
SYSTEM_FALLBACK_CHAIN = "'IRANSansX', 'IRANYekan', 'Tahoma', 'Helvetica Neue', Arial, sans-serif"

def build_font_stack(chosen: str | None) -> str:
    c = chosen or DEFAULT_PERSIAN_FONT
    if c not in AVAILABLE_PERSIAN_FONTS:
        c = DEFAULT_PERSIAN_FONT
    return f"'{c}', {SYSTEM_FALLBACK_CHAIN}"

def get_selected_persian_font() -> str:
    font = request.cookies.get('persian_font') if request else None  # type: ignore
    if font and font in AVAILABLE_PERSIAN_FONTS:
        return font
    return DEFAULT_PERSIAN_FONT

@app.context_processor
def inject_global_font_config():  # type: ignore
    """Inject dynamic font variables for templates.

    Template variables:
      - PERSIAN_FONT_STACK: Full font stack string for CSS var.
      - AVAILABLE_PERSIAN_FONTS: List for building UI pickers.
      - SELECTED_PERSIAN_FONT: Currently chosen font family.
    """
    sel = get_selected_persian_font()
    return {
        'PERSIAN_FONT_STACK': build_font_stack(sel),
        'AVAILABLE_PERSIAN_FONTS': AVAILABLE_PERSIAN_FONTS,
        'SELECTED_PERSIAN_FONT': sel,
    }

# ----------------------------- Font API ----------------------------------- #
@app.route('/api/fonts')
def api_fonts():
    """Return list of available fonts and current selection."""
    sel = get_selected_persian_font()
    return jsonify({'ok': True, 'fonts': AVAILABLE_PERSIAN_FONTS, 'selected': sel})

@app.route('/api/font', methods=['POST'])
def api_set_font():
    """Set active Persian font via cookie.

    JSON body: { "font": "Vazirmatn" }
    Persisted with a 30-day cookie.
    """
    data = request.get_json(force=True, silent=True) or {}
    font = (data.get('font') or '').strip()
    if font not in AVAILABLE_PERSIAN_FONTS:
        return jsonify({'ok': False, 'error': 'Invalid font'}), 400
    resp = make_response(jsonify({'ok': True, 'selected': font, 'stack': build_font_stack(font)}))
    max_age = 60 * 60 * 24 * 30  # 30 days
    resp.set_cookie('persian_font', font, max_age=max_age, samesite='Lax')
    return resp

# Multiple passcodes mapped to room ids (1..3)
# Extend or change these as needed. Each passcode selects a distinct room instance.
PASSCODES = {
    '1111': 1,
    '2222': 2,
    '3333': 3,
}

# Personas are now derived dynamically from prompt files.
# - CHAT_PERSONAS are keys of CHAT_PROMPTS (llm_combined/prompts_chat.py)
# - REPORTER_PERSONAS are keys of REPORTER_PROMPTS (llm_combined/prompts_reporter.py)
def _list_chat_personas() -> List[str]:
    try:
        return [str(k) for k in CHAT_PROMPTS.keys()]  # type: ignore
    except Exception:
        return []

def _list_reporter_personas() -> List[str]:
    try:
        return [str(k) for k in REPORTER_PROMPTS.keys()]  # type: ignore
    except Exception:
        return []

CHAT_PERSONAS: List[str] = _list_chat_personas()
REPORTER_PERSONAS: List[str] = _list_reporter_personas()

# ----------------------------- Game State ---------------------------------- #
class Player:
    def __init__(self, name: str):
        self.name = name
        self.last_active = time.time()
        self.current_word: Optional[str] = None
        self.decision: Optional[str] = None  # 'same' | 'again' | None
        # For per-user chat reset: ignore all chat messages with id <= this value
        self.chat_reset_after_id: int = 0

    def to_public(self):
        return {
            'name': self.name,
            'current_word': self.current_word,
            'decision': self.decision,
        }

class GameState:
    def __init__(self):
        self.lock = threading.Lock()
        self.players: Dict[str, Player] = {}
        self.round_index = 1
        self.words_history: List[Dict[str, str]] = []  # list of {player: word}
        self.status = 'collecting'  # 'collecting' | 'deciding' | 'finished'
        self.prompt: str = 'Think of a word'  # current prompt question
        # Maximum number of rounds allowed (None -> unlimited). When the
        # limit is reached after finishing decisions for that round (i.e., a
        # non-converged "again" path), the game will auto-finish with reason
        # 'round_limit'. Exposed to clients so they can show progress.
        self.max_rounds: Optional[int] = None
        # Reason for finishing: 'converged' (all said same) | 'round_limit'
        # | 'manual' (future) | None (while active)
        self.finished_reason: Optional[str] = None
        # Internal flag caching whether round limit adjustments are allowed;
        # computed dynamically (not persisted) but cached for minor perf.
        # We treat the game as "started" (locking the slider) once ANY word
        # has been submitted in round 1. After a reset, it becomes adjustable
        # again until the first submission.

    # ------------------------ Round Limit Control ------------------------ #
    def game_started(self) -> bool:
        """Return True once the first round has seen any submission.

        Criteria:
          - Any history exists (means at least one full round has elapsed), OR
          - Current round index > 1, OR
          - Any player has a non-None current_word (a submission in progress), OR
          - Status is not 'collecting' (deciding/finished already implies start)
        """
        if self.words_history:
            return True
        if self.round_index > 1:
            return True
        if self.status != 'collecting':
            return True
        # Any partial submission in the first collecting phase locks it
        for p in self.players.values():
            if p.current_word is not None:
                return True
        return False

    def can_adjust_round_limit(self) -> bool:
        """Round limit adjustable only BEFORE game starts.

        Once locked, it remains locked until a reset (soft or hard) that clears
        history and submissions.
        """
        return not self.game_started()

    def join(self, name: str) -> str:
        with self.lock:
            # Use stable id for player names unique enforcement
            for pid, p in self.players.items():
                if p.name == name:
                    p.last_active = time.time()
                    return pid
            pid = str(uuid.uuid4())
            self.players[pid] = Player(name)
            return pid

    def submit_word(self, player_id: str, word: str):
        word = (word or '').strip()
        if not word:
            raise ValueError('Empty word')
        with self.lock:
            self._require_active_player(player_id)
            player = self.players[player_id]
            player.current_word = word
            player.decision = None
            # Check if all players submitted to move to deciding phase
            if self._all_players(lambda p: p.current_word is not None):
                self.status = 'deciding'
                # Trigger reporter commentary generation (async-ish in thread)
                try:
                    self._trigger_reporters()
                except Exception:
                    pass

    def submit_decision(self, player_id: str, decision: str):
        if decision not in ('same', 'again'):
            raise ValueError('Invalid decision')
        with self.lock:
            self._require_active_player(player_id)
            if self.status != 'deciding':
                raise ValueError('Not in deciding phase')
            self.players[player_id].decision = decision
            # If all decided...
            if self._all_players(lambda p: p.decision in ('same', 'again')):
                # If all said same -> finish
                if all(p.decision == 'same' for p in self.players.values()):
                    # Append convergence round to history
                    snapshot = {p.name: p.current_word for p in self.players.values()}
                    self.words_history.append(snapshot)
                    self.status = 'finished'
                    self.finished_reason = 'converged'
                else:
                    # store history for the round
                    snapshot = {p.name: p.current_word for p in self.players.values()}
                    self.words_history.append(snapshot)
                    # prepare next round
                    # Check limit BEFORE starting a new round
                    next_round = self.round_index + 1
                    if self.max_rounds is not None and next_round > self.max_rounds:
                        # Reached limit; finish without convergence
                        self.status = 'finished'
                        self.finished_reason = 'round_limit'
                    else:
                        self.round_index = next_round
                        for p in self.players.values():
                            p.current_word = None
                            p.decision = None
                        self.status = 'collecting'

    def set_prompt(self, prompt: str):
        with self.lock:
            self.prompt = prompt.strip() or 'Think of a word'

    def reset(self):
        with self.lock:
            self.round_index = 1
            self.words_history.clear()
            for p in self.players.values():
                p.current_word = None
                p.decision = None
            self.status = 'collecting'
            self.prompt = 'Think of a word'
            self.finished_reason = None

    def leave(self, player_id: str):
        """Remove a player from the game. Recompute phase if needed.

        The logic mirrors submit_word/submit_decision transitions so that
        if a player leaves mid-phase and the remaining players satisfy
        the completion predicate, the game advances appropriately.
        """
        with self.lock:
            if player_id not in self.players:
                return
            del self.players[player_id]
            # If no players remain, just soft reset state markers
            if not self.players:
                self.round_index = 1
                self.status = 'collecting'
                return
            # Re-evaluate status after player removal
            if self.status == 'collecting':
                if self._all_players(lambda p: p.current_word is not None):
                    self.status = 'deciding'
            elif self.status == 'deciding':
                if self._all_players(lambda p: p.decision in ('same','again')):
                    if all(p.decision == 'same' for p in self.players.values()):
                        snapshot = {p.name: p.current_word for p in self.players.values()}
                        self.words_history.append(snapshot)
                        self.status = 'finished'
                    else:
                        snapshot = {p.name: p.current_word for p in self.players.values()}
                        self.words_history.append(snapshot)
                        self.round_index += 1
                        for p in self.players.values():
                            p.current_word = None
                            p.decision = None
                        self.status = 'collecting'

    # ---------------- Reporter Integration ------------------ #
    def _collect_current_round_context(self) -> List[Dict[str, str]]:
        """Build a lightweight message history for reporters.

        Format: [{'player': <name>, 'text': <word-info>}, ...]
        We include last 3 rounds + current submissions.
        """
        msgs: List[Dict[str, str]] = []
        # Include prior rounds
        tail_history = self.words_history[-3:]
        for idx, snap in enumerate(tail_history, start=len(self.words_history)-len(tail_history)+1):
            joined = ' | '.join(f"{k}:{v}" for k,v in snap.items())
            msgs.append({'player': 'RoundHistory', 'text': f'Round {idx}: {joined}'})
        # Current submissions (all players have submitted when called)
        current = ' | '.join(f"{p.name}:{p.current_word}" for p in self.players.values())
        msgs.append({'player': 'CurrentRound', 'text': f'Round {self.round_index} submissions: {current}'})
        return msgs

    def _trigger_reporters(self):
        """Spawn a background thread to generate two reporter persona comments.

        This avoids blocking the submit_word response round-trip. Comments will
        be appended to Room.reporters list (room object found by reverse lookup).
        """
        # Find owning room (naive linear search acceptable for few rooms)
        for r in multi.rooms.values():
            if r.game is self:
                room_ref = r
                break
        else:
            return
        # Use configured personas (validated) else fallback to first two available dynamic reporter personas.
        reporter_personas = getattr(room_ref, 'reporter_personas', None) or REPORTER_PERSONAS[:2]
        if not reporter_personas:
            return  # no reporter prompts configured
        context_messages = self._collect_current_round_context()

        def worker():
            # reporter1 then reporter2; second still only needs shared round context.
            seq = reporter_personas[:2]
            for persona in seq:
                try:
                    # Extract last 5 previous comments from THIS persona for continuity
                    prior_persona_comments: List[Dict[str, str]] = []
                    for c in reversed(room_ref.reporters):
                        if c.get('persona') == persona and c.get('round') < self.round_index:
                            prior_persona_comments.append({'player': persona, 'text': c.get('text','')})
                            if len(prior_persona_comments) >= 5:
                                break
                    prior_persona_comments.reverse()  # restore chronological order
                    assembled = prior_persona_comments + context_messages + [
                        {'player': 'System', 'text': 'یک نظر کوتاه بده.'}
                    ]
                    reply = generate_reporter_reply(assembled, persona)
                except Exception as e:
                    reply = f"(خطای گزارشگر: {e})"
                room_ref.add_reporter_comment(persona, reply, self.round_index)
        threading.Thread(target=worker, daemon=True).start()

    def _all_players(self, predicate):
        return bool(self.players) and all(predicate(p) for p in self.players.values())

    def prune_inactive(self, timeout: float = 8.0):
        """Remove players that have not polled or acted within timeout seconds.

        This is a defensive server-side cleanup so that if a user closes the
        browser/tab or loses connection without calling /api/exit explicitly,
        their slot is eventually freed. Timeout kept small (default 8s) because
        the client polls roughly every ~1s; adjust as needed.
        """
        now = time.time()
        removed: List[str] = []
        with self.lock:
            for pid, p in list(self.players.items()):
                if now - p.last_active > timeout:
                    removed.append(pid)
                    del self.players[pid]
            # If removals happened we may need to recompute status logic similar
            # to leave(); reuse same phase transition checks.
            if removed:
                if not self.players:
                    self.round_index = 1
                    self.status = 'collecting'
                elif self.status == 'collecting':
                    if self._all_players(lambda p: p.current_word is not None):
                        self.status = 'deciding'
                elif self.status == 'deciding':
                    if self._all_players(lambda p: p.decision in ('same','again')):
                        if all(p.decision == 'same' for p in self.players.values()):
                            snapshot = {p.name: p.current_word for p in self.players.values()}
                            self.words_history.append(snapshot)
                            self.status = 'finished'
                        else:
                            snapshot = {p.name: p.current_word for p in self.players.values()}
                            self.words_history.append(snapshot)
                            self.round_index += 1
                            for p in self.players.values():
                                p.current_word = None
                                p.decision = None
                            self.status = 'collecting'

    def _require_active_player(self, player_id: str):
        if player_id not in self.players:
            raise ValueError('Unknown player')
        self.players[player_id].last_active = time.time()

    def to_public(self, player_id: Optional[str] = None):
        with self.lock:
            return {
                'round': self.round_index,
                'status': self.status,
                'prompt': self.prompt,
                'players': [p.to_public() for p in self.players.values()],
                'you': self.players.get(player_id).name if player_id and player_id in self.players else None,
                'submitted_count': sum(1 for p in self.players.values() if p.current_word is not None),
                'decided_count': sum(1 for p in self.players.values() if p.decision in ('same','again')),
                'history': self.words_history,
                'max_rounds': self.max_rounds,
                'finished_reason': self.finished_reason,
                'round_limit_locked': self.game_started(),
            }

    def set_round_limit(self, limit: Optional[int]):
        """Set maximum rounds. None or 0 disables the limit.

        If limit is lower than current round_index and game not finished, and
        we already exceeded it, finish immediately with reason 'round_limit'.
        """
        with self.lock:
            if limit is not None:
                if isinstance(limit, (int,)):
                    if limit < 0:
                        raise ValueError('Limit must be >= 0')
                else:
                    raise ValueError('Limit must be integer')
            self.max_rounds = None if (limit is None or limit == 0) else int(limit)
            # If active and limit now below current progress, end.
            if self.max_rounds is not None and self.round_index > self.max_rounds and self.status != 'finished':
                self.status = 'finished'
                self.finished_reason = 'round_limit'

class ChatLogger:
    """Centralized CSV logger for ALL rooms including room_id column.

    Creates daily file chat_YYYY-MM-DD.csv with columns:
        room_id, name, id, exact time, message

    If an existing file without the room_id column is found, it is rotated
    to *.legacy once per process start to avoid format mismatch.
    """
    def __init__(self, base_dir: Optional[str] = None):
        base_dir = base_dir or os.getenv('GAME_CHAT_LOG_DIR', 'chat_logs')
        self.base = Path(base_dir)
        try:
            self.base.mkdir(parents=True, exist_ok=True)
        except Exception:
            self.base = None  # type: ignore
        self._header_cache = set()  # track which files have proper header
        self._lock = threading.Lock()

    def _daily_file(self, ts: float) -> Optional[Path]:
        if not self.base:
            return None
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return self.base / f"chat_{dt.date().isoformat()}.csv"

    def _ensure_header(self, path: Path):
        if path in self._header_cache:
            return
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8-sig') as f:
                    first = f.readline().strip().split(',')
                if first and 'room_id' not in first:
                    # rotate legacy file
                    legacy = path.with_suffix('.legacy.csv')
                    try: path.rename(legacy)
                    except Exception: pass
                else:
                    self._header_cache.add(path)
                    return
            except Exception:
                pass
        # write fresh header
        try:
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['room_id','name','id','exact time','message'])
            self._header_cache.add(path)
        except Exception:
            pass

    def log(self, room_id: int, name: str, player_uuid: str, ts: float, text: str):
        try:
            file_path = self._daily_file(ts)
            if not file_path:
                return
            with self._lock:
                self._ensure_header(file_path)
                iso_time = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                with open(file_path, 'a', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([room_id, name, player_uuid, iso_time, text])
        except Exception:
            pass

chat_logger = ChatLogger()

# ----------------------------- Player Join Logger ------------------------- #
class PlayerJoinLogger:
    """CSV logger for player joins.

    File: log/players.csv (UTF-8 BOM for Excel friendliness)
    Columns: player name, player id, exact time (ISO UTC), ip, room id

    The 'player id' is a persistent device_id cookie, stable per browser/device.
    The IP attempts to use X-Forwarded-For (if behind proxy) falling back to
    request.remote_addr. Adding room id lets you analyze per-room activity.
    If an older file exists without the new 'room id' column, it is rotated
    to players.legacy.csv once so a clean header can be written.
    """
    def __init__(self, base_dir: Optional[str] = None):
        self.base = Path(base_dir or os.path.join(os.path.dirname(__file__), 'log'))
        try:
            self.base.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self.path = self.base / 'players.csv'
        self._lock = threading.Lock()
        self._header_written = False
        self._ensure_header()

    def _ensure_header(self):
        if self._header_written:
            return
        if self.path.exists():
            try:
                with open(self.path, 'r', encoding='utf-8-sig') as f:
                    first_line = f.readline().strip()
                cols = [c.strip().lower() for c in first_line.split(',')] if first_line else []
                # Detect legacy header (without room id)
                if cols and 'room id' in cols:
                    self._header_written = True
                    return
                elif cols:
                    # rotate legacy file
                    legacy = self.path.with_suffix('.legacy.csv')
                    try: self.path.rename(legacy)
                    except Exception: pass
            except Exception:
                pass
        try:
            with open(self.path, 'w', encoding='utf-8-sig', newline='') as f:
                w = csv.writer(f)
                w.writerow(['player name','player id','exact time','ip','room id'])
            self._header_written = True
        except Exception:
            pass

    def log(self, player_name: str, player_id: str, join_ts: float, ip: str, room_id: int):
        try:
            iso_time = datetime.fromtimestamp(join_ts, tz=timezone.utc).isoformat()
            with self._lock:
                self._ensure_header()
                with open(self.path, 'a', encoding='utf-8-sig', newline='') as f:
                    w = csv.writer(f)
                    w.writerow([player_name, player_id, iso_time, ip, room_id])
        except Exception:
            pass

player_join_logger = PlayerJoinLogger()

class Room:
    def __init__(self, room_id: int):
        self.room_id = room_id
        self.game = GameState()
        self.chat = None  # assigned after ChatRoom class defined
        # Reporter commentary (list of dicts: {id:int, persona:str, text:str, ts:float, round:int})
        self.reporters: List[Dict[str, Any]] = []
        self._reporter_counter = 0
        # Active reporter personas (ordered: reporter1 then reporter2). Configurable
        # only before the game starts. Default to first two from dynamic list.
        self.reporter_personas = REPORTER_PERSONAS[:2]

    def set_reporter_personas(self, personas: List[str]):
        """Configure up to two distinct reporter personas (order matters).

        Previous strict requirement (exactly two) is relaxed so users can
        deselect back to 0 or 1 before the game starts. Generation logic will
        simply create commentary for whichever personas are currently chosen
        (0, 1, or 2). Once a first word is submitted (game_started), the list
        becomes locked until a reset.
        """
        if self.game.game_started():
            raise ValueError('Reporters locked (game already started). Reset game to change.')
        # Sanitize list: keep order, unique, valid, max 2
        cleaned: List[str] = []
        for p in personas:
            p = (p or '').strip()
            if p and p in REPORTER_PERSONAS and p not in cleaned:
                cleaned.append(p)
            if len(cleaned) == 2:
                break
        self.reporter_personas = cleaned

    def add_reporter_comment(self, persona: str, text: str, round_index: int):
        # Sanitize: some LLM replies repeat the persona name at the start (e.g., "Robin Williams: ...").
        # We remove a leading persona token (case-insensitive) plus trailing punctuation so UI does not show duplicate names.
        try:
            raw = (text or '').strip()
            p_norm = persona.lower().strip()
            t_norm = raw.lower().lstrip()
            if t_norm.startswith(p_norm):
                # slice off persona length
                trimmed = raw[len(raw) - len(raw.lstrip()):]  # account for original leading spaces
                trimmed = trimmed[len(persona):].lstrip()  # remove persona
                # remove leading punctuation tokens
                while trimmed and trimmed[0] in ':：-—–>»«._ ':
                    trimmed = trimmed[1:]
                raw = trimmed.lstrip()
            if not raw:
                raw = text.strip() if text else ''
        except Exception:
            raw = (text or '').strip()
        self._reporter_counter += 1
        entry = {
            'id': self._reporter_counter,
            'persona': persona,
            'text': raw,
            'ts': time.time(),
            'round': round_index,
        }
        self.reporters.append(entry)
        try:
            reporter_logger.log(self.room_id, entry)
        except Exception:
            pass

class ReporterLogger:
    """CSV logger for reporter commentary (per day).

    Files: log/report_YYYY-MM-DD.csv with UTF-8 BOM so Persian renders in Excel.
    Columns: name,time,text,round,room_id
    """
    def __init__(self, base_dir: Optional[str] = None):
        self.base = Path(base_dir or os.path.join(os.path.dirname(__file__), 'log'))
        try:
            self.base.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self._header_written: set[Path] = set()
        self._lock = threading.Lock()

    def _file_for(self, ts: float) -> Path:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return self.base / f"report_{dt.date().isoformat()}.csv"

    def _ensure_header(self, path: Path):
        if path in self._header_written:
            return
        try:
            if not path.exists():
                with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['name','time','text','round','room_id'])
            self._header_written.add(path)
        except Exception:
            pass

    def log(self, room_id: int, entry: Dict[str, Any]):
        ts = entry.get('ts', time.time())
        path = self._file_for(ts)
        with self._lock:
            self._ensure_header(path)
            try:
                with open(path, 'a', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    iso_t = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                    writer.writerow([
                        entry.get('persona',''),
                        iso_t,
                        entry.get('text',''),
                        entry.get('round',''),
                        room_id,
                    ])
            except Exception:
                pass

reporter_logger = ReporterLogger()

class MultiRoomManager:
    def __init__(self, room_ids: List[int]):
        self.rooms: Dict[int, Room] = {rid: Room(rid) for rid in room_ids}
        # After ChatRoom definition, we will attach chats.

    def get(self, room_id: int) -> Room:
        if room_id not in self.rooms:
            raise ValueError('Invalid room')
        return self.rooms[room_id]

    def join(self, passcode: str, player_name: str) -> tuple[int, str]:
        if passcode not in PASSCODES:
            raise ValueError('Invalid password')
        rid = PASSCODES[passcode]
        room = self.get(rid)
        # enforce max 2 players per requirement
        with room.game.lock:
            active_players = len(room.game.players)
            if active_players >= 2 and all(p.name != player_name for p in room.game.players.values()):
                raise ValueError('Room is full (2 players already).')
        pid = room.game.join(player_name)
        return rid, pid

multi = MultiRoomManager(list({v for v in PASSCODES.values()}))

# ----------------------------- Chat State ---------------------------------- #
class ChatRoom:
    """Simple in-memory chat buffer with optional CSV persistence per day.

    A CSV file is created (if not exists) for each day with filename pattern:
        chat_YYYY-MM-DD.csv

    Columns: name, id, exact time, message
    - "id" here refers to the player's UUID (for humans) or a static token for the bot.
    - Time is stored in ISO-8601 UTC (e.g. 2025-09-21T12:34:56.789012+00:00)
    - Encoding: UTF-8 with BOM (utf-8-sig) so Persian characters display nicely in Excel.
    """
    def __init__(self, room_id: int, max_messages: int = 500):
        self.lock = threading.Lock()
        self.messages: deque[Dict[str, Any]] = deque(maxlen=max_messages)
        self.counter = 0  # simple incremental id
        # A generation marker that increments whenever the chat is globally cleared.
        # Clients can detect a generation jump and wipe any locally cached history.
        self.generation = 1
        self.room_id = room_id

    # ------------------- Internal helpers ---------------------------------
    def _log_message(self, name: str, player_uuid: str, ts: float, text: str):
        # delegate to central logger including room id
        chat_logger.log(self.room_id, name, player_uuid, ts, text)

    # ------------------- Public API --------------------------------------
    def post(self, player: Player, text: str, player_uuid: Optional[str] = None, reply_to: Optional[int] = None) -> Dict[str, Any]:
        text = (text or '').strip()
        if not text:
            raise ValueError('Empty message')
        if len(text) > 500:
            text = text[:500]
        with self.lock:
            self.counter += 1
            parent: Optional[Dict[str, Any]] = None
            if reply_to is not None:
                for m in self.messages:
                    if m['id'] == reply_to:
                        parent = m
                        break
                if parent is None:
                    reply_to = None
            ts_val = time.time()
            msg = {
                'id': self.counter,
                'player': player.name,
                'text': text,
                'ts': ts_val,
                'reply_to': reply_to,
                'reply_preview': {
                    'id': parent['id'],
                    'player': parent['player'],
                    'text': parent['text'][:120]
                } if parent else None,
                'gen': self.generation,
            }
            self.messages.append(msg)
            # Logging (player_uuid may be None if older code paths call without it)
            self._log_message(player.name, player_uuid or 'unknown', ts_val, text)
            return msg

    def post_bot(self, bot_name: str, text: str, bot_id: str = 'llm') -> Dict[str, Any]:
        """Post a message as an LLM bot (also logged)."""
        if not text.strip():
            text = "(پیامی برای گفتن نداشت)"
        with self.lock:
            self.counter += 1
            ts_val = time.time()
            msg = {
                'id': self.counter,
                'player': bot_name,
                'text': text.strip()[:500],
                'ts': ts_val,
                'reply_to': None,
                'reply_preview': None,
                'gen': self.generation,
            }
            self.messages.append(msg)
            self._log_message(bot_name, bot_id, ts_val, msg['text'])
            return msg

    def since(self, last_id: int) -> List[Dict[str, Any]]:
        with self.lock:
            if last_id <= 0:
                return list(self.messages)
            return [m for m in self.messages if m['id'] > last_id]

    def clear(self):
        """Globally clear all chat history (in-memory only) and increment generation.

        Log files are intentionally not deleted (they are append-only audit trail).
        Any future messages will have a new generation number so clients can
        detect that previously cached messages (with older gen) should be discarded.
        """
        with self.lock:
            self.messages.clear()
            # Do not reset counter to avoid accidental id reuse if other threads race.
            # Instead we keep incrementing; generation is the authoritative reset marker.
            self.generation += 1

# Attach per-room ChatRoom instances
for _rid, _room in multi.rooms.items():
    _room.chat = ChatRoom(_rid)

# ----------------------------- Routes -------------------------------------- #
@app.route('/')
def index():
    return redirect(url_for('join_page'))

@app.route('/join', methods=['GET', 'POST'])
def join_page():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        password = request.form.get('password','').strip()
        if not name:
            return render_template('join.html', error='Name required', passcodes=list(PASSCODES.keys()), allowed_reporters=REPORTER_PERSONAS, default_reporters=REPORTER_PERSONAS[:2])
        # Obtain / create a persistent device identifier (cookie survives multiple joins)
        device_id = request.cookies.get('device_id')
        new_device_id = False
        if not device_id:
            device_id = str(uuid.uuid4())
            new_device_id = True
        try:
            room_id, pid = multi.join(password, name)
        except ValueError as ve:
            return render_template('join.html', error=str(ve), passcodes=list(PASSCODES.keys()), allowed_reporters=REPORTER_PERSONAS, default_reporters=REPORTER_PERSONAS[:2])
        # Log player join (after successful room join & id creation)
        try:
            # Derive IP (supports reverse proxy setups)
            forwarded = request.headers.get('X-Forwarded-For', '')
            ip = forwarded.split(',')[0].strip() if forwarded else (request.remote_addr or 'unknown')
            # Use stable device_id for correlation instead of transient session pid
            player_join_logger.log(name, device_id, time.time(), ip, room_id)
        except Exception:
            pass
        resp = redirect(url_for('game_page'))
        resp.set_cookie('player_id', pid, path='/', samesite='Lax')
        resp.set_cookie('room_id', str(room_id), path='/', samesite='Lax')
        if new_device_id:
            # One year expiry for device tracking (adjust as desired)
            one_year = 60 * 60 * 24 * 365
            resp.set_cookie('device_id', device_id, path='/', max_age=one_year, samesite='Lax')
        return resp
    return render_template('join.html', passcodes=list(PASSCODES.keys()), allowed_reporters=REPORTER_PERSONAS, default_reporters=REPORTER_PERSONAS[:2])

@app.route('/game')
def game_page():
    pid = request.cookies.get('player_id')
    rid = request.cookies.get('room_id')
    if not pid or not rid:
        return redirect(url_for('join_page'))
    try:
        rid_int = int(rid)
        room = multi.get(rid_int)
        # ensure player still present (may have been removed)
        if pid not in room.game.players:
            return redirect(url_for('join_page'))
    except Exception:
        return redirect(url_for('join_page'))
    return render_template('game.html', room_id=rid_int)

@app.route('/api/state')
def api_state():
    pid = request.cookies.get('player_id')
    rid = request.cookies.get('room_id')
    try:
        rid_int = int(rid) if rid else None
    except Exception:
        rid_int = None
    if not rid_int or rid_int not in multi.rooms:
        return jsonify({'ok': False, 'error': 'Invalid room'}), 400
    room = multi.get(rid_int)
    # Mark requester active & prune inactive players defensively
    if pid and pid in room.game.players:
        room.game.players[pid].last_active = time.time()
    # prune outside lock safe because method acquires lock internally
    # Prune players who have been inactive beyond configured timeout.
    room.game.prune_inactive(timeout=INACTIVITY_TIMEOUT)
    state = room.game.to_public(pid)
    state['room_id'] = rid_int
    state['players_in_room'] = [p.name for p in room.game.players.values()]
    # Include ONLY reporter messages for the current round (hide prior rounds from UI)
    # New behavior: show rolling window of last 2 comments per active persona (max 4 total)
    active_personas = getattr(room, 'reporter_personas', [])[:2]
    selected: List[Dict[str, Any]] = []
    if active_personas:
        for persona in active_personas:
            # collect last two comments for this persona
            persona_comments = [c for c in room.reporters if c.get('persona') == persona]
            tail = persona_comments[-2:]
            selected.extend(tail)
    # Sort by id (or timestamp) to maintain chronological order in UI
    selected.sort(key=lambda x: x.get('id', 0))
    state['reporter_comments'] = selected
    # Reporter personas & lock flag
    state['reporter_personas'] = getattr(room, 'reporter_personas', REPORTER_PERSONAS[:2])
    state['reporter_lock'] = room.game.game_started()
    state['allowed_reporter_personas'] = REPORTER_PERSONAS
    return jsonify(state)

@app.route('/api/submit_word', methods=['POST'])
def api_submit_word():
    pid = request.cookies.get('player_id')
    rid = request.cookies.get('room_id')
    data = request.get_json(force=True)
    word = data.get('word','')
    try:
        if not rid:
            raise ValueError('Missing room id')
        room = multi.get(int(rid))
        if not pid or pid not in room.game.players:
            raise ValueError('Not joined (missing player id). Re-join the game.')
        room.game.submit_word(pid, word)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@app.route('/api/decision', methods=['POST'])
def api_decision():
    pid = request.cookies.get('player_id')
    rid = request.cookies.get('room_id')
    data = request.get_json(force=True)
    decision = data.get('decision','')
    try:
        room = multi.get(int(rid))
        room.game.submit_decision(pid, decision)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@app.route('/api/prompt', methods=['POST'])
def api_prompt():
    data = request.get_json(force=True)
    rid = request.cookies.get('room_id')
    prompt = data.get('prompt','')
    try:
        room = multi.get(int(rid))
        room.game.set_prompt(prompt)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@app.route('/api/round_limit', methods=['POST'])
def api_round_limit():
    """Set or clear the maximum round limit.

    JSON body: { "limit": <int|null> }
      limit <=0 or null disables the limit.
    """
    rid = request.cookies.get('room_id')
    data = request.get_json(force=True)
    limit = data.get('limit', None)
    try:
        room = multi.get(int(rid))
        # Enforce: cannot change after the game has started (first submission)
        if not room.game.can_adjust_round_limit():
            return jsonify({'ok': False, 'error': 'Round limit locked (game already started). Reset game to change.'}), 400
        # Accept null / undefined -> remove limit
        if limit in (None, ''):
            coerce = None
        else:
            coerce = int(limit)
        room.game.set_round_limit(coerce)
        return jsonify({'ok': True, 'max_rounds': room.game.max_rounds, 'round_limit_locked': room.game.game_started()})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@app.route('/api/reset', methods=['POST'])
def api_reset():
    rid = request.cookies.get('room_id')
    try:
        room = multi.get(int(rid))
        # Soft reset: only game state & history. Chat MUST be preserved.
        room.game.reset()
        # Clear reporter comments & allow fresh selection
        room.reporters.clear()
        room._reporter_counter = 0
        # Do NOT force personas list; leave previous selection so user can deselect/change.
        return jsonify({'ok': True, 'chat_cleared': False, 'reporters_cleared': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@app.route('/api/reset_hard', methods=['POST'])
def api_reset_hard():
    """Hard reset: reset game state AND clear the room chat.

    Previously /api/reset also cleared the chat; that behavior was split so that
    the regular "Play Again" button can keep conversation history, while an
    explicit Hard Reset button (admin/trust model) can wipe everything.
    """
    rid = request.cookies.get('room_id')
    try:
        room = multi.get(int(rid))
        room.game.reset()
        room.chat.clear()
        room.reporters.clear()
        room._reporter_counter = 0
        # Return new generation so clients can discard their cached messages
        return jsonify({'ok': True, 'chat_cleared': True, 'generation': room.chat.generation, 'reporters_cleared': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

# ----------------------------- Chat Routes --------------------------------- #
@app.route('/api/chat/send', methods=['POST'])
def api_chat_send():
    pid = request.cookies.get('player_id')
    rid = request.cookies.get('room_id')
    try:
        room = multi.get(int(rid))
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid room'}), 403
    if not pid or pid not in room.game.players:
        return jsonify({'ok': False, 'error': 'Not joined'}), 403
    data = request.get_json(force=True)
    text = data.get('text', '')
    reply_to = data.get('reply_to')
    if reply_to is not None:
        try:
            reply_to = int(reply_to)
        except Exception:
            reply_to = None
    try:
        msg = room.chat.post(room.game.players[pid], text, player_uuid=pid, reply_to=reply_to)
        return jsonify({'ok': True, 'message': msg})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@app.route('/api/chat/since')
def api_chat_since():
    pid = request.cookies.get('player_id')
    rid = request.cookies.get('room_id')
    try:
        room = multi.get(int(rid))
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid room'}), 403
    if not pid or pid not in room.game.players:
        return jsonify({'ok': False, 'error': 'Not joined'}), 403
    try:
        last_id = int(request.args.get('after', '0'))
    except ValueError:
        last_id = 0
    player_threshold = room.game.players[pid].chat_reset_after_id if pid in room.game.players else 0
    effective_after = max(last_id, player_threshold)
    msgs = room.chat.since(effective_after)
    return jsonify({'ok': True, 'messages': msgs, 'generation': room.chat.generation})

@app.route('/api/chat/llm_talk', methods=['POST'])
def api_chat_llm_talk():
    pid = request.cookies.get('player_id')
    rid = request.cookies.get('room_id')
    try:
        room = multi.get(int(rid))
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid room'}), 403
    if not pid or pid not in room.game.players:
        return jsonify({'ok': False, 'error': 'Not joined'}), 403
    with room.chat.lock:
        recent = list(room.chat.messages)
        simple = [{ 'name': m['player'], 'text': m['text'] } for m in recent]
    # Persona selection (optional) from request JSON body.
    persona = None
    try:
        data = request.get_json(silent=True) or {}
        persona = data.get('persona')
    except Exception:
        persona = None
    if not persona or persona not in CHAT_PERSONAS:
        persona = CHAT_PERSONAS[0] if CHAT_PERSONAS else ''
    if not CHAT_PERSONAS:
        reply_text = "(LLM persona prompts not configured)"
    else:
        try:
            reply_text = generate_llm_reply(simple, persona)
        except Exception as e:
            reply_text = f"(Generation Error {e})"
    bot_name = persona
    bot_msg = room.chat.post_bot(bot_name, reply_text)
    return jsonify({'ok': True, 'message': bot_msg})

@app.route('/api/chat/reset_self', methods=['POST'])
def api_chat_reset_self():
    pid = request.cookies.get('player_id')
    rid = request.cookies.get('room_id')
    try:
        room = multi.get(int(rid))
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid room'}), 403
    if not pid or pid not in room.game.players:
        return jsonify({'ok': False, 'error': 'Not joined'}), 403
    with room.chat.lock:
        cutoff = room.chat.counter
    room.game.players[pid].chat_reset_after_id = cutoff
    return jsonify({'ok': True, 'after': cutoff})

@app.route('/api/chat/reset_all', methods=['POST'])
def api_chat_reset_all():
    pid = request.cookies.get('player_id')
    rid = request.cookies.get('room_id')
    try:
        room = multi.get(int(rid))
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid room'}), 403
    if not pid or pid not in room.game.players:
        return jsonify({'ok': False, 'error': 'Not joined'}), 403
    room.chat.clear()
    for p in room.game.players.values():
        p.chat_reset_after_id = 0
    return jsonify({'ok': True, 'generation': room.chat.generation})

# ----------------------------- Chat Personas API -------------------------- #
@app.route('/api/chat/personas', methods=['GET'])
def api_chat_personas():
    """Return allowed chat personas and suggested default.

    This allows the front-end to build the persona drawer dynamically from
    the keys present in llm_combined/prompts_chat.py without hardcoding.
    """
    allowed = CHAT_PERSONAS
    default = allowed[0] if allowed else 'Bot'
    return jsonify({'ok': True, 'allowed': allowed, 'default': default})

@app.route('/api/exit', methods=['POST'])
def api_exit():
    pid = request.cookies.get('player_id')
    rid = request.cookies.get('room_id')
    if pid and rid and rid.isdigit():
        try:
            room = multi.get(int(rid))
            room.game.leave(pid)
        except Exception:
            pass
    resp = jsonify({'ok': True})
    resp.set_cookie('player_id', '', expires=0, path='/', samesite='Lax')
    resp.set_cookie('room_id', '', expires=0, path='/', samesite='Lax')
    return resp

# ---------------- Reporter Persona Routes ----------------- #
@app.route('/api/reporters', methods=['GET'])
def api_get_reporters():
    rid = request.cookies.get('room_id')
    try:
        room = multi.get(int(rid))
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid room'}), 400
    return jsonify({'ok': True, 'personas': room.reporter_personas, 'allowed': REPORTER_PERSONAS, 'locked': room.game.game_started()})

@app.route('/api/reporters', methods=['POST'])
def api_set_reporters():
    rid = request.cookies.get('room_id')
    try:
        room = multi.get(int(rid))
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid room'}), 400
    data = request.get_json(force=True, silent=True) or {}
    personas = data.get('personas') or []
    if not isinstance(personas, list):
        return jsonify({'ok': False, 'error': 'personas must be list'}), 400
    try:
        room.set_reporter_personas(personas)
        return jsonify({'ok': True, 'personas': room.reporter_personas})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

# ----------------------------- Asset Routes (favicon / logo) ------------- #
@app.route('/favicon.ico')
@app.route('/favicon.png')
def favicon_png():
    """Serve the square favicon (with background)."""
    return send_from_directory(os.path.dirname(__file__), 'logo-site.png')

@app.route('/logo-inline.png')
def logo_inline():
    """Serve transparent logo for inline usage (header)."""
    return send_from_directory(os.path.dirname(__file__), 'logo-no-background.png')

if __name__ == '__main__':
    # For local dev only; in production use a WSGI server (gunicorn, etc.)
    app.run(host='0.0.0.0', port=5052, debug=True)
