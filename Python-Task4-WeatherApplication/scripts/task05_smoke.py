"""Real widget captures with explicit live retrieval; never performs speech or IP lookup."""

import sys, time, tempfile, argparse
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import ImageGrab
from app.core.models import Location
from app.core.exceptions import WeatherNetworkError
from app.services.weather_service import LocationWeatherResult
from app.storage.local import LocalStore
from app.ui.controller import Controller, Backend
from app.ui.window import SkyCastWindow
from app.ui.presentation import local_today


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
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
    backend = Backend()
    bundles = [backend.weather(loc) for loc in locations]
    with tempfile.TemporaryDirectory() as temp:
        store = LocalStore(Path(temp) / "skycast.sqlite3")
        now = lambda: datetime.now(timezone.utc)
        for bundle in bundles:
            store.save(bundle, now())
        c = Controller(backend, store=store, clock=now)
        c.state.bundle = bundles[0]
        c.state.selected_date = local_today(bundles[0], now())
        for b in bundles:
            c.state.cities[b.location] = LocationWeatherResult(b.location, b)
        app = SkyCastWindow(c, store=store)
        errors = []
        app.report_callback_exception = lambda *a: errors.append(str(a))

        def settle(seconds=0.7):
            end = time.monotonic() + seconds
            while time.monotonic() < end:
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
            settle(15)
            capture("SkyCast_Task05_Dashboard.png")
            app.enhancements.save_favorite()
            app.toggle_details()
            settle()
            app.page._parent_canvas.yview_moveto(1)
            settle()
            capture("SkyCast_Task05_Details.png")
            app.unit_changed("°F")
            settle()
            capture("SkyCast_Task05_Fahrenheit.png")
            app.enhancements.show_favorites()
            settle()
            app.page._parent_canvas.yview_moveto(1)
            settle()
            capture("SkyCast_Task05_Favorites.png")
            assert LocalStore(store.path).favorites()[0] == [locations[0]]
            app.enhancements.favorite_list.pack_forget()
            app.enhancements.request_location()
            settle()
            capture("SkyCast_Task05_Location_Consent.png")
            app.enhancements.consent_panel.pack_forget()

            class Offline:
                def weather(self, location):
                    raise WeatherNetworkError("Simulated offline transport")

            c.backend = Offline()
            app.refresh()
            settle(1)
            assert c.state.offline and c.state.bundle.location == locations[0]
            app.toggle_details()
            app.unit_changed("°C")
            app.page._parent_canvas.yview_moveto(0)
            settle()
            capture("SkyCast_Task05_Offline.png")
            for width, height in [(1366, 768), (1024, 700)]:
                app.geometry(f"{width}x{height}+0+0")
                settle()
                capture(f"SkyCast_Task05_{width}x{height}.png")
            assert not errors, errors
            print(
                "Three live bundles; persisted favorite reopened; offline fallback simulated with real cached weather; eight real GUI captures; no speech or IP requests."
            )
        finally:
            app.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.output)
