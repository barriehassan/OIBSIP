# NOMOLI FORGE — SkyCast

*Know the Sky. Plan Your Day.*

SkyCast is a Windows-targeted desktop weather application for Hassan Barrie's Oasis Infobyte Python Programming internship, **Task 4 — Basic Weather App, Advanced Tier**.

## Status

Task 01 and Task 02 are published to `barriehassan/OIBSIP/main`. Task 02 baseline: `b253cc0d4f62a8239a39214245d2519f74d4b91a`. **Task 03 is published in commit `d1f5f3c`. Task 04 is implemented and approved for publication.** A functional CustomTkinter GUI is included; a packaged executable is not yet available. See the [Task 03 technical completion report](docs/TASK03_COMPLETION_REPORT.md).

The application supports city/postal-code search, current conditions, six upcoming hourly forecasts, seven dated daily forecast slots, Celsius/Fahrenheit switching, and GUI error handling. Its approved visual direction is the specified near-black dashboard with horizontal forecast cards, a rain chart, a large global map, and an Other Large Cities panel.

## Project documents

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
- [Task 04 completion report and Windows checklist](docs/TASK04_COMPLETION_REPORT.md)
- [Asset attribution](assets/ATTRIBUTION.md)
- [Actual Linux GUI screenshots](screenshots/README.md)

## Technology

Python 3.11+ (validated on Python 3.12), requests, pytest and tzdata power the backend. CustomTkinter and Pillow power the implemented GUI. Tcl/Tk 8.6 is required; Tk 9 is rejected because visual testing found incompatible rendering. Open-Meteo supplies weather and geocoding; official OpenWeatherMap icon URLs preserve the assignment's icon requirement. Python `zoneinfo` with packaged `tzdata` supports Windows timezone handling. SQLite, pyttsx3, and matplotlib are reserved for the relevant later features; only current backend dependencies are included in requirements files.

## Roadmap

| Task | Deliverable | Status |
|---|---|---|
| 01 | Requirements, API research, architecture | Approved and published |
| 02 | Detailed design using the exact approved mockup | Approved and published |
| 03 | Weather engine and deterministic tests | Published; 176 backend tests retained |
| 04 | Desktop GUI and mandatory functionality | Implemented; approved for publication; Windows verification pending |
| 05 | Seven approved enhancements | Not started |
| 06 | Final QA, Windows validation and submission | Not started |

Enhancements: SkyCast Voice; favorites; rain/feels-like statistics; hourly temperature chart; timestamped cache; sunrise/sunset; opt-in approximate IP location.

## Attribution and use

