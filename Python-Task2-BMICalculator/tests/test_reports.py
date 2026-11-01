from dataclasses import replace
from datetime import date, datetime, timezone, timedelta
from io import BytesIO
from pathlib import Path
import pytest
from pypdf import PdfReader
from app.core.validator import ValidationError
from app.services.report_service import ReportService
from app.reports.report_models import ReportOptions, ReportData, ReportError, safe_filename
from app.reports.pdf_generator import generate_pdf, chart_image, DISCLAIMER

NOW=datetime(2026,11,1,12,tzinfo=timezone.utc)

@pytest.fixture
def reporting(storage):
    _,profiles,measurements,history=storage
    a=profiles.create('Export <A> & Élodie');b=profiles.create('PRIVATE_OTHER_PROFILE')
    measurements.save(a.id,70,1.75,NOW-timedelta(days=60))
    measurements.save(a.id,73,1.75,NOW-timedelta(days=1))
    measurements.save(b.id,199,2,NOW)
    return ReportService(profiles,history),a,b

def extract(path):
    reader=PdfReader(path)
    return reader,'\n'.join(page.extract_text() for page in reader.pages)

def test_pdf_profile_values_and_charts(reporting,tmp_path):
    service,a,b=reporting;data=service.prepare(a.id,ReportOptions(),NOW)
    path=generate_pdf(data,tmp_path/'report.pdf')
    assert path.read_bytes().startswith(b'%PDF-')
    reader,text=extract(path)
    assert a.name in text and b.name not in text and '199.00' not in text
    assert '23.84' in text and 'Normal' in text and '70.00' in text
    assert 'adults aged 20 and older' in text
    assert 'screening measure, not a medical diagnosis' in text
    assert sum(len(page.images) for page in reader.pages)==2
    assert len(reader.pages)>=3

def test_custom_inclusive_dates_and_precision(reporting):
    service,a,b=reporting
    opts=ReportOptions(period='Custom dates',start_date=date(2026,10,31),end_date=date(2026,10,31))
    data=service.prepare(a.id,opts,NOW)
    assert len(data.analytics.records)==1
    assert data.analytics.records[0].bmi_value==pytest.approx(73/1.75**2)
    assert data.analytics.start.hour==0 and data.analytics.end.hour==23
    assert 'inclusive UTC' in data.period_label

def test_preset_filter_excludes_old_record(reporting,tmp_path):
    service,a,b=reporting
    data=service.prepare(a.id,ReportOptions(period='Last 30 days'),NOW)
    assert len(data.analytics.records)==1 and data.all_time_count==2
    _,text=extract(generate_pdf(data,tmp_path/'filtered.pdf'))
    assert '70.00' not in text and '73.00' in text
    assert 'One measurement' in text

def test_custom_day_edges(storage):
    _,profiles,measurements,history=storage;p=profiles.create('Edges')
    for stamp in [datetime(2026,1,1,tzinfo=timezone.utc),datetime(2026,1,1,23,59,59,999999,tzinfo=timezone.utc),datetime(2026,1,2,tzinfo=timezone.utc)]:
        measurements.save(p.id,70,1.75,stamp)
    data=ReportService(profiles,history).prepare(p.id,ReportOptions(period='Custom dates',start_date=date(2026,1,1),end_date=date(2026,1,1)))
    assert len(data.analytics.records)==2

@pytest.mark.parametrize('kwargs',[{'title':''},{'title':'x'*101},{'title':'bad\nname'},
    {'include_history':1},{'include_charts':'yes'},{'period':'invalid'},
    {'period':'Custom dates'},{'period':'Custom dates','start_date':date(2026,2,2),'end_date':date(2026,1,1)},
    {'start_date':date(2026,1,1)},{'period':'Custom dates','start_date':'2026-01-01','end_date':date(2026,1,1)}])
def test_invalid_options(kwargs):
    with pytest.raises(ValidationError):ReportOptions(**kwargs)

def test_empty_report(storage,tmp_path):
    _,profiles,_,history=storage;p=profiles.create('Empty')
    data=ReportService(profiles,history).prepare(p.id,ReportOptions())
    reader,text=extract(generate_pdf(data,tmp_path/'empty.pdf'))
    assert 'No measurements recorded yet.' in text
    assert sum(len(page.images) for page in reader.pages)==0

