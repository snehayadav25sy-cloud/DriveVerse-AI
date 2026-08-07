"""
Phase 8 tests — Pedestrian population engine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.world_generation.models import WorldPlan, WorldCoordinate, WorldBoundingBox
from app.world_generation.pedestrians import PedestrianPopulationEngine

PASS, FAIL = "PASS", "FAIL"
results = []

def check(c, d):
    s = PASS if c else FAIL
    results.append((s, d))
    print(f"  [{s}]  {d}")
    if not c: raise AssertionError(f"CHECK FAILED: {d}")

def test_8_1_pedestrian_generation():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    engine = PedestrianPopulationEngine(plan, {}, {})
    peds = engine.generate(density=0.3, time_of_day="noon", weather="sunny")
    check(len(peds) > 0, f"Generated pedestrians: {len(peds)}")

def test_8_2_time_modifier():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    engine = PedestrianPopulationEngine(plan, {}, {})
    noon = engine.generate(density=0.3, time_of_day="noon", weather="sunny")
    night = engine.generate(density=0.3, time_of_day="night", weather="sunny")
    check(len(night) < len(noon), f"Night ({len(night)}) < Noon ({len(noon)})")

def test_8_3_weather_modifier():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    engine = PedestrianPopulationEngine(plan, {}, {})
    sunny = engine.generate(density=0.3, time_of_day="noon", weather="sunny")
    rain = engine.generate(density=0.3, time_of_day="noon", weather="rain")
    check(len(rain) < len(sunny), f"Rain ({len(rain)}) < Sunny ({len(sunny)})")

def test_8_4_walking_speed():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    engine = PedestrianPopulationEngine(plan, {}, {})
    peds = engine.generate(density=0.3)
    for p in peds:
        check(0.5 <= p.walking_speed_ms <= 2.5, f"Walking speed in range: {p.walking_speed_ms}")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 8 - Pedestrian Population Tests")
    print("=" * 65)
    try:
        test_8_1_pedestrian_generation()
        test_8_2_time_modifier()
        test_8_3_weather_modifier()
        test_8_4_walking_speed()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0: sys.exit(1)

