import re
import cv2
import os
from PIL import Image
import easyocr
reader = easyocr.Reader(["en"])


def captcha_solver_easyOCR(image_file_name):
    img = Image.open(image_file_name)
    # Create a new image with a white background
    new_img = Image.new("RGB", (img.width, img.height), color="white")

    new_img.paste(img, (0, 0), img)

    new_img = new_img.convert("L")
    new_img = new_img.point(lambda x: 0 if x < 128 else 255, "1")
    new_img.save("sample/new_image_BW_easyOCR.png")
    inverted_image = Image.eval(new_img, lambda pixel: 255 - pixel)

    inverted_image.save("sample/new_image_WB_easyOCR.png")

    img = cv2.imread("sample/new_image_WB_easyOCR.png", 0)
    img = cv2.copyMakeBorder(img, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    blur = cv2.GaussianBlur(img, (13, 13), 0)
    thresh = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY)[1]

    cv2.imwrite("sample/result_easyOCR.png", thresh)
    bounds = reader.readtext("sample/result_easyOCR.png")
    captcha_text = re.sub(r"\W+", "", bounds[0][1])
    return captcha_text.replace(" ", "").upper()
