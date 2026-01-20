import cv2
import numpy as np



def build_warm_lut():
    lut = np.zeros((256, 3), dtype=np.uint8)
    for i in range(256):
        r = np.clip(i * 1.25, 0, 255)
        g = np.clip(i * 1.05, 0, 255)
        b = np.clip(i * 0.85, 0, 255)
        lut[i] = [b, g, r]
    return lut