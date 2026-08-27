# UrbanEye Edge Module

This module contains the AI logic for detecting urban events (like potholes) from images, typically running on an edge device (e.g., a bus camera system).

## Architecture

*   `preprocess.py`: OpenCV-based image preprocessing (resizing, denoising, contrast enhancement).
*   `detect.py`: YOLOv8 inference wrapper.
*   `event.py`: Formats the detection into the strict JSON schema required by the UrbanEye API Contract.
*   `train.py`: A helper script to fine-tune a YOLOv8 model on a custom dataset.
*   `test_run.py`: An example script showing how to process an image and generate the JSON output.

## Setup

1.  **Install dependencies:**
    ```bash
    cd edge
    pip install -r requirements.txt
    ```

2.  **Dataset (for training):**
    Ensure your dataset is organized in YOLO format. The configuration is expected at `data/data.yaml`.

## Usage

### Training

To fine-tune the model on your dataset:
```bash
python train.py
```
This will output weights into `runs/detect/urbaneye_model/weights/best.pt`.

### Inference / Test Run

To test the detection and JSON formatting pipeline:
```bash
python test_run.py
```
*(This script will create a dummy image if none is provided, run inference, and print the resulting JSON event).*

## Expected JSON Output Schema

```json
{
  "bus_id": "BUS_01",
  "lat": 17.4239,
  "lon": 78.4738,
  "timestamp": "2026-08-26T10:15:00Z",
  "type": "pothole",
  "confidence": 0.87
}
```
