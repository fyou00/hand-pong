"""Kemampuan per pemain; timer mengikuti waktu permainan aktif."""
import math
import config
from sound import sound


class Ability:
    def __init__(self):
        self.cooldown = 0.
        self.active = 0.
        self.combo = 0

    def update(self, dt, fist):
        self.cooldown = max(0., self.cooldown-dt)
        self.active = max(0., self.active-dt)
        if fist and self.cooldown == 0:
            self.active = config.POWER_DURATION
            self.cooldown = config.POWER_COOLDOWN
            sound.play('charge')

    def hit(self, ball, maximum):
        if self.active > 0:
            speed = math.hypot(ball.vx, ball.vy)
            factor = min(config.POWER_MULTIPLIER, maximum*config.POWER_MULTIPLIER/speed)
            ball.vx *= factor
            ball.vy *= factor
            ball.power = True
            self.active = 0.
            sound.play('power')
        self.combo += 1
        if self.combo == 3:
            self.combo = 0
            self.cooldown = 0.
            sound.play('combo')

    def rally_end(self):
        self.combo = 0
        self.active = 0.

    def label(self):
        state = 'AKTIF' if self.active else f'{self.cooldown:.1f}s' if self.cooldown else 'SIAP'
        return f'C:{self.combo}/3 POWER:{state}'
