"""Komponen UI sederhana: tombol menu. Tanpa logika game."""

import pygame

import config

_font = {}  # cache font per ukuran


def get_font(size):
    """Font bawaan pygame, di-cache supaya tidak dibuat ulang tiap frame."""
    if size not in _font:
        _font[size] = pygame.font.SysFont(None, size)
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
        pygame.draw.rect(screen, isi, self.rect, border_radius=8)
        pygame.draw.rect(screen, garis, self.rect,
                         width=4 if highlighted else 2, border_radius=8)
        teks = get_font(config.FONT_TOMBOL).render(self.label, True,
                                                   config.WARNA_TEKS_RGB)
        screen.blit(teks, teks.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        """True bila posisi mouse (klik) ada di dalam tombol."""
        return self.rect.collidepoint(pos)
