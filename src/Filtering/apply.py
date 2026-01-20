import cv2
import numpy as np
from src.Filtering import build_cinematic_lut, build_cool_lut, build_sepia_lut, build_warm_lut

def apply_lut(img, lut):
    """
    Apply a 3-channel LUT correctly (per channel).
    """
    b, g, r = cv2.split(img)
    b = cv2.LUT(b, lut[:, 0])
    g = cv2.LUT(g, lut[:, 1])
    r = cv2.LUT(r, lut[:, 2])
    return cv2.merge((b, g, r))

def apply_color_filter(img, preset_name, intensity_percent):
    """
    img: BGR uint8 image
    preset_name: string from dropdown
    intensity_percent: 0–100 (slider)
    """

    intensity = np.clip(intensity_percent / 100.0, 0.0, 1.0)

    if preset_name == "Warm":
        lut = build_warm_lut()
        filtered = apply_lut(img, lut)

    elif preset_name == "Cool":
        lut = build_cool_lut()
        filtered = apply_lut(img, lut)

    elif preset_name == "Sepia":
        lut = build_sepia_lut()
        filtered = apply_lut(img, lut)

    elif preset_name == "Cinematic":
        lut = build_cinematic_lut()
        filtered = apply_lut(img, lut)

    elif preset_name == "Black & White":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        filtered = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    else:
        # No filter
        filtered = img.copy()

    # Blend original and filtered image
    output = cv2.addWeighted(
        img, 1.0 - intensity,
        filtered, intensity,
        0
    )

    return output




