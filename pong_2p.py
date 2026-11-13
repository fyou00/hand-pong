"""Pong dua pemain: paddle kiri dan kanan digerakkan dua tangan dari webcam.

Struktur: Ball (fisika + sweep), Paddle (vertikal + smoothing), Game (loop).
Tahap PCD ada di hand_tracker.py: segmentasi kulit -> kontur terbesar ->
centroid tiap tangan -> dipasangkan ke zona kiri/kanan frame.

Dipakai menu.py lewat run_game(screen, clock, tracker). Untuk pengujian tanpa
menu, `python pong_2p.py` tetap bisa dijalankan sendiri.
"""

import math
import random

import cv2
import pygame

import config
from hand_tracker import HandTracker

def bgr(rgb):
    """Warna config disimpan dalam RGB (pygame); OpenCV butuh BGR."""
    return (rgb[2], rgb[1], rgb[0])

def hand_to_paddle(cy, frame_h):
    """Item 6: rentang 20%..80% tinggi frame dipetakan ke 0..HEIGHT."""
    norm = (cy / frame_h - config.HAND_Y_MIN) / (config.HAND_Y_MAX - config.HAND_Y_MIN)
    norm = min(max(norm, 0.0), 1.0)
    return norm * config.HEIGHT

def assign_zones(hands, frame_w, zona_aktif):
    """Tahap PCD: pasangkan tiap tangan ke zona kiri/kanan frame.

    `hands` urut area terbesar (dari find_hand_centers). Aturannya:
    - tangan di kiri garis tengah -> zona kiri, di kanan -> zona kanan;
    - tangan yang masih di pita mati (ZONE_HYSTERESIS) boleh tetap di zona
      yang frame lalu punya tangan, jadi tangan yang menyilang garis tengah
      tidak langsung berpindah pemain;
    - zona tanpa tangan bernilai None -> paddle diam di posisi terakhir.
    `zona_aktif` diubah di tempat (status zona pada frame ini).
    """
    mid = frame_w / 2.0
    band = config.ZONE_HYSTERESIS * frame_w
    sisa = list(hands)
    hasil = {}
    for zona in ("kiri", "kanan"):
        pilih = None
        for h in sisa:
            x = h[0]
            if zona == "kiri":
                dalam = x < mid or (zona_aktif[zona] and x < mid + band)
            else:
                dalam = x > mid or (zona_aktif[zona] and x > mid - band)
            if dalam:
                pilih = h
                break
        if pilih is not None:
            sisa.remove(pilih)
        hasil[zona] = pilih
        zona_aktif[zona] = pilih is not None

    # Kunci tangan ke zonanya: posisi x dibatasi pada separuh frame miliknya.
    for zona, h in hasil.items():
        if h is None:
            continue
        if zona == "kiri":
            hasil[zona] = (min(max(h[0], 0), mid), h[1])
        else:
            hasil[zona] = (min(max(h[0], mid), frame_w), h[1])
    return hasil

