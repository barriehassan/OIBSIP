# Task 04 — Desktop GUI completion report

**NOMOLI FORGE — SkyCast · 2 November 2026**

Status: functional CustomTkinter application implemented; user approved committing and pushing Task 04 on 2026-11-02. This report accompanies that publication. Task 05 has not begun.

## Baseline and design authority

Verified `barriehassan/OIBSIP/main` at Task 03 commit `d1f5f3c23c4aff2ff3b01557554141c2d08cdb49`. The available workspace is a verified project source snapshot, not a Git checkout: no local branch/index status exists. No replacement repository was initialized. Read the architecture, asset plan, component inventory, interaction flows and UI specification; inspected the existing models/providers/services. Baseline: **176 passed in 0.25s**. Backend implementation and existing backend tests are retained unchanged. Password Forge, BMI Insight and repository-root files were not modified.

The authoritative Task 04 reference is the newly attached `image(20261102-095116).png` (1400 × 909). Its near-black shell, horizontal cards, blue selected card, rain chart, large lower-left world map and lower-right city cards govern this implementation. Task 02's older reference remains historical documentation. The screenshot itself is neither bundled as artwork nor used as an application background.

## Implemented functionality

| Area | Behavior |
|---|---|
| Window | Rounded near-black CustomTkinter shell; resizable; practical 1024 × 700 minimum; default up to 1440 × 900, clamped to available screen size |
| Search | City, country-qualified city and supported postal queries; Enter/button submission; validation; explicit geographic candidate dialog; cancellation; retry |
| Current conditions | Selected location, current temperature, condition, provider valid time, humidity, wind and feels-like; provider model estimates identified |
| Tabs | Today, Tomorrow and Next 7 Days update selection without HTTP refetches |
| Daily cards | Seven dated slots; blue card expands in its chronological position; daily high/low labels; missing forecasts remain unavailable |
| Hourly detail | Today selects the next six actual future instants; future days start around local 06:00 and page through actual hourly data; gaps/partial coverage are labeled |
| Rain chart | Canvas bars use the same hourly window, on a 0–100% axis; null probability is a gap/“—”; zero has a baseline mark; detail dialog gives exact dates, offsets and values |
| Map | Bundled Natural Earth land raster with correct equirectangular projection; selected/fetched-location pins; active label; clickable markers; working View wide dialog |
| City panel | Up to three explicitly selected session-only cities; Add current city, select, update/retry and remove; independent failures and previous-data notices |
| Metrics | Compact current-condition cards for humidity, wind, feels-like and condition; always explicitly labeled current, even while viewing a future forecast |
| Units | Shared Celsius/Fahrenheit display state; canonical Celsius values preserved; current, daily, hourly, cities and feels-like all update without HTTP |
| Status | Loading, cancelled, ambiguous, unknown, timeout, rate-limit, provider-error and partial-data states; old results retain their identity and download time |
| Keyboard | Enter searches; Tab-focusable action buttons; Enter/Space activation; card arrow navigation retains focus; candidate Up/Down/Enter; Escape cancels; Ctrl+L focuses search; Ctrl+U switches units |
| Entry point | `py -3 main.py`; clear dependency/display initialization errors; Tk 9 receives an actionable compatibility message |

## Architecture and service integration

`app/ui/controller.py` contains a Tk-independent state machine, production backend adapter and bounded worker scheduler. `Backend.search` delegates to Task 03 geocoding. `Backend.weather` uses `WeatherService(OpenMeteoWeather(...))`. Each network task owns and closes its requests session. Widgets consume normalized models, never Open-Meteo JSON.

`app/ui/presentation.py` formats temperatures via Task 03 conversion utilities, selects daily/hourly windows, provides local-time labels, and projects coordinates. `theme.py` centralizes styling, system-font fallbacks and keyboard-operable buttons. `window.py` composes reusable components from `app/ui/components/`: forecast/stat cards, hourly strip, rain Canvas, map Canvas and icon helpers.

A successful combined weather request supplies the whole dashboard. Switching tabs/dates/units never refetches it. Adding the current city reuses its bundle. Selecting an already loaded city reuses explicitly dated session data; Refresh deliberately obtains new data. This is in-memory view state, not a persistent weather cache or favorites system.

Missing backend sections become honest unavailable views. No new current-weather fallback is introduced. DST-adjusted daily extrema retain the Task 03 source description, available in Forecast details. Current humidity/wind are not relabeled as tomorrow's values. Repeated DST wall times are disambiguated by UTC offsets in the text details.

## Threading and lifecycle

