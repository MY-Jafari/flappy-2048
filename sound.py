"""
sound.py — Tiny synthesized sound effects.

All SFX are generated procedurally (sine/square sweeps) at startup —
no audio asset files needed. If the audio device is unavailable the
manager silently disables itself and every play_* call becomes a no-op,
so the game always runs.

Only this module and ui.py (rendering) may touch pygame directly;
the game logic in game_logic.py / player.py / obstacle.py stays clean.
"""

from __future__ import annotations

import math
import struct

import pygame

SAMPLE_RATE = 44100


def _build_sound(samples_per_second: int, volume: float,
                 steps: list) -> pygame.mixer.Sound:
    """Render a mono 16-bit sound from a list of (freq, duration, shape)."""
    data = bytearray()
    for freq, duration, shape in steps:
        n = int(samples_per_second * duration)
        for i in range(n):
            t = i / samples_per_second
            # Exponential decay envelope for a plucky feel.
            envelope = math.exp(-3.2 * t / duration) if duration > 0 else 0.0
            if shape == "sine":
                sample = math.sin(2.0 * math.pi * freq * t)
            elif shape == "square":
                sample = 1.0 if math.sin(2.0 * math.pi * freq * t) >= 0 else -1.0
            else:  # "noise"
                sample = 2.0 * (t * 2654435761 % 1.0) - 1.0
            value = int(sample * envelope * volume * 32767)
            data += struct.pack("<h", max(-32768, min(32767, value)))
    return pygame.mixer.Sound(buffer=bytes(data))


class SoundManager:
    """Builds and plays the game's synthesized sound effects."""

    JUMP = [(420, 0.07, "sine"), (640, 0.08, "sine")]
    MERGE = [(523.25, 0.07, "sine"), (659.25, 0.07, "sine"),
             (783.99, 0.12, "sine")]
    HIT = [(180, 0.16, "square"), (90, 0.20, "sine")]
    WIN = [(523.25, 0.12, "sine"), (659.25, 0.12, "sine"),
           (783.99, 0.12, "sine"), (1046.5, 0.30, "sine")]

    def __init__(self) -> None:
        self.enabled = False
        self._sounds = {}
        try:
            pygame.mixer.init(SAMPLE_RATE, -16, 1, 512)
            self.enabled = True
            self._sounds = {
                "jump": _build_sound(SAMPLE_RATE, 0.35, self.JUMP),
                "merge": _build_sound(SAMPLE_RATE, 0.45, self.MERGE),
                "hit": _build_sound(SAMPLE_RATE, 0.50, self.HIT),
                "win": _build_sound(SAMPLE_RATE, 0.50, self.WIN),
            }
        except pygame.error:
            # No audio device — run silently.
            self.enabled = False

    def play(self, name: str) -> None:
        if self.enabled and name in self._sounds:
            self._sounds[name].play()

    def play_jump(self) -> None:
        self.play("jump")

    def play_merge(self) -> None:
        self.play("merge")

    def play_hit(self) -> None:
        self.play("hit")

    def play_win(self) -> None:
        self.play("win")
