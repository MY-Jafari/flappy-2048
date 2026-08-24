"""
main.py — Flappy 2048 entry point and game loop.

Runs `python main.py` to play.

This module owns the pygame event loop and the state machine
(START -> PLAYING -> DYING/GAME_OVER, PLAYING -> WINNING/WIN and
PLAYING <-> PAUSED), and wires the pure logic modules (player,
obstacle, game_logic) to the rendering layer (ui) and the sound
manager.

Hidden cheat: while playing (or paused) type "2048" on the number
row to jump straight to the win screen.

Run a headless self-check with:
    python main.py --selftest
"""

from __future__ import annotations

import enum
import math
import random
import sys

import pygame

import ui
from game_logic import merge_numbers, speed_at
from obstacle import Obstacle, spawn_obstacle
from player import Player
from settings import (
    BADGE_SIZE, BEST_SCORE_PATH, CAPTION, COLUMN_WIDTH, DEATH_ANIM_TIME,
    DIFFICULTIES, FPS, GAP_MARGIN, MAX_FALL_SPEED, MAX_SPEED,
    MERGE_PULSE_TIME, PLAYER_X, RESTART_COOLDOWN, SCREEN_FADE_TIME,
    START_VALUE, WIN_ANIM_TIME, WIN_VALUE, WINDOW_HEIGHT, WINDOW_WIDTH,
)
from sound import SoundManager
from storage import (load_best_scores, load_level, load_muted, set_level,
                     set_muted, update_best_score)


class State(enum.Enum):
    START = enum.auto()
    PLAYING = enum.auto()
    PAUSED = enum.auto()     # game frozen, small menu shown
    DYING = enum.auto()      # game-over animation playing
    WINNING = enum.auto()    # confetti celebration playing
    GAME_OVER = enum.auto()
    WIN = enum.auto()


