# SkyCast — Requirements

**Task 01 · 2 November 2026 · Planning, not implementation**

## Authority and objective

The user's Consolidated Final Specification v1.0 is the project authority. The supplied `OASIS INFOBYTE — Task List(1).pdf`, physical page 28 of 45, was separately read to verify Task 4's beginner and advanced checklists. Pages 1–4 establish submission obligations. The original selected dashboard image was not available in this execution; the written composition is preserved, but pixel fidelity is not yet verified.

Build a dependable Python desktop application that helps users inspect current weather and forecasts. Complete the mandatory internship behavior before the seven approved enhancements. “Current” values must identify their source and valid time; freshly fetched model estimates are not direct station observations.

## Mandatory traceability

All requirements below are **planned, not passed**. Test IDs refer to [TEST_PLAN.md](TEST_PLAN.md).

| ID | Requirement | Planned acceptance evidence | Tests |
|---|---|---|---|
| FR-01 | City or supported postal/ZIP input | Show resolved name, region and country; require candidate selection when ambiguous; preserve postal leading zeros | LOC-01–05 |
| FR-02 | Request weather and parse JSON | Normalize a real provider response; reject malformed or mismatched data | API-01–05 |
| FR-03 | Current °C and °F | Show selected unit prominently and equivalent secondary value; shared toggle changes primary unit | UNIT-01–03 |
| FR-04 | Current humidity | Correct percentage; unavailable if missing, never fabricated zero | API-02, GUI-02 |
| FR-05 | Condition description | Shared mapping returns meaningful text, including unknown-code fallback | CODE-01 |
| FR-06 | Wind speed | Canonical km/h with explicit unit; never mislabel speed | API-02, GUI-02 |
| FR-07 | GUI input, Get Weather, results | Visible Get Weather action and Enter submission; CustomTkinter is the selected Tk-based GUI | GUI-01–03 |
| FR-08 | Condition icons | Use official OpenWeatherMap icon URLs as explicitly required by the brief, mapped from normalized conditions | CODE-01–03 |
| FR-09 | Next six hours | Six consecutive future hourly instants; allow midnight crossing; label unavailable gaps | TIME-01–04 |
| FR-10 | Next five days | At least tomorrow through local day +5, with conditions and high/low temperatures | TIME-05–06 |
| FR-11 | Unit switch | All temperature views update without another weather request or cumulative rounding | UNIT-02–03 |
| FR-12 | Input validation | Empty/whitespace input rejected in GUI before network access | LOC-01 |
| FR-13 | Errors | Unknown place, timeout, credential rejection where applicable, outage and malformed response do not crash the app | API-03–05 |
| FR-14 | GUI feedback | Errors, loading, retry and partial results appear in the window | GUI-03–05 |

The brief permits an equivalent free weather API but separately names OpenWeatherMap icon URLs. Therefore alternate weather data does not waive the icon clause. Open-Meteo's proposed public endpoint needs no weather API key; still model a credential error for provider portability and test it using a fake adapter.

The brief's IP detection via ipinfo.io is a **bonus**, not a mandatory release requirement. A provider substitution for that bonus must be recorded honestly, rather than described as literal ipinfo.io compliance.

## Product requirements beyond the official minimum

| ID | Requirement | Boundary |
|---|---|---|
| UI-01 | Preserve approved dark dashboard composition | Top location/search, three tabs, horizontal cards, blue active card, upper-right rain bars, lower-left map, lower-right city cards |
| UI-02 | Current conditions and next-six-hour strip | Compact current summary and secondary hourly strip; do not displace the map |
| UI-03 | Today / Tomorrow / Next 7 days | Today emphasizes current and next hours; Tomorrow uses the next local date; seven-day cards cover today through +6 |
| UI-04 | Map | Local base map with genuine geocoded pins; no fake global live weather |
| UI-05 | Other Large Cities | Resolve suggestions and fetch real values independently; errors isolated per card |
| UI-06 | Statistics | Mandatory humidity/wind visible in Phase 1; enhanced feels-like/rain tiles in Phase 2 |
| DATA-01 | Provenance | Source, valid timestamp, retrieval timestamp and cache status are distinct |
| DATA-02 | Missing values | Explicit unavailable values; retain usable sections and show degraded state |

