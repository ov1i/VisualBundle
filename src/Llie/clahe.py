import cv2
import numpy as np

def apply_clahe_color(img, clip_limit=2.0, tile_grid_size=(8, 8)):
    """Apply CLAHE to the luminance (Y) channel of a color image.


    Args:
        img: BGR uint8 image.
        clip_limit: CLAHE clip limit.
        tile_grid_size: tile grid size for CLAHE.


    Returns:
        BGR uint8 image with CLAHE applied on luminance.
    """
    # Convert to YCrCb
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    y_clahe = clahe.apply(y)
    ycrcb_clahe = cv2.merge((y_clahe, cr, cb))
    out = cv2.cvtColor(ycrcb_clahe, cv2.COLOR_YCrCb2BGR)
    return out
