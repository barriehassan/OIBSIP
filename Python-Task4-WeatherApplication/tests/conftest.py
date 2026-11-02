import json
from pathlib import Path
from datetime import datetime, timezone
import pytest
import requests
from app.core.models import Location
from app.providers.open_meteo import OpenMeteoWeather

@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError('Unit tests must not access the network')
    monkeypatch.setattr(requests.sessions.Session, 'request', fail)

@pytest.fixture
def location():
    return Location(2643743, 'London', 'England', 'United Kingdom', 'GB', 51.50853, -0.12574, 'Europe/London')

@pytest.fixture
def now():
    return datetime(2026, 1, 15, 14, 20, tzinfo=timezone.utc)

@pytest.fixture
def payload():
    return json.loads((Path(__file__).parent/'fixtures/forecast.json').read_text())

@pytest.fixture
def geo_payload():
    return json.loads((Path(__file__).parent/'fixtures/geocoding.json').read_text())

@pytest.fixture
def bundle(payload, location, now):
    return OpenMeteoWeather.normalize(payload, location, now)

class StubClient:
    def __init__(self, data):
        self.data, self.calls = data, []
    def get(self, url, params):
        self.calls.append((url, params))
        if isinstance(self.data, Exception):
            raise self.data
        return self.data