Planned attribution: [Weather data by Open-Meteo.com](https://open-meteo.com/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); geocoding by Open-Meteo and [GeoNames](https://www.geonames.org/). Display conversions and formatting will be performed by SkyCast. Icons: OpenWeatherMap, separately credited. Map: Natural Earth, public-domain data. Keep visible provider links beside weather displays and full notices in the eventual About view.

The free Open-Meteo service is proposed for an educational, noncommercial submission. NOMOLI FORGE branding does not automatically authorize commercial or promotional use of that service. Reassess the terms before commercial distribution. Asset acquisition and icon redistribution permissions remain implementation/release checks; no third-party assets are bundled here.

## Repository handoff

Tasks 01 and 02 are included in this repository revision. Future work should use the existing OIBSIP working copy after checking its current branch, status, instructions and any newer changes. Do not replace the repository root README or either existing project. This package contains the Task 03 source and prior planning files; it is not a second Git repository. See the completion report for the inspected remote revision and verification limits.


## Launch the desktop app

Use **Python 3.12 with Tcl/Tk 8.6** for the validated runtime configuration. From the project directory in PowerShell:

```powershell
py -3 -m pip install -r requirements.txt
py -3 main.py
```

The same interpreter must install dependencies and launch the app. If your default `py -3` uses Tk 9, use `py -3.12` instead. Optional isolated setup:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python main.py
```

No batch script is required. Assets resolve relative to the application source, not the current working directory. Linux requires a working desktop display (or Xvfb for tests) and Tk 8.6. Windows execution is still pending verification.

Search a city/country or supported postal code, then choose the correct geographic candidate if prompted. Today shows current conditions and the next six actual hourly forecasts. Tomorrow and date cards select a local calendar day, with Previous/Next hourly windows. The pale-blue card expands in place. Daily values are labeled high/low; current values are labeled separately.

Use °C/°F to update all temperatures without a network request. Scroll to the compact current-statistics row and use **Add current city** to pin up to three places for this session; city cards support selection, update/retry and removal. They are not persistent favorites. The map shows only resolved selected/pinned locations, with weather badges only where a bundle exists. View wide expands the same geographic overview, not global live coverage.

Forecast details exposes exact values, local UTC offsets, partial coverage, and daily aggregation sources. Loading/errors appear inline, previous weather keeps its location and download time, and Retry/Refresh recover when the provider permits. No weather cache is saved to disk. Ctrl+L focuses search; Ctrl+U switches units; Enter/Space activates buttons; arrow keys navigate candidate/day selections; Escape cancels location selection.

Official OpenWeather icons load asynchronously into memory; original condition illustrations remain usable offline. The Natural Earth basemap is bundled locally. See the [asset notices](assets/ATTRIBUTION.md). The GUI preserves the selected dark dashboard composition; extra required hourly/statistics content is reached by scrolling at smaller heights.

## Backend setup and testing

From `Python-Task4-WeatherApplication/` on Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest -q
```

On Linux/macOS use `python3 -m venv .venv`, then `.venv/bin/python` for the same commands. Python 3.11+ is required. `requirements.txt` contains runtime dependencies; `requirements-dev.txt` adds pytest. Tests prohibit real HTTP and use injected clocks. Task 03 historical result: **176 passed in 0.55s**; bytecode compilation and dependency consistency also passed. A limited two-request live smoke test succeeded on 2026-11-02. Windows execution remains to be verified.

```python
from app.providers.geocoding import OpenMeteoGeocoding
from app.providers.open_meteo import OpenMeteoWeather
from app.services.location_service import LocationService
from app.services.weather_service import WeatherService

locations = LocationService(OpenMeteoGeocoding())
candidates = locations.search_locations("London", "GB")
# Present every candidate; the user must choose a resolved Location.
# selected_location = ...
weather = WeatherService(OpenMeteoWeather())
# bundle = weather.get_weather(selected_location)  # one combined API call
# current = weather.get_current_weather(bundle)
# six_hours = weather.get_hourly_forecast(bundle)
# seven_days = weather.get_daily_forecast(bundle)
# rain_points = weather.get_rain_chart(bundle)
```

`resolve_unique` raises `AmbiguousLocationError` rather than selecting the first match. No-results searches raise `LocationNotFoundError`. City/country strings and supported postal codes are passed to the provider without inventing metadata. Two-character queries are allowed for exact matching; shorter queries are rejected. Coverage is not universal.

Services are synchronous; the Task 04 controller runs them outside Tk's UI thread, with one session per network task. Reuse the returned bundle for all cards and charts. This is explicit data reuse, not a weather cache.

## Data contracts

- Endpoints: `https://geocoding-api.open-meteo.com/v1/search` and `https://api.open-meteo.com/v1/forecast`.
- Current: temperature, relative humidity, apparent temperature, WMO code, wind speed, day/night flag.
- Hourly: temperature, WMO code, precipitation probability, day/night flag (for correct icon identifiers).
- Daily: WMO code, maximum/minimum temperature, sunrise, sunset, maximum precipitation probability.
- Requests use seven days, `timezone=auto`, Unix timestamps and Celsius/kmh/mm canonical units. Missing optional values are `None`, never zero-filled.
- Frozen `Location`, `CurrentWeather`, `HourlyForecast`, `DailyForecast`, `WeatherBundle` models isolate the GUI from provider JSON. Description/category/icon identifiers are computed properties. Celsius/Fahrenheit helpers preserve internal precision; display rounding belongs to the GUI.
- Timestamps are UTC instants; convert with `ZoneInfo(bundle.timezone)` for display. `tzdata` supports Windows. Six-hour selection is strictly after the injected current instant and retains gaps and partial status.
- Seven-day selection returns dated slots for Today through Today + 6; missing days remain `None`. Fixed-offset provider daily labels are retained correctly. DST-affected local-day extrema are derived only from complete hourly samples and labeled accordingly; incomplete extrema and unsupported corrected condition aggregates remain unavailable.
- Rain points retain percentages and timestamps; the hourly selection supplies completeness/gap metadata. Map markers expose resolved coordinates and associated current weather or a safe failure message. Multi-city requests are explicit, sequential, limited to ten inputs, and deduplicated within each batch.

The Task 04 GUI, local map and feels-like display are implemented. Speech, persistent favorites, persistent caching, IP location, the dedicated hourly temperature chart and full sunrise/sunset interface remain pending for Task 05.


## Task 04 validation and limitations

Run `python -m pytest -q` from the project directory, using the interpreter with installed development dependencies. Desktop widget tests need a display; they explicitly skip on headless Linux without DISPLAY. Final validation: **240 passed, 0 failed, 0 skipped in 17.49s** under Linux/Tk 8.6 with a display. Further details and live-check status are in [TASK04_COMPLETION_REPORT.md](docs/TASK04_COMPLETION_REPORT.md).

The GUI has been executed and visually inspected on Linux with Tk 8.6 at 1440 × 900, 1366 × 768 and 1024 × 700. A 125% widget-scale simulation is also tested. This does not establish Windows DPI or screen-reader compatibility. Full map/statistics content scrolls vertically, with horizontal card/hour strips at narrow widths. The map retains its 2:1 projection and may have gutters. Official and original fallback icon styles differ from the reference. Worker cancellation cannot forcibly interrupt an already running requests socket; late results are discarded and daemon workers cannot hold process exit indefinitely.

Task 05 remains unstarted. No speech, persistent favorites/weather database, IP geolocation, dedicated temperature trend, AI advice or cloud synchronization is included.