class Ball:
    """Bola. Kecepatan dalam piksel/detik; tabrakan paddle dicek dengan sapuan."""

    def __init__(self):
        self.reset()

    def reset(self, arah=None):
        """Kembali ke tengah. arah -1 = ke kiri, +1 = ke kanan, None = acak."""
        self.x = config.WIDTH / 2
        self.y = config.HEIGHT / 2
        if arah is None:
            arah = random.choice([-1, 1])
        self.vx = arah * config.BALL_SPEED_X_2P
        self.vy = random.choice([-1, 1]) * config.BALL_SPEED_Y_2P

    @property
    def rect(self):
        r = config.BALL_R
        return pygame.Rect(int(self.x - r), int(self.y - r), 2 * r, 2 * r)

    def update(self, dt, paddles):
        """Gerak satu frame; kembalikan None / "hit" / "kiri" / "kanan" (yang dapat poin)."""
        prev_x, prev_y = self.x, self.y
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Pantulan dinding atas & bawah (paddle ada di kiri/kanan, bukan bawah).
        if self.y - config.BALL_R <= 0 and self.vy < 0:
            self.vy = abs(self.vy)
            self.y = config.BALL_R
        elif self.y + config.BALL_R >= config.HEIGHT and self.vy > 0:
            self.vy = -abs(self.vy)
            self.y = config.HEIGHT - config.BALL_R

        for paddle in paddles:
            if self._sweep_paddle(prev_x, prev_y, paddle):
                return "hit"

        # Bola lolos: sisi yang lolos menentukan siapa yang dapat poin.
        if self.x + config.BALL_R < 0:
            return "kanan"
        if self.x - config.BALL_R > config.WIDTH:
            return "kiri"
        return None

    def _sweep_paddle(self, prev_x, prev_y, paddle):
        """Tabrakan sapuan: cari titik tembus bola pada muka paddle.

        Tanpa sweep, bola cepat bisa melompati paddle tebal 16 piksel dalam
        satu frame (jarak tempuh sampai ~31 piksel/frame saat dt dibatasi).
        """
        r = config.BALL_R
        rect = paddle.rect
        if self.vx > 0 and paddle.side == "kanan":
            muka = rect.left
            tepi_lama, tepi_baru = prev_x + r, self.x + r
        elif self.vx < 0 and paddle.side == "kiri":
            muka = rect.right
            tepi_lama, tepi_baru = prev_x - r, self.x - r
        else:
            return False  # bola menjauh dari paddle ini

        lo, hi = sorted((tepi_lama, tepi_baru))
        if not lo <= muka <= hi:
            return False

        # Posisi y bola tepat saat menembus muka paddle.
        t = (muka - tepi_lama) / (tepi_baru - tepi_lama)
        y_sentuh = prev_y + (self.y - prev_y) * t
        if not rect.top - r <= y_sentuh <= rect.bottom + r:
            return False

        self._pantul(paddle, y_sentuh)
        return True

    def _pantul(self, paddle, y_sentuh):
        """Sudut pantul dari posisi sentuh; kecepatan naik sedikit tiap pantulan."""
        offset = (y_sentuh - paddle.cy) / (config.PADDLE_LEN / 2)
        offset = min(max(offset, -1.0), 1.0)
        speed = min(math.hypot(self.vx, self.vy) * config.BALL_ACCEL_2P,
                    config.BALL_SPEED_MAX_2P)
        sudut = math.radians(config.MAX_BOUNCE_ANGLE * offset)
        arah = -1 if paddle.side == "kanan" else 1  # arah horizontal setelah pantul
        self.vx = arah * math.cos(sudut) * speed
        self.vy = math.sin(sudut) * speed
        # Item 9: jamin |vx| cukup besar supaya bola tidak bolak-balik vertikal saja.
        if abs(self.vx) < config.MIN_VX_2P:
            self.vx = config.MIN_VX_2P if arah > 0 else -config.MIN_VX_2P
        # Dorong bola keluar dari paddle agar tidak menempel dan memantul ulang.
        if paddle.side == "kanan":
            self.x = paddle.rect.left - config.BALL_R
        else:
            self.x = paddle.rect.right + config.BALL_R

class Paddle:
    """Paddle vertikal di sisi kiri atau kanan; cy = titik tengah (sumbu y)."""

    def __init__(self, side):
        self.side = side
        if side == "kiri":
            self.x = config.PADDLE_MARGIN
        else:
            self.x = config.WIDTH - config.PADDLE_MARGIN - config.PADDLE_THICK
        self.cy = config.HEIGHT / 2

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.cy - config.PADDLE_LEN / 2),
                           config.PADDLE_THICK, config.PADDLE_LEN)

    def update(self, dt, target):
        """Item 7: smoothing eksponensial, alpha dari dt clock.tick() tiap paddle."""
        alpha = 1.0 - math.exp(-dt / config.SMOOTH_TAU)
        self.cy += (target - self.cy) * alpha
        half = config.PADDLE_LEN / 2
        self.cy = min(max(self.cy, half), config.HEIGHT - half)

