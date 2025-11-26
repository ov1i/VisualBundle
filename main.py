""" MAIN -> this is the entry point of the app """
import cv2
import numpy

green = numpy.uint8([[[0,255,0 ]]])
hsv_green = cv2.cvtColor(green,cv2.COLOR_BGR2HSV)
print( hsv_green )

print("HELL WORLD!")
