"""
ROOTS & REFLECTANCE: September NDVI 2026 against past seasons with the same crop,
beside the harvest drop each farmer reported.

Usage: python src/loss_proxy.py
"""
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "output")

MIN_CLEAR = 0.8
WINDOW = ("09-15", "10-05")
LATE = ("10-20", "11-30")
BARE, GREEN = 0.40, 0.50
YEAR = 2026

# main crop this season, by area, from the farmers; tur fills about 80% of Karanja 1
CROP_2026 = {("sawardoh", 1): "cotton", ("sawardoh", 2): "cotton", ("sawardoh", 3): "cotton",
             ("sawardoh", 4): "cotton", ("sawardoh", 5): "cotton",
             ("karanja", 1): "tur", ("karanja", 2): "soyabean"}
# what a past season must have looked like in late October to count as the same kind of crop
LATE_SIGN = {"cotton": "green", "tur": "green", "soyabean": "bare"}
NOTES = {("sawardoh", 2): "young orange trees in the field keep NDVI up",
         ("sawardoh", 4): "young orange trees in the field keep NDVI up",
         ("karanja", 1): "about 80% tur with soyabean rows; past seasons read by late-October greenness only"}


def load():
    d = pd.read_csv(os.path.join(ROOT, "data", "roots_reflectance_ndvi_history.csv"))
    d["date"] = pd.to_datetime(d["date"])
    d = d[(d["clear"] / d["all"] >= MIN_CLEAR) & d["NDVI"].notna()]
    return d.groupby(["zone", "field_num", "date"], as_index=False)["NDVI"].median()


def in_window(g, year, md):
    a, b = pd.Timestamp(f"{year}-{md[0]}"), pd.Timestamp(f"{year}-{md[1]}")
    return g[(g.date >= a) & (g.date <= b)]["NDVI"]


def farmer_change(row, crop):
    def q(text):
        m = re.search(crop + r"\s+([0-9.]+)", str(text))
        return float(m.group(1)) if m else None
    now, normal = q(row["q4_harvest_q"]), q(row["q6_normal_yield_q"])
    return None if not now or not normal else round(100 * (now - normal) / normal, 1)


def main():
    os.makedirs(OUT, exist_ok=True)
    d = load()
    survey = pd.read_csv(os.path.join(ROOT, "data", "farmer_survey_2026.csv"))
    rows = []
    for (zone, num), g in d.groupby(["zone", "field_num"]):
        crop = CROP_2026[(zone, num)]
        now = in_window(g, YEAR, WINDOW)
        past, used = [], []
        for y in sorted(g.date.dt.year.unique()):
            if y >= YEAR:
                continue
            late = in_window(g, y, LATE)
            sign = None if late.empty else ("green" if late.median() >= GREEN else
                                            "bare" if late.median() < BARE else None)
            w = in_window(g, y, WINDOW)
            if sign == LATE_SIGN[crop] and not w.empty:
                past.append(w.median())
                used.append(str(y))
        s = survey[(survey.zone == zone) & (survey.field == num)]
        ndvi_now = round(now.median(), 3) if len(now) else None
        ndvi_past = round(pd.Series(past).median(), 3) if past else None
        rows.append({
            "zone": zone, "field": num, "crop_2026": crop,
            "ndvi_2026": ndvi_now, "passes_2026": len(now),
            "ndvi_past_same_crop": ndvi_past, "past_seasons_used": " ".join(used),
            "ndvi_change_pct": round(100 * (ndvi_now - ndvi_past) / ndvi_past, 1)
            if ndvi_now is not None and ndvi_past else None,
            "farmer_yield_change_pct": farmer_change(s.iloc[0], crop) if len(s) else None,
            "note": NOTES.get((zone, num), ""),
        })
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUT, "loss_proxy.csv"), index=False)
    print(out.to_string(index=False))

    both = out.dropna(subset=["ndvi_change_pct", "farmer_yield_change_pct"])
    if len(both) >= 4:
        rho, p = stats.spearmanr(both.ndvi_change_pct, both.farmer_yield_change_pct)
        print(f"\nRank correlation, satellite vs farmer change ({len(both)} fields): {rho:.2f} (p = {p:.2f})")

    labels = [f"{'S' if z == 'sawardoh' else 'K'}{n}" for z, n in zip(out.zone, out.field)]
    x = range(len(out))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar([i - 0.2 for i in x], out.ndvi_change_pct, width=0.4, color="#2f5d1e",
           label="September NDVI, 2026 against past seasons with the same crop")
    ax.bar([i + 0.2 for i in x], out.farmer_yield_change_pct, width=0.4, color="#c9a227",
           label="harvest the farmer reported, 2026 against a normal year")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(list(x), labels)
    ax.set_ylabel("change (%)")
    ax.set_title("What the satellite saw and what the farmers reported, kharif 2026")
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=1)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "loss_proxy.png"), dpi=150)


if __name__ == "__main__":
    main()
