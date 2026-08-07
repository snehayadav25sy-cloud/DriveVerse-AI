"""
Phase 17 tests — Build 4 regression: Country compiler
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.country_profiles.models import CountryProfile, TrafficRules, SpeedLimits, DriverBehavior, ResolvedScenario, RealityScenario

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_17_1_country_profile_schema():
    profile = CountryProfile(
        id="india",
        rules=TrafficRules(drive_side="left", speed_limits=SpeedLimits(highway=120, urban=50, residential=40, school=20), behavior=DriverBehavior(aggressiveness=0.7)),
        vehicle_mix={"sedan": 0.3, "rickshaw": 0.2, "motorcycle": 0.5},
    )
    check(profile.rules.drive_side == "left", "India drive side")
    check(profile.rules.speed_limits.highway == 120, "India highway speed limit")

def test_17_2_resolved_scenario():
    scenario = ResolvedScenario(drive_side="left", difficulty_score=0.8)
    check(scenario.drive_side == "left", "Resolved drive side")
    check(scenario.difficulty_score == 0.8, "Difficulty score")

def test_17_3_reality_scenario():
    reality = RealityScenario(country="usa", weather="rain", traffic="heavy", time_of_day="night")
    check(reality.country == "usa", "Country")
    check(reality.weather == "rain", "Weather")
    check(reality.traffic == "heavy", "Traffic")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 17 - Build 4 Regression Tests")
    print("=" * 65)
    try:
        test_17_1_country_profile_schema()
        test_17_2_resolved_scenario()
        test_17_3_reality_scenario()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0:
            sys.exit(1)
