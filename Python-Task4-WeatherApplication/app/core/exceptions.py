"""Safe messages for presentation; original exceptions are chained for debugging."""


class SkyCastError(Exception):
    """Base for expected application failures."""


class LocationValidationError(SkyCastError, ValueError):
    pass


class LocationNotFoundError(SkyCastError):
    pass


class AmbiguousLocationError(SkyCastError):
    def __init__(self, candidates):
        self.candidates = tuple(candidates)
        super().__init__("Several locations match. Choose a city, region and country.")


class WeatherNetworkError(SkyCastError):
    pass


class WeatherTimeoutError(WeatherNetworkError):
    pass


class WeatherProviderError(SkyCastError):
    pass


class WeatherRateLimitError(WeatherProviderError):
    def __init__(self, retry_after_seconds=None):
        self.retry_after_seconds = retry_after_seconds
        super().__init__("The weather service is busy. Please retry later.")


class WeatherDataError(SkyCastError, ValueError):
    pass


class ForecastUnavailableError(SkyCastError):
    pass
