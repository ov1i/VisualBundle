import cv2
import numpy as np


def build_cinematic_lut():
    """
    Teal-Orange cinematic look:
    - Shadows pushed toward teal
    - Highlights toward orange
    """
    lut = np.zeros((256, 3), dtype=np.uint8)
    for i in range(256):
        b = np.clip(i * 1.15 if i < 128 else i * 0.95, 0, 255)
        g = np.clip(i * 1.05, 0, 255)
        r = np.clip(i * 0.90 if i < 128 else i * 1.20, 0, 255)
        lut[i] = [b, g, r]
    return lut