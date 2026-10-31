"""Pastel mountain header artwork, using a local user image when available."""

from __future__ import annotations
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKGROUND_FOLDER = PROJECT_ROOT / "assets" / "backgrounds"


def build_background(width: int = 1120, height: int = 230) -> Image.Image:
    """Read an optional mountain image, otherwise draw an offline pastel illustration."""
    for name in ("mountain.png", "mountain.jpg", "mountain.jpeg", "mountain.webp"):
        image_file = BACKGROUND_FOLDER / name
        if image_file.is_file():
            try:
                with Image.open(image_file) as image:
                    return ImageOps.fit(image.convert("RGB"), (width, height), method=Image.Resampling.LANCZOS)
            except (OSError, ValueError):
                pass
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    start, end = (224, 233, 253), (250, 225, 244)
    for y in range(height):
        t = y / max(height - 1, 1)
        color = tuple(round(a * (1 - t) + b * t) for a, b in zip(start, end))
        for x in range(width):
            pixels[x, y] = color
    canvas = ImageDraw.Draw(image)
    w, h = width, height
    canvas.ellipse((int(.75*w), int(.06*h), int(.85*w), int(.53*h)), fill=(254, 244, 225))
    canvas.polygon([(0, .82*h), (.18*w, .30*h), (.35*w, .84*h), (.55*w, .40*h), (.80*w, .86*h), (w, .33*h), (w, h), (0,h)], fill=(189, 191, 226))
    canvas.polygon([(0,.96*h), (.25*w,.49*h), (.51*w,.97*h), (.70*w,.48*h), (w,.94*h), (w,h), (0,h)], fill=(151, 174, 218))
    canvas.polygon([(0,h), (.20*w,.71*h), (.40*w,h), (.64*w,.69*h), (.86*w,h), (w,.77*h), (w,h)], fill=(124, 150, 200))
    return image
