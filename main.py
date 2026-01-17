""" MAIN -> this is the entry point of the app """
import cv2
import numpy
from src.Llie import enhance_image

img = cv2.imread('res/city.png')
enhanced_image = enhance_image(img)
cv2.imwrite('res/test.png', enhanced_image)

