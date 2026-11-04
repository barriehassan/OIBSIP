"""Complete desktop save/export/delete/reopen workflow with synthetic profiles."""
import os
import time
import tkinter as tk
import pytest
from pypdf import PdfReader
from app.ui.bootstrap import create_controller
from app.ui.window import BMIWindow
from app.core.validator import ValidationError

@pytest.fixture
def desktop(tmp_path):
    if not os.environ.get('DISPLAY') and os.name!='nt':pytest.skip('Graphical display required.')
    app=BMIWindow(create_controller(tmp_path/'release.sqlite3'));errors=[]
    app.report_callback_exception=lambda *error:errors.append(error);app.update()
    yield app
    if app.reports_page and app.reports_page.busy:wait_for_export(app)
    try:
        if app.winfo_exists():app.destroy()
    except tk.TclError:
        pass  # This workflow intentionally closes its original Tcl interpreter.
    assert errors==[]

def wait_for_export(app):
    limit=time.monotonic()+25
    while app.reports_page.busy and time.monotonic()<limit:
        app.update();time.sleep(.02)
    assert not app.reports_page.busy


def test_complete_release_workflow(desktop,tmp_path,monkeypatch):
    app=desktop
    first=app.controller.create_profile('Release QA Alpha');second=app.controller.profiles.create('Release QA Beta')
    app.reload_profiles()
    for weight in ('75','73'):
        app.height.set('175');app.weight.set(weight);app.calculate_button.invoke();app.save_button.invoke();app.update()
    last=app.controller.saved
    assert last.category.value=='Normal'
    for page in ('History','Trends','Dashboard','Reports'):
        app.navigate(page);app.update();assert app.controller.profile_id==first.id
    assert app.dashboard_page.data.statistics.weight_change==-2
    target=tmp_path/'release.pdf'
    monkeypatch.setattr('app.ui.reports_view.filedialog.asksaveasfilename',lambda **k:str(target))
    app.reports_page.generate_button.invoke();app.navigate('Calculator');app.update();wait_for_export(app)
    assert 'Saved report' in app.reports_page.status.cget('text')
    reader=PdfReader(target);text='\n'.join(page.extract_text() for page in reader.pages)
    assert first.name in text and second.name not in text
    assert sum(len(page.images) for page in reader.pages)==2
    app.select_trends_profile(second.id);app.update()
    assert app.preview_chart.data.records==app.trends_page.data.records==app.dashboard_page.data.records==()
    assert '0 records in period' in app.reports_page.summary.cget('text')
    app.select_trends_profile(first.id)
    monkeypatch.setattr('app.ui.window.messagebox.askyesno',lambda *a,**k:True)
    app.delete_measurement(last.id);app.update()
    assert app.dashboard_page.data.statistics.count==1 and len(app.trends_page.data.records)==1
    # Close, then reopen the same temporary database in a new desktop instance.
    app.destroy()
    reopened=BMIWindow(create_controller(tmp_path/'release.sqlite3'))
    try:
        reopened.update()
        assert reopened.controller.history.count(first.id)==1
        assert reopened.controller.history.latest(first.id).weight_kg==75
        assert reopened.controller.history.count(second.id)==0
    finally:reopened.destroy()


def test_invalid_navigation_preserves_selected_page(desktop):
    with pytest.raises(ValidationError):desktop.navigate('Not a page')
    assert desktop.active_page=='Calculator'


def test_long_profile_names_keep_actions_visible(desktop):
    app=desktop;app.geometry('1240x860')
    p=app.controller.create_profile('W'*100);app.reload_profiles();app.refresh_summary()
    for page in ('Profiles','History','Trends','Dashboard','Reports'):
        app.navigate(page);app.update();assert app.controller.profile_id==p.id
    view=app.reports_page
    assert view.generate_button.winfo_width()>250
    assert view.generate_button.winfo_rootx()+view.generate_button.winfo_width()<app.winfo_rootx()+app.winfo_width()
