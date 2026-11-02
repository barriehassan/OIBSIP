# Actual Linux GUI captures

Captured from CustomTkinter running on Linux/Xvfb with Python 3.12 and Tk 8.6.14. These are not Windows screenshots.

The 1440 × 900, 1366 × 768, 1024 × 700 Map/Stats and Tomorrow/Fahrenheit captures use real Open-Meteo forecasts retrieved on 2 November 2026 for explicitly resolved London, Beijing Municipality and Freetown/Western Area. Values are snapshots, not continuously updated images. Original icon fallbacks are shown while hosted OpenWeather icons load; six hosted images loaded during the capture run.

Tomorrow_F verifies the Fahrenheit selector and all displayed temperatures together, using the same real retrieved bundles as the other final captures. The earlier offline fixture captures are not included in this delivery.

`python scripts/visual_smoke.py --output /your/capture/path` runs the deterministic fixture capture on an existing display. Add `--live` only for an intentional limited live check; that mode makes three forecast requests for the documented resolved locations. Standard pytest runs never invoke live HTTP.
