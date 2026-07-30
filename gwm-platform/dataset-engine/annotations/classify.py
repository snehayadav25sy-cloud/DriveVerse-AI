"""
annotations/classify.py — apply class_mapping to a list of raw actor dicts.

Design rules:
  - Zero KITTI class strings here. Internal taxonomy constants only.
  - Zero CARLA imports.
  - Receives raw actor data dicts from the CARLA world snapshot.
  - Returns enriched dicts with "internal_class" added.
"""

from .class_mapping import map_blueprint, DONTCARE


def classify_actors(actors: list) -> list:
    """
    Apply CARLA blueprint → internal taxonomy mapping to a list of actors.

    Parameters
    ----------
    actors : list of dict
        Each dict must have at minimum:
          "blueprint_id" : str   e.g. "vehicle.tesla.model3"
        Other keys are passed through unchanged.

    Returns
    -------
    list of dict
        Same dicts with "internal_class" key added (or overwritten).
    """
    classified = []
    for actor in actors:
        bp = actor.get("blueprint_id", "")
        cls = map_blueprint(bp)
        enriched = dict(actor)
        enriched["internal_class"] = cls
        classified.append(enriched)
    return classified


def filter_dontcare(actors: list) -> list:
    """
    Return only actors whose internal_class is NOT DONTCARE.

    Useful for exporters that want to skip background/prop clutter.
    The full set (including DONTCARE) is always written to the internal
    label file first — filtering is an exporter-level concern.
    """
    return [a for a in actors if a.get("internal_class") != DONTCARE]
