"""
app/scenario_execution/adapters/carla_adapter.py — Build 7: CARLA simulator adapter

ONLY this module may import CARLA.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from app.scenario_execution.adapters.simulator import SimulatorAdapter
from app.scenario_execution.models import ActorState, ExecutionSession, SensorState

logger = logging.getLogger(__name__)

try:
    import carla as _carla
    _CARLA_AVAILABLE = True
except ImportError:
    _carla = None
    _CARLA_AVAILABLE = False

REQUIRED_CARLA_VERSION = "0.9.16"


class CarlaSimulatorAdapter(SimulatorAdapter):
    """CARLA 0.9.16 simulator adapter."""

    def __init__(self, session: ExecutionSession):
        self.session = session
        self.client = None
        self.world = None
        self._actors: Dict[str, Any] = {}
        self._sensors: Dict[str, Any] = {}
        self._frame = 0
        self._simulation_time = 0.0

    def connect(self) -> bool:
        if not _CARLA_AVAILABLE:
            logger.error("CARLA not available")
            return False
        try:
            self.client = _carla.Client("127.0.0.1", 2000)
            self.client.set_timeout(60.0)
            self.world = self.client.get_world()
            logger.info("[CarlaAdapter] Connected to CARLA")
            return True
        except Exception as e:
            logger.error(f"[CarlaAdapter] Connection failed: {e}")
            return False

    def disconnect(self) -> None:
        self.cleanup()
        self.client = None
        self.world = None
        logger.info("[CarlaAdapter] Disconnected")

    def load_map(self, map_config) -> bool:
        if not _CARLA_AVAILABLE or not self.client:
            return False
        try:
            self.world = self.client.load_world(map_config.map_name)
            logger.info(f"[CarlaAdapter] Loaded map {map_config.map_name}")
            return True
        except Exception as e:
            logger.error(f"[CarlaAdapter] Failed to load map: {e}")
            return False

    def spawn_actor(self, actor_state: ActorState) -> Optional[Any]:
        if not _CARLA_AVAILABLE or not self.world:
            return None
        try:
            bp = self.world.get_blueprint_library().find(actor_state.blueprint_id or "vehicle.tesla.model3")
            transform = _carla.Transform(
                _carla.Location(x=actor_state.position.x, y=actor_state.position.y, z=actor_state.position.z),
                _carla.Rotation(yaw=actor_state.rotation_deg),
            )
            actor = self.world.spawn_actor(bp, transform)
            self._actors[actor_state.actor_id] = actor
            logger.info(f"[CarlaAdapter] Spawned {actor_state.actor_id}")
            return actor
        except Exception as e:
            logger.error(f"[CarlaAdapter] Failed to spawn {actor_state.actor_id}: {e}")
            return None

    def destroy_actor(self, actor_id: str) -> bool:
        actor = self._actors.get(actor_id)
        if actor:
            try:
                if actor.is_alive:
                    actor.destroy()
                del self._actors[actor_id]
                return True
            except Exception as e:
                logger.error(f"[CarlaAdapter] Failed to destroy {actor_id}: {e}")
        return False

    def attach_sensor(self, sensor: SensorState, parent_actor_id: Optional[str] = None) -> Optional[Any]:
        if not _CARLA_AVAILABLE or not self.world:
            return None
        try:
            bp = self.world.get_blueprint_library().find(f"sensor.camera.{sensor.sensor_type}")
            if sensor.resolution:
                bp.set_attribute("image_size_x", str(sensor.resolution[0]))
                bp.set_attribute("image_size_y", str(sensor.resolution[1]))
            if sensor.fov:
                bp.set_attribute("fov", str(sensor.fov))
            transform = _carla.Transform(
                _carla.Location(x=sensor.position.x, y=sensor.position.y, z=sensor.position.z),
                _carla.Rotation(*sensor.rotation),
            )
            parent = self._actors.get(parent_actor_id) if parent_actor_id else None
            sensor_actor = self.world.spawn_actor(bp, transform, attach_to=parent)
            self._sensors[sensor.sensor_id] = sensor_actor
            return sensor_actor
        except Exception as e:
            logger.error(f"[CarlaAdapter] Failed to attach sensor {sensor.sensor_id}: {e}")
            return None

    def apply_weather(self, weather_params: Dict[str, float]) -> None:
        if not _CARLA_AVAILABLE or not self.world:
            return
        try:
            weather = _carla.WeatherParameters(
                cloudiness=float(weather_params.get("cloudiness", 0.0)),
                precipitation=float(weather_params.get("precipitation", 0.0)),
                precipitation_deposits=float(weather_params.get("precipitation_deposits", 0.0)),
                wind_intensity=float(weather_params.get("wind_intensity", 0.0)),
                fog_density=float(weather_params.get("fog_density", 0.0)),
                fog_distance=float(weather_params.get("fog_distance", 100.0)),
                sun_azimuth_angle=float(weather_params.get("sun_azimuth_angle", 0.0)),
                sun_altitude_angle=float(weather_params.get("sun_altitude_angle", 45.0)),
                wetness=float(weather_params.get("wetness", 0.0)),
            )
            self.world.set_weather(weather)
        except Exception as e:
            logger.error(f"[CarlaAdapter] Failed to apply weather: {e}")

    def tick(self) -> int:
        if not _CARLA_AVAILABLE or not self.world:
            return self._frame
        try:
            self.world.tick()
            self._frame += 1
            self._simulation_time += self.session.timing.fixed_delta_seconds
            return self._frame
        except Exception as e:
            logger.error(f"[CarlaAdapter] Tick failed: {e}")
            return self._frame

    def get_world_frame(self) -> int:
        return self._frame

    def get_simulation_time(self) -> float:
        return self._simulation_time

    def health_check(self) -> Dict[str, Any]:
        if not _CARLA_AVAILABLE or not self.client or not self.world:
            return {"connected": False}
        return {
            "connected": True,
            "actor_count": len(self._actors),
            "sensor_count": len(self._sensors),
            "frame": self._frame,
        }

    def cleanup(self) -> None:
        for actor in list(self._actors.values()):
            try:
                if actor.is_alive:
                    actor.destroy()
            except Exception:
                pass
        for sensor in list(self._sensors.values()):
            try:
                if sensor.is_alive:
                    sensor.destroy()
            except Exception:
                pass
        self._actors.clear()
        self._sensors.clear()
        logger.info("[CarlaAdapter] Cleaned up all actors and sensors")
