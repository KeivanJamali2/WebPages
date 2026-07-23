"""Logging utilities for Word Guess game.

Provides:
 - generate_game_id(): short unique id (k-lexic) for each started game
 - append_csv_row(path, header, row_dict): create-if-missing with header
 - helper functions to build filenames per requirements

Filenames (examples):
  2025-09-24__gX3KF2__12-30-05__Ali-Reza__room1__سیب-qa.csv
  2025-09-24__gX3KF2__Ali-Reza__room1__سیب-chat.csv

We intentionally separate real time (HH-MM-SS) only in QA file name (as requested pattern had time). Chat file omits start time segment for stability.

All files stored in ./logs relative to this module.
"""
from __future__ import annotations

import csv
import os
import time
import uuid
import threading
from typing import Sequence

LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

_csv_lock = threading.Lock()

# ---------------- ID generation ---------------- #

def generate_game_id() -> str:
    # 8 char base32-ish slug (no padding) using uuid4 int
    return uuid.uuid4().hex[:8]

# ---------------- Generic CSV append ---------------- #

def append_csv_row(path: str, header: Sequence[str], row: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with _csv_lock:
        file_exists = os.path.exists(path)
        with open(path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(header))
            if not file_exists:
                writer.writeheader()
            # filter to declared fields only (drop extras silently)
            safe = {k: row.get(k, '') for k in header}
            writer.writerow(safe)

# ---------------- Filename builders ---------------- #

def _sanitize_token(token: str) -> str:
    token = token.strip().replace(' ', '-')
    # remove path separators / colon like characters to be safe
    bad = ['/', '\\', ':', ';', '..']
    for b in bad:
        token = token.replace(b, '')
    return token[:40]


def build_players_token(players: Sequence[str]) -> str:
    return '-'.join(_sanitize_token(p) for p in players)


def build_room_token(room_id: int, room_name: str) -> str:
    # prefer numeric id for stability
    base = f"room{room_id}"
    return _sanitize_token(base)


def qa_filename(game_id: str, players: Sequence[str], room_id: int, room_name: str, real_word: str, start_ts: int) -> str:
    date_part = time.strftime('%Y-%m-%d', time.localtime(start_ts))
    time_part = time.strftime('%H-%M-%S', time.localtime(start_ts))
    return os.path.join(LOG_DIR, f"{date_part}__{game_id}__{time_part}__{build_players_token(players)}__{build_room_token(room_id, room_name)}__{_sanitize_token(real_word)}-qa.csv")


def chat_filename(game_id: str, players: Sequence[str], room_id: int, room_name: str, real_word: str, start_ts: int) -> str:
    date_part = time.strftime('%Y-%m-%d', time.localtime(start_ts))
    return os.path.join(LOG_DIR, f"{date_part}__{game_id}__{build_players_token(players)}__{build_room_token(room_id, room_name)}__{_sanitize_token(real_word)}-chat.csv")

# ---------------- Players master log ---------------- #

PLAYERS_CSV = os.path.join(LOG_DIR, 'players.csv')
PLAYERS_HEADER = ['ts', 'player_name', 'session_id', 'room_id', 'room_name']


def log_player_join(player_name: str, session_id: str, room_id: int, room_name: str):
    append_csv_row(PLAYERS_CSV, PLAYERS_HEADER, {
        'ts': int(time.time()),
        'player_name': player_name,
        'session_id': session_id,
        'room_id': room_id,
        'room_name': room_name,
    })

# ---------------- Game scoped file state ---------------- #

class GameFileBundle:
    """Keeps track of per-game file paths so handlers can append.

    Stored on Room after game start.
    """
    def __init__(self, game_id: str, players: Sequence[str], room_id: int, room_name: str, real_word: str):
        self.game_id = game_id
        self.players = list(players)
        self.room_id = room_id
        self.room_name = room_name
        self.real_word = real_word
        self.started_at = int(time.time())
        self.qa_path = qa_filename(game_id, players, room_id, room_name, real_word, self.started_at)
        self.chat_path = chat_filename(game_id, players, room_id, room_name, real_word, self.started_at)
        # Pre-create files with headers so they exist even if no data yet
        append_csv_row(self.qa_path, QA_HEADER, {})
        append_csv_row(self.chat_path, CHAT_HEADER, {})

QA_HEADER = ['ts', 'game_id', 'round', 'phase', 'player', 'action', 'text', 'answer_or_correct']
CHAT_HEADER = ['ts', 'game_id', 'round', 'sender', 'message', 'is_assistant']


def log_question(bundle: GameFileBundle, round_no: int, phase: str, player: str, question: str, answer_bool: bool):
    append_csv_row(bundle.qa_path, QA_HEADER, {
        'ts': int(time.time()),
        'game_id': bundle.game_id,
        'round': round_no,
        'phase': phase,
        'player': player,
        'action': 'Q',
        'text': question,
        'answer_or_correct': int(bool(answer_bool)),
    })


def log_guess(bundle: GameFileBundle, round_no: int, phase: str, player: str, guess: str, correct: bool):
    append_csv_row(bundle.qa_path, QA_HEADER, {
        'ts': int(time.time()),
        'game_id': bundle.game_id,
        'round': round_no,
        'phase': phase,
        'player': player,
        'action': 'G',
        'text': guess,
        'answer_or_correct': int(bool(correct)),
    })


def log_chat(bundle: GameFileBundle, round_no: int, sender: str, message: str, is_assistant: bool):
    append_csv_row(bundle.chat_path, CHAT_HEADER, {
        'ts': int(time.time()),
        'game_id': bundle.game_id,
        'round': round_no,
        'sender': sender,
        'message': message,
        'is_assistant': int(is_assistant),
    })
