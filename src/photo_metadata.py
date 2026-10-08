"""
ROOTS & REFLECTANCE — where and when was each ground photo taken?

My weekly photos are taken with a GPS camera app that prints the position and time on
the picture itself (the EXIF GPS fields are empty). This script reads that stamp off
every photo in geotagged_images/ with Tesseract OCR and writes one row per photo:
    lat, lon, taken (local time), and which mapped field the position falls in
    (or the nearest field and the distance to it, if it falls outside all of them).

It then joins the photo log (data/ground_photo_index.csv: which file fills which slot
of the weekly log) so I can check two things I had only assumed so far:
  1. is each "Field N overview" photo really taken in or beside Field N?
     (I often stand on the bund between two fields, so the position can fall a few
     metres inside the neighbour: the test is distance to the field, not containment.)
  2. how far apart, week to week, are the positions I took a field's photo from?

Usage:   python3 src/photo_metadata.py
Needs:   tesseract on the PATH (https://github.com/tesseract-ocr/tesseract)
Output:  data/ground_photo_positions.csv, output/photo_position_spread.csv,
         output/photo_positions_sawardoh.png, output/photo_positions_karanja.png
"""
import json
import os
import re
import subprocess
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from pyproj import Transformer
from shapely.geometry import Point, Polygon
from shapely.ops import transform

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PHOTOS = os.path.join(ROOT, "geotagged_images")
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True).transform

LATLON = re.compile(r"Lat\s*([0-9]{2}[.,][0-9]{4,7}).{0,6}Long\s*([0-9]{2}[.,][0-9]{4,7})", re.S)
WHEN = re.compile(r"(\d{2})/(\d{2})/(\d{4})\s+(\d{1,2})[:.](\d{2})\s*([AP]M)")


def _ocr(image, psm):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as t:
        image.save(t.name)
    try:
        return subprocess.run(["tesseract", t.name, "-", "--psm", str(psm)], capture_output=True, text=True).stdout
    finally:
        os.unlink(t.name)


# (threshold, page mode): plain inversion first, then hard thresholds on the white text.
# Busy backgrounds behind the stamp (leaves, soil) defeat one setting and not another.
ATTEMPTS = [(None, 6), (200, 6), (200, 11), (170, 11), (None, 11), (225, 6)]


