"""Core game logic for the Word Guess web application.

Enhanced version supports:
 - Two players (configurable names / IDs)
 - Multiple phases (QUESTION -> DISCUSSION -> GUESS) repeating across rounds
 - Dynamic per-round limits (questions per player, guesses per player)
 - State serialization (for storing in session / DB between HTTP requests)
 - Dependency injection for the LLM reply function (simplifies testing)
 - Backward compatibility with the earlier single-phase API (ask_question / make_guess)

Intended future web usage pattern (high-level):
 1. Create a Game and store its serialized state in server-side session/cache.
 2. On each HTTP request, deserialize, apply action, re-serialize.
 3. Transition to DISCUSSION phase triggers UI to enable player chat (handled externally).
 4. After discussion, server calls advance_phase() to allow guesses.
 5. If no winner after guesses, start a new round with increased / altered limits.

You can adapt round progression rules easily by customizing next_round_config().
"""

from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from enum import Enum, auto
from typing import Callable, Dict, Optional, Any, List


from llm_combined.llm_game import generate_llm_reply  # type: ignore
from words import get_random_word  # type: ignore


class Phase(Enum):
    QUESTION = auto()
    DISCUSSION = auto()  # (handled externally, we just mark phase)
    GUESS = auto()
    COMPLETED = auto()


@dataclass
class RoundLimits:
    questions_per_player: int
    guesses_per_player: int


@dataclass
class PlayerState:
    name: str
    questions_used: int = 0
    guesses_used: int = 0


