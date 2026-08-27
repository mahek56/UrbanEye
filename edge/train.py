from ultralytics import YOLO
import os

def train_model(
    data_yaml_path,
    epochs=100,
    imgsz=640,
    base_model="yolov8s.pt",
    patience=20
):
    """
    Fine-tunes a YOLOv8 model on a custom dataset.

    Args:
        data_yaml_path (str): Path to the dataset configuration file (e.g., 'data/data.yaml').
        epochs (int): Maximum number of training epochs.
        imgsz (int): Image size for training.
        base_model (str): The base YOLOv8 model to start from.
            'yolov8n.pt' = nano (fastest, less accurate)
            'yolov8s.pt' = small (recommended, ~11M params, good balance)
        patience (int): Early stopping patience — stops training if val loss doesn't
            improve for this many consecutive epochs.

    Notes on augmentation:
        Ultralytics YOLOv8 already applies comprehensive augmentation by default:
        mosaic=1.0, fliplr=0.5, hsv_h/s/v, scale=0.5, translate=0.1.
        We only add degrees=5.0 (mild rotation) as roads benefit from rotational variance.
        We do NOT override the default confidence threshold (0.25) during training.
        See detect.py for inference threshold discussion.
    """
    if not os.path.exists(data_yaml_path):
        raise FileNotFoundError(f"Dataset config not found at: {data_yaml_path}")

    print(f"Starting training on {data_yaml_path}")
    print(f"  Base model : {base_model}")
    print(f"  Max epochs : {epochs} (early stopping patience={patience})")
    print(f"  Image size : {imgsz}")

    # Load the base model
    model = YOLO(base_model)

    # Train the model
    results = model.train(
        data=data_yaml_path,
        epochs=epochs,
        imgsz=imgsz,
        patience=patience,           # Early stopping
        degrees=5.0,                 # Mild rotation augmentation (not in YOLO defaults)
        project="runs/detect",       # Outputs saved in edge/runs/detect/
        name="urbaneye_model",
        exist_ok=True,               # Overwrite previous run folder instead of creating urbaneye_model2
    )

    print("\nTraining complete.")
    print("Best weights saved at: runs/detect/urbaneye_model/weights/best.pt")
    return results

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(script_dir, "data", "data.yaml")

    train_model(yaml_path)
