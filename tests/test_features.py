"""Uji fitur demo dan statistik tanpa kamera atau perangkat audio."""
import csv
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import cv2
import numpy as np
import pygame

import config
import menu
import pong
import pong_2p
from diagnostics import Diagnostics
from hand_tracker import HandTracker


class FeaturesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def tearDown(self):
        config.set_difficulty('Normal')

    def test_statistics_and_csv(self):
        with patch('diagnostics.time.perf_counter', return_value=10):
            stats = Diagnostics('single')
        with patch('diagnostics.time.perf_counter', return_value=12):
            stats.sample({'Left': (1, 2)}, 10)
            stats.sample({}, 20)
            stats.sample({'Right': (1, 2)}, 30)
            stats.sample({'Left': (1, 2), 'Right': (3, 4)}, 40)
            result = stats.snapshot()
            self.assertEqual(result['fps_avg'], 2)
            self.assertEqual(result['processing_ms_avg'], 25)
            self.assertEqual(result['detected_pct'], 75)
            self.assertEqual(result['left_pct'], 50)
            self.assertEqual(result['right_pct'], 50)
            with tempfile.TemporaryDirectory() as folder:
                path = stats.export(folder)
                with path.open() as stream:
                    rows = list(csv.DictReader(stream))
                self.assertEqual(rows[-1]['detected_pct'], '75.0')
                with patch.object(Path, 'mkdir', side_effect=OSError('test')):
                    self.assertIsNone(stats.export(folder))

    def test_demo_pipeline_and_session(self):
        tracker = HandTracker.__new__(HandTracker)
        tracker.cap = SimpleNamespace(read=lambda: (True, np.full((480, 640, 3), 90, np.uint8)))
        tracker.clahe = cv2.createCLAHE(2., (8, 8))
        tracker.hands = SimpleNamespace(process=lambda rgb: SimpleNamespace(multi_hand_landmarks=None))
        for module, mode in ((pong, 'single'), (pong_2p, 'two')):
            game = module.Game(self.screen, pygame.time.Clock(), tracker)
            frame, debug, hands = game.update(.016)
            self.assertEqual(frame.shape, (240, 320, 3))
            self.assertEqual(len(tracker.stages), 3)
            self.assertGreater(tracker.processing_ms, 0)
            game.diagnostics.demo = True
            composite = game.diagnostics.image(tracker, debug)
            self.assertEqual(composite.shape, (480, 640, 3))
            game.diagnostics.draw(self.screen)
            with patch('cv2.imshow'), patch('cv2.waitKey'):
                game.draw(debug, hands)
            game.restart()
            self.assertEqual(game.diagnostics.frames, 0)
            self.assertFalse(game.play.ready)

    def test_difficulties_mapping_and_sweep(self):
        for name, width, length in (('Mudah', 150, 150), ('Normal', 120, 120), ('Sulit', 96, 96)):
            config.set_difficulty(name)
            config.set_difficulty(name)
            self.assertEqual(config.PADDLE_W, width)
            self.assertEqual(config.PADDLE_LEN, length)
            self.assertEqual(pong.Game.hand_to_paddle(0, 320), width / 2)
            self.assertEqual(pong_2p.hand_to_paddle(240, 240), 480 - length / 2)
            paddle = pong.Paddle()
            ball = pong.Ball()
            ball.x, ball.y = paddle.cx, paddle.rect.top - config.BALL_R - 2
            ball.vx, ball.vy = 0, config.BALL_SPEED_MAX
            self.assertEqual(ball.update(.05, paddle), 'hit')
            self.assertGreaterEqual(abs(ball.vx), config.MIN_VX)
            for side in ('kiri', 'kanan'):
                paddle2 = pong_2p.Paddle(side)
                ball2 = pong_2p.Ball()
                ball2.y, ball2.vy = paddle2.cy, 0
                ball2.x = paddle2.rect.right + config.BALL_R + 2 if side == 'kiri' else paddle2.rect.left - config.BALL_R - 2
                ball2.vx = -config.BALL_SPEED_MAX_2P if side == 'kiri' else config.BALL_SPEED_MAX_2P
                self.assertEqual(ball2.update(.05, [paddle2]), 'hit')
            menu._gambar(self.screen, menu.make_buttons(), 0)
        config.set_difficulty('Normal')
        self.assertEqual(config.BALL_SPEED_X, 180)


if __name__ == '__main__':
    unittest.main()
