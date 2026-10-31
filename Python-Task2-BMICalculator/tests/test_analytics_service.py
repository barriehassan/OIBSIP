"""Profile-scoped statistics and deterministic UTC period semantics."""
from datetime import datetime, timedelta, timezone
import pytest
from app.services.analytics_service import AnalyticsService, prepare_history, period_start, PERIODS
from app.core.validator import ValidationError

NOW=datetime(2026,10,31,12,tzinfo=timezone.utc)

@pytest.fixture
def analytics(storage):
    _,profiles,measurements,history=storage
    profile=profiles.create('Selected')
    return AnalyticsService(history),profile,measurements,profiles


def test_empty_and_single(analytics):
    service,profile,save,_=analytics
    empty=service.snapshot(profile.id,now=NOW)
    assert empty.records==empty.dates==()
    assert empty.statistics.count==0 and empty.statistics.average_bmi is None
    saved=save.save(profile.id,70,1.75,NOW)
    single=service.snapshot(profile.id,now=NOW)
    assert single.statistics.latest==saved
    assert single.statistics.previous is None and single.statistics.bmi_change is None
    assert single.statistics.average_bmi==saved.bmi_value


def test_sort_ties_and_full_precision(analytics):
    service,p,save,_=analytics
    newest=save.save(p.id,73,1.75,NOW)
    first=save.save(p.id,75,1.75,NOW-timedelta(days=2))
    previous=save.save(p.id,74,1.75,NOW-timedelta(days=2))
    data=service.snapshot(p.id,now=NOW)
    assert data.records==(first,previous,newest)
    assert data.dates[0]==data.dates[1]
    assert data.bmi_values==tuple(r.bmi_value for r in data.records)
    assert data.weight_values==(75,74,73)
    stats=data.statistics
    assert stats.latest==newest and stats.previous==previous
    assert stats.weight_change==-1 and stats.weight_change_from_first==-2
    assert stats.bmi_change==newest.bmi_value-previous.bmi_value
    assert stats.bmi_change_from_first==newest.bmi_value-first.bmi_value
    assert stats.highest_bmi==first.bmi_value and stats.lowest_bmi==newest.bmi_value
    assert stats.average_bmi==pytest.approx(sum(data.bmi_values)/3)


@pytest.mark.parametrize('period,expected',[
    ('Last 30 days',datetime(2026,10,1,12,tzinfo=timezone.utc)),
    ('Last 3 months',datetime(2026,7,31,12,tzinfo=timezone.utc)),
    ('Last 6 months',datetime(2026,4,30,12,tzinfo=timezone.utc)),
    ('Last 12 months',datetime(2025,10,31,12,tzinfo=timezone.utc)),
    ('All records',None)])
def test_period_start(period,expected):
    assert period_start(period,NOW)==expected


def test_leap_day_calendar_months():
    now=datetime(2024,5,31,tzinfo=timezone.utc)
    assert period_start('Last 3 months',now)==datetime(2024,2,29,tzinfo=timezone.utc)


@pytest.mark.parametrize('period',PERIODS[:-1])
def test_inclusive_filter_and_exclude_future(analytics,period):
    service,p,save,_=analytics
    start=period_start(period,NOW)
    save.save(p.id,80,1.75,start-timedelta(microseconds=1))
    begin=save.save(p.id,75,1.75,start)
    end=save.save(p.id,73,1.75,NOW)
    save.save(p.id,72,1.75,NOW+timedelta(microseconds=1))
    data=service.snapshot(p.id,period,NOW)
    assert data.records==(begin,end)
    assert data.statistics.count==2 and data.statistics.weight_change==-2
    assert service.snapshot(p.id,'All records',NOW).statistics.count==4


def test_empty_period_and_no_profile(analytics):
    service,p,save,_=analytics
    save.save(p.id,70,1.75,NOW-timedelta(days=400))
    assert service.snapshot(p.id,'Last 30 days',NOW).statistics.count==0
    assert service.snapshot(None,now=NOW).records==()


def test_profile_isolation(analytics):
    service,a,save,profiles=analytics
    first=save.save(a.id,70,1.75,NOW)
    b=profiles.create('Other')
    second=save.save(b.id,90,1.8,NOW)
    assert service.snapshot(a.id,now=NOW).records==(first,)
    assert service.snapshot(b.id,now=NOW).records==(second,)
    with pytest.raises(ValidationError,match='different profile'):
        prepare_history([first,second],a.id,now=NOW)


def test_invalid_period_time_and_timestamp(analytics):
    service,p,save,_=analytics
    with pytest.raises(ValidationError):service.snapshot(p.id,'Unknown',NOW)
    with pytest.raises(ValidationError):service.snapshot(p.id,now=NOW.replace(tzinfo=None))
    record=save.save(p.id,70,1.75,NOW)
    from dataclasses import replace
    with pytest.raises(ValidationError):prepare_history([replace(record,measured_at='bad')],p.id,now=NOW)


def test_timezone_equivalence(analytics):
    service,p,save,_=analytics
    save.save(p.id,70,1.75,NOW)
    assert service.snapshot(p.id,now=NOW).dates==service.snapshot(p.id,now=NOW.astimezone(timezone(timedelta(hours=8)))).dates


def test_single_history_read_per_snapshot(analytics,monkeypatch):
    service,p,save,_=analytics
    original=service.history.history;calls=[]
    def history(pid):calls.append(pid);return original(pid)
    monkeypatch.setattr(service.history,'history',history)
    service.snapshot(p.id,now=NOW)
    assert calls==[p.id]