## Seven approved enhancements

| ID | Feature | Acceptance boundary |
|---|---|---|
| EN-01 | SkyCast Voice | User-triggered local speech, Stop button, correct units/location/cache warning; no microphone, cloud speech or overlap |
| EN-02 | Favorite locations | Add/select/remove persisted resolved locations; prevent duplicate provider/location IDs |
| EN-03 | Rain and feels-like statistics | Real feels-like temperature, humidity, wind and probability with time period; distinguish mm from % |
| EN-04 | Hourly temperature chart | Real chronological points, current unit, missing-value gaps and date-aware labels |
| EN-05 | Cached weather | Location/provider-specific records, 20-minute proposed freshness, retrieval time and explicit stale label; safe corrupt-cache recovery |
| EN-06 | Sunrise/sunset | Correct location-local events for selected day, with unavailable handling for polar cases |
| EN-07 | IP location | Opt-in approximate result, explained provider disclosure, correction, no stored IP and graceful failure |

The Phase 1 rain bar chart and map container are design commitments, although not official checklist items. EN-03 adds the richer statistic cards; EN-04 adds the temperature trend; EN-05 adds persistent cache. These distinctions avoid silently expanding the core backend task into all Phase 2 work.

## Exclusions

No AI recommendations, accounts, microphone capture, cloud synchronization, paid subscriptions without approval, satellite prediction, radar layers, or complex live global mapping. No application code, GUI, SQL database, dependency installation, live weather implementation, commit, push or Task 02 work belongs in Task 01.

## Nonfunctional requirements

| ID | Requirement | Review criterion |
|---|---|---|
| NFR-01 | Reliability | Recover from failure while preserving valid, clearly identified previous results |
| NFR-02 | Responsiveness | Network and speech off Tk thread; stale requests cannot overwrite a later selection |
| NFR-03 | Maintainability | Core models and pure processing separate from provider, storage and UI |
| NFR-04 | Accessibility | Keyboard path, visible focus, useful labels, readable scale, selection beyond color alone |
| NFR-05 | Accuracy | Typed units, explicit aggregation periods, validated ranges, no invented measurements |
| NFR-06 | Transparency | Forecast/current/cached status and source visible |
| NFR-07 | Security/privacy | HTTPS, bounded requests, no secrets in Git, no IP lookup without consent |
| NFR-08 | Testability | Inject clock/provider/storage/speech; offline deterministic default suite |
| NFR-09 | Extensibility | Optional failures cannot break mandatory weather retrieval |
| NFR-10 | Visual fidelity | Compare Windows screenshots with the exact approved image before signoff |

## Phase 1 acceptance gate

FR-01–14 must pass together on Windows. The user must be able to start SkyCast, resolve a city/postal code, view real conditions and icons, inspect six future hourly entries and five future dates, toggle units and recover from invalid searches/network failures. Tabs, selected-card state, rain chart, map and city cards must behave honestly and remain readable on resize. No data or successful test result may be fabricated. Automated tests and manual Windows evidence are separate requirements.

## Submission obligations for Task 06

Preserve the single public `OIBSIP` repository and specified project folder. Include source, README and relevant screenshots/output. Prepare a functioning end-to-end demo beginning with a two-second title card showing Hassan Barrie, Python Programming, and the task title. The supplied task list additionally requires an Oasis Infobyte tagged LinkedIn demo with `#oasisinfobyte`, substantive comments on two cohort demos, and submission through the provided form. These are future user actions; Task 01 authorizes no posting, comments or submission.
