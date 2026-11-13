"""Tahap PCD: segmentasi warna kulit + pencarian pusat tangan.

Alur: resize 320x240 -> blur -> konversi warna -> threshold -> morfologi
      -> buang wajah -> kontur terbesar -> pusat (bbox/moment) -> rata-rata N frame.
"""

import time

import cv2
import numpy as np

import config


def skin_mask(bgr, lower, upper, kernel_size=5):
    """Tahap 1-3: blur -> ruang warna (HSV/YCrCb) -> thresholding -> morfologi."""
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
        self.history = []        # riwayat pusat tangan untuk perata-rataan
        self.last_rect = None    # bbox tangan terakhir (untuk gambar debug)
        self.last_rects = []     # bbox semua tangan pada mode dua pemain

        self.face_cascade = None
        if config.USE_FACE_HAAR:
            path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.face_cascade = cv2.CascadeClassifier(path)
            if self.face_cascade.empty():
                print("[PERINGATAN] Cascade wajah tidak ditemukan, deteksi wajah dimatikan.")
                self.face_cascade = None

    # ------------------------------------------------------------------ kamera
    def _open_camera(self, cam_index):
        """Item 5: kamera dibuka pada index RGB; index 0 (kamera IR) tidak pernah dipakai.

        Kamera IR (Windows Hello) menghasilkan frame hitam/abu-abu, sehingga
        segmentasi warna kulit pasti gagal. Karena itu index 0 tidak pernah
        dibuka: kalau CAM_INDEX = 0, nilainya diabaikan dan pencarian otomatis
        dimulai dari CAM_INDEX_CANDIDATES (index 1 ke atas).
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
                      "Mask kulit akan hitam. Coba index lain di CAM_INDEX (config.py).")
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
                  "memakai kamera tanpa warna -> mask kulit akan hitam.")
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
            "  tidak bisa dipakai untuk segmentasi warna."
        )

    def release(self):
        self.cap.release()

    # ------------------------------------------------------------- pipeline PCD
    def _read_frame(self):
        """Ambil frame, resize + cermin, lalu buang area wajah dari mask.

        Kembalikan (frame, mask, faces); frame None bila kamera gagal.
        """
        ok, frame = self.cap.read()
        if not ok:
            return None, None, None

        # Item 8: semua deteksi dikerjakan di 320x240 agar ringan.
        frame = cv2.resize(frame, (config.PROC_W, config.PROC_H),
                           interpolation=cv2.INTER_AREA)
        frame = cv2.flip(frame, 1)  # cermin agar gerakan terasa natural

        faces = self.detect_faces(frame)
        mask = self.segment(frame, faces)
        return frame, mask, faces

    def read(self):
        """Kembalikan (frame, mask, center, faces); center None bila tak ada tangan."""
        frame, mask, faces = self._read_frame()
        if frame is None:
            return None, None, None, []
        return frame, mask, self.find_hand_center(mask), faces

    def read_hands(self):
        """Varian dua pemain: (frame, mask, daftar pusat tangan, faces)."""
        frame, mask, faces = self._read_frame()
        if frame is None:
            return None, None, [], []
        return frame, mask, self.find_hand_centers(mask), faces

    def detect_faces(self, frame):
        """Item 2: kotak wajah (Haar) diperluas sedikit agar dagu/leher ikut terbuang."""
        if self.face_cascade is None:
            return []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        found = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1,
                                                  minNeighbors=5, minSize=(60, 60))
        h_frame, w_frame = frame.shape[:2]
        boxes = []
        for (x, y, w, h) in found:
            mx, my = int(w * config.FACE_MARGIN), int(h * config.FACE_MARGIN)
            x0, y0 = max(0, x - mx), max(0, y - my)
            x1, y1 = min(w_frame, x + w + mx), min(h_frame, y + h + my)
            boxes.append((x0, y0, x1 - x0, y1 - y0))
        return boxes

    def segment(self, frame, faces=()):
        """Mask kulit, lalu area wajah dan (opsional) bagian atas dibuang."""
        if config.COLOR_SPACE == "ycrcb":
            lower, upper = config.YCRCB_LOWER, config.YCRCB_UPPER
        else:
            lower, upper = config.HSV_LOWER, config.HSV_UPPER

        mask = skin_mask(frame, lower, upper)

        for (x, y, w, h) in faces:
            mask[y:y + h, x:x + w] = 0

        if config.ROI_TOP > 0:
            mask[:int(mask.shape[0] * config.ROI_TOP), :] = 0
        return mask

    def find_hand_center(self, mask):
        """Tahap 4-5: kontur terbesar = tangan, lalu hitung pusatnya."""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        min_area = config.MIN_AREA_RATIO * mask.shape[0] * mask.shape[1]
        largest = max(contours, key=cv2.contourArea) if contours else None

        # Item 3: ambang area relatif terhadap luas frame.
        if largest is None or cv2.contourArea(largest) < min_area:
            self.history.clear()
            self.last_rect = None
            return None

        x, y, w, h = cv2.boundingRect(largest)
        self.last_rect = (x, y, w, h)

        # Item 4: pilih pusat bounding box atau centroid momen.
        if config.CENTER_MODE == "moment":
            m = cv2.moments(largest)
            if m["m00"] == 0:
                self.history.clear()
                return None
            cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
        else:
            cx, cy = x + w / 2, y + h / 2

        # Item 4: rata-rata beberapa frame terakhir agar tidak bergetar.
        self.history.append((cx, cy))
        if len(self.history) > config.AVG_FRAMES:
            self.history.pop(0)
        n = len(self.history)
        return (int(sum(p[0] for p in self.history) / n),
                int(sum(p[1] for p in self.history) / n))

    def find_hand_centers(self, mask, max_hands=config.MAX_HANDS):
        """Tahap 4-5 (dua pemain): centroid dari maksimal `max_hands` kontur terbesar.

        Beda dengan find_hand_center: tiap tangan dianggap objek terpisah, jadi
        tidak ada rata-rata N frame (smoothing-nya di paddle, pakai dt). Hasil
        diurut area terbesar -> terkecil, supaya tangan utama (lebih dekat
        kamera) dipakai lebih dulu saat dua tangan jatuh di zona yang sama.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        # Item 3: ambang area relatif terhadap luas frame.
        min_area = config.MIN_AREA_RATIO * mask.shape[0] * mask.shape[1]
        kandidat = [c for c in contours if cv2.contourArea(c) >= min_area]
        kandidat.sort(key=cv2.contourArea, reverse=True)

        pusat = []
        self.last_rects = []
        for c in kandidat[:max_hands]:
            x, y, w, h = cv2.boundingRect(c)
            # Item 4: pusat bounding box atau centroid momen, sama seperti mode satu pemain.
            if config.CENTER_MODE == "moment":
                m = cv2.moments(c)
                if m["m00"] == 0:
                    continue
                cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
            else:
                cx, cy = x + w / 2, y + h / 2
            pusat.append((int(cx), int(cy)))
            self.last_rects.append((x, y, w, h))
        return pusat
