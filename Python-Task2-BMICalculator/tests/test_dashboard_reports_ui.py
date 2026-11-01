"""Real Tk integration and spawned PDF worker checks; temporary storage only."""
from datetime import datetime, timezone, timedelta
import os
import time
from concurrent.futures import Future
import pytest
from app.ui.bootstrap import create_controller
from app.ui.window import BMIWindow
from app.reports.report_models import ReportError
from pypdf import PdfReader

@pytest.fixture
def app(tmp_path):
    if not os.environ.get('DISPLAY') and os.name!='nt':pytest.skip('Graphical display required.')
    window=BMIWindow(create_controller(tmp_path/'ui.sqlite3'));errors=[]
    window.report_callback_exception=lambda *error:errors.append(error)
    window.update()
    yield window
    if window.reports_page and window.reports_page.busy:
        finish(window)
    window.destroy()
    assert errors==[]

def finish(app):
    deadline=time.monotonic()+25
    while app.reports_page.busy and time.monotonic()<deadline:
        app.update();time.sleep(.02)
    assert not app.reports_page.busy

def populate(app):
    p=app.controller.create_profile('UI verification');app.reload_profiles()
    now=datetime.now(timezone.utc)
    for days,weight in [(60,80),(5,75),(1,73)]:app.controller.measurements.save(p.id,weight,1.75,now-timedelta(days=days))
    app.refresh_summary();return p

def test_dashboard_cards_filter_and_reuse(app):
    populate(app);app.navigate('Dashboard');app.update();view=app.dashboard_page
    assert view.values['Latest BMI'].cget('text')=='23.84'
    assert view.values['Latest Weight'].cget('text')=='73.00 kg'
    assert view.values['Weight Change'].cget('text')=='-2.00 kg'
    view.set_period('Last 30 days');app.update()
    assert view.values['Total Records'].cget('text')=='2'
    assert '3 all time' in view.details['Total Records'].cget('text')
    figure=view.bmi_chart.figure
    app.navigate('Calculator');app.navigate('Dashboard');app.update()
    assert app.dashboard_page is view and view.bmi_chart.figure is figure

def test_all_views_refresh_on_save_delete_and_switch(app,monkeypatch):
    p=populate(app);app.navigate('Dashboard');app.navigate('Reports');app.update()
    app.navigate('Calculator');app.height.set('175');app.weight.set('72');app.calculate();app.save_result();app.update()
    record=app.controller.saved
    assert app.dashboard_page.data.statistics.count==4
    assert '4 records in period' in app.reports_page.summary.cget('text')
    monkeypatch.setattr('app.ui.window.messagebox.askyesno',lambda *a,**k:True)
    app.delete_measurement(record.id);app.update()
    assert app.dashboard_page.data.statistics.count==3
    b=app.controller.profiles.create('Other');app.select_trends_profile(b.id);app.update()
    assert app.dashboard_page.data.records==()
    assert '0 records in period' in app.reports_page.summary.cget('text')
    app.delete_profile(p.id);app.update()
    assert app.dashboard_page.data.profile_id==b.id

def test_delete_selected_profile_clears_every_view(app,monkeypatch):
    p=populate(app);app.navigate('Dashboard');app.navigate('Reports');app.update()
    monkeypatch.setattr('app.ui.window.messagebox.askyesno',lambda *a,**k:True)
    app.delete_profile(p.id);app.update()
    assert app.dashboard_page.data.records==()
    assert app.reports_page.generate_button.cget('state')=='disabled'
    assert 'No profile selected' in app.reports_page.summary.cget('text')

def test_dashboard_empty_single_and_action(app):
    app.navigate('Dashboard');app.update();view=app.dashboard_page
    assert view.state_label.cget('text')=='No measurements recorded yet.'
    view.calculator_button.invoke();assert app.active_page=='Calculator'
    p=app.controller.create_profile('Single');app.reload_profiles()
    app.controller.measurements.save(p.id,70,1.75);app.refresh_summary()
    assert 'One measurement' in view.state_label.cget('text')
    assert view.details['Weight Change'].cget('text')=='No previous measurement available.'

def test_dashboard_minimum_size_scroll(app):
    populate(app);app.geometry('1240x860');app.navigate('Dashboard');app.update();view=app.dashboard_page
    assert view.bmi_chart.winfo_width()>400 and view.bmi_chart.winfo_height()>=250
    app.viewport._parent_canvas.yview_moveto(1);app.update()
    assert view.calculator_button.winfo_rooty()+view.calculator_button.winfo_height()<app.winfo_rooty()+app.winfo_height()

def test_report_ui_validation_and_cancel(app,monkeypatch):
    populate(app);app.navigate('Reports');app.update();view=app.reports_page
    view.period_menu.set('Custom dates');view.generate();assert 'YYYY-MM-DD' in view.status.cget('text')
    view.period_menu.set('All records')
    monkeypatch.setattr('app.ui.reports_view.filedialog.asksaveasfilename',lambda **k:'')
    view.generate();assert not view.busy

def test_real_worker_and_navigation_during_export(app,tmp_path,monkeypatch):
    p=populate(app);app.navigate('Reports');app.update();view=app.reports_page
    target=tmp_path/'worker.pdf'
    monkeypatch.setattr('app.ui.reports_view.filedialog.asksaveasfilename',lambda **k:str(target))
    view.generate();assert view.busy and view.generate_button.cget('state')=='disabled'
    app.navigate('Dashboard');app.update();assert app.active_page=='Dashboard'
    finish(app)
    assert target.read_bytes().startswith(b'%PDF-')
    assert 'Saved report for UI verification' in view.status.cget('text')
    assert any(p.name in page.extract_text() for page in PdfReader(target).pages)

def test_worker_error_feedback(app,monkeypatch):
    populate(app);app.navigate('Reports');app.update();view=app.reports_page
    future=Future();future.set_exception(ReportError('Destination unavailable.'))
    view.future=future;view._poll();assert not view.busy
    assert view.status.cget('text')=='Destination unavailable.'
    assert view.generate_button.cget('state')=='normal'

def test_close_waits_for_active_export(app,monkeypatch):
    populate(app);app.navigate('Reports');app.update();view=app.reports_page
    future=Future();view.future=future;messages=[]
    monkeypatch.setattr('app.ui.window.messagebox.showinfo',lambda *a,**k:messages.append(a))
    app.destroy();assert app.winfo_exists() and messages
    future.set_exception(ReportError('Cancelled test export.'));view._poll()

def test_dashboard_error_clears_stale_records(app,monkeypatch):
    from app.database.errors import DatabaseError
    populate(app);app.navigate('Dashboard');app.update();view=app.dashboard_page
    def fail(*a,**k):raise DatabaseError('Unavailable')
    errors=[];view.on_error=errors.append
    monkeypatch.setattr(view.service,'snapshot',fail)
    view.refresh()
    assert view.data.records==() and view.values['Latest BMI'].cget('text')=='—'
    assert errors
