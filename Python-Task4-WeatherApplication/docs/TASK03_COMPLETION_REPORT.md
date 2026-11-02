# Task 03 — Weather backend completion report

Date: 2026-11-02. Status: implemented, validated and approved for commit/push following review. Task 04 has not begun. The original review package was uncommitted; this repository revision incorporates the subsequent publication approval.

## Repository inspection and scope

Verified remote `barriehassan/OIBSIP/main` at `b253cc0d4f62a8239a39214245d2519f74d4b91a` (published Task 02). Inspected the remote tree and Task 01/02 requirements, architecture, API and UI documents. No SkyCast application modules, tests or applicable AGENTS.md existed in that revision. The 16 local baseline project files matched the published Git blobs before implementation.

The available workspace is a source snapshot, not a Git working tree: there is no local branch/index status to report. No replacement repository was initialized. Changes are isolated to the `Python-Task4-WeatherApplication/` snapshot. Password Forge, BMI Insight and the repository root were not modified. Before a later approved commit, recheck remote main and apply these files to the existing repository, preserving intervening changes.

## Implemented behavior and architecture

`app/core` owns immutable models, validation, safe exceptions, temperature conversion, condition interpretation and forecast selection. `app/providers` owns provider protocols, HTTPS transport, geocoding and Open-Meteo normalization. `app/services` coordinates location selection, combined weather retrieval, explicit bundle reuse, multi-location results and map markers. Tests use injected clients/sessions and clocks; no GUI dependencies are introduced.

The public integration is `LocationService(OpenMeteoGeocoding())` and `WeatherService(OpenMeteoWeather())`. `get_weather(location)` fetches a combined bundle. Current/hourly/daily/rain accessors accept that bundle to avoid repeated API requests. `get_many` accepts resolved locations, deduplicates repeated selections inside that call, preserves input order and isolates expected failures. It is sequential and accepts at most ten input locations. On a rate-limit response it marks remaining uncached batch results as deferred without additional calls. Callers must respect `retry_after_seconds` before starting another batch.

A `LocationWeatherResult` retains requested location, optional bundle and optional controlled exception. `MapMarker` retains location/coordinates, current temperature, icon ID, observation timestamp and optional safe error message. No global dataset, fake city weather or map renderer is included.

### Endpoints and fields

Geocoding: `https://geocoding-api.open-meteo.com/v1/search`, with normalized `name`, optional ISO `countryCode`, count 10, English results and JSON format. Unicode city names, comma-qualified city/country strings and supported postal codes retain their meaning. Postal leading zeros are preserved. Empty, single-character, control-character and overlong queries are rejected before HTTP. Two-character queries are allowed. Unknown locations are distinct from network failure. Multiple plausible matches are returned as candidates; `resolve_unique` explicitly raises ambiguity. Region may be absent; required missing metadata invalidates the response rather than being fabricated. Search results are limited to ten; callers should refine ambiguous searches.

Forecast: `https://api.open-meteo.com/v1/forecast` with validated coordinates, `timezone=auto`, `timeformat=unixtime`, `forecast_days=7`, `temperature_unit=celsius`, `wind_speed_unit=kmh`, `precipitation_unit=mm`.

| Section | Variables |
|---|---|
| current | temperature_2m, relative_humidity_2m, apparent_temperature, weather_code, wind_speed_10m, is_day |
| hourly | temperature_2m, weather_code, precipitation_probability, is_day |
| daily | weather_code, temperature_2m_max, temperature_2m_min, sunrise, sunset, precipitation_probability_max |

Current conditions require all six values plus an observation time and matching units. Finite numbers, humidity/probability bounds, nonnegative wind, coordinate bounds, strict integer condition codes and valid day/night flags are checked. Unknown WMO codes are accepted with an unknown interpretation. Current conditions never fall back to unrelated forecast entries. Open-Meteo current conditions are model estimates, not a claim of station observations.

Optional forecast values remain `None`; absent forecast sections yield empty tuples and bundle warnings. Invalid structures, unequal parallel arrays, wrong units and conflicting duplicate timestamps fail with `WeatherDataError`. Identical duplicates are deduplicated and entries sorted. Description, category and icon identifier are computed model properties. Frozen dataclasses and tuple collections prevent accidental cross-card mutation.

