# SkyCast — Test and acceptance plan

**Task 01 · Planned tests only. No application tests have been run.**

Use pytest with injected providers, clock, storage and speech. Standard tests must work without internet, actual speech, a real user database or API credentials. Do not mix optional live smoke tests into the default suite. Tests below describe meaningful behavior, not a promised test count.

## Fixtures and layers

Keep hand-authored synthetic provider fixtures visibly marked as test data. Later, sanitize any recorded real contract fixtures, retaining provenance and capture date without private locations or keys. Include complete responses, null optional fields, absent sections, wrong units/types, mismatched arrays, duplicates, malformed JSON and HTTP failures. Test pure core functions first, adapter normalization second, service/controller behavior third, GUI and live integration separately.

Recommended offline command once tests exist: `python -m pytest -m "not live and not gui"`. Register markers. Windows GUI checks and live smoke commands must report their own results, environment and skips. Never report a skipped Windows test as verification.

## Core and adapter test matrix

| ID | Scenario | Expected result |
|---|---|---|
| LOC-01 | Empty/whitespace/control-only input | In-app validation, no HTTP call |
| LOC-02 | Unicode city, punctuation, city plus country | Query preserved/encoded; correct structured candidate |
| LOC-03 | Multiple places named the same | No automatic first-result selection; chooser identifies country/region |
| LOC-04 | Postal input with leading zero; country ambiguity | String preserved; explicit supported result or honest no-match |
| LOC-05 | Unknown place, malformed coordinates or timezone | Typed failure; no invented location |
| API-01 | Complete response | Correct normalized immutable models and provenance |
| API-02 | Nulls, missing fields, wrong units, out-of-range humidity | Preserve optional nulls; flag unavailable mandatory values; reject corrupt data |
| API-03 | Timeout/disconnect/5xx/429 | Bounded retry/deadline; retry-later status; no indefinite loader |
| API-04 | 400/401/403 and malformed JSON | No inappropriate retry; safe message; no secrets logged |
| API-05 | Missing/unequal arrays, oversized or slow-stream response | Partial/error according to contract; size/deadline enforced; no silent truncation |
| TIME-01 | Clock 14:00 and 14:20 UTC | Future hourly values begin at 15:00; exactly six if available |
| TIME-02 | Search near local midnight | Next-six-hour panel crosses dates honestly |
| TIME-03 | Duplicate/out-of-order/missing timestamps | Sort/deduplicate by UTC; missing interval stays a gap, no interpolation |
| TIME-04 | DST forward/back, fractional-offset zone | UTC spacing remains hourly; local repeat/skip labeled with offsets |
| TIME-05 | Today through +6 | Seven distinct local dates; tomorrow through +5 available |
| TIME-06 | 23/25-hour day and fixed-offset daily bins | Group actual instants into local dates; correct coverage and aggregation_basis; no date shifts |
| TIME-07 | Missing sunrise/sunset, polar cases | Unavailable display; no midnight or made-up event |
| UNIT-01 | 0°C, 100°C, −40°C | 32°F, 212°F, −40°F; inverse conversion returns input within tolerance |
| UNIT-02 | Repeated unit toggles and negative fractional values | Canonical Celsius unchanged; stable rounding and no negative zero |
| UNIT-03 | Main cards, other cities, chart and speech | All share unit state; wind remains labeled km/h; no network refetch |
| CODE-01 | All listed WMO groups, day/night, unknown | Consistent text/category/official icon-family mapping |
| CODE-02 | Official icon URL resolution | Allowlisted host/path/family, not arbitrary provider text |
| CODE-03 | Icon timeout, invalid image or oversize | Text/neutral fallback; weather display still usable |

For TIME-04/06, include `Africa/Freetown`, `America/New_York` on both transition directions, `Asia/Kathmandu`, and a location in a different date from the host. Use explicit frozen dates, not today's date. For daily calculations require coverage from one local midnight to the next, comparing UTC instants; do not assume exactly 24 samples. Test request-time offset differing from a later date's offset.

## Controller and UI tests

