"""Konstanta game + parameter PCD. Dipisah agar mudah dijelaskan di laporan."""

# ---------------------------------------------------------------- layar & game
WIDTH, HEIGHT = 640, 480
FPS = 60
LIVES = 3

PADDLE_W, PADDLE_H = 120, 16
PADDLE_Y = HEIGHT - 40
BALL_R = 8

# Kecepatan dalam piksel/detik (bukan piksel/frame) supaya tidak tergantung FPS.
BALL_SPEED_X = 180
BALL_SPEED_Y = 240
BALL_SPEED_MAX = 540
BALL_ACCEL = 1.03
MIN_VX = 90          # |vx| minimal (~1.5 px/frame @60fps)

KEY_SPEED = 320      # piksel/detik untuk kontrol keyboard
SMOOTH_TAU = 0.08    # konstanta waktu smoothing paddle (detik)
HAND_LOST_DELAY = 1.0  # detik tanpa tangan sebelum keyboard mengambil alih

# ------------------------------------------------------------------- tahap PCD
PROC_W, PROC_H = 320, 240     # deteksi diproses di resolusi kecil
DEBUG_SIZE = (320, 240)       # ukuran jendela debug OpenCV
DEBUG_WINDOW = "Debug - Kamera"   # menampilkan pra-pemrosesan + landmark + anchor

COLOR_SPACE = "hsv"           # "hsv" atau "ycrcb" (hanya untuk calibrate.py)
HSV_LOWER = (0, 40, 60)
HSV_UPPER = (25, 255, 255)
YCRCB_LOWER = (0, 133, 77)
YCRCB_UPPER = (255, 173, 127)

# ------------------------------------------------------- tahap PCD + MediaPipe
CLAHE_CLIP = 2.0              # tahap 1: batas peningkatan kontras CLAHE
CLAHE_TILE = (8, 8)
BLUR_KSIZE = 5                # tahap 1: ukuran kernel Gaussian blur

MP_MAX_HANDS = 2              # tahap 3: jumlah tangan maksimum
MP_MODEL_COMPLEXITY = 1       # 0 = cepat, 1 = akurat
MP_DETECTION_CONF = 0.6
MP_TRACKING_CONF = 0.5

# tahap 4: anchor = pusat telapak (9 = middle finger MCP, 8 = ujung telunjuk)
ANCHOR_LANDMARK = 9

# 20%..80% lebar frame dipetakan ke 0..WIDTH
HAND_X_MIN, HAND_X_MAX = 0.2, 0.8

# ------------------------------------------------- mode dua pemain (pong_2p.py)
PADDLE_THICK = 16             # tebal paddle vertikal (sumbu x)
PADDLE_LEN = 120              # panjang paddle vertikal (sumbu y)
PADDLE_MARGIN = 28            # jarak paddle dari dinding kiri/kanan
WIN_SCORE = 7                 # poin untuk menang

BALL_SPEED_X_2P = 260         # kecepatan awal horizontal (piksel/detik)
BALL_SPEED_Y_2P = 140         # kecepatan awal vertikal (piksel/detik)
BALL_ACCEL_2P = 1.05          # kecepatan naik sedikit tiap pantulan paddle
BALL_SPEED_MAX_2P = 620       # batas kecepatan setelah percepatan
MIN_VX_2P = 180               # |vx| >= 3 piksel/frame @60fps (sumbu utama)
MAX_BOUNCE_ANGLE = 60         # derajat, sudut pantul maksimum dari offset paddle

# 20%..80% tinggi frame dipetakan ke 0..HEIGHT (paddle bergerak di sumbu y)
HAND_Y_MIN, HAND_Y_MAX = 0.2, 0.8
ZONE_HYSTERESIS = 0.05        # pita mati di garis tengah (5% lebar frame)

# Warna pemain (RGB untuk pygame; OpenCV memakai urutan terbalik)
WARNA_KIRI_RGB = (90, 255, 140)
WARNA_KANAN_RGB = (255, 170, 80)

# ------------------------------------------------------------------- menu & UI
JUDUL_APLIKASI = "Hand Pong"
JUDUL_MENU = "HAND PONG"
FONT_JUDUL = 72
FONT_TOMBOL = 32
FONT_PESAN = 18

BUTTON_W, BUTTON_H = 260, 64  # kedua tombol menu selalu sama ukuran
BUTTON_GAP = 24

WARNA_LATAR_RGB = (0, 0, 0)
WARNA_JUDUL_RGB = (255, 255, 255)
WARNA_TEKS_RGB = (235, 235, 240)
WARNA_TOMBOL_RGB = (32, 32, 38)
WARNA_TOMBOL_AKTIF_RGB = (64, 70, 96)
WARNA_BORDER_RGB = (110, 110, 120)
WARNA_BORDER_AKTIF_RGB = (90, 255, 140)
WARNA_PESAN_RGB = (255, 120, 120)

# index kamera. Index 0 di mesin ini adalah kamera IR dan TIDAK PERNAH
# dipakai. Default 1 = kamera RGB. None = cari otomatis mulai dari index 1.
CAM_INDEX = 1
CAM_INDEX_CANDIDATES = (1, 2, 3)   # index yang dicoba saat CAM_INDEX = None
