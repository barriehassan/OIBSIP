from dataclasses import replace
from datetime import datetime, timedelta, timezone, date
from zoneinfo import ZoneInfo
import pytest
from app.core.models import HourlyForecast, DailyForecast
from app.core.forecast_processor import next_six_hours, seven_days, rain_chart
from app.core.exceptions import ForecastUnavailableError, WeatherDataError

def test_six_hours(bundle,now):
    result=next_six_hours(bundle,now)
    assert [r.forecast_at.hour for r in result.entries]==[15,16,17,18,19,20]
    assert result.complete and not result.gap_after
    assert rain_chart(result)[0].probability_percent==100
    assert rain_chart(result)[2].probability_percent is None
    assert next_six_hours(bundle,now.replace(minute=0)).entries[0].forecast_at.hour==15

def test_midnight(bundle,now):
    rows=next_six_hours(bundle,now.replace(hour=22)).entries
    assert [r.forecast_at.hour for r in rows]==[23,0,1,2,3,4]
    assert rows[-1].forecast_at.date()==date(2026,1,16)

@pytest.mark.parametrize('start,expected_hours', [('2026-03-08T06:00:00+00:00',[3,4,5,6,7,8]),('2026-11-01T04:00:00+00:00',[1,1,2,3,4,5])])
def test_dst_hours(bundle,start,expected_hours):
    now=datetime.fromisoformat(start)
    rows=tuple(HourlyForecast(now+timedelta(hours=i),10,0,20) for i in range(1,7))
    result=next_six_hours(replace(bundle,hourly_forecasts=tuple(reversed(rows))),now)
    assert result.complete
    assert [r.forecast_at.astimezone(ZoneInfo('America/New_York')).hour for r in result.entries]==expected_hours
    assert len(set(r.forecast_at for r in result.entries))==6

@pytest.mark.parametrize('kind',['gap','short','null','late'])
def test_partial_hours(bundle,now,kind):
    rows=list(next_six_hours(bundle,now).entries)
    if kind=='gap': rows.pop(2)
    if kind=='short': rows=rows[:2]
    if kind=='null': rows[0]=replace(rows[0],temperature_c=None)
    if kind=='late': rows=[replace(r,forecast_at=r.forecast_at+timedelta(hours=3)) for r in rows]
    result=next_six_hours(replace(bundle,hourly_forecasts=tuple(rows)),now)
    assert not result.complete
    if kind=='gap': assert result.gap_after

def test_missing_hours(bundle,now):
    with pytest.raises(ForecastUnavailableError): next_six_hours(replace(bundle,hourly_forecasts=()),now)
    with pytest.raises(WeatherDataError): next_six_hours(bundle,now.replace(tzinfo=None))

def test_seven_days(bundle,now):
    result=seven_days(bundle,now)
    assert result.complete and len(result.entries)==7
    assert result.dates[0]==now.date() and result.dates[-1]==now.date()+timedelta(days=6)
    assert result.entries[0].temperature_max_c==11

def test_missing_days(bundle,now):
    result=seven_days(replace(bundle,daily_forecasts=bundle.daily_forecasts[1:]),now)
    assert result.entries[0] is None and not result.complete
    with pytest.raises(ForecastUnavailableError): seven_days(replace(bundle,daily_forecasts=()),now)

@pytest.mark.parametrize('tz,expected',[('UTC',date(2026,1,15)),('Asia/Tokyo',date(2026,1,16)),('America/Los_Angeles',date(2026,1,15))])
def test_local_today(bundle,tz,expected):
    location=replace(bundle.location,timezone=tz)
    result=seven_days(replace(bundle,location=location,timezone=tz),datetime(2026,1,15,23,tzinfo=timezone.utc))
    assert result.dates[0]==expected

@pytest.mark.parametrize('d,count',[(date(2026,3,8),23),(date(2026,11,1),25)])
def test_dst_daily_bounds(bundle,d,count):
    tz=ZoneInfo('America/New_York')
    start=datetime(d.year,d.month,d.day,tzinfo=tz).astimezone(timezone.utc)
    rows=tuple(HourlyForecast(start+timedelta(hours=i),float(i),0) for i in range(count))
    day=DailyForecast(d,99,-99,0)
    b=replace(bundle,location=replace(bundle.location,timezone=tz.key),timezone=tz.key,
              retrieved_at=start,hourly_forecasts=rows,daily_forecasts=(day,))
    r=seven_days(b,start).entries[0]
    assert (r.temperature_min_c,r.temperature_max_c)==(0,count-1)
    assert r.source=='hourly-derived local day' and r.weather_code is None
    r=seven_days(replace(b,hourly_forecasts=rows[:-1]),start).entries[0]
    assert r.temperature_min_c is None and r.temperature_max_c is None

def test_provider_period_offset_not_clock_offset(bundle):
    tz=ZoneInfo('Europe/Berlin')
    start=datetime(2026,10,26,tzinfo=tz).astimezone(timezone.utc)
    rows=tuple(HourlyForecast(start+timedelta(hours=i),i,0) for i in range(24))
    day=DailyForecast(date(2026,10,26),99,-99,0,period_utc_offset_seconds=7200)
    b=replace(bundle,location=replace(bundle.location,timezone=tz.key),timezone=tz.key,
              retrieved_at=start,hourly_forecasts=rows,daily_forecasts=(day,))
    result=seven_days(b,start)
    assert result.entries[0].temperature_max_c==23
    assert not result.complete  # condition aggregation for the corrected period is unavailable

def test_three_hourly_not_claimed_hourly(bundle,now):
    rows=tuple(HourlyForecast(now+timedelta(hours=3*i),10,0) for i in range(1,7))
    result=next_six_hours(replace(bundle,hourly_forecasts=rows),now)
    assert len(result.entries)==6 and len(result.gap_after)==5 and not result.complete
