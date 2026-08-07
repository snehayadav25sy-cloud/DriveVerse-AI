"""
app/scenario_execution/adapters/simulator.py — Build 7: Abstract simulator adapter

Only adapter modules may import CARLA.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.scenario_execution.models import ExecutionSession, ActorState, SensorState


class SimulatorAdapter(ABC):
    """Abstract simulator adapter interface."""

    @abstractmethod
    def connect(self) -> bool:
        """Connect to simulator."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from simulator."""
        pass

    @abstractmethod
    def load_map(self, map_config) -> bool:
        """Load map."""
        pass

    @abstractmethod
    def spawn_actor(self, actor_state: ActorState) -> Optional[Any]:
        """Spawn an actor. Returns simulator actor handle."""
        pass

    @abstractmethod
    def destroy_actor(self, actor_id: str) -> bool:
        """Destroy an actor."""
        pass

    @abstractmethod
    def attach_sensor(self, sensor: SensorState, parent_actor_id: Optional[str] = None) -> Optional[Any]:
        """Attach a sensor."""
        pass

    @abstractmethod
    def apply_weather(self, weather_params: Dict[str, float]) -> None:
        """Apply weather parameters."""
        pass

    @abstractmethod
    def tick(self) -> int:
        """Advance simulation by one tick. Returns frame number."""
        pass

    @abstractmethod
    def get_world_frame(self) -> int:
        """Get current world frame."""
        pass

    @abstractmethod
    def get_simulation_time(self) -> float:
        """Get current simulation time in seconds."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check simulator health."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup all actors and sensors."""
        pass
