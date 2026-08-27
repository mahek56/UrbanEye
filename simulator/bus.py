"""
bus.py — BusSimulator: drives one bus route through the city.

For each waypoint:
  1. Resolves the test image path
  2. Runs EdgeDetector.detect() on it
  3. Formats each detection via format_event()
  4. POSTs to the backend (unless --dry-run)
  5. Sleeps for the configured delay
  6. Prints structured console output throughout

Used by simulate.py — one instance per bus, run in a thread.
"""

import os
import sys
import time
import requests

from event import format_event
from routes import CORROBORATION_COORD


# ── ANSI colours for terminal output ─────────────────────────────────────────
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_GREEN  = "\033[92m"
_YELLOW = "\033[93m"
_RED    = "\033[91m"
_CYAN   = "\033[96m"
_DIM    = "\033[2m"

BUS_COLORS = {
    "BUS_01": "\033[94m",   # blue
    "BUS_02": "\033[95m",   # magenta
}


def _tag(bus_id: str) -> str:
    color = BUS_COLORS.get(bus_id, "")
    return f"{color}{_BOLD}[{bus_id}]{_RESET}"


def _is_corroboration(lat: float, lon: float) -> bool:
    return (lat, lon) == CORROBORATION_COORD


class BusSimulator:
    """
    Simulates one bus driving a route and posting detections to the backend.

    Args:
        bus_id:       "BUS_01" or "BUS_02"
        route:        List of Waypoint(lat, lon, image) namedtuples
        detector:     Loaded EdgeDetector instance (shared across buses)
        images_dir:   Absolute path to edge/data/test/images/
        backend_url:  Full URL for POST, e.g. "http://localhost:8000/events"
        waypoint_delay_s: Seconds to sleep between waypoints
        dry_run:      If True, skip actual HTTP POST (print only)
    """

    def __init__(self, bus_id: str, route: list, detector,
                 images_dir: str, backend_url: str,
                 waypoint_delay_s: float = 3.0,
                 dry_run: bool = False):
        self.bus_id           = bus_id
        self.route            = route
        self.detector         = detector
        self.images_dir       = images_dir
        self.backend_url      = backend_url
        self.waypoint_delay_s = waypoint_delay_s
        self.dry_run          = dry_run
        self.tag              = _tag(bus_id)

    # ── Main run loop ─────────────────────────────────────────────────────────
    def run(self):
        total_wps = len(self.route)
        print(f"\n{self.tag} Starting route — {total_wps} waypoints  "
              f"{_DIM}(delay={self.waypoint_delay_s}s/wp){_RESET}\n")

        for idx, wp in enumerate(self.route, start=1):
            self._process_waypoint(idx, total_wps, wp)
            if idx < total_wps:
                time.sleep(self.waypoint_delay_s)

        print(f"\n{self.tag} {_GREEN}Route complete.{_RESET}\n")

    # ── Single waypoint ───────────────────────────────────────────────────────
    def _process_waypoint(self, idx: int, total: int, wp):
        corroboration_flag = ""
        if _is_corroboration(wp.lat, wp.lon):
            corroboration_flag = f"  {_YELLOW}★ CORROBORATION POINT{_RESET}"

        print(f"{self.tag}  WP {idx}/{total}  "
              f"{_DIM}({wp.lat:.4f}, {wp.lon:.4f}){_RESET}"
              f"{corroboration_flag}")

        # Resolve image path
        image_path = os.path.join(self.images_dir, wp.image)
        if not os.path.exists(image_path):
            print(f"{self.tag}  WP {idx}/{total}  "
                  f"{_RED}✗ Image not found: {wp.image}{_RESET}")
            return

        # Run detection
        print(f"{self.tag}  WP {idx}/{total}  → detecting…  "
              f"{_DIM}{wp.image[:30]}…{_RESET}")

        try:
            detections = self.detector.detect(image_path)
        except Exception as exc:
            print(f"{self.tag}  WP {idx}/{total}  "
                  f"{_RED}✗ Detection error: {exc}{_RESET}")
            return

        if not detections:
            print(f"{self.tag}  WP {idx}/{total}  "
                  f"{_DIM}→ CLEAR — no detections{_RESET}")
            return

        # Process each detection
        for det in detections:
            self._handle_detection(idx, total, wp, det)

    # ── Single detection → format → POST ─────────────────────────────────────
    def _handle_detection(self, idx: int, total: int, wp, detection: dict):
        det_type = detection["type"]
        conf     = detection["confidence"]

        print(f"{self.tag}  WP {idx}/{total}  "
              f"→ {_BOLD}DETECTED:{_RESET} {_CYAN}{det_type}{_RESET}  "
              f"conf={_BOLD}{conf:.3f}{_RESET}")

        event = format_event(
            bus_id         = self.bus_id,
            lat            = wp.lat,
            lon            = wp.lon,
            detection_type = det_type,
            confidence     = conf,
        )

        if self.dry_run:
            print(f"{self.tag}  WP {idx}/{total}  "
                  f"→ {_YELLOW}DRY-RUN{_RESET} — skipping POST  "
                  f"{_DIM}{event}{_RESET}")
            return

        self._post_event(idx, total, event)

    # ── HTTP POST ─────────────────────────────────────────────────────────────
    def _post_event(self, idx: int, total: int, event: dict):
        try:
            resp = requests.post(
                self.backend_url,
                json    = event,
                timeout = 5,
            )
            if resp.status_code in (200, 201, 202):
                print(f"{self.tag}  WP {idx}/{total}  "
                      f"→ {_GREEN}POSTED ✓{_RESET}  "
                      f"(HTTP {resp.status_code})")
            else:
                print(f"{self.tag}  WP {idx}/{total}  "
                      f"→ {_RED}POST failed{_RESET}  "
                      f"(HTTP {resp.status_code})  "
                      f"{_DIM}{resp.text[:120]}{_RESET}")
        except requests.exceptions.ConnectionError:
            print(f"{self.tag}  WP {idx}/{total}  "
                  f"→ {_RED}✗ Cannot connect to backend{_RESET}  "
                  f"{_DIM}({self.backend_url}){_RESET}  "
                  f"— continuing route")
        except requests.exceptions.Timeout:
            print(f"{self.tag}  WP {idx}/{total}  "
                  f"→ {_RED}✗ POST timed out{_RESET}  — continuing route")
        except Exception as exc:
            print(f"{self.tag}  WP {idx}/{total}  "
                  f"→ {_RED}✗ POST error: {exc}{_RESET}  — continuing route")
