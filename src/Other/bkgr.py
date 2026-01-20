# bkgr.py
import os
import io
from typing import Optional, Tuple

from PIL import Image
from rembg import remove


def run_background_removal(
    image_path: str,
    pil_image: Optional[Image.Image] = None
) -> Tuple[Image.Image, Image.Image]:
    """
    Removes background from the given image.
    - No saving to disk.
    Returns: (original_pil, removed_bg_pil_rgba)
    """
    if not image_path or not os.path.exists(image_path):
        raise FileNotFoundError(f"File does not exist:\n{image_path}")

    original = pil_image if pil_image is not None else Image.open(image_path)

    result = remove(original)  # may return PIL.Image or bytes depending on rembg version
    if isinstance(result, Image.Image):
        removed_bg = result
    else:
        removed_bg = Image.open(io.BytesIO(result))

    removed_bg = removed_bg.convert("RGBA")
    return original, removed_bg
