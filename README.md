# Pong Hand Tracking (Tugas PCD)

Game Pong yang paddle-nya digerakkan oleh deteksi tangan dari webcam.
Deteksi memakai pengolahan citra klasik (tanpa machine learning): segmentasi
warna kulit → morfologi → kontur terbesar → pusat kontur.

## Struktur file

| File | Isi |
|---|---|
| `hand_tracker.py` | Tahap PCD: blur, konversi HSV/YCrCb, threshold, morfologi, buang wajah, kontur, pusat tangan |
| `pong.py` | Kelas `Ball`, `Paddle`, `Game` + loop utama pygame |
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
python pong.py
```

Jendela yang muncul:

- **Pong Hand Tracking** — game (640×480)
- **Debug - Kamera** — feed kamera 320×240 + kotak kandidat tangan (biru),
  kotak wajah yang diabaikan (kuning), titik pusat (hijau)
- **Debug - Mask kulit** — hasil segmentasi 320×240

Kontrol: gerakkan tangan (posisi X → paddle), panah kiri/kanan sebagai
cadangan keyboard, `R` untuk main lagi, `Esc` untuk keluar.

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

**Mask kulit hitam** — cek output terminal. `HandTracker` sekarang memilih
kamera yang frame-nya benar-benar berwarna; kamera IR (Windows Hello) atau
kamera yang belum memberi izin akan menghasilkan frame hitam/abu-abu dan
dilewati. Kalau pesan `[PERINGATAN] ... tanpa warna` muncul, set `CAM_INDEX`
di `config.py` ke index kamera RGB (misalnya `CAM_INDEX = 1`).

**Tangan tidak terdeteksi** — lihat jendela *Mask kulit*: area tangan harus
putih. Kalau tidak, jalankan `calibrate.py`. Turunkan juga `MIN_AREA_RATIO`
kalau tangan jauh dari kamera.

**Paddle tidak bergerak walau tangan terlihat** — pastikan teks di jendela
kamera menunjukkan `TANGAN: TERDETEKSI`.
