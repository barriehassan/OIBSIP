"""Desktop lifecycle checks using temporary SQLite, without requiring a display."""
import pytest
from app.core.validator import ValidationError
from app.core.classification import BMICategory
from app.database.errors import DatabaseError
from app.ui.controller import UIController

@pytest.fixture
def controller(storage):
    _, profiles, measurements, history = storage
    return UIController(profiles,measurements,history)


def test_calculate_centimetres(controller):
    result=controller.calculate('70','175')
    assert result.bmi_value == pytest.approx(22.857142857)
    assert result.height_m == 1.75
    assert result.category is BMICategory.NORMAL
    assert controller.calculated_at.tzinfo is not None


def test_save_requires_profile_and_calculation(controller):
    with pytest.raises(ValidationError,match='Select or create'):controller.save()
    controller.create_profile('Local')
    with pytest.raises(ValidationError,match='Calculate'):controller.save()


def test_edit_and_switch_invalidate(controller):
    a=controller.create_profile('A')
    b=controller.profiles.create('B')
    controller.calculate(70,175)
    controller.invalidate()
    with pytest.raises(ValidationError):controller.save()
    controller.calculate(70,175)
    controller.select(b.id)
    assert controller.result is None
    assert controller.history.count(a.id)==0
    assert controller.history.count(b.id)==0


def test_no_duplicate_save(controller):
    p=controller.create_profile('Local')
    controller.calculate(70,175)
    first=controller.save()
    assert first.bmi_value==controller.result.bmi_value
    with pytest.raises(ValidationError,match='already saved'):controller.save()
    assert controller.history.count(p.id)==1


@pytest.mark.parametrize('weight,height',[('',175),('bad',175),(70,''),(70,'abc'),(70,0),(70,17500),(0,175),(True,175),(70,True),(float('nan'),175)])
def test_bad_inputs_never_persist(controller,weight,height):
    p=controller.create_profile('Local')
    controller.calculate(70,175)
    with pytest.raises(ValidationError):controller.calculate(weight,height)
    assert controller.result is None
    assert controller.history.count(p.id)==0


def test_summary_uses_first_not_previous(controller):
    controller.create_profile('Local')
    for weight in [75,74,73]:
        controller.calculate(weight,175);controller.save()
    summary=controller.summary()
    assert summary.count==3 and summary.weight_change==-2
    assert summary.latest.weight_kg==73 and summary.first_weight==75
    assert len(controller.trend_points())==3


def test_empty_and_one_record_summary(controller):
    assert controller.summary().latest is None
    assert controller.trend_points()==[]
    controller.create_profile('Empty')
    assert controller.summary().count==0
    controller.calculate(70,175);controller.save()
    assert controller.summary().weight_change is None


def test_delete_explicit_confirmation(controller):
    profile=controller.create_profile('Local')
    with pytest.raises(ValidationError):controller.delete_profile()
    assert controller.profiles.get(profile.id)==profile
    controller.delete_profile(confirmed=True)
    assert controller.profile_id is None and controller.summary().count==0


def test_profile_names_and_rename(controller):
    profile=controller.create_profile(' A ')
    assert controller.rename_profile(' B ').id==profile.id
    assert controller.profiles.get(profile.id).name=='B'


def test_profile_isolation(controller):
    a=controller.create_profile('A');controller.calculate(70,175);controller.save()
    b=controller.create_profile('B')
    assert controller.summary().count==0
    assert controller.trend_points()==[]
    controller.select(a.id)
    assert controller.summary().count==1
    assert all(r.profile_id==a.id for r in controller.history.history(a.id))


def test_storage_failure_keeps_result_retryable(controller,monkeypatch):
    controller.create_profile('Local');controller.calculate(70,175)
    def fail(*args,**kwargs):raise DatabaseError('Storage unavailable.')
    monkeypatch.setattr(controller.measurements,'save',fail)
    with pytest.raises(DatabaseError):controller.save()
    assert controller.result is not None and controller.saved is None