def read_stamp(path):
    """OCR the lower part of the photo, where the app prints the position and time."""
    im = Image.open(path).convert("L")
    w, h = im.size
    crop = im.crop((int(w * 0.28), int(h * 0.72), w, h))
    crop = crop.resize((crop.width // 2, crop.height // 2))    # stamp text is large; half size reads as well, faster
    lat = lon = taken = None
    raw = ""
    for thr, psm in ATTEMPTS:
        if thr is None:
            prepared = crop.point(lambda v: 255 - v)                       # white text on dark -> dark on white
        else:
            prepared = crop.point(lambda v, t=thr: 0 if v > t else 255)    # keep only the brightest pixels
        txt = _ocr(prepared, psm)
        raw = raw or txt
        if lat is None:
            m = LATLON.search(txt)
            if m:
                lat, lon = float(m.group(1).replace(",", ".")), float(m.group(2).replace(",", "."))
        if taken is None:
            m = WHEN.search(txt)
            if m:
                d, mo, y, hh, mm, ap = m.groups()
                hh = int(hh) % 12 + (12 if ap == "PM" else 0)
                taken = f"{y}-{mo}-{d} {hh:02d}:{mm}"
        if lat is not None and taken is not None:
            break
    return lat, lon, taken, " ".join(raw.split())


def load_fields():
    with open(os.path.join(ROOT, "data", "field_boundaries.geojson"), encoding="utf-8") as f:
        gj = json.load(f)
    return [(ft["properties"], transform(TO_UTM, Polygon(ft["geometry"]["coordinates"][0]))) for ft in gj["features"]]


def main():
    fields = load_fields()
    rows = []
    for name in sorted(os.listdir(PHOTOS)):
        if not name.lower().endswith((".jpg", ".jpeg")):
            continue
        lat, lon, taken, raw = read_stamp(os.path.join(PHOTOS, name))
        r = dict(file=name, lat=lat, lon=lon, taken=taken)
        if lat is not None:
            p = Point(*TO_UTM(lon, lat))
            r["x_utm"], r["y_utm"] = round(p.x, 1), round(p.y, 1)
            d = sorted((poly.distance(p), pr) for pr, poly in fields)
            dist, pr = d[0]
            r["zone_at_position"] = pr["zone"]
            r["field_at_position"] = pr["field_num"]
            r["inside_field"] = dist == 0
            r["distance_to_field_m"] = round(dist, 1)
        else:
            r["stamp_text"] = raw[:120]
        rows.append(r)
    pos = pd.DataFrame(rows)

    idx_path = os.path.join(ROOT, "data", "ground_photo_index.csv")
    if os.path.exists(idx_path):
        idx = pd.read_csv(idx_path, dtype=str)
        pos = idx.merge(pos, on="file", how="outer")
    pos.to_csv(os.path.join(ROOT, "data", "ground_photo_positions.csv"), index=False)
    print("photos:", len(pos), " stamp read:", int(pos.lat.notna().sum()))

    if "slot" not in pos:
        return
    ov = pos[(pos.slot == "overview") & pos.lat.notna()].copy()
    ov["field"] = ov.field.astype(int)
    spread = []
    for (zone, field), g in ov.groupby(["zone", "field"]):
        xy = g[["x_utm", "y_utm"]].to_numpy()
        c = np.median(xy, axis=0)               # usual spot = median position, so one odd week does not move it
        dd = np.hypot(*(xy - c).T)
        poly = [pl for pr, pl in fields if pr["zone"] == zone and pr["field_num"] == field][0]
        dist_own = [poly.distance(Point(x, y)) for x, y in xy]
        spread.append(dict(zone=zone, field=field, photos=len(g), within_10m_of_own_field=int(sum(d <= 10 for d in dist_own)),
                           max_distance_to_own_field_m=round(max(dist_own), 1),
                           median_distance_from_usual_spot_m=round(float(np.median(dd)), 1),
                           weeks_within_10m_of_usual_spot=int((dd <= 10).sum()),
                           max_distance_from_usual_spot_m=round(dd.max(), 1)))
    sp = pd.DataFrame(spread)
    sp.to_csv(os.path.join(ROOT, "output", "photo_position_spread.csv"), index=False)
    pd.set_option("display.width", 250)
    print(sp.to_string(index=False))

    colours = {1: "#d1495b", 2: "#2e86ab", 3: "#3a7d44", 4: "#b5651d", 5: "#6a4c93"}
    for zone in ("sawardoh", "karanja"):
        fig, ax = plt.subplots(figsize=(8.5, 7.5), constrained_layout=True)
        for pr, poly in fields:
            if pr["zone"] != zone:
                continue
            ax.fill(*poly.exterior.xy, fc=colours[pr["field_num"]], alpha=0.10)
            ax.plot(*poly.exterior.xy, color=colours[pr["field_num"]], lw=1.6)
            cx, cy = poly.representative_point().coords[0]
            ax.text(cx, cy, str(pr["field_num"]), fontsize=15, fontweight="bold", color=colours[pr["field_num"]], ha="center", va="center", alpha=0.5)
        z = pos[(pos.zone == zone) & pos.lat.notna()]
        for _, r in z.iterrows():
            if r.slot == "overview":
                ax.plot(r.x_utm, r.y_utm, "o", ms=7, mfc=colours[int(r.field)], mec="white", mew=0.8)
            else:
                ax.plot(r.x_utm, r.y_utm, "s", ms=5, mfc="#555555", mec="white", mew=0.6)
        ax.plot([], [], "o", ms=7, mfc="#888888", mec="white", label="field overview photo (colour = field it is logged under)")
        ax.plot([], [], "s", ms=5, mfc="#555555", mec="white", label="crop or soil photo")
        ax.legend(loc="upper right", frameon=False, fontsize=9)
        ax.set_aspect("equal"); ax.ticklabel_format(useOffset=False, style="plain"); ax.tick_params(labelsize=8)
        ax.set_xlabel("UTM 44N easting (m)"); ax.set_ylabel("northing (m)")
        ax.set_title(f"{zone.capitalize()}: where each weekly photo was taken (position printed on the photo)", fontsize=11)
        fig.savefig(os.path.join(ROOT, "output", f"photo_positions_{zone}.png"), dpi=160)
        plt.close(fig)


if __name__ == "__main__":
    main()
