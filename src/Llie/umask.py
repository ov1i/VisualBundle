import numpy as np
import cv2

def unsharp_mask(img, amount=1.0, radius=1.0):
    """Simple unsharp mask: enhance local detail.


    Args:
        img: BGR uint8 image.
        amount: strength multiplier.
        radius: gaussian blur sigma for mask.
    Returns:
        BGR uint8 sharpened image.
    """
    if radius <= 0:
        return img.copy()
    img_f = img.astype(np.float32)
    blurred = cv2.GaussianBlur(img_f, (0, 0), sigmaX=radius, sigmaY=radius)
    mask = img_f - blurred
    sharp = img_f + amount * mask
    sharp = np.clip(sharp, 0, 255).astype(np.uint8)
    return sharp