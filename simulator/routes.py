"""
routes.py — Bus route definitions for the UrbanEye simulator.

Each route is a list of Waypoint namedtuples:
    (lat, lon, image_filename)

image_filename is a basename from edge/data/test/images/.
The simulator resolves the full path at runtime.

─── CORROBORATION DESIGN ────────────────────────────────────────────────────
Both buses pass through the EXACT same coordinate at different times:

    CORROBORATION_COORD = (17.4156, 78.4512)   # Banjara Hills Road No. 12

BUS_01 hits it at waypoint 4 (~18s into its run).
BUS_02 hits it at waypoint 2 (~14s into ITS run, which starts 90s later).

Both buses are deliberately fed CORROBORATION_IMAGE at this waypoint — a
photo with a high-confidence pothole — to guarantee a real YOLO detection
from both buses, proving the corroboration mechanism end-to-end in the demo.

All other waypoints cycle through the remaining test images.
─────────────────────────────────────────────────────────────────────────────
"""

from collections import namedtuple

Waypoint = namedtuple("Waypoint", ["lat", "lon", "image"])

# ── Corroboration anchor ─────────────────────────────────────────────────────
# Both buses are sent to this exact point with the same image.
CORROBORATION_COORD = (17.4156, 78.4512)   # Banjara Hills Road No. 12 junction

# High-confidence pothole image — guaranteed detection on both buses
CORROBORATION_IMAGE = "img-43_jpg.rf.a63cf022f8ba7dbadc62c5d274547b79.jpg"

# ── BUS_01 — Hitech City → Banjara Hills ────────────────────────────────────
# Route: Hitech City signal → Madhapur → Jubilee Hills →
#        ⭐ Banjara Hills Rd 12 → Road No. 36 → Peddamma Temple Rd
BUS_01_ROUTE = [
    Waypoint(
        lat=17.4500, lon=78.3750,
        image="img-47_jpg.rf.53aba5861cc3e2c2f7783276288b2b97.jpg",
    ),  # WP1 — Hitech City signal
    Waypoint(
        lat=17.4430, lon=78.3950,
        image="img-72_jpg.rf.02fb39f41fc685d8b616b0751976a8a3.jpg",
    ),  # WP2 — Madhapur junction
    Waypoint(
        lat=17.4320, lon=78.4200,
        image="img-98_jpg.rf.667209472947ff4d519f65c6e206a7c3.jpg",
    ),  # WP3 — Jubilee Hills Check Post
    Waypoint(
        lat=CORROBORATION_COORD[0], lon=CORROBORATION_COORD[1],
        image=CORROBORATION_IMAGE,
    ),  # WP4 ⭐ — Banjara Hills Rd 12 (CORROBORATION POINT)
    Waypoint(
        lat=17.4080, lon=78.4650,
        image="img-79_jpg.rf.3b2198b179f00a052f569a6224172c8a.jpg",
    ),  # WP5 — Road No. 36 signal
    Waypoint(
        lat=17.3980, lon=78.4740,
        image="img-105_jpg.rf.3fe9dff3d1631e79ecb480ff403bcb86.jpg",
    ),  # WP6 — Peddamma Temple Road
]

# ── BUS_02 — Secunderabad → Khairatabad ─────────────────────────────────────
# Route: Secunderabad Clock Tower → ⭐ Banjara Hills Rd 12 →
#        Somajiguda → Punjagutta → Khairatabad
BUS_02_ROUTE = [
    Waypoint(
        lat=17.4401, lon=78.4983,
        image="img-107_jpg.rf.2e40485785f6e5e2efec404301b235c2.jpg",
    ),  # WP1 — Secunderabad Clock Tower
    Waypoint(
        lat=CORROBORATION_COORD[0], lon=CORROBORATION_COORD[1],
        image=CORROBORATION_IMAGE,
    ),  # WP2 ⭐ — Banjara Hills Rd 12 (CORROBORATION POINT)
    Waypoint(
        lat=17.4060, lon=78.4400,
        image="img-161_jpg.rf.211541e7178a4a93ec0680f26b905427.jpg",
    ),  # WP3 — Somajiguda circle
    Waypoint(
        lat=17.3950, lon=78.4620,
        image="img-168_jpg.rf.af3590e07b06b43e91fa53990ff94af3.jpg",
    ),  # WP4 — Punjagutta X-roads
    Waypoint(
        lat=17.3860, lon=78.4720,
        image="img-179_jpg.rf.8632eb0d9b75fefe144829e67b75015a.jpg",
    ),  # WP5 — Khairatabad
]

ALL_ROUTES = {
    "BUS_01": BUS_01_ROUTE,
    "BUS_02": BUS_02_ROUTE,
}
