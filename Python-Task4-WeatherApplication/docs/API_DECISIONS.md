# SkyCast — API decisions and feasibility

**Research date: 2 November 2026.** Documentation was reviewed; no live weather integration or endpoint smoke test was executed. Endpoint contracts below are implementation proposals requiring fixture and live smoke validation in Task 03. Sources are linked at the end.

## Decision summary

| Area | Decision | Reason / limitation |
|---|---|---|
| Weather | Open-Meteo adapter | Proposed fit for the educational app; confirm noncommercial use context |
| Location search | Open-Meteo geocoding | Candidate chooser; supported city and postal-code queries |
| Icons | Official OpenWeatherMap hosted icon URLs | Meets the assignment's explicit icon source clause |
| Map | Local Natural Earth basemap with Canvas pins | Feasible without paid tiles or global weather layer |
| Speech | Local pyttsx3, Phase 2 | No cloud or microphone needed; Windows runtime test pending |
| IP location | ipwho.is candidate, Phase 2 | Documented city/coordinate fields; user opt-in; not literal ipinfo.io bonus compliance |
| Alternative weather | Future OpenWeather adapter | Keep interface portable; do not assume a free three-hour endpoint meets hourly requirements |

## Forecast request proposal

`GET https://api.open-meteo.com/v1/forecast`

| Parameter | Proposed value |
|---|---|
| latitude, longitude | Resolved location coordinates |
| current | temperature_2m, relative_humidity_2m, apparent_temperature, is_day, precipitation, weather_code, wind_speed_10m |
| hourly | temperature_2m, relative_humidity_2m, apparent_temperature, precipitation_probability, weather_code, wind_speed_10m, is_day |
| daily | temperature_2m_min, temperature_2m_max, weather_code, precipitation_probability_max, sunrise, sunset |
| temperature_unit / wind_speed_unit / precipitation_unit | celsius / kmh / mm |
| timezone / timeformat | Resolved IANA timezone / unixtime |
| forecast_days / past_days | 9 / 1, for local-boundary coverage; show only the required window |

Documentation confirms hourly and daily fields, epoch-time output, and timezone controls. Current conditions are model-based. The documented daily boundaries use a fixed offset, while epoch times can be converted with an IANA zone for DST-aware display. The architecture therefore explicitly handles transition-day aggregation. [S1]

All remaining behavior is SkyCast policy: combine required fields in one bundle, validate array lengths against timestamps, keep nulls, accept partial usable sections, and report missing coverage. A mandatory field being absent prevents a full acceptance pass even if the rest of the response can be shown. Preserve provider coordinate metadata separately: a model grid point is not the user's exact location. Render rain probability as %, rainfall as mm, and indicate the period each statistic describes. Do not calculate probability from rainfall amount.

The usual seven displayed dates are today through +6. Nine requested days are a small safety margin, not a promise to display nine. Limit secondary city cards to three visible independently fetched locations, deduplicate refreshes and avoid a worldwide polling loop.

## Geocoding

`GET https://geocoding-api.open-meteo.com/v1/search` with `name`, `count=10`, `language=en`, `format=json` and optional `countryCode`. The documented search accepts location names/postal codes and comma-separated country or administrative qualifiers. Responses provide location identity, coordinates and timezone metadata. Coverage is not universal. [S2]

SkyCast passes queries as encoded request parameters, preserving Unicode and leading zeros. Display name, region and country for every candidate. Never silently choose the first of several plausible places. A postal code shared across countries needs a country filter or explicit choice. Empty/missing results become “No supported location found; try a nearby city or add a country.” Do not invent a match or silently convert a numeric query into coordinates. Resolve user confirmation before downloading weather.

## Service limits and attribution

The published open-access limits are 600 calls/minute, 5,000/hour, 10,000/day and 300,000/month; keep safely below them and honor 429 responses. Multi-variable or longer requests can consume more than one billed call, so an HTTP-request count is not necessarily the quota count. Free access excludes commercial use. Educational use is listed as a qualifying example, while commercial promotional activities are not. [S3, S4]

Recommendation: use the free endpoint for Hassan's noncommercial internship demonstration. Before a business/promotional launch, recheck use classification and obtain an appropriate provider arrangement; do not automatically subscribe or treat company branding as permission.

API data licensing and hosted-service access are different matters. Open-Meteo publishes data under CC BY 4.0 and requires credit, license linkage and an indication of modifications. Its geocoding data source includes GeoNames. [S5] Planned UI attribution is a visible Open-Meteo link in each independently viewed weather area, plus full source/license/change notes in About and README. State that SkyCast converts units and may aggregate hourly samples; do not imply endorsement. Recheck notices when dependencies/assets are acquired.

## Icon strategy and assignment compliance

The supplied Task 4 brief, page 28, specifically requires OpenWeatherMap icon URLs. The official documentation currently shows `https://openweathermap.org/payload/api/media/file/10d@2x.png` and the day/night icon families. [S6] Use that documented host/path pattern with a validated allowlist of icon names, rather than constructing a URL from arbitrary API text.

The following is **SkyCast's proposed semantic mapping**, not a claim that Open-Meteo emits OpenWeather IDs:

