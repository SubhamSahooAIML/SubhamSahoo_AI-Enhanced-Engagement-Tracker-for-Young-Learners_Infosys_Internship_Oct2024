import cv2
import numpy as np

img1 = cv2.imread("C:\\Users\\Acer\\OneDrive\\Desktop\\download images\\download (3).jpg")
img2 = cv2.imread("C:\\Users\\Acer\\OneDrive\\Desktop\\download images\\download (2).jpg")
img3 = cv2.imread("C:\\Users\\Acer\\OneDrive\\Desktop\\download images\\download (2).jpg")
img1 = cv2.resize(img1, (500, 500))
img2 = cv2.resize(img2, (500, 500))
img3 = cv2.resize(img3, (500, 500))

h_concat = np.hstack((img1, img2,img3))#concatination horizontally adding the two image  
v_concat = np.vstack((img1, img2,img3))#concatination vertically adding the two image 

cv2.imshow('Horizontal Concatenation', h_concat)
cv2.imshow('Vertical Concatenation', v_concat)

cv2.waitKey(0)
cv2.destroyAllWindows()