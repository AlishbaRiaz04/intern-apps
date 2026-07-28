"""
score.py

Tracks the current run's score and persists the all-time high score
to disk (high_score.json) so it survives between runs of the game.
"""

import json
import os

HIGH_SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "high_score.json")

# Points awarded per frame of survival - at 60 FPS this works out to
# roughly 10 points/second before any multiplier is applied.
BASE_POINTS_PER_FRAME = 0.17


class Score:
    """
    Call update() once per frame while the game is running, and
    save_high_score() whenever a run ends (on collision), so the file
    is only written when it actually needs to be.
    """

    def __init__(self):
        self.current = 0.0
        self.high_score = self._load_high_score()
        self.multiplier = 1  # set to 2 while a Score Boost power-up is active

    def _load_high_score(self):
        if not os.path.exists(HIGH_SCORE_FILE):
            return 0
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                data = json.load(f)
                return int(data.get("high_score", 0))
        except (json.JSONDecodeError, ValueError, OSError):
            # Corrupt or unreadable file - fail safe rather than crash the game
            return 0

    def save_high_score(self):
        """Write the high score to disk, but only if it actually changed."""
        if self.get_current_int() > self.high_score:
            self.high_score = self.get_current_int()
            try:
                with open(HIGH_SCORE_FILE, "w") as f:
                    json.dump({"high_score": self.high_score}, f)
            except OSError:
                pass  # non-fatal - the game just won't persist this run

    def update(self):
        """Called once per frame while the game is running."""
        self.current += BASE_POINTS_PER_FRAME * self.multiplier

    def reset(self):
        """Start a fresh run - the high score itself is untouched."""
        self.current = 0.0
        self.multiplier = 1

    def get_current_int(self):
        return int(self.current)
