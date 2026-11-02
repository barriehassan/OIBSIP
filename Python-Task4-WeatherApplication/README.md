# NOMOLI FORGE — SkyCast

*Know the Sky. Plan Your Day.*

SkyCast is a Windows-targeted desktop weather application for Hassan Barrie's Oasis Infobyte Python Programming internship, **Task 4 — Basic Weather App, Advanced Tier**.

## Status

Tasks 01–04 are published to `barriehassan/OIBSIP/main`; the approved Task 04 alignment baseline is `6f9fa9b6744013d22092cd8fcbf491052435547f`. **Task 05 implements all seven approved enhancements and is approved for publication.** Windows speech and native Windows GUI verification remain pending. Task 06 has not started. See the [Task 05 completion report](docs/TASK05_COMPLETION_REPORT.md). A packaged executable is not included.

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

Python 3.11+ (validated on Python 3.12), requests, pytest and tzdata power the backend. CustomTkinter and Pillow power the implemented GUI. Tcl/Tk 8.6 is required; Tk 9 is rejected because visual testing found incompatible rendering. Open-Meteo supplies weather and geocoding; official OpenWeatherMap icon URLs preserve the assignment's icon requirement. Python `zoneinfo` with packaged `tzdata` supports Windows timezone handling. Task 05 uses standard-library SQLite, a reusable Tk Canvas chart, and Windows-only pyttsx3 2.99 with SAPI5. Matplotlib is not required.

## Roadmap

| Task | Deliverable | Status |
|---|---|---|
| 01 | Requirements, API research, architecture | Approved and published |
| 02 | Detailed design using the exact approved mockup | Approved and published |
| 03 | Weather engine and deterministic tests | Published; 176 backend tests retained |
| 04 | Desktop GUI and mandatory functionality | Published; native Windows verification pending |
| 05 | Seven approved enhancements | Implemented; approved for publication |
| 06 | Final QA, Windows validation and submission | Not started |

Enhancements: SkyCast Voice; favorites; rain/feels-like statistics; hourly temperature chart; timestamped cache; sunrise/sunset; opt-in approximate IP location.

## Attribution and use

