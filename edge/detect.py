from ultralytics import YOLO
from preprocess import preprocess_image
import os

# Map YOLO class IDs to API event types
# Default YOLOv8 models usually have 80 COCO classes, but our fine-tuned model 
# will have classes defined in data.yaml (0: 'pothole').
CLASS_MAP = {
    0: "pothole",
    # If trained with more classes:
    # 1: "road_damage",
    # 2: "congestion",
    # 3: "obstruction"
}

class EdgeDetector:
    def __init__(self, model_path="runs/detect/runs/detect/urbaneye_model/weights/best.pt"):
        """
        Initializes the YOLOv8 model.
        Args:
            model_path: Path to the YOLOv8 weights (e.g., 'best.pt' after training).
        """
        self.model = YOLO(model_path)

    def detect(self, image_path):
        """
        Runs detection on a given image.
        Args:
            image_path: Path to the image file.
        Returns:
            A list of dictionaries representing detections:
            [{"type": "pothole", "confidence": 0.95, "bbox": [x1, y1, x2, y2]}]
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        # We bypass custom OpenCV preprocessing because the YOLO model was trained 
        # on raw images, and applying CLAHE/Blur causes it to miss the potholes.
        # YOLO internally handles resizing and normalization anyway.
        
        # Run inference
        results = self.model(image_path, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].tolist() # [x1, y1, x2, y2]
                
                # Default to 'road_damage' if class id isn't in map for some reason
                event_type = CLASS_MAP.get(cls_id, "road_damage")
                
                detections.append({
                    "type": event_type,
                    "confidence": conf,
                    "bbox": xyxy
                })
                
        return detections
