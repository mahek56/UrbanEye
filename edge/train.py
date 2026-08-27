from ultralytics import YOLO
import os

def train_model(data_yaml_path, epochs=50, imgsz=640, base_model="yolov8n.pt"):
    """
    Fine-tunes a YOLOv8 model on a custom dataset.
    
    Args:
        data_yaml_path (str): Path to the dataset configuration file (e.g., 'data/data.yaml').
        epochs (int): Number of training epochs.
        imgsz (int): Image size for training.
        base_model (str): The base YOLOv8 model to start from.
    """
    if not os.path.exists(data_yaml_path):
        raise FileNotFoundError(f"Dataset config not found at: {data_yaml_path}")
        
    print(f"Starting training on {data_yaml_path} using {base_model}...")
    
    # Load the base model
    model = YOLO(base_model)
    
    # Train the model
    results = model.train(
        data=data_yaml_path,
        epochs=epochs,
        imgsz=imgsz,
        project="runs/detect", # Outputs will be saved in edge/runs/detect
        name="urbaneye_model"
    )
    
    print("Training complete.")
    print("Best weights should be saved in: runs/detect/urbaneye_model/weights/best.pt")
    
if __name__ == "__main__":
    # Assuming data.yaml is in the 'data' directory relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(script_dir, "data", "data.yaml")
    
    train_model(yaml_path, epochs=10) # Set to a low number for quick MVP testing
