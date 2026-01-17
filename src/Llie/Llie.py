import numpy as np
import cv2
from src.Llie import apply_clahe_color,  unsharp_mask, combine_adaptive, single_scale_retinex

def enhance_image(img, intensity=0.2, detail=0.3, clahe_clip=2.0, tile_grid=(8, 8)):
    """Main enhancement function exposed to GUI.


    Args:
    img: BGR uint8 image (numpy array).
    intensity: float in [0,1] — controls mixing between CLAHE (0) and SSR (1).
    detail: float in [0,1] — controls detail enhancement strength.
    clahe_clip: CLAHE clip limit.
    tile_grid: CLAHE tile grid size tuple.


    Returns:
    Enhanced BGR uint8 image.
    """
    # Input validation
    if img is None:
        raise ValueError("Input image is None")
    if img.dtype != np.uint8:
        raise ValueError("Input image must be uint8 BGR")


    # Step 1: CLAHE on luminance
    clahe_img = apply_clahe_color(img, clip_limit=clahe_clip, tile_grid_size=tile_grid)


    # Step 2: SSR — adapt sigma based on detail (small detail => larger sigma?)
    # We'll make sigma inversely proportional to detail to keep fine details when detail slider high
    min_sigma = 10.0
    max_sigma = 80.0
    # If detail high -> small sigma to preserve fine structures; detail low -> large sigma for smoother illumination
    sigma = max_sigma - (max_sigma - min_sigma) * detail
    ssr_img = single_scale_retinex(img, sigma=sigma)


    # Step 3: Combine adaptively
    out = combine_adaptive(img, clahe_img, ssr_img, intensity=float(intensity), detail=float(detail))
    return out