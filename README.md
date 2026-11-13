# Hand Pong (Tugas PCD)

Game Pong yang paddle-nya digerakkan oleh tangan di depan webcam. Pendekatan
**hybrid**: MediaPipe Hands dipakai hanya untuk mendapatkan landmark dan label
tangan (Left/Right), sedangkan tahap pengolahan citra digital dikerjakan sendiri
(pra-pemrosesan CLAHE, pemilihan anchor, pemetaan, dan smoothing).

## Struktur file

| File | Isi |
|---|---|
| `menu.py` | **Titik masuk aplikasi**: menu utama (tombol Single Player / 2 Player), pemilik kamera, loop menu → game → menu |
| `ui.py` | Kelas `Button` (rect, label, `draw`, `is_clicked`) — tanpa logika game |
| `hand_tracker.py` | Tahap PCD: resize 320×240 → cermin → CLAHE pada LAB → blur → MediaPipe Hands → anchor pusat telapak. `read()` mengembalikan `(frame, debug, hands)` dengan `hands = {"Left": (x, y), "Right": (x, y)}` |
| `pong.py` | Game satu pemain: `Ball`, `Paddle`, `Game`, `run_game(screen, clock, tracker)` |
| `pong_2p.py` | Game dua pemain: dua paddle vertikal, label Left/Right, skor sampai 7 |
| `calibrate.py` | Opsional/legacy: eksplorasi rentang warna kulit dengan trackbar. Tidak dipakai game |
| `config.py` | Semua konstanta game dan parameter PCD |
| `requirements.txt` | `opencv-python<5`, `numpy`, `pygame`, `mediapipe==0.10.14` |

## Instalasi

```bash
cd /Users/kindtomato/ping-pong
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> `mediapipe` dipin ke **0.10.14** dan dipakai lewat API `mp.solutions.hands`
> (bukan Tasks API). Versi lain punya nama API yang berbeda.

## Menjalankan

```bash
source .venv/bin/activate
python menu.py
```

Menu utama menampilkan judul dan dua tombol berukuran sama: **Single Player**
dan **2 Player**.

- Pilih dengan panah atas/bawah (memutar) atau gerakkan mouse ke tombol;
  sorotan ditandai warna lebih terang + border hijau lebih tebal.
- `Enter` atau klik kiri untuk masuk ke game.
- `Esc` di menu untuk keluar aplikasi.
- `Esc` di dalam game untuk kembali ke menu (bukan keluar aplikasi). Skor, bola,
  dan nyawa direset, jadi game berikutnya mulai dari awal.
- Kamera dibuka sekali saat game pertama dimulai dan dipakai ulang, sehingga
  tidak ada dua kamera aktif saat berpindah menu → game → menu.

Game juga bisa dijalankan langsung tanpa menu (untuk pengujian):
`python pong.py` atau `python pong_2p.py`.

Jendela yang muncul saat bermain:

- **Pong Hand Tracking** — game (640×480)
- **Debug - Kamera** — 320×240, hasil pra-pemrosesan (CLAHE + blur) dengan
  skeleton landmark, label `Left`/`Right`, titik hijau di pusat telapak, dan
  teks jumlah tangan yang terdeteksi

Kontrol di game satu pemain: gerakkan tangan (posisi X → paddle), panah
kiri/kanan sebagai cadangan keyboard, `R` untuk main lagi, `Esc` ke menu.

## Mode dua pemain

Pilih tombol **2 Player** di menu, atau jalankan langsung `python pong_2p.py`.

- Label **Left** menggerakkan paddle kiri, label **Right** menggerakkan paddle
  kanan. Tidak ada pembagian zona berdasarkan posisi x, jadi tangan yang
  menyilang ke sisi lain layar tetap menggerakkan paddle pemiliknya.
- Paddle bergerak vertikal: posisi Y tangan pada 20%..80% tinggi frame
  dipetakan ke seluruh tinggi layar. Di luar rentang itu paddle menempel tepi.
- Skor: bola lolos di kiri → pemain kanan dapat poin, dan sebaliknya. Pemain
  pertama yang mencapai 7 poin menang; tekan `R` untuk main lagi.
- Cadangan keyboard: `W`/`S` untuk paddle kiri, panah atas/bawah untuk paddle
  kanan, `Esc` kembali ke menu.
- Jendela debug sama seperti mode satu pemain, dengan titik anchor berwarna
  berbeda untuk tiap pemain (hijau = kiri, oranye = kanan).

## Tangan hilang dan kontrol keyboard

Paddle tidak pernah melompat ke keyboard. Aturannya sama di kedua mode:

1. Selama tangan terlihat, paddle hanya mengikuti tangan.
2. Tangan hilang → paddle diam di posisi terakhir.
3. Tangan hilang lebih dari `HAND_LOST_DELAY` (1 detik) → keyboard aktif dan
   bisa menggeser paddle. Begitu tangan terlihat lagi, keyboard langsung
   diabaikan dan paddle kembali mengikuti tangan.

## Kalibrasi warna kulit (opsional)

```bash
python calibrate.py
```

Game tidak lagi memakai segmentasi warna kulit (deteksi tangan memakai
MediaPipe), jadi langkah ini **tidak diperlukan** untuk bermain. Skrip ini
tetap disimpan untuk eksplorasi/laporan: geser trackbar sampai mask putih
mengikuti tangan, tekan `s` untuk mencetak `HSV_LOWER` / `HSV_UPPER`, `q` untuk
keluar. Nilai yang dicetak tidak memengaruhi jalannya game.

## Troubleshooting

**Kamera IR terpakai / frame hitam** — `CAM_INDEX = 1` adalah default dan
**index 0 tidak pernah dibuka** karena di mesin ini index 0 adalah kamera IR.
Kalau kamera RGB ada di index lain, ubah `CAM_INDEX` di `config.py`. Terminal
mencetak `Kamera dibuka: index N (dipilih manual)` saat berhasil.

**Kamera gagal dibuka** — menu menampilkan pesan penyebab (izin macOS, kamera
dipakai aplikasi lain, atau index salah) dan aplikasi tetap berjalan. Kalau
kamera terputus saat bermain, game kembali ke menu dengan pesan; sambungkan
kamera lalu pilih mode lagi.

**Tangan tidak terdeteksi** — lihat jendela *Debug - Kamera*: skeleton harus
muncul mengikuti tangan. Bila tidak: pastikan tangan masuk frame (bukan hanya
ujung jari), cahaya cukup, dan tangan tidak terlalu dekat lensa. `CLAHE_CLIP`
dan `MP_DETECTION_CONF` di `config.py` bisa disesuaikan. MediaPipe juga
mencetak log `INFO`/`WARNING` sendiri di terminal — itu normal.

**Paddle bergerak di sisi yang salah pada mode dua pemain** — label Left/Right
dari MediaPipe mengikuti gambar yang sudah dicerminkan. Bila hasilnya terbalik
di perangkat Anda, tukar pemetaan di `label_ke_sisi()` (`pong_2p.py`).

**Jendela pygame tidak kelihatan** — jendela debug OpenCV dibuat 320×240 di
pojok kiri atas lewat `cv2.namedWindow` + `resizeWindow` + `moveWindow`, jadi
tidak menutupi game. Kalau masih ketutupan, geser jendela debug.

**Paddle tidak bergerak walau tangan terlihat** — cek teks `TANGAN: n` di
jendela *Debug - Kamera*. Bila `0`, deteksi gagal (lihat poin di atas).
