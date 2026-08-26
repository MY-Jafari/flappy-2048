"""
Unit tests for the pygame-free core logic (game_logic, player, obstacle).
Run with:  python -m unittest tests.test_logic
"""

import random
import unittest

import game_logic
from game_logic import (
    clamp, ease_out_cubic, inset_rect, lerp, merge_numbers,
    pick_column_number, powers_of_two, rects_overlap, smaller_powers_of_two,
    speed_at,
)
from obstacle import Obstacle, spawn_obstacle
from player import Player


class MergeTests(unittest.TestCase):
    def test_equal_values_add(self):
        self.assertEqual(merge_numbers(2, 2), 4)
        self.assertEqual(merge_numbers(16, 16), 32)
        self.assertEqual(merge_numbers(1024, 1024), 2048)

    def test_unequal_values_do_not_merge(self):
        self.assertIsNone(merge_numbers(2, 4))
        self.assertIsNone(merge_numbers(8, 2))
        self.assertIsNone(merge_numbers(2, 2048))


class PowersTests(unittest.TestCase):
    def test_powers_of_two(self):
        self.assertEqual(powers_of_two(2), [2])
        self.assertEqual(powers_of_two(8), [2, 4, 8])
        self.assertEqual(powers_of_two(2048), [2, 4, 8, 16, 32, 64,
                                               128, 256, 512, 1024, 2048])

    def test_smaller_powers(self):
        self.assertEqual(smaller_powers_of_two(2), [])
        self.assertEqual(smaller_powers_of_two(8), [2, 4])
        self.assertEqual(smaller_powers_of_two(4), [2])


class PickNumberTests(unittest.TestCase):
    def test_number_pool_is_always_valid(self):
        rng = random.Random(42)
        for value in (2, 4, 8, 16, 64, 512):
            for _ in range(500):
                number = pick_column_number(value, rng)
                self.assertIn(number, powers_of_two(value))

    def test_mostly_matches_player_value(self):
        rng = random.Random(7)
        value = 16
        draws = [pick_column_number(value, rng) for _ in range(2000)]
        matches = sum(1 for d in draws if d == value)
        self.assertGreater(matches / len(draws), 0.55)

    def test_value_two_always_matches(self):
        rng = random.Random(3)
        for _ in range(200):
            self.assertEqual(pick_column_number(2, rng), 2)


class SpeedTests(unittest.TestCase):
    def test_speed_starts_at_base_and_grows(self):
        self.assertEqual(speed_at(0, 150, 0.0045, 330), 150)
        self.assertGreater(speed_at(1000, 150, 0.0045, 330), 150)
        self.assertGreater(speed_at(5000, 150, 0.0045, 330),
                           speed_at(1000, 150, 0.0045, 330))

    def test_speed_is_capped(self):
        self.assertEqual(speed_at(10 ** 9, 150, 0.0045, 330), 330)


class CollisionTests(unittest.TestCase):
    def test_overlap(self):
        self.assertTrue(rects_overlap(0, 0, 10, 10, 5, 5, 10, 10))

    def test_no_overlap(self):
        self.assertFalse(rects_overlap(0, 0, 10, 10, 20, 0, 10, 10))
        self.assertFalse(rects_overlap(0, 0, 10, 10, 0, 20, 10, 10))

    def test_obstacle_body_hit(self):
        obs = Obstacle(100, gap_y=200, gap_height=100, width=80,
                       number=2, world_height=720)
        # Player fully inside the gap: no body hit
        self.assertFalse(obs.hits_body((90, 175, 50, 50)))
        # Player crossing the top block
        self.assertTrue(obs.hits_body((90, 80, 50, 50)))
        # Player crossing the bottom block
        self.assertTrue(obs.hits_body((90, 280, 50, 50)))

    def test_obstacle_badge_hit(self):
        obs = Obstacle(100, gap_y=200, gap_height=100, width=80,
                       number=2, world_height=720)
        # Player centered on the badge
        self.assertTrue(obs.hits_badge((100, 180, 50, 50), badge_size=52))
        # Player far below the badge
        self.assertFalse(obs.hits_badge((100, 280, 50, 50), badge_size=52))

    def test_spawn_keeps_gap_inside_screen(self):
        rng = random.Random(11)
        for _ in range(300):
            obs = spawn_obstacle(rng, player_value=4,
                                 world_width=480, world_height=720,
                                 gap_height=205, column_width=90,
                                 gap_margin=115)
            self.assertGreaterEqual(obs.gap_top, 0)
            self.assertLessEqual(obs.gap_bottom, 720)


class PlayerTests(unittest.TestCase):
    def test_jump_and_gravity(self):
        player = Player(100, 300, 56, value=2)
        player.jump(-560)
        self.assertEqual(player.vy, -560)
        player.update(1 / 60, gravity=1500, max_fall_speed=950)
        self.assertLess(player.vy, 0)          # still rising
        self.assertLess(player.y, 300)         # moved up

    def test_merge_updates_value_and_pulse(self):
        player = Player(100, 300, 56, value=2)
        player.merge_with(2, pulse_time=0.3)
        self.assertEqual(player.value, 4)
        self.assertGreater(player.pulse, 0)

    def test_tilt_direction(self):
        player = Player(100, 300, 56)
        player.vy = -500  # rising -> tilts up (positive degrees)
        self.assertGreater(player.tilt_degrees(0.06, 35, 60), 0)
        player.vy = 500   # falling -> tilts down (negative degrees)
        self.assertLess(player.tilt_degrees(0.06, 35, 60), 0)


class HelperTests(unittest.TestCase):
    def test_clamp(self):
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-3, 0, 10), 0)
        self.assertEqual(clamp(99, 0, 10), 10)

    def test_lerp_and_easing(self):
        self.assertEqual(lerp(0, 10, 0.5), 5)
        self.assertEqual(lerp(0, 10, 2.0), 10)      # clamped
        self.assertEqual(ease_out_cubic(0), 0)
        self.assertEqual(ease_out_cubic(1), 1)
        self.assertAlmostEqual(ease_out_cubic(0.5), 0.875)

    def test_inset_rect_shrinks_on_every_side(self):
        self.assertEqual(inset_rect((0, 0, 10, 10), 2), (2, 2, 6, 6))

    def test_inset_rect_never_collapses(self):
        # Dimensions are clamped to at least 1px for extreme insets.
        self.assertEqual(inset_rect((5, 5, 4, 4), 100), (105, 105, 1.0, 1.0))


if __name__ == "__main__":
    unittest.main()
