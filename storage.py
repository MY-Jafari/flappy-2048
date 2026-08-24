"""
storage.py — Persisting game state to a small JSON file.

Pure Python (no pygame). Stores the best score (the biggest number the
cube has ever reached) and the sound mute preference so both survive
restarts of the game.

The file format is a tiny dict:  {"best": 128, "muted": true}
"""

from __future__ import annotations

import json

from settings import BEST_SCORE_PATH

DEFAULT_BEST = 0
DEFAULT_STATE = {"best": DEFAULT_BEST, "muted": False}


def load_state(path: str = BEST_SCORE_PATH) -> dict:
    """Read the saved state, merging over safe defaults.

    Missing or corrupt files fall back to defaults; unknown keys are
    ignored so older save files keep working.
    """
    state = dict(DEFAULT_STATE)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            if isinstance(data.get("best"), int) and data["best"] >= 0:
                state["best"] = data["best"]
            if isinstance(data.get("muted"), bool):
                state["muted"] = data["muted"]
    except (OSError, ValueError):
        pass  # missing/corrupt file -> defaults
    return state


def save_state(state: dict, path: str = BEST_SCORE_PATH) -> None:
    """Write the state dict to disk (best-effort, never raises)."""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"best": int(state["best"]),
                       "muted": bool(state["muted"])}, fh)
    except OSError:
        pass  # saving is best-effort; the game still runs without it


# -- best score -----------------------------------------------------------


def load_best_score(path: str = BEST_SCORE_PATH) -> int:
    return load_state(path)["best"]


def save_best_score(score: int, path: str = BEST_SCORE_PATH) -> None:
    state = load_state(path)
    state["best"] = max(DEFAULT_BEST, int(score))
    save_state(state, path)


def update_best_score(score: int, path: str = BEST_SCORE_PATH) -> int:
    """Load, merge with ``score`` and persist. Returns the new best."""
    state = load_state(path)
    state["best"] = max(state["best"], int(score))
    save_state(state, path)
    return state["best"]


# -- sound mute -----------------------------------------------------------


def load_muted(path: str = BEST_SCORE_PATH) -> bool:
    return load_state(path)["muted"]


def set_muted(muted: bool, path: str = BEST_SCORE_PATH) -> bool:
    """Persist the mute preference and return the stored value."""
    state = load_state(path)
    state["muted"] = bool(muted)
    save_state(state, path)
    return state["muted"]
