"""
app/scenario_execution/events/event_scheduler.py — Build 7: Deterministic event scheduler

Given the same scenario, world, and seed, the event schedule MUST be identical.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from app.scenario_execution.models import ScenarioEventPlan, EventTrigger, TriggerType, EventType


class EventScheduler:
    """Deterministic event scheduler."""

    _EVENT_TYPE_NORMALIZATION = {
        "lane_closure": "LANE_CLOSURE",
        "construction": "ROAD_CONSTRUCTION",
        "parked_vehicle": "VEHICLE_BRAKING",
        "broken_down_vehicle": "VEHICLE_BRAKING",
        "pedestrian_crossing": "PEDESTRIAN_CROSSING",
        "jaywalking": "JAYWALKING",
        "accident": "ACCIDENT",
        "emergency_vehicle": "EMERGENCY_VEHICLE",
        "sudden_braking": "VEHICLE_BRAKING",
        "lane_blockage": "LANE_CLOSURE",
        "puddle_zone": "PUDDLE_ZONE",
    }

    def __init__(self, master_seed: int = 0, event_seed: int = 0):
        self.master_seed = master_seed
        self.event_seed = event_seed

    def schedule(self, events: List[Dict[str, Any]], total_duration_s: float) -> List[ScenarioEventPlan]:
        """
        Schedule events deterministically.
        """
        rng = random.Random(self.event_seed)
        scheduled: List[ScenarioEventPlan] = []

        for i, event_data in enumerate(events):
            raw_type = event_data.get("event_type", "VEHICLE_BRAKING")
            normalized_type = self._EVENT_TYPE_NORMALIZATION.get(raw_type, raw_type.upper())
            event_type = EventType(normalized_type)
            start_time = event_data.get("start_time_s", rng.uniform(0, total_duration_s))
            duration = event_data.get("duration_s", 10.0)
            priority = event_data.get("priority", 0)
            affected_actors = event_data.get("affected_actor_ids", [])
            action = event_data.get("action", {})
            seed = rng.randint(0, 2**31 - 1)

            trigger_type = TriggerType.TIME_TRIGGER
            if event_data.get("distance_trigger"):
                trigger_type = TriggerType.DISTANCE_TRIGGER
            elif event_data.get("proximity_trigger"):
                trigger_type = TriggerType.PROXIMITY_TRIGGER
            elif event_data.get("random_trigger"):
                trigger_type = TriggerType.RANDOM_TRIGGER

            trigger = EventTrigger(
                trigger_type=trigger_type,
                parameters=event_data.get("trigger_parameters", {}),
            )

            plan = ScenarioEventPlan(
                event_id=event_data.get("event_id", f"event_{i:04d}"),
                event_type=event_type,
                trigger=trigger,
                start_time_s=start_time,
                duration_s=duration,
                priority=priority,
                affected_actor_ids=affected_actors,
                action=action,
                seed=seed,
            )
            scheduled.append(plan)

        scheduled.sort(key=lambda e: (e.start_time_s, e.priority))
        return scheduled

    def reschedule(self, events: List[ScenarioEventPlan], new_event_seed: int) -> List[ScenarioEventPlan]:
        """Reschedule with a different event seed."""
        old_seed = self.event_seed
        self.event_seed = new_event_seed
        result = self.schedule(
            [e.model_dump() for e in events],
            max((e.start_time_s + e.duration_s) for e in events) if events else 30.0,
        )
        self.event_seed = old_seed
        return result
