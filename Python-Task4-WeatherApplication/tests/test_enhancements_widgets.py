import os
from dataclasses import replace
from datetime import timedelta
import pytest
from app.ui.controller import Controller
from app.storage.local import LocalStore
from app.services.voice_service import VoiceService
from test_ui_controller import Workers, Backend, ready
from test_enhancements_voice_ip import Context


@pytest.fixture
def app(tmp_path, bundle, location, now):
    if not os.environ.get("DISPLAY") and os.name != "nt":
        pytest.skip("A display is required")
    from app.ui.window import SkyCastWindow

    store = LocalStore(tmp_path / "user.db")
    c = Controller(Backend(), Workers(), clock=lambda: now)
    ready(c, bundle, location)
    voice = VoiceService(context=Context(), supported=True)
    errors = []
    w = SkyCastWindow(c, remote_icons=False, store=store, voice=voice)
    w.report_callback_exception = lambda *args: errors.append(args)
    w.geometry("1440x900")
    w.update()
    yield w
    w.close()
    assert not errors


def test_favorites_and_voice_location_unit_invalidation(app, location):
    e = app.enhancements
    e.star.invoke()
    e.favorites_button.invoke()
    app.update()
    assert e.store.favorites()[0] == [location]
    assert e.favorite_list.winfo_ismapped()
    assert not e.voice.active
    e.listen.invoke()
    assert e.voice.active
    app.unit_changed("°F")
    assert e.voice.status == "Stopping"
    e.voice.close()
    e.voice = VoiceService(context=Context(), supported=True)
    e.listen.invoke()
    app.choose(replace(location, provider_id=7, name="Other"))
    assert e.voice.status == "Stopping"
    e.remove(location)
    assert e.store.favorites()[0] == []


def test_geolocation_consent_panel_and_cancel(app):
    e = app.enhancements
    assert not app.controller.workers.pending
    e.detect.invoke()
    app.update()
    assert e.consent_panel.winfo_ismapped() and not app.controller.workers.pending
    e.consent_panel.pack_forget()
    e.confirm_detection()
    assert not app.controller.workers.pending
    e.detect.invoke()
    app.update()
    e.confirm_detection()
    assert app.controller.state.loading and "main" in app.controller.workers.pending
    app.cancel()
    assert not app.controller.workers.pending


def test_chart_reuses_canvas_and_breaks_missing_hours(app, bundle, now):
    e = app.enhancements
    app.toggle_details()
    app.update()
    chart = e.chart
    ident = str(chart)
    row = bundle.hourly_forecasts[0]
    chart.set_data(
        (row, replace(row, forecast_at=row.forecast_at + timedelta(hours=2))),
        "°C",
        "UTC",
    )
    assert len(chart.find_withtag("point")) == 2
    assert not chart.find_withtag("segment")
    chart.set_data(
        (row, replace(row, forecast_at=row.forecast_at + timedelta(hours=1))),
        "°C",
        "UTC",
    )
    assert len(chart.find_withtag("segment")) == 1
    for _ in range(10):
        app.unit_changed("°F")
        app.update()
    assert app.enhancements.chart is chart and str(chart) == ident
    chart.set_data((), "°C", "UTC")
    assert not chart.find_withtag("point")


def test_cached_status_visible_without_details(app, bundle):
    app.controller.state.cache_source = "stale cache"
    app.controller.state.offline = True
    app.render()
    app.update()
    assert app.enhancements.indicator.winfo_ismapped()
    assert "cache" in app.enhancements.indicator.cget("text")
    assert "Connection unavailable" in app.enhancements.indicator.cget("text")
    assert not app.detail_panel.winfo_ismapped()
