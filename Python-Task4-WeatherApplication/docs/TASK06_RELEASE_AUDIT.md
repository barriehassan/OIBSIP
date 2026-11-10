# NOMOLI FORGE — SkyCast: Task 06 Release Audit

**Date:** 2 November 2026  
**Author/project owner:** Hassan Barrie (`barriehassan`)  
**Assignment:** Oasis Infobyte Python Programming, Task 4 — Basic Weather App, Advanced Tier  
**Audited baseline:** `87fe883427faf29f11f7acab4cc01b94a7669bb5` on `barriehassan/OIBSIP/main`  
**Recommendation:** **Conditionally ready, pending specific checks.**

## A. Executive summary

The current Task 05 source was inspected and its existing 307 tests rerun before changes. This audit preserves the approved near-black dashboard and all mandatory/enhancement functionality. Focused fixes address excessive rate-limit metadata, deeply nested corrupt JSON, unlabelled old secondary-city readings and leftover Tcl timers at shutdown. No major feature or redesign was introduced.

The final suite collected and passed **315 tests**, with **0 failures, 0 errors and 0 skips**, in **48.19 seconds**. All 307 baseline tests remain, with eight release regression cases added. Live city searches/weather retrieval, simulated offline fallback, subsequent live recovery, favorite persistence and application reopening were exercised on Linux/Tk 8.6. Ten genuine application screenshots are included.

No critical defect identified by this audit remains open. This is not a claim of exhaustive correctness or native Windows certification. Windows SAPI5 playback/Stop, DPI/fonts/accessibility and user-side IP-location accuracy remain acceptance gates. No commit, push, merge, tag, GitHub release or publication was performed for Task 06.

## B. Official requirement compliance

Status legend: **V** = implemented and verified through code/tests and the named Linux/live evidence; **W** = implemented, with native Windows acceptance still required. V does not imply Windows verification. No requirement was marked not applicable merely because a widget exists.

| ID | Requirement | Status | Evidence and limits |
|---|---|---|---|
| FR-01 | City or postal-code input | V | `test_geocoding.py` validates normalization, invalid input, Unicode, ambiguity and transport errors. Live qualified London/Freetown and postal `10115` searches returned results. Postal coverage/country interpretation is provider-dependent; verify the selected country. |
| FR-02 | API and JSON processing | V | `providers/http.py`, `open_meteo.py`; `test_http.py`, `test_weather_provider.py`; two real city bundles and a live refresh succeeded. |
| FR-03 | Current °C/°F temperature | V | Canonical Celsius, shared converter, display/unit tests and actual °F capture. 0→32, 100→212, −40→−40, decimals/negative values tested. |
| FR-04 | Humidity | V | `relative_humidity_2m`, percentage bounds, normalized data and GUI labels verified; no fabricated values. |
| FR-05 | Weather condition | V | WMO mapping, unknown-code fallback and provider normalization tested. Live codes 2 and 55 returned during the run. |
| FR-06 | Wind speed | V | `wind_speed_10m`, explicit km/h request/normalization/display; live GUI inspected. |
| FR-07 | Functional desktop GUI | W | Real Linux window search, selection, rendering and errors passed; native Windows startup/rendering pending. |
| FR-08 | Condition icons | W | Day/night, cloud/rain/thunder/fog/snow/unknown mapping and asset failure tests passed. Original fallback illustrations were used in Task 06 captures; native Windows rendering pending. |
| FR-09 | Six-hour forecast | V | Six genuine upcoming hourly entries verified for both live cities; tests cover ordering, missing/three-hourly data, midnight and DST. |
| FR-10 | At least five daily forecasts | V | Seven provider days returned for both live cities. Seven local dated slots are supported; absent or incomplete provider days stay unavailable. DST-derived extrema are explicitly distinguished. |
| FR-11 | Unit toggle | W | Unit tests and live GUI switch cover current/daily/hourly/city/feels-like/chart; speech-summary text tested. Actual Windows spoken output pending. |
| FR-12 | Input validation | V | Empty/short/control-character/oversize input and metadata validation; live GUI empty-input check passed. |
| FR-13 | API failure handling | V | Timeout, disconnect, rate-limit, server errors, bad JSON, missing fields, response caps and controlled retries tested; simulated offline/timeout plus actual network recovery passed. |
| FR-14 | In-GUI errors | W | Inline errors, previous-result retention, retry/cancel and stale-response rejection verified on Linux; native Windows acceptance pending. |

