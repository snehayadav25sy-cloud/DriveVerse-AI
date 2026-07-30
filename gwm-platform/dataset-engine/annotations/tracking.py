"""
annotations/tracking.py — persistent object ID assignment across frames.

Uses CARLA actor IDs as stable keys — they are consistent within a single
simulation run. Maps them to compact sequential track_ids (0, 1, 2, ...) that
are stable across frames and suitable for multi-object tracking metrics.

Design: no CARLA imports. Receives plain dicts.
"""


class ObjectTracker:
    """
    Maintains a mapping from CARLA actor_id → sequential track_id.

    Usage
    -----
        tracker = ObjectTracker()

        # per tick:
        actors_with_track = tracker.assign(actors)

    The assigned track_id is stable across frames for the same actor_id.
    New actor_ids get a new track_id. Actors that disappear are remembered
    (so their IDs are never reused within the same run).
    """

    def __init__(self):
        self._actor_to_track: dict = {}
        self._next_id: int = 0

    def assign(self, actors: list) -> list:
        """
        Add a "track_id" field to each actor dict.

        Parameters
        ----------
        actors : list of dict
            Each dict must have "actor_id" : int (CARLA actor id).

        Returns
        -------
        list of dict
            Same dicts with "track_id" : int added.
        """
        result = []
        for actor in actors:
            actor_id = actor.get("actor_id")
            if actor_id is None:
                # Fallback: treat each unknown actor as new
                track_id = self._next_id
                self._next_id += 1
            elif actor_id in self._actor_to_track:
                track_id = self._actor_to_track[actor_id]
            else:
                track_id = self._next_id
                self._actor_to_track[actor_id] = track_id
                self._next_id += 1

            enriched = dict(actor)
            enriched["track_id"] = track_id
            result.append(enriched)
        return result

    @property
    def num_tracked(self) -> int:
        """Total number of unique actors seen so far."""
        return self._next_id
