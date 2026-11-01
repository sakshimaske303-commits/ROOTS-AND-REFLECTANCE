"""
ROOTS & REFLECTANCE: match the Sawardoh fields to the land records by crop history.

The village crop register gives the crop on each survey number for 2022-23 to 2024-25
(data/land_record_crops.csv, records L1 to L4). L1 and L2 swapped soyabean and cotton
between kharif 2023 and kharif 2024, and in rabi 2024-25 L1 had wheat and L2 gram.
Soyabean is harvested by early October, so a soyabean field is bare in late October and
November while a cotton field is still green. Gram is cut by late February; wheat stays
green into early March.

For each field I take the median NDVI of clear passes in three windows and compare the
pattern with what each record says was grown. A field is only called a match when the
gap between the two kharif windows is large and points the right way.

Input:  data/roots_reflectance_crop_history.csv   (from src/gee_crop_history.js)
        data/land_record_crops.csv
Output: output/crop_history_windows.csv
        output/crop_history_match.csv
        output/crop_history_sawardoh.png

Usage:  python src/crop_history.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "output")

MIN_CLEAR = 0.8   # share of the field's pixels that must be clear on a pass
BARE = 0.40       # below this in late October-November the kharif crop is already cut (soyabean)
GREEN = 0.50      # above this the crop is still standing (cotton; wheat in late February)

WINDOWS = {
    "late_kharif_2022": ("2022-10-20", "2022-11-30"),
    "late_kharif_2023": ("2023-10-20", "2023-11-30"),
    "late_kharif_2024": ("2024-10-20", "2024-11-30"),
    "late_feb_2025":    ("2025-02-16", "2025-03-10"),
}

# What each record should look like, from the crop register: C = still green in late
# kharif (cotton), S = bare by then (soyabean), W = green in late February (wheat),
# G = bare by then (gram cut). None = the register says nothing for that season.
EXPECTED = {
    "L1": {"late_kharif_2022": "C", "late_kharif_2023": "S", "late_kharif_2024": "C", "late_feb_2025": "W"},
    "L2": {"late_kharif_2022": "C", "late_kharif_2023": "C", "late_kharif_2024": "S", "late_feb_2025": "G"},
    "L4": {"late_kharif_2022": "C", "late_kharif_2023": "C", "late_kharif_2024": "C", "late_feb_2025": None},
}


def load_passes():
    df = pd.read_csv(os.path.join(ROOT, "data", "roots_reflectance_crop_history.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df["clear_share"] = df["clear"] / df["all"]
    # I drop passes where cloud covers part of the field, and same-day duplicates
    # from overlapping tiles.
    df = df[(df["clear_share"] >= MIN_CLEAR) & df["NDVI"].notna()]
    return df.groupby(["field_num", "date"], as_index=False)["NDVI"].median()


def window_table(df):
    rows = []
    for field, g in df.groupby("field_num"):
        row = {"field": int(field)}
        for name, (a, b) in WINDOWS.items():
            w = g[(g["date"] >= a) & (g["date"] <= b)]["NDVI"]
            row[name] = round(w.median(), 3) if len(w) else None
            row[name + "_passes"] = len(w)
        rows.append(row)
    return pd.DataFrame(rows)


def read_season(name, v):
    if pd.isna(v):
        return None
    if name == "late_feb_2025":
        return "W" if v >= GREEN else ("G" if v < BARE else "?")
    return "C" if v >= GREEN else ("S" if v < BARE else "?")


def judge(row):
    seen = {k: read_season(k, row[k]) for k in WINDOWS}
    row_out = {"field": int(row["field"]), "seen": " ".join(f"{k[-4:]}:{v}" for k, v in seen.items())}
    for rec, exp in EXPECTED.items():
        checks = [(seen[k] == e) for k, e in exp.items() if e is not None and seen[k] is not None]
        row_out[rec] = f"{sum(checks)}/{len(checks)}"
    return pd.Series(row_out)


def plot(df):
    fig, axes = plt.subplots(5, 1, figsize=(11, 12), sharex=True, sharey=True)
    for ax, (field, g) in zip(axes, df.groupby("field_num")):
        ax.plot(g["date"], g["NDVI"], "o-", ms=3, lw=0.8, color="#2f5d1e")
        for a, b in WINDOWS.values():
            ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color="#e8c766", alpha=0.35, lw=0)
        ax.set_ylabel(f"Field {int(field)}\nNDVI")
        ax.set_ylim(0, 0.95)
        ax.grid(alpha=0.3)
    axes[0].set_title("Sawardoh fields, clear Sentinel-2 passes 2022 to 2025 "
                      "(shaded: windows used to tell soyabean, cotton, wheat and gram apart)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "crop_history_sawardoh.png"), dpi=150)


def main():
    os.makedirs(OUT, exist_ok=True)
    df = load_passes()
    win = window_table(df)
    win.to_csv(os.path.join(OUT, "crop_history_windows.csv"), index=False)
    match = win.apply(judge, axis=1)
    match.to_csv(os.path.join(OUT, "crop_history_match.csv"), index=False)
    plot(df)
    print(win[["field"] + list(WINDOWS)].to_string(index=False))
    print("\nSeasons each record agrees with (C cotton, S soyabean, W wheat, G gram, ? unclear):")
    print(match.to_string(index=False))
    print("  L3: no crop register page in hand")


if __name__ == "__main__":
    main()
