"""
event.py — Event formatter for the UrbanEye simulator.

Packages a detection result into a POST /events body that exactly matches
the API_Contract.md schema.

Can also be used by the real edge pipeline (edge/detect.py) — just import
format_event from here if you want a single canonical formatter across the
whole system.
"""

from datetime import datetime, timezone


def format_event(bus_id: str, lat: float, lon: float,
                 detection_type: str, confidence: float) -> dict:
    """
    Build a contract-compliant event dict for POST /events.

    Args:
        bus_id:          Bus identifier, e.g. "BUS_01"
        lat:             Latitude of detection location
        lon:             Longitude of detection location
        detection_type:  One of: pothole, road_damage, congestion, obstruction
        confidence:      AI model confidence score in [0.0, 1.0]

    Returns:
        dict with keys: bus_id, lat, lon, timestamp, type, confidence
        matching API_Contract.md § POST /events exactly.
    """
    return {
        "bus_id":     bus_id,
        "lat":        lat,
        "lon":        lon,
        "timestamp":  datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type":       detection_type,
        "confidence": round(confidence, 4),
    }
