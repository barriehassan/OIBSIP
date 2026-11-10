import tkinter as tk
from datetime import timedelta
from dataclasses import replace
from app.services.weather_service import LocationWeatherResult
from test_enhancements_widgets import app


def labels(widget):
    output = []
    for child in widget.winfo_children():
        try:
            output.append(str(child.cget("text")))
        except (ValueError, TypeError, AttributeError, tk.TclError):
            pass
        output.extend(labels(child))
    return output


def test_city_snapshot_age_and_failure_visible(app, bundle, now):
    old = replace(bundle, retrieved_at=now - timedelta(hours=2))
    app.controller.state.cities[bundle.location] = LocationWeatherResult(
        bundle.location, old
    )
    app.render()
    app.update()
    assert any("Cached · 15 Jan 12:20" in x for x in labels(app.cities))
    app.controller.state.cities[bundle.location] = LocationWeatherResult(
        bundle.location, bundle, RuntimeError("offline")
    )
    app.render()
    app.update()
    assert any("Cached · 15 Jan 14:20" in x for x in labels(app.cities))


def test_close_cancels_interpreter_timers_before_reopen(app):
    from app.ui.controller import Controller
    from app.ui.window import SkyCastWindow
    from test_ui_controller import Workers, Backend
    app.after(500, lambda: None)
    assert app.tk.call("after", "info")
    app.close()
    assert not app.tk.call("after", "info")
    reopened=SkyCastWindow(Controller(Backend(), Workers()),remote_icons=False)
    try:
        reopened.update()
        assert reopened.winfo_exists()
    finally:
        reopened.close()