Two fixed workers perform network operations. Pending work is keyed by scope and replaced when superseded; at most five scopes can wait (main search/weather, three cities, icons). Duplicate pending main requests are coalesced. Each main request and city update has a generation token. Workers return plain models/images through a queue; an 80 ms Tk poll applies only current results. No worker creates or manipulates Tk widgets or Tk images.

Rate limits defer new network requests until Retry-After (or a 60-second default); queued secondary-city work is cancelled, and late results are rejected. Already running HTTP cannot be forcibly recalled. The UI retains previous successful data with appropriate failure text.

Close cancels Tk polling/redraw callbacks, clears pending jobs, rejects late results and joins workers briefly. Idle workers terminate cleanly. Running requests retain Task 03 connect/read limits; workers are daemon threads so a stuck third-party read cannot prevent process exit. This is bounded UI shutdown, not a claim that Python requests can hard-cancel a socket/DNS operation. There is no persistent data write to corrupt on exit.

## Map and asset strategy

The local map is derived from Natural Earth 1:110m land polygons. The downloaded archive declares **version 4.1.0**; source URL and SHA-256 hashes are recorded in `assets/maps/source.json`. The website's download-page version label differs; the archive's own version is recorded rather than guessed. Natural Earth data is public domain. The map was rasterized and recolored to a 3072 × 1536 image. Build-time `pyshp` is optional and is not a runtime dependency.

The entire 2:1 map is contained within its widget. Pins use that image rectangle: longitude maps left-to-right from −180° to +180°, latitude top-to-bottom from +90° to −90°. This intentionally leaves gutters rather than stretching coordinates. Only the active location and up to three selected city records are shown; overlapping active/city identities are deduplicated. Weather glyphs require an associated retrieved bundle. Failed map loading retains a coordinate/name list. View wide displays an existing-data snapshot and performs no network call. There is no global live weather coverage, radar, tiling, panning, zoom or layers claim.

Official OpenWeather icon IDs from Task 03 map to the documented hosted PNG endpoint. Downloads are asynchronous, HTTPS-only, allowlisted by ID, bounded in size/dimensions/time, and held in memory. No third-party icon files are redistributed. Original Pillow-drawn SkyCast condition illustrations provide immediate/offline fallback, including day/night, rain, thunderstorm, fog, snow and unknown states. Text descriptions always remain available. Image variants are reused rather than decoded on every redraw. Map badges use these original condition illustrations.

Source and license notices appear in About, the visible footer and `assets/ATTRIBUTION.md`. No avatar, notification bell, login, air-quality toggle, promotional satellite image or inert map controls were copied from the reference.

## Validation

**Final result: 240 passed, 0 failed, 0 skipped in 17.49s**, including all 176 Task 03 tests. Final visual review also added an explicit no-clipping regression for Fahrenheit labels in selected and city cards. Command: `python -m pytest -q` from the project directory with the virtual display enabled. The suite includes all 176 backend tests plus controller, pure presentation, assets, entry-point and genuine Tk-widget tests. Normal tests block real HTTP. The widget tests require a display and skip explicitly when no desktop/Xvfb display is available.

Runtime used for final GUI validation: Python 3.12, Tcl/Tk 8.6.14, CustomTkinter 6.0.0, Pillow 13.0.0, Linux virtual display. The default managed Python initially supplied Tk 9.0.4; visual inspection exposed incorrect fonts/corners despite functional widget tests passing. A separate Tk 8.6 runtime fixed rendering. The entry point now rejects Tk 9 with a clear instruction. This is a compatibility restriction, not a backend change.

Checks cover search success/validation/failure/ambiguity, stale responses, cancellation, bounded rapid requests, per-city partial failure, rate-limit deferral, bundle reuse, Today/Tomorrow/day changes, shared units, null/gapped data, rain inputs, exact map projection, asset hash integrity, icon download validation, keyboard operation, close behavior, and 1440 × 900 / 1366 × 768 / 1024 × 700 resizing. A 125% CustomTkinter widget-scale simulation passed; this is **not Windows DPI verification**. Compilation and dependency consistency checks passed.

### Live checks and actual screenshots

Geocoding checks successfully exposed distinct Beijing and Freetown candidates; exploratory captures stopped rather than silently selecting a match. An additional attempt encountered a controlled geocoding timeout. The final capture reused three explicitly verified location records (London/England, Beijing Municipality, Freetown/Western Area) and successfully retrieved fresh forecasts for each. Six official icon images were fetched. It produced five genuine GUI captures from the Linux virtual display. A final limited three-forecast refresh recaptured all five images after the Fahrenheit layout corrections; all delivered screenshots use those real retrieved bundles.

