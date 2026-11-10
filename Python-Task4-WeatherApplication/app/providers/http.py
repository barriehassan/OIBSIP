"""Small synchronous transport. One retry; never follows redirects or retries 429."""

import json
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import requests
from app.core.exceptions import (
    WeatherDataError,
    WeatherNetworkError,
    WeatherProviderError,
    WeatherRateLimitError,
    WeatherTimeoutError,
)

ENDPOINTS = frozenset(
    (
        "https://geocoding-api.open-meteo.com/v1/search",
        "https://api.open-meteo.com/v1/forecast",
    )
)


class JsonClient:
    def __init__(
        self,
        session=None,
        *,
        sleep=time.sleep,
        monotonic=time.monotonic,
        clock=lambda: datetime.now(timezone.utc),
    ):
        self.session = session if session is not None else requests.Session()
        self.sleep, self.monotonic, self.clock = sleep, monotonic, clock

    def get(self, url, params):
        if url not in ENDPOINTS:
            raise WeatherProviderError("Unsupported weather endpoint.")
        started = self.monotonic()
        for attempt in range(2):
            try:
                with self.session.get(
                    url,
                    params=params,
                    timeout=(3.05, 10),
                    allow_redirects=False,
                    stream=True,
                ) as response:
                    status = response.status_code
                    if status == 429 or (
                        status == 503
                        and response.headers.get("Retry-After") is not None
                    ):
                        raise WeatherRateLimitError(
                            self._retry_after(response.headers.get("Retry-After"))
                        )
                    if status in (500, 502, 503, 504) and attempt == 0:
                        self.sleep(0.25)
                        continue
                    if not 200 <= status < 300:
                        raise WeatherProviderError(
                            "The weather provider could not complete the request."
                        )
                    chunks, size = [], 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > 2_000_000:
                            raise WeatherDataError("Weather response is too large.")
                        if self.monotonic() - started > 30:
                            raise WeatherTimeoutError(
                                "The weather request took too long."
                            )
                        chunks.append(chunk)
                    try:
                        result = json.loads(b"".join(chunks))
                    except (ValueError, UnicodeError, RecursionError) as exc:
                        raise WeatherDataError(
                            "The weather provider returned unreadable data."
                        ) from exc
                    if not isinstance(result, dict):
                        raise WeatherDataError(
                            "The weather provider returned an invalid response."
                        )
                    if result.get("error"):
                        raise WeatherProviderError(
                            "The weather provider rejected the request."
                        )
                    return result
            except (requests.Timeout, requests.ConnectionError) as exc:
                if attempt == 0 and self.monotonic() - started < 15:
                    self.sleep(0.25)
                    continue
                cls = (
                    WeatherTimeoutError
                    if isinstance(exc, requests.Timeout)
                    else WeatherNetworkError
                )
                raise cls("Unable to reach the weather service. Please retry.") from exc
            except requests.RequestException as exc:
                raise WeatherNetworkError(
                    "Unable to reach the weather service. Please retry."
                ) from exc

    def _retry_after(self, value):
        if value is None:
            return None
        try:
            seconds = int(value)
            return min(86400, max(0, seconds))
        except (ValueError, TypeError):
            try:
                return min(
                    86400,
                    max(
                        0, (parsedate_to_datetime(value) - self.clock()).total_seconds()
                    ),
                )
            except (ValueError, TypeError, OverflowError):
                return None
