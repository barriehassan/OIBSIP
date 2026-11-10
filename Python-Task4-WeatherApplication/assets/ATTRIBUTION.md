# SkyCast assets and provider attribution

- **Weather:** Open-Meteo, https://open-meteo.com/ ; data attribution under CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ . Current values are model estimates. SkyCast applies display conversions and documented local-day aggregation corrections. Educational noncommercial service use; reassess service terms before commercial distribution.
- **Geocoding:** Open-Meteo / GeoNames, https://www.geonames.org/ . City coverage is not universal.
- **Basemap:** Natural Earth land polygons, public domain. Source and exact version/hash in `maps/source.json`. Terms: https://www.naturalearthdata.com/about/terms-of-use/ . Rasterization/recoloring by SkyCast. No political boundaries or claim of survey precision. The raster can be rebuilt with `scripts/build_map.py` and build-only Pillow/pyshp dependencies.
- **Hosted weather icons:** OpenWeather, documented at https://docs.openweather.co.uk/weather-conditions . Allowed condition IDs select `https://openweathermap.org/img/wn/<id>@2x.png`. Fetch at runtime, retain only in memory, credit visibly; no hosted PNG files are bundled for redistribution. This uses the official task's icon convention when reachable.
- **Fallback weather illustrations:** Original procedural Pillow artwork in `app/ui/components/weather_icon.py`, created for SkyCast in Task 04. Used when hosted icons are unavailable or still loading; not represented as OpenWeather artwork. Map badges use these local illustrations. Text preserves the actual condition.
- **Brand:** Text-only NOMOLI FORGE / SkyCast identity; no new final company logo is asserted.
- **Mockup:** User-supplied reference for dashboard layout, spacing and typography.

## Alignment revision artwork

`app/ui/components/chrome.py` draws original interface symbols. The S monogram represents SkyCast and opens About.

## Task 05 services and libraries

Optional approximate location: IPWHOIS.IO, https://ipwhois.io/documentation and https://ipwhois.io/terms . Requested only after explicit consent; approximate results require confirmation.

Local Windows speech: pyttsx3 2.99, https://pypi.org/project/pyttsx3/2.99/ (MPL-2.0), using installed Windows SAPI5 voices. Installed through requirements, not bundled as modified library source or redistributed voice assets. Engine API: https://pyttsx3.readthedocs.io/en/latest/engine.html .

## Task 06 review

Current provider terms, attribution, IP service caveats and distribution limitations are reviewed in `docs/TASK06_RELEASE_AUDIT.md`, section I (2026-11-02). This educational source candidate does not establish permission for future commercial/promotional service use.

The storm thumbnail in the map card is a crop from the project’s supplied generated SkyCast design reference. It is decorative artwork.
