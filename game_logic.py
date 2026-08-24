"""
game_logic.py — Pure game logic for Flappy 2048.

Everything in this module is plain Python with NO pygame imports.
It is the part of the codebase you would port to JavaScript/HTML5
almost line-for-line. Rendering lives in ui.py; only that module
(plus main.py's event loop and sound.py) touches pygame.

Mechanics covered here:
  * 2048-style number merging (equal numbers combine by addition)
  * generating the numbers shown on columns
  * gradual difficulty (speed grows with distance traveled)
  * AABB collision helpers
"""

from __future__ import annotations

import random
from typing import List, Optional, Sequence

# ---------------------------------------------------------------------------
# Number merging (2048 rules)
# ---------------------------------------------------------------------------


def merge_numbers(a: int, b: int) -> Optional[int]:
    """Merge two numbers like 2048: equal values add up.

    Returns the merged value (a + b) when ``a == b``, otherwise None
    (meaning "no merge happened").
    """
    if a == b:
        return a + b
    return None


def powers_of_two(max_value: int) -> List[int]:
    """All powers of two in [2, max_value], e.g. powers_of_two(8) == [2, 4, 8]."""
    result: List[int] = []
    value = 2
    while value <= max_value:
        result.append(value)
        value *= 2
    return result


def smaller_powers_of_two(max_value: int) -> List[int]:
    """Powers of two strictly smaller than ``max_value`` (used for variety)."""
    return [v for v in powers_of_two(max_value) if v < max_value]


def pick_column_number(player_value: int,
                       rng: random.Random,
                       match_chance: float = 0.65) -> int:
    """Choose the number displayed on a column.

    Only a number equal to the player's current value can be merged
    (2+2=4), so most columns show exactly that value to keep progress
    possible. The rest are smaller powers of two, which give visual
    variety but cannot be merged — the player must pick the right gap.

    ``match_chance``: probability a column matches the player's value.
    """
    if rng.random() < match_chance:
        return player_value
    smaller = smaller_powers_of_two(player_value)
    if not smaller:
        # Player is at 2 — there is nothing smaller, always match.
        return player_value
    return rng.choice(smaller)


# ---------------------------------------------------------------------------
# Difficulty
# ---------------------------------------------------------------------------


def speed_at(distance: float,
             base_speed: float,
             accel: float,
             max_speed: float) -> float:
    """Column scroll speed for a given distance traveled (px).

    Only speed increases over time — gap size stays constant (design
    decision from the interview). Speed grows linearly with distance
    and is capped at ``max_speed``.
    """
    return min(base_speed + distance * accel, max_speed)


# ---------------------------------------------------------------------------
# Collision helpers (pure AABB math)
# ---------------------------------------------------------------------------


def rects_overlap(ax: float, ay: float, aw: float, ah: float,
                  bx: float, by: float, bw: float, bh: float) -> bool:
    """True when two axis-aligned rectangles overlap."""
    return (ax < bx + bw and ax + aw > bx and
            ay < by + bh and ay + ah > by)


def clamp(value: float, low: float, high: float) -> float:
    """Clamp ``value`` into the inclusive range [low, high]."""
    return max(low, min(high, value))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation from a to b with factor t (clamped to [0, 1])."""
    t = clamp(t, 0.0, 1.0)
    return a + (b - a) * t


def ease_out_cubic(t: float) -> float:
    """Ease-out cubic easing function, used by animations."""
    t = clamp(t, 0.0, 1.0)
    return 1.0 - (1.0 - t) ** 3


def ease_out_back(t: float) -> float:
    """Ease-out-back: overshoots slightly, nice for pop-in animations."""
    t = clamp(t, 0.0, 1.0)
    c1, c3 = 1.70158, 2.70158
    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2



