"""Komponen UI sederhana: tombol menu. Tanpa logika game."""

import pygame

import config

_font = {}  # cache font per ukuran


def get_font(size):
    """Font bawaan pygame, di-cache supaya tidak dibuat ulang tiap frame."""
    if size not in _font:
        _font[size] = pygame.font.SysFont("menlo,dejavusansmono,monospace", size)
    return _font[size]


class Button:
    """Tombol persegi panjang: rect, label, gambar, dan cek klik."""

    def __init__(self, rect, label):
        self.rect = pygame.Rect(rect)
        self.label = label

    def draw(self, screen, highlighted):
        """Gambar tombol. Versi tersorot: isi lebih terang + border lebih tebal."""
        isi = config.WARNA_TOMBOL_AKTIF_RGB if highlighted else config.WARNA_TOMBOL_RGB
        garis = config.WARNA_BORDER_AKTIF_RGB if highlighted else config.WARNA_BORDER_RGB
        pygame.draw.rect(screen, isi, self.rect, border_radius=0)
        pygame.draw.rect(screen, garis, self.rect,
                         width=4 if highlighted else 2, border_radius=0)
        teks = get_font(config.FONT_TOMBOL).render(self.label, True,
                                                   config.WARNA_TEKS_RGB)
        screen.blit(teks, teks.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        """True bila posisi mouse (klik) ada di dalam tombol."""
        return self.rect.collidepoint(pos)


class Arena:
    """Presentasi arena; koordinat fisika tetap memakai ukuran game."""

    def __init__(self):
        self.surface = pygame.Surface((config.WIDTH, config.HEIGHT))
        self.trail = []

    def begin(self):
        self.surface.fill(config.WARNA_ARENA_RGB)
        x = config.WIDTH // 2
        for y in range(76, config.HEIGHT - 52, 24):
            pygame.draw.rect(self.surface, config.WARNA_NET_RGB, (x - 2, y, 3, 12))
        return self.surface

    def ball(self, ball):
        # Buang jejak saat bola kembali ke tengah setelah poin atau restart.
        if self.trail and ((ball.x - self.trail[-1][0]) ** 2 +
                           (ball.y - self.trail[-1][1]) ** 2) > 100 ** 2:
            self.trail.clear()
        self.trail.append((ball.x, ball.y))
        self.trail = self.trail[-8:]
        for i, (x, y) in enumerate(self.trail[:-1]):
            t = (i + 1) / len(self.trail)
            color = tuple(int(a + (b - a) * t * .6) for a, b in
                          zip(config.WARNA_ARENA_RGB, config.WARNA_KIRI_RGB))
            pygame.draw.rect(self.surface, color, (int(x) - 3, int(y) - 3, 6, 6))
        pygame.draw.rect(self.surface, config.WARNA_TEKS_RGB, ball.rect)

    def present(self, screen, left, right, mode, message=None):
        w, h = screen.get_size()
        rect = pygame.Rect(12, 24, w - 32, h - 60)
        screen.fill(config.WARNA_LATAR_RGB)
        pygame.draw.rect(screen, config.WARNA_KANAN_RGB, rect.move(7, 7))
        screen.blit(pygame.transform.smoothscale(self.surface, rect.size), rect)
        def label(text, size, color, pos, center=False):
            img = get_font(size).render(text, True, color)
            screen.blit(img, img.get_rect(center=pos) if center else pos)
        label(mode, 11, config.WARNA_REDUP_RGB, (rect.x + 16, rect.y + 14))
        label("ESC / MENU", 11, config.WARNA_REDUP_RGB, (rect.right - 100, rect.y + 14))
        for text, color, x in ((left, config.WARNA_KIRI_RGB, .39),
                               (right, config.WARNA_KANAN_RGB, .59)):
            label(text, 36, color, (rect.x + rect.w * x, rect.y + 64), True)
        label("Gerakkan tangan. Kejar bola.", 12, config.WARNA_TEKS_RGB,
              (rect.x + 16, rect.bottom - 26))
        if message:
            box = pygame.Rect(0, 0, rect.w - 32, 92)
            box.center = rect.center
            pygame.draw.rect(screen, config.WARNA_LATAR_RGB, box)
            label(message, 18, config.WARNA_KANAN_RGB, (box.centerx, box.centery - 14), True)
            label("R / MAIN LAGI    ESC / MENU", 12, config.WARNA_TEKS_RGB,
                  (box.centerx, box.centery + 18), True)
