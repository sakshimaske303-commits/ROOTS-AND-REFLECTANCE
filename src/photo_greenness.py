"""
ROOTS & REFLECTANCE — a greenness number from each ground photo.

The satellite gives me a number (NDVI). My photos so far give me a picture. To compare
the two I need a number from the picture too. For every overview and crop photo this
computes, over a fixed band of the frame:
    gcc             green chromatic coordinate, G / (R + G + B), averaged over the band
    green_fraction  share of pixels in the band that are "green vegetation" by the
                    excess-green rule: 2g - r - b > 0.10, with r, g, b = each channel / (R+G+B)

The band is the part of the frame between 40% and 70% of the height: below the horizon
and trees in a level shot, above the position stamp the camera app prints.

What this is NOT: a measured canopy cover. These are oblique photos, framed by hand,
taken at different times of day. An oblique view hides the soil between rows, so it
overstates cover, and the light changes the colours. It is a relative, indicative series.
Photos taken straight down from a fixed point (see docs/FIELD_PROTOCOL.md) are what will
give a cover fraction that can be compared with NDVI properly.

Usage:   python3 src/photo_greenness.py
Output:  data/ground_photo_greenness.csv, output/ground_greenness_by_field.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BAND = (0.40, 0.70)
EXG_MIN = 0.10


def measure(path):
    im = Image.open(path).convert("RGB")
    im.thumbnail((1000, 1000))
    a = np.asarray(im, dtype="float32")
    h = a.shape[0]
    a = a[int(h * BAND[0]):int(h * BAND[1])]
    tot = a.sum(axis=2)
    ok = tot > 30                                   # ignore near-black pixels, where ratios are noise
    r, g, b = (a[..., i][ok] / tot[ok] for i in range(3))
    exg = 2 * g - r - b
    brightness = float(tot[ok].mean() / 3)
    return float(g.mean()), float((exg > EXG_MIN).mean()), brightness


def main():
    idx = pd.read_csv(os.path.join(ROOT, "data", "ground_photo_index.csv"), dtype=str)
    idx = idx[idx.slot != "soil"].copy()
    rows = []
    for r in idx.itertuples():
        gcc, gf, br = measure(os.path.join(ROOT, "geotagged_images", r.file))
        rows.append(dict(date=r.date, zone=r.zone, field=r.field, slot=r.slot, file=r.file,
                         gcc=round(gcc, 4), green_fraction=round(gf, 3), mean_brightness=round(br, 1)))
    df = pd.DataFrame(rows).sort_values(["zone", "field", "slot", "date"])
    pos_path = os.path.join(ROOT, "data", "ground_photo_positions.csv")
    if os.path.exists(pos_path):
        pos = pd.read_csv(pos_path)[["file", "taken"]]
        df = df.merge(pos, on="file", how="left")
    df.to_csv(os.path.join(ROOT, "data", "ground_photo_greenness.csv"), index=False)
    pd.set_option("display.width", 200)
    ov = df[df.slot == "overview"]
    print(ov.pivot_table(index=["zone", "field"], columns="date", values="green_fraction").round(2).to_string())

    colours = {"1": "#d1495b", "2": "#2e86ab", "3": "#3a7d44", "4": "#b5651d", "5": "#6a4c93"}
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True, constrained_layout=True)
    for ax, zone in zip(axes, ("sawardoh", "karanja")):
        for field, g in ov[ov.zone == zone].groupby("field"):
            ax.plot(pd.to_datetime(g.date), g.green_fraction, "-o", color=colours[field], lw=1.6, ms=5, label=f"Field {field}")
        ax.set_title(zone.capitalize(), fontsize=12)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b")); ax.tick_params(labelsize=9)
        ax.set_ylim(0, 1); ax.grid(alpha=0.25); ax.legend(frameon=False, fontsize=9, ncol=3)
    axes[0].set_ylabel("green share of the photo band\n(oblique view, indicative)")
    fig.suptitle("Greenness read from the weekly overview photos", fontsize=13)
    fig.savefig(os.path.join(ROOT, "output", "ground_greenness_by_field.png"), dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
