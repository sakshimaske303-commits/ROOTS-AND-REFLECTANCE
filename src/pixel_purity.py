"""
ROOTS & REFLECTANCE — how many Sentinel-2 pixels does each of my fields really have?

A field mean from a satellite is only as good as the pixels under it. My fields are
0.2 to 1 ha, and a Sentinel-2 pixel is 10 m (red, NIR) or 20 m (red-edge, SCL cloud
classes). Pixels on the boundary mix my crop with the bund, the road or the neighbour.

For every field this script lays the real Sentinel-2 pixel grid (UTM zone 44N, the grid
the tiles are delivered on) over the boundary and counts, at 10 m and at 20 m:
    centre_in   pixels whose centre falls inside the field (what a zonal mean uses)
    pure        pixels that lie wholly inside the field
    purity      pure / centre_in

Usage:   python3 src/pixel_purity.py
Output:  output/pixel_purity.csv, output/pixel_grid_sawardoh.png, output/pixel_grid_karanja.png
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Polygon, box
from shapely.ops import transform

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True).transform


def load_fields():
    with open(os.path.join(ROOT, "data", "field_boundaries.geojson"), encoding="utf-8") as f:
        gj = json.load(f)
    out = []
    for ft in gj["features"]:
        poly = transform(TO_UTM, Polygon(ft["geometry"]["coordinates"][0]))
        out.append((ft["properties"], poly))
    return out


def grid_cells(poly, size):
    """Sentinel-2 pixels (aligned to multiples of `size` in UTM metres) touching the polygon."""
    x0, y0, x1, y1 = poly.bounds
    xs = np.arange(np.floor(x0 / size) * size, x1 + size, size)
    ys = np.arange(np.floor(y0 / size) * size, y1 + size, size)
    cells = []
    for x in xs:
        for y in ys:
            c = box(x, y, x + size, y + size)
            if c.intersects(poly):
                cells.append(c)
    return cells


def count(poly, size):
    cells = grid_cells(poly, size)
    centre_in = [c for c in cells if poly.contains(c.centroid)]
    pure = [c for c in cells if poly.contains(c)]
    return cells, centre_in, pure


def main():
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    fields = load_fields()
    rows = []
    for p, poly in fields:
        r = dict(zone=p["zone"], field_num=p["field_num"], crops=",".join(p["crops"]),
                 area_ha_listed=p["area_ha"], area_ha_from_boundary=round(poly.area / 1e4, 4),
                 perimeter_m=round(poly.length, 1))
        for size in (10, 20):
            _, cin, pure = count(poly, size)
            r[f"centre_in_{size}m"] = len(cin)
            r[f"pure_{size}m"] = len(pure)
            r[f"purity_{size}m"] = round(len(pure) / len(cin), 2) if cin else np.nan
        # how far inside the boundary is the innermost point: a field narrower than
        # two pixels has no pure pixel at all
        r["max_inset_m"] = round(max(d for d in np.arange(0, 80, 0.5) if not poly.buffer(-d).is_empty), 1)
        rows.append(r)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(ROOT, "output", "pixel_purity.csv"), index=False)
    pd.set_option("display.width", 250)
    print(df.to_string(index=False))

    for zone in ("sawardoh", "karanja"):
        zf = [(p, g) for p, g in fields if p["zone"] == zone]
        fig, axes = plt.subplots(1, 2, figsize=(13, 6.2), constrained_layout=True)
        for ax, size in zip(axes, (10, 20)):
            for p, poly in zf:
                cells, cin, pure = count(poly, size)
                pure_ids = {id(c) for c in pure}
                cin_ids = {id(c) for c in cin}
                for c in cells:
                    if id(c) in pure_ids:
                        fc, al = "#2a9d6f", 0.55
                    elif id(c) in cin_ids:
                        fc, al = "#e0a030", 0.55
                    else:
                        fc, al = "#b0b0b0", 0.25
                    ax.fill(*c.exterior.xy, fc=fc, ec="white", lw=0.4, alpha=al)
                ax.plot(*poly.exterior.xy, color="#1f2a44", lw=1.8)
                cx, cy = poly.representative_point().coords[0]
                ax.text(cx, cy, str(p["field_num"]), ha="center", va="center", fontsize=13, fontweight="bold", color="#1f2a44")
            ax.set_aspect("equal")
            ax.set_title(f"{size} m pixels" + (" (red, near-infrared: NDVI)" if size == 10 else " (red-edge, cloud classes: NDRE)"), fontsize=11)
            ax.set_xlabel("UTM 44N easting (m)"); ax.set_ylabel("northing (m)")
            ax.ticklabel_format(useOffset=False, style="plain"); ax.tick_params(labelsize=8)
        handles = [plt.Rectangle((0, 0), 1, 1, fc="#2a9d6f", alpha=0.55), plt.Rectangle((0, 0), 1, 1, fc="#e0a030", alpha=0.55),
                   plt.Rectangle((0, 0), 1, 1, fc="#b0b0b0", alpha=0.25)]
        fig.legend(handles, ["pure: wholly inside the field", "mixed: centre inside, edge outside", "touches the field, centre outside (not used)"],
                   loc="outside lower center", ncol=3, frameon=False, fontsize=10)
        fig.suptitle(f"{zone.capitalize()}: the Sentinel-2 pixel grid over my field boundaries", fontsize=13)
        fig.savefig(os.path.join(ROOT, "output", f"pixel_grid_{zone}.png"), dpi=160)
        plt.close(fig)


if __name__ == "__main__":
    main()
