import cv2
import numpy as np

def build_sepia_lut():
    lut = np.zeros((256, 3), dtype=np.uint8)
    for i in range(256):
        r = np.clip(0.393 * i + 0.769 * i + 0.189 * i, 0, 255)
        g = np.clip(0.349 * i + 0.686 * i + 0.168 * i, 0, 255)
        b = np.clip(0.272 * i + 0.534 * i + 0.131 * i, 0, 255)
        lut[i] = [b, g, r]
    return lut