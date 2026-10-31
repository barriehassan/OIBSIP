from datetime import datetime, timezone, timedelta
import pytest
from app.core.calculator import calculate_bmi
from app.core.classification import BMICategory
from app.core.validator import ValidationError
from app.database.errors import ProfileNotFound

def test_calculation_and_comparison(storage):
    _, profiles, service, history = storage
    p = profiles.create('A')
    first = service.save(p.id,'75','1.75')
    second = service.save(p.id,73,1.75)
    assert second.id > first.id
    assert second.bmi_value == calculate_bmi(73,1.75)
    assert second.category is BMICategory.NORMAL
    comparison = history.comparison(p.id)
    assert comparison.weight_change == -2
    assert comparison.bmi_change == second.bmi_value-first.bmi_value
    assert comparison.previous == first and comparison.latest == second

def test_unrounded_classification(storage):
    _, profiles, service, history = storage
    p = profiles.create('A')
    r = service.save(p.id,24.9999*4,2)
    assert r.formatted_bmi == '25.00'
    assert r.category is BMICategory.NORMAL
    assert history.get(p.id,r.id).bmi_value == r.bmi_value

@pytest.mark.parametrize('bad',['', 'abc',0,-1,True,None,float('nan'),float('inf'),501])
def test_invalid_not_saved(storage,bad):
    _, profiles, service, history = storage
    p = profiles.create('A')
    with pytest.raises(ValidationError): service.save(p.id,bad,1.75)
    assert history.count(p.id) == 0

def test_missing_profile(storage):
    _, _, service, _ = storage
    with pytest.raises(ProfileNotFound): service.save(999,70,1.75)

def test_timestamp_normalization(storage):
    _, profiles, service, _ = storage
    p = profiles.create('A')
    time = datetime(2026,1,1,2,tzinfo=timezone(timedelta(hours=2)))
    assert service.save(p.id,70,1.75,time).measured_at == '2026-01-01T00:00:00.000000+00:00'
    with pytest.raises(ValidationError): service.save(p.id,70,1.75,datetime(2026,1,1))
