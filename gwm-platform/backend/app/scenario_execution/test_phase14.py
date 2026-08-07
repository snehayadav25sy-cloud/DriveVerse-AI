"""
Phase 14 tests — Country behavior
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.country_profiles.models import CountryProfile, TrafficRules, SpeedLimits, DriverBehavior, ResolvedScenario

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_14_1_drive_side_rules():
    india = CountryProfile(id="india", rules=TrafficRules(drive_side="left"))
    usa = CountryProfile(id="usa", rules=TrafficRules(drive_side="right"))
    japan = CountryProfile(id="japan", rules=TrafficRules(drive_side="left"))
    germany = CountryProfile(id="germany", rules=TrafficRules(drive_side="right"))
    dubai = CountryProfile(id="dubai", rules=TrafficRules(drive_side="right"))

    check(india.rules.drive_side == "left", "India drive side")
    check(usa.rules.drive_side == "right", "USA drive side")
    check(japan.rules.drive_side == "left", "Japan drive side")
    check(germany.rules.drive_side == "right", "Germany drive side")
    check(dubai.rules.drive_side == "right", "Dubai drive side")

def test_14_2_behavior_params():
    india = CountryProfile(
        id="india",
        rules=TrafficRules(
            drive_side="left",
            behavior=DriverBehavior(aggressiveness=0.7, horn_frequency=0.3),
        ),
    )
    resolved = ResolvedScenario(
        drive_side=india.rules.drive_side,
        behavior=india.rules.behavior,
    )
    check(resolved.drive_side == "left", "Resolved drive side")
    check(resolved.behavior.aggressiveness == 0.7, "Resolved aggressiveness")
    check(resolved.behavior.horn_frequency == 0.3, "Resolved horn frequency")

def test_14_3_weather_params():
    from app.country_profiles.models import WeatherPreset
    india = CountryProfile(
        id="india",
        weather_presets={
            "rain": WeatherPreset(rain=80.0, cloudiness=90.0),
        },
    )
    check("rain" in india.weather_presets, "Rain preset exists")
    check(india.weather_presets["rain"].rain == 80.0, "Rain intensity")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 14 - Country Behavior Tests")
    print("=" * 65)
    try:
        test_14_1_drive_side_rules()
        test_14_2_behavior_params()
        test_14_3_weather_params()
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
