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
MIN_VX = 90          # item 9: |vx| minimal (~1.5 px/frame @60fps)

KEY_SPEED = 320      # piksel/detik untuk kontrol keyboard
SMOOTH_TAU = 0.08    # item 7: konstanta waktu smoothing paddle (detik)

# ------------------------------------------------------------------- tahap PCD
PROC_W, PROC_H = 320, 240     # item 8: deteksi diproses di resolusi kecil
DEBUG_SIZE = (320, 240)       # ukuran jendela debug OpenCV

COLOR_SPACE = "hsv"           # "hsv" atau "ycrcb"
HSV_LOWER = (0, 40, 60)
HSV_UPPER = (25, 255, 255)
YCRCB_LOWER = (0, 133, 77)
YCRCB_UPPER = (255, 173, 127)

MIN_AREA_RATIO = 0.02         # item 3: tangan minimal 2% dari luas frame
CENTER_MODE = "bbox"          # item 4: "bbox" (titik tengah kotak) atau "moment"
AVG_FRAMES = 5                # item 4: jumlah frame yang dirata-rata

USE_FACE_HAAR = True          # item 2: buang area wajah dari mask
FACE_MARGIN = 0.15            # perluas kotak wajah 15% tiap sisi
ROI_TOP = 0.0                 # item 2 (alternatif): 0 = nonaktif, 0.35 = buang 35% atas

# item 6: 20%..80% lebar frame dipetakan ke 0..WIDTH
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
MAX_HANDS = 2                 # jumlah tangan yang dilacak

# Warna pemain (RGB untuk pygame; OpenCV memakai urutan terbalik)
WARNA_KIRI_RGB = (90, 255, 140)
WARNA_KANAN_RGB = (255, 170, 80)

# item 5: index kamera. None = otomatis pilih kamera berwarna (kamera IR dilewati).
CAM_INDEX = None