class Game:
    """Represents one multi-round two-player match.

    Backward compatibility:
        - ask_question(question) assumes player index 0.
        - make_guess(guess, player_name) still works.
    """

    def __init__(
        self,
        player_names: Optional[List[str]] = None,
        initial_limits: RoundLimits | None = None,
        llm_reply_fn: Callable[[str, str], str] = None,
        word: Optional[str] = None,
        max_rounds: int = 5,
    ) -> None:
        if player_names is None:
            player_names = ["Player 1", "Player 2"]
        if len(player_names) != 2:
            raise ValueError("Exactly two players are required.")

        self.players: Dict[str, PlayerState] = {p: PlayerState(name=p) for p in player_names}
        self.player_order: List[str] = player_names[:]  # preserve order
        self.word, self.description = (word, word) or get_random_word()
        self.round_number: int = 1
        self.max_rounds = max_rounds
        self.phase: Phase = Phase.QUESTION
        self.limits: RoundLimits = initial_limits or RoundLimits(questions_per_player=3, guesses_per_player=1)
        self.llm_reply_fn = llm_reply_fn or generate_llm_reply
        self.winner: Optional[str] = None
        self.is_over: bool = False

    # ---------------------------- Phase & Round Management ---------------------------- #
    def _check_completed(self) -> None:
        if self.winner is not None:
            self.phase = Phase.COMPLETED
            self.is_over = True

    def next_round_config(self, previous: RoundLimits) -> RoundLimits:
        """Business rule: escalate difficulty / allowance per round.

        Default: +1 question per player every two rounds, +1 guess on odd rounds after first.
        Adjust as desired.
        """
        # Simple example rule; can be replaced
        q = previous.questions_per_player + (1 if (self.round_number % 2 == 0) else 0)
        g = previous.guesses_per_player + (1 if (self.round_number > 1 and self.round_number % 2 == 1) else 0)
        return RoundLimits(q, g)

    def start_new_round(self) -> None:
        if self.round_number >= self.max_rounds:
            self.is_over = True
            self.phase = Phase.COMPLETED
            return
        self.round_number += 1
        self.limits = self.next_round_config(self.limits)
        for ps in self.players.values():
            ps.questions_used = 0
            ps.guesses_used = 0
        self.phase = Phase.QUESTION

    def advance_phase(self) -> None:
        if self.is_over:
            return
        if self.phase == Phase.QUESTION:
            self.phase = Phase.DISCUSSION
        elif self.phase == Phase.DISCUSSION:
            self.phase = Phase.GUESS
        elif self.phase == Phase.GUESS:
            # end of round if no winner
            self.start_new_round()

    # ---------------------------- Core Actions ---------------------------- #
    def ask_question(self, question: str, player_name: Optional[str] = None) -> str:  # backward compatible wrapper
        if player_name is None:
            # fallback to first player for legacy calls
            player_name = self.player_order[0]
        if self.is_over:
            return "The game is over."
        if self.phase != Phase.QUESTION:
            return f"Not in QUESTION phase (current phase: {self.phase.name})."
        if player_name not in self.players:
            return "Unknown player."
        ps = self.players[player_name]
        if ps.questions_used >= self.limits.questions_per_player:
            return f"{player_name} has no questions left this round."

        answer = self.llm_reply_fn(question, {self.word: self.description})
        ps.questions_used += 1

        # Check if all players exhausted questions -> move to discussion automatically
        if all(p.questions_used >= self.limits.questions_per_player for p in self.players.values()):
            self.phase = Phase.DISCUSSION
        return answer

    def make_guess(self, guess: str, player_name: str) -> str:
        if self.is_over:
            return "The game is over."
        if player_name not in self.players:
            return "Unknown player."
        if self.phase not in (Phase.GUESS, Phase.QUESTION):  # allow early guess during questions if desired
            return f"Not allowed to guess during {self.phase.name} phase."
        ps = self.players[player_name]
        if ps.guesses_used >= self.limits.guesses_per_player:
            return f"{player_name} has no guesses left this round."

        ps.guesses_used += 1
        if guess.strip().lower() == self.word.lower():
            self.winner = player_name
            self._check_completed()
            return f"Correct! {player_name} wins! The word was '{self.word}'."
        else:
            # If all guesses exhausted for all players and phase==GUESS -> new round
            if self.phase == Phase.GUESS and all(
                p.guesses_used >= self.limits.guesses_per_player for p in self.players.values()
            ):
                self.start_new_round()
            return "Incorrect guess."

    # ---------------------------- Introspection & Serialization ---------------------------- #
    def to_dict(self) -> Dict[str, Any]:
        return {
            "word": self.word,
            "round_number": self.round_number,
            "phase": self.phase.name,
            "limits": asdict(self.limits),
            "players": {k: asdict(v) for k, v in self.players.items()},
            "player_order": self.player_order,
            "winner": self.winner,
            "is_over": self.is_over,
            "max_rounds": self.max_rounds,
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        llm_reply_fn: Callable[[str, str], str] = None,
    ) -> "Game":
        game = cls(
            player_names=data["player_order"],
            initial_limits=RoundLimits(**data["limits"]),
            llm_reply_fn=llm_reply_fn or generate_llm_reply,
            word=data["word"],
            max_rounds=data.get("max_rounds", 5),
        )
        game.round_number = data["round_number"]
        game.phase = Phase[data["phase"]]
        game.players = {
            name: PlayerState(**pstate) for name, pstate in data["players"].items()
        }
        game.player_order = data["player_order"]
        game.winner = data.get("winner")
        game.is_over = data.get("is_over", False)
        return game

    # ---------------------------- Convenience ---------------------------- #
    def remaining_questions(self, player_name: str) -> int:
        ps = self.players[player_name]
        return self.limits.questions_per_player - ps.questions_used

    def remaining_guesses(self, player_name: str) -> int:
        ps = self.players[player_name]
        return self.limits.guesses_per_player - ps.guesses_used

    def summary(self) -> Dict[str, Any]:
        return {
            "round": self.round_number,
            "phase": self.phase.name,
            "winner": self.winner,
            "is_over": self.is_over,
            "limits": asdict(self.limits),
            "players": {
                name: {
                    "questions_used": ps.questions_used,
                    "guesses_used": ps.guesses_used,
                    "questions_left": self.remaining_questions(name),
                    "guesses_left": self.remaining_guesses(name),
                }
                for name, ps in self.players.items()
            },
        }

    # Backward compatibility indicator
    def questions_asked(self) -> int:  # type: ignore
        # Maintain similarity to old attribute style; returns total questions
        return sum(ps.questions_used for ps in self.players.values())

__all__ = [
    "Game",
    "Phase",
    "RoundLimits",
    "PlayerState",
]

# --------------------------------------------------------------------------------------
# Simple (single-stage) game implementation matching the user's textual specification.
# --------------------------------------------------------------------------------------

from dataclasses import field

