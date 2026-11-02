"""Capture real GUI pixels; --live fetches forecasts for three explicitly resolved cities.
Default: labeled offline fixture. Never invoked by ordinary tests.
"""

import argparse, json, sys, time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import ImageGrab
from app.ui.controller import Controller, Backend
from app.ui.window import SkyCastWindow
from app.ui.presentation import local_today
from app.core.models import Location
from app.providers.open_meteo import OpenMeteoWeather
from app.services.weather_service import LocationWeatherResult


def run(output, live=False):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    backend = Backend()
    bundles = []
    if live:
        # Explicit metadata resolved through Open-Meteo geocoding on 2026-11-02.
        # Reuse these verified choices; no silent first-result selection.
        locations = [
            Location(
                2643743,
                "London",
                "England",
                "United Kingdom",
                "GB",
                51.50853,
                -0.12574,
                "Europe/London",
            ),
            Location(
                1816670,
                "Beijing",
                "Beijing Municipality",
                "China",
                "CN",
                39.9075,
                116.39723,
                "Asia/Shanghai",
            ),
            Location(
                2409306,
                "Freetown",
                "Western Area",
                "Sierra Leone",
                "SL",
                8.48714,
                -13.2356,
                "Africa/Freetown",
            ),
        ]
        for location in locations:
            bundles.append(backend.weather(location))
        now = lambda: datetime.now(timezone.utc)
    else:
        payload = json.loads(
            (
                Path(__file__).resolve().parents[1] / "tests/fixtures/forecast.json"
            ).read_text()
        )
        clock = datetime(2026, 1, 15, 14, 20, tzinfo=timezone.utc)
        loc = Location(
            2643743,
            "London",
            "England",
            "United Kingdom",
            "GB",
            51.50853,
            -0.12574,
            "Europe/London",
        )
        bundles = [OpenMeteoWeather.normalize(payload, loc, clock)]
        now = lambda: clock
    controller = Controller(clock=now)
    controller.state.bundle = bundles[0]
    controller.state.selected_date = local_today(bundles[0], now())
    controller.state.status = (
        "Live API smoke · downloaded this session"
        if live
        else "OFFLINE TEST FIXTURE · synthetic weather · not live"
    )
    for b in bundles:
        controller.state.cities[b.location] = LocationWeatherResult(b.location, b)
    app = SkyCastWindow(controller, remote_icons=live)
    errors = []
    app.report_callback_exception = lambda *args: errors.append(str(args))

    def settle(seconds=0.7):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            app.update()
            time.sleep(0.02)

    def capture(name):
        app.update()
        ImageGrab.grab(
            bbox=(
                app.winfo_rootx(),
                app.winfo_rooty(),
                app.winfo_rootx() + app.winfo_width(),
                app.winfo_rooty() + app.winfo_height(),
            )
        ).save(output / name)

    try:
        app.geometry("1440x900+0+0")
        settle(2)
        capture("SkyCast_Task04_1440x900.png")
        app.page._parent_canvas.yview_moveto(1)
        settle()
        capture("SkyCast_Task04_Map_Stats.png")
        app.page._parent_canvas.yview_moveto(0)
        app.tab_changed("Tomorrow")
        app.unit_changed("°F")
        settle()
        capture("SkyCast_Task04_Tomorrow_F.png")
        app.tab_changed("Today")
        app.unit_changed("°C")
        for width, height in [(1366, 768), (1024, 700)]:
            app.geometry(f"{width}x{height}+0+0")
            settle()
            capture(f"SkyCast_Task04_{width}x{height}.png")
        assert not errors, errors
        print("Official icon images retrieved:", len(app.icons.remote))
        print(
            "Visual smoke:",
            len(bundles),
            "normalized bundles;",
            len(list(output.glob("*.png"))),
            "captures",
        )
    finally:
        app.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    p.add_argument("--live", action="store_true")
    a = p.parse_args()
    run(a.output, a.live)
