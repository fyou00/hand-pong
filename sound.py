"""Efek audio sintetis; mixer tidak tersedia -> game tetap berjalan."""

from io import BytesIO
import math
import struct
import wave

import pygame


class SoundEffects:
    def __init__(self):
        self.muted = False
        self.sounds = {}
        self.attempted = False

    def _load(self):
        if self.attempted:
            return
        self.attempted = True
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            notes = {
                "wall": [(330, .045)],
                "hit": [(660, .065)],
                "point": [(660, .09), (880, .13)],
                "miss": [(330, .12), (220, .18)],
                "over": [(330, .12), (220, .15), (110, .3)],
                "win": [(523, .1), (659, .1), (784, .1), (1047, .3)],
            }
            for name, melody in notes.items():
                data = bytearray()
                for frequency, duration in melody:
                    count = int(22050 * duration)
                    for i in range(count):
                        envelope = min(1, i / 110, (count - 1 - i) / 220)
                        value = int(7000 * envelope * math.sin(2 * math.pi * frequency * i / 22050))
                        data.extend(struct.pack('<h', value))
                stream = BytesIO()
                with wave.open(stream, 'wb') as audio:
                    audio.setparams((1, 2, 22050, 0, 'NONE', 'not compressed'))
                    audio.writeframes(data)
                stream.seek(0)
                self.sounds[name] = pygame.mixer.Sound(file=stream)
        except pygame.error:
            self.sounds.clear()

    def play(self, name):
        self._load()
        if not self.muted and name in self.sounds:
            self.sounds[name].play()

    def toggle(self):
        self.muted = not self.muted
        if self.muted and pygame.mixer.get_init():
            pygame.mixer.stop()

    def stop(self):
        if pygame.mixer.get_init():
            pygame.mixer.stop()

    @property
    def label(self):
        if self.attempted and not self.sounds:
            return 'M: AUDIO N/A'
        return 'M: OFF' if self.muted else 'M: ON'


sound = SoundEffects()