| Open-Meteo WMO code | Meaning | OpenWeather icon family |
|---|---|---|
| 0 | Clear | 01d / 01n |
| 1 | Mainly clear | 02d / 02n |
| 2 | Partly cloudy | 03d / 03n |
| 3 | Overcast | 04d / 04n |
| 45, 48 | Fog / depositing rime fog | 50d / 50n |
| 51, 53, 55, 56, 57 | Drizzle / freezing drizzle | 09d / 09n |
| 61, 63, 65, 66, 67 | Rain / freezing rain | 10d / 10n |
| 71, 73, 75, 77, 85, 86 | Snow / grains / snow showers | 13d / 13n |
| 80, 81, 82 | Rain showers | 09d / 09n |
| 95, 96, 99 | Thunderstorm / with hail | 11d / 11n |
| Other or missing | Unknown | Neutral local placeholder and “Unknown conditions” |

Keep exact condition text to distinguish conditions sharing one coarse icon. Day/night comes from the relevant timestamp's data, not the PC clock. A daily summary uses a daytime icon and is identified as a daily summary. Download images off-thread, validate content/size and decode with Pillow. Weather remains readable if icons fail. No icon is embedded in this planning package.

The icon documentation demonstrates hosted usage, but it does not establish a blanket redistribution license for bundling every PNG with an installer. Use hosted official assets for the compliance path; verify applicable use/caching/redistribution terms before packaging, retain source records and credit OpenWeather separately from the weather data. Do not silently substitute another pack to claim FR-08 has passed.

If hosted official icons become unavailable or unsuitable, Meteocons is an MIT-licensed alternative with copyright/license preservation. [S7] Using it would require an explicitly accepted exception to the internship icon requirement. It is a fallback decision, not the selected compliance route.

## Alternative weather provider

OpenWeather's five-day endpoint provides three-hour intervals. [S8] It cannot directly satisfy six consecutive hourly values; SkyCast must not interpolate that feed and present it as provider-supplied hourly weather. A future switch requires a currently verified plan covering hourly data and at least five future days, credential handling and user approval for any cost. Keep the current adapter architecture; do not build a second provider in Task 01.

## Map feasibility

Natural Earth raster/vector datasets are public domain and can be restyled; attribution is optional, though SkyCast will credit the source. [S9] Proposed implementation: derive a simple dark equirectangular land image at build time from low-resolution world land polygons and ship the resulting local PNG with source/version records. Do not use an arbitrary web screenshot as a redistributable map.

Use a Tk Canvas inside the CustomTkinter panel. For an equirectangular extent, project longitude/latitude into the displayed image rectangle: x = x0 + (longitude + 180) × width / 360; y = y0 + (90 − latitude) × height / 180. Preserve the map aspect ratio and account for letterboxing. Test equator, poles, corners and the antimeridian. Draw only genuinely resolved locations. Pin selection can fetch that location's weather; attach a temperature only when its bundle exists and show its timestamp/status.

Phase 1 supports the selected location and fetched secondary cities. Saved-location pins arrive with favorites. A local image supports limited coordinate selection, not live radar or global observation coverage. Zoom/pan is technically possible by transforming the same image and pins, but adds hit-testing, clipping and blur concerns; omit those controls initially unless actually implemented. Redraw only on resize/selection, retain one base image and debounce resize. Label the panel “Global Map — location overview.” An offline basemap is not offline weather.

## IP geolocation feasibility

IPinfo Lite supplies country/continent and ASN information, not the city coordinates needed for a weather location. [S10] Do not substitute a country's capital as the user's position.

The current ipwho.is documentation supports HTTPS, automatic caller-IP lookup, and geolocation fields; it lists a free limit of 1,000 requests/day and no SLA. [S11] Candidate endpoint: `https://ipwho.is/`. Validate `success`, numeric latitude/longitude, country/city and timezone metadata. Recheck terms, availability and fields during Task 05; this review did not make a location request.

Before calling, explain that an external provider receives the public IP and returns an approximate network location that can be wrong, particularly on VPN/mobile connections. Require explicit activation, allow cancel, and confirm/correct the returned place. Never log/store the returned IP. Fail safely back to manual city search. This alternative fulfills the project's opt-in detection goal, but differs from the brief's named ipinfo.io bonus; do not represent it as exact bonus-provider compliance.

## Sources reviewed

- **S1:** [Open-Meteo forecast documentation](https://open-meteo.com/en/docs).
- **S2:** [Open-Meteo geocoding documentation](https://open-meteo.com/en/docs/geocoding-api).
- **S3:** [Open-Meteo pricing and limits](https://open-meteo.com/en/pricing).
- **S4:** [Open-Meteo service terms](https://open-meteo.com/en/terms).
- **S5:** [Open-Meteo data license and source attribution](https://open-meteo.com/en/licence).
- **S6:** [OpenWeather condition and icon documentation](https://openweathermap.org/api/weather-conditions).
- **S7:** [Meteocons upstream repository and MIT license](https://github.com/basmilius/meteocons).
- **S8:** [OpenWeather five-day forecast documentation](https://m.openweathermap.org/api/forecast5).
- **S9:** [Natural Earth terms](https://www.naturalearthdata.com/about/terms-of-use/).
- **S10:** [IPinfo Lite documentation](https://ipinfo.io/developers/lite-api).
- **S11:** [IPWhois API documentation](https://ipwhois.io/documentation).
- **Assignment:** `OASIS INFOBYTE — Task List(1).pdf`, supplied by Hassan, page 28, and submission instructions pages 1–4. This source was read; it is not republished in this pack.

All sources were reviewed on 2 November 2026. The official brief's older free-tier suggestions do not override current provider terms. Revalidate endpoints, licenses and quotas before implementation/release.
