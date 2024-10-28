import cv2

img = cv2.imread("C:\\Users\\Acer\\OneDrive\\Desktop\\images stock\\lighthouse-9073925_640.webp",0)
_, threshold = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY) #255 =white ,>127 is black 
contours ,_= cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

cv2.drawContours(img, contours, -1, (0, 256, 0), 0)

cv2.imshow('Contours', img)
cv2.waitKey(0)
cv2.destroyAllWindows()