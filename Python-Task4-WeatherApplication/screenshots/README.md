# Actual Linux GUI captures — alignment revision

Captured from CustomTkinter running on Linux/Xvfb with Python 3.12 and Tk 8.6.14 on 2 November 2026. These are actual application pixels, not generated mockups or Windows screenshots.

The six captures use real Open-Meteo forecasts for explicitly resolved London, Beijing Municipality and Freetown/Western Area. Values are snapshots, not continuously updated images. Official OpenWeather icons load asynchronously, with original artwork as a fallback.

- 1440x900 and 1366x768: corrected desktop composition with all seven forecast cards, map controls and three cities.
- 1024x700: smaller window with scroll access preserved.
- Tomorrow_F: future-day selection and Fahrenheit labels.
- Map_Stats: expanded details panel with hourly windows, units, refresh, city management and statistics.
- Light: light theme, with the geographic map retaining its dark artwork.

`python scripts/visual_smoke.py --output /your/capture/path` runs an offline deterministic fixture on an existing display. Add `--live` only for an intentional limited live check; it makes three forecast requests for documented resolved locations. Ordinary pytest tests never invoke live HTTP. The offline fixture captures are not included in this delivery.


## Task 05 actual GUI captures — 2026-11-02

Eight captures made by `scripts/task05_smoke.py` on Linux/Python 3.12/Tk 8.6. Weather was fetched live for London, Beijing and Freetown. These are real running widgets, not mockups. Offline captures deliberately simulate transport failure using those real cached bundles, not a measured internet outage. Voice is unavailable on Linux; no audio or public-IP request occurred. Favorites were verified by reopening the temporary SQLite database.

- [1024x700](SkyCast_Task05_1024x700.png)
- [1366x768](SkyCast_Task05_1366x768.png)
- [Dashboard](SkyCast_Task05_Dashboard.png)
- [Details](SkyCast_Task05_Details.png)
- [Fahrenheit](SkyCast_Task05_Fahrenheit.png)
- [Favorites](SkyCast_Task05_Favorites.png)
- [Location Consent](SkyCast_Task05_Location_Consent.png)
- [Offline](SkyCast_Task05_Offline.png)

The details, Fahrenheit, favorites and consent views are intentionally scrolled down within the expandable content area. The 1024×700 view uses scrolling to reach remaining cards/map content. Native Windows DPI/audio checks remain pending.


## Task 06 release-candidate evidence — Linux/Tk 8.6

Captured on 2026-11-02 by `scripts/task06_acceptance.py` using actual retrieved London/Freetown weather. Offline and timeout paths deliberately simulate transport failures; cache snapshots keep original timestamps. No real speech or public-IP request was made. Original fallback weather illustrations are used. These are actual widgets, not generated mockups or Windows captures.

- [1024x700](SkyCast_Task06_1024x700.png)
- [1366x768](SkyCast_Task06_1366x768.png)
- [Cached City](SkyCast_Task06_Cached_City.png)
- [Dashboard](SkyCast_Task06_Dashboard.png)
- [Details](SkyCast_Task06_Details.png)
- [Favorites](SkyCast_Task06_Favorites.png)
- [Location Consent](SkyCast_Task06_Location_Consent.png)
- [Offline](SkyCast_Task06_Offline.png)
- [Seven Days](SkyCast_Task06_Seven_Days.png)
- [Tomorrow Fahrenheit](SkyCast_Task06_Tomorrow_Fahrenheit.png)

[Machine-readable acceptance observations](task06_acceptance.json). The first close/reopen emitted Tcl timer warnings; the subsequent cleanup fix passed the final shutdown/reopen regression. Images predate that nonvisual fix. Details are scrolled inside the content area; 1024×700 uses scrollbars for remaining content.
