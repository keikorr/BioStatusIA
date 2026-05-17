import cv2
import numpy as np


def segmentar(img: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    img_u8 = (img * 255).astype(np.uint8)
    thresh = cv2.adaptiveThreshold(
        img_u8, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2,
    )
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mascara = np.zeros_like(img_u8)
    if contours:
        cnt = max(contours, key=cv2.contourArea)
        cv2.drawContours(mascara, [cnt], -1, 255, -1)
    return mascara, img_u8
