"""Image compositing for the desktop's actual frosted-glass background."""
from PIL import Image, ImageDraw, ImageFilter
from app.ui.background import build_background

WIDTH, HEIGHT = 1440, 900
PANELS = {
    'sidebar': (18, 18, 238, 882),
    'output': (266, 200, 1000, 452),
    'strength': (1018, 200, 1420, 452),
    'settings': (266, 472, 790, 814),
    'history': (808, 472, 1420, 814),
    'footer': (266, 834, 1420, 882),
}


def render_glass(width=WIDTH, height=HEIGHT):
    """Blur the landscape behind each rounded panel, then tint it navy blue."""
    image = build_background(width, height).convert('RGBA')
    image = Image.alpha_composite(image, Image.new('RGBA', image.size, (5, 17, 51, 45)))
    blurred = image.filter(ImageFilter.GaussianBlur(16 * width / WIDTH))
    sx, sy = width / WIDTH, height / HEIGHT
    for name, box in PANELS.items():
        bounds = tuple(round(n * (sx if i % 2 == 0 else sy)) for i, n in enumerate(box))
        mask = Image.new('L', image.size)
        d = ImageDraw.Draw(mask)
        d.rounded_rectangle(bounds, radius=round(20 * sx), fill=255)
        tint = (10, 29, 71, 205) if name == 'sidebar' else (24, 44, 91, 174)
        layer = Image.alpha_composite(blurred, Image.new('RGBA', image.size, tint))
        image.paste(layer, (0, 0), mask)
        ImageDraw.Draw(image).rounded_rectangle(bounds, radius=round(20 * sx), outline=(187, 212, 255, 120), width=1)
    return image.convert('RGB')
