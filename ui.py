"""
ui.py — Everything that draws to the screen.

This is the ONLY rendering layer: it translates the pure game state
(player, obstacles, scores) into pixels. The rest of the codebase is
pygame-free so it can be ported to the web later — swapping this file
for an HTML5 canvas renderer is the intended porting path.

Also houses small presentation-only helpers (clouds background and
confetti particles) that have no gameplay meaning.
"""

from __future__ import annotations

import random
from typing import List, Sequence, Tuple

import pygame

from settings import (
    BADGE_SIZE, CLOUD_COLOR, CLOUD_COUNT, CLOUD_MAX_SPEED, CLOUD_MIN_SPEED,
    COLUMN_COLOR, COLUMN_EDGE_COLOR, COLUMN_EDGE_WIDTH, CONFETTI_COLORS,
    DIFFICULTIES, DIFFICULTY_ORDER, FADE_COLOR, FONT_NAME, MAX_TILT_DOWN,
    MAX_TILT_UP, MERGE_PULSE_SCALE, MERGE_PULSE_TIME, SKY_BOTTOM, SKY_TOP,
    TILE_COLORS, TILE_TEXT_DARK, TILE_TEXT_LIGHT, TILT_SPEED_FACTOR,
    UI_BUTTON_COLOR, UI_BUTTON_EDGE, UI_BUTTON_HOVER, UI_SELECT_COLOR,
    UI_SELECT_EDGE, UI_SUBTEXT_COLOR, UI_TEXT_COLOR, UI_TITLE_COLOR,
    WIN_OVERLAY, WINDOW_HEIGHT, WINDOW_WIDTH,
)
from game_logic import ease_out_cubic, lerp

Color = Tuple[int, int, int]


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def color_for_value(value: int) -> Color:
    """Tile color for a number; large values clamp to the 2048 color."""
    if value in TILE_COLORS:
        return TILE_COLORS[value]
    keys = sorted(TILE_COLORS)
    for key in keys:
        if value <= key:
            return TILE_COLORS[key]
    return TILE_COLORS[keys[-1]]


def text_color_for_value(value: int) -> Color:
    """Dark text on light tiles (2, 4), light text on warm tiles."""
    return TILE_TEXT_DARK if value <= 4 else TILE_TEXT_LIGHT


