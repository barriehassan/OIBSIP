"""Release audit regressions; all persistence/export paths are temporary."""
from datetime import datetime, timezone
from pathlib import Path
import socket
import sqlite3
import pytest
from pypdf import PdfReader
from app.core.conversions import feet_inches_to_metres
from app.core.validator import ValidationError
from app.database.connection import Database, default_database_path
from app.database.errors import DatabaseError, InitializationError
from app.database.validation import profile_name
from app.reports.report_models import ReportOptions, ReportError
from app.reports.pdf_generator import generate_pdf
from app.services.report_service import ReportService

@pytest.mark.parametrize('inches',[0,.5,11.99])
def test_huge_imperial_value_is_controlled(inches):
    with pytest.raises(ValidationError):feet_inches_to_metres(10**400,inches)

@pytest.mark.parametrize('character',['\u0085','\u200b','\u202e','\u2028','\u2029','\ud800'])
def test_unicode_profile_controls_rejected(character):
    with pytest.raises(ValidationError):profile_name('First'+character+'Last')

@pytest.mark.parametrize('character',['\u2028','\u2029'])
def test_report_title_line_separators_rejected(character):
    with pytest.raises(ValidationError):ReportOptions(title='First'+character+'Last')


def test_profile_unicode_letters_and_sql_text_preserved(storage):
    _,profiles,measurements,history=storage
    name="Élodie 李'); DROP TABLE profiles; --"
    p=profiles.create(name);measurements.save(p.id,70,1.75)
    assert profiles.get(p.id).name==name
    assert len(profiles.list())==1 and history.count(p.id)==1


def test_failed_rollback_is_controlled_and_connection_closes(storage):
    db,profiles,*_=storage;closed=[]
    class Failure(sqlite3.Connection):
        def commit(self):raise sqlite3.OperationalError('private commit details')
        def rollback(self):raise sqlite3.OperationalError('private recovery details')
        def close(self):super().close();closed.append(True)
    db.factory=lambda *a,**k:sqlite3.connect(*a,**k,factory=Failure)
    with pytest.raises(DatabaseError,match='Database recovery failed') as error:profiles.create('Uncommitted')
    assert 'private' not in str(error.value) and closed==[True]
    db.factory=sqlite3.connect
    assert profiles.list()==[]


def test_failed_close_is_controlled(storage):
    db,profiles,*_=storage
    class Failure(sqlite3.Connection):
        def close(self):super().close();raise sqlite3.OperationalError('private close details')
    db.factory=lambda *a,**k:sqlite3.connect(*a,**k,factory=Failure)
    with pytest.raises(DatabaseError,match='could not be closed') as error:profiles.list()
    assert 'private' not in str(error.value)


def test_failed_close_during_initialize_is_controlled(tmp_path):
    class Failure(sqlite3.Connection):
        def close(self):super().close();raise sqlite3.OperationalError('private close details')
    with pytest.raises(InitializationError):
        Database(tmp_path/'closed.sqlite3',lambda *a,**k:sqlite3.connect(*a,**k,factory=Failure))


@pytest.mark.parametrize('weight,category',[(70,'Underweight'),(90,'Normal'),(110,'Overweight'),(130,'Obese')])
def test_pdf_all_categories_and_offline_operation(storage,tmp_path,monkeypatch,weight,category):
    def blocked(*a,**k):raise AssertionError('Network access is not allowed in this workflow.')
    monkeypatch.setattr(socket.socket,'connect',blocked)
    _,profiles,measurements,history=storage;p=profiles.create('Synthetic QA')
    record=measurements.save(p.id,weight,2)
    data=ReportService(profiles,history).prepare(p.id,ReportOptions(include_charts=False))
    path=generate_pdf(data,tmp_path/'offline.pdf')
    text='\n'.join(page.extract_text() for page in PdfReader(path).pages)
    assert f'{record.bmi_value:.2f} / {category}' in text
    assert record.category.value==category


def test_pdf_does_not_replace_file_created_during_render(storage,tmp_path,monkeypatch):
    from app.reports import pdf_generator
    _,profiles,_,history=storage;p=profiles.create('Race test')
    data=ReportService(profiles,history).prepare(p.id,ReportOptions(include_charts=False))
    path=tmp_path/'target.pdf';original=pdf_generator._build_pdf
    def raced(data,stream):original(data,stream);path.write_bytes(b'Other writer')
    monkeypatch.setattr(pdf_generator,'_build_pdf',raced)
    with pytest.raises(ReportError):generate_pdf(data,path)
    assert path.read_bytes()==b'Other writer'
    assert not list(tmp_path.glob('.bmi-report-*'))


def test_windows_storage_path_selection(tmp_path,monkeypatch):
    monkeypatch.delenv('BMI_INSIGHT_DATA_DIR',raising=False)
    monkeypatch.setattr('app.database.connection.sys.platform','win32')
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path/'User Data'))
    assert default_database_path()==tmp_path/'User Data'/'NOMOLI_FORGE'/'BMI_Insight'/'bmi_insight.sqlite3'
