from datetime import datetime, timezone, timedelta
import pytest
from app.database.errors import ProfileNotFound, MeasurementNotFound
from app.core.validator import ValidationError

def test_history_order_and_scoping(storage):
    _, profiles, service, history = storage
    a,b = profiles.create('A'),profiles.create('B')
    t = datetime(2026,1,1,tzinfo=timezone.utc)
    newest = service.save(a.id,73,1.75,t+timedelta(days=1))
    old = service.save(a.id,75,1.75,t)
    tie = service.save(a.id,74,1.75,t)
    foreign = service.save(b.id,90,1.8,t)
    assert history.history(a.id) == [old,tie,newest]
    assert history.history(a.id,2) == [tie,newest]
    assert history.latest(a.id) == newest
    assert history.previous(a.id) == tie
    assert history.count(a.id) == 3
    assert history.get(a.id,old.id) == old
    with pytest.raises(MeasurementNotFound): history.get(a.id,foreign.id)
    with pytest.raises(MeasurementNotFound): history.delete(a.id,foreign.id)
    assert history.history(b.id) == [foreign]
    assert history.chart_data(a.id) == [(r.measured_at,r.weight_kg,r.bmi_value) for r in [old,tie,newest]]
    history.delete(a.id,tie.id)
    assert history.count(a.id) == 2
    with pytest.raises(MeasurementNotFound): history.get(a.id,tie.id)

def test_empty(storage):
    _, profiles, _, history = storage
    p = profiles.create('Empty')
    assert history.history(p.id) == []
    assert history.latest(p.id) is None
    assert history.previous(p.id) is None
    assert history.comparison(p.id) is None
    assert history.chart_data(p.id) == []

@pytest.mark.parametrize('limit',[0,-1,True,'2',1.5,10**100])
def test_bad_limit(storage,limit):
    _, profiles, _, history = storage
    p = profiles.create('A')
    with pytest.raises(ValidationError): history.history(p.id,limit)

def test_forged_result(storage):
    from app.core.models import BMIResult
    _, profiles, service, _ = storage
    p = profiles.create('A')
    result = BMIResult(70,1.75)
    object.__setattr__(result,'bmi_value',100)
    with pytest.raises(ValidationError): service.measurements.save(p.id,result)
