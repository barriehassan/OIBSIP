from app.core.exceptions import AmbiguousLocationError

class LocationService:
    def __init__(self, provider):
        self.provider = provider

    def search_locations(self, query, country_code=None):
        return self.provider.search_locations(query, country_code)

    def resolve_unique(self, query, country_code=None):
        candidates = self.search_locations(query, country_code)
        if len(candidates) != 1:
            raise AmbiguousLocationError(candidates)
        return candidates[0]
