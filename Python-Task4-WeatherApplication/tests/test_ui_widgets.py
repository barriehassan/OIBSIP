"""Real widget checks under a desktop display or Linux Xvfb. No live HTTP."""

import os
from datetime import timedelta
import pytest
from app.ui.controller import Controller
from test_ui_controller import Workers, Backend, ready


@pytest.fixture
def window(bundle, location, now):
    if not os.environ.get("DISPLAY") and os.name != "nt":
        pytest.skip("A display is required for genuine Tk widget tests")
    from app.ui.window import SkyCastWindow

    controller = Controller(Backend(), Workers(), clock=lambda: now)
    ready(controller, bundle, location)
    errors = []
    app = SkyCastWindow(controller, remote_icons=False)
    app.report_callback_exception = lambda *args: errors.append(args)
    app.geometry("1440x900")
    app.update()
    yield app
    app.close()
    assert not errors, errors


def test_widgets_render_actual_bundle(window):
    assert len(window.card_strip.winfo_children()) == 7
    assert len(window.hourly.slots.winfo_children()) == 6
    assert len(window.rain.rows) == 6
    assert window.map.base is not None
    assert len(window.map.markers) == 1
    assert "London" in window.location.cget("text")
    assert window.controller.state.bundle.current.temperature_c == 8.4


def test_tab_and_unit_buttons(window, now):
    window.tab_buttons["Tomorrow"].invoke()
    window.update()
    assert window.controller.state.selected_date == now.date() + timedelta(days=1)
    assert window.rain.rows[0].forecast_at.hour == 6
    window.unit_changed("°F")
    window.update()
    assert window.controller.state.unit == "°F"
    assert window.unit.get() == "°F"
    assert "47°F" in window.location.cget("text")
    assert not window.controller.workers.pending


def test_card_select_and_city(window, now):
    window.card_strip.winfo_children()[3].select.invoke()
    window.update()
    assert window.controller.state.selected_date == now.date() + timedelta(days=3)
    window.add_button.invoke()
    window.update()
    assert len(window.controller.state.cities) == 1
    assert len(window.map.markers) == 1  # shared active/city identity is deduplicated
    window.unit_changed("°F")
    window.update()
    assert (
        window.controller.state.cities[
            next(iter(window.controller.state.cities))
        ].weather.current.temperature_c
        == 8.4
    )


@pytest.mark.parametrize("size", [(1440, 900), (1366, 768), (1024, 700)])
def test_resize_scrolls_instead_of_clipping(window, size):
    width, height = size
    window.geometry(f"{width}x{height}")
    window.update()
    window.reflow()
    window.update()
    assert window.page.winfo_width() > 500
    assert window.search_group.winfo_width() > 300
    assert window.card_strip._parent_canvas.winfo_width() > 400
    assert window.map.winfo_width() > 400
    # Seven real cards remain reachable in a horizontal scrolling strip.
    assert len(window.card_strip.winfo_children()) == 7
    canvas = window.page._parent_canvas
    canvas.yview_moveto(1)
    window.update()
    assert window.stats.winfo_height() > 40


def test_error_and_candidate_dialog(window, location):
    from dataclasses import replace

    window.entry.delete(0, "end")
    window.search_button.invoke()
    window.update()
    assert window.controller.state.failed and "Previous results" in window.status.cget(
        "text"
    )
    candidates = (
        location,
        replace(location, provider_id=2, country="Canada", country_code="CA"),
    )
    window.show_candidates(candidates)
    window.update()
    assert window.dialog.winfo_exists()
    window.cancel()
    window.update()
    assert window.dialog is None


def test_empty_chart_and_missing_map(window):
    window.rain.set_data()
    window.update()
    assert not window.rain.rows
    window.map.base = None
    window.map.redraw()
    window.update()
    texts = [
        window.map.itemcget(item, "text")
        for item in window.map.find_all()
        if window.map.type(item) == "text"
    ]
    assert any("Map asset unavailable" in text for text in texts)


def test_keyboard_activation(window, now):
    window.focus_force()
    button = window.tab_buttons["Tomorrow"]
    button.focus_set()
    window.update()
    button._canvas.event_generate("<Return>")
    window.update()
    assert window.controller.state.selected_date == now.date() + timedelta(days=1)
    window.toggle_unit()
    window.update()
    assert window.controller.state.unit == "°F"
    assert window.unit.get() == "°F"


def test_simulated_125_percent_widget_scaling(window):
    import customtkinter as ctk

    try:
        ctk.set_widget_scaling(1.25)
        window.update()
        window.reflow()
        window.update()
        assert len(window.card_strip.winfo_children()) == 7
        assert window.search_button.winfo_width() > 50
        assert window.page._parent_canvas.winfo_height() > 200
    finally:
        ctk.set_widget_scaling(1)


def test_day_keyboard_focus_survives_render(window, now):
    window.focus_force()
    window.select_day(now.date() + timedelta(days=2))
    window.update()
    selected = window.card_strip.winfo_children()[2].select
    assert window.focus_get() is selected._canvas
    selected._canvas.event_generate("<Right>")
    window.update()
    assert window.controller.state.selected_date == now.date() + timedelta(days=3)
    assert window.focus_get() is window.card_strip.winfo_children()[3].select._canvas


def test_fahrenheit_labels_fit_selected_and_city_cards(window, now):
    window.add_city()
    window.tab_changed("Tomorrow")
    window.unit_changed("°F")
    window.update()
    selected = window.card_strip.winfo_children()[1]
    assert (
        selected.temperature_label.winfo_width()
        >= selected.temperature_label.winfo_reqwidth()
    )
    for label in window.city_temperature_labels:
        assert label.winfo_width() >= label.winfo_reqwidth()
