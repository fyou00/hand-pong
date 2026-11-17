"""Statistik sesi dan panel demonstrasi PCD tanpa membuka kamera tambahan."""

import csv
from datetime import datetime
from pathlib import Path
import time

import cv2
import numpy as np
import pygame

import config
from ui import get_font


class Diagnostics:
    def __init__(self, mode):
        self.mode = mode
        self.difficulty = config.DIFFICULTY
        self.demo = False
        self.started = time.perf_counter()
        self.frames = 0
        self.detected = 0
        self.left = 0
        self.right = 0
        self.processing_ms = 0.0
        self.rows = []
        self.last_second = -1
        self.notice = ''
        self.notice_until = 0.0

    def sample(self, hands, processing_ms):
        self.frames += 1
        self.detected += bool(hands)
        self.left += 'Left' in hands
        self.right += 'Right' in hands
        self.processing_ms += processing_ms
        second = int(time.perf_counter() - self.started)
        if second != self.last_second:
            self.rows.append(self.snapshot())
            self.last_second = second

    def snapshot(self):
        elapsed = max(time.perf_counter() - self.started, 1e-6)
        count = max(self.frames, 1)
        return {
            'mode': self.mode, 'difficulty': self.difficulty,
            'elapsed_s': round(elapsed, 3), 'frames': self.frames,
            'fps_avg': round(self.frames / elapsed, 2),
            'processing_ms_avg': round(self.processing_ms / count, 3),
            'detected_pct': round(100 * self.detected / count, 2),
            'left_pct': round(100 * self.left / count, 2),
            'right_pct': round(100 * self.right / count, 2),
        }

    def export(self, directory=None):
        directory = Path(directory) if directory else Path(__file__).parent / 'reports'
        try:
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / f"pcd_{self.mode}_{datetime.now():%Y%m%d_%H%M%S_%f}.csv"
            with path.open('x', newline='', encoding='utf-8') as stream:
                final = self.snapshot()
                writer = csv.DictWriter(stream, fieldnames=final.keys())
                writer.writeheader()
                writer.writerows(self.rows)
                writer.writerow(final)
            self.notice = 'CSV tersimpan di reports/'
            print(f'Statistik PCD: {path}')
            return path
        except OSError as exc:
            self.notice = 'Ekspor CSV gagal; lihat terminal'
            print(f'Ekspor statistik gagal: {exc}')
            return None
        finally:
            self.notice_until = time.perf_counter() + 4

    def event(self, key):
        if key == pygame.K_d:
            self.demo = not self.demo
            cv2.resizeWindow(config.DEBUG_WINDOW, *( (640, 480) if self.demo else config.DEBUG_SIZE))
        elif key == pygame.K_e:
            self.export()

    def draw(self, screen):
        info = self.snapshot()
        text = (f"{self.difficulty} | FPS {info['fps_avg']:.1f} | "
                f"PCD {info['processing_ms_avg']:.1f} ms | Det {info['detected_pct']:.0f}%")
        for y, line in ((4, text), (screen.get_height() - 38,
                self.notice if time.perf_counter() < self.notice_until else 'D: DEMO PCD   E: EKSPOR CSV')):
            image = get_font(11).render(line, True, config.WARNA_REDUP_RGB)
            screen.blit(image, (18, y))

    def image(self, tracker, debug):
        if not self.demo:
            return debug
        stages = tracker.stages
        panels = []
        for title, source in zip(('1. RGB / cermin', '2. CLAHE / LAB',
                                  '3. Gaussian blur', '4. Landmark + anchor / ROI'),
                                 (*stages, debug)):
            panel = source.copy()
            h, w = panel.shape[:2]
            if len(panels) == 3:
                # ROI pemetaan, bukan pembagian kepemilikan tangan.
                if self.mode == 'single':
                    for bound in (config.HAND_X_MIN, config.HAND_X_MAX):
                        x = int(bound * w)
                        cv2.line(panel, (x, 28), (x, h - 1), (113, 232, 229), 1)
                else:
                    for bound in (config.HAND_Y_MIN, config.HAND_Y_MAX):
                        y = int(bound * h)
                        cv2.line(panel, (0, y), (w - 1, y), (113, 232, 229), 1)
            cv2.rectangle(panel, (0, 0), (w, 25), (36, 31, 47), -1)
            cv2.putText(panel, title, (6, 17), cv2.FONT_HERSHEY_SIMPLEX, .4, (240, 235, 235), 1)
            panels.append(panel)
        return np.vstack((np.hstack(panels[:2]), np.hstack(panels[2:])))
