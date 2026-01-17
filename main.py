""" MAIN -> this is the entry point of the app """
import cv2
import numpy
from src.Llie import enhance_image
from src.Filtering import apply_color_filter

img = cv2.imread('res/background.png')
#enhanced_image = enhance_image(img)
#filtered_image = apply_color_filter(img, "Warm", 100)
#cv2.imwrite('res/test.png', filtered_image)


for preset in ["Warm", "Cool", "Sepia", "Cinematic", "Black & White"]:
        out = apply_color_filter(img, preset, 100)
        cv2.imwrite(f"res/out_{preset}.jpg", out)

