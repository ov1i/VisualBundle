import cv2
import numpy as np
from src.Llie import apply_clahe_color,  unsharp_mask

def combine_adaptive(original, clahe_img, ssr_img, intensity=0.5, detail=0.2):
    """Combine CLAHE and SSR adaptively using intensity and detail weights.


    Args:
        original: BGR uint8 original input image.
        clahe_img: BGR uint8 CLAHE result.
        ssr_img: BGR uint8 SSR result.
        intensity: [0..1] weight favoring SSR (illumination correction) over CLAHE.
        detail: [0..1] detail enhancement strength.


    Returns:
        BGR uint8 combined enhanced image.
    """
    # Ensure floats for blending
    o = original.astype(np.float32)
    c = clahe_img.astype(np.float32)
    s = ssr_img.astype(np.float32)


    # Detail enhancement via unsharp mask on CLAHE result (so colors are preserved)
    # Map detail slider to unsharp mask amount and radius
    amount = 0.6 * detail + 0.1 # base amount
    radius = 1.0 + 10.0 * detail
    detail_sharp = unsharp_mask(c.astype(np.uint8), amount=amount, radius=radius).astype(np.float32)


    # Combine: weighted sum of CLAHE and SSR, plus a small contribution of sharpened detail
    combined = (1.0 - intensity) * c + intensity * s
    combined = 0.85 * combined + 0.15 * detail_sharp


    # Tiny preserve of original color balance by a small mix
    combined = 0.95 * combined + 0.05 * o


    combined = np.clip(combined, 0, 255).astype(np.uint8)
    return combined