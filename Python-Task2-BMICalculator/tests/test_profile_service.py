import pytest
from app.core.validator import ValidationError
from app.database.errors import ProfileNotFound

def test_confirmation_cascade_isolation(storage):
    _, profiles, measurements, history = storage
    a,b = profiles.create('A'),profiles.create('B')
    measurements.save(a.id,75,1.75)
    other = measurements.save(b.id,70,1.75)
    preview = profiles.deletion_preview(a.id)
    assert preview.profile == a and preview.measurement_count == 1
    with pytest.raises(ValidationError): profiles.delete(a.id)
    profiles.rename(a.id,'Renamed')
    assert history.count(a.id) == 1
    assert profiles.get(b.id) == b
    profiles.delete(a.id,confirmed=True)
    assert history.history(b.id) == [other]
    with pytest.raises(ProfileNotFound): history.history(a.id)

@pytest.mark.parametrize('bad',[True,False,0,-1,'1',None,10**100])
def test_bad_ids(storage,bad):
    _, profiles, *_ = storage
    with pytest.raises(ValidationError): profiles.get(bad)
