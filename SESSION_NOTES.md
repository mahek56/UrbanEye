# Session Notes

Running log for whoever (human or agent) picks up this repo next. Update after every meaningful chunk of work — don't wait till end of session.

---

## Project Snapshot
UrbanEye — public buses as mobile AI sensors for pothole/road-infra detection.
4-way split: edge/AI, backend, frontend, simulator. Contract = API_CONTRACT.md (don't touch without updating CHANGELOG.md + telling team).

## Owners
- Edge/AI: Mahek
- Backend: teammates (handled separately)
- Frontend: Mahek + teammate
- Simulator: Mahek + teammate

---

## Status by Module

### Edge (DONE)
- YOLOv8s fine-tuned on Roboflow public pothole dataset, retrained on Colab GPU (100 epochs, patience=20, degrees=5.0).
- Metrics: mAP50 ~0.75-0.77, precision ~0.80-0.82, recall ~0.67-0.69 (up from initial yolov8n/10-epoch baseline of 0.72/0.76/0.64).
- Files: `/edge/detect.py`, `/edge/preprocess.py`, `/edge/event.py`, `/edge/train.py`, weights at `/edge/runs/detect/urbaneye_model/weights/best.pt`.
- Verified: output JSON matches API_CONTRACT.md exactly, tested on 5 real test images, all correct.
- Confidence threshold: 0.25 (Ultralytics default), intentionally not raised — don't filter below this downstream, real detections show up as low as ~0.29.

### Frontend (IN PROGRESS)
- Stack: React + Leaflet.
- Design direction locked: "City Ledger" editorial/municipal aesthetic — NOT typical dark AI dashboard. Warm off-white canvas, charcoal linework map, serif/slab headline font + monospace data font, ink-blot-style incident markers (size/opacity = severity) instead of pins, ledger/departure-board style incident list instead of card grid, one warm accent color (rust/terracotta) for severity instead of red-orange-green. Explicitly avoid: dark navy, neon/glow, glassmorphism, gradients, generic Inter/Roboto-only type.
- Currently building against MOCKED /incidents data (5 fake entries matching contract shape) — not waiting on backend.
- `fetchIncidents()` function isolated so its internals can later be swapped to call the real backend endpoint without touching the rest of the app.

### Simulator (NOT STARTED)
- Blocked on: backend's `/events` endpoint needs to be live/confirmed before this is truly useful (can scaffold GPS-route + image-feed logic earlier, but final "send to backend" step needs real endpoint).
- Plan: fake 2+ bus routes walking GPS paths, feeding test images into edge's `detect()`, POSTing resulting events to backend. Deliberately route 2 simulated buses over the same pothole location ~1 min apart to demo multi-bus corroboration live.

### Backend (owned by teammates — not tracked in detail here, check with them)

---

## Key Decisions Log
- MVP detection scope: pothole/road_damage/congestion/obstruction (illegal parking dropped).
- Near-real-time, not continuous real-time streaming.
- GPS: use existing fleet tracker where available, else low-cost module — no unverified "fleet already has GPS" claim.
- Contract fields are locked/law; internal implementation per module is free.

## Open Questions / TODO
- Confirm backend `/events` is live before starting simulator's real integration.
- Frontend: swap mock `fetchIncidents()` for real API call once backend `/incidents` is ready.
- Decide demo city / map center coordinates for frontend + simulator to match.

### Frontend (SCAFFOLDED — mocked data, design confirmed)
- Stack: React + Leaflet (CRA), Stadia Maps/Stamen tiles for the warm paper basemap.
- "City Ledger" design direction confirmed working: ink-blot incident markers 
  (size/color by severity), dark editorial header bar ("UrbanEye // Field Ledger"), 
  monospace ledger-style incident table sorted by severity, coordinates readout, 
  corroboration count shown per row. Distinct from generic dark-AI-dashboard look — goal met.
- Currently running on mocked /incidents data (5 fake entries matching contract shape).
- Known gotcha: CRA doesn't reliably resolve `.jsx` extension — components renamed 
  to `.js` to fix build (`Module not found: Can't resolve './App'` errors otherwise). 
  If scaffolding again, use `.js` extension from the start.
- `fetchIncidents()` isolated as planned — swap its internals for the real 
  `GET /incidents` call once backend is live, rest of app shouldn't need changes.
- Minor polish TODO (non-blocking): make severity-based blot color/opacity 
  contrast more visible between low and high severity incidents.
- Not yet pushed/PR'd — do this next.
