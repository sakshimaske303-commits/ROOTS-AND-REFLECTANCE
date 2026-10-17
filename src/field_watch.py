"""
ROOTS & REFLECTANCE — Field Watch: weak patches inside a field, flagged before anyone walks there.

Input:  data/roots_reflectance_field_watch.csv   (from src/gee_field_watch.js)
        data/field_boundaries.geojson
Output: output/field_watch/passes.csv            every pass x field: usable share, median NDVI
        output/field_watch/patches_<date>.csv     the patches flagged on that pass
        output/field_watch/map_<zone>_<date>.png  pixel map with the flagged patches outlined
        data/field_alerts.csv                     one new row per new patch, status 'flagged'
                                                  (ground columns stay empty until the visit)

How a patch is flagged (all thresholds are set below and can be rerun at other values):
  1. The pass must be usable for the field: at least 80% of its pixels pass the
     Cloud Score+ / SCL test (the same rule as the kharif audit).
  2. Only interior pixels count: pixel centre at least 7.1 m inside the boundary, so
     the whole 10 m pixel lies in the field (half a diagonal of a 10 m square).
  3. A pixel is weak when its NDVI is at least DROP below the median of the field's
     interior pixels on that pass.
  4. Weak pixels that touch each other (8-neighbours on the 10 m grid) form a patch.
     A patch needs at least MIN_PIXELS pixels (3 pixels = 300 m2).
  5. A patch that overlaps a patch from the field's previous usable pass is marked
     'repeat'. Repeats are the stronger signal; one-pass patches can be haze or a
     shadow the masks missed.

The alert is written to data/field_alerts.csv (and should be committed) BEFORE the
ground visit, so the commit time shows the satellite call came first.

No geometry library is needed: at field scale (under 200 m) a local flat projection
around each field is accurate to a few centimetres.

Usage:  python src/field_watch.py [data/roots_reflectance_field_watch.csv]
"""
import csv
import json
import math
import os
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

USABLE_SHARE = 0.80   # same field-level rule as the kharif audit
INTERIOR_M = 7.1      # pixel centre this far inside the boundary => whole pixel inside
DROP = 0.10           # NDVI below the field's interior median by at least this much
MIN_PIXELS = 3        # smallest patch, in 10 m pixels
GRID_M = 10.0

ALERT_COLUMNS = [
    "alert_id", "flagged_on", "pass_date", "zone", "field", "patch_pixels", "patch_area_m2",
    "centre_lat", "centre_lon", "patch_ndvi", "field_median_ndvi", "repeat",
    # filled in after the ground visit
    "visited_on", "found_on_ground", "ground_photos", "farmer_told_on", "farmer_action",
    "action_cost_rs", "notes",
]


# ---------- geometry helpers (local metres) ----------
class LocalFrame:
    def __init__(self, lat0, lon0):
        self.lat0, self.lon0 = lat0, lon0
        self.kx = 111320.0 * math.cos(math.radians(lat0))
        self.ky = 110540.0

    def to_xy(self, lon, lat):
        return (np.asarray(lon) - self.lon0) * self.kx, (np.asarray(lat) - self.lat0) * self.ky

    def to_lonlat(self, x, y):
        return self.lon0 + x / self.kx, self.lat0 + y / self.ky


