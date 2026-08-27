"""
preprocess.py — Image preprocessing utilities for UrbanEye edge detection.

NOTE: The EdgeDetector.detect() method currently bypasses this preprocessing
step because the YOLOv8 model was trained on raw images. Applying CLAHE/blur
causes the model to miss detections. YOLO handles resizing/normalisation
internally. This module is retained as a stub for future use.
"""

import cv2


def preprocess_image(image_path: str):
    """
    Load and preprocess an image for edge analysis.

    Currently a pass-through — returns the raw image loaded by OpenCV.
    CLAHE and blur preprocessing is intentionally disabled (see module docstring).

    Args:
        image_path: Path to the image file.

    Returns:
        numpy.ndarray: The loaded image in BGR format.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")
    return img
