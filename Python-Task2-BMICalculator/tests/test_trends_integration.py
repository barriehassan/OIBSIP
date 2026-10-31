"""TkAgg integration: isolated profiles, refresh, periods and figure lifecycle."""
from datetime import datetime, timezone, timedelta
import os
import pytest
from app.ui.bootstrap import create_controller
from app.ui.window import BMIWindow
from matplotlib._pylab_helpers import Gcf

@pytest.fixture
def app(tmp_path):
    if not os.environ.get('DISPLAY') and os.name!='nt':pytest.skip('Graphical display required.')
    window=BMIWindow(create_controller(tmp_path/'trends.sqlite3'))
    errors=[];window.report_callback_exception=lambda *error:errors.append(error)
    window.update()
    yield window
    charts=[window.preview_chart]
    if window.trends_page:charts += [window.trends_page.bmi_chart,window.trends_page.weight_chart]
    window.destroy()
    assert all(chart.closed and chart.figure.axes==[] for chart in charts)
    assert not Gcf.get_all_fig_managers()
    assert errors==[]


def test_trends_page_creation_and_reuse(app):
    app.navigate('Trends');app.update();view=app.trends_page
    assert view.data.statistics.count==0
    figure=view.bmi_chart.figure;canvas=view.bmi_chart.canvas
    for _ in range(3):
        app.navigate('Calculator');app.navigate('Trends');app.update()
    assert app.trends_page is view and view.bmi_chart.figure is figure and view.bmi_chart.canvas is canvas
    assert len(view.bmi_chart.figure.axes)==1


def test_save_delete_switch_refresh(app,monkeypatch):
    a=app.controller.create_profile('A');app.reload_profiles()
    app.height.set('175');app.weight.set('70');app.calculate();app.save_result();app.update()
    record=app.controller.saved
    assert app.preview_chart.data.statistics.count==1
    app.navigate('Trends');app.update()
    assert app.trends_page.data.records[0].id==record.id
    b=app.controller.profiles.create('B')
    app.select_trends_profile(b.id);app.update()
    assert app.trends_page.data.statistics.count==0
    assert app.preview_chart.data.records==()
    app.select_trends_profile(a.id);app.update()
    assert app.trends_page.data.statistics.count==1
    monkeypatch.setattr('app.ui.window.messagebox.askyesno',lambda *a,**k:True)
    app.delete_measurement(record.id);app.update()
    assert app.trends_page.data.statistics.count==0 and app.preview_chart.data.records==()
    app.delete_profile(a.id);app.update()
    assert app.controller.profile_id==b.id
    assert app.trends_page.data.profile_id==b.id


def test_period_selector_and_stats(app):
    p=app.controller.create_profile('A');app.reload_profiles()
    now=datetime.now(timezone.utc)
    app.controller.measurements.save(p.id,80,1.75,now-timedelta(days=200))
    app.controller.measurements.save(p.id,75,1.75,now-timedelta(days=5))
    app.controller.measurements.save(p.id,73,1.75,now-timedelta(days=1))
    app.refresh_summary();app.navigate('Trends');app.update()
    view=app.trends_page;view.set_period('Last 30 days');app.update()
    assert view.data.statistics.count==2
    assert view.stat_values['Weight Δ vs previous'].cget('text')=='-2.00 kg'
    assert view.stat_values['Weight Δ vs first'].cget('text')=='-2.00 kg'
    view.set_period('All records');app.update()
    assert view.data.statistics.weight_change_from_first==-7
    view.threshold_toggle.deselect();view._threshold_changed();app.update()
    assert len(view.bmi_chart.axes.lines)==1
    app.change_preview_period('All records');app.update()
    assert app.preview_chart.data.statistics.count==3


def test_storage_failure_clears_old_charts(app,monkeypatch):
    from app.database.errors import DatabaseError
    p=app.controller.create_profile('A');app.reload_profiles()
    app.controller.measurements.save(p.id,70,1.75)
    app.refresh_summary();app.navigate('Trends');app.update()
    def fail(*args,**kwargs):raise DatabaseError('Unavailable')
    monkeypatch.setattr(app.controller.analytics,'snapshot',fail)
    messages=[];app.trends_page.on_error=messages.append
    app.trends_page.refresh();app.update()
    assert app.trends_page.data.records==()
    assert len(app.trends_page.bmi_chart.axes.lines)==0
    assert len(messages)==1


def test_fingerprint_avoids_unnecessary_redraw(app,monkeypatch):
    p=app.controller.create_profile('A');app.reload_profiles()
    app.controller.measurements.save(p.id,70,1.75)
    app.refresh_summary();app.navigate('Trends');app.update()
    chart=app.trends_page.bmi_chart
    calls=[];monkeypatch.setattr(chart.canvas,'draw_idle',lambda:calls.append(1))
    app.trends_page.refresh()
    assert calls==[]


def test_short_window_chart_layout(app):
    app.geometry('1240x860');app.navigate('Trends');app.update()
    assert app.trends_page.bmi_chart.winfo_width()>400
    assert app.trends_page.bmi_chart.winfo_height()>200
    app.viewport._parent_canvas.yview_moveto(1);app.update()
    assert app.trends_page.footnote.winfo_rooty()<app.winfo_rooty()+app.winfo_height()


def test_preview_filter_empty_and_single_marker(app):
    p=app.controller.create_profile('A');app.reload_profiles()
    old=app.controller.measurements.save(p.id,70,1.75,datetime.now(timezone.utc)-timedelta(days=400))
    app.refresh_summary();app.update()
    assert app.preview_chart.data.records==()
    app.change_preview_period('All records');app.update()
    assert app.preview_chart.data.records==(old,)
    assert app.preview_chart.axes.lines[0].get_linestyle()=='None'


def test_storage_failure_clears_calculator_summaries(app,monkeypatch):
    from app.database.errors import DatabaseError
    p=app.controller.create_profile('A');app.reload_profiles()
    app.controller.measurements.save(p.id,70,1.75);app.refresh_summary();app.update()
    def fail(*args,**kwargs):raise DatabaseError('Unavailable')
    monkeypatch.setattr(app.controller.analytics,'snapshot',fail)
    messages=[];monkeypatch.setattr(app,'show_error',messages.append)
    app.refresh_summary();app.update()
    assert all(value.cget('text')=='—' for value in app.summary_values)
    assert app.preview_chart.data.records==()
    assert len(messages)==1