| ID | Scenario | Acceptance |
|---|---|---|
| GUI-01 | Start, search, Enter/Get Weather, candidate selection | Logical keyboard focus and usable results |
| GUI-02 | Current + hourly + daily layout | Units, times, descriptions and data type visible; no mislabeled maxima |
| GUI-03 | Loading/error/no-match/partial | Feedback inside GUI; controls remain usable |
| GUI-04 | City A slow, city B fast | A's late response never overwrites B |
| GUI-05 | Close while request or speech pending | No callbacks to destroyed widgets, no application crash |
| GUI-06 | Today/Tomorrow/seven-day tabs and card selection | Date selection, details and rain window agree |
| GUI-07 | Resizing and Windows scaling | Readable, no overlap; scrolling exposes all required regions |
| GUI-08 | Map at resize, antimeridian and poles | Projection/hit targets correct; no false weather pins |
| GUI-09 | One secondary-city request fails | Main location and other cards remain usable; failed card labeled |
| GUI-10 | Compare approved reference | Layout and emphasis preserved; no substituted design |

Headless controller tests should use fake dispatchers instead of starting Tk. A later Linux GUI smoke run is useful but cannot substitute for Windows rendering and packaged timezone checks.

## Phase 2 tests

| ID | Area | Cases and expected behavior |
|---|---|---|
| EXT-01 | Voice | Fake engine captures correct location/unit/current-vs-forecast/cache wording; stop cancels; no overlap; failure isolated |
| EXT-02 | Favorites | Persist/reload/remove; duplicate normalized location rejected; same city name in different countries remains distinct |
| EXT-03 | Statistics | Feels-like conversion; probability vs amount; selected time period correct |
| EXT-04 | Temperature chart | Sorted timestamps, missing gaps, changed axis units, no leaked figures after refresh/close |
| EXT-05 | Cache | Fresh hit, stale hit, offline missing, corrupt/schema mismatch, clock rollback and location isolation |
| EXT-06 | Sunrise/sunset | UTC-to-local conversion, DST, polar nulls, selected-day association |
| EXT-07 | IP detection | No request without consent; cancel; wrong approximation corrected; invalid/failure/429; raw IP not stored |
| EXT-08 | Persistence failure | Read-only app-data location/SQLite failure; no source-tree write; mandatory weather still works |

Use temporary directories for all persistence tests. Force clock values around the 20-minute boundary. Cache tests must prove expired forecast intervals do not reappear under “next six hours.” Speech unit tests must never play audio or open a microphone.

## Task 03 live smoke checklist — later, opt-in

Validate provider response shape and units with one resolved Freetown query, one ambiguous city, and a documented supported postal-code example. Fetch one small bundle and one official icon with HTTPS; inspect response keys, actual forecast length, timestamp semantics and content type. Record what ran and any endpoint/coverage limitations. Test network and malformed data primarily with mocks, not by abusing provider endpoints. Do not perform IP location lookup as part of this weather smoke test.

## Windows acceptance checklist — Task 04 and Task 06

- [ ] Record Windows version, Python version, Tk/CustomTkinter versions, resolution and scaling.
- [ ] Launch from documented entry point in a clean virtual environment.
- [ ] Verify packaged timezone data; selecting a distant timezone changes dates/hours correctly.
- [ ] Complete one city and one supported postal-code search with real provider data.
- [ ] Confirm current data, official condition icon, six hourly entries and five future dates.
- [ ] Toggle units throughout; no chart, city card or spoken value keeps the old unit.
- [ ] Test loading, retry, unknown city, offline mode and partial data.
- [ ] Verify keyboard navigation, focus, text scale and no clipped controls.
- [ ] Exercise tabs, card selection, map pins, other cities and resize/scroll behavior.
- [ ] Compare screenshots against the supplied approved image.
- [ ] After Phase 2, test local speech/Stop and favorites/cache across restart.
- [ ] Verify IP lookup remains disabled until consent.
- [ ] Verify no runtime files/keys/private values entered the repository.

## Gates and reporting

Task 01 checks document completeness, cross-links, traceability and source-backed feasibility. Task 03 checks engine contracts. Task 04 requires all FR items and baseline visual/Windows checks before optional work. Task 05 tests each enhancement independently. Task 06 runs regressions, final Windows acceptance, attribution/asset review and actual demo preparation.

Each implementation report must give commands, platform, exact passed/failed/skipped counts, failures, and manual evidence. This planning task has **zero application tests executed**; it makes no GUI or Windows success claim.
