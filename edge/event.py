import json

def create_event(detection, bus_id, lat, lon, timestamp):
    """
    Wraps a detection result into the standard JSON event schema.
    
    Args:
        detection (dict): Detection from EdgeDetector (must have 'type' and 'confidence').
        bus_id (str): The ID of the detecting bus.
        lat (float): Latitude.
        lon (float): Longitude.
        timestamp (str): ISO-8601 timestamp string.
        
    Returns:
        dict: The formatted JSON event as a dictionary.
    """
    event = {
        "bus_id": bus_id,
        "lat": lat,
        "lon": lon,
        "timestamp": timestamp,
        "type": detection.get("type", "road_damage"),
        "confidence": round(detection.get("confidence", 0.0), 4)
    }
    
    # Validating against allowed types (basic validation)
    allowed_types = ["pothole", "road_damage", "congestion", "obstruction"]
    if event["type"] not in allowed_types:
        event["type"] = "road_damage"
        
    return event

def event_to_json(event):
    """Converts the event dictionary to a JSON string."""
    return json.dumps(event, indent=2)
