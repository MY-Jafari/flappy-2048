"""
obstacle.py — Columns (obstacles) with a passable gap.

Pure logic (no pygame): each column is a pair of solid blocks (top and
bottom) separated by a vertical gap, plus a small number badge floating
in the middle of the gap. Touching the badge merges numbers; touching
the solid body kills the player.

Position model: ``x`` is the left edge of the column, ``gap_y`` is the
vertical CENTER of the gap.
"""

from __future__ import annotations

import random

from game_logic import pick_column_number, rects_overlap


class Obstacle:
    """A scrolling column with a gap and a number badge."""

    def __init__(self, x: float, gap_y: float, gap_height: float,
                 width: float, number: int, world_height: float) -> None:
        self.x = x
        self.gap_y = gap_y            # vertical center of the gap
        self.gap_height = gap_height
        self.width = width
        self.number = number          # number shown on the badge
        self.merged = False           # already merged with the player?
        self.passed = False           # already flown past (for scoring cues)
        self.world_height = world_height

    # -- geometry ---------------------------------------------------------

    @property
    def gap_top(self) -> float:
        return self.gap_y - self.gap_height / 2.0

    @property
    def gap_bottom(self) -> float:
        return self.gap_y + self.gap_height / 2.0

    def top_body_rect(self) -> tuple:
        """Solid block above the gap: (x, y, w, h)."""
        return (self.x, 0.0, self.width, self.gap_top)

    def bottom_body_rect(self) -> tuple:
        """Solid block below the gap: (x, y, w, h)."""
        return (self.x, self.gap_bottom, self.width,
                self.world_height - self.gap_bottom)

    def badge_rect(self, badge_size: float) -> tuple:
        """The mergeable number block, centered inside the gap."""
        return (self.x + self.width / 2.0 - badge_size / 2.0,
                self.gap_y - badge_size / 2.0,
                badge_size, badge_size)

    # -- behaviour --------------------------------------------------------

    def update(self, dt: float, speed: float) -> None:
        """Scroll the column leftwards."""
        self.x -= speed * dt

    def off_screen(self) -> bool:
        """True when the whole column has scrolled past the left edge."""
        return self.x + self.width < 0.0

    def hits_body(self, player_rect: tuple) -> bool:
        """True if the player's AABB touches either solid block."""
        px, py, pw, ph = player_rect
        tx, ty, tw, th = self.top_body_rect()
        bx, by, bw, bh = self.bottom_body_rect()
        return (rects_overlap(px, py, pw, ph, tx, ty, tw, th) or
                rects_overlap(px, py, pw, ph, bx, by, bw, bh))

    def hits_badge(self, player_rect: tuple, badge_size: float) -> bool:
        """True if the player's AABB touches the number badge."""
        px, py, pw, ph = player_rect
        bx, by, bw, bh = self.badge_rect(badge_size)
        return rects_overlap(px, py, pw, ph, bx, by, bw, bh)


def spawn_obstacle(rng: random.Random,
                   player_value: int,
                   world_width: float, world_height: float,
                   gap_height: float, column_width: float,
                   gap_margin: float) -> Obstacle:
    """Create a new column just off the right edge of the screen.

    The gap center is chosen randomly inside the safe band defined by
    ``gap_margin``; the badge number follows the mergeable-biased
    distribution from game_logic.pick_column_number.
    """
    low = gap_margin + gap_height / 2.0
    high = world_height - gap_margin - gap_height / 2.0
    gap_y = rng.uniform(low, high) if high > low else world_height / 2.0
    number = pick_column_number(player_value, rng)
    return Obstacle(world_width + column_width, gap_y, gap_height,
                    column_width, number, world_height)
