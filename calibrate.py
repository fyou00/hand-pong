"""Kalibrasi rentang warna kulit dengan trackbar.

Jalankan:  python calibrate.py
Atur trackbar sampai tangan berwarna putih penuh dan latar hitam.
Tekan 's' untuk mencetak nilai yang siap ditempel ke config.py.
Tekan 'q' atau ESC untuk keluar.

Ruang warna mengikuti COLOR_SPACE di config.py ("hsv" atau "ycrcb").
"""

import cv2

import config
from hand_tracker import HandTracker, skin_mask

MAX_VAL = {"H": 179}  # H cuma sampai 179, sisanya 255


def nothing(_):
    pass


def main():
    if config.COLOR_SPACE == "ycrcb":
        names = ("Y", "Cr", "Cb")
        lower = list(config.YCRCB_LOWER)
        upper = list(config.YCRCB_UPPER)
    else:
        names = ("H", "S", "V")
        lower = list(config.HSV_LOWER)
        upper = list(config.HSV_UPPER)

    # Pakai HandTracker supaya pemilihan kamera (lewati kamera IR) sama dengan game.
    tracker = HandTracker()
    cap = tracker.cap

    cv2.namedWindow("Kalibrasi - Mask")
    cv2.namedWindow("Kalibrasi - Kamera")
    for i, name in enumerate(names):
        hi = MAX_VAL.get(name, 255)
        cv2.createTrackbar(f"{name} min", "Kalibrasi - Mask", int(lower[i]), hi, nothing)
        cv2.createTrackbar(f"{name} max", "Kalibrasi - Mask", int(upper[i]), hi, nothing)

    print("Geser trackbar sampai mask putih mengikuti tangan. 's' = cetak nilai, 'q' = keluar.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Frame gagal dibaca (kamera terputus?).")
            break

        frame = cv2.resize(frame, (config.PROC_W, config.PROC_H),
                           interpolation=cv2.INTER_AREA)
        frame = cv2.flip(frame, 1)

        lo, hi = [], []
        for i, name in enumerate(names):
            lo.append(cv2.getTrackbarPos(f"{name} min", "Kalibrasi - Mask"))
            hi.append(cv2.getTrackbarPos(f"{name} max", "Kalibrasi - Mask"))

        # Mask yang ditampilkan = mask yang dipakai game (tanpa buang wajah).
        mask = skin_mask(frame, lo, hi)

        cv2.imshow("Kalibrasi - Kamera", frame)
        cv2.imshow("Kalibrasi - Mask", mask)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        if key == ord("s"):
            if config.COLOR_SPACE == "ycrcb":
                print(f"YCRCB_LOWER = {tuple(lo)}")
                print(f"YCRCB_UPPER = {tuple(hi)}")
            else:
                print(f"HSV_LOWER = {tuple(lo)}")
                print(f"HSV_UPPER = {tuple(hi)}")

    tracker.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
