import cv2
import numpy as np

def preprocess_image(image_path):
    """
    Reads an image from a path and applies preprocessing steps.
    - Resizes to standard YOLO size (640x640) for consistent output if needed
      (Though YOLOv8 handles resizing internally, we might want it for other pipelines).
    - Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) for better feature extraction.
    - Applies mild Gaussian Blur for denoising.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image at {image_path}")

    # Resize (optional, Ultralytics YOLO does this internally by default, 
    # but good for explicit preprocessing step if we want to save the processed image)
    img_resized = cv2.resize(img, (640, 640))

    # Convert to LAB color space to apply CLAHE to the L channel
    lab = cv2.cvtColor(img_resized, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)

    # Merge channels back and convert to BGR
    limg = cv2.merge((cl, a, b))
    img_clahe = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    # Mild denoising
    img_denoised = cv2.GaussianBlur(img_clahe, (3, 3), 0)

    return img_denoised
