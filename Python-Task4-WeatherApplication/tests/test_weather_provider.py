import pytest
from conftest import StubClient
from app.providers.open_meteo import OpenMeteoWeather
from app.core.exceptions import WeatherDataError


def test_normalization(payload,location,now):
    client=StubClient(payload)
    b=OpenMeteoWeather(client,clock=lambda:now).get_weather(location)
    assert (b.current.temperature_c,b.current.humidity_percent,b.current.wind_speed_kmh,b.current.feels_like_c)==(8.4,78,12.6,5.2)
    assert b.current.description=='Overcast' and b.current.is_day is True
    assert b.current.observed_at.hour==14 and b.current.observed_at.utcoffset().total_seconds()==0
    assert len(b.hourly_forecasts)==168 and len(b.daily_forecasts)==7
    assert b.daily_forecasts[0].temperature_min_c==5
    assert b.daily_forecasts[0].sunrise_at.hour==8
    assert client.calls[0][1]['forecast_days']==7
    assert client.calls[0][1]['timeformat']=='unixtime'

@pytest.mark.parametrize('field,value', [('temperature_2m',float('nan')),('temperature_2m',float('inf')),('temperature_2m',True),('temperature_2m','8'),('relative_humidity_2m',101),('relative_humidity_2m',-1),('wind_speed_10m',-1),('apparent_temperature',None),('time',10**100),('time',None),('is_day',2),('is_day',True),('weather_code',1.5)])
def test_invalid_current(field,value,payload,location,now):
    payload['current'][field]=value
    with pytest.raises(WeatherDataError): OpenMeteoWeather.normalize(payload,location,now)

@pytest.mark.parametrize('field', ['time','temperature_2m','relative_humidity_2m','apparent_temperature','weather_code','wind_speed_10m','is_day'])
def test_required_current(field,payload,location,now):
    del payload['current'][field]
    with pytest.raises(WeatherDataError): OpenMeteoWeather.normalize(payload,location,now)

@pytest.mark.parametrize('section,field,value',[('current_units','temperature_2m','°F'),('current_units','wind_speed_10m','m/s'),('hourly_units','time','iso8601'),('daily_units','temperature_2m_max','°F')])
def test_bad_units(section,field,value,payload,location,now):
    payload[section][field]=value
    with pytest.raises(WeatherDataError): OpenMeteoWeather.normalize(payload,location,now)

def test_missing_optional(payload,location,now):
    del payload['hourly']['precipitation_probability']
    del payload['daily']['sunrise']
    payload['hourly']['temperature_2m'][0]=None
    b=OpenMeteoWeather.normalize(payload,location,now)
    assert b.hourly_forecasts[0].temperature_c is None
    assert b.hourly_forecasts[0].precipitation_probability is None
    assert b.daily_forecasts[0].sunrise_at is None

def test_unknown_night(payload,location,now):
    payload['current'].update(weather_code=999,is_day=0)
    b=OpenMeteoWeather.normalize(payload,location,now)
    assert b.current.description=='Unknown conditions' and b.current.is_day is False

@pytest.mark.parametrize('section', ['hourly','daily'])
def test_absent_forecast(section,payload,location,now):
    del payload[section]
    b=OpenMeteoWeather.normalize(payload,location,now)
    assert b.warnings

@pytest.mark.parametrize('section,field,value',[('hourly','temperature_2m',[1]),('hourly','time','bad'),('hourly','precipitation_probability',[101]*168),('daily','temperature_2m_min',[99]*7)])
def test_bad_arrays(section,field,value,payload,location,now):
    payload[section][field]=value
    with pytest.raises(WeatherDataError): OpenMeteoWeather.normalize(payload,location,now)

def test_order_duplicates(payload,location,now):
    for k,values in payload['hourly'].items():
        payload['hourly'][k]=list(reversed(values))+[values[0]]
    b=OpenMeteoWeather.normalize(payload,location,now)
    assert len(b.hourly_forecasts)==168
    assert b.hourly_forecasts[0].forecast_at<b.hourly_forecasts[1].forecast_at
    payload['hourly']['temperature_2m'][-1]=999
    with pytest.raises(WeatherDataError): OpenMeteoWeather.normalize(payload,location,now)

@pytest.mark.parametrize('data', [None, [], {}, {'error':True}])
def test_bad_envelope(data,location,now):
    with pytest.raises(WeatherDataError): OpenMeteoWeather.normalize(data,location,now)

def test_fixed_offset_daily_labels(payload,location,now):
    from datetime import date
    # Fixed +02:00 API labels before DST ends: IANA conversion alone would label
    # Oct 26's 22:00 UTC boundary as Oct 25 23:00 in Berlin after the transition.
    from datetime import datetime, timezone
    from dataclasses import replace
    payload['timezone']='Europe/Berlin'
    payload['utc_offset_seconds']=7200
    start=int(datetime(2026,10,24,22,tzinfo=timezone.utc).timestamp())
    payload['daily']['time']=[start+i*86400 for i in range(7)]
    b=OpenMeteoWeather.normalize(payload,replace(location,timezone='Europe/Berlin'),now)
    assert b.daily_forecasts[1].date==date(2026,10,26)
    assert b.daily_forecasts[1].period_utc_offset_seconds==7200