class Game:
    """The whole game: state machine, update loop and rendering."""

    def __init__(self, best_path: str = BEST_SCORE_PATH) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(CAPTION)
        self.clock = pygame.time.Clock()

        self.fonts = ui.FontCache()
        self.sound = SoundManager()
        self.rng = random.Random()

        self.sky = ui.make_sky(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.clouds = ui.Clouds(self.rng)
        self.confetti = None

        # The storage path is injectable so tests (and future ports) can
        # run against an isolated state file.
        self.best_path = best_path
        self.best = load_best_scores(self.best_path)   # per-level dict
        self.level = load_level(self.best_path)
        self.muted = load_muted(self.best_path)
        self.sound.muted = self.muted
        self.mouse_pos = (0, 0)
        self.screen_buttons = []
        self.popups = []
        self._cheat = ""

        self.state = State.START
        self.state_time = 0.0
        self.reset_run()

    # ------------------------------------------------------------------
    # Run lifecycle
    # ------------------------------------------------------------------

    def reset_run(self) -> None:
        """Reset everything for a fresh run (still keeps state/state_time)."""
        self.diff = DIFFICULTIES[self.level]   # parameters of this level
        self.player = Player(PLAYER_X, WINDOW_HEIGHT * 0.45,
                             self.diff["player_size"], START_VALUE)
        self.obstacles = []
        self.distance = 0.0
        self.distance_since_spawn = 0.0
        self.popups = []
        self._cheat = ""

    def run(self) -> None:
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)  # clamp big jumps
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._save_progress()
                    running = False
                else:
                    self._handle_event(event)
            self._update(dt)
            self._draw()
            pygame.display.flip()
        pygame.quit()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def _primary_action(self) -> None:
        """Jump (playing) or advance the current screen."""
        if self.state is State.PLAYING:
            self.player.jump(self.diff["jump_velocity"])
            self.sound.play_jump()
        elif self.state is State.PAUSED:
            self.state = State.PLAYING  # space also resumes
        elif self.state is State.START:
            self._start_run()
        elif self.state in (State.GAME_OVER, State.WIN):
            if self.state_time >= RESTART_COOLDOWN:
                self._start_run()

    # Digit keys used by the hidden cheat code.
    DIGIT_KEYS = {
        pygame.K_0: "0", pygame.K_1: "1", pygame.K_2: "2", pygame.K_3: "3",
        pygame.K_4: "4", pygame.K_5: "5", pygame.K_6: "6", pygame.K_7: "7",
        pygame.K_8: "8", pygame.K_9: "9",
        pygame.K_KP0: "0", pygame.K_KP1: "1", pygame.K_KP2: "2",
        pygame.K_KP3: "3", pygame.K_KP4: "4", pygame.K_KP5: "5",
        pygame.K_KP6: "6", pygame.K_KP7: "7", pygame.K_KP8: "8",
        pygame.K_KP9: "9",
    }

    def _handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                # The QUIT handler saves progress before exiting.
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            elif event.key == pygame.K_p:
                self._toggle_pause()
            elif event.key == pygame.K_m:
                self._toggle_mute()
            elif event.key in self.DIGIT_KEYS:
                self._type_cheat_digit(self.DIGIT_KEYS[event.key])
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN,
                               pygame.K_UP, pygame.K_w):
                self._primary_action()
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
        elif event.type == pygame.WINDOWFOCUSLOST:
            # Auto-pause when the window loses focus (no unfair deaths).
            if self.state is State.PLAYING:
                self.state = State.PAUSED
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state in (State.PLAYING, State.PAUSED):
                for button in self.screen_buttons:
                    if button.hit(event.pos):
                        if button.action == "mute":
                            self._toggle_mute()
                        elif button.action == "resume":
                            self.state = State.PLAYING
                        elif button.action == "restart":
                            self._start_run()
                        elif button.action == "menu":
                            self._to_menu()
                        return
                if self.state is State.PLAYING:
                    self.player.jump(self.diff["jump_velocity"])
                    self.sound.play_jump()
            elif self.state is State.START:
                for button in self.screen_buttons:
                    if button.hit(event.pos) and \
                            button.action.startswith("level:"):
                        self._set_level(button.action[len("level:"):])
                        self._start_run()
                        return
                # Clicking anywhere else on the title screen starts the
                # game with the currently selected difficulty.
                self._start_run()
            elif self.state in (State.GAME_OVER, State.WIN):
                if self.state_time >= RESTART_COOLDOWN:
                    for button in self.screen_buttons:
                        if button.hit(event.pos):
                            if button.action == "restart":
                                self._start_run()
                            break

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def _toggle_pause(self) -> None:
        if self.state is State.PLAYING:
            self.state = State.PAUSED
        elif self.state is State.PAUSED:
            self.state = State.PLAYING

    def _toggle_mute(self) -> None:
        self.muted = not self.muted
        self.sound.muted = self.muted
        set_muted(self.muted, self.best_path)

    def _set_level(self, level: str) -> None:
        """Switch difficulty and remember the choice for next launch."""
        if level not in DIFFICULTIES:
            return
        self.level = level
        set_level(level, self.best_path)

    def _to_menu(self) -> None:
        """Return to the start screen (from the pause menu)."""
        self.reset_run()
        self.state = State.START
        self.state_time = 0.0

    def _type_cheat_digit(self, digit: str) -> None:
        """Hidden cheat: typing 2048 (playing or paused) jumps to the win."""
        if self.state not in (State.PLAYING, State.PAUSED):
            return
        self._cheat = (self._cheat + digit)[-4:]
        if self._cheat == "2048":
            self._cheat = ""
            self.player.value = WIN_VALUE
            self.popups.append((f"+{WIN_VALUE} CHEAT!",
                                self.player.x + self.player.size / 2.0,
                                self.player.top - 12, 1.2, 1.2))

    def _start_run(self) -> None:
        self.reset_run()
        self.state = State.PLAYING
        self.state_time = 0.0

    def _die(self) -> None:
        self.state = State.DYING
        self.state_time = 0.0
        self.best[self.level] = update_best_score(
            self.player.value, self.level, self.best_path)
        self.sound.play_hit()

    def _win(self) -> None:
        self.state = State.WINNING
        self.state_time = 0.0
        self.confetti = ui.Confetti(90, self.rng)
        self.best[self.level] = update_best_score(
            self.player.value, self.level, self.best_path)
        self.sound.play_win()

    def _save_progress(self) -> None:
        """Persist the best score even if the player quits mid-run."""
        if self.state in (State.PLAYING, State.PAUSED, State.DYING,
                          State.WINNING):
            self.best[self.level] = update_best_score(
                self.player.value, self.level, self.best_path)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def _update(self, dt: float) -> None:
        self.state_time += dt
        if self.state is State.PAUSED:
            return  # full pause: scene and clouds stay frozen
        self.clouds.update(dt)

        if self.popups:
            self.popups = [(t, x, y, ttl - dt, total)
                           for t, x, y, ttl, total in self.popups
                           if ttl - dt > 0]

        if self.state is State.PLAYING:
            self._update_playing(dt)
        elif self.state is State.DYING:
            if self.state_time >= DEATH_ANIM_TIME:
                self.state = State.GAME_OVER
                self.state_time = 0.0
        elif self.state is State.WINNING:
            self.confetti.update(dt)
            if self.state_time >= WIN_ANIM_TIME:
                self.state = State.WIN
                self.state_time = 0.0

    def _update_playing(self, dt: float) -> None:
        self.speed = speed_at(self.distance, self.diff["base_speed"],
                              self.diff["speed_accel"], MAX_SPEED)
        self.distance += self.speed * dt

        self.player.update(dt, self.diff["gravity"], MAX_FALL_SPEED)

        # Spawn a new column once enough distance has been covered.
        self.distance_since_spawn += self.speed * dt
        if self.distance_since_spawn >= self.diff["column_spacing"]:
            self.distance_since_spawn -= self.diff["column_spacing"]
            self.obstacles.append(spawn_obstacle(
                self.rng, self.player.value, WINDOW_WIDTH, WINDOW_HEIGHT,
                self.diff["gap_height"], COLUMN_WIDTH, GAP_MARGIN))

        for obstacle in self.obstacles:
            obstacle.update(dt, self.speed)

        player_rect = self.player.rect()
        for obstacle in self.obstacles:
            if obstacle.hits_body(player_rect):
                self._die()
                return
            if not obstacle.merged and obstacle.hits_badge(player_rect,
                                                           BADGE_SIZE):
                self._merge(obstacle)

        # Out of bounds (floor / ceiling) also ends the run.
        if self.player.top < 0 or self.player.bottom > WINDOW_HEIGHT:
            self._die()
            return

        if self.player.value >= WIN_VALUE:
            self._win()
            return

        self.obstacles = [ob for ob in self.obstacles if not ob.off_screen()]

    def _merge(self, obstacle: Obstacle) -> None:
        """2048-style merge: equal values add up (2+2=4)."""
        merged = merge_numbers(self.player.value, obstacle.number)
        if merged is None:
            return  # a "dud" badge (smaller power of two) — nothing happens
        self.player.merge_with(obstacle.number, MERGE_PULSE_TIME)
        obstacle.merged = True
        self.sound.play_merge()
        self.popups.append((f"+{obstacle.number}",
                            self.player.x + self.player.size / 2.0,
                            self.player.top - 12, 0.9, 0.9))

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self) -> None:
        self.screen.blit(self.sky, (0, 0))
        self.clouds.draw(self.screen)

        in_play = self.state in (State.PLAYING, State.PAUSED, State.DYING,
                                 State.WINNING, State.GAME_OVER, State.WIN)
        if in_play:
            for obstacle in self.obstacles:
                ui.draw_obstacle(self.screen, obstacle, self.fonts)

            angle_offset = 0.0
            alpha = 255
            shake = 0.0
            if self.state is State.DYING:
                progress = min(self.state_time / DEATH_ANIM_TIME, 1.0)
                angle_offset = self.state_time * 540.0        # spin
                shake = 9.0 * (1.0 - progress) * math.sin(progress * 45.0)
                if progress > 0.6:
                    alpha = int(255 * (1.0 - (progress - 0.6) / 0.4))
            ui.draw_player(self.screen, self.player, self.fonts,
                           angle_offset=angle_offset, alpha=alpha,
                           offset_x=shake)

            if self.state in (State.PLAYING, State.PAUSED, State.DYING,
                              State.WINNING):
                ui.draw_hud(self.screen, self.fonts, self.player.value,
                            self.best[self.level])
                ui.draw_merge_popups(self.screen, self.fonts, self.popups)

        if self.state is State.START:
            self.screen_buttons = ui.draw_start_screen(
                self.screen, self.fonts, self.mouse_pos, self.level,
                self.best)
        elif self.state is State.GAME_OVER:
            fade = min(self.state_time / SCREEN_FADE_TIME, 1.0)
            self.screen_buttons = ui.draw_game_over_screen(
                self.screen, self.fonts, self.mouse_pos, self.player.value,
                self.best[self.level], fade)
        elif self.state in (State.WINNING, State.WIN):
            if self.confetti is not None:
                self.confetti.draw(self.screen)
            fade = min(self.state_time / SCREEN_FADE_TIME, 1.0)
            self.screen_buttons = ui.draw_win_screen(
                self.screen, self.fonts, self.mouse_pos, self.player.value,
                self.best[self.level], fade)
        elif self.state is State.PLAYING:
            self.screen_buttons = [ui.draw_mute_button(
                self.screen, self.fonts, self.muted, self.mouse_pos)]
        elif self.state is State.PAUSED:
            pause_buttons = ui.draw_pause_screen(
                self.screen, self.fonts, self.mouse_pos)
            mute_button = ui.draw_mute_button(
                self.screen, self.fonts, self.muted, self.mouse_pos)
            self.screen_buttons = pause_buttons + [mute_button]




def selftest() -> None:
    """Headless sanity run: exercises states without a visible window.

    Uses a temporary best-score file so the player's real save data is
    never touched.
    """
    import os
    import tempfile
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    game = Game(best_path=tmp.name)
    game._start_run()
    for _ in range(1200):  # ~20 seconds at 60fps
        game._update(1 / 60)
        game._draw()
        if game.state is State.PLAYING:
            game.player.jump(game.diff["jump_velocity"])  # keep it alive-ish
    assert game.state in (State.PLAYING, State.GAME_OVER, State.WIN,
                          State.DYING, State.WINNING)
    os.unlink(tmp.name)
    print("selftest OK - no crashes across ~20s of gameplay")
    pygame.quit()


def main() -> None:
    if "--selftest" in sys.argv:
        selftest()
        return
    Game().run()


if __name__ == "__main__":
    main()