class FontCache:
    """Caches pygame fonts so we don't rebuild them every frame."""

    def __init__(self) -> None:
        self._fonts = {}

    def get(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in self._fonts:
            self._fonts[key] = pygame.font.SysFont(FONT_NAME, size, bold=bold)
        return self._fonts[key]


def draw_text(surface: pygame.Surface, text: str, font: pygame.font.Font,
              color: Color, center: Tuple[float, float] | None = None,
              topleft: Tuple[float, float] | None = None,
              shadow: bool = False) -> pygame.Rect:
    """Draw text centered or by top-left; optional drop shadow."""
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center is not None:
        rect.center = (int(center[0]), int(center[1]))
    else:
        rect.topleft = (int(topleft[0]), int(topleft[1]))
    if shadow:
        shadow_rect = rect.move(3, 3)
        surface.blit(font.render(text, True, (60, 52, 48)), shadow_rect)
    surface.blit(rendered, rect)
    return rect


def make_sky(width: int, height: int) -> pygame.Surface:
    """Pre-render a vertical sky gradient."""
    sky = pygame.Surface((width, height))
    strips = 48
    for i in range(strips):
        t = i / (strips - 1)
        color = (int(lerp(SKY_TOP[0], SKY_BOTTOM[0], t)),
                 int(lerp(SKY_TOP[1], SKY_BOTTOM[1], t)),
                 int(lerp(SKY_TOP[2], SKY_BOTTOM[2], t)))
        y = int(height * i / strips)
        h = int(height / strips) + 1
        pygame.draw.rect(sky, color, (0, y, width, h))
    return sky


def draw_fade(surface: pygame.Surface, alpha: int) -> None:
    """Draw a full-screen fade overlay with the given alpha (0-255)."""
    if alpha <= 0:
        return
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((*FADE_COLOR, min(alpha, 255)))
    surface.blit(overlay, (0, 0))


# ---------------------------------------------------------------------------
# Player / obstacles
# ---------------------------------------------------------------------------


def _tile_surface(size: float, color: Color, number: int,
                  font: pygame.font.Font) -> pygame.Surface:
    """Rounded cube with the number printed on it (pre-rotation)."""
    side = int(size)
    surf = pygame.Surface((side, side), pygame.SRCALPHA)
    radius = max(6, int(side * 0.22))
    rect = pygame.Rect(0, 0, side, side)
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    # Cartoon outline
    pygame.draw.rect(surf, (255, 255, 255), rect,
                     width=max(2, side // 14), border_radius=radius)
    number_color = text_color_for_value(number)
    label = font.render(str(number), True, number_color)
    label_rect = label.get_rect(center=(side // 2, side // 2))
    surf.blit(label, label_rect)
    return surf


def draw_player(surface: pygame.Surface, player, font_cache: FontCache,
                angle_offset: float = 0.0, alpha: int = 255,
                scale_override: float | None = None,
                offset_x: float = 0.0) -> None:
    """Draw the player cube with tilt, merge pulse and optional extras.

    ``angle_offset`` spins the cube (used by the death animation),
    ``alpha`` fades it out, ``offset_x`` shifts it horizontally (used
    for the death shake) and ``scale_override`` replaces the pulse scale.
    """
    size = player.size
    scale = scale_override if scale_override is not None else 1.0
    if player.pulse > 0.0:
        t = 1.0 - player.pulse / MERGE_PULSE_TIME
        scale *= 1.0 + (MERGE_PULSE_SCALE - 1.0) * (1.0 - ease_out_cubic(t))

    font = font_cache.get(max(12, int(size * 0.42)))
    tile = _tile_surface(size, color_for_value(player.value),
                         player.value, font)

    if scale != 1.0:
        new_w = max(1, int(size * scale))
        tile = pygame.transform.smoothscale(tile, (new_w, new_w))

    # Natural tilt from vertical speed + optional spin from the death anim.
    tilt = player.tilt_degrees(TILT_SPEED_FACTOR, MAX_TILT_UP, MAX_TILT_DOWN)
    angle = tilt + angle_offset
    if angle != 0.0:
        tile = pygame.transform.rotate(tile, angle)
    if alpha < 255:
        tile.set_alpha(alpha)

    center = (int(player.x + player.size / 2.0 + offset_x), int(player.y))
    rect = tile.get_rect(center=center)
    surface.blit(tile, rect)


def draw_obstacle(surface: pygame.Surface, obstacle, font_cache: FontCache,
                  badge_size: float = BADGE_SIZE) -> None:
    """Draw a column (two solid blocks + number badge in the gap)."""
    radius = 10
    x = int(obstacle.x)

    # Top block
    top_rect = pygame.Rect(x, 0, int(obstacle.width), int(obstacle.gap_top))
    if top_rect.height > 0:
        pygame.draw.rect(surface, COLUMN_COLOR, top_rect, border_radius=radius)
        pygame.draw.rect(surface, COLUMN_EDGE_COLOR, top_rect,
                         width=COLUMN_EDGE_WIDTH, border_radius=radius)

    # Bottom block
    bottom = int(obstacle.gap_bottom)
    bottom_rect = pygame.Rect(x, bottom, int(obstacle.width),
                              int(obstacle.world_height) - bottom)
    if bottom_rect.height > 0:
        pygame.draw.rect(surface, COLUMN_COLOR, bottom_rect,
                         border_radius=radius)
        pygame.draw.rect(surface, COLUMN_EDGE_COLOR, bottom_rect,
                         width=COLUMN_EDGE_WIDTH, border_radius=radius)

    # Number badge — hidden once merged with the player
    if obstacle.merged:
        return
    bx, by, bw, bh = obstacle.badge_rect(badge_size)
    badge = pygame.Rect(int(bx), int(by), int(bw), int(bh))
    font = font_cache.get(max(10, int(badge_size * 0.42)))
    tile = _tile_surface(badge_size, color_for_value(obstacle.number),
                         obstacle.number, font)
    surface.blit(tile, badge)


# ---------------------------------------------------------------------------
# Decorative background / celebration
# ---------------------------------------------------------------------------


class Clouds:
    """A few cartoon clouds drifting slowly leftwards (presentation only)."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng
        self.clouds: List[dict] = []
        for _ in range(CLOUD_COUNT):
            self.clouds.append(self._make_cloud(rng, rng.uniform(0, WINDOW_WIDTH)))

    def _make_cloud(self, rng: random.Random, x: float) -> dict:
        w = int(rng.uniform(70, 130))
        h = int(rng.uniform(26, 46))
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        # Puffy blob: three overlapping ellipses
        pygame.draw.ellipse(surf, CLOUD_COLOR, (0, h // 3, w // 2, h))
        pygame.draw.ellipse(surf, CLOUD_COLOR, (w // 4, 0, w // 2, h))
        pygame.draw.ellipse(surf, CLOUD_COLOR, (w // 2, h // 4, w // 2, h))
        return {
            "surf": surf,
            "x": x,
            "y": rng.uniform(30, 260),
            "speed": rng.uniform(CLOUD_MIN_SPEED, CLOUD_MAX_SPEED),
        }

    def update(self, dt: float) -> None:
        for cloud in self.clouds:
            cloud["x"] -= cloud["speed"] * dt
            if cloud["x"] + cloud["surf"].get_width() < 0:
                cloud["x"] = WINDOW_WIDTH + self._rng.uniform(10, 120)
                cloud["y"] = self._rng.uniform(30, 260)

    def draw(self, surface: pygame.Surface) -> None:
        for cloud in self.clouds:
            surface.blit(cloud["surf"], (int(cloud["x"]), int(cloud["y"])))


class Confetti:
    """Celebration confetti falling over the play area.

    Pieces are pre-rendered and rotation is quantized to ANGLE_STEP
    buckets with a shared cache, so drawing allocates no new surfaces
    per frame (previously 90 surfaces were built every frame).
    """

    ANGLE_STEP = 15  # degrees between cached rotations

    def __init__(self, count: int, rng: random.Random) -> None:
        self._rng = rng
        self.particles = []
        for _ in range(count):
            self.particles.append(self._make(rng.uniform(0, WINDOW_WIDTH)))
        self._pieces = {}    # (color, size) -> unrotated square
        self._rotated = {}   # (color, size, angle bucket) -> rotated piece

    def _make(self, x: float) -> dict:
        return {
            "x": x,
            "y": self._rng.uniform(-40, WINDOW_HEIGHT * 0.5),
            "vy": self._rng.uniform(80, 200),
            "vx": self._rng.uniform(-30, 30),
            "rot": self._rng.uniform(0, 360),
            "vrot": self._rng.uniform(-240, 240),
            "size": float(self._rng.choice((6, 9, 12))),
            "color": self._rng.choice(CONFETTI_COLORS),
        }

    def update(self, dt: float) -> None:
        for p in self.particles:
            p["y"] += p["vy"] * dt
            p["x"] += p["vx"] * dt
            p["rot"] = (p["rot"] + p["vrot"] * dt) % 360.0
            if p["y"] > WINDOW_HEIGHT + 20:
                p.update(self._make(-10))  # recycle at the top

    def draw(self, surface: pygame.Surface) -> None:
        for p in self.particles:
            size = int(p["size"])
            bucket = int(p["rot"] // self.ANGLE_STEP)
            key = (p["color"], size, bucket)
            piece = self._rotated.get(key)
            if piece is None:
                base = self._pieces.get((p["color"], size))
                if base is None:
                    base = pygame.Surface((size, size), pygame.SRCALPHA)
                    pygame.draw.rect(base, p["color"], base.get_rect(),
                                     border_radius=2)
                    self._pieces[(p["color"], size)] = base
                piece = pygame.transform.rotate(
                    base, bucket * self.ANGLE_STEP)
                self._rotated[key] = piece
            rect = piece.get_rect(center=(int(p["x"]), int(p["y"])))
            surface.blit(piece, rect)


# ---------------------------------------------------------------------------
# HUD and screens
# ---------------------------------------------------------------------------


class Button:
    """A clickable rounded button on one of the screens."""

    def __init__(self, rect: pygame.Rect, label: str, action: str) -> None:
        self.rect = rect
        self.label = label
        self.action = action

    def hit(self, pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)

    def draw(self, surface: pygame.Surface, font_cache: FontCache,
             mouse_pos: Tuple[int, int]) -> None:
        hovered = self.hit(mouse_pos)
        color = UI_BUTTON_HOVER if hovered else UI_BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=16)
        pygame.draw.rect(surface, UI_BUTTON_EDGE, self.rect,
                         width=4, border_radius=16)
        font = font_cache.get(28, bold=True)
        draw_text(surface, self.label, font, (255, 255, 255),
                  center=self.rect.center)


def _pill(label: str, value: int, font_cache: FontCache) -> pygame.Surface:
    """Rounded pill with a small label on top and a big value below."""
    small = font_cache.get(13, bold=True)
    big = font_cache.get(22, bold=True)
    label_surf = small.render(label, True, UI_SUBTEXT_COLOR)
    value_surf = big.render(str(value), True, UI_TEXT_COLOR)
    pad_x, pad_y = 14, 8
    width = max(label_surf.get_width(), value_surf.get_width()) + pad_x * 2
    height = (pad_y + label_surf.get_height() + 2 + value_surf.get_height()
              + pad_y)
    pill = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(pill, (255, 255, 255, 215), pill.get_rect(),
                     border_radius=16)
    pill.blit(label_surf, (pad_x, pad_y))
    pill.blit(value_surf, (pad_x, pad_y + label_surf.get_height() + 2))
    return pill


def draw_hud(surface: pygame.Surface, font_cache: FontCache,
             score: int, best: int) -> None:
    """Score and best score pills at the top of the play screen."""
    score_pill = _pill("SCORE", score, font_cache)
    best_pill = _pill("BEST", best, font_cache)
    surface.blit(score_pill, (14, 14))
    surface.blit(best_pill, (WINDOW_WIDTH - best_pill.get_width() - 14, 14))


def _draw_difficulty_button(surface: pygame.Surface, font_cache: FontCache,
                            rect: pygame.Rect, level: str, best_value: int,
                            selected: bool,
                            mouse_pos: Tuple[int, int]) -> Button:
    """One difficulty pill: label on top, its best score below."""
    button = Button(rect, "", f"level:{level}")
    hovered = button.hit(mouse_pos)
    fill = UI_SELECT_COLOR if selected else (
        UI_BUTTON_HOVER if hovered else UI_BUTTON_COLOR)
    edge = UI_SELECT_EDGE if selected else UI_BUTTON_EDGE
    pygame.draw.rect(surface, fill, rect, border_radius=16)
    pygame.draw.rect(surface, edge, rect, width=4, border_radius=16)
    draw_text(surface, DIFFICULTIES[level]["label"],
              font_cache.get(24, bold=True), (255, 255, 255),
              center=(rect.centerx, rect.y + 21))
    draw_text(surface, f"BEST {best_value}", font_cache.get(13, bold=True),
              (255, 255, 255), center=(rect.centerx, rect.y + 43))
    return button


def draw_start_screen(surface: pygame.Surface, font_cache: FontCache,
                      mouse_pos: Tuple[int, int], level: str,
                      bests: dict) -> List[Button]:
    """Title screen with three difficulty buttons (EASY / MEDIUM / HARD)."""
    title_font = font_cache.get(54, bold=True)
    draw_text(surface, "Flappy 2048", title_font, UI_TITLE_COLOR,
              center=(WINDOW_WIDTH / 2, 125), shadow=True)

    draw_text(surface, "Match the numbers. Reach 2048!",
              font_cache.get(18), (255, 255, 255),
              center=(WINDOW_WIDTH / 2, 175), shadow=True)

    # Decorative cube
    tile = _tile_surface(76, color_for_value(64), 64,
                         font_cache.get(32, bold=True))
    surface.blit(tile, tile.get_rect(center=(WINDOW_WIDTH // 2, 260)))

    draw_text(surface, "CHOOSE DIFFICULTY",
              font_cache.get(18, bold=True), (255, 255, 255),
              center=(WINDOW_WIDTH / 2, 332), shadow=True)

    buttons = []
    y = 362
    for diff_level in DIFFICULTY_ORDER:
        rect = pygame.Rect(WINDOW_WIDTH / 2 - 100, y, 200, 56)
        buttons.append(_draw_difficulty_button(
            surface, font_cache, rect, diff_level,
            bests.get(diff_level, 0), diff_level == level, mouse_pos))
        y += 68

    draw_text(surface, "Click a level to start",
              font_cache.get(15, bold=True), (255, 255, 255),
              center=(WINDOW_WIDTH / 2, 620), shadow=True)
    draw_text(surface, "Space also starts - jump with click / tap / Space",
              font_cache.get(14), (255, 255, 255),
              center=(WINDOW_WIDTH / 2, 650), shadow=True)
    return buttons


def draw_game_over_screen(surface: pygame.Surface, font_cache: FontCache,
                          mouse_pos: Tuple[int, int], score: int,
                          best: int, fade: float) -> List[Button]:
    """Game Over panel with final score, best and Restart."""
    draw_fade(surface, int(150 * fade))
    panel = pygame.Rect(40, 180, WINDOW_WIDTH - 80, 340)
    pygame.draw.rect(surface, (255, 255, 255, 235), panel,
                     border_radius=24)

    draw_text(surface, "GAME OVER", font_cache.get(44, bold=True),
              (230, 84, 60), center=(WINDOW_WIDTH / 2, 240))
    draw_text(surface, "Final score", font_cache.get(18),
              UI_SUBTEXT_COLOR, center=(WINDOW_WIDTH / 2, 290))
    draw_text(surface, str(score), font_cache.get(64, bold=True),
              UI_TEXT_COLOR, center=(WINDOW_WIDTH / 2, 345))
    draw_text(surface, f"BEST  {best}", font_cache.get(22, bold=True),
              UI_SUBTEXT_COLOR, center=(WINDOW_WIDTH / 2, 400))

    restart = Button(pygame.Rect(WINDOW_WIDTH / 2 - 90, 430, 180, 58),
                     "RESTART", "restart")
    restart.draw(surface, font_cache, mouse_pos)
    return [restart]


def draw_win_screen(surface: pygame.Surface, font_cache: FontCache,
                    mouse_pos: Tuple[int, int], score: int,
                    best: int, fade: float) -> List[Button]:
    """Victory panel with confetti background already drawn by caller."""
    glow = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    glow.fill((*WIN_OVERLAY, int(90 * fade)))
    surface.blit(glow, (0, 0))

    panel = pygame.Rect(40, 180, WINDOW_WIDTH - 80, 340)
    pygame.draw.rect(surface, (255, 255, 255, 235), panel,
                     border_radius=24)

    draw_text(surface, "YOU WIN!", font_cache.get(48, bold=True),
              (230, 150, 40), center=(WINDOW_WIDTH / 2, 240), shadow=True)
    draw_text(surface, "You reached the magic tile!",
              font_cache.get(18), UI_SUBTEXT_COLOR,
              center=(WINDOW_WIDTH / 2, 285))
    draw_text(surface, str(score), font_cache.get(64, bold=True),
              UI_TEXT_COLOR, center=(WINDOW_WIDTH / 2, 345))
    draw_text(surface, f"BEST  {best}", font_cache.get(22, bold=True),
              UI_SUBTEXT_COLOR, center=(WINDOW_WIDTH / 2, 400))

    restart = Button(pygame.Rect(WINDOW_WIDTH / 2 - 90, 430, 180, 58),
                     "PLAY AGAIN", "restart")
    restart.draw(surface, font_cache, mouse_pos)
    return [restart]


def draw_pause_screen(surface: pygame.Surface, font_cache: FontCache,
                      mouse_pos: Tuple[int, int]) -> List[Button]:
    """Pause menu: Resume, Restart, or back to the difficulty selector."""
    draw_fade(surface, 150)
    panel = pygame.Rect(100, 220, WINDOW_WIDTH - 200, 300)
    pygame.draw.rect(surface, (255, 255, 255, 235), panel,
                     border_radius=24)

    draw_text(surface, "PAUSED", font_cache.get(40, bold=True),
              UI_TEXT_COLOR, center=(WINDOW_WIDTH / 2, 270))

    resume = Button(pygame.Rect(WINDOW_WIDTH / 2 - 90, 310, 180, 54),
                    "RESUME", "resume")
    resume.draw(surface, font_cache, mouse_pos)
    restart = Button(pygame.Rect(WINDOW_WIDTH / 2 - 90, 376, 180, 54),
                     "RESTART", "restart")
    restart.draw(surface, font_cache, mouse_pos)
    menu = Button(pygame.Rect(WINDOW_WIDTH / 2 - 90, 442, 180, 54),
                  "MENU", "menu")
    menu.draw(surface, font_cache, mouse_pos)
    return [resume, restart, menu]


def draw_mute_button(surface: pygame.Surface, font_cache: FontCache,
                     muted: bool, mouse_pos: Tuple[int, int]) -> Button:
    """Small sound toggle pill in the bottom-right corner."""
    rect = pygame.Rect(WINDOW_WIDTH - 148, WINDOW_HEIGHT - 50, 134, 38)
    button = Button(rect, "", "mute")
    hovered = button.hit(mouse_pos)
    color = (255, 255, 255, 205) if not hovered else (255, 255, 255, 245)
    pill = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(pill, color, pill.get_rect(), border_radius=19)
    surface.blit(pill, rect)
    label = "SOUND OFF" if muted else "SOUND ON"
    draw_text(surface, label, font_cache.get(15, bold=True), UI_TEXT_COLOR,
              center=rect.center)
    return button


def draw_merge_popups(surface: pygame.Surface, font_cache: FontCache,
                      popups: Sequence) -> None:
    """Small '+N' texts that float up and fade after a merge."""
    font = font_cache.get(24, bold=True)
    for text, x, y, ttl, total in popups:
        progress = 1.0 - ttl / total if total > 0 else 1.0
        alpha = int(255 * (1.0 - progress))
        rendered = font.render(text, True, (255, 255, 255))
        rendered.set_alpha(max(0, min(255, alpha)))
        rect = rendered.get_rect(center=(int(x), int(y - progress * 46)))
        surface.blit(rendered, rect)


