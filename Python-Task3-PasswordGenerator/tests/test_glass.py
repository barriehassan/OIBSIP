from app.ui.glass import render_glass, PANELS
from app.ui import background


def test_glass_scales_and_tints_background():
    width, height = 720, 450
    glass = render_glass(width, height)
    raw = background.build_background(width, height)
    assert glass.size == (width, height)
    assert glass.mode == 'RGB'
    # Sidebar must be darker than the uncomposited landscape.
    point = (50, 150)
    assert sum(glass.getpixel(point)) < sum(raw.getpixel(point))
    assert {'sidebar', 'output', 'strength', 'settings', 'history'} <= PANELS.keys()


def test_missing_artwork_has_offline_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(background, 'BACKGROUND_FOLDER', tmp_path)
    image = background.build_background(320, 200)
    assert image.size == (320, 200)
    assert image.getpixel((0, 0)) != image.getpixel((160, 199))
