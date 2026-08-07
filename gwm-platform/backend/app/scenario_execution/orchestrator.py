"""
app/scenario_execution/orchestrator.py — Build 7: Scenario orchestrator

Transforms WorldPlan into an executable ExecutionSession.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.scenario_execution.models import (
    ActorState,
    ExecutionSession,
    MapConfig,
    ScenarioEventPlan,
    SensorState,
    TimingConfig,
    VehicleActorState,
    PedestrianActorState,
)
from app.scenario_execution.session import create_execution_session
from app.scenario_execution.state_machine import ExecutionStateMachine
from app.scenario_execution.preflight import PreflightValidator
from app.scenario_execution.events.event_scheduler import EventScheduler
from app.scenario_execution.provenance.execution_provenance import compute_execution_provenance


class ScenarioOrchestrator:
    """Orchestrates scenario execution."""

    def __init__(self):
        self.state_machine: Optional[ExecutionStateMachine] = None

    def create_session(
        self,
        world_plan: Any,
        resolved_scenario: Dict[str, Any],
        seeds: Optional[Dict[str, int]] = None,
    ) -> ExecutionSession:
        """Create an ExecutionSession from a WorldPlan."""
        session = create_execution_session(
            scenario_id=resolved_scenario.get("scenario_id"),
            world_plan_id=world_plan.world_id if hasattr(world_plan, "world_id") else None,
            resolved_scenario=resolved_scenario,
            world_plan=world_plan,
            seeds=seeds,
        )
        self.state_machine = ExecutionStateMachine(session.status)
        return session

    def prepare_session(self, session: ExecutionSession, world_plan: Any) -> ExecutionSession:
        """Prepare session for execution by populating actors, sensors, and events."""
        session.actors = self._plan_actors(world_plan)
        session.sensors = self._plan_sensors(world_plan)
        session.events = self._plan_events(world_plan, session)
        return session

    def validate_session(self, session: ExecutionSession) -> Any:
        """Run preflight validation."""
        validator = PreflightValidator(session)
        report = validator.validate()
        session.warnings = report.warnings
        if not report.passed:
            session.errors.append({
                "code": "preflight_failed",
                "message": "; ".join(report.errors),
                "phase": "preflight",
                "recoverable": False,
                "details": {"checks": [c.model_dump() for c in report.checks]},
            })
        return report

    def build_execution_provenance(self, session: ExecutionSession, resolved_scenario: Dict[str, Any], world_plan: Any) -> Any:
        """Build execution provenance."""
        return compute_execution_provenance(session, resolved_scenario, world_plan)

    def _plan_actors(self, world_plan: Any) -> list:
        actors = []
        for v in getattr(world_plan, "vehicles", []):
            actors.append(VehicleActorState(
                actor_id=v.vehicle_id,
                semantic_class=v.semantic_type,
                blueprint_id=v.blueprint_id,
                position=v.position,
                rotation_deg=v.rotation_deg,
                speed_ms=v.speed_ms,
                is_ego=v.is_ego,
                is_parked=v.is_parked,
                target_speed_ms=v.speed_ms or 10.0,
            ))
        for p in getattr(world_plan, "pedestrians", []):
            actors.append(PedestrianActorState(
                actor_id=p.pedestrian_id,
                semantic_class="pedestrian",
                position=p.position,
                rotation_deg=p.rotation_deg,
                walking_speed_ms=p.walking_speed_ms,
                destination=p.destination,
                crossing_probability=p.crossing_probability,
                spawn_zone=p.spawn_zone,
            ))
        return actors

    def _plan_sensors(self, world_plan: Any) -> list:
        sensors = []
        for s in getattr(world_plan, "sensors", []):
            sensors.append(SensorState(
                sensor_id=s.sensor_id,
                sensor_type=s.sensor_type,
                position=s.position,
                rotation=s.rotation,
                resolution=s.resolution,
                fov=s.fov,
                frequency_hz=1.0 / s.sensor_tick if s.sensor_tick > 0 else 10.0,
                calibration={
                    "intrinsic": s.intrinsic,
                    "extrinsic": s.extrinsic,
                },
            ))
        return sensors

    def _plan_events(self, world_plan: Any, session: ExecutionSession) -> list:
        events = []
        event_seed = session.seeds.get("event_seed", 45)
        scheduler = EventScheduler(master_seed=session.seeds.get("master_seed", 42), event_seed=event_seed)
        raw_events = []
        for i, e in enumerate(getattr(world_plan, "events", [])):
            raw_events.append({
                "event_id": e.event_id,
                "event_type": e.event_type,
                "start_time_s": float(i) * 5.0,
                "duration_s": e.duration_s,
                "priority": int(e.severity * 10),
                "affected_actor_ids": [],
                "action": e.metadata,
                "seed": event_seed + i,
            })
        total_duration = session.timing.total_simulation_seconds
        events = scheduler.schedule(raw_events, total_duration)
        return events
