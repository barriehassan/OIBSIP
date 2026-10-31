import sqlite3
import pytest
from app.database.connection import Database, default_database_path
from app.database.errors import DatabaseError, InitializationError, IntegrityError

def test_schema(storage):
    db, *_ = storage
    with db.connection() as c:
        assert c.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert c.execute("PRAGMA user_version").fetchone()[0] == 1
        assert {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")} >= {"profiles", "bmi_records"}
        assert c.execute("PRAGMA index_list(bmi_records)").fetchone()[1] == "idx_bmi_profile_time"
    db.initialize()

def test_rollback(storage):
    db, profiles, *_ = storage
    with pytest.raises(IntegrityError):
        with db.connection(write=True) as c:
            c.execute("INSERT INTO profiles(name,created_at) VALUES ('temporary','time')")
            c.execute("INSERT INTO profiles(name,created_at) VALUES ('','time')")
    assert profiles.list() == []

def test_arbitrary_failure_rollback(storage):
    db, profiles, *_ = storage
    with pytest.raises(RuntimeError):
        with db.connection(write=True) as c:
            c.execute("INSERT INTO profiles(name,created_at) VALUES ('temporary','time')")
            raise RuntimeError()
    assert profiles.list() == []

def test_foreign_key(storage):
    db, *_ = storage
    with pytest.raises(IntegrityError):
        with db.connection(write=True) as c:
            c.execute("INSERT INTO bmi_records(profile_id,weight_kg,height_m,bmi_value,category,measured_at) VALUES (999,70,1.75,23,'Normal','time')")

@pytest.mark.parametrize("value", [0,-1,float('inf'),float('-inf'),float('nan'),'invalid'])
@pytest.mark.parametrize("column", ["weight_kg","height_m","bmi_value"])
def test_numeric_constraints(storage,value,column):
    db, profiles, *_ = storage
    profile = profiles.create("Local")
    values = dict(weight_kg=70,height_m=1.75,bmi_value=23)
    values[column] = value
    with pytest.raises(IntegrityError):
        with db.connection(write=True) as c:
            c.execute("INSERT INTO bmi_records(profile_id,weight_kg,height_m,bmi_value,category,measured_at) VALUES (?,?,?,?,?,?)",(profile.id,values['weight_kg'],values['height_m'],values['bmi_value'],'Normal','time'))

def test_reopen(storage):
    db, profiles, service, _ = storage
    profile = profiles.create("Stored")
    record = service.save(profile.id,70,1.75)
    from app.database.measurement_repository import MeasurementRepository
    assert MeasurementRepository(Database(db.path)).get(profile.id,record.id) == record

def test_inaccessible(tmp_path):
    blocker = tmp_path / 'file'
    blocker.write_text('not a directory')
    with pytest.raises(InitializationError):
        Database(blocker / 'db')
    with pytest.raises(InitializationError):
        Database(tmp_path)  # directory cannot be opened as a DB

def test_read_error(storage):
    db, *_ = storage
    with pytest.raises(DatabaseError,match="Database operation failed"):
        with db.connection() as c:
            c.execute('SELECT * FROM missing_table')

def test_future_version(storage):
    db, *_ = storage
    with db.connection(write=True) as c:
        c.execute('PRAGMA user_version=99')
    with pytest.raises(InitializationError):
        Database(db.path)

def test_override(monkeypatch,tmp_path):
    monkeypatch.setenv('BMI_INSIGHT_DATA_DIR',str(tmp_path))
    assert default_database_path() == tmp_path/'bmi_insight.sqlite3'

def test_connection_closed(storage):
    db, *_ = storage
    with db.connection() as c:
        pass
    with pytest.raises(sqlite3.ProgrammingError):
        c.execute('SELECT 1')

def test_factory_failure(tmp_path):
    def denied(*args,**kwargs):
        raise PermissionError('private details')
    with pytest.raises(InitializationError,match='Could not initialize'):
        Database(tmp_path/'db',connection_factory=denied)

def test_failed_commit_rolls_back(storage):
    db, profiles, *_ = storage
    class FailingCommit(sqlite3.Connection):
        def commit(self):
            raise sqlite3.OperationalError('simulated commit failure')
    db.factory = lambda *a, **kw: sqlite3.connect(*a, **kw, factory=FailingCommit)
    with pytest.raises(DatabaseError): profiles.create('Not persisted')
    db.factory = sqlite3.connect
    assert profiles.list() == []

def test_read_and_write_permission_errors(storage):
    db, profiles, *_ = storage
    def denied(*args,**kwargs):
        raise PermissionError('simulated storage denial')
    db.factory = denied
    with pytest.raises(DatabaseError): profiles.list()
    with pytest.raises(DatabaseError): profiles.create('Blocked')
