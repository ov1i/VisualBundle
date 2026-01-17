import cv2
import numpy as np

def single_scale_retinex(img, sigma=30, eps=1e-6):
    """Compute Single-Scale Retinex (SSR) on a color image.


    We operate per-channel in float, compute log(I) - log(blur(I)). Output is
    contrast-normalized back to uint8.


    Args:
        img: BGR uint8 image.
        sigma: Gaussian blur sigma for the surround function.
        eps: small epsilon to avoid log(0).


    Returns:
        BGR uint8 image after SSR.
    """
    img_f = img.astype(np.float32) + eps
    # Split channels B, G, R
    channels = cv2.split(img_f)
    result_channels = []
    for ch in channels:
        # Gaussian blur as surround
        blur = cv2.GaussianBlur(ch, (0, 0), sigmaX=sigma, sigmaY=sigma)
        # SSR formula (log domain)
        ssr = np.log(ch) - np.log(blur + eps)
        # Normalize ssr to 0..255
        ssr = ssr - ssr.min()
        if ssr.max() > 0:
            ssr = ssr / ssr.max()
        ssr = (ssr * 255).astype(np.uint8)
        result_channels.append(ssr)
    out = cv2.merge(result_channels)
    return out