City-and-country input is passed to Open-Meteo's documented qualifier syntax. The audit checked current documentation instead of assuming that comma-qualified input was unsupported. Candidate selection remains explicit when multiple results exist. The live unqualified postal `10115` returned New York, United States, not an assumed city in another country; the application does not override the provider with invented metadata.

## C. Advanced feature verification

| Enhancement | Verified behavior | Remaining qualification |
|---|---|---|
| SkyCast Voice | Explicit Listen/Stop, no startup speech; unit/location/current-value summary; cached wording; no overlap; cancellation on selection/unit change; engine error and cleanup tests; real silent spawned-process lifecycle. | Windows-only SAPI5 engine/audio and Stop latency not executed. Linux deliberately reports unavailable. |
| Favorite locations | Temporary SQLite add/remove/select/duplicates, distinct identities, corrupt-row handling and reopen tests; two actual resolved cities persisted across GUI close/reopen. | Manual Windows path/permission and restart acceptance pending. |
| Statistics | Humidity, wind, apparent temperature and next-hour rain probability; timestamped forecast label; unit/missing-value projections tested and inspected. | Rain probability is a forecast percentage, not observed rainfall volume. |
| Temperature chart | Six-hour selected window, UTC ordering/local offsets, C/F, null values, single dots, gap breaks and Canvas reuse tested. | No 24-hour selector is claimed; future-date windows use existing Previous/Next. |
| Cache | Recent reuse, forced refresh, network-only fallback, original periods/timestamps, stale age, corruption, newer-wins writes, bounded retention and clear-without-favorite-deletion verified. | Fresh data always requires a network. Offline startup requires a saved location/snapshot; no location is automatically chosen. |
| Sunrise/sunset | Selected local date and timezone; missing/mismatched-date events neutral; DST/solar projections tested and actual times inspected. | Missing polar events do not imply a diagnosis of polar day/night. |
| IP detection | Consent before HTTPS, separate result confirmation, manual fallback, no saved IP, finite response/time limits, malformed payload/rate/timeout/stale-result tests; actual consent panel inspected. | Implemented with mocked service verification; real IP accuracy/availability was not exercised. Provider terms caveat in section I. |

## D. Design fidelity and visual inspection

The authoritative Chennai dark-dashboard mockup was compared with the running application. The main composition remains: left grid/bell/location, central search, theme/About controls; Today/Tomorrow/Next 7 Days; horizontal cards with pale-blue selected card; rain chart at upper right; large dark map below left and other-city cards below right. Map marker and land transforms share the same equirectangular viewport. Pan, zoom, reset, layers and recenter have working handlers/tests. Missing map/icon assets have safe fallbacks.

Reviewed 1440×900, 1366×768 and 1024×700 captures. At 1024×700 the existing card/page scrollbars provide access to content outside the viewport; the screenshot is not a claim that everything fits simultaneously. Expanded details/favorites/consent intentionally scroll below the main dashboard. Chart final labels remain inside the canvas; cached-city timestamps fit their cards. Keyboard day/candidate navigation and 125% widget-scale simulation pass automated checks. There is no evidence here of native Windows DPI or screen-reader compatibility.

Remaining intentional differences from the reference: truthful percentage rain axis replaces qualitative mockup labels; °C/°F and high/low/date labels provide real data semantics; a second compact action row houses approved enhancements; icons/fonts are platform/asset-dependent; an S monogram and original storm illustration replace unlicensed avatar/photo assets; city cards and map pins show only chosen places, so their count varies. The search field retains the user's query while the pin header identifies the selected place. No fictional city/weather was added to fill empty space.

