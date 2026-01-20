# flip.py
from PIL import Image


def flip_horizontal(pil_img: Image.Image) -> Image.Image:
    return pil_img.transpose(Image.FLIP_LEFT_RIGHT)


def flip_vertical(pil_img: Image.Image) -> Image.Image:
    return pil_img.transpose(Image.FLIP_TOP_BOTTOM)
