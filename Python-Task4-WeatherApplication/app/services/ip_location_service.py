"""Opt-in HTTPS approximate lookup; never retain or expose the returned IP."""

import hashlib
import json
import time
import requests
from app.core.models import Location
from app.core.exceptions import (
    LocationValidationError,
    WeatherNetworkError,
    WeatherProviderError,
)

URL = "https://ipwho.is/"
FIELDS = "success,city,region,country,country_code,latitude,longitude,timezone.id"
CONSENT = (
    "Detect My Location uses the external IPWHOIS.IO service over HTTPS. The provider sees your public IP address. "
    "The result is approximate: VPNs, proxies and mobile networks can place it elsewhere. "
    "SkyCast does not save your IP. You can reject the result or use manual search. Continue?"
)


def normalize(payload):
    try:
        if not isinstance(payload, dict) or payload.get("success") is not True:
            raise ValueError()
        city = payload["city"]
        if not isinstance(city, str) or not city.strip() or len(city) > 150:
            raise ValueError()
        region = payload.get("region") or None
        country = payload["country"]
        code = payload["country_code"]
        lat, lon = payload["latitude"], payload["longitude"]
        zone = payload["timezone"]["id"]
        # Negative stable namespace; never pretend this is a GeoNames identifier.
        key = json.dumps([city, region, code, lat, lon, zone], sort_keys=True)
        ident = -int(hashlib.sha256(key.encode()).hexdigest()[:15], 16) - 1
        return Location(ident, city.strip(), region, country, code, lat, lon, zone)
    except (KeyError, TypeError, ValueError) as exc:
        raise LocationValidationError(
            "A usable city and coordinates could not be detected. Please use manual search."
        ) from exc


class IpLocationService:
    def __init__(self, session_factory=requests.Session, clock=time.monotonic):
        self.session_factory = session_factory
        self.clock = clock
        self.next_allowed = 0

    def detect(self, *, consent=False):
        if consent is not True:
            raise LocationValidationError("Location detection requires your consent.")
        if self.clock() < self.next_allowed:
            raise WeatherProviderError(
                "Location detection is cooling down. Please use manual search or try later."
            )
        self.next_allowed = self.clock() + 60
        try:
            with self.session_factory() as session:
                with session.get(
                    URL,
                    params={"fields": FIELDS},
                    timeout=(3, 6),
                    allow_redirects=False,
                    stream=True,
                ) as response:
                    if response.status_code == 429:
                        try:
                            delay = max(
                                60,
                                min(
                                    86400,
                                    int(response.headers.get("Retry-After", 86400)),
                                ),
                            )
                        except (ValueError, TypeError):
                            delay = 86400
                        self.next_allowed = self.clock() + delay
                    if response.status_code != 200:
                        raise WeatherProviderError(
                            "Approximate location is unavailable. Please use manual search."
                        )
                    data = bytearray()
                    started = self.clock()
                    for chunk in response.iter_content(4096):
                        data.extend(chunk)
                        if len(data) > 32768 or self.clock() - started > 10:
                            raise WeatherProviderError(
                                "Location response could not be used. Please search manually."
                            )
                    try:
                        payload = json.loads(data)
                    except (ValueError, UnicodeError):
                        raise LocationValidationError(
                            "Invalid location response. Please search manually."
                        ) from None
                    return normalize(payload)
        except requests.RequestException:
            raise WeatherNetworkError(
                "Unable to contact the location provider. Please use manual search."
            ) from None
