"""
settings.py — Central configuration for Flappy 2048.

Every tunable value of the game lives here so the game can be
rebalanced without touching the logic or rendering code.

This module is pure data — it never imports pygame.
"""

# ---------------------------------------------------------------------------
# Window / timing
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 480
WINDOW_HEIGHT = 720
FPS = 60
CAPTION = "Flappy 2048"

# ---------------------------------------------------------------------------
# Player (the cube)
# ---------------------------------------------------------------------------
PLAYER_SIZE = 56          # width/height of the cube in pixels
PLAYER_X = WINDOW_WIDTH * 0.28   # fixed horizontal position of the cube
START_VALUE = 2           # the number printed on the cube when a run starts
WIN_VALUE = 2048          # reaching this number wins the game

# Physics (per second, so delta-time based)
GRAVITY = 1500.0          # px/s^2, downward acceleration
JUMP_VELOCITY = -560.0    # px/s, upward velocity applied on jump
MAX_FALL_SPEED = 950.0    # px/s, terminal velocity while falling
TILT_SPEED_FACTOR = 0.06  # cube rotation (degrees) per px/s of vertical speed
MAX_TILT_UP = 35.0        # max tilt (degrees) while rising
MAX_TILT_DOWN = 60.0      # max tilt (degrees) while falling

# Merge feedback
MERGE_PULSE_TIME = 0.30   # seconds the cube scales up after a merge
MERGE_PULSE_SCALE = 1.35  # peak scale factor during the pulse

# ---------------------------------------------------------------------------
# Columns (obstacles)
# ---------------------------------------------------------------------------
COLUMN_WIDTH = 90
GAP_HEIGHT = 205          # vertical opening the player must fly through
GAP_MARGIN = 115          # min distance from gap center to top/bottom edge
COLUMN_SPACING = 250      # horizontal distance between consecutive columns

# Difficulty: speed grows with distance traveled (only speed increases,
# gap size stays constant — as decided in the design interview).
BASE_SPEED = 150.0        # px/s at the start of a run
SPEED_ACCEL = 0.0045      # px/s gained per pixel of distance traveled
MAX_SPEED = 330.0         # speed cap

BADGE_SIZE = 52           # size of the number block attached to the gap

# ---------------------------------------------------------------------------
# Animation / background
# ---------------------------------------------------------------------------
DEATH_ANIM_TIME = 1.0     # seconds the game-over animation lasts
WIN_ANIM_TIME = 2.2       # seconds confetti rains before the win screen
SCREEN_FADE_TIME = 0.45   # seconds of fade used when a screen appears
RESTART_COOLDOWN = 0.6    # seconds after death/win before input is accepted
CLOUD_COUNT = 6
CLOUD_MIN_SPEED = 10.0    # px/s
CLOUD_MAX_SPEED = 26.0

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
# Comic Sans MS gives the rounded cartoon look and ships with Windows;
# on other platforms pygame falls back to its bundled font automatically.
FONT_NAME = "comicsansms"

# ---------------------------------------------------------------------------
# Colors (cartoon-ish 2048 palette, warm and saturated)
# ---------------------------------------------------------------------------
SKY_TOP = (126, 200, 245)
SKY_BOTTOM = (196, 232, 248)
CLOUD_COLOR = (255, 255, 255)

COLUMN_COLOR = (110, 190, 84)       # cartoon green for the column body
COLUMN_EDGE_COLOR = (84, 156, 64)   # darker outline
COLUMN_EDGE_WIDTH = 3

# Number colors follow the classic 2048 palette with extra saturation.
TILE_COLORS = {
    2:    (240, 228, 218),
    4:    (240, 222, 198),
    8:    (244, 178, 122),
    16:   (246, 150, 100),
    32:   (247, 124, 96),
    64:   (247, 94, 60),
    128:  (240, 208, 112),
    256:  (240, 204, 96),
    512:  (240, 198, 78),
    1024: (240, 194, 60),
    2048: (240, 190, 44),
}
TILE_TEXT_DARK = (119, 110, 101)     # text on the light tiles (2, 4)
TILE_TEXT_LIGHT = (255, 248, 240)    # text on the warm tiles (8+)

UI_BUTTON_COLOR = (255, 154, 62)     # warm orange, cartoon feel
UI_BUTTON_EDGE = (214, 110, 24)
UI_BUTTON_HOVER = (255, 172, 92)
UI_TITLE_COLOR = (255, 255, 255)
UI_TEXT_COLOR = (66, 62, 58)
UI_SUBTEXT_COLOR = (110, 104, 96)

FADE_COLOR = (24, 20, 26)            # color used to fade screens in/out
WIN_OVERLAY = (255, 244, 180)        # warm glow behind the win screen

CONFETTI_COLORS = [
    (247, 124, 96), (240, 208, 112), (110, 190, 84),
    (126, 200, 245), (214, 140, 240), (255, 154, 62),
]

# ---------------------------------------------------------------------------
# Difficulty levels
# ---------------------------------------------------------------------------
# Each level tunes the columns (speed, gap, spacing) AND the cube
# (size, gravity, jump) as decided in the design interview.
DEFAULT_DIFFICULTY = "medium"
DIFFICULTY_ORDER = ["easy", "medium", "hard"]

DIFFICULTIES = {
    # EASY: really easy — huge gaps, slow scroll, floaty high jumps,
    # lots of breathing room between columns.
    "easy": {
        "label": "EASY",
        "player_size": 52,
        "gravity": 1300.0,
        "jump_velocity": -580.0,
        "gap_height": 246.0,
        "base_speed": 115.0,
        "speed_accel": 0.0030,
        "column_spacing": 280.0,
    },
    "medium": {
        "label": "MEDIUM",
        # Medium: balanced, slightly more forgiving than the original.
        "player_size": PLAYER_SIZE,
        "gravity": GRAVITY,
        "jump_velocity": JUMP_VELOCITY,
        "gap_height": 215.0,
        "base_speed": 140.0,
        "speed_accel": 0.0038,
        "column_spacing": 250.0,
    },
    "hard": {
        "label": "HARD",
        # HARD: tight gaps, fast columns, heavy cube and weaker jumps —
        # challenging, but the bot should still sometimes win.
        "player_size": 60,
        "gravity": 1600.0,
        "jump_velocity": -530.0,
        "gap_height": 190.0,
        "base_speed": 170.0,
        "speed_accel": 0.0055,
        "column_spacing": 240.0,
    },
}

# UI colors for the difficulty selector
UI_SELECT_COLOR = (96, 196, 112)          # green: currently selected level
UI_SELECT_EDGE = (56, 148, 74)

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
import os

BEST_SCORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "best_score.json")
