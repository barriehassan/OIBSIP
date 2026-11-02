from io import BytesIO
from pathlib import Path
from PIL import Image
import pytest
from app.ui.components.weather_icon import original_icon, fetch_icons, VALID_IDS
from app.ui.components.global_map import ASSET


@pytest.mark.parametrize(
    "icon",
    ["01d", "01n", "02d", "03n", "04d", "09d", "10n", "11d", "13d", "50n", "unknown"],
)
def test_original_icon_variants(icon):
    image = original_icon(icon)
    assert image.mode == "RGBA" and image.size == (256, 256)
    assert image.getbbox() is not None
    assert original_icon(icon) is image


def test_map_asset_matches_manifest():
    import json, hashlib

    manifest = json.loads(ASSET.with_name("source.json").read_text())
    assert hashlib.sha256(ASSET.read_bytes()).hexdigest() == manifest["asset_sha256"]
    with Image.open(ASSET) as image:
        assert image.size == (3072, 1536)
    assert manifest["extent"] == [-180, -90, 180, 90]


def test_official_icon_validation(monkeypatch):
    calls = []
    image = Image.new("RGBA", (100, 100), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    class Response:
        status_code = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def iter_content(self, size):
            yield buffer.getvalue()

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, url, **kwargs):
            calls.append((url, kwargs))
            return Response()

    monkeypatch.setattr("app.ui.components.weather_icon.requests.Session", Session)
    images = fetch_icons({"01d", "unknown", "../../evil"})
    assert set(images) == {"01d"} and len(calls) == 1
    assert calls[0][0] == "https://openweathermap.org/img/wn/01d@2x.png"
    assert calls[0][1]["allow_redirects"] is False


def test_bad_icon_keeps_fallback(monkeypatch):
    class Response:
        status_code = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def iter_content(self, size):
            yield b"not a PNG"

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr("app.ui.components.weather_icon.requests.Session", Session)
    assert fetch_icons({"01d"}) == {}
