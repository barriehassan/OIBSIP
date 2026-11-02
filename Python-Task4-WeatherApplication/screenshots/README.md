# Actual Linux GUI captures — alignment revision

Captured from CustomTkinter running on Linux/Xvfb with Python 3.12 and Tk 8.6.14 on 2 November 2026. These are actual application pixels, not generated mockups or Windows screenshots.

The six captures use real Open-Meteo forecasts for explicitly resolved London, Beijing Municipality and Freetown/Western Area. Values are snapshots, not continuously updated images. Official OpenWeather icons load asynchronously, with original artwork as a fallback.

- 1440x900 and 1366x768: corrected desktop composition with all seven forecast cards, map controls and three cities.
- 1024x700: smaller window with scroll access preserved.
- Tomorrow_F: future-day selection and Fahrenheit labels.
- Map_Stats: expanded details panel with hourly windows, units, refresh, city management and statistics.
- Light: light theme, with the geographic map retaining its dark artwork.

`python scripts/visual_smoke.py --output /your/capture/path` runs an offline deterministic fixture on an existing display. Add `--live` only for an intentional limited live check; it makes three forecast requests for documented resolved locations. Ordinary pytest tests never invoke live HTTP. The offline fixture captures are not included in this delivery.
