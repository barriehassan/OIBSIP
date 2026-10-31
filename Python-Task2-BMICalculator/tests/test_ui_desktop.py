"""Real-widget smoke tests. Run with a graphical display; use only temp storage."""
import os
import tkinter as tk
from types import SimpleNamespace
import pytest
from app.ui.bootstrap import create_controller
from app.ui.window import BMIWindow

@pytest.fixture
def window(tmp_path):
    if not os.environ.get('DISPLAY') and os.name!='nt':pytest.skip('A graphical display is required.')
    app=BMIWindow(create_controller(tmp_path/'ui.sqlite3'))
    errors=[]
    app.report_callback_exception=lambda *error:errors.append(error)
    app.update()
    yield app
    app.destroy()
    assert errors==[]


def test_empty_screen_and_actual_calculation(window):
    assert window.summary_values[1].cget('text')=='0'
    assert window.gauge.result is None
    assert window.save_button.cget('state')=='disabled'
    profile=window.controller.create_profile('Smoke')
    window.reload_profiles()
    window.height.set('175');window.weight.set('70')
    window.calculate_button.invoke();window.update()
    assert window.gauge.result.formatted_bmi=='22.86'
    assert window.save_button.cget('state')=='normal'
    window.save_button.invoke();window.update()
    assert window.controller.history.count(profile.id)==1
    assert window.save_button.cget('state')=='disabled'
    assert window.summary_values[0].cget('text')=='70 kg'
    window.weight.set('71');window.update()
    assert window.gauge.result is None
    assert window.save_button.cget('state')=='disabled'


def test_validation_feedback_and_reset(window):
    window.height.set('wrong');window.weight.set('70')
    window.calculate();window.update()
    assert 'valid number' in window.status.get()
    assert window.controller.result is None
    window.reset()
    assert window.height.get()==window.weight.get()==''


def test_navigation_and_minimum_layout(window):
    window.geometry('1240x860');window.update()
    for page in ['Profiles','History','Trends','Dashboard','Reports','Calculator']:
        window.nav_buttons[page].invoke();window.update()
        assert window.active_page==page
    assert window.gauge.winfo_width()>180
    assert window.gauge.winfo_height()>140
    assert window.calculate_button.winfo_ismapped()
    assert window.trend_note.winfo_ismapped()


def test_dialog_profile_lifecycle_and_delete_cancellation(window,monkeypatch):
    monkeypatch.setattr('app.ui.window.ctk.CTkInputDialog',lambda **kwargs:SimpleNamespace(get_input=lambda:'Local'))
    window.new_profile();window.update()
    profile=window.controller.profiles.list()[0]
    window.height.set('175');window.weight.set('70');window.calculate();window.save_result()
    monkeypatch.setattr('app.ui.window.messagebox.askyesno',lambda *args,**kwargs:False)
    window.delete_profile(profile.id)
    assert window.controller.history.count(profile.id)==1
    monkeypatch.setattr('app.ui.window.ctk.CTkInputDialog',lambda **kwargs:SimpleNamespace(get_input=lambda:'Renamed'))
    window.rename_profile(profile.id)
    assert window.controller.profiles.get(profile.id).name=='Renamed'
    monkeypatch.setattr('app.ui.window.messagebox.askyesno',lambda *args,**kwargs:True)
    window.delete_profile(profile.id);window.update()
    assert window.controller.profiles.list()==[]
    assert window.controller.profile_id is None


def test_history_profile_switch_and_record_delete(window,monkeypatch):
    a=window.controller.create_profile('A')
    window.height.set('175');window.weight.set('70');window.calculate();window.save_result()
    record=window.controller.saved
    b=window.controller.profiles.create('B');window.reload_profiles()
    window._select_from_page(b.id);window.navigate('History');window.update()
    assert window.controller.summary().count==0
    window._select_from_page(a.id);window.navigate('History');window.update()
    monkeypatch.setattr('app.ui.window.messagebox.askyesno',lambda *args,**kwargs:True)
    window.delete_measurement(record.id);window.update()
    assert window.controller.history.count(a.id)==0


def test_failed_save_shows_controlled_feedback(window,monkeypatch):
    from app.database.errors import DatabaseError
    window.controller.create_profile('A');window.reload_profiles()
    window.height.set('175');window.weight.set('70');window.calculate()
    def fail(*args,**kwargs):raise DatabaseError('Storage unavailable.')
    monkeypatch.setattr(window.controller.measurements,'save',fail)
    window.save_result();window.update()
    assert window.status.get()=='Storage unavailable.'
    assert window.save_button.cget('state')=='normal'


def test_short_window_can_scroll_to_actions(window):
    window.geometry('1240x860');window.update()
    window.viewport._parent_canvas.yview_moveto(1.0);window.update()
    bottom=window.calculate_button.winfo_rooty()+window.calculate_button.winfo_height()
    assert bottom <= window.winfo_rooty()+window.winfo_height()
    assert window.calculate_button.winfo_width()>250


def test_extreme_supported_bmi_fits_gauge(window):
    window.height.set('30');window.weight.set('500');window.calculate();window.update()
    assert window.controller.result.formatted_bmi=='5555.56'
    box=window.gauge.bbox('bmi_value')
    assert box[0]>=0 and box[2]<=window.gauge.winfo_width()
