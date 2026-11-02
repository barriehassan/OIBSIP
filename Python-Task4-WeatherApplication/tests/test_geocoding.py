import pytest
from conftest import StubClient
from app.providers.geocoding import OpenMeteoGeocoding
from app.services.location_service import LocationService
from app.core.exceptions import *

@pytest.mark.parametrize('query,normalized', [(' London  ', 'London'), ('London, United Kingdom','London, United Kingdom'), ('00100','00100'), ('São   Paulo','São Paulo'), ('LA','LA')])
def test_search(query, normalized, geo_payload):
    client = StubClient(geo_payload)
    rows = OpenMeteoGeocoding(client).search_locations(query, 'gb')
    assert rows[0].name == 'London' and rows[1].country_code == 'CA'
    assert client.calls[0][1]['name'] == normalized
    assert client.calls[0][1]['countryCode'] == 'GB'

@pytest.mark.parametrize('query', ['', ' ', 'x', ',', '!!', 'a, GB', None, 123, 'a'*121, 'London\n'])
def test_invalid(query):
    client = StubClient({})
    with pytest.raises(LocationValidationError): OpenMeteoGeocoding(client).search_locations(query)
    assert not client.calls

@pytest.mark.parametrize('data', [{}, {'results':[]}])
def test_no_results(data):
    with pytest.raises(LocationNotFoundError): OpenMeteoGeocoding(StubClient(data)).search_locations('Nowhere')

@pytest.mark.parametrize('data', [[], {'results':None}, {'results':[{}]}, {'results':['London']}, {'error':True}])
def test_malformed(data):
    with pytest.raises(WeatherDataError): OpenMeteoGeocoding(StubClient(data)).search_locations('London')

def test_ambiguity(geo_payload):
    service = LocationService(OpenMeteoGeocoding(StubClient(geo_payload)))
    with pytest.raises(AmbiguousLocationError) as e: service.resolve_unique('London')
    assert len(e.value.candidates) == 2
    geo_payload['results'] = geo_payload['results'][:1]
    assert service.resolve_unique('London').provider_id == 2643743

@pytest.mark.parametrize('exc', [WeatherTimeoutError('Retry later'), WeatherNetworkError('Retry later'), WeatherProviderError('Retry later')])
def test_transport_errors(exc):
    with pytest.raises(type(exc)): OpenMeteoGeocoding(StubClient(exc)).search_locations('London')

@pytest.mark.parametrize('field,value', [('latitude',91),('longitude',float('nan')),('timezone','No/Such_Zone'),('id',True),('country_code','GBR')])
def test_invalid_metadata(field,value,geo_payload):
    geo_payload['results'][0][field]=value
    with pytest.raises(WeatherDataError): OpenMeteoGeocoding(StubClient(geo_payload)).search_locations('London')
