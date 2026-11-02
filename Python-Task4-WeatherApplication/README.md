# NOMOLI FORGE — SkyCast

*Know the Sky. Plan Your Day.*

SkyCast is a planned Windows desktop weather application for Hassan Barrie's Oasis Infobyte Python Programming internship, **Task 4 — Basic Weather App, Advanced Tier**.

## Status

Task 01 was approved and published to `barriehassan/OIBSIP/main` in commit [4db40b7](https://github.com/barriehassan/OIBSIP/commit/4db40b7a64092b25d24a6d2b42afce8e4afdd05f). Task 02 detailed UI/UX documents use the exact supplied dashboard and are approved for publication. This revision contains the Task 02 design specifications and static wireframe. No application code, executable or passing application tests exist in this package.

The planned application supports city/postal-code search, current conditions, six upcoming hourly forecasts, five upcoming daily forecasts, Celsius/Fahrenheit switching, and GUI error handling. Its approved visual direction is the specified near-black dashboard with horizontal forecast cards, a rain chart, a large global map, and an Other Large Cities panel.

## Planning documents

- [Requirements and acceptance criteria](docs/REQUIREMENTS.md)
- [Architecture and data contracts](docs/ARCHITECTURE.md)
- [API decisions and research sources](docs/API_DECISIONS.md)
- [Approved UI requirements](docs/UI_DESIGN_REQUIREMENTS.md)
- [Testing and Windows verification plan](docs/TEST_PLAN.md)
- [Task 01 historical completion report](docs/TASK01_COMPLETION_REPORT.md)
- [Detailed UI design](docs/UI_DESIGN_SPEC.md)
- [Component inventory](docs/COMPONENT_INVENTORY.md)
- [Interaction flows](docs/INTERACTION_FLOWS.md)
- [Asset plan](docs/ASSET_PLAN.md)
- [UI acceptance checklist](docs/UI_ACCEPTANCE_CHECKLIST.md)
- [Structural wireframe and preview](docs/UI_LAYOUT_WIREFRAME.md)
- [Task 02 completion report](docs/TASK02_COMPLETION_REPORT.md)

## Planned technology

Python 3, CustomTkinter, requests, Pillow, and pytest. Open-Meteo is the proposed weather and geocoding provider; official OpenWeatherMap icon URLs preserve the assignment's icon requirement. Python `zoneinfo` with packaged `tzdata` supports Windows timezone handling. SQLite, pyttsx3, and matplotlib are reserved for the relevant later features; install and pin dependencies only during implementation.

## Roadmap

| Task | Deliverable | Status |
|---|---|---|
| 01 | Requirements, API research, architecture | Approved and published |
| 02 | Detailed design using the exact approved mockup | Approved; reference inspected |
| 03 | Weather engine and deterministic tests | Not started |
| 04 | Desktop GUI and mandatory functionality | Not started |
| 05 | Seven approved enhancements | Not started |
| 06 | Final QA, Windows validation and submission | Not started |

Enhancements: SkyCast Voice; favorites; rain/feels-like statistics; hourly temperature chart; timestamped cache; sunrise/sunset; opt-in approximate IP location.

## Attribution and use

Planned attribution: [Weather data by Open-Meteo.com](https://open-meteo.com/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); geocoding by Open-Meteo and [GeoNames](https://www.geonames.org/). Display conversions and formatting will be performed by SkyCast. Icons: OpenWeatherMap, separately credited. Map: Natural Earth, public-domain data. Keep visible provider links beside weather displays and full notices in the eventual About view.

The free Open-Meteo service is proposed for an educational, noncommercial submission. NOMOLI FORGE branding does not automatically authorize commercial or promotional use of that service. Reassess the terms before commercial distribution. Asset acquisition and icon redistribution permissions remain implementation/release checks; no third-party assets are bundled here.

## Repository handoff

Tasks 01 and 02 are included in this repository revision. Future work should use the existing OIBSIP working copy after checking its current branch, status, instructions and any newer changes. Do not replace the repository root README or either existing project. This package is documentation, not a second Git repository. See the completion report for the inspected remote revision and verification limits.