class SimpleWordGuessGame:
    """A minimal two-player cooperative / competitive word guessing game.

    Specification (as requested):
      - There is a dictionary of many Persian words (provided in `words.WORDS`).
      - One word is randomly chosen at the start and hidden from players.
      - Players declare how many YES/NO questions (N) they want for the *whole* game.
      - They can ask up to N questions total (shared pool or per game) before making a final guess.
      - Each question is answered by an LLM function that receives (question, real_word) and
        returns True/False (or a string convertible to bool). We do NOT implement the LLM here;
        we just call the injected dependency `llm_answer_fn` (default = generate_llm_reply).
      - After questions are exhausted they MUST guess (unless `allow_early_guess=True`, in which
        case they may guess earlier). A correct guess ends the game with a winner; otherwise they
        may optionally allow multiple guesses (configurable) or end immediately on a wrong guess.

    Modes:
      * By default the total question limit is shared across both players (cooperative deduction).
        Set `shared_question_pool=False` to give each player their own quota of N questions.

    Serialization helpers (`to_dict` / `from_dict`) are provided so this class can be used in a
    web session workflow (store serialized state between HTTP requests).

    This class intentionally stays simpler than the more advanced `Game` class above; pick the
    one that matches your UX requirements.
    """

    def __init__(
        self,
        question_limit: int,
        players: Optional[List[str]] = None,
        llm_answer_fn: Callable[[str, str], Any] = None,
        word: Optional[str] = None,
        allow_early_guess: bool = True,
        end_on_first_wrong_guess: bool = False,
        shared_question_pool: bool = True,
        max_guesses_per_player: int = 1,
    ) -> None:
        if question_limit <= 0:
            raise ValueError("question_limit must be positive")
        self.players = players or ["Player 1", "Player 2"]
        if len(self.players) < 1:
            raise ValueError("At least one player required.")
        self.word, self.description = (word, word) or get_random_word()
        self.question_limit = question_limit
        self.shared_question_pool = shared_question_pool
        self.allow_early_guess = allow_early_guess
        self.end_on_first_wrong_guess = end_on_first_wrong_guess
        self.max_guesses_per_player = max_guesses_per_player
        self.llm_answer_fn = llm_answer_fn or generate_llm_reply

        # State tracking
        self.questions_used_total: int = 0
        self.questions_used_per_player: Dict[str, int] = {p: 0 for p in self.players}
        self.guesses_used_per_player: Dict[str, int] = {p: 0 for p in self.players}
        self.history_questions: List[Dict[str, Any]] = []  # each: {player, question, answer_bool}
        self.history_guesses: List[Dict[str, Any]] = []    # each: {player, guess, correct}
        self.is_over: bool = False
        self.winner: Optional[str] = None
        self.revealed: bool = False  # becomes True when game ends

    # --------------------- Internal Utilities --------------------- #
    @staticmethod
    def _coerce_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            v = value.strip().lower()
            if v in {"true", "yes", "y", "1", "بله", "درست"}:
                return True
            if v in {"false", "no", "n", "0", "خیر", "غلط"}:
                return False
        # Fallback conservative False (avoid granting positive facts on malformed output)
        return False

    def _check_player(self, player: str) -> None:
        if player not in self.players:
            raise ValueError(f"Unknown player '{player}'")

    # --------------------- Query Introspection --------------------- #
    def remaining_questions(self, player: Optional[str] = None) -> int:
        if self.shared_question_pool:
            return max(0, self.question_limit - self.questions_used_total)
        if player is None:
            raise ValueError("player must be provided when not using shared_question_pool")
        return max(0, self.question_limit - self.questions_used_per_player[player])

    def remaining_guesses(self, player: str) -> int:
        return max(0, self.max_guesses_per_player - self.guesses_used_per_player[player])

    # --------------------- Core Actions --------------------- #
    def ask(self, question: str, player: str) -> bool:
        """Ask a yes/no question.

        Returns the boolean answer.
        Raises ValueError if rules are violated.
        """
        if self.is_over:
            raise ValueError("Game is over")
        self._check_player(player)

        # Enforce question limits
        if self.shared_question_pool:
            if self.questions_used_total >= self.question_limit:
                raise ValueError("No questions remaining (shared pool)")
        else:
            if self.questions_used_per_player[player] >= self.question_limit:
                raise ValueError(f"{player} has no questions remaining")

        raw_answer = self.llm_answer_fn(question, {self.word, self.description})
        answer_bool = self._coerce_bool(raw_answer)

        # Record history
        self.history_questions.append({
            "player": player,
            "question": question,
            "answer": answer_bool,
        })
        # Update counters
        self.questions_used_total += 1
        self.questions_used_per_player[player] += 1
        return answer_bool

    def can_guess_now(self) -> bool:
        if self.is_over:
            return False
        if self.allow_early_guess:
            return True
        # Must wait until all questions have been used (shared or per-player)
        if self.shared_question_pool:
            return self.questions_used_total >= self.question_limit
        # per-player: both players have exhausted their quotas
        return all(self.questions_used_per_player[p] >= self.question_limit for p in self.players)

    def guess(self, guess_word: str, player: str) -> bool:
        """Player makes a guess. Returns True if correct, False otherwise.

        Side effects: updates history, sets winner/is_over when appropriate.
        Raises ValueError if guessing not allowed yet or limits exceeded.
        """
        if self.is_over:
            raise ValueError("Game is over")
        self._check_player(player)
        if not self.can_guess_now():
            raise ValueError("Guessing not allowed yet (questions remaining)")
        if self.guesses_used_per_player[player] >= self.max_guesses_per_player:
            raise ValueError(f"{player} has no guesses remaining")

        self.guesses_used_per_player[player] += 1
        correct = guess_word.strip().lower() == self.word.lower()
        self.history_guesses.append({
            "player": player,
            "guess": guess_word,
            "correct": correct,
        })
        if correct:
            self.winner = player
            self.is_over = True
            self.revealed = True
        else:
            if self.end_on_first_wrong_guess:
                self.is_over = True
                self.revealed = True
            else:
                # Optional: end when all players consumed guesses
                if all(self.guesses_used_per_player[p] >= self.max_guesses_per_player for p in self.players):
                    self.is_over = True
                    self.revealed = True
        return correct

    def reveal_word(self) -> str:
        self.revealed = True
        return self.word

    # --------------------- Serialization / Summary --------------------- #
    def to_dict(self) -> Dict[str, Any]:
        return {
            "word": self.word,
            "players": self.players,
            "question_limit": self.question_limit,
            "shared_question_pool": self.shared_question_pool,
            "allow_early_guess": self.allow_early_guess,
            "end_on_first_wrong_guess": self.end_on_first_wrong_guess,
            "max_guesses_per_player": self.max_guesses_per_player,
            "questions_used_total": self.questions_used_total,
            "questions_used_per_player": self.questions_used_per_player,
            "guesses_used_per_player": self.guesses_used_per_player,
            "history_questions": self.history_questions,
            "history_guesses": self.history_guesses,
            "is_over": self.is_over,
            "winner": self.winner,
            "revealed": self.revealed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], llm_answer_fn: Callable[[str, str], Any] = None) -> "SimpleWordGuessGame":
        game = cls(
            question_limit=data["question_limit"],
            players=data["players"],
            llm_answer_fn=llm_answer_fn or generate_llm_reply,
            word=data["word"],
            allow_early_guess=data.get("allow_early_guess", True),
            end_on_first_wrong_guess=data.get("end_on_first_wrong_guess", False),
            shared_question_pool=data.get("shared_question_pool", True),
            max_guesses_per_player=data.get("max_guesses_per_player", 1),
        )
        # Restore mutable state
        game.questions_used_total = data.get("questions_used_total", 0)
        game.questions_used_per_player = data.get("questions_used_per_player", {p:0 for p in game.players})
        game.guesses_used_per_player = data.get("guesses_used_per_player", {p:0 for p in game.players})
        game.history_questions = data.get("history_questions", [])
        game.history_guesses = data.get("history_guesses", [])
        game.is_over = data.get("is_over", False)
        game.winner = data.get("winner")
        game.revealed = data.get("revealed", False)
        return game

    def summary(self) -> Dict[str, Any]:
        data = {
            "word_revealed": self.word if self.revealed else None,
            "winner": self.winner,
            "is_over": self.is_over,
            "questions_remaining_shared": self.remaining_questions() if self.shared_question_pool else None,
            "questions_remaining_per_player": None if self.shared_question_pool else {
                p: self.remaining_questions(p) for p in self.players
            },
            "guesses_remaining_per_player": {p: self.remaining_guesses(p) for p in self.players},
            "asked": len(self.history_questions),
            "guesses": len(self.history_guesses),
        }
        if not self.shared_question_pool:
            data["questions_used_per_player"] = dict(self.questions_used_per_player)
        return data

__all__.append("SimpleWordGuessGame")