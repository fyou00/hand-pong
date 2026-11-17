import unittest
from types import SimpleNamespace
from unittest.mock import patch
from gestures import classify, GestureState
from abilities import Ability
from ui import PlayState


class GestureTests(unittest.TestCase):
    def test_geometry(self):
        points = [SimpleNamespace(x=0., y=0.) for _ in range(21)]
        self.assertEqual(classify(points, 320, 240), 'unknown')
        for a,b,c in ((5,6,7),(9,10,11),(13,14,15),(17,18,19)):
            points[a] = SimpleNamespace(x=0., y=0.)
            points[b] = SimpleNamespace(x=0., y=.5)
            points[c] = SimpleNamespace(x=0., y=1.)
        self.assertEqual(classify(points, 320, 240), 'open')
        for c in (7,11,15,19):
            points[c] = SimpleNamespace(x=.1, y=0.)
        self.assertEqual(classify(points, 320, 240), 'fist')

    def test_once_and_lost_hand(self):
        for dt in (1/30, 1/60, 1/120):
            state = GestureState()
            events = sum(state.update('fist', dt)['fist'] for _ in range(round(2/dt)))
            self.assertEqual(events, 1)
            state.update('unknown', 1)
            self.assertFalse(state.update('fist', 1)['fist'])
            for _ in range(round(1/dt)):
                state.update('open', dt)
            self.assertTrue(any(state.update('fist', dt)['fist'] for _ in range(round(1/dt))))

    def test_ready(self):
        play = PlayState()
        gestures = {'Left': {'kind': 'open', 'duration': .8}}
        play.gesture_ready(gestures, two=True)
        self.assertFalse(play.ready)
        gestures['Right'] = gestures['Left']
        play.gesture_ready(gestures, two=True)
        self.assertTrue(play.ready)
        self.assertEqual(play.remaining, 3)

    @patch('abilities.sound.play')
    def test_power_combo(self, audio):
        ability = Ability()
        ball = SimpleNamespace(vx=200., vy=200., power=False)
        ability.update(.01, True)
        ability.hit(ball, 500)
        self.assertTrue(ball.power)
        self.assertEqual(ball.vx, 260)
        self.assertEqual(ability.active, 0)
        ability.hit(ball, 500)
        ability.hit(ball, 500)
        self.assertEqual(ability.cooldown, 0)
        self.assertEqual(ability.combo, 0)
        ability.update(.01, True)
        ability.rally_end()
        self.assertEqual(ability.active, 0)
        self.assertGreater(ability.cooldown, 0)
