"""
app/scenario_execution/actors/actor_manager.py — Build 7: Abstract actor manager

Responsibilities:
  - spawn
  - configure
  - track
  - update
  - destroy
  - health-check
  - recover
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.scenario_execution.models import ActorState, ActorStatus, ActorType

logger = logging.getLogger(__name__)


class ActorManager:
    """Abstract actor manager for simulator-agnostic actor lifecycle."""

    def __init__(self):
        self._actors: Dict[str, ActorState] = {}
        self._simulator_actors: Dict[str, Any] = {}

    def spawn(self, actor_state: ActorState) -> bool:
        """Spawn an actor. Returns True on success."""
        self._actors[actor_state.actor_id] = actor_state
        logger.info(f"[ActorManager] Spawned {actor_state.actor_id} ({actor_state.actor_type.value})")
        return True

    def destroy(self, actor_id: str) -> bool:
        """Destroy an actor. Returns True on success."""
        if actor_id in self._actors:
            self._actors[actor_id].status = ActorStatus.DESTROYED
            logger.info(f"[ActorManager] Destroyed {actor_id}")
            return True
        return False

    def get_state(self, actor_id: str) -> Optional[ActorState]:
        """Get actor state by ID."""
        return self._actors.get(actor_id)

    def get_all_actors(self) -> List[ActorState]:
        """Get all managed actors."""
        return list(self._actors.values())

    def get_actors_by_type(self, actor_type: ActorType) -> List[ActorState]:
        """Get actors filtered by type."""
        return [a for a in self._actors.values() if a.actor_type == actor_type]

    def update(self, simulation_time_s: float) -> None:
        """Update all actors for the current simulation tick."""
        for actor in self._actors.values():
            if actor.status == ActorStatus.ACTIVE:
                self._update_actor(actor, simulation_time_s)

    def _update_actor(self, actor: ActorState, simulation_time_s: float) -> None:
        """Override in subclass for simulator-specific updates."""
        pass

    def health_check(self) -> Dict[str, bool]:
        """Check health of all actors."""
        return {actor_id: actor.status != ActorStatus.FAILED for actor_id, actor in self._actors.items()}

    def cleanup(self) -> None:
        """Destroy all actors."""
        for actor_id in list(self._actors.keys()):
            self.destroy(actor_id)
        self._simulator_actors.clear()

    def count(self) -> int:
        """Return count of non-destroyed actors."""
        return sum(1 for a in self._actors.values() if a.status != ActorStatus.DESTROYED)
