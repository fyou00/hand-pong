# AGENTS.md

Panduan kerja untuk agent di repo ini: game Pong yang paddle-nya dikontrol
gerakan tangan lewat webcam. Tugas akhir mata kuliah Pengolahan Citra Digital.

## Lingkungan

- macOS, Intel x86_64, **Python 3.11.18** di `.venv` (bukan 3.12).
- Aktifkan venv sebelum apa pun: `source .venv/bin/activate`.
- `opencv-python` **harus < 5**. OpenCV 5 tidak lagi membawa file cascade Haar
  (`cv2.data.haarcascades` kosong), sehingga deteksi wajah gagal. Venv saat ini
  memakai 4.14.0.
- pygame 2.6.1 (SDL 2.28.4), numpy 2.4.6.

## Struktur file

| File | Isi |
|---|---|
| `menu.py` | **Titik masuk aplikasi** (`python menu.py`): judul + dua tombol, pemilik `HandTracker`, loop menu → game → menu |
| `ui.py` | Kelas `Button`: rect, label, `draw(screen, highlighted)`, `is_clicked(pos)`; tanpa logika game |
| `hand_tracker.py` | Tahap PCD: resize 320×240, blur, konversi HSV/YCrCb, threshold, morfologi, buang wajah (Haar), kontur, pusat tangan (`find_hand_center` satu tangan, `find_hand_centers` maks. 2 tangan) |
| `pong.py` | Kelas `Ball`, `Paddle`, `Game` + `run_game(screen, clock, tracker)` (satu pemain) |
| `pong_2p.py` | Versi dua pemain: dua paddle vertikal (kiri/kanan), zona tangan, fisika sweep, skor sampai `WIN_SCORE` |
| `calibrate.py` | Kalibrasi rentang warna kulit dengan trackbar |
| `config.py` | Semua konstanta game dan parameter PCD |
| `requirements.txt` | `opencv-python<5`, `numpy`, `pygame` |
| `README.md` | Dokumentasi untuk pengguna |

## Aturan kerja

- **Jangan mengganti pygame atau OpenCV** dengan library lain.
- **Jangan menghapus fitur yang sudah ada** kecuali diminta eksplisit.
- **Tahap PCD harus tetap terlihat**: jendela `Debug - Kamera` dan
  `Debug - Mask kulit` wajib tetap ada dan tetap menampilkan frame/mask asli
  hasil pemrosesan. Jangan mengganti dengan visualisasi lain.
- **Komentar dan pesan ke pengguna dalam bahasa Indonesia**, singkat, dan
  menjelaskan tahap PCD-nya (mis. `# Tahap 3: morfologi`).
- **Hindari abstraksi berlebihan.** Kode harus mudah dijelaskan di laporan;
  jangan tambah base class, registry, plugin, atau layer yang tidak perlu.
- **Konstanta baru masuk `config.py`**, jangan di-hardcode di dalam fungsi.
- **Kamera IR tidak boleh dipakai** untuk segmentasi warna kulit. Index 0 di
  mesin ini adalah kamera IR (frame hitam, mean S ≈ 0.7); kamera RGB di index 1.
  `CAM_INDEX = 1` adalah default dan **index 0 tidak pernah dibuka**; kalau
  `CAM_INDEX = 0`, nilainya diabaikan dan `HandTracker` mencari kamera berwarna
  mulai dari `CAM_INDEX_CANDIDATES` (1, 2, 3).
- **Anchor tangan = pusat bounding box (`CENTER_MODE = "bbox"`) atau centroid
  kontur (`"moment"`), bukan ujung telunjuk.** Jangan menambah mode
  `"fingertip"`, `cv2.convexityDefects`, atau MediaPipe: game hanya memakai
  koordinat X, dan pusat telapak lebih stabil daripada ujung jari yang
  bergoyang saat jari menekuk.
- **Titik masuk aplikasi adalah `menu.py`.** Game tidak boleh memanggil
  `pygame.init()` atau `pygame.display.set_mode()`; keduanya hanya ada di
  `main()` masing-masing file untuk pengujian langsung. Game menerima
  `screen`, `clock`, dan `tracker` lewat `run_game(...)`.
