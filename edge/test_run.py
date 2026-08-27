import os
import glob
import random
from detect import EdgeDetector
from event import create_event, event_to_json

if __name__ == "__main__":
    test_images_dir = os.path.join("data", "test", "images")
    
    # Try to find all images
    image_files = glob.glob(os.path.join(test_images_dir, "*.jpg")) + \
                  glob.glob(os.path.join(test_images_dir, "*.jpeg")) + \
                  glob.glob(os.path.join(test_images_dir, "*.png"))
                  
    if not image_files:
        print(f"Error: No images found in {test_images_dir}")
        exit(1)
        
    # Pick a random sample of up to 5 images
    num_samples = min(5, len(image_files))
    # Seed random for repeatable output in testing (optional, but nice)
    random.seed(42)
    sample_images = random.sample(image_files, num_samples)
        
    print(f"Initializing EdgeDetector (loading from runs/detect/urbaneye_model/weights/best.pt)...")
    detector = EdgeDetector() 
    
    total_images_tested = 0
    images_with_detections = 0
    total_detections_found = 0
    
    print("\n" + "="*50)
    print(f"STARTING DETECTION ON {num_samples} IMAGES")
    print("="*50)
    
    for img_path in sample_images:
        filename = os.path.basename(img_path)
        print(f"\n--- Processing: {filename} ---")
        
        try:
            detections = detector.detect(img_path)
        except Exception as e:
            print(f"Failed to run detection on {filename}: {e}")
            continue
            
        total_images_tested += 1
        
        if len(detections) > 0:
            images_with_detections += 1
            total_detections_found += len(detections)
            print(f"Raw Detections List: {detections}")
            
            for det in detections:
                event = create_event(
                    detection=det,
                    bus_id="BUS_99",
                    lat=17.385044,
                    lon=78.486671,
                    timestamp="2026-08-27T12:00:00Z"
                )
                print("Generated JSON Event:")
                print(event_to_json(event))
        else:
            print("Raw Detections List: []")
            print("=> ZERO detections found for this image.")
            
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Total images tested:           {total_images_tested}")
    print(f"Images with at least 1 detect: {images_with_detections}")
    print(f"Total detections found:        {total_detections_found}")
    print("="*50 + "\n")