## E. Tests and live acceptance evidence

| Run | Result |
|---|---|
| Baseline before Task 06 changes | 307 passed in 42.15 s |
| Final full suite, Linux/Python 3.12/Tk 8.6 | 315 collected; 315 passed; 0 failed; 0 errors; 0 skipped; 48.19 s |
| pytest warnings | No warnings reported by the final run |
| Syntax/compilation | 35 application modules parsed; application/entry/script bytecode compilation passed |
| Dependency consistency | `pip check`: no broken requirements |
| Static import inventory | No unused imported names detected by the simple AST name-use scan after removing one unused UI import; this is not a full linter/security scanner |
| Coverage | Coverage instrumentation was not run; no coverage percentage is claimed |
| Not executed | Native Windows GUI/audio/DPI/accessibility; real IP lookup; installer build; automated dependency-vulnerability scan; long-duration memory profiling |

Command from the project directory: `python -m pytest -q -ra`. The full run used an Xvfb display so desktop tests did not skip. Tests block ordinary network calls, use deterministic clocks and temporary databases, and never speak through a real audio engine. No existing assertion was weakened. Regression evidence includes a reproduced rate-limit overflow and deeply nested cache failure before their fixes, and a test of timer cancellation followed by reopening.

Live/scripted acceptance (`scripts/task06_acceptance.py`, completed 12:38 UTC):

- `London, United Kingdom` resolved to London/GB, `Europe/London`; retrieval at 12:37:54 UTC, six upcoming hours, seven days, WMO code 2.
- `Freetown, Sierra Leone` resolved to Freetown/SL, `Africa/Freetown`; retrieval at 12:38:09 UTC, six upcoming hours, seven days, WMO code 55.
- Three application-level geocoding operations (two cities and one postal code), three weather operations (two initial cities and one recovery refresh). No hosted-icon, speech or IP request was made in this run. Transport can make its documented single retry; no total raw wire-request count is asserted.
- Simulated network loss used the actual saved bundles and showed offline/cache labels. Restoring the real backend and refreshing succeeded. A separate simulated timeout produced a GUI error. These simulations are not represented as an observed internet outage.
- Actual C/F switching, Today/Tomorrow/seven-day selection, chart/stats/solar rendering, map/city rendering, favorite save/reopen, cache reuse, empty-input error and close/reopen completed. No application `report_callback_exception` was recorded.
- The first close/reopen run emitted two third-party Tcl timer warnings despite the zero application-callback count. Task 06 then cancelled remaining interpreter timers before destruction; the final regression suite includes close/reopen and passes. Captures predate that nonvisual shutdown fix; display code is the same as captured.

Acceptance-flow coverage: requested steps 1–18, 21–26, 29–30 were exercised through the scripted Linux GUI/live or explicitly simulated paths. Steps 19–20 (real speech) are Windows-pending; step 27 was exercised only through consent UI and mocked service tests; step 28 (unknown city) is covered by deterministic geocoding/controller/widget error tests, not an additional live unknown-city request. Automated map-control tests supplement the live map inspection.

## F. Bugs found and fixed

| Finding | Impact and focused fix | Regression evidence |
|---|---|---|
| Unbounded Retry-After metadata | A 400-digit delay overflowed float arithmetic during controller drain, interrupting the UI poll; remote far-future dates could also impose unreasonable cooldowns. Normalize delays to 0–86,400 seconds. There is no automatic retry when the cooldown expires. | Three malformed/extreme delay cases, including controller integration. |
| Deeply nested corrupt cache JSON | Decoder recursion failure escaped the storage-error path and prevented normal online recovery. Translate recursion failures into existing safe errors in local cache/favorite, HTTP and IP JSON paths; preserve favorite records. | Deep cache recovery, corrupt favorite preservation and deep HTTP response cases. |
| Secondary-city age hidden | Old readings and failed refreshes lacked a visible retrieval timestamp. Cards now show Cached plus local download date/time when stale or failed; city actions show full retrieval time/offset. | Widget age/failure regression and actual cached-city screenshot. |
| Tcl callbacks survived shutdown | Creating another app in the same process exposed invalid-command warnings from CTk appearance/DPI timers. Cancel remaining timers in the closing Tcl interpreter before destroying its windows. | Close, assert no remaining timers, reopen actual Tk window. |
| Documentation/hygiene gaps | Replaced stage-mixed README with current release guide; added compliance/privacy/licensing/Windows checklists; excluded logs/build/private outputs; removed unused `fetch_icons` import. | Link/archive/source inventory checks; dependency and syntax checks. |

No broad architecture rewrite, runtime-data deletion or dependency removal was needed. The pinned runtime requirements remain unchanged. No user database was opened or modified.

## G. Files modified

Application fixes:

- `app/providers/http.py`: safe deep-JSON errors and bounded rate-limit delays; formatting.
- `app/storage/local.py`: safe recursion failures when reading corrupt stored JSON.
- `app/services/ip_location_service.py`: safe deep-JSON error handling.
- `app/ui/window.py`: secondary-city provenance, city retrieval detail, map help, unused import removal and Tcl-timer cleanup.

Verification/documentation:

- `tests/test_release_qa.py`, `tests/test_release_widgets.py`: eight release regression cases.
- `scripts/task06_acceptance.py`: reproducible explicit live GUI acceptance with temporary storage.
- `.gitignore`: log/build/cache/configuration exclusions.
- `README.md`: complete current installation/usage/architecture/privacy/limitations guide.
- `docs/TASK06_RELEASE_AUDIT.md`, `docs/WINDOWS_ACCEPTANCE.md`: this audit and remaining acceptance steps.
- `screenshots/README.md`, ten `SkyCast_Task06_*.png` files, `screenshots/task06_acceptance.json`: labeled evidence.
- `assets/ATTRIBUTION.md`: current provider-review reference.

## H. Security, privacy and resource review

No hardcoded credentials/API secrets, unsafe eval/pickle/shell execution, environment dumps or sensitive-content logging were found in application source during inspection/search. This is a source audit, not a penetration test or vulnerability-database scan. Weather/geocoding use two fixed HTTPS endpoints and encoded query parameters; icon IDs are allowlisted; IP detection uses a fixed HTTPS endpoint. TLS verification is not disabled and redirects are not followed. Weather bodies are capped at 2 MB, icon bodies at 200 KB with image format/dimension validation, and IP bodies at 32 KB. Socket timeouts and cooperative elapsed checks are present; they are not guaranteed hard wall-clock deadlines under all transport behavior. Weather retries once for selected transient failures and never immediately retries a 429.

The controller owns two daemon workers and replaces pending work by scope. Generation checks reject stale search/weather/city results. Tk mutations occur on its event loop. Active sockets cannot be forcibly interrupted; shutdown waits briefly and late results are discarded. Icons have bounded IDs and cached images; charts reuse Canvas items rather than creating matplotlib figures. Map redraws can allocate a larger raster at high zoom; no leak was observed in exercised navigation, but long-duration memory profiling was not performed. SQLite connections close per operation, writes are transactional and parameterized, and cache size/age/count are bounded. Voice owns COM/SAPI5 in its spawned process and has stop/time guards plus bounded shutdown.

Favorites/cache are local plaintext within the OS user's data directory, not encrypted or cloud-synced. They reveal saved locations to someone with access to that account. Runtime files are excluded from the package. Weather/search queries and coordinates go to Open-Meteo; icon requests go to OpenWeather. IP detection separately discloses that the provider sees the public address. No microphone, audio recording, cloud speech or unnecessary IP storage is present. No permissions or security protections were disabled.

## I. API and licensing review

Primary sources checked on 2026-11-02:

