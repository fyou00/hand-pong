# Pong Hand Tracking (Tugas PCD)

Game Pong yang paddle-nya digerakkan oleh deteksi tangan dari webcam.
Deteksi memakai pengolahan citra klasik (tanpa machine learning): segmentasi
warna kulit → morfologi → kontur terbesar → pusat kontur.

## Struktur file

| File | Isi |
|---|---|
| `hand_tracker.py` | Tahap PCD: blur, konversi HSV/YCrCb, threshold, morfologi, buang wajah, kontur, pusat tangan (1 atau 2 tangan) |
| `pong.py` | Kelas `Ball`, `Paddle`, `Game` + loop utama pygame (satu pemain) |
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
python pong.py
```

Jendela yang muncul:

- **Pong Hand Tracking** — game (640×480)
- **Debug - Kamera** — feed kamera 320×240 + kotak kandidat tangan (biru),
  kotak wajah yang diabaikan (kuning), titik pusat (hijau)
- **Debug - Mask kulit** — hasil segmentasi 320×240

Kontrol: gerakkan tangan (posisi X → paddle), panah kiri/kanan sebagai
cadangan keyboard, `R` untuk main lagi, `Esc` untuk keluar.

## Mode dua pemain

```bash
python pong_2p.py
```

- Paddle **kiri** dikontrol tangan di separuh kiri frame, paddle **kanan** di
  separuh kanan. Paddle bergerak vertikal: posisi Y tangan (20%..80% tinggi
  frame) dipetakan ke tinggi layar.
- Tangan yang menyilang garis tengah tidak langsung berpindah pemain: ada pita
  mati `ZONE_HYSTERESIS` (5% lebar frame). Kalau sebuah zona tidak punya tangan,
  paddle di zona itu diam di posisi terakhir.
- Skor: bola lolos di kiri → pemain kanan dapat poin, dan sebaliknya. Pemain
  pertama yang mencapai 7 poin menang; tekan `R` untuk main lagi.
- Cadangan keyboard (bisa dipakai tanpa kamera): `W`/`S` untuk paddle kiri,
  panah atas/bawah untuk paddle kanan, `Esc` keluar.
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

**Mask kulit hitam** — cek output terminal. `HandTracker` sekarang memilih
kamera yang frame-nya benar-benar berwarna; kamera IR (Windows Hello) atau
kamera yang belum memberi izin akan menghasilkan frame hitam/abu-abu dan
dilewati. Kalau pesan `[PERINGATAN] ... tanpa warna` muncul, set `CAM_INDEX`
di `config.py` ke index kamera RGB (misalnya `CAM_INDEX = 1`).

**Tangan tidak terdeteksi** — lihat jendela *Mask kulit*: area tangan harus
putih. Kalau tidak, jalankan `calibrate.py`. Turunkan juga `MIN_AREA_RATIO`
kalau tangan jauh dari kamera.

**Paddle tidak bergerak walau tangan terlihat** — pastikan teks di jendela
kamera menunjukkan `TANGAN: TERDETEKSI` (mode satu pemain) atau `TANGAN: 1/2`
/ `TANGAN: 2/2` (mode dua pemain).