class Game:
    """Satu sesi game dua pemain. Layar, clock, dan kamera datang dari menu."""

    def __init__(self, screen, clock, tracker):
        self.screen = screen
        self.clock = clock
        self.tracker = tracker
        self.font = pygame.font.SysFont(None, 36)
        self.font_besar = pygame.font.SysFont(None, 48)

        # State baru tiap sesi: keluar ke menu lalu masuk lagi = mulai dari awal.
        self.paddles = {"kiri": Paddle("kiri"), "kanan": Paddle("kanan")}
        # Target paddle disimpan: kalau tangan hilang, paddle diam di posisi terakhir.
        self.target = {"kiri": config.HEIGHT / 2, "kanan": config.HEIGHT / 2}
        # Zona mana yang frame lalu punya tangan (untuk histeresis garis tengah).
        self.zona_aktif = {"kiri": False, "kanan": False}
        self.zona = {"kiri": None, "kanan": None}
        self.ball = Ball()
        self.score = {"kiri": 0, "kanan": 0}
        self.winner = None
        self.running = True
        self.keluar_app = False  # True bila jendela ditutup (bukan Esc)

    # ------------------------------------------------------- jendela debug PCD
    def _buka_debug(self):
        """Jendela debug kecil di pojok kiri atas, tidak menutupi game."""
        for name, x in (("Debug - Kamera", 0), ("Debug - Mask kulit", 340)):
            cv2.namedWindow(name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(name, *config.DEBUG_SIZE)
            cv2.moveWindow(name, x, 0)

    def _tutup_debug(self):
        """Tutup jendela debug saja; kamera tetap dipakai menu."""
        for name in ("Debug - Kamera", "Debug - Mask kulit"):
            try:
                cv2.destroyWindow(name)
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
                elif event.key == pygame.K_r and self.winner is not None:
                    self.restart()

    def restart(self):
        self.score = {"kiri": 0, "kanan": 0}
        self.winner = None
        self.ball.reset()

    def update_targets(self, dt, zona, frame_h):
        """Target paddle: keyboard dulu, lalu tangan menimpa bila terdeteksi."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.target["kiri"] -= config.KEY_SPEED * dt
        if keys[pygame.K_s]:
            self.target["kiri"] += config.KEY_SPEED * dt
        if keys[pygame.K_UP]:
            self.target["kanan"] -= config.KEY_SPEED * dt
        if keys[pygame.K_DOWN]:
            self.target["kanan"] += config.KEY_SPEED * dt
        for sisi in ("kiri", "kanan"):
            self.target[sisi] = min(max(self.target[sisi], 0), config.HEIGHT)

        for sisi, h in zona.items():
            if h is not None:
                self.target[sisi] = hand_to_paddle(h[1], frame_h)

        for sisi, paddle in self.paddles.items():
            paddle.update(dt, self.target[sisi])

    # ------------------------------------------------------------------ update
    def update(self, dt):
        frame, mask, hands, faces = self.tracker.read_hands()
        if frame is None:
            print("Kamera tidak terbaca (frame kosong).")
            self.running = False
            return None, None, None, []

        self.zona = assign_zones(hands, frame.shape[1], self.zona_aktif)
        self.update_targets(dt, self.zona, frame.shape[0])

        if self.winner is None:
            hasil = self.ball.update(dt, list(self.paddles.values()))
            if hasil in ("kiri", "kanan"):
                self.score[hasil] += 1
                if self.score[hasil] >= config.WIN_SCORE:
                    self.winner = hasil
                else:
                    # Bola direset ke tengah, arah acak ke pemain yang kehilangan poin.
                    kalah = "kanan" if hasil == "kiri" else "kiri"
                    self.ball.reset(-1 if kalah == "kiri" else 1)
        return frame, mask, self.zona, faces

    # -------------------------------------------------------------------- draw
    def draw(self, frame, mask, zona, faces):
        self.screen.fill((0, 0, 0))
        pygame.draw.line(self.screen, (60, 60, 60), (config.WIDTH / 2, 0),
                         (config.WIDTH / 2, config.HEIGHT), 2)
        pygame.draw.rect(self.screen, config.WARNA_KIRI_RGB, self.paddles["kiri"].rect)
        pygame.draw.rect(self.screen, config.WARNA_KANAN_RGB, self.paddles["kanan"].rect)
        pygame.draw.circle(self.screen, (255, 255, 255),
                           (int(self.ball.x), int(self.ball.y)), config.BALL_R)
        self.screen.blit(self.font.render(f"Kiri: {self.score['kiri']}", True,
                                          config.WARNA_KIRI_RGB), (10, 10))
        skor_kanan = self.font.render(f"Kanan: {self.score['kanan']}", True,
                                      config.WARNA_KANAN_RGB)
        self.screen.blit(skor_kanan, (config.WIDTH - 10 - skor_kanan.get_width(), 10))

        if self.winner is not None:
            warna = (config.WARNA_KIRI_RGB if self.winner == "kiri"
                     else config.WARNA_KANAN_RGB)
            menang = self.font_besar.render(f"PEMAIN {self.winner.upper()} MENANG",
                                            True, warna)
            lagi = self.font.render("tekan R untuk main lagi", True, (255, 255, 255))
            self.screen.blit(menang, menang.get_rect(center=(config.WIDTH / 2,
                                                             config.HEIGHT / 2 - 20)))
            self.screen.blit(lagi, lagi.get_rect(center=(config.WIDTH / 2,
                                                         config.HEIGHT / 2 + 20)))
        pygame.display.flip()

        # --- jendela debug PCD: zona + centroid tiap tangan ---
        self.draw_debug(frame, mask, zona, faces)
        cv2.imshow("Debug - Kamera", frame)
        cv2.waitKey(1)

    def draw_debug(self, frame, mask, zona, faces):
        h_frame, w_frame = frame.shape[:2]
        mid = w_frame // 2
        cv2.line(frame, (mid, 0), (mid, h_frame), (255, 255, 255), 1)

        for (x, y, w, h) in faces:  # kotak wajah yang diabaikan
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
        for (x, y, w, h) in self.tracker.last_rects:  # kandidat tangan
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 1)

        for sisi, h in zona.items():
            warna = bgr(config.WARNA_KIRI_RGB if sisi == "kiri" else config.WARNA_KANAN_RGB)
            if h is not None:
                cv2.circle(frame, h, 6, warna, -1)
                cv2.putText(frame, sisi.upper(), (h[0] + 8, h[1]),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, warna, 1)

        jumlah = sum(1 for h in zona.values() if h is not None)
        cv2.putText(frame, f"TANGAN: {jumlah}/2", (6, h_frame - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (0, 255, 0) if jumlah else (0, 0, 255), 1)

        # Mask abu-abu -> BGR supaya garis tengah berwarna tetap terlihat.
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        cv2.line(mask_bgr, (mid, 0), (mid, h_frame), (120, 120, 120), 1)
        for sisi, h in zona.items():
            warna = bgr(config.WARNA_KIRI_RGB if sisi == "kiri" else config.WARNA_KANAN_RGB)
            if h is not None:
                cv2.circle(mask_bgr, h, 5, warna, -1)
        cv2.imshow("Debug - Mask kulit", mask_bgr)

    # --------------------------------------------------------------------- loop
    def run(self):
        """Loop sesi ini; kembali saat Esc (ke menu) atau jendela ditutup."""
        self._buka_debug()
        try:
            while self.running:
                dt = self.clock.tick(config.FPS) / 1000.0
                dt = min(dt, 0.05)  # batasi kalau frame sempat macet
                self.handle_events()
                frame, mask, zona, faces = self.update(dt)
                if frame is not None:
                    self.draw(frame, mask, zona, faces)
        finally:
            self._tutup_debug()
        return self.keluar_app

def run_game(screen, clock, tracker):
    """Jalankan satu sesi game dua pemain.

    Kembalikan True bila aplikasi harus ditutup (jendela ditutup), False bila
    pemain menekan Esc dan harus kembali ke menu.
    """
    pygame.display.set_caption("Pong 2 Pemain - Hand Tracking")
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
