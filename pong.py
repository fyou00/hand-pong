"""Game Pong satu pemain dengan paddle yang digerakkan deteksi tangan (PCD klasik).

Struktur: Ball (fisika bola), Paddle (posisi paddle + smoothing), Game (loop).
Tahap PCD ada di hand_tracker.py, sedangkan loop + render ada di sini.

Dipakai menu.py lewat run_game(screen, clock, tracker). Untuk pengujian tanpa
menu, `python pong.py` tetap bisa dijalankan sendiri.
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
        """Gerak dipecah jadi sub-langkah kecil supaya tidak menembus paddle."""
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
            # Cegah bola memantul vertikal terus (|vx| terlalu kecil).
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
        """Smoothing pakai dt (bebas FPS) dengan konstanta waktu SMOOTH_TAU."""
        alpha = 1.0 - math.exp(-dt / config.SMOOTH_TAU)
        self.cx += (target - self.cx) * alpha
        half = config.PADDLE_W / 2
        self.cx = min(max(self.cx, half), config.WIDTH - half)


class Game:
    """Satu sesi game satu pemain. Layar, clock, dan kamera datang dari menu."""

    def __init__(self, screen, clock, tracker):
        self.screen = screen
        self.clock = clock
        self.tracker = tracker
        self.font = pygame.font.SysFont(None, 36)

        # State baru tiap sesi: keluar ke menu lalu masuk lagi = mulai dari awal.
        self.ball = Ball()
        self.paddle = Paddle()
        self.score = 0
        self.lives = config.LIVES
        self.game_over = False
        self.running = True
        self.keluar_app = False  # True bila jendela ditutup (bukan Esc)
        # Target paddle disimpan, jadi saat tangan hilang paddle diam
        # di posisi terakhir (bukan melompat ke tengah / ke keyboard).
        self.target = config.WIDTH / 2
        # Lama tangan tidak terlihat; keyboard baru aktif setelah HAND_LOST_DELAY.
        self.hilang_dt = 0.0

    # ------------------------------------------------------- jendela debug PCD
    def _buka_debug(self):
        """Jendela debug kecil di pojok kiri atas, tidak menutupi game."""
        cv2.namedWindow(config.DEBUG_WINDOW, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(config.DEBUG_WINDOW, *config.DEBUG_SIZE)
        cv2.moveWindow(config.DEBUG_WINDOW, 0, 0)

    def _tutup_debug(self):
        """Tutup jendela debug saja; kamera tetap dipakai menu."""
        try:
            cv2.destroyWindow(config.DEBUG_WINDOW)
        except cv2.error:
            pass

    # ------------------------------------------------------------------ input
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.keluar_app = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False  # kembali ke menu
                elif event.key == pygame.K_r and self.game_over:
                    self.restart()

    def restart(self):
        self.score = 0
        self.lives = config.LIVES
        self.game_over = False
        self.ball.reset()

    @staticmethod
    def hand_to_paddle(cx, frame_w):
        """Rentang 20%..80% lebar frame dipetakan ke 0..WIDTH."""
        norm = (cx / frame_w - config.HAND_X_MIN) / (config.HAND_X_MAX - config.HAND_X_MIN)
        norm = min(max(norm, 0.0), 1.0)
        return norm * config.WIDTH

    # ------------------------------------------------------------------ update
    def update(self, dt):
        frame, debug, hands = self.tracker.read()
        if frame is None:
            print("Kamera tidak terbaca (frame kosong).")
            self.running = False
            return None, None, {}

        # Posisi diambil dari label tangan; kiri diutamakan.
        anchor = hands.get("Left") or hands.get("Right")
        if anchor is not None:
            self.target = self.hand_to_paddle(anchor[0], frame.shape[1])
            self.hilang_dt = 0.0
        else:
            # Item 2: tangan hilang -> paddle tetap di posisi terakhir. Keyboard
            # baru mengambil alih setelah HAND_LOST_DELAY, jadi tangan yang
            # sebentar keluar dari frame tidak langsung "loncat" ke keyboard.
            self.hilang_dt += dt
            if self.hilang_dt >= config.HAND_LOST_DELAY:
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

        return frame, debug, hands

    # -------------------------------------------------------------------- draw
    def draw(self, debug, hands):
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

        # --- jendela debug PCD: hasil pra-pemrosesan + landmark + anchor ---
        cv2.imshow("Debug - Kamera", debug)
        cv2.waitKey(1)

    # --------------------------------------------------------------------- loop
    def run(self):
        """Loop sesi ini; kembali saat Esc (ke menu) atau jendela ditutup."""
        self._buka_debug()
        try:
            while self.running:
                dt = self.clock.tick(config.FPS) / 1000.0
                dt = min(dt, config.DT_MAX)  # jepit kalau frame sempat macet
                self.handle_events()
                frame, debug, hands = self.update(dt)
                if frame is not None:
                    self.draw(debug, hands)
        finally:
            self._tutup_debug()
        return self.keluar_app


def run_game(screen, clock, tracker):
    """Jalankan satu sesi game satu pemain.

    Kembalikan True bila aplikasi harus ditutup (jendela ditutup), False bila
    pemain menekan Esc dan harus kembali ke menu.
    """
    pygame.display.set_caption("Pong Hand Tracking")
    return Game(screen, clock, tracker).run()


def main():
    """Jalankan game langsung tanpa menu (untuk pengujian)."""
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    clock = pygame.time.Clock()
    tracker = HandTracker()
    try:
        run_game(screen, clock, tracker)
    finally:
        tracker.release()
        cv2.destroyAllWindows()
        pygame.quit()


if __name__ == "__main__":
    main()
