"""
exporters/class_mapping_kitti.py — internal taxonomy → KITTI label strings.

DESIGN RULE (enforced):
  This is the ONLY file in the entire codebase where KITTI class name strings
  (e.g. "Car", "Pedestrian") appear. bbox.py, classify.py, and all other
  annotation modules must never reference these strings directly.

  This design means future exporters (COCO, nuScenes) only need to add a
  new class_mapping_<format>.py file. Zero changes elsewhere.
"""

from annotations.class_mapping import (
    CAR, VAN, TRUCK, PEDESTRIAN, CYCLIST, TRAM, MISC, DONTCARE
)

# Internal taxonomy → KITTI exact label strings
INTERNAL_TO_KITTI: dict = {
    CAR:        "Car",
    VAN:        "Van",
    TRUCK:      "Truck",
    PEDESTRIAN: "Pedestrian",
    CYCLIST:    "Cyclist",
    TRAM:       "Tram",
    MISC:       "Misc",
    DONTCARE:   "DontCare",
}


def to_kitti(internal_class: str) -> str:
    """
    Convert an internal taxonomy class string to its KITTI label string.

    Parameters
    ----------
    internal_class : str  One of CAR, VAN, TRUCK, PEDESTRIAN, CYCLIST, TRAM,
                          MISC, DONTCARE.

    Returns
    -------
    str  KITTI label string, or "DontCare" if the class is unrecognised.
    """
    return INTERNAL_TO_KITTI.get(internal_class, "DontCare")
