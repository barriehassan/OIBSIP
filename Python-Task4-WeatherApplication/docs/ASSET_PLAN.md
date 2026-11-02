# SkyCast — Asset and rendering plan

**Task 02 · Production assets are planned, not downloaded or bundled**

The approved screenshot is a visual reference, not permission to redistribute its illustrations, avatar, satellite image or full screenshot as application artwork. Its image dimensions and sampled palette inform the design. It is not cropped into widgets, included as a fake functional interface or published to the repository by this task.

## Asset register

| Asset | Planned source/license | Format and resolution | Use / fallback |
|---|---|---|---|
| Application icon | Original SkyCast sky/forge mark to be created later; user approval before final branding | Master vector; PNG 256/512; Windows ICO 16,24,32,48,64,128,256 | Title/taskbar; simple original neutral cloud placeholder during development |
| NOMOLI FORGE identity | User-approved original logo only when actual source file is supplied | Prefer vector master and transparent PNG at 2× target | Until then use plain text SkyCast + NOMOLI FORGE; do not invent a replacement final logo |
| Weather graphics | Official OpenWeatherMap hosted icon URLs, as required by assignment | PNG, choose supplied resolution suitable for 88/48/32 logical px targets | Separate source credit; neutral original unknown icon + condition text if unavailable |
| Dark basemap | Natural Earth public-domain world land dataset; record exact version when acquired | Equirectangular source extent; build 3072 × 1536 transparent-land PNG plus 1536 × 768 variant | Dark land on #1B1B1D; coordinate/name list if loading fails |
| Search/location/star/utility | Original simple vector paths or Canvas line geometry | 24 × 24 vector grid; render 18–24 logical px, 2× raster if needed | Text button labels remain; do not use unrelated emoji |
| Rain bars | Original programmatic Canvas drawing | Vector geometry, recalculated at current size | Textual six-slot probability list |
| Unknown weather | Original simple outlined cloud/question mark | SVG master + 32/64/128 PNG | Explicit unknown condition; never sunny fallback |

No asset is claimed created or licensed by this document alone. At acquisition time, retain upstream URL, version/hash, license text, attribution requirement, modification notes, and permitted distribution/caching use in an asset manifest. Avoid dependency installation purely to prepare this plan.

## Weather icon mapping

This maps normalized categories to official icon families. Text retains exact condition detail even when several codes share a picture. WMO code interpretation comes from the Task 01 API decision. Do not use an Open-Meteo number as an OpenWeather condition ID.

| WMO code(s) | Text/category | Day / night family |
|---|---|---|
| 0 | Clear sky | 01d / 01n |
| 1 | Mainly clear | 02d / 02n |
| 2 | Partly cloudy | 03d / 03n |
| 3 | Overcast | 04d / 04n |
| 45,48 | Fog / rime fog | 50d / 50n |
| 51,53,55 | Drizzle | 09d / 09n |
| 56,57 | Freezing drizzle | 09d / 09n |
| 61,63,65 | Rain | 10d / 10n |
| 66,67 | Freezing rain | 10d / 10n |
| 71,73,75,77 | Snow / snow grains | 13d / 13n |
| 80,81,82 | Rain showers | 09d / 09n |
| 85,86 | Snow showers | 13d / 13n |
| 95,96,99 | Thunderstorm / thunderstorm with hail | 11d / 11n |
| Missing/other | Unknown conditions | Original neutral placeholder |

Use the official documented hosted URL pattern identified in [API_DECISIONS.md](API_DECISIONS.md). Validate host and icon family; load images asynchronously with size/type checks. Use `is_day` for current/hourly variants, daytime illustration for daily summaries. Do not stretch a low-resolution downloaded icon beyond an acceptable tested size; request documented larger assets where available or reduce display size with approval. Keep image transparency and aspect ratio.

The screenshot's softly rendered illustrations may differ from official OpenWeather icons. The assignment's explicit source requirement takes priority over a claimed exact illustration match. Official URL use is the compliance strategy; a blanket installer-redistribution license has not been established. Do not commit/download an entire icon set for redistribution until applicable terms are verified. Credit icons separately from Open-Meteo weather data. MIT Meteocons remains a documented fallback only if the user/evaluator accepts an exception; preserve its copyright/license if adopted.

## World map decision

Render a local, north-up **equirectangular** land silhouette with full longitude −180 to +180 and latitude +90 to −90. Use low-resolution Natural Earth land polygons at build time to create a subtle dark raster, recording source/version. Do not require geopandas/cartopy or live map tiles at application runtime merely for this image. Natural Earth terms permit modification and redistribution as public-domain data; credit it voluntarily.

A 2:1 source image is contained within the map widget. At the default 968 × 408 panel, the displayed 816 × 408 map has 76 px side gutters; this avoids distorting geographic coordinates. Source-image composition is visually similar, but geographic projection fidelity is more important than stretching the map. A same-colored background makes the gutters unobtrusive. Markers use the displayed-image rectangle, not the entire panel.

For displayed rectangle `(x0, y0, w, h)`: x = x0 + (longitude + 180)w/360; y = y0 + (90 − latitude)h/180. This formula is valid only for the declared equirectangular extent. Normalize the ±180 seam consistently and clip hit targets. Reject invalid coordinates. Tooltip labels clamp to the widget boundary; small hit areas may be enlarged invisibly without moving the true marker position. Keep a list-based selection path for keyboard users.

Pin visual: 24–28 px dark circle, 16–20 px weather graphic when real data exists; selected pin 2 px light-blue ring and label. Without data use a location dot, not a weather icon. Source/age appears in detail. Actual labels replace the screenshot's sample geographic errors. Overlapping locations can share a selector popup; do not jitter them to false coordinates.

Phase 1: one selected place and up to three fetched secondary cities. Phase 2 adds favorites. No radar, satellite animation, worldwide live weather, or zoom/layers claim. View wide changes the rendering space only; it uses the same coordinates/source data. Do not offer centering/panning buttons until the transform and hit-testing exist.

## Attribution plan

Weather areas: a visible [Open-Meteo](https://open-meteo.com/) link and source/time information. About/README: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), geocoding credit to [GeoNames](https://www.geonames.org/), conversion/aggregation modification notes, separate OpenWeather icon credit and [Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/) source. Do not imply any provider endorses SkyCast.

License/service findings are carried forward from Task 01 research dated 2 November 2026. Recheck actual asset terms before acquisition/release. A personal educational API plan does not automatically permit future commercial promotional distribution.

## Delivery assets in this task

`UI_LAYOUT_PREVIEW.svg` and `UI_LAYOUT_PREVIEW.png` are original static structural wireframes, not production artwork or runnable UI. They contain labeled data placeholders, not fabricated live weather. The PNG is rendered from the SVG and visually inspected; no screenshot parity or Windows rendering is claimed.
