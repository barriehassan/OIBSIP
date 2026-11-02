from app.core.models import Location
from app.core.validator import normalize_query, country_filter
from app.core.exceptions import WeatherDataError, LocationNotFoundError
from .http import JsonClient

class OpenMeteoGeocoding:
    def __init__(self, client=None):
        self.client = client if client is not None else JsonClient()

    def search_locations(self, query, country_code=None):
        params = {'name': normalize_query(query), 'count': 10, 'language': 'en', 'format': 'json'}
        country = country_filter(country_code)
        if country:
            params['countryCode'] = country
        data = self.client.get('https://geocoding-api.open-meteo.com/v1/search', params)
        if not isinstance(data, dict) or data.get('error'):
            raise WeatherDataError('Invalid location response.')
        rows = data.get('results', [])
        if not isinstance(rows, list):
            raise WeatherDataError('Invalid location results.')
        results = []
        try:
            for row in rows:
                results.append(Location(row['id'], row['name'], row.get('admin1'), row['country'],
                                        row['country_code'], row['latitude'], row['longitude'], row['timezone']))
        except (KeyError, TypeError, AttributeError) as exc:
            raise WeatherDataError('Incomplete location data.') from exc
        if not results:
            raise LocationNotFoundError('No matching locations. Try a city and country or another postal code.')
        return tuple(dict.fromkeys(results))