- **Kamera dibuat sekali di `menu.py`** (`get_tracker()`), dipakai ulang oleh
  kedua game, dan dilepas `close_camera()` saat aplikasi keluar. Jangan membuat
  `HandTracker()` di dalam game — kamera akan terbuka dua kali.
- **`Esc` di dalam game = kembali ke menu**, bukan keluar aplikasi. Jendela
  debug OpenCV ditutup di akhir sesi (`_tutup_debug`), kamera tetap hidup.
- Perubahan harus bisa dijalankan: `python menu.py` tanpa traceback.

## Cara verifikasi

```bash
source .venv/bin/activate
python -m py_compile config.py ui.py menu.py hand_tracker.py pong.py pong_2p.py calibrate.py
python menu.py            # menu 640x480: judul + 2 tombol; Esc keluar
python pong.py            # langsung mode satu pemain (tanpa menu)
python pong_2p.py         # langsung dua paddle: kiri & kanan, skor sampai 7
python calibrate.py       # trackbar; 's' cetak HSV_LOWER/HSV_UPPER, 'q' keluar
```

Alur menu yang harus terbukti: pilih game (Enter/klik) → game jalan dengan
jendela debug → `Esc` → kembali ke menu dengan skor/bola/nyawa ter-reset →
pilih game lagi tanpa pesan kamera kedua (kamera hanya dibuka sekali).

Bukti yang dipakai saat memeriksa perubahan (bukan sekadar "tidak error"):

- Terminal menulis `Kamera dibuka: index N (berwarna)`, bukan `[PERINGATAN] ... tanpa warna`.
- Mask kulit terisi di area tangan, hitam di latar.
- Jendela tidak saling menutupi (game 640×480 di (640,272), debug 320×240 di kiri atas).
- Proses tetap hidup setelah beberapa detik (bukan exit seketika).

## Parameter PCD di `config.py`

| Konstanta | Arti |
|---|---|
| `COLOR_SPACE` | `"hsv"` (default) atau `"ycrcb"` |
| `HSV_LOWER` / `HSV_UPPER` | Rentang kulit HSV, hasil `calibrate.py` |
| `YCRCB_LOWER` / `YCRCB_UPPER` | Rentang kulit YCrCb, kalibrasi ulang bila dipakai |
| `MIN_AREA_RATIO` | Ambang area tangan relatif luas frame (0.02 = 2%) |
| `CENTER_MODE` | `"bbox"` (titik tengah kotak) atau `"moment"` (centroid) |
| `AVG_FRAMES` | Jumlah frame yang dirata-rata untuk menstabilkan pusat |
| `USE_FACE_HAAR`, `FACE_MARGIN` | Buang area wajah dari mask |
| `ROI_TOP` | Alternatif: buang bagian atas frame (0 = nonaktif) |
| `HAND_X_MIN`, `HAND_X_MAX` | Rentang lebar frame (0.2..0.8) yang dipetakan ke layar |
| `HAND_Y_MIN`, `HAND_Y_MAX` | Rentang tinggi frame (0.2..0.8) yang dipetakan ke `0..HEIGHT` (mode dua pemain) |
| `MAX_HANDS`, `ZONE_HYSTERESIS` | Jumlah tangan yang dilacak (2) dan pita mati di garis tengah (5% lebar frame) |
| `PROC_W`, `PROC_H` | Resolusi pemrosesan (320×240) |
| `CAM_INDEX`, `CAM_INDEX_CANDIDATES` | Index kamera (default `1`; `0` = kamera IR, tidak pernah dipakai) dan daftar index untuk mode otomatis (`None`) |

## Jebakan yang sudah ditemui

- Jendela pygame "tidak muncul" ternyata tertutup dua jendela debug OpenCV
  berukuran 1280×720 di posisi yang sama. Jendela debug sekarang dibuat
  320×240 lewat `namedWindow` + `resizeWindow` + `moveWindow`.
- Kamera butuh pemanasan: frame pertama bisa hitam. `HandTracker._probe()`
  membaca beberapa frame sebelum memutuskan kamera berwarna atau tidak.
- `cv2.data.haarcascades` kosong di OpenCV 5 → downgrade ke `<5`.
