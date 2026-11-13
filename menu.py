"""Titik masuk aplikasi: menu utama -> game -> kembali ke menu.

Kamera (HandTracker) dibuka sekali di sini lalu dipakai ulang oleh kedua game,
jadi tidak ada dua VideoCapture aktif saat berpindah dari menu ke game.

Jalankan: python menu.py
Kontrol menu: panah atas/bawah atau mouse untuk memilih, Enter/klik untuk
             konfirmasi, Esc untuk keluar aplikasi.
"""

import cv2
import pygame

import config
import pong
import pong_2p
from hand_tracker import HandTracker
from ui import Button, get_font

# Pilihan menu: (kode mode, label tombol, fungsi game)
PILIHAN = (
    ("single", "Single Player", pong.run_game),
    ("two", "2 Player", pong_2p.run_game),
)

# Kamera disimpan di level modul supaya dibuka sekali untuk seluruh aplikasi.
_kamera = {"tracker": None, "pesan": None}


def get_tracker():
    """Buka kamera sekali saja. Kalau gagal, pesannya disimpan untuk menu."""
    if _kamera["tracker"] is None and _kamera["pesan"] is None:
        try:
            _kamera["tracker"] = HandTracker()
        except RuntimeError as exc:  # kamera tidak ada / tidak diizinkan
            _kamera["pesan"] = str(exc)
    return _kamera["tracker"]


def close_camera():
    """Lepas kamera sekali di akhir aplikasi."""
    if _kamera["tracker"] is not None:
        _kamera["tracker"].release()
        _kamera["tracker"] = None


def make_buttons():
    """Dua tombol dengan ukuran sama, tersusun vertikal di tengah layar."""
    x = (config.WIDTH - config.BUTTON_W) // 2
    total = len(PILIHAN) * config.BUTTON_H + (len(PILIHAN) - 1) * config.BUTTON_GAP
    y0 = (config.HEIGHT - total) // 2
    return [Button((x, y0 + i * (config.BUTTON_H + config.BUTTON_GAP),
                    config.BUTTON_W, config.BUTTON_H), label)
            for i, (_, label, _) in enumerate(PILIHAN)]


def _mulai(index):
    """Kode mode untuk tombol ke-index, atau None kalau kamera gagal dibuka."""
    if get_tracker() is None:
        return None
    return PILIHAN[index][0]


def _baris_pesan(font, teks, lebar_maks):
    """Pecah pesan panjang jadi baris-baris yang muat di layar."""
    hasil = []
    for baris in teks.splitlines():
        sekarang = ""
        for kata in baris.split():
            coba = f"{sekarang} {kata}".strip()
            if font.size(coba)[0] <= lebar_maks:
                sekarang = coba
            else:
                if sekarang:
                    hasil.append(sekarang)
                sekarang = kata
        hasil.append(sekarang)
    return hasil


def _gambar(screen, buttons, index):
    screen.fill(config.WARNA_LATAR_RGB)
    judul = get_font(config.FONT_JUDUL).render(config.JUDUL_MENU, True,
                                               config.WARNA_JUDUL_RGB)
    screen.blit(judul, judul.get_rect(center=(config.WIDTH / 2, config.HEIGHT * 0.25)))

    for i, tombol in enumerate(buttons):
        tombol.draw(screen, i == index)

    if _kamera["pesan"]:
        font = get_font(config.FONT_PESAN)
        baris = _baris_pesan(font, _kamera["pesan"], config.WIDTH - 40)
        y = config.HEIGHT - 14 - len(baris) * 16
        for teks in baris:
            gambar = font.render(teks, True, config.WARNA_PESAN_RGB)
            screen.blit(gambar, (20, y))
            y += 16
    pygame.display.flip()


def run_menu(screen, clock):
    """Tampilkan menu. Kembalikan "single" / "two", atau None kalau keluar.

    Navigasi: panah atas/bawah memindah sorotan (memutar), Enter/klik kiri
    menjalankan pilihan, Esc keluar aplikasi. Sorotan juga mengikuti kursor
    mouse, tetapi hanya saat mouse benar-benar bergerak — kalau tidak, kursor
    yang diam di atas sebuah tombol akan terus menimpa pilihan keyboard.
    """
    pygame.display.set_caption(config.JUDUL_APLIKASI)
    buttons = make_buttons()
    index = 0
    pos_lama = pygame.mouse.get_pos()

    while True:
        clock.tick(config.FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_UP:
                    index = (index - 1) % len(buttons)
                elif event.key == pygame.K_DOWN:
                    index = (index + 1) % len(buttons)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    mode = _mulai(index)
                    if mode is not None:
                        return mode
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, tombol in enumerate(buttons):
                    if tombol.is_clicked(event.pos):
                        index = i
                        mode = _mulai(i)
                        if mode is not None:
                            return mode

        # Sorot tombol di bawah kursor, hanya bila mouse bergerak.
        pos = pygame.mouse.get_pos()
        if pos != pos_lama:
            pos_lama = pos
            for i, tombol in enumerate(buttons):
                if tombol.is_clicked(pos):
                    index = i

        _gambar(screen, buttons, index)


def main():
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    clock = pygame.time.Clock()
    try:
        while True:
            mode = run_menu(screen, clock)
            if mode is None:
                break
            fungsi = next(f for kode, _, f in PILIHAN if kode == mode)
            # Game membuat state baru tiap panggilan: skor/bola/nyawa mulai awal.
            if fungsi(screen, clock, get_tracker()):
                break  # jendela ditutup saat bermain -> keluar aplikasi
    finally:
        close_camera()
        cv2.destroyAllWindows()
        pygame.quit()


if __name__ == "__main__":
    main()
