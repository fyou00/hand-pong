# AGENTS.md

## Ringkasan proyek

Game Pong yang dikontrol dengan deteksi tangan lewat webcam. Proyek ini adalah
tugas akhir mata kuliah Pengolahan Citra Digital (PCD) mahasiswa Teknologi
Informatika. Pendekatan: hybrid, yaitu MediaPipe Hands untuk landmark tangan
(komponen pihak ketiga, pretrained), dan tahap PCD ditulis sendiri.

## Lingkungan

- macOS Intel, **Python 3.11.18** di `.venv` (bukan 3.12)
- Gunakan webcam RGB. Jangan pakai kamera IR laptop Lenovo ThinkPad T480s.
- Dependensi (`requirements.txt`): `opencv-contrib-python<5`, `numpy`, `pygame`,
  `mediapipe==0.10.14`
- **Hanya boleh ada satu paket OpenCV terpasang**, yaitu
  `opencv-contrib-python<5`. `mediapipe` menarik `opencv-contrib-python` tanpa
  pin, jadi tanpa pin di `requirements.txt` ia memasang OpenCV 5 dan menimpa
  `opencv-python` 4.x (gejalanya: `cv2.__version__` jadi 5.0.0). Jangan
  menambahkan `opencv-python` lagi — dua paket itu berbagi folder `cv2`.
- Gunakan API `mp.solutions.hands` (bukan Tasks API) sesuai versi yang dipin.

## Struktur file

- `menu.py`: entry point. Menu Single Player / 2 Player, loop utama menu -> game -> menu.
- `ui.py`: kelas `Button` (draw, is_clicked). Tanpa logika game.
- `hand_tracker.py`: kelas `HandTracker`. Tahap PCD (resize, CLAHE pada LAB, blur)
  dan pemanggilan MediaPipe Hands. `read()` mengembalikan `(frame, debug, hands)`,
  dengan `hands` berupa dict `{"Left": (x, y), "Right": (x, y)}` dalam koordinat frame.
- `pong.py`: game satu pemain. Fungsi `run_game(screen, clock, tracker)`.
- `pong_2p.py`: game dua pemain. Fungsi `run_game(screen, clock, tracker)`.

## Batasan

- Boleh memakai MediaPipe Hands HANYA untuk mendapatkan landmark dan label Left/Right.
- Tahap PCD harus tetap terlihat dan bisa dijelaskan: pra-pemrosesan, ROI/zona,
  normalisasi, pemilihan anchor, dan smoothing.
- Jangan mengganti pygame atau OpenCV.
- Jangan memanggil `pygame.init()` atau `set_mode()` di dalam fungsi game.
- Kamera hanya dibuka sekali (di `menu.py`) dan di-release saat aplikasi keluar.

## Konvensi kode

- Komentar dalam bahasa Indonesia, singkat, dan menjelaskan tahap PCD.
- Jangan menghapus fitur yang sudah ada kecuali diminta.
- Ubah satu hal per langkah, dan pastikan `python menu.py` tetap bisa dijalankan.
- Jika ada keputusan yang bisa berbeda, beri pilihan singkat beserta trade-off-nya
  sebelum memilih.

## Masalah yang sedang dikerjakan (urutkan sesuai prioritas)

1. Sinkronkan `pong.py` dengan `hand_tracker.read()` yang baru: ambil posisi dari
   `hands.get("Left")` atau `hands.get("Right")`, dan tampilkan `debug` di jendela kamera.
2. Tangan hilang: paddle tetap di posisi terakhir, jangan langsung pindah ke keyboard.
3. Pada `pong_2p.py`, gunakan label Left untuk paddle kiri dan Right untuk paddle kanan.
   Jangan lagi membagi zona dengan centroid.
4. Smoothing paddle memakai `dt` dari `clock.tick()` agar respons konsisten terhadap FPS.
5. Bola: batas minimal |vx| >= 3 agar tidak bergerak vertikal terus.
6. Bola tidak boleh menembus paddle: periksa tabrakan dengan sapuan (sweep).
7. Pemetaan posisi tangan (20% sampai 80% tinggi frame) ke posisi paddle, dengan batas tepi.
8. Menu: navigasi mouse dan keyboard (panah atas/bawah, Enter, Esc untuk keluar).
9. Esc di dalam game kembali ke menu, dan state game (skor, nyawa, bola) direset.
10. Kamera gagal dibuka: tampilkan pesan di menu, jangan crash.

## Output yang diharapkan dari agent

- Daftar file yang dibuat atau diubah.
- Ringkasan perubahan per item.
- Langkah uji manual: cek mask/landmark, cek paddle kiri dan kanan, cek menu,
  cek Esc kembali ke menu, cek kamera tidak error saat berpindah mode.