# Task 05 — completion report

Date: 2026-11-02. Project: NOMOLI FORGE SkyCast, Oasis Infobyte Python Task 4, Advanced Tier.

## Outcome and scope

All seven requested enhancements are implemented in the existing CustomTkinter application. The approved dark dashboard, city/country placement, search, forecast cards, rain visualization, map and city column remain the foundation. Additions use a compact secondary action row and the existing expandable details area. No unrelated OIBSIP project or repository-root file was edited. The implementation review package was delivered without a commit or push. The user subsequently approved committing and pushing Task 05 on 2026-11-02. Task 06 has not started.

Baseline: inspected remote main `6f9fa9b6744013d22092cd8fcbf491052435547f`, containing the approved Task 04 alignment. Work was performed on an isolated source snapshot, not a replacement Git repository. Review against the current repository before later publication. The baseline suite passed 244 tests in 23.19 seconds before enhancements.

## Implemented features

| Feature | Implementation and behavior |
|---|---|
| SkyCast Voice | Explicit Listen/Stop, local Windows SAPI5 via pyttsx3 2.99; actual normalized current values, active unit and full resolved location. Cached speech identifies last-retrieved conditions and time. Optional missing metrics are omitted. |
| Favorites | Transactional SQLite, resolved identity including provider ID/country/coordinates; add, reopen, select, remove, duplicate suppression and a 50-location cap. Distinct same-name places remain distinct. Session city pins remain separate. |
| Statistics | Four current-statistics cards: humidity, wind, feels-like and next-hour rain probability with its actual forecast timestamp. Temperature units propagate; absent values stay unavailable. |
| Temperature chart | One reusable Canvas for the selected six-hour window. UTC-ordered samples, local date/hour/offset labels, C/F conversion, single-point dots, line breaks at missing values or noncontiguous hours. Existing window navigation is reused. |
| Cached weather | Validated normalized bundle plus provider/timezone/retrieval/schema metadata in SQLite. Recent cache may avoid a request; explicit Refresh attempts network; network failure can fall back to valid recent/stale cache. Download time remains visible even when details are collapsed. |
| Sunrise/sunset | Selected-date daily records, converted using location timezone; date mismatch or unavailable events display neutral unavailable text. No invented times or polar diagnosis. |
| Approximate IP location | Opt-in HTTPS IPWHOIS.IO lookup after disclosure; result requires confirmation before weather selection. Manual search remains available; no IP is persisted. |

## Speech ownership and cleanup

Tk owns only controls and status polling. Each requested utterance spawns one isolated process; its main thread initializes COM and SAPI5, pumps the engine's external event loop, and releases both on exit. No engine object is passed across threads. Repeated requests cannot overlap. Stop signals an event; the parent terminates a nonresponsive child after a short grace interval. Window closure uses bounded joins, termination and a final kill fallback. Runtime guards prevent indefinitely active speech. Location/search/unit changes stop obsolete output. Errors become visible unavailable/error states without breaking weather functionality.

The Windows-only dependency marker installs pyttsx3 2.99; its wheel metadata lists comtypes, pypiwin32 and pywin32 for Windows. Engine initialization is lazy. Linux shows Voice unavailable. No microphone, recording, online TTS or real audio playback was used in validation. Tests inject engines/processes, plus a real spawned silent worker checks actual lifecycle. These checks do not establish Windows COM/audio correctness.

