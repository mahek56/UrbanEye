
# UrbanEye API Contract

This document defines the data format shared between the AI/Edge module,
Backend, Simulator, and Frontend.

The contract should not be changed without discussing it with the whole team.

---

## 1. POST /events

### Purpose

Used to send a detected urban event from the AI/Edge module
(or Bus Simulator) to the Backend.

### Request Body

```json
{
  "bus_id": "BUS_01",
  "lat": 17.4239,
  "lon": 78.4738,
  "timestamp": "2026-08-26T10:15:00Z",
  "type": "pothole",
  "confidence": 0.87
}
````

### Fields

| Field      | Type   | Required | Description                           |
| ---------- | ------ | -------- | ------------------------------------- |
| bus_id     | string | Yes      | ID of the bus that detected the event |
| lat        | number | Yes      | Latitude of the detected location     |
| lon        | number | Yes      | Longitude of the detected location    |
| timestamp  | string | Yes      | Time at which the event was detected  |
| type       | string | Yes      | Type of urban event                   |
| confidence | number | Yes      | AI confidence score, from 0 to 1      |

### Allowed event types

* `pothole`
* `road_damage`
* `congestion`
* `obstruction`

---

## 2. GET /incidents

### Purpose

Used by the Frontend Dashboard to retrieve verified and processed incidents
from the Backend.

### Response

```json
[
  {
    "incident_id": "abc123",
    "lat": 17.4239,
    "lon": 78.4738,
    "type": "pothole",
    "severity": 8.2,
    "corroboration_count": 2,
    "first_seen": "2026-08-26T10:15:00Z",
    "last_seen": "2026-08-26T10:25:00Z"
  }
]
```

### Fields

| Field               | Type    | Description                                     |
| ------------------- | ------- | ----------------------------------------------- |
| incident_id         | string  | Unique ID of the verified incident              |
| lat                 | number  | Latitude of the incident                        |
| lon                 | number  | Longitude of the incident                       |
| type                | string  | Type of incident                                |
| severity            | number  | Priority/severity score                         |
| corroboration_count | integer | Number of buses that detected the same incident |
| first_seen          | string  | Time when the incident was first detected       |
| last_seen           | string  | Most recent detection time                      |

---

## Overall Flow

AI / Bus Simulator
→ POST /events
→ Backend
→ Database
→ Corroboration / Verification
→ GET /incidents
→ Frontend Dashboard




