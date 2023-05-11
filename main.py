import cv2
from picamera2 import Picamera2
import time
from time import sleep
import numpy as np
from fastiecm import fastiecm
from pathlib import Path
import RPi.GPIO as GPIO
import os

base_folder = Path(__file__).parent.resolve()
GPIO.setmode(GPIO.BCM)
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)


REDVAL = 0.544
REDINIT = int(REDVAL / (4 / 255))
BLUEVAL = 1.248
BLUEINIT = int(BLUEVAL / (4 / 255))
AGAINVAL = 9.286
AGINIT = int(AGAINVAL / (10 / 255))
CONTRAST = 1.376
CINIT = int(CONTRAST / (2 / 255))
BRIGHT = 0.0


def RedSetting(val):
    global REDVAL
    redFloat = val * (4 / 255)
    REDVAL = redFloat
    print("Red: ", REDVAL)


def BlueSetting(val):
    global BLUEVAL
    blueFloat = val * (4 / 255)
    BLUEVAL = blueFloat
    print("Blue: ", blueFloat)


def AnalogueGainSetting(val):
    global AGAINVAL
    AGainFloat = val * (10 / 255)
    AGAINVAL = AGainFloat
    print("Analogue Gain: ", AGainFloat)

def ContrastSetting(val):
    global CONTRAST
    ContrastFloat = val * (2 / 255)
    CONTRAST = ContrastFloat
    print("Contrast: ", ContrastFloat)


def BrightnessSetting(val):
    global BRIGHT
    BrightFloat = (val / 255) * 2 - 1
    BRIGHT = BrightFloat
    print("Brightness: ", BrightFloat)


def PrintSettings():
    metadata = picam2.capture_metadata()
    controls = {c: metadata[c] for c in ["ExposureTime", "AnalogueGain", "ColourGains"]}
    print(picam2.camera_controls["ExposureTime"])
    print(picam2.camera_controls["AnalogueGain"])
    print(picam2.camera_controls["ColourGains"])


def contrast_stretch(image):
    in_min = np.percentile(image, 5)
    in_max = np.percentile(image, 95)

    out_min = 0.0
    out_max = 255.0

    out = image - in_min
    out *= (out_min - out_max) / (in_min - in_max)
    out += in_min

    return out


# Filter NDVI
def calc_ndvi(image):
    b, g, r, a = cv2.split(image)
    bottom = r.astype(float) + b.astype(float)
    bottom[bottom == 0] = 0.01
    ndvi = (b.astype(float) - r) / bottom
    return ndvi

# Colour map NDVI
def color_map(image):
    color_mapped_prep = image.astype(np.uint8)
    color_mapped_image = cv2.applyColorMap(color_mapped_prep, fastiecm)
    return color_mapped_image


if __name__ == "__main__":
    picam2 = Picamera2()
    picam2.set_controls(
        {"ExposureTime": 12000, "AnalogueGain": 1.2, "AwbEnable": 0, "AeEnable": 0})
    picam2.preview_configuration.main.format = "XRGB8888"
    picam2.preview_configuration.main.size = (640, 360)
    picam2.preview_configuration.controls.FrameRate = 15
    picam2.preview_configuration.align()
    picam2.start()
    time.sleep(2)

    im = picam2.capture_array()
    ndvi_im = calc_ndvi(im)
    ndvi_contrast_im = contrast_stretch(ndvi_im)
    colour_map = color_map(ndvi_contrast_im)
    cv2.imshow("Camera", colour_map)
    cv2.createTrackbar("Red", "Camera", REDINIT, 255, RedSetting)
    cv2.createTrackbar("Blue", "Camera", BLUEINIT, 255, BlueSetting)
    cv2.createTrackbar("AnalogueGain", "Camera", AGINIT, 255, AnalogueGainSetti>
    cv2.createTrackbar("Contrast", "Camera", CINIT, 255, ContrastSetting)
    cv2.createTrackbar("Brightness", "Camera", 0, 255, BrightnessSetting)

    # Set up variables for the images folder and filenames
    images_folder = "images"
    image_name_prefix = "image_"
    image_ext = ".jpg"

    # Find the next available image number
    count = 1
    while True:
        image_name = f"{image_name_prefix}{count:03d}{image_ext}"
        image_path = os.path.join(images_folder, image_name)
        if not os.path.exists(image_path):
            break
        count += 1
    img_count = count

    while True:
        im = picam2.capture_array()
        ndvi_im = calc_ndvi(im)
        ndvi_contrast_im = contrast_stretch(ndvi_im)
        colour_map = color_map(ndvi_contrast_im)
        cv2.imshow("Camera", colour_map)
        with picam2.controls as controls:
            controls.ColourGains = (REDVAL, BLUEVAL)
            controls.AnalogueGain = AGAINVAL
            controls.Contrast = CONTRAST
            controls.Brightness = BRIGHT
        if cv2.waitKey(1) == ord("q"):
            break
        if GPIO.input(15) == GPIO.LOW:
            # Create the filename for the new image
            img_count += 1
            filename = f"{image_name_prefix}{img_count:03d}{image_ext}"
            output_path = os.path.join(images_folder, filename)

            # Save the image and print a message
            cv2.imwrite(output_path, colour_map)
            print(f"Captured {filename}")
            sleep(1)  # add a short delay to prevent button bounce
    cv2.destroyAllWindows()
    picam2.stop()