References: [pyttsx3 2.99](https://pypi.org/project/pyttsx3/2.99/), [engine API](https://pyttsx3.readthedocs.io/en/latest/engine.html), [SAPI5 driver source](https://github.com/nateshmbhat/pyttsx3/blob/master/pyttsx3/drivers/sapi5.py).

## Persistence and cache policy

Windows path: `%APPDATA%/NOMOLI_FORGE/SkyCast/skycast.sqlite3`. Linux: `$XDG_DATA_HOME/NOMOLI_FORGE/SkyCast/skycast.sqlite3`, defaulting to `~/.local/share`. Connections are opened per operation and never shared between threads. Weather storage/network work runs through the existing worker controller. Small favorite operations are bounded local transactions with a short busy timeout.

Schema version 1 rejects unknown newer versions. Cache decoding reconstructs validated model objects, verifies association/timezone/periods, rejects duplicate periods, oversize payloads, malformed values and unreasonable future timestamps. Only equally recent or newer writes replace a location's snapshot. Freshness is 20 minutes; the maximum usable age is seven days. Successful writes prune old entries and retain at most 30 locations, at most 500 KB per payload. Cache clearing does not remove favorites. Invalid favorite rows are skipped and counted, not silently erased. Corruption or inaccessible storage leaves online weather usable and reports a safe notice. There is no IP, token, credential or raw provider response stored.

Offline fallback is restricted to network failures, not arbitrary invalid/provider/rate-limit responses. Forecast timestamps remain unchanged. Upcoming-hour selection removes past periods; missing future coverage remains unavailable. The display marks cache provenance and stale age, including as time passes. City refresh also uses the cache path, with cached failures marked for retry. Existing generation checks reject obsolete worker results.

## IP provider verification and privacy

Provider checked on 2026-11-02: [IPWHOIS.IO documentation](https://ipwhois.io/documentation), [pricing](https://ipwhois.io/pricing), [terms](https://ipwhois.io/terms). The advertised key-free HTTPS endpoint allows 1,000 daily requests with standard accuracy and no SLA; commercial use is advertised subject to terms. The app requests only city/region/country/coordinates/timezone and success fields, never saves an IP, and does not silently select a country capital. Invalid city/coordinates/timezone or ambiguous payloads fail safely. Stable negative identifiers distinguish approximate locations from GeoNames IDs.

Consent explains that the external service sees the public IP and that VPNs/proxies/mobile networks affect accuracy. There is no startup or background detection. Request timeout/response-size limits, a one-minute cooldown, rate-limit delay handling and controller cancellation protect responsiveness. Manual search is available on rejection/failure. Tests cover success, malformed data, HTTP/rate errors, timeout and stale results. No actual public-IP lookup was performed from this cloud environment; a user's real detected location must be checked locally.

## Validation and visual review

- Final full suite: **307 passed, 0 failed, 0 skipped in 40.80 seconds** on Linux, Python 3.12, Tcl/Tk 8.6 with an Xvfb display. All 244 previous tests remain included; 63 tests were added. Ordinary tests block real HTTP.
- After the final panel-scroll timing adjustment, the four enhancement widget tests passed again in 13.59 seconds. Bytecode compilation passed and `pip check` reported no broken requirements. Windows-only dependency resolution was inspected from the published wheel metadata; it was not installed/executed on Linux.
- Actual GUI smoke script retrieved weather for resolved London, Beijing and Freetown locations. It saved a favorite and reopened the database, then forced a simulated transport failure and verified real saved weather was displayed with an offline/cache label. Temporary databases were removed. No speech or IP request occurred.
- Eight real application captures cover the dashboard, details, Fahrenheit, favorites, consent, offline state, 1366×768 and 1024×700. No screenshot is a generated mockup. Captures are under `screenshots/` and described in its README.
- Visual inspection found and fixed the final chart-label clipping by reserving more right margin. Opening inline panels now waits for geometry to settle before scrolling them into view. The 1440×900 and 1366×768 dashboards retain the original top-bar/map composition; 1024×700 uses existing horizontal/vertical scrolling. Details are intentionally below the fold and the top bar stays visible.

## Manual Windows verification and remaining limitations

No known failing automated test remains. Native Windows behavior is not claimed verified. Before release, test:

1. Fresh Python 3.12/Tk 8.6 environment installation and launch; no console traceback with unavailable storage or network.
2. Actual SAPI5 speech in C/F, cached wording, long place names, repeated clicks, Stop during startup/playback, changing city/unit while speaking, and closing during speech; confirm no lingering process or overlapping audio.
3. Missing Windows voice, broken audio device/engine and permission failures; weather and manual search must remain usable.
4. Favorites across a real restart, remove/duplicate behavior, cache reuse/clear, offline cold start with and without data, reconnect/Refresh and stale periods.
5. Explicit IP consent/cancel, approximate local result acceptance/rejection, VPN mismatch, provider failure/rate limit and manual-search recovery.
6. Native 100%/125%/150% DPI, keyboard/focus traversal, screen-reader behavior and window sizes. Linux captures and existing scale simulation do not certify native Windows accessibility.

Speech is deliberately Windows-only in this implementation. Geographic detection is approximate and provider-dependent. Forecast availability and provider failures remain visible rather than synthesized. The chart currently presents six-hour windows, not an added 24-hour selector. No installer/executable, AI recommendations, accounts or cloud sync is included.

Task 05 is approved for publication with these explicit platform checks outstanding. Task 06 may begin only after approval; this report does not claim final release readiness.

## Files

The following source/documentation inventory is relative to the project directory (historical files remain intact). New screenshots and this report are additional review artifacts.

Modified:
- `.gitignore`
- `README.md`
- `app/ui/components/forecast.py`
- `app/ui/controller.py`
- `app/ui/window.py`
- `assets/ATTRIBUTION.md`
- `requirements.txt`

Created:
- `app/services/cache_service.py`
- `app/services/ip_location_service.py`
- `app/services/voice_service.py`
- `app/storage/__init__.py`
- `app/storage/local.py`
- `app/ui/components/temperature_chart.py`
- `app/ui/enhancement_data.py`
- `app/ui/enhancements.py`
- `scripts/task05_smoke.py`
- `tests/test_enhancements_data.py`
- `tests/test_enhancements_storage.py`
- `tests/test_enhancements_voice_ip.py`
- `tests/test_enhancements_widgets.py`
