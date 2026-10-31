from app.ui.background import build_background


def test_offline_mountain_rendering():
    image = build_background(320, 100)
    assert image.size == (320, 100)
    assert image.mode == "RGB"
    assert image.getpixel((5, 5)) != image.getpixel((160, 95))
