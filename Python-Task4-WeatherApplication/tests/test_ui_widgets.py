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
    assert window.location.cget("text") == "London, United Kingdom"
    window.tab_changed("Today")
    window.update()
    assert (
        window.card_strip.winfo_children()[0].temperature_label.cget("text") == "47°F"
    )
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
    if width >= 1366:
        last = window.card_strip.winfo_children()[-1]
        assert (
            last.winfo_x() + last.winfo_width()
            <= window.card_strip._parent_canvas.winfo_width()
        )
    # Seven real cards remain reachable in a horizontal scrolling strip.
    assert len(window.card_strip.winfo_children()) == 7
    window.toggle_details()
    window.update()
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
        assert window.search_button.winfo_width() >= 40
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


def test_reference_header_and_map_composition(window):
    window.reflow()
    window.update()
    assert window.location.winfo_rootx() < window.search_group.winfo_rootx()
    assert abs(window.location.winfo_rooty() - window.entry.winfo_rooty()) < 18
    assert window.search_group.winfo_width() < 600
    assert not window.detail_panel.winfo_ismapped()
    assert window.map.winfo_rooty() < 530
    assert (
        window.map.winfo_rooty() + window.map.winfo_height()
        < window.winfo_rooty() + 900
    )
    assert window.map.exploration.winfo_ismapped()
    assert window.menu_button.winfo_width() == window.menu_button.winfo_height()


def test_map_controls_transform_and_reset(window):
    view = window.map
    start = view.viewport()
    view.controls["plus"].invoke()
    window.update()
    assert view.viewport()[2] > start[2]
    view.controls["layers"].invoke()
    assert not view.show_markers
    assert not view.find_withtag("pin0")
    view.controls["layers"].invoke()
    assert view.find_withtag("pin0")
    view.controls["locate"].invoke()
    assert view.center == (view.active.longitude, view.active.latitude)
    view.controls["reset"].invoke()
    assert view.zoom == 1.0
    assert view.viewport() == start


def test_details_can_be_opened_and_closed_without_network(window):
    window.menu_button.invoke()
    window.update()
    assert window.detail_panel.winfo_ismapped()
    assert window.stats.winfo_height() > 40
    window.forecast_button.invoke()
    window.update()
    assert not window.detail_panel.winfo_ismapped()
    assert not window.controller.workers.pending


def test_theme_switch_keeps_weather_and_units(window):
    original = window.controller.state.bundle
    window.add_city()
    window.sun_button.invoke()
    window.update()
    assert window.light_mode
    assert window.cget("fg_color") == "#dce3e8"
    assert window.page._parent_canvas.cget("bg") == "#f5f7fb"
    assert all(
        label.cget("text_color") == "#17212c"
        for label in window.city_temperature_labels
    )
    assert window.controller.state.bundle is original
    window.unit_changed("°F")
    window.moon_button.invoke()
    window.update()
    assert not window.light_mode
    assert window.cget("fg_color") == "#292929"
    assert window.controller.state.unit == "°F"
    assert not window.controller.workers.pending


def test_maximized_scaled_forecast_fits_and_map_uses_window_height(bundle, location, now):
    if not os.environ.get("DISPLAY") and os.name != "nt":
        pytest.skip("A display is required for genuine Tk widget tests")
    import customtkinter as ctk

    ctk.set_widget_scaling(1.25)
    window = None
    try:
        from app.ui.window import SkyCastWindow
        controller = Controller(Backend(), Workers(), clock=lambda: now)
        ready(controller, bundle, location)
        window = SkyCastWindow(controller, remote_icons=False)
        window.geometry("2048x1252")
        window.update()
        window.reflow()
        window.update()
        cards = window.card_strip.winfo_children()
        canvas = window.card_strip._parent_canvas
        assert len(cards) == 7
        assert cards[-1].winfo_x() + cards[-1].winfo_width() <= canvas.winfo_width()
        assert cards[0].winfo_width() > cards[1].winfo_width() * 1.8
        assert window.map.winfo_height() > 390
        assert window.cities.winfo_width() > window.page.winfo_width() * 0.19
        assert (
            abs(
                window.search_group.winfo_rootx()
                + window.search_group.winfo_width() / 2
                - (window.header.winfo_rootx() + window.header.winfo_width() * 0.52)
            )
            < 6
        )
    finally:
        if window is not None:
            window.close()
        ctk.set_widget_scaling(1)
