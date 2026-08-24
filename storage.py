"""
storage.py — Persisting the best score to a small JSON file.

Pure Python (no pygame). The best score is the biggest number the
cube has ever reached; it survives restarts of the game.
"""

from __future__ import annotations

import json
import os

from settings import BEST_SCORE_PATH

DEFAULT_BEST = 0


def load_best_score(path: str = BEST_SCORE_PATH) -> int:
    """Read the saved best score. Returns DEFAULT_BEST when missing/corrupt."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        value = int(data["best"])
        return value if value >= 0 else DEFAULT_BEST
    except (OSError, ValueError, KeyError, TypeError):
        return DEFAULT_BEST


def save_best_score(score: int, path: str = BEST_SCORE_PATH) -> None:
    """Write the best score to disk (best-effort, never raises)."""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"best": int(score)}, fh)
    except OSError:
        pass  # saving is best-effort; the game still runs without it


def update_best_score(score: int, path: str = BEST_SCORE_PATH) -> int:
    """Load, merge with ``score`` and persist. Returns the new best."""
    best = max(load_best_score(path), int(score))
    save_best_score(best, path)
    return best
