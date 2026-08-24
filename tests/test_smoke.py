"""
Integration smoke tests: drive the real Game through its states using a
dummy SDL video driver (no window, no audio device needed).

Run with:  python -m unittest tests.test_smoke
"""

import os
import tempfile
import unittest

import pygame

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from main import Game, State            # noqa: E402  (needs env vars first)
from obstacle import Obstacle           # noqa: E402
from settings import (                  # noqa: E402
    COLUMN_SPACING, COLUMN_WIDTH, GAP_HEIGHT, JUMP_VELOCITY,
    RESTART_COOLDOWN, START_VALUE, WIN_ANIM_TIME, WIN_VALUE,
    WINDOW_HEIGHT,
)
from storage import (                   # noqa: E402
    load_best_score, load_muted, save_best_score, set_muted,
    update_best_score,
)

DT = 1 / 60


class GameSmokeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.close()
        self.best_path = tmp.name
        self.game = Game()
        self.game.best_path = self.best_path

    def tearDown(self):
        if os.path.exists(self.best_path):
            os.unlink(self.best_path)

    def step(self, n=1):
        for _ in range(n):
            self.game._update(DT)
            self.game._draw()

    def press_key(self, key):
        self.game._handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=key))

    # -- basic flow -------------------------------------------------------

    def test_start_and_jump(self):
        self.game._start_run()
        self.assertIs(self.game.state, State.PLAYING)
        self.game._primary_action()
        self.assertEqual(self.game.player.vy, JUMP_VELOCITY)
        self.assertEqual(self.game.player.value, START_VALUE)

    def test_obstacles_spawn_and_scroll(self):
        self.game._start_run()
        self.game.distance_since_spawn = COLUMN_SPACING  # force a spawn
        self.step()
        self.assertEqual(len(self.game.obstacles), 1)
        before = self.game.obstacles[0].x
        self.step(10)
        self.assertLess(self.game.obstacles[0].x, before)

    # -- merge ------------------------------------------------------------

    def test_merge_grows_the_cube(self):
        self.game._start_run()
        # Place a matching column right on the player.
        self.game.obstacles.append(Obstacle(
            self.game.player.x - 10, self.game.player.y, GAP_HEIGHT,
            COLUMN_WIDTH, number=self.game.player.value,
            world_height=WINDOW_HEIGHT))
        self.step()
        self.assertEqual(self.game.player.value, START_VALUE * 2)
        self.assertTrue(self.game.obstacles[0].merged)

    def test_dud_badge_does_not_merge(self):
        self.game._start_run()
        self.game.player.value = 8
        self.game.obstacles.append(Obstacle(
            self.game.player.x - 10, self.game.player.y, GAP_HEIGHT,
            COLUMN_WIDTH, number=2, world_height=WINDOW_HEIGHT))
        self.step()
        self.assertEqual(self.game.player.value, 8)
        self.assertFalse(self.game.obstacles[0].merged)

    # -- death ------------------------------------------------------------

    def test_death_by_column_body(self):
        self.game._start_run()
        # Gap far below the player: the top block covers the player.
        self.game.obstacles.append(Obstacle(
            self.game.player.x - 10, self.game.player.y + 400, GAP_HEIGHT,
            COLUMN_WIDTH, number=2, world_height=WINDOW_HEIGHT))
        self.step()
        self.assertIs(self.game.state, State.DYING)

    def test_death_by_floor(self):
        self.game._start_run()
        self.game.player.y = WINDOW_HEIGHT + 200
        self.step()
        self.assertIs(self.game.state, State.DYING)

    def test_game_over_screen_after_anim(self):
        self.game._start_run()
        self.game.player.y = WINDOW_HEIGHT + 200
        self.step()
        self.step(int(1.2 / DT))  # past DEATH_ANIM_TIME
        self.assertIs(self.game.state, State.GAME_OVER)

    def test_restart_resets_everything(self):
        self.game._start_run()
        self.game.player.y = WINDOW_HEIGHT + 200
        self.step()
        self.step(int(1.2 / DT))
        self.assertIs(self.game.state, State.GAME_OVER)
        self.game.state_time = RESTART_COOLDOWN + 0.1
        self.game._primary_action()
        self.assertIs(self.game.state, State.PLAYING)
        self.assertEqual(self.game.player.value, START_VALUE)
        self.assertEqual(self.game.obstacles, [])

    # -- win --------------------------------------------------------------

    def test_win_flow(self):
        self.game._start_run()
        self.game.player.value = WIN_VALUE
        self.step()
        self.assertIs(self.game.state, State.WINNING)
        self.assertIsNotNone(self.game.confetti)
        self.step(int(WIN_ANIM_TIME / DT) + 5)
        self.assertIs(self.game.state, State.WIN)

    def test_best_score_saved_on_death(self):
        self.game._start_run()
        self.game.player.value = 64
        self.game.player.y = WINDOW_HEIGHT + 200
        self.step()
        self.assertEqual(load_best_score(self.best_path), 64)

    # -- pause -----------------------------------------------------------

    def test_pause_freezes_the_game(self):
        self.game._start_run()
        self.press_key(pygame.K_p)
        self.assertIs(self.game.state, State.PAUSED)
        y_before = self.game.player.y
        self.step(5)
        self.assertEqual(self.game.player.y, y_before)  # physics frozen
        self.press_key(pygame.K_p)
        self.assertIs(self.game.state, State.PLAYING)

    def test_space_resumes_pause(self):
        self.game._start_run()
        self.press_key(pygame.K_p)
        self.game._primary_action()
        self.assertIs(self.game.state, State.PLAYING)

    def test_pause_on_focus_loss(self):
        self.game._start_run()
        self.game._handle_event(
            pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertIs(self.game.state, State.PAUSED)

    # -- mute ------------------------------------------------------------

    def test_mute_toggle_and_persist(self):
        self.game._start_run()
        self.assertFalse(self.game.muted)
        self.press_key(pygame.K_m)
        self.assertTrue(self.game.muted)
        self.assertTrue(self.game.sound.muted)
        self.assertTrue(load_muted(self.game.best_path))
        self.press_key(pygame.K_m)
        self.assertFalse(self.game.muted)
        self.assertFalse(load_muted(self.game.best_path))

    # -- hidden cheat ----------------------------------------------------

    def test_cheat_2048_wins(self):
        self.game._start_run()
        for key in (pygame.K_2, pygame.K_0, pygame.K_4, pygame.K_8):
            self.press_key(key)
        self.assertEqual(self.game.player.value, WIN_VALUE)
        self.step()
        self.assertIs(self.game.state, State.WINNING)

    def test_cheat_2048_while_paused(self):
        self.game._start_run()
        self.press_key(pygame.K_p)
        for key in (pygame.K_2, pygame.K_0, pygame.K_4, pygame.K_8):
            self.press_key(key)
        self.assertEqual(self.game.player.value, WIN_VALUE)
        self.press_key(pygame.K_p)
        self.step()
        self.assertIs(self.game.state, State.WINNING)

    def test_partial_cheat_does_nothing(self):
        self.game._start_run()
        for key in (pygame.K_2, pygame.K_0, pygame.K_4):
            self.press_key(key)
        self.assertEqual(self.game.player.value, START_VALUE)


class StorageTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.close()
        self.path = tmp.name

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_roundtrip(self):
        save_best_score(128, self.path)
        self.assertEqual(load_best_score(self.path), 128)

    def test_update_keeps_max(self):
        save_best_score(64, self.path)
        self.assertEqual(update_best_score(32, self.path), 64)
        self.assertEqual(update_best_score(256, self.path), 256)

    def test_missing_file_returns_default(self):
        self.assertEqual(load_best_score(self.path + ".nope"), 0)

    def test_corrupt_file_returns_default(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("not json {")
        self.assertEqual(load_best_score(self.path), 0)

    def test_muted_roundtrip(self):
        self.assertFalse(load_muted(self.path))
        set_muted(True, self.path)
        self.assertTrue(load_muted(self.path))
        set_muted(False, self.path)
        self.assertFalse(load_muted(self.path))

    def test_update_best_preserves_muted(self):
        set_muted(True, self.path)
        update_best_score(64, self.path)
        self.assertEqual(load_best_score(self.path), 64)
        self.assertTrue(load_muted(self.path))


if __name__ == "__main__":
    unittest.main()
