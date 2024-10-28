import cv2

img = cv2.imread("C:\\Users\\Acer\\OneDrive\\Desktop\\download images\\download (3).jpg")
hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

cv2.imshow('HSV Image', hsv_img)
cv2.waitKey(0)
cv2.destroyAllWindows()