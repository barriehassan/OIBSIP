"""Original condition illustrations plus validated OpenWeather hosted icons.

Pillow images are cached in memory; Tk images are created only on the UI thread.
No third-party icon files are redistributed or saved to disk.
"""

from functools import lru_cache
from io import BytesIO
import math
from time import monotonic
import requests
from PIL import Image, ImageDraw, ImageFilter
import customtkinter as ctk

FAMILIES = ("01", "02", "03", "04", "09", "10", "11", "13", "50")
VALID_IDS = frozenset(f + n for f in FAMILIES for n in ("d", "n"))


@lru_cache(maxsize=20)
def original_icon(icon_id):
    im = Image.new("RGBA", (256, 256))
    d = ImageDraw.Draw(im)
    family, night = icon_id[:2], icon_id.endswith("n")
    if family in ("01", "02", "03", "10"):
        x, y, r = (128, 116, 46) if family == "01" else (165, 82, 38)
        if night:
            d.ellipse((x - r, y - r, x + r, y + r), fill="#dae9ff")
            d.ellipse(
                (x - r + 22, y - r - 9, x + r + 14, y + r - 19), fill=(0, 0, 0, 0)
            )
            d.ellipse((69, 64, 76, 71), fill="#fff0aa")
        else:
            for i in range(12):
                a = i * math.pi / 6
                d.line(
                    (
                        x + math.cos(a) * (r + 12),
                        y + math.sin(a) * (r + 12),
                        x + math.cos(a) * (r + 23),
                        y + math.sin(a) * (r + 23),
                    ),
                    fill="#ffe682",
                    width=6,
                )
            for ring in range(r, 0, -1):
                t = 1 - ring / r
                d.ellipse(
                    (x - ring, y - ring, x + ring, y + ring),
                    fill=(255, int(165 + 54 * t), int(22 + 45 * t), 255),
                )
    if family != "01":
        mask = Image.new("L", im.size)
        m = ImageDraw.Draw(mask)
        m.ellipse((43, 101, 126, 175), fill=255)
        m.ellipse((85, 69, 173, 161), fill=255)
        m.ellipse((139, 105, 215, 178), fill=255)
        m.rounded_rectangle((52, 132, 211, 181), radius=25, fill=255)
        shadow = Image.new("RGBA", im.size, "#000000")
        shadow.putalpha(
            mask.filter(ImageFilter.GaussianBlur(8)).point(lambda x: int(x * 0.25))
        )
        im.alpha_composite(shadow, (0, 7))
        cloud = Image.new("RGBA", im.size)
        cd = ImageDraw.Draw(cloud)
        for y in range(256):
            shade = max(150, min(255, int(265 - (y - 75) * 0.75)))
            cd.line((0, y, 256, y), fill=(shade, shade, min(255, shade + 6), 255))
        cloud.putalpha(mask)
        im.alpha_composite(cloud)
        d = ImageDraw.Draw(im)
    if family in ("09", "10", "11"):
        for x, y in ((75, 195), (124, 207), (173, 195)):
            d.line((x + 7, y - 6, x - 2, y + 9), fill="#44c8fb", width=9)
    if family == "11":
        d.polygon(
            [
                (142, 146),
                (119, 189),
                (145, 189),
                (130, 229),
                (177, 174),
                (151, 174),
                (166, 146),
            ],
            fill="#ffd65a",
        )
    if family == "13":
        for x in (76, 130, 184):
            for angle in (0, math.pi / 3, 2 * math.pi / 3):
                dx, dy = math.cos(angle) * 11, math.sin(angle) * 11
                d.line((x - dx, 207 - dy, x + dx, 207 + dy), fill="#b9e7ff", width=4)
    if family == "50":
        for y in (185, 204, 223):
            d.rounded_rectangle((53, y, 204, y + 5), radius=2, fill="#b6c2ca")
    if icon_id not in VALID_IDS:
        d.ellipse((114, 119, 140, 145), outline="#657383", width=4)
        d.line((127, 144, 127, 157), fill="#657383", width=4)
        d.ellipse((124, 163, 130, 169), fill="#657383")
    return im


def fetch_icons(ids):
    images = {}
    deadline = monotonic() + 12
    with requests.Session() as session:
        for icon_id in sorted(set(ids) & VALID_IDS):
            if monotonic() > deadline:
                break
            try:
                with session.get(
                    f"https://openweathermap.org/img/wn/{icon_id}@2x.png",
                    timeout=(2, 3),
                    allow_redirects=False,
                    stream=True,
                ) as response:
                    if response.status_code != 200:
                        continue
                    body = bytearray()
                    for chunk in response.iter_content(16384):
                        body.extend(chunk)
                        if len(body) > 200_000 or monotonic() > deadline:
                            break
                    if len(body) > 200_000:
                        continue
                    with Image.open(BytesIO(body)) as image:
                        if (
                            image.format != "PNG"
                            or image.width > 512
                            or image.height > 512
                        ):
                            continue
                        images[icon_id] = image.convert("RGBA")
            except (requests.RequestException, OSError, ValueError):
                continue
    return images


class IconImages:
    def __init__(self):
        self.remote = {}
        self.tk = {}
        self.attempted = set()

    def image(self, icon_id, size):
        key = (icon_id, size, icon_id in self.remote)
        if key not in self.tk:
            image = self.remote.get(icon_id)
            if image is None:
                image = original_icon(icon_id)
            self.tk[key] = ctk.CTkImage(
                light_image=image, dark_image=image, size=(size, size)
            )
        return self.tk[key]

    def accept(self, images):
        self.remote.update(images)
        self.tk.clear()