Attribution: [Weather data by Open-Meteo.com](https://open-meteo.com/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); geocoding by Open-Meteo and [GeoNames](https://www.geonames.org/). Display conversions and formatting will be performed by SkyCast. Icons: OpenWeatherMap, separately credited. Map: Natural Earth, public-domain data. Provider links appear beside weather displays and in About.

The free Open-Meteo service is proposed for an educational, noncommercial submission. NOMOLI FORGE branding does not automatically authorize commercial or promotional use of that service. Reassess the terms before commercial distribution. Hosted weather icons are fetched into memory, not redistributed; the public-domain Natural Earth basemap is bundled with attribution.

## Repository handoff

Tasks 01 and 02 are included in this repository revision. Future work should use the existing OIBSIP working copy after checking its current branch, status, instructions and any newer changes. Do not replace the repository root README or either existing project. This package contains Task 05 source and the prior planning/history files; it is not a second Git repository. See the completion report for the inspected remote revision and verification limits.


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

Open the grid menu (top left) or **Forecast** to expand hourly details, current statistics, °C/°F, Refresh and **Add current city**. Units update all temperatures without a network request. Pin up to three places for this session; click a city to select it, or right-click / Shift+F10 on its name for update/retry and removal. They are not persistent favorites. The map shows only resolved selected/pinned locations, with weather badges only where a bundle exists. View wide expands the same geographic overview, not global live coverage.

The **Full report** action exposes exact values, local UTC offsets, partial coverage, and daily aggregation sources. Loading/errors appear inline, previous weather keeps its location and download time, and Retry/Refresh recover when the provider permits. Task 05 saves validated weather snapshots locally; the retrieval time and cache/offline state remain visible. Ctrl+L focuses search; Ctrl+U switches units; Enter/Space activates buttons; arrow keys navigate candidate/day selections; Escape cancels location selection.

Official OpenWeather icons load asynchronously into memory; original condition illustrations remain usable offline. The Natural Earth basemap is bundled locally. See the [asset notices](assets/ATTRIBUTION.md). The top bar follows the reference order: grid menu, activity bell, location pin and city/country, centered search, light/dark buttons and an S monogram opening About. The bell shows retrieval activity, not weather alerts. Air quality opens an explicit unavailable-data message; no AQI is fabricated. Map controls reset, toggle pins, zoom and recenter on the active location; drag to pan. The map exploration card explains available layers. The extra hourly/statistics panel is collapsed by default.

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

Services are synchronous; the Task 04 controller runs them outside Tk's UI thread, with one session per network task. Reuse the returned bundle for all cards and charts. Task 05 adds a persistent cache around the same normalized bundles.

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

All seven Task 05 enhancements are integrated; their controls and limitations are described below.


## Task 04 validation and limitations

Run `python -m pytest -q` from the project directory, using the interpreter with installed development dependencies. Desktop widget tests need a display; they explicitly skip on headless Linux without DISPLAY. Initial Task 04 validation: **240 passed, 0 failed, 0 skipped in 17.49s** under Linux/Tk 8.6 with a display. Historical details are in [TASK04_COMPLETION_REPORT.md](docs/TASK04_COMPLETION_REPORT.md). The alignment revision passes **244 tests, 0 failed, 0 skipped in 27.23s**; see [the revision report](docs/TASK04_ALIGNMENT_REVISION.md).

The GUI has been executed and visually inspected on Linux with Tk 8.6 at 1440 × 900, 1366 × 768 and 1024 × 700. A 125% widget-scale simulation is also tested. This does not establish Windows DPI or screen-reader compatibility. The follow-up alignment revision is described in [TASK04_ALIGNMENT_REVISION.md](docs/TASK04_ALIGNMENT_REVISION.md). At narrower widths content remains scrollable. The map retains its 2:1 geographic projection but fills its viewport by cropping; markers share the same pan/zoom transform. Official and original fallback icon styles differ from the reference. Worker cancellation cannot forcibly interrupt an already running requests socket; late results are discarded and daemon workers cannot hold process exit indefinitely.

Task 04 results above are historical. Task 05 results are recorded below. AI advice, accounts and cloud synchronization are outside scope.


## Task 05 controls and local data

The compact action row beneath the original top bar contains **Listen to Weather**, **☆ Save**, **Favorites** and **Detect My Location**. Open **Forecast** or the grid menu for the existing detail area, now including the four statistics, sunrise/sunset, hourly temperature chart and **Clear weather cache**. Favorites and location consent open inline and scroll into view.

- **Voice:** On Windows, Listen starts local SAPI5 speech and becomes Stop. It reads the resolved place, condition, temperature, available feels-like/humidity/wind, and the selected temperature unit. Cached readings announce that they are last retrieved conditions and include download time. Search, location/unit changes and window closure stop speech. No microphone, audio file or online speech service is used. Other platforms show Voice unavailable; weather remains usable. Install `requirements.txt` on Windows to install pyttsx3 and its Windows dependencies, including pywin32/comtypes. An installed Windows voice and functioning audio output are required. Native Windows audio has not been verified here.
- **Favorites:** Save stores the current resolved location, not the search text. Favorites survive restart; choose a row to load it or Remove to delete it. Duplicate identities are ignored, while distinct coordinates/countries remain distinct. Up to 50 locations are retained. This is separate from the three session-only city cards.
- **Statistics:** Humidity and wind retain canonical percentage/km/h units. Feels-like follows °C/°F. Rain chance is forecast probability for the explicitly labeled upcoming hour, not rainfall amount or an invented current measurement. Missing values display —.
- **Temperature chart:** Uses the selected six-hour forecast window and existing Previous/Next controls. Labels include local date/hour and UTC offset. Missing temperatures and absent hours break the line; a single sample remains a dot. No extrapolated or zero-filled values are drawn.
- **Sunrise/sunset:** Follow the selected local calendar date and location timezone. Missing or mismatched local-date events remain unavailable; no polar-day/night diagnosis is invented.
- **Cache:** Snapshots less than 20 minutes old can be reused without a weather request; Refresh forces an attempt. On a network failure a valid saved snapshot may be shown as recent or stale cache, with its original retrieval time. Forecast dates never shift to pretend the snapshot is current; expired periods disappear from upcoming selections. Malformed/provider-error responses do not silently become network-offline fallbacks. A successfully fetched newer snapshot replaces the prior one. Clear weather cache leaves favorites and the currently displayed snapshot intact.
- **Approximate location:** Detect My Location first explains the external provider and asks consent. Only Continue makes the HTTPS request; a second confirmation is required before selecting the returned place. VPNs/proxies/mobile networks can produce the wrong city. SkyCast stores no public IP and offers manual search throughout. No automatic startup lookup, paid service or API key is involved.

SQLite is stored at `%APPDATA%/NOMOLI_FORGE/SkyCast/skycast.sqlite3` on Windows, or `$XDG_DATA_HOME/NOMOLI_FORGE/SkyCast/skycast.sqlite3` on Linux (default `~/.local/share`). It contains resolved favorite locations and normalized weather snapshots with provider, timezone, retrieval time and schema metadata. Snapshots are limited to 30 locations, 500 KB per record and a seven-day usable retention period; old rows are pruned on successful writes. Invalid rows/schema or inaccessible storage produce a safe notice without disabling online search. Invalid favorite rows are skipped rather than silently deleting the database. There is no cloud sync. Do not commit the database.

IP location uses [IPWHOIS.IO documentation](https://ipwhois.io/documentation), [pricing](https://ipwhois.io/pricing) and [terms](https://ipwhois.io/terms), checked 2026-11-02. Its advertised free HTTPS endpoint needs no key and allows 1,000 requests/day with standard accuracy and no SLA; commercial use is advertised, subject to service terms. SkyCast makes only explicit current-IP lookups, applies a one-minute cooldown and respects rate-limit retry delays. The provider necessarily sees the requesting public IP. No actual public-IP lookup was performed during cloud validation.

## Task 05 validation

The full Linux/Python 3.12/Tk 8.6 suite passes **307 tests, 0 failures, 0 skips in 40.80 seconds**. The 244 existing tests remain included. Tests prohibit real HTTP; new checks cover storage/restart/corruption, cache policy and recovery, actual-period/unit/timezone projections, chart gaps, consent/errors/stale results, and mocked speech lifecycle. A real spawned-process lifecycle test uses a silent worker, not a speech engine. Actual GUI captures separately use live weather for London, Beijing and Freetown, with a simulated network failure against real saved data. See the [completion report](docs/TASK05_COMPLETION_REPORT.md) and [screenshots](screenshots/README.md).

Windows SAPI5 playback/stop/cleanup, missing voices, native DPI and accessibility still require manual verification. These are explicit release checks, not claimed test passes. Task 06 awaits approval.
