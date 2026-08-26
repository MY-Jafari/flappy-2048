"""
player.py — The player's cube.

Pure logic only (no pygame imports): physics, the current number,
and the merge pulse timer. How the cube *looks* is decided in ui.py
from this state (color comes from ``value``, rotation from ``vy``).

Position model: ``x`` is the left edge (fixed during a run),
``y`` is the vertical CENTER of the cube.
"""

from __future__ import annotations


class Player:
    """A square cube that hops under gravity and holds a 2048-style value."""

    def __init__(self, x: float, y: float, size: float, value: int = 2) -> None:
        self.x = x
        self.y = y                  # vertical center
        self.size = size
        self.vx = 0.0               # horizontal speed (unused; kept for porting)
        self.vy = 0.0               # vertical speed, px/s (negative = up)
        self.value = value          # current number on the cube
        self.pulse = 0.0            # seconds remaining of the merge pulse

    # -- geometry ---------------------------------------------------------

    @property
    def left(self) -> float:
        return self.x

    @property
    def top(self) -> float:
        return self.y - self.size / 2.0

    @property
    def bottom(self) -> float:
        return self.y + self.size / 2.0

    def rect(self) -> tuple:
        """(x, y, w, h) AABB, used by the pure collision helpers."""
        return (self.x, self.top, self.size, self.size)

    # -- behaviour --------------------------------------------------------

    def jump(self, jump_velocity: float) -> None:
        """Apply an upward velocity (a tap / space / click)."""
        self.vy = jump_velocity

    def update(self, dt: float, gravity: float, max_fall_speed: float) -> None:
        """Advance physics by ``dt`` seconds (gravity is per-second)."""
        self.vy = min(self.vy + gravity * dt, max_fall_speed)
        self.y += self.vy * dt
        if self.pulse > 0.0:
            self.pulse = max(0.0, self.pulse - dt)

    def merge_with(self, other_value: int, pulse_time: float) -> None:
        """Merge an equal value into the cube and start the pulse effect."""
        self.value += other_value
        self.pulse = pulse_time

    def tilt_degrees(self, factor: float,
                     max_up: float, max_down: float) -> float:
        """Rotation for rendering, derived from vertical speed.

        Rising (vy < 0) tilts the cube slightly counter-clockwise,
        falling tilts it clockwise — a natural flappy feel.
        """
        tilt = -self.vy * factor
        if tilt > 0:
            return min(tilt, max_up)
        return max(tilt, -max_down)
