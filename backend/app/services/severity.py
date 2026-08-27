"""
app/services/severity.py – Type weights, severity formula, and 0-10 normalisation.

ASSUMPTION: Type weights are not specified by the API contract or build plan.
They are configurable via the TYPE_WEIGHTS environment variable.

Formula:
    raw_severity = type_weight × mean_confidence × ln(corroboration_count + 1)
    severity     = min(10.0, raw_severity × (10.0 / SEVERITY_SCALE))
"""
from __future__ import annotations

import math

from app.config import get_settings

# ── Default type weights (assumption – must be approved by team) ─────────────
# Rationale:
#   pothole     8.0 – immediate vehicle / safety damage
#   road_damage 7.0 – structural risk, slightly broader category
#   obstruction 6.0 – situational hazard, depends on context
#   congestion  5.0 – traffic flow impact only, no physical danger
DEFAULT_TYPE_WEIGHTS: dict[str, float] = {
    "pothole": 8.0,
    "road_damage": 7.0,
    "obstruction": 6.0,
    "congestion": 5.0,
}


def _get_type_weight(event_type: str) -> float:
    """Return the weight for an event type.

    Uses TYPE_WEIGHTS from settings; falls back to 5.0 for unknown types.
    """
    settings = get_settings()
    weights = settings.type_weights_dict
    return weights.get(event_type, 5.0)


def compute_severity(
    event_type: str,
    mean_confidence: float,
    corroboration_count: int,
) -> float:
    """Compute a normalised severity score in the range [0.0, 10.0].

    Args:
        event_type:          The incident type string (e.g. "pothole").
        mean_confidence:     Running arithmetic mean of all event confidences.
        corroboration_count: Number of distinct buses that reported this incident.

    Returns:
        Severity score clipped to [0.0, 10.0].
    """
    settings = get_settings()

    type_weight = _get_type_weight(event_type)
    raw = type_weight * mean_confidence * math.log(corroboration_count + 1)
    normalised = raw * (10.0 / settings.SEVERITY_SCALE)
    return min(10.0, max(0.0, normalised))