def point_in_polygon(x, y, ring):
    """Ray casting, vectorised over points. ring: list of (x, y), closed or not."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    inside = np.zeros(x.shape, bool)
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]; x2, y2 = ring[(i + 1) % n]
        crosses = ((y1 > y) != (y2 > y))
        with np.errstate(divide="ignore", invalid="ignore"):
            xint = (x2 - x1) * (y - y1) / (y2 - y1) + x1
        inside ^= crosses & (x < xint)
    return inside


def distance_to_edges(x, y, ring):
    x = np.asarray(x, float); y = np.asarray(y, float)
    best = np.full(x.shape, np.inf)
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]; x2, y2 = ring[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = np.clip(((x - x1) * dx + (y - y1) * dy) / L2, 0, 1) if L2 else 0
        px, py = x1 + t * dx, y1 + t * dy
        best = np.minimum(best, np.hypot(x - px, y - py))
    return best


def load_fields():
    with open(os.path.join(ROOT, "data", "field_boundaries.geojson"), encoding="utf-8") as f:
        gj = json.load(f)
    out = {}
    for ft in gj["features"]:
        p = ft["properties"]
        coords = ft["geometry"]["coordinates"][0]
        lons = [c[0] for c in coords]; lats = [c[1] for c in coords]
        frame = LocalFrame(float(np.mean(lats)), float(np.mean(lons)))
        xs, ys = frame.to_xy(lons, lats)
        ring = list(zip(xs, ys))
        if ring[0] == ring[-1]:
            ring = ring[:-1]
        out[(p["zone"], int(p["field_num"]))] = dict(props=p, frame=frame, ring=ring)
    return out


# ---------- patches ----------
def find_patches(px):
    """px: DataFrame of weak interior pixels with x, y (metres). Returns list of index arrays."""
    if px.empty:
        return []
    gx = np.round(px["x"].values / GRID_M).astype(int)
    gy = np.round(px["y"].values / GRID_M).astype(int)
    cells = {(a, b): i for i, (a, b) in enumerate(zip(gx, gy))}
    seen, groups = set(), []
    for start in range(len(px)):
        if start in seen:
            continue
        stack, group = [start], []
        seen.add(start)
        while stack:
            i = stack.pop(); group.append(i)
            for da in (-1, 0, 1):
                for db in (-1, 0, 1):
                    j = cells.get((gx[i] + da, gy[i] + db))
                    if j is not None and j not in seen:
                        seen.add(j); stack.append(j)
        groups.append(np.array(group))
    return groups


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "roots_reflectance_field_watch.csv")
    if not os.path.exists(src):
        sys.exit(f"Not found: {src}\nRun src/gee_field_watch.js in the Earth Engine Code Editor and download the CSV into data/.")
    out_dir = os.path.join(ROOT, "output", "field_watch")
    os.makedirs(out_dir, exist_ok=True)

    fields = load_fields()
    df = pd.read_csv(src)
    df["field_num"] = df["field_num"].astype(int)

    # interior flag and local coordinates, per field
    parts = []
    for (zone, num), g in df.groupby(["zone", "field_num"]):
        fd = fields[(zone, num)]
        x, y = fd["frame"].to_xy(g["lon"].values, g["lat"].values)
        g = g.copy(); g["x"], g["y"] = x, y
        inside = point_in_polygon(x, y, fd["ring"])
        g["interior"] = inside & (distance_to_edges(x, y, fd["ring"]) >= INTERIOR_M)
        parts.append(g)
    df = pd.concat(parts, ignore_index=True)

    # where two tiles cover the same date, keep the image with more usable pixels for that field
    score = df.groupby(["date", "zone", "field_num", "image_id"])["usable"].sum().reset_index()
    best = score.sort_values("usable").groupby(["date", "zone", "field_num"]).tail(1)
    df = df.merge(best[["date", "zone", "field_num", "image_id"]], on=["date", "zone", "field_num", "image_id"])

    pass_rows, patch_rows = [], []
    prev_patch_cells = {}   # (zone, field) -> set of grid cells flagged on the previous usable pass
    for (date, zone, num), g in df.sort_values("date").groupby(["date", "zone", "field_num"], sort=True):
        share = g["usable"].mean()
        interior = g[g["interior"]]
        usable_px = interior[interior["usable"] == 1]
        row = dict(date=date, zone=zone, field=num, pixels=len(g), interior_pixels=len(interior),
                   usable_share=round(share, 3), usable=bool(share >= USABLE_SHARE and len(usable_px) > 0),
                   median_ndvi=round(usable_px["NDVI"].median(), 3) if len(usable_px) else np.nan,
                   patches=0)
        if row["usable"]:
            med = usable_px["NDVI"].median()
            weak = usable_px[usable_px["NDVI"] <= med - DROP].reset_index(drop=True)
            groups = [grp for grp in find_patches(weak) if len(grp) >= MIN_PIXELS]
            cells_now = set()
            prev = prev_patch_cells.get((zone, num), set())
            for k, grp in enumerate(groups, start=1):
                p = weak.iloc[grp]
                cells = {(int(round(a / GRID_M)), int(round(b / GRID_M))) for a, b in zip(p["x"], p["y"])}
                cells_now |= cells
                cx, cy = p["x"].mean(), p["y"].mean()
                clon, clat = fields[(zone, num)]["frame"].to_lonlat(cx, cy)
                patch_rows.append(dict(
                    alert_id=f"{date}_{zone[:3].upper()}{num}_{k}", pass_date=date, zone=zone, field=num,
                    patch_pixels=len(p), patch_area_m2=int(len(p) * GRID_M * GRID_M),
                    centre_lat=round(clat, 6), centre_lon=round(clon, 6),
                    patch_ndvi=round(p["NDVI"].mean(), 3), field_median_ndvi=round(med, 3),
                    repeat="yes" if cells & prev else "no"))
            row["patches"] = len(groups)
            prev_patch_cells[(zone, num)] = cells_now
        pass_rows.append(row)

    passes = pd.DataFrame(pass_rows)
    passes.to_csv(os.path.join(out_dir, "passes.csv"), index=False)
    patches = pd.DataFrame(patch_rows)
    print(passes.to_string(index=False))

    if patches.empty:
        print("\nNo patches flagged on any usable pass.")
        return
    for date, g in patches.groupby("pass_date"):
        g.to_csv(os.path.join(out_dir, f"patches_{date}.csv"), index=False)
        for zone in g["zone"].unique():
            draw_map(df, fields, patches, date, zone, out_dir)

    append_alerts(patches)
    print(f"\n{len(patches)} patch(es) flagged in total. New ones were added to data/field_alerts.csv.")
    print("Commit data/field_alerts.csv now, before the ground visit.")


def append_alerts(patches):
    path = os.path.join(ROOT, "data", "field_alerts.csv")
    existing = set()
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            existing = {r["alert_id"] for r in csv.DictReader(f)}
    new = patches[~patches["alert_id"].isin(existing)]
    write_header = not os.path.exists(path) or os.path.getsize(path) == 0
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ALERT_COLUMNS)
        if write_header:
            w.writeheader()
        for _, r in new.iterrows():
            rec = {c: "" for c in ALERT_COLUMNS}
            rec.update({k: r[k] for k in r.index if k in rec})
            rec["flagged_on"] = today
            w.writerow(rec)


def draw_map(df, fields, patches, date, zone, out_dir):
    keys = sorted(k for k in fields if k[0] == zone)
    fig, axes = plt.subplots(1, len(keys), figsize=(3.4 * len(keys), 3.8), constrained_layout=True, squeeze=False)
    for ax, key in zip(axes[0], keys):
        fd = fields[key]
        g = df[(df["date"] == date) & (df["zone"] == zone) & (df["field_num"] == key[1])]
        ring = fd["ring"] + [fd["ring"][0]]
        ax.plot([p[0] for p in ring], [p[1] for p in ring], color="#1f2a44", lw=1.6)
        if not g.empty:
            ok = g[(g["usable"] == 1) & g["interior"]]
            sc = ax.scatter(ok["x"], ok["y"], c=ok["NDVI"], cmap="RdYlGn", vmin=0.1, vmax=0.9, marker="s", s=60)
            p = patches[(patches["pass_date"] == date) & (patches["zone"] == zone) & (patches["field"] == key[1])]
            for _, r in p.iterrows():
                x, y = fd["frame"].to_xy(r["centre_lon"], r["centre_lat"])
                ax.scatter([x], [y], s=380, facecolors="none", edgecolors="black", linewidths=2)
                ax.annotate(r["alert_id"].split("_")[-1], (x, y), xytext=(6, 6), textcoords="offset points", fontsize=9, fontweight="bold")
        ax.set_title(f"Field {key[1]}", fontsize=10)
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle(f"{zone.capitalize()}, Sentinel-2 {date}: interior 10 m pixels (NDVI), flagged patches circled", fontsize=11)
    fig.savefig(os.path.join(out_dir, f"map_{zone}_{date}.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