### Time and forecast behavior

All weather times are parsed as aware UTC instants. Display conversion uses the provider-returned IANA timezone, including fractional offsets and repeated DST wall-clock hours. `tzdata` is an explicit Windows dependency. No machine-local timezone is assumed. Retrieval and selection clocks can be injected independently.

The six-hour engine sorts actual UTC instants, excludes times at or before now, and returns up to six upcoming entries. At 14:00 and 14:20, the first standard hourly slot is 15:00. Midnight and DST transitions preserve absolute order. Gaps are listed as `gap_after`; missing temperature/code, a late first slot, gaps or fewer than six entries make `complete=False`. Three-hourly data is never claimed to be consecutive hourly data. No upcoming entries raise `ForecastUnavailableError`. Missing probability is independent of core forecast completeness and remains a null rain point; Task 04 must render that as unavailable rather than a zero bar.

Daily selection returns seven dates and seven corresponding optional entries: the selected location's Today through Today + 6. Missing slots are not shifted or synthesized. Seven available entries satisfy the minimum five upcoming daily forecasts. Completely absent relevant daily data raises `ForecastUnavailableError`; partial coverage returns `complete=False`.

Open-Meteo Unix daily labels use its reported fixed UTC offset. That offset is retained on each daily model; labels do not accidentally shift to the preceding date after DST. If the provider's period does not match a local day's IANA boundaries, extrema are recalculated only when every hourly temperature for that 23-, 24- or 25-hour day is available. These are explicitly labeled `hourly-derived local day`, not exact provider daily extrema. Corrected condition and maximum-probability aggregates remain unavailable because no undocumented aggregation rule is invented. Incomplete local-day sampling leaves extrema unavailable. Original sunrise/sunset instants remain identifiable as provider fields. Daily `complete` requires high, low and condition for every slot.

Task 03 follows the supplied seven-day request, superseding Task 01's proposed nine-day plus past-day buffer for this stage. Consequently a DST boundary or the final forecast day may lack enough hourly coverage; partial status is intentional. A later approved design can request a buffer if required.

### Units, interpretation and chart data

Canonical values remain Celsius, km/h and percent. Pure Celsius/Fahrenheit utilities validate finite inputs and preserve full floating-point precision; repeated toggles should convert from the canonical Celsius value, never from previously rounded display values.

All documented WMO codes map to granular English descriptions, categories and OpenWeatherMap-style identifiers: clear 01, mainly clear 02, partly cloudy 03, overcast 04, fog 50, drizzle/showers 09, rain 10, snow 13 and thunderstorms 11, with day/night suffixes where solar state is known. Freezing precipitation retains its own category/description. Unknown codes and unknown solar state have safe icon fallbacks. Daily icons use a daytime summary convention. No graphical assets are downloaded or redistributed.

Rain chart points contain the original UTC time and precipitation probability (0–100 or None), not rainfall amount. The future UI should retain the paired hourly selection's gap/completeness information.

### Errors and transport

Controlled categories: location validation, not found, ambiguous, network, timeout, provider, rate limit, malformed data and unavailable forecast. Safe messages exclude raw API reason strings and network internals. Original parse/request exceptions are chained where available.

Only the two approved HTTPS URLs are accepted. Query values use `requests` parameters; redirects are disabled. Explicit connect/read timeouts are 3.05/10 seconds. There is at most one retry with a 0.25-second pause for timeout/connection failures and HTTP 500/502/503/504. Other HTTP errors, malformed JSON and provider error objects are not retried. HTTP 429 and HTTP 503 with `Retry-After` return `WeatherRateLimitError` without an immediate retry; integer and HTTP-date headers become retry-delay metadata.

Responses are streamed with a 2 MB decoded-body cap and a cooperative 30-second elapsed check. This is not a hard wall-clock deadline: requests cannot guarantee prompt cancellation during DNS or a blocked/drip-fed read. Task 04 must run these synchronous operations in workers, with a separate service/session per worker. No threading, persistent cache, telemetry, credentials, IP geolocation or personal data storage is added.

## Validation

