"""Original vector-style interface symbols, rasterized for Tk at high resolution."""

import math
from PIL import Image, ImageDraw
import customtkinter as ctk


def symbol(name, color="#f5f5f7", size=22):
    scale = 4
    image = Image.new("RGBA", (size * scale, size * scale))
    d = ImageDraw.Draw(image)

    def box(coords):
        return tuple(v * size * scale / 24 for v in coords)

    def line(points, width=1.5):
        d.line(box(points), fill=color, width=round(width * size * scale / 24))

    def oval(coords, fill=None, width=1.5):
        d.ellipse(
            box(coords),
            fill=fill,
            outline=color,
            width=round(width * size * scale / 24),
        )

    if name == "grid":
        for x in (3, 13):
            for y in (3, 13):
                d.rectangle(box((x, y, x + 7, y + 7)), fill=color)
    elif name == "bell":
        d.pieslice(box((5, 4, 19, 21)), 180, 360, fill=color)
        d.polygon(
            [box(p) for p in [(5, 11), (19, 11), (19, 16), (21, 19), (3, 19), (5, 16)]],
            fill=color,
        )
        oval((10, 20, 14, 23), color)
        oval((10, 2, 14, 6), color)
    elif name == "pin":
        oval((5, 2, 19, 16), color)
        d.polygon([box(p) for p in [(6, 12), (18, 12), (12, 23)]], fill=color)
        d.ellipse(box((9, 6, 15, 12)), fill="#111015")
    elif name == "search":
        oval((3, 2, 17, 16))
        line((16, 15, 22, 22), 2)
    elif name == "sun":
        oval((8, 8, 16, 16))
        for i in range(8):
            a = i * math.pi / 4
            line(
                (
                    12 + 7 * math.cos(a),
                    12 + 7 * math.sin(a),
                    12 + 10 * math.cos(a),
                    12 + 10 * math.sin(a),
                )
            )
    elif name == "moon":
        # Crescent path constructed as a polygon, with no background-colored cutout.
        points = []
        for i in range(41):
            a = math.radians(60 + i * 6)
            points.append((12 + 9 * math.cos(a), 12 + 9 * math.sin(a)))
        for i in range(41):
            a = math.radians(270 - i * 4.5)
            points.append((16.5 + 7.8 * math.cos(a), 12 + 7.8 * math.sin(a)))
        d.polygon([box(p) for p in points], fill=color)
    elif name == "layers":
        for y in (0, 5, 10):
            line((3, 8 + y, 12, 3 + y, 21, 8 + y, 12, 13 + y, 3, 8 + y))
    elif name == "reset":
        d.arc(box((5, 7, 21, 20)), 220, 500, fill=color, width=5)
        line((8, 3, 3, 8, 8, 12))
        line((3, 8, 12, 8))
    elif name == "locate":
        oval((6, 6, 18, 18))
        oval((10, 10, 14, 14), color)
        for points in [
            (12, 2, 12, 7),
            (12, 17, 12, 22),
            (2, 12, 7, 12),
            (17, 12, 22, 12),
        ]:
            line(points)
    elif name in ("plus", "minus"):
        line((5, 12, 19, 12))
        if name == "plus":
            line((12, 5, 12, 19))
    return ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))
