"""Game Pong dengan paddle yang digerakkan deteksi tangan (PCD klasik).

Struktur: Ball (fisika bola), Paddle (posisi paddle + smoothing), Game (loop utama).
Tahap PCD ada di hand_tracker.py, sedangkan loop + render ada di sini.
"""

import math
import random

import cv2
import pygame

import config
from hand_tracker import HandTracker


class Ball:
    """Bola. Semua kecepatan dalam piksel/detik."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.x = config.WIDTH / 2
        self.y = config.HEIGHT / 2
        self.vx = random.choice([-1, 1]) * config.BALL_SPEED_X
        self.vy = -config.BALL_SPEED_Y

    @property
    def rect(self):
        r = config.BALL_R
        return pygame.Rect(int(self.x - r), int(self.y - r), 2 * r, 2 * r)

    def update(self, dt, paddle):
        """Item 10: gerak dipecah jadi sub-langkah kecil supaya tidak menembus paddle."""
        jarak = max(abs(self.vx), abs(self.vy)) * dt
        langkah = max(1, int(math.ceil(jarak / (config.BALL_R / 2))))
        hasil = None
        for _ in range(langkah):
            hasil = self._step(dt / langkah, paddle) or hasil
        return hasil  # None / "hit" / "miss"

    def _step(self, dt, paddle):
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Pantulan dinding kiri/kanan dan atas
        if self.x - config.BALL_R <= 0 or self.x + config.BALL_R >= config.WIDTH:
            self.vx = -self.vx
            self.x = min(max(self.x, config.BALL_R), config.WIDTH - config.BALL_R)
        if self.y - config.BALL_R <= 0:
            self.vy = abs(self.vy)
            self.y = config.BALL_R

        # Pantulan paddle: sudut pantul ditentukan posisi sentuh
        if self.vy > 0 and self.rect.colliderect(paddle.rect):
            offset = (self.x - paddle.cx) / (config.PADDLE_W / 2)  # -1..1
            self.vx = offset * config.BALL_SPEED_X * 2
            # Item 9: cegah bola memantul vertikal terus (|vx| terlalu kecil).
            if abs(self.vx) < config.MIN_VX:
                self.vx = config.MIN_VX if offset >= 0 else -config.MIN_VX
            self.vy = -min(abs(self.vy) * config.BALL_ACCEL, config.BALL_SPEED_MAX)
            self.y = paddle.rect.top - config.BALL_R
            return "hit"

        if self.y - config.BALL_R > config.HEIGHT:
            return "miss"
        return None


class Paddle:
    def __init__(self):
        self.cx = config.WIDTH / 2

    @property
    def rect(self):
        return pygame.Rect(int(self.cx - config.PADDLE_W / 2), config.PADDLE_Y,
                           config.PADDLE_W, config.PADDLE_H)

    def update(self, dt, target):
        """Item 7: smoothing pakai dt (bebas FPS) dengan konstanta waktu SMOOTH_TAU."""
        alpha = 1.0 - math.exp(-dt / config.SMOOTH_TAU)
        self.cx += (target - self.cx) * alpha
        half = config.PADDLE_W / 2
        self.cx = min(max(self.cx, half), config.WIDTH - half)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        pygame.display.set_caption("Pong Hand Tracking")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)

        self.tracker = HandTracker()

        # Jendela debug PCD: kecil, di pojok kiri atas, tidak menutupi game.
        for name, x in (("Debug - Kamera", 0), ("Debug - Mask kulit", 340)):
            cv2.namedWindow(name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(name, *config.DEBUG_SIZE)
            cv2.moveWindow(name, x, 0)

        self.ball = Ball()
        self.paddle = Paddle()
        self.score = 0
        self.lives = config.LIVES
        self.game_over = False
        self.running = True
        # Item 11: target paddle disimpan, jadi saat tangan hilang paddle diam
        # di posisi terakhir (bukan melompat ke tengah / ke keyboard).
        self.target = config.WIDTH / 2

    # ------------------------------------------------------------------ input
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r and self.game_over:
                    self.restart()

    def restart(self):
        self.score = 0
        self.lives = config.LIVES
        self.game_over = False
        self.ball.reset()

    @staticmethod
    def hand_to_paddle(cx, frame_w):
        """Item 6: rentang 20%..80% lebar frame dipetakan ke 0..WIDTH."""
        norm = (cx / frame_w - config.HAND_X_MIN) / (config.HAND_X_MAX - config.HAND_X_MIN)
        norm = min(max(norm, 0.0), 1.0)
        return norm * config.WIDTH

    # ------------------------------------------------------------------ update
    def update(self, dt):
        frame, mask, center, faces = self.tracker.read()
        if frame is None:
            print("Kamera tidak terbaca (frame kosong).")
            self.running = False
            return None, None, None, []

        if center is not None:
            self.target = self.hand_to_paddle(center[0], frame.shape[1])
        else:
            # Tangan hilang: target tetap di posisi terakhir, keyboard hanya
            # menggeser target bila tombol panah ditekan.
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.target -= config.KEY_SPEED * dt
            if keys[pygame.K_RIGHT]:
                self.target += config.KEY_SPEED * dt
            self.target = min(max(self.target, 0), config.WIDTH)

        self.paddle.update(dt, self.target)

        if not self.game_over:
            hasil = self.ball.update(dt, self.paddle)
            if hasil == "hit":
                self.score += 1
            elif hasil == "miss":
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
                else:
                    self.ball.reset()

        return frame, mask, center, faces

    # -------------------------------------------------------------------- draw
    def draw(self, frame, mask, center, faces):
        self.screen.fill((0, 0, 0))
        pygame.draw.rect(self.screen, (255, 255, 255), self.paddle.rect)
        pygame.draw.circle(self.screen, (255, 255, 255),
                           (int(self.ball.x), int(self.ball.y)), config.BALL_R)
        self.screen.blit(self.font.render(f"Skor: {self.score}", True,
                                          (255, 255, 255)), (10, 10))
        self.screen.blit(self.font.render(f"Nyawa: {self.lives}", True,
                                          (255, 255, 255)),
                         (config.WIDTH - 150, 10))
        if self.game_over:
            msg = self.font.render("GAME OVER - tekan R untuk main lagi", True,
                                   (255, 80, 80))
            self.screen.blit(msg, msg.get_rect(center=(config.WIDTH / 2,
                                                       config.HEIGHT / 2)))
        pygame.display.flip()

        # --- jendela debug PCD ---
        for (x, y, w, h) in faces:  # kotak wajah yang diabaikan
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
        if self.tracker.last_rect is not None:  # kandidat tangan
            x, y, w, h = self.tracker.last_rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 1)
        if center is not None:
            cv2.circle(frame, center, 6, (0, 255, 0), -1)
        status = "TANGAN: TERDETEKSI" if center is not None else "TANGAN: TIDAK TERDETEKSI"
        cv2.putText(frame, status, (6, frame.shape[0] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (0, 255, 0) if center is not None else (0, 0, 255), 1)
        cv2.imshow("Debug - Kamera", frame)
        cv2.imshow("Debug - Mask kulit", mask)
        cv2.waitKey(1)

    # --------------------------------------------------------------------- loop
    def run(self):
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            dt = min(dt, 0.05)  # batasi kalau frame sempat macet
            self.handle_events()
            frame, mask, center, faces = self.update(dt)
            if frame is not None:
                self.draw(frame, mask, center, faces)
        self.tracker.release()
        cv2.destroyAllWindows()
        pygame.quit()


def main():
    Game().run()


if __name__ == "__main__":
    main()
