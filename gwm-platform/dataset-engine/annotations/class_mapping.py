"""
annotations/class_mapping.py — CARLA blueprint ID -> internal taxonomy.

DESIGN RULE (enforced, do not change without team review):
  - This is a static, hand-written, version-controlled mapping table.
  - It is NEVER generated dynamically or inferred at runtime from CARLA's
    blueprint library.
  - It maps CARLA blueprint IDs to our INTERNAL taxonomy ONLY.
  - KITTI class strings (e.g. "Car", "Pedestrian") NEVER appear here.
    They live exclusively in exporters/class_mapping_kitti.py.

Internal taxonomy (fixed — do not add labels without a build review):
    CAR | VAN | TRUCK | PEDESTRIAN | CYCLIST | TRAM | MISC | DONTCARE

Lookup order for a given blueprint_id:
  1. Exact match in CARLA_TO_INTERNAL
  2. Wildcard prefix match (e.g. "walker.pedestrian.*" matches any pedestrian)
  3. Catch-all vehicle.* fallback -> CAR
  4. Default -> DONTCARE (logged as warning)
"""

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal taxonomy constants
# ---------------------------------------------------------------------------
CAR        = "CAR"
VAN        = "VAN"
TRUCK      = "TRUCK"
PEDESTRIAN = "PEDESTRIAN"
CYCLIST    = "CYCLIST"
TRAM       = "TRAM"
MISC       = "MISC"
DONTCARE   = "DONTCARE"

INTERNAL_CLASSES = {CAR, VAN, TRUCK, PEDESTRIAN, CYCLIST, TRAM, MISC, DONTCARE}

# ---------------------------------------------------------------------------
# CARLA blueprint ID -> internal class (exact matches first)
# ---------------------------------------------------------------------------
CARLA_TO_INTERNAL: dict = {
    # ── Cars ──────────────────────────────────────────────────────────────
    "vehicle.tesla.model3":             CAR,
    "vehicle.tesla.cybertruck":         CAR,
    "vehicle.audi.etron":               CAR,
    "vehicle.audi.a2":                  CAR,
    "vehicle.audi.tt":                  CAR,
    "vehicle.ford.mustang":             CAR,
    "vehicle.ford.crown":               CAR,
    "vehicle.bmw.grandtourer":          CAR,
    "vehicle.chevrolet.impala":         CAR,
    "vehicle.citroen.c3":               CAR,
    "vehicle.dodge.charger_2020":       CAR,
    "vehicle.dodge.charger_police":     CAR,
    "vehicle.dodge.charger_police_2020": CAR,
    "vehicle.jeep.wrangler_rubicon":    CAR,
    "vehicle.lincoln.mkz_2017":         CAR,
    "vehicle.lincoln.mkz_2020":         CAR,
    "vehicle.mercedes.coupe":           CAR,
    "vehicle.mercedes.coupe_2020":      CAR,
    "vehicle.mini.cooper_s":            CAR,
    "vehicle.mini.cooper_s_2021":       CAR,
    "vehicle.nissan.micra":             CAR,
    "vehicle.nissan.patrol":            CAR,
    "vehicle.nissan.patrol_2021":       CAR,
    "vehicle.seat.leon":                CAR,
    "vehicle.toyota.prius":             CAR,

    # ── Vans ──────────────────────────────────────────────────────────────
    "vehicle.volkswagen.t2":            VAN,
    "vehicle.volkswagen.t2_2021":       VAN,
    "vehicle.ford.ambulance":           VAN,
    "vehicle.mercedes.sprinter":        VAN,

    # ── Trucks ────────────────────────────────────────────────────────────
    "vehicle.carlamotors.firetruck":    TRUCK,
    "vehicle.carlamotors.carlacola":    TRUCK,
    "vehicle.mitsubishi.fusorosa":      TRUCK,

    # ── Motorcycles / Cyclists ────────────────────────────────────────────
    "vehicle.bh.crossbike":             CYCLIST,
    "vehicle.diamondback.century":      CYCLIST,
    "vehicle.gazelle.omafiets":         CYCLIST,
    "vehicle.harley-davidson.low_rider": MISC,
    "vehicle.kawasaki.ninja":           MISC,
    "vehicle.yamaha.yzf":               MISC,
    "vehicle.vespa.zx125":              MISC,

    # ── Emergency / Special ───────────────────────────────────────────────
    "vehicle.dodge.charger_police":     CAR,
    "vehicle.ford.police":              CAR,

    # (static props — declared via wildcard below, listed here for clarity)
    # "static.prop.*" -> DONTCARE  (see wildcard section)
}

# ---------------------------------------------------------------------------
# Wildcard prefix patterns (checked in ORDER after exact match fails)
# ---------------------------------------------------------------------------
# Format: (prefix_to_match, internal_class)
# Checked top-to-bottom; first match wins.
CARLA_WILDCARD_PATTERNS = [
    ("walker.pedestrian.",  PEDESTRIAN),  # all pedestrian blueprints
    ("static.prop.",        DONTCARE),    # static environment props
    ("static.",             DONTCARE),    # other static actors
    ("traffic.",            DONTCARE),    # traffic signs / lights
    ("vehicle.",            CAR),         # catch-all vehicle fallback
]


def map_blueprint(blueprint_id: str) -> str:
    """
    Return the internal taxonomy class for a CARLA blueprint ID.

    Lookup order:
      1. Exact match in CARLA_TO_INTERNAL
      2. Wildcard prefix in CARLA_WILDCARD_PATTERNS (first match wins)
      3. Default DONTCARE (logged as warning)

    Parameters
    ----------
    blueprint_id : str  e.g. "vehicle.tesla.model3"

    Returns
    -------
    str  One of the internal taxonomy constants.
    """
    bp = blueprint_id.lower().strip()

    # 1. Exact match
    if bp in CARLA_TO_INTERNAL:
        return CARLA_TO_INTERNAL[bp]

    # 2. Wildcard prefix
    for prefix, cls in CARLA_WILDCARD_PATTERNS:
        if bp.startswith(prefix):
            return cls

    # 3. Unknown — default to DONTCARE with a warning
    logger.warning(
        "[class_mapping] Unknown blueprint '%s' -> defaulting to DONTCARE. "
        "Add it to CARLA_TO_INTERNAL in annotations/class_mapping.py.",
        blueprint_id,
    )
    return DONTCARE
