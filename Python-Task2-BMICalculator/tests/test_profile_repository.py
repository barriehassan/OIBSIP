import pytest
from app.database.errors import ProfileNotFound
from app.core.validator import ValidationError

def test_profile_lifecycle(storage):
    _, profiles, *_ = storage
    first = profiles.create('  First  ')
    second = profiles.create('First')
    assert first.name == 'First'
    assert first.id != second.id
    assert profiles.list() == [first,second]
    renamed = profiles.rename(first.id,' Renamed ')
    assert renamed.id == first.id
    assert renamed.created_at == first.created_at
    assert profiles.get(second.id) == second
    assert profiles.select(first.id) == renamed
    profiles.delete(first.id,confirmed=True)
    with pytest.raises(ProfileNotFound):
        profiles.get(first.id)

@pytest.mark.parametrize('name',['','   ',None,True,123,'x'*101,'line\nname'])
def test_bad_names(storage,name):
    _, profiles, *_ = storage
    with pytest.raises(ValidationError):
        profiles.create(name)

def test_parameterized_name(storage):
    _, profiles, *_ = storage
    name = "Robert'); DROP TABLE profiles;--"
    assert profiles.get(profiles.create(name).id).name == name
    assert len(profiles.list()) == 1

@pytest.mark.parametrize('operation',['get','rename','delete'])
def test_missing_profile(storage,operation):
    _, profiles, *_ = storage
    with pytest.raises(ProfileNotFound):
        if operation == 'get': profiles.get(999)
        elif operation == 'rename': profiles.rename(999,'new')
        else: profiles.delete(999,confirmed=True)
