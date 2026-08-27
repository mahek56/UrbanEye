"""
simulate.py — UrbanEye Bus Simulator entry point.

Simulates 2 buses (BUS_01 and BUS_02) driving routes through Hyderabad,
running real YOLO detections on test images, and POSTing events to the
backend's POST /events endpoint.

Usage:
    python simulate.py                    # normal run (3s/waypoint, 90s bus gap)
    python simulate.py --fast             # demo run (1s/waypoint, 10s bus gap)
    python simulate.py --dry-run          # print only, skip HTTP POST
    python simulate.py --fast --dry-run   # both
    python simulate.py --url http://localhost:9000/events  # custom backend URL
    python simulate.py --delay 5          # custom waypoint delay (seconds)
    python simulate.py --bus-gap 120      # custom inter-bus start delay (seconds)
    python simulate.py --help             # show this help

Environment variable override:
    BACKEND_URL=http://host:port/events python simulate.py
"""

import argparse
import os
import sys
import threading
import time

# ── Path setup ────────────────────────────────────────────────────────────────
# Allow imports from both /simulator (sibling modules) and /edge (EdgeDetector)
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT   = os.path.dirname(SCRIPT_DIR)
EDGE_DIR    = os.path.join(REPO_ROOT, "edge")
IMAGES_DIR  = os.path.join(EDGE_DIR, "data", "test", "images")
MODEL_PATH  = os.path.join(
    EDGE_DIR, "runs", "detect", "runs", "detect",
    "urbaneye_model", "weights", "best.pt"
)

# Insert edge dir so we can import EdgeDetector
if EDGE_DIR not in sys.path:
    sys.path.insert(0, EDGE_DIR)

from detect import EdgeDetector   # noqa: E402  (after sys.path insert)
from bus import BusSimulator      # noqa: E402
from routes import BUS_01_ROUTE, BUS_02_ROUTE, CORROBORATION_COORD  # noqa: E402

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_BACKEND_URL    = os.environ.get("BACKEND_URL", "http://localhost:8000/events")
DEFAULT_WAYPOINT_DELAY = 3.0   # seconds between waypoints (normal mode)
DEFAULT_BUS_GAP        = 90    # seconds between BUS_01 start and BUS_02 start
FAST_WAYPOINT_DELAY    = 1.0
FAST_BUS_GAP           = 10

_BOLD  = "\033[1m"
_RESET = "\033[0m"
_GREEN = "\033[92m"
_DIM   = "\033[2m"
_YELLOW = "\033[93m"


# ── Banner ────────────────────────────────────────────────────────────────────
def print_banner(args, waypoint_delay, bus_gap):
    print()
    print("═" * 62)
    print(f"  {_BOLD}UrbanEye Bus Simulator{_RESET}")
    print("  Hyderabad road infrastructure sensing demo")
    print("═" * 62)
    print(f"  Backend URL    : {args.url}")
    print(f"  Model          : {os.path.relpath(MODEL_PATH, REPO_ROOT)}")
    print(f"  Images dir     : {os.path.relpath(IMAGES_DIR, REPO_ROOT)}")
    print(f"  Waypoint delay : {waypoint_delay}s")
    print(f"  Bus start gap  : {bus_gap}s  "
          f"{_DIM}(BUS_02 starts {bus_gap}s after BUS_01){_RESET}")
    print(f"  Dry run        : {'YES — no POSTs will be made' if args.dry_run else 'no'}")
    print(f"  Corroboration  : {_YELLOW}★{_RESET} ({CORROBORATION_COORD[0]}, "
          f"{CORROBORATION_COORD[1]})  Banjara Hills Rd 12")
    print("═" * 62)
    print()


# ── Argument parser ───────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="UrbanEye Bus Simulator — simulates 2 buses POSTing road events.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--fast", action="store_true",
        help=f"Demo mode: {FAST_WAYPOINT_DELAY}s/waypoint, {FAST_BUS_GAP}s bus gap",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print events but skip HTTP POST (safe for testing without backend)",
    )
    parser.add_argument(
        "--url", default=DEFAULT_BACKEND_URL, metavar="URL",
        help=f"Backend POST /events URL (default: {DEFAULT_BACKEND_URL})",
    )
    parser.add_argument(
        "--delay", type=float, default=None, metavar="SECONDS",
        help="Waypoint delay in seconds (overrides --fast default)",
    )
    parser.add_argument(
        "--bus-gap", type=int, default=None, metavar="SECONDS",
        help="Seconds between BUS_01 and BUS_02 starting (overrides --fast default)",
    )
    return parser.parse_args()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    args = parse_args()

    # Resolve timing
    waypoint_delay = args.delay  if args.delay   is not None else (
                     FAST_WAYPOINT_DELAY if args.fast else DEFAULT_WAYPOINT_DELAY)
    bus_gap        = args.bus_gap if args.bus_gap is not None else (
                     FAST_BUS_GAP if args.fast else DEFAULT_BUS_GAP)

    print_banner(args, waypoint_delay, bus_gap)

    # ── Load model (once, shared) ─────────────────────────────────────────────
    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Model weights not found: {MODEL_PATH}")
        print("        Run training first, or check the path in simulate.py.")
        sys.exit(1)

    if not os.path.isdir(IMAGES_DIR):
        print(f"[ERROR] Test images directory not found: {IMAGES_DIR}")
        sys.exit(1)

    print(f"  Loading model… {_DIM}{os.path.relpath(MODEL_PATH, REPO_ROOT)}{_RESET}")
    detector = EdgeDetector(model_path=MODEL_PATH)
    print(f"  {_GREEN}Model loaded.{_RESET}\n")

    # ── Build simulators ──────────────────────────────────────────────────────
    bus01 = BusSimulator(
        bus_id           = "BUS_01",
        route            = BUS_01_ROUTE,
        detector         = detector,
        images_dir       = IMAGES_DIR,
        backend_url      = args.url,
        waypoint_delay_s = waypoint_delay,
        dry_run          = args.dry_run,
    )
    bus02 = BusSimulator(
        bus_id           = "BUS_02",
        route            = BUS_02_ROUTE,
        detector         = detector,
        images_dir       = IMAGES_DIR,
        backend_url      = args.url,
        waypoint_delay_s = waypoint_delay,
        dry_run          = args.dry_run,
    )

    # ── Run BUS_01 in a thread, stagger BUS_02 ───────────────────────────────
    t1 = threading.Thread(target=bus01.run, name="BUS_01", daemon=False)
    t1.start()

    if bus_gap > 0:
        print(f"  {_DIM}BUS_02 starts in {bus_gap}s…{_RESET}")
        time.sleep(bus_gap)

    t2 = threading.Thread(target=bus02.run, name="BUS_02", daemon=False)
    t2.start()

    # Wait for both to finish
    t1.join()
    t2.join()

    print()
    print("═" * 62)
    print(f"  {_GREEN}{_BOLD}Simulation complete.{_RESET}")
    print(f"  Check GET /incidents — corroboration_count should be ≥ 2")
    print(f"  for the incident at {CORROBORATION_COORD}")
    print("═" * 62)
    print()


if __name__ == "__main__":
    main()
