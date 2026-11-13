# Pong Hand Tracking (Tugas PCD)

Game Pong yang paddle-nya digerakkan oleh deteksi tangan dari webcam.
Deteksi memakai pengolahan citra klasik (tanpa machine learning): segmentasi
warna kulit → morfologi → kontur terbesar → pusat kontur.

## Struktur file

| File | Isi |
|---|---|
| `menu.py` | **Titik masuk aplikasi**: menu utama (tombol Single Player / 2 Player), pemilik kamera, loop menu → game → menu |
| `ui.py` | Kelas `Button` (rect, label, `draw`, `is_clicked`) — tanpa logika game |
| `hand_tracker.py` | Tahap PCD: blur, konversi HSV/YCrCb, threshold, morfologi, buang wajah, kontur, pusat tangan (1 atau 2 tangan) |
| `pong.py` | Kelas `Ball`, `Paddle`, `Game` + `run_game(screen, clock, tracker)` (satu pemain) |
| `pong_2p.py` | Versi dua pemain: dua paddle vertikal, dua tangan, skor sampai 7 |
| `calibrate.py` | Kalibrasi rentang warna kulit dengan trackbar |
| `config.py` | Semua konstanta game dan parameter PCD |
| `requirements.txt` | `opencv-python<5`, `numpy`, `pygame` |

## Instalasi

```bash
cd /Users/kindtomato/ping-pong
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> `opencv-python` **harus versi < 5**. Mulai OpenCV 5 file cascade Haar
> (`haarcascade_frontalface_default.xml`) tidak ikut terpasang lagi, sehingga
> deteksi wajah untuk membuang area wajah gagal.

## Menjalankan

```bash
source .venv/bin/activate
python menu.py
```

Menu utama menampilkan judul dan dua tombol berukuran sama: **Single Player**
dan **2 Player**.

- Pilih dengan panah atas/bawah atau arahkan mouse; sorotan ditandai warna
  berbeda + border lebih tebal.
- `Enter` atau klik kiri untuk masuk ke game.
- `Esc` di menu untuk keluar aplikasi.
- `Esc` di dalam game untuk kembali ke menu (bukan keluar aplikasi). Skor, bola,
  dan nyawa direset, jadi game berikutnya mulai dari awal.
- Kamera dibuka sekali saat game pertama dimulai dan dipakai ulang, sehingga
  tidak ada dua kamera aktif saat berpindah menu → game → menu. Kalau kamera
  gagal dibuka, pesannya tampil di menu dan aplikasi tidak crash.

Game juga bisa dijalankan langsung tanpa menu (untuk pengujian):
`python pong.py` atau `python pong_2p.py`.

Jendela yang muncul saat bermain:

- **Pong Hand Tracking** — game (640×480)
- **Debug - Kamera** — feed kamera 320×240 + kotak kandidat tangan (biru),
  kotak wajah yang diabaikan (kuning), titik pusat (hijau)
- **Debug - Mask kulit** — hasil segmentasi 320×240

Kontrol di game satu pemain: gerakkan tangan (posisi X → paddle), panah
kiri/kanan sebagai cadangan keyboard, `R` untuk main lagi, `Esc` ke menu.

## Mode dua pemain

Pilih tombol **2 Player** di menu, atau jalankan langsung `python pong_2p.py`.

- Paddle **kiri** dikontrol tangan di separuh kiri frame, paddle **kanan** di
  separuh kanan. Paddle bergerak vertikal: posisi Y tangan (20%..80% tinggi
  frame) dipetakan ke tinggi layar.
- Tangan yang menyilang garis tengah tidak langsung berpindah pemain: ada pita
  mati `ZONE_HYSTERESIS` (5% lebar frame). Kalau sebuah zona tidak punya tangan,
  paddle di zona itu diam di posisi terakhir.
- Skor: bola lolos di kiri → pemain kanan dapat poin, dan sebaliknya. Pemain
  pertama yang mencapai 7 poin menang; tekan `R` untuk main lagi.
- Cadangan keyboard: `W`/`S` untuk paddle kiri, panah atas/bawah untuk paddle
  kanan, `Esc` kembali ke menu.
- Jendela debug sama seperti mode satu pemain, dengan garis tengah pemisah zona
  dan titik centroid berwarna berbeda untuk tiap pemain (hijau = kiri,
  oranye = kanan).

## Kalibrasi warna kulit

```bash
python calibrate.py
```

Geser trackbar sampai tangan putih penuh dan latar hitam, lalu tekan `s`
untuk mencetak nilai `HSV_LOWER` / `HSV_UPPER` yang bisa ditempel ke `config.py`.
Kalau HSV sulit stabil terhadap pencahayaan, ganti `COLOR_SPACE = "ycrcb"`
di `config.py` (YCrCb lebih tahan terhadap perubahan terang, tapi rentangnya
lebih sempit dan perlu kalibrasi ulang).

## Troubleshooting

**Jendela pygame tidak kelihatan** — biasanya tertutup dua jendela debug OpenCV.
Jendela debug sekarang dibuat 320×240 di pojok kiri atas lewat
`cv2.namedWindow` + `resizeWindow` + `moveWindow`, jadi tidak menutupi game.
Kalau masih ketutupan, geser jendela debug atau nonaktifkan sementara dua
baris `cv2.imshow` di `pong.py`.

**Mask kulit hitam** — cek output terminal. `HandTracker` sekarang membuka
kamera RGB langsung di `CAM_INDEX = 1`; **index 0 tidak pernah dipakai** karena
di mesin ini index 0 adalah kamera IR (Windows Hello) yang frame-nya
hitam/abu-abu. Kalau pesan `[PERINGATAN] ... tanpa warna` muncul, ganti
`CAM_INDEX` di `config.py` ke index kamera RGB lain (misalnya `2`).

**Tangan tidak terdeteksi** — lihat jendela *Mask kulit*: area tangan harus
putih. Kalau tidak, jalankan `calibrate.py`. Turunkan juga `MIN_AREA_RATIO`
kalau tangan jauh dari kamera.

**Paddle tidak bergerak walau tangan terlihat** — pastikan teks di jendela
kamera menunjukkan `TANGAN: TERDETEKSI` (mode satu pemain) atau `TANGAN: 1/2`
/ `TANGAN: 2/2` (mode dua pemain).
