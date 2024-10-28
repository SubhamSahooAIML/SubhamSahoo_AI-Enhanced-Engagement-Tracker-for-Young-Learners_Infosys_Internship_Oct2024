import cv2

img = cv2.imread("C:\\Users\\Acer\\OneDrive\\Desktop\\images stock\\lighthouse-9073925_640.webp",0)
equalized = cv2.equalizeHist(img)

cv2.imshow('Equalized Image', equalized)
cv2.waitKey(0)
cv2.destroyAllWindows()