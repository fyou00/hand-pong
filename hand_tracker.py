"""Tahap PCD + MediaPipe Hands: pra-pemrosesan citra dan posisi tangan.

Alur: resize 320x240 -> cermin -> CLAHE pada kanal L (LAB) -> blur
      -> MediaPipe Hands (landmark + label Left/Right) -> anchor pusat telapak.
"""

import time

import cv2
import mediapipe as mp
import numpy as np

import config

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


def skin_mask(bgr, lower, upper, kernel_size=5):
    """Segmentasi warna kulit. Dipakai calibrate.py untuk eksplorasi rentang HSV."""
    blur = cv2.GaussianBlur(bgr, (5, 5), 0)
    if config.COLOR_SPACE == "ycrcb":
        conv = cv2.cvtColor(blur, cv2.COLOR_BGR2YCrCb)
    else:
        conv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

    lo = np.array(lower, dtype=np.uint8)
    hi = np.array(upper, dtype=np.uint8)
    mask = cv2.inRange(conv, lo, hi)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    return mask


class HandTracker:
    def __init__(self, cam_index=config.CAM_INDEX):
        self.cap = self._open_camera(cam_index)

        # Tahap 1: CLAHE untuk meratakan kontras cahaya sebelum dideteksi.
        self.clahe = cv2.createCLAHE(clipLimit=config.CLAHE_CLIP,
                                     tileGridSize=config.CLAHE_TILE)

        # Tahap 3: MediaPipe Hands, hanya untuk landmark + label Left/Right.
        # True bila frame terakhir gagal dibaca (kamera dicabut / dipakai proses lain).
        self.terputus = False

        self.hands = mp_hands.Hands(static_image_mode=False,
                                    max_num_hands=config.MP_MAX_HANDS,
                                    model_complexity=config.MP_MODEL_COMPLEXITY,
                                    min_detection_confidence=config.MP_DETECTION_CONF,
                                    min_tracking_confidence=config.MP_TRACKING_CONF)

    # ------------------------------------------------------------------ kamera
    def _open_camera(self, cam_index):
        """Kamera dibuka pada index RGB; index 0 (kamera IR) tidak pernah dipakai.

        Kamera IR (Windows Hello) menghasilkan frame hitam/abu-abu, sehingga
        deteksi tangan pasti gagal. Karena itu index 0 tidak pernah dibuka:
        kalau CAM_INDEX = 0, nilainya diabaikan dan pencarian otomatis dimulai
        dari CAM_INDEX_CANDIDATES (index 1 ke atas).
        """
        if cam_index == 0:
            print("[PERINGATAN] CAM_INDEX = 0 adalah kamera IR dan tidak dipakai; "
                  f"mencari kamera berwarna di index {config.CAM_INDEX_CANDIDATES}.")
            cam_index = None

        if cam_index is not None:
            cap = cv2.VideoCapture(cam_index)
            if not cap.isOpened():
                cap.release()
                raise RuntimeError(self._camera_error([cam_index]))
            print(f"Kamera dibuka: index {cam_index} (dipilih manual)")
            sat, bright = self._probe(cap)
            if sat is None:
                cap.release()
                raise RuntimeError(self._camera_error([cam_index]))
            if sat < 10 or bright < 10:
                print("[PERINGATAN] Frame kamera ini hampir tanpa warna (kamera IR?). "
                      "Coba index lain di CAM_INDEX (config.py).")
            return cap

        candidates = list(config.CAM_INDEX_CANDIDATES)
        fallback = None
        for idx in candidates:
            cap = cv2.VideoCapture(idx)
            if not cap.isOpened():
                cap.release()
                continue
            sat, bright = self._probe(cap)
            if sat is None:  # tidak ada frame sama sekali
                cap.release()
                continue
            if sat >= 10 and bright >= 10:
                if fallback is not None:
                    fallback.release()
                print(f"Kamera dibuka: index {idx} (berwarna)")
                return cap
            if fallback is None:
                print(f"[INFO] index {idx} tanpa warna (kamera IR?), lanjut cari kamera lain.")
                fallback = cap
            else:
                cap.release()

        if fallback is not None:
            print("[PERINGATAN] Tidak ada kamera berwarna yang terbuka; "
                  "memakai kamera tanpa warna -> deteksi tangan bisa gagal.")
            return fallback
        raise RuntimeError(self._camera_error(candidates))

    @staticmethod
    def _probe(cap, tries=10, delay=0.03):
        """Baca beberapa frame (kamera perlu pemanasan), ambil saturasi/terang terbaik."""
        best_sat = best_bright = 0.0
        got = False
        for _ in range(tries):
            ok, frame = cap.read()
            if ok and frame is not None:
                got = True
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                best_sat = max(best_sat, float(hsv[:, :, 1].mean()))
                best_bright = max(best_bright, float(hsv[:, :, 2].mean()))
            time.sleep(delay)
        return (best_sat, best_bright) if got else (None, None)

    @staticmethod
    def _camera_error(candidates):
        return (
            "Kamera tidak bisa dibuka. Kemungkinan penyebab:\n"
            "  1. Izin kamera macOS belum diberikan "
            "(System Settings > Privacy & Security > Camera).\n"
            "  2. Kamera sedang dipakai aplikasi lain (Zoom, Teams, browser).\n"
            f"  3. Index kamera salah (dicoba: {candidates}). Ubah CAM_INDEX di config.py.\n"
            "  Catatan: index 0 adalah kamera IR dan tidak pernah dipakai; kamera IR\n"
            "  tidak bisa dipakai untuk deteksi tangan."
        )

    def release(self):
        self.cap.release()
        self.hands.close()

    # ------------------------------------------------------------- pipeline PCD
    def preprocess(self, frame):
        """Tahap 1: CLAHE pada kanal L (LAB) lalu blur.

        CLAHE dipakai supaya kontras tetap terbaca saat cahaya tidak rata
        (mis. tangan di dekat jendela), tanpa mengubah warna asli terlalu jauh.
        """
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = self.clahe.apply(l)
        hasil = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
        return cv2.GaussianBlur(hasil, (config.BLUR_KSIZE, config.BLUR_KSIZE), 0)

    def anchor(self, landmark, shape):
        """Tahap 4: anchor tangan = pusat telapak (landmark 9) dalam piksel."""
        h_frame, w_frame = shape[:2]
        titik = landmark.landmark[config.ANCHOR_LANDMARK]
        return int(titik.x * w_frame), int(titik.y * h_frame)

    def read(self):
        """Kembalikan (frame, debug, hands).

        frame : gambar kamera 320x240 yang sudah dicerminkan (tanpa gambar debug)
        debug : frame pra-pemrosesan + skeleton landmark + label + titik anchor
        hands : {"Left": (x, y), "Right": (x, y)} dalam koordinat frame.
                Label mengikuti gambar yang sudah dicerminkan, jadi "Left" berarti
                tangan di sisi kiri layar.
        """
        ok, frame = self.cap.read()
        if not ok:
            self.terputus = True
            return None, None, {}
        self.terputus = False

        # Semua deteksi dikerjakan di 320x240 agar ringan.
        frame = cv2.resize(frame, (config.PROC_W, config.PROC_H),
                           interpolation=cv2.INTER_AREA)
        frame = cv2.flip(frame, 1)  # cermin agar gerakan terasa natural

        prep = self.preprocess(frame)                    # Tahap 1: CLAHE + blur
        rgb = cv2.cvtColor(prep, cv2.COLOR_BGR2RGB)
        hasil = self.hands.process(rgb)                  # Tahap 2: MediaPipe Hands

        debug = prep.copy()
        posisi = {}
        if hasil.multi_hand_landmarks:
            for landmark, handed in zip(hasil.multi_hand_landmarks,
                                        hasil.multi_handedness):
                label = handed.classification[0].label   # "Left" / "Right"
                # Tahap 3: gambar landmark supaya tahap PCD terlihat.
                mp_drawing.draw_landmarks(debug, landmark, mp_hands.HAND_CONNECTIONS)
                # Tahap 4: anchor pusat telapak.
                titik = self.anchor(landmark, debug.shape)
                cv2.circle(debug, titik, 6, (0, 255, 0), -1)
                cv2.putText(debug, label, (titik[0] + 8, titik[1]),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                # Satu tangan per label: yang pertama (skor tertinggi) dipakai.
                posisi.setdefault(label, titik)

        jumlah = len(posisi)
        cv2.putText(debug, f"TANGAN: {jumlah}", (6, debug.shape[0] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (0, 255, 0) if jumlah else (0, 0, 255), 1)
        return frame, debug, posisi