Environment: Python 3.12 on Linux; requests 2.34.2, pytest 9.2.0, tzdata 2026.6. Runtime dependencies and development dependencies are separately pinned. `pip check` reported no broken requirements. Application bytecode compilation passed.

Final command, from the project directory: `python -m pytest -q` (the recorded equivalent used an explicit project pytest.ini and test-directory path).

**176 passed in 0.55s.** Standard tests block real HTTP. Coverage includes city/country/postal search, ambiguity, malformed metadata, required current fields, units, nulls, finite numeric bounds, day/night, all WMO codes, conversions, HTTP failures and bounded retries, rate headers, invalid JSON, body limits, strict future selection, midnight, positive/negative/UTC zones, both DST transitions, fixed-offset daily labeling, complete and incomplete local-day coverage, three-hour gaps, seven-day slots, batch deduplication, partial failure and wrong-location rejection.

An initial test invocation from the workspace parent failed collection because that directory was outside the project's import configuration. Running from the documented project root resolved collection without changing application code or weakening tests. The first suite passed 172 tests; four further regression tests for reported offsets, three-hour gaps and 503 Retry-After produced the final 176 passes.

Fixtures are explicitly synthetic and sanitized Open-Meteo-shaped JSON, with plausible values and known location metadata. They are not represented as recordings or live observations.

Live smoke test on 2026-11-02: **passed**. One geocoding query for London filtered to GB resolved the explicit London/England/GB candidate; one combined forecast call constructed normalized models with current conditions, **168 hourly entries and 7 daily entries**, timezone Europe/London. No repeated live test was performed. This validates one location at that time, not global provider coverage or availability.

## Files changed

Modified: `README.md` (implementation status, setup, usage, data contracts and roadmap).

Created:

- `.gitignore`
- `app/__init__.py`
- `app/core/__init__.py`
- `app/core/condition_mapper.py`
- `app/core/exceptions.py`
- `app/core/forecast_processor.py`
- `app/core/models.py`
- `app/core/unit_converter.py`
- `app/core/validator.py`
- `app/providers/__init__.py`
- `app/providers/base.py`
- `app/providers/geocoding.py`
- `app/providers/http.py`
- `app/providers/open_meteo.py`
- `app/services/__init__.py`
- `app/services/location_service.py`
- `app/services/weather_service.py`
- `pytest.ini`
- `requirements-dev.txt`
- `requirements.txt`
- `tests/conftest.py`
- `tests/fixtures/README.md`
- `tests/fixtures/forecast.json`
- `tests/fixtures/geocoding.json`
- `tests/test_condition_mapper.py`
- `tests/test_forecast_processor.py`
- `tests/test_geocoding.py`
- `tests/test_http.py`
- `tests/test_unit_converter.py`
- `tests/test_weather_provider.py`
- `tests/test_weather_service.py`
- `docs/TASK03_COMPLETION_REPORT.md`


All existing Task 01/02 documentation and design assets are retained unchanged.

## Limitations and handoff

Task 03 is ready for Task 04 review. Backend calls are blocking and require worker integration; session instances should not be shared concurrently. Windows execution and the final desktop package remain unverified. Network availability, postal coverage and forecast completeness vary. Provider-daily and hourly-derived extrema are explicitly distinguished; partial DST boundary coverage is not concealed. Retry policy is bounded, not a guaranteed global rate limiter. No GUI, map rendering, speech, favorites, caching database, IP detection, full hourly chart, AI recommendations or cloud features are implemented.

Task 04: implement the approved exact dark dashboard, background requests, explicit candidate choice, current-versus-daily labels, partial-data notices, null chart handling, licensed icon rendering, visible attribution, coordinates-based markers and unit toggle. Task 05: implement only separately approved enhancements, including speech, favorites, cache and the planned additional visual/statistical features. No Task 04 files were started.

Attribution: weather by Open-Meteo (CC BY 4.0); geocoding by Open-Meteo/GeoNames. The educational noncommercial free API is not a blanket commercial-use permission. Preserve provider attribution and review service terms before commercial distribution. Source references: https://open-meteo.com/en/docs and https://open-meteo.com/en/docs/geocoding-api ; prior licensing and asset research remains in `docs/API_DECISIONS.md` and `docs/ASSET_PLAN.md`.
