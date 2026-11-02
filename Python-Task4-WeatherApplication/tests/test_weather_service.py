from dataclasses import replace, FrozenInstanceError
import pytest
from app.services.weather_service import WeatherService
from app.core.exceptions import WeatherNetworkError, WeatherRateLimitError, LocationValidationError, WeatherDataError

class Provider:
    def __init__(self,bundle,fail_id=None,error=None):
        self.bundle,self.fail_id,self.error=bundle,fail_id,error
        self.calls=[]
    def get_weather(self,location):
        self.calls.append(location)
        if location.provider_id==self.fail_id: raise self.error
        return replace(self.bundle,location=location,timezone=location.timezone,
                       current=replace(self.bundle.current,temperature_c=float(location.provider_id)))

def test_reuse_and_isolation(bundle,location,now):
    provider=Provider(bundle)
    service=WeatherService(provider,clock=lambda:now)
    b=service.get_weather(location)
    assert service.get_current_weather(b).temperature_c==location.provider_id
    assert len(service.get_hourly_forecast(b).entries)==6
    assert len(service.get_daily_forecast(b).entries)==7
    assert len(service.get_rain_chart(b))==6 and len(provider.calls)==1
    other=replace(location,provider_id=2,name='Other',latitude=30)
    results=service.get_many([location,other,location])
    assert results[0] is results[2] and len(provider.calls)==3
    assert results[1].weather.current.temperature_c==2
    assert service.map_marker(results[1]).location.latitude==30

@pytest.mark.parametrize('error',[WeatherNetworkError('Try again'),WeatherRateLimitError(60)])
def test_partial_failure(bundle,location,error):
    other=replace(location,provider_id=2)
    third=replace(location,provider_id=3)
    provider=Provider(bundle,2,error)
    service=WeatherService(provider)
    results=service.get_many([location,other,third])
    assert results[0].weather is not None and results[1].weather is None
    marker=service.map_marker(results[1])
    assert marker.temperature_c is None and marker.error_message
    if isinstance(error,WeatherRateLimitError):
        assert len(provider.calls)==2 and results[2].error is error
    else: assert results[2].weather is not None

def test_limits(bundle,location):
    service=WeatherService(Provider(bundle))
    with pytest.raises(LocationValidationError): service.get_many([location]*11)
    with pytest.raises(LocationValidationError): service.get_weather('London')
    assert service.get_many([])==()

def test_wrong_location(bundle,location):
    class Wrong:
        def get_weather(self,loc): return replace(bundle,location=replace(loc,latitude=0))
    with pytest.raises(WeatherDataError): WeatherService(Wrong()).get_weather(location)

def test_immutable(bundle):
    with pytest.raises(FrozenInstanceError): bundle.current.temperature_c=2
    assert isinstance(bundle.hourly_forecasts,tuple)