- [Open-Meteo terms](https://open-meteo.com/en/terms): free service is noncommercial, with limits below 10,000/day, 5,000/hour and 600/minute. Educational use is listed; commercial products/promotional use need reassessment. The data's CC BY 4.0 licence is distinct from access to the hosted free service.
- [Open-Meteo source attribution guidance](https://github.com/open-meteo/open-meteo): credit provider, link the licence and identify modifications. SkyCast includes provider links, [asset attribution](../assets/ATTRIBUTION.md), unit conversions and local-day correction notices.
- [Forecast docs](https://open-meteo.com/en/docs): `/v1/forecast` supports genuine hourly data and seven days. The code requests canonical units, Unix times, coordinates and `timezone=auto`, validating arrays/units before model construction.
- [Geocoding docs](https://open-meteo.com/en/docs/geocoding-api): city/postal search and comma qualifiers are supported; returned timezone/coordinates/country are validated. Coverage and qualifier semantics remain provider-dependent.
- [IPWHOIS.IO docs](https://ipwhois.io/documentation) and [pricing](https://ipwhois.io/pricing): advertise HTTPS, key-free/no-signup access and 1,000 requests/day. [Terms](https://ipwhois.io/terms) describe personal/internal-business use, restrict redistribution/resale, and include an account-registration obligation. That general wording is not fully aligned with the free endpoint's no-signup description. The implementation does not resell data or credentials; confirm applicable terms before wider/commercial distribution rather than claiming unrestricted permission. No real lookup was made here.
- [Natural Earth terms](https://www.naturalearthdata.com/about/terms-of-use/): land data is public domain. Bundled raster source/hash/projection are documented and tested.
- [OpenWeather icon docs](https://docs.openweather.co.uk/weather-conditions): documented condition IDs/hosted icon URL pattern. A direct page fetch timed out, but official indexed documentation was available. Hosted PNGs are fetched into memory and not redistributed in this source package; original fallback art is included. This audit does not grant new redistribution rights to provider artwork.
- [pyttsx3 2.99](https://pypi.org/project/pyttsx3/2.99/): dependency/voice details retained from the Task 05 review; installed package licence notices remain with the dependency. Windows voice assets are not bundled.

## J. Windows verification

Actual execution here: Linux, Python 3.12, Tk 8.6, CustomTkinter 6.0.0, requests 2.34.2, Pillow 13.0.0, tzdata 2026.6, pytest 9.2.0. `requirements.txt` includes pyttsx3 2.99 only on Windows. Its Windows engine/dependencies were not executed on Linux. A fresh native Windows installation is still required. No executable/installer was built.

Use [WINDOWS_ACCEPTANCE.md](WINDOWS_ACCEPTANCE.md) to record installation, first launch, real requests, native scaling, keyboard/accessibility, persistence/offline behavior, speech startup/Stop/errors/closure and consented approximate location. These remain explicit pending checks, not inferred passes from screenshots.

## K. Repository status

Remote `main` was verified at `87fe883427faf29f11f7acab4cc01b94a7669bb5` when Task 06 started. The environment provides source snapshots with no `.git` metadata: local branch and `git status` are unavailable, not clean. Changes are isolated in the Task 06 project snapshot and packaged for review. No replacement repository was initialized. Remote history was not rewritten and no Task 06 push occurred. Password Forge, BMI Insight and the repository root were not modified. Historical Task 01–05 files remain intact except the current project README/asset index updates listed above.

## L. Final recommendation

**Conditionally ready, pending specific checks.** The code and documentation form a reviewable release candidate; the supplied acceptance checks are necessary before calling it Windows release-ready.

Remaining actions:

1. Install and run the candidate on Windows using Python 3.12/Tk 8.6; complete the checklist, especially real SAPI5 Stop/cleanup, DPI/layout and network recovery.
2. Test IP detection only after consent on the user's machine; reject inaccurate results and use manual search. Clarify provider terms before wider/commercial distribution.
3. Capture native Windows evidence and record any defects; do not replace pending items with assumed passes.
4. Review and approve this candidate before commit/push or creating a release. Recheck remote head and preserve intervening work when publication is authorized.

Task 06 stops here. No later task or publication is started.
