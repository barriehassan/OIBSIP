from datetime import datetime, timezone, timedelta
import pytest
from app.services.analytics_service import AnalyticsService
from app.services.dashboard_service import DashboardService, describe_change
from app.core.validator import ValidationError

NOW=datetime(2026,11,1,tzinfo=timezone.utc)

@pytest.fixture
def dashboard(storage):
    _,profiles,measurements,history=storage
    a=profiles.create('A');b=profiles.create('B')
    for days,weight in [(60,80),(5,75),(1,73)]:measurements.save(a.id,weight,1.75,NOW-timedelta(days=days))
    measurements.save(b.id,100,2,NOW)
    return DashboardService(AnalyticsService(history)),a,b

def test_dashboard_statistics(dashboard):
    service,a,b=dashboard;data=service.snapshot(a.id,now=NOW);s=data.selected.statistics
    assert s.count==data.all_time_count==3
    assert s.latest.weight_kg==73 and s.previous.weight_kg==75
    assert s.latest.bmi_value==pytest.approx(73/1.75**2)
    assert s.weight_change==-2
    assert s.bmi_change==s.latest.bmi_value-s.previous.bmi_value
    assert [r.weight_kg for r in data.selected.records]==[80,75,73]

def test_dashboard_filter_and_profile_isolation(dashboard):
    service,a,b=dashboard;data=service.snapshot(a.id,'Last 30 days',NOW)
    assert data.selected.statistics.count==2 and data.all_time_count==3
    assert {r.profile_id for r in data.selected.records}=={a.id}
    other=service.snapshot(b.id,now=NOW).selected.statistics
    assert other.count==1 and other.weight_change is None

def test_empty_dashboard(storage):
    service=DashboardService(AnalyticsService(storage[3]))
    data=service.snapshot(None)
    assert data.all_time_count==0 and data.selected.statistics.latest is None

def test_dashboard_refresh_after_changes(storage,dashboard):
    service,a,b=dashboard
    saved=storage[2].save(a.id,72,1.75,NOW)
    assert service.snapshot(a.id,now=NOW).selected.statistics.latest==saved
    storage[3].delete(a.id,saved.id)
    assert service.snapshot(a.id,now=NOW).selected.statistics.latest.weight_kg==73

def test_wrong_snapshot_rejected(dashboard):
    service,a,b=dashboard
    with pytest.raises(ValidationError):service.snapshot(a.id,all_data=service.analytics.snapshot(b.id))

@pytest.mark.parametrize('value,expected',[(None,'No previous'),(0,'No change'),(-2,'Decreased by 2.00'),(1.2,'Increased by 1.20'),(.0001,'Increased by less than 0.01')])
def test_neutral_changes(value,expected):
    assert describe_change(value,'kg').startswith(expected)
