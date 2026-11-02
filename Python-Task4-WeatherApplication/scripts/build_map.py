"""Build the bundled map from an already downloaded Natural Earth land ZIP.

Build-time only: pip install pyshp Pillow. No GIS dependency at app runtime.
Usage: python scripts/build_map.py /path/to/ne_110m_land.zip
"""

from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import hashlib
import json
import sys
import shapefile
from PIL import Image, ImageDraw


def build(source):
    data = Path(source).read_bytes()
    archive = ZipFile(BytesIO(data))
    reader = shapefile.Reader(
        **{
            ext: BytesIO(archive.read("ne_110m_land." + ext))
            for ext in ("shp", "shx", "dbf")
        }
    )
    image = Image.new("RGB", (3072, 1536), "#19191b")
    draw = ImageDraw.Draw(image)
    for shape in reader.shapes():
        bounds = list(shape.parts) + [len(shape.points)]
        for a, b in zip(bounds, bounds[1:]):
            points = [
                ((lon + 180) * 3072 / 360, (90 - lat) * 1536 / 180)
                for lon, lat in shape.points[a:b]
            ]
            draw.polygon(points, fill="#363638")
    destination = Path(__file__).resolve().parents[1] / "assets/maps"
    destination.mkdir(parents=True, exist_ok=True)
    image.save(destination / "world_land.png")
    version = next(
        (
            archive.read(n).decode().strip()
            for n in archive.namelist()
            if "VERSION" in n
        ),
        "not declared",
    )
    metadata = {
        "source": "https://naturalearth.s3.amazonaws.com/110m_physical/ne_110m_land.zip",
        "version": version,
        "download_sha256": hashlib.sha256(data).hexdigest(),
        "projection": "equirectangular",
        "extent": [-180, -90, 180, 90],
        "size": [3072, 1536],
        "license": "Public domain",
        "terms": "https://www.naturalearthdata.com/about/terms-of-use/",
        "modification": "Rasterized and recolored for SkyCast; no political boundaries",
        "asset_sha256": hashlib.sha256(
            (destination / "world_land.png").read_bytes()
        ).hexdigest(),
    }
    (destination / "source.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("Map built:", version)


if __name__ == "__main__":
    build(sys.argv[1])
