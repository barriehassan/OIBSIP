# SkyCast assets and provider attribution

- **Weather:** Open-Meteo, https://open-meteo.com/ ; data attribution under CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ . Current values are model estimates. SkyCast applies display conversions and documented local-day aggregation corrections. Educational noncommercial service use; reassess service terms before commercial distribution.
- **Geocoding:** Open-Meteo / GeoNames, https://www.geonames.org/ . City coverage is not universal.
- **Basemap:** Natural Earth land polygons, public domain. Source and exact version/hash in `maps/source.json`. Terms: https://www.naturalearthdata.com/about/terms-of-use/ . Rasterization/recoloring by SkyCast. No political boundaries or claim of survey precision. The raster can be rebuilt with `scripts/build_map.py` and build-only Pillow/pyshp dependencies.
- **Hosted weather icons:** OpenWeather, documented at https://docs.openweather.co.uk/weather-conditions . Allowed condition IDs select `https://openweathermap.org/img/wn/<id>@2x.png`. Fetch at runtime, retain only in memory, credit visibly; no hosted PNG files are bundled for redistribution. This uses the official task's icon convention when reachable.
- **Fallback weather illustrations:** Original procedural Pillow artwork in `app/ui/components/weather_icon.py`, created for SkyCast in Task 04. Used when hosted icons are unavailable or still loading; not represented as OpenWeather artwork. Map badges use these local illustrations. Text preserves the actual condition.
- **Brand:** Text-only NOMOLI FORGE / SkyCast identity; no new final company logo is asserted.
- **Mockup:** User-supplied design reference only. Its full screenshot, avatar, weather artwork and promotional photo are not redistributed as application assets.