def test_long_history_paginates(storage,tmp_path):
    _,profiles,measurements,history=storage;p=profiles.create('Pagination test')
    for i in range(160):measurements.save(p.id,70+i/100,1.75,NOW-timedelta(days=160-i))
    data=ReportService(profiles,history).prepare(p.id,ReportOptions(include_charts=False),NOW)
    reader,text=extract(generate_pdf(data,tmp_path/'long.pdf'))
    history_pages=[page for page in reader.pages if 'Weight (kg)' in page.extract_text()]
    assert len(history_pages)>=4
    assert all('Height (m)' in page.extract_text() and 'Category' in page.extract_text() for page in history_pages)
    assert '71.59' in text

def test_excluded_sections(reporting,tmp_path):
    service,a,_=reporting
    data=service.prepare(a.id,ReportOptions(include_history=False,include_charts=False),NOW)
    reader,text=extract(generate_pdf(data,tmp_path/'summary.pdf'))
    assert 'Measurement history' not in text and 'Measurement trends' not in text
    assert not any(page.images for page in reader.pages)

@pytest.mark.parametrize('destination',['missing/report.pdf','report.txt',''])
def test_invalid_output_paths(reporting,tmp_path,destination):
    service,a,_=reporting
    with pytest.raises(ReportError):generate_pdf(service.prepare(a.id,ReportOptions()),tmp_path/destination)

def test_overwrite_requires_explicit_permission(reporting,tmp_path):
    service,a,_=reporting;path=tmp_path/'existing.pdf';path.write_bytes(b'original')
    data=service.prepare(a.id,ReportOptions(include_charts=False))
    with pytest.raises(ReportError):generate_pdf(data,path)
    assert path.read_bytes()==b'original'
    generate_pdf(data,path,overwrite=True)
    assert path.read_bytes().startswith(b'%PDF-')

def test_failed_render_preserves_existing_and_cleans_stage(reporting,tmp_path,monkeypatch):
    service,a,_=reporting;path=tmp_path/'existing.pdf';path.write_bytes(b'original')
    def fail(data,stream):stream.write(b'partial');raise RuntimeError('sensitive raw detail')
    monkeypatch.setattr('app.reports.pdf_generator._build_pdf',fail)
    with pytest.raises(ReportError,match='could not be saved') as error:
        generate_pdf(service.prepare(a.id,ReportOptions()),path,overwrite=True)
    assert 'sensitive' not in str(error.value)
    assert path.read_bytes()==b'original' and sorted(p.name for p in tmp_path.iterdir())==['data','existing.pdf']

def test_permission_error_controlled(reporting,tmp_path,monkeypatch):
    service,a,_=reporting
    def denied(*a,**k):raise PermissionError('private path')
    monkeypatch.setattr('app.reports.pdf_generator.tempfile.NamedTemporaryFile',denied)
    with pytest.raises(ReportError):generate_pdf(service.prepare(a.id,ReportOptions()),tmp_path/'out.pdf')
    assert not (tmp_path/'out.pdf').exists()

def test_cross_profile_model_rejected(reporting):
    service,a,b=reporting;data=service.prepare(a.id,ReportOptions())
    with pytest.raises(ValidationError):replace(data,profile=b)

def test_snapshot_does_not_change_after_profile_deletion(reporting,storage,tmp_path):
    service,a,_=reporting;data=service.prepare(a.id,ReportOptions(include_charts=False))
    storage[1].delete(a.id,confirmed=True)
    assert generate_pdf(data,tmp_path/'snapshot.pdf').exists()

def test_safe_filename():
    name=safe_filename('../CON: / unsafe ? * '+('a'*100),NOW)
    assert '/' not in name and ':' not in name and len(name)<85 and name.endswith('.pdf')

def test_chart_png_and_cleanup(reporting):
    from matplotlib._pylab_helpers import Gcf
    service,a,_=reporting;data=service.prepare(a.id,ReportOptions()).analytics
    with chart_image(data,'bmi') as stream:assert stream.read(8)==b'\x89PNG\r\n\x1a\n'
    assert not Gcf.get_all_fig_managers()

def test_tie_order_deterministic(storage):
    _,profiles,measurements,history=storage;p=profiles.create('Tie')
    first=measurements.save(p.id,75,1.75,NOW);last=measurements.save(p.id,73,1.75,NOW)
    data=ReportService(profiles,history).prepare(p.id,ReportOptions(),NOW)
    assert data.analytics.records==(first,last) and data.analytics.statistics.weight_change==-2
