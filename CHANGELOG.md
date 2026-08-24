# Changelog

All notable changes to the DriveVerse AI repository are documented here chronologically.

---

## [Build 1] - Initial CARLA Video Engine
* Implemented core video recorder attaching virtual RGB camera/LiDAR sensors in CARLA.
* Added deterministic scenario presetting for weather presets.

## [Build 2] - Multi-Sensor Synced Recording
* Built `MultiSensorCapture` wrapping synchronous CARLA simulation frame steps.
* Implemented multi-format annotation export (KITTI, YOLO, COCO).

## [Build 3] - Parameterized Country Profiles
* Added `CountryProfileRegistry` reading structured YAML country config profiles.
* Implemented scenario modifiers and weather preset registry support (India baseline).

## [Build 4] - Geo-Spatial OSM Integration
* Implemented road validator, geocoding service, and OpenDRIVE compiler compiling raw OSM roads to XODR maps.

## [Build 5] - Deterministic Event Scheduler
* Wired scenario template generators executing and scheduling timed events.
* Verified 100% byte-for-byte identical output files on matching seeds.

## [Build 6] - Regulator Monitoring Dashboard
* Designed and built React frontend regulator monitoring dashboard with interactive deck.gl map canvases and Recharts analytics.

## [Build 7] - Final Integration & Mauritius Pilot
* **Mauritius Country Profile:** Created `mauritius.yaml` defining tropical weather presets and NLTA vehicle mixes, verified zero India regression.
* **Ebene Cybercity & Pont-Fer Roundabout:** Downloaded OSM, compiled and validated OpenDRIVE maps.
* **Mauritius Scenarios:** Created 5 pilot scenarios including heavy tropical rain and manual safety-operator interventions.
* **Regulator Dashboard Support:** Added 🇮🇳/🇲🇺 selector dropdown, centered geospatial deck.gl canvases, added NLTA mix pie charts and badges.
* **Clean Production Build:** Resolved dynamic imports issue (`import('yaml')`) in frontend, ensuring `npm run build` succeeds cleanly.
