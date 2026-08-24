"""
storage.py — Persisting game state to a small JSON file.

Pure Python (no pygame). Stores:
  * the best score for EACH difficulty level
  * the sound mute preference
  * the last difficulty level chosen by the player

File format:
    {"best": {"easy": 64, "medium": 128, "hard": 0},
     "muted": true,
     "level": "medium"}

Older save files that only had {"best": <int>, "muted": <bool>} are
migrated on load — the old single best score becomes the medium score.
"""

from __future__ import annotations

import json

from settings import BEST_SCORE_PATH, DEFAULT_DIFFICULTY, DIFFICULTY_ORDER

DEFAULT_BEST = 0


def _default_state() -> dict:
    return {
        "best": {level: DEFAULT_BEST for level in DIFFICULTY_ORDER},
        "muted": False,
        "level": DEFAULT_DIFFICULTY,
    }


def load_state(path: str = BEST_SCORE_PATH) -> dict:
    """Read the saved state, merging over safe defaults.

    Missing or corrupt files fall back to defaults; legacy files with a
    single integer best score are migrated into the medium slot.
    """
    state = _default_state()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return state

        # Best scores: either per-level dict or legacy single integer.
        best = data.get("best")
        if isinstance(best, dict):
            for level in DIFFICULTY_ORDER:
                value = best.get(level)
                if isinstance(value, int) and value >= 0:
                    state["best"][level] = value
        elif isinstance(best, int) and best >= 0:
            state["best"]["medium"] = best  # legacy file migration

        if isinstance(data.get("muted"), bool):
            state["muted"] = data["muted"]
        if data.get("level") in DIFFICULTY_ORDER:
            state["level"] = data["level"]
    except (OSError, ValueError):
        pass  # missing/corrupt file -> defaults
    return state


def save_state(state: dict, path: str = BEST_SCORE_PATH) -> None:
    """Write the state dict to disk (best-effort, never raises)."""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({
                "best": {level: int(state["best"][level])
                         for level in DIFFICULTY_ORDER},
                "muted": bool(state["muted"]),
                "level": state["level"],
            }, fh)
    except OSError:
        pass  # saving is best-effort; the game still runs without it


# -- best scores (one per difficulty) -------------------------------------


def load_best_scores(path: str = BEST_SCORE_PATH) -> dict:
    """Per-level best scores, e.g. {"easy": 64, "medium": 128, "hard": 0}."""
    return dict(load_state(path)["best"])


def update_best_score(score: int, level: str,
                      path: str = BEST_SCORE_PATH) -> int:
    """Merge ``score`` into the given level's best and persist it.

    Returns the updated best score for that level.
    """
    if level not in DIFFICULTY_ORDER:
        level = DEFAULT_DIFFICULTY
    state = load_state(path)
    state["best"][level] = max(state["best"][level], int(score))
    save_state(state, path)
    return state["best"][level]


# -- difficulty level -----------------------------------------------------


def load_level(path: str = BEST_SCORE_PATH) -> str:
    return load_state(path)["level"]


def set_level(level: str, path: str = BEST_SCORE_PATH) -> str:
    """Persist the chosen difficulty and return it (validated)."""
    if level not in DIFFICULTY_ORDER:
        level = DEFAULT_DIFFICULTY
    state = load_state(path)
    state["level"] = level
    save_state(state, path)
    return level


# -- sound mute -----------------------------------------------------------


def load_muted(path: str = BEST_SCORE_PATH) -> bool:
    return load_state(path)["muted"]


def set_muted(muted: bool, path: str = BEST_SCORE_PATH) -> bool:
    """Persist the mute preference and return the stored value."""
    state = load_state(path)
    state["muted"] = bool(muted)
    save_state(state, path)
    return state["muted"]