Screenshots supplied:

- `SkyCast_Task04_1440x900.png`: live-data Today view.
- `SkyCast_Task04_1366x768.png`: live-data desktop layout.
- `SkyCast_Task04_1024x700.png`: live-data compact header and scrollable forecast strips.
- `SkyCast_Task04_Map_Stats.png`: live-data scrolled map, three session city cards and current statistics.
- `SkyCast_Task04_Tomorrow_F.png`: live-data Tomorrow view in Fahrenheit, recaptured after the unit-selector and label-width corrections.

These are captured pixels from independently functional widgets, not HTML approximations or painted mockups. Some live captures precede official icon arrival and show the original fallback illustrations; later captures show official graphics. Data download/valid times remain visible. The live panel contains the active London location as one of the three session-pinned cities, as permitted by the same Add current city workflow. No screenshot is claimed to represent Windows.

### Design comparison

Preserved: near-black rounded shell; prominent centered search; restrained text tabs; chronological horizontal daily cards with one expanded pale-blue card; narrow right-hand rain chart; dominant dark map; right-hand stacked city cards; clean weather artwork and light type.

Deliberate differences: meaningful branding and unit/refresh controls replace avatar/theme/air-quality controls; percentage rain axes replace decorative qualitative labels; high/low/current labels replace ambiguous example numbers; the mandatory hourly strip and compact current-statistics row add vertical content. The selected map uses an accurate full-world projection instead of stretching/cropping geography. The white promotional overlay and nonfunctional zoom controls are omitted. System fonts and official/fallback weather icons differ from the reference's unidentified typeface and proprietary illustrations.

At default height, scrolling reveals the complete map and statistics; narrow widths also scroll cards horizontally. This preserves legibility and the map's prominence rather than shrinking all mandatory content into one screenshot. No pixel-perfect or Windows-rendering parity is claimed.

## Windows verification and remaining work

Use Python with Tcl/Tk 8.6 (Python 3.12 is the validated interpreter family). In PowerShell, from `Python-Task4-WeatherApplication/`:

```powershell
py -3 -m pip install -r requirements-dev.txt
py -3 -m pytest -q
py -3 main.py
```

Use the same interpreter for dependency installation and launch. If `py -3` selects a Tk 9 build, explicitly use `py -3.12` or a Python 3.12 virtual environment. There is no batch-file requirement.

Manually verify: search Freetown and choose Western Area; inspect current humidity/wind and six hourly entries; switch Tomorrow/Next 7 Days and select a later card; toggle °F and inspect every temperature view; add up to three selected cities; update/remove/select them; open View wide and Forecast details; interrupt networking and retry; submit rapid searches; close during a request; resize to all three target sizes; test Windows 100%, 125% and 150% display scaling. These Windows checks remain pending.

Known limits: network/provider coverage varies; requests cancellation is cooperative; city choices do not persist; official icon availability may vary; corrected DST daily conditions may be unavailable; map is a geographic overview only; screen-reader behavior is unverified. The application is source-runnable, not a packaged Windows executable.

Task 04 is approved for publication. Local Windows verification remains pending before Task 05. Speech, persistent favorites/cache, dedicated hourly temperature chart, full sunrise/sunset interface and IP-based location remain deferred. No AI recommendations or cloud synchronization were added.


## File inventory

Modified: `README.md`, `requirements.txt`.

Created:

- `app/ui/__init__.py`
- `app/ui/components/__init__.py`
- `app/ui/components/forecast.py`
- `app/ui/components/global_map.py`
- `app/ui/components/rain_chart.py`
- `app/ui/components/weather_icon.py`
- `app/ui/controller.py`
- `app/ui/presentation.py`
- `app/ui/theme.py`
- `app/ui/window.py`
- `assets/ATTRIBUTION.md`
- `assets/maps/source.json`
- `assets/maps/world_land.png`
- `docs/TASK04_COMPLETION_REPORT.md`
- `main.py`
- `screenshots/README.md`
- `screenshots/SkyCast_Task04_1024x700.png`
- `screenshots/SkyCast_Task04_1366x768.png`
- `screenshots/SkyCast_Task04_1440x900.png`
- `screenshots/SkyCast_Task04_Map_Stats.png`
- `screenshots/SkyCast_Task04_Tomorrow_F.png`
- `scripts/build_map.py`
- `scripts/visual_smoke.py`
- `tests/test_main.py`
- `tests/test_ui_assets.py`
- `tests/test_ui_controller.py`
- `tests/test_ui_presentation.py`
- `tests/test_ui_widgets.py`
