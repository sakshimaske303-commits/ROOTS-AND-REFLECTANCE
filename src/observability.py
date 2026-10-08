"""
ROOTS & REFLECTANCE — what could the satellite see of my fields, pass by pass?

Reads the audit exported by gee_observability_audit.js (every Sentinel-2 pass since
sowing, with the share of each field that was usable) and answers:
  - of all passes over a field, on how many was the field itself usable?
  - how many of those did my old tile-wide rule (tile < 40% cloud) throw away,
    and how many did it keep although the field was not usable?
  - how long were the stretches with no usable look, and which weeks after sowing
    went unobserved?
  - does the field mean change when the 10 m edge strip is left out?
  - which usable satellite dates have a ground photo within three days?

Usage:
    python3 src/observability.py data/roots_reflectance_s2_audit.csv
    python3 src/observability.py data/roots_reflectance_s2_audit.csv --sar data/roots_reflectance_sar.csv --rain data/roots_reflectance_rain.csv

Output (in output/):
    observability_by_field.csv, observability_passes.csv, ground_satellite_pairs.csv,
    observation_timeline_sawardoh.png, observation_timeline_karanja.png
    with --sar:  radar_in_optical_gap.csv, optical_radar_series_<zone>.png
    with --rain: rain_on_pass_days.csv, rain_by_month.csv
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "output")

USABLE_MIN = 0.80      # a pass counts as a usable look at a field if at least 80% of the field is usable
TILE_RULE = 40.0       # the tile-wide cloud percentage my first script filtered on
PAIR_DAYS = 3          # a photo and a satellite look within this many days are treated as a pair


def load_audit(path):
    d = pd.read_csv(path)
    d["date"] = pd.to_datetime(d["date"])
    d["sown"] = pd.to_datetime(d["sown"])
    # Cloud Score+ arrives a little after the image. A pass with no score yet has not
    # been judged, so it is left out here and picked up on the next export.
    pending = d[d["cs"].isna()]["date"].dt.strftime("%Y-%m-%d").unique()
    if len(pending):
        print("passes left out because Cloud Score+ is not available yet:", ", ".join(sorted(pending)))
    d = d[d["cs"].notna()].copy()
    for c in ("covered", "usable", "scl_cloud", "scl_shadow", "scl_clear"):
        d[c] = d[c].fillna(0.0)
    # two tiles or two satellites can deliver the same field on the same day: keep the better look
    d = d.sort_values("usable", ascending=False).drop_duplicates(["zone", "field_num", "footprint", "date"])
    d = d[d.covered >= 0.99]                          # passes that only clip the field are not looks at it
    return d.sort_values(["zone", "field_num", "footprint", "date"])


def gaps(dates, start, end):
    """Lengths in days of the stretches without a usable look, including before the first and after the last."""
    pts = [start] + sorted(dates) + [end]
    return [(b - a).days for a, b in zip(pts[:-1], pts[1:])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audit_csv")
    ap.add_argument("--sar")
    ap.add_argument("--rain")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    d = load_audit(a.audit_csv)
    full = d[d.footprint == "full"].copy()
    full["usable_look"] = full.usable >= USABLE_MIN
    full["kept_by_tile_rule"] = full.tile_cloud_pct < TILE_RULE
    full["days_after_sowing"] = (full.date - full.sown).dt.days
    full.to_csv(os.path.join(OUT, "observability_passes.csv"), index=False)
    end = full.date.max()

    inner = d[d.footprint == "inner"][["zone", "field_num", "date", "NDVI", "NDRE"]].rename(columns={"NDVI": "NDVI_inner", "NDRE": "NDRE_inner"})
    both = full.merge(inner, on=["zone", "field_num", "date"], how="left")

    rows = []
    for (zone, field), g in both.groupby(["zone", "field_num"]):
        g = g[g.date >= g.sown.iloc[0]]
        ok = g[g.usable_look]
        gp = gaps(list(ok.date), g.sown.iloc[0], end)
        dif = (ok.NDVI - ok.NDVI_inner).abs()
        rows.append(dict(
            zone=zone, field_num=field, crops=g.crops.iloc[0], sown=g.sown.iloc[0].date(), audit_ends=end.date(),
            passes=len(g), usable_looks=len(ok), usable_share=round(len(ok) / len(g), 2) if len(g) else np.nan,
            kept_by_tile_rule=int(g.kept_by_tile_rule.sum()),
            usable_and_kept_by_tile_rule=int((g.usable_look & g.kept_by_tile_rule).sum()),
            usable_but_dropped_by_tile_rule=int((g.usable_look & ~g.kept_by_tile_rule).sum()),
            kept_by_tile_rule_but_not_usable=int((~g.usable_look & g.kept_by_tile_rule).sum()),
            longest_gap_days=max(gp), median_gap_days=float(np.median(gp)),
            mean_abs_ndvi_difference_full_vs_inner=round(float(dif.mean()), 4) if len(dif.dropna()) else np.nan))
    summary = pd.DataFrame(rows)
    summary.to_csv(os.path.join(OUT, "observability_by_field.csv"), index=False)
    pd.set_option("display.width", 250)
    print(summary.to_string(index=False))

    # ---- ground photos next to satellite looks ----
    gpath = os.path.join(ROOT, "data", "ground_photo_greenness.csv")
    photos = None
    if os.path.exists(gpath):
        photos = pd.read_csv(gpath, dtype={"field": str})
        photos["date"] = pd.to_datetime(photos["date"])
        ov = photos[photos.slot == "overview"].copy()
        ov["field_num"] = ov.field.astype(int)
        pairs = []
        for r in full[full.usable_look].itertuples():
            c = ov[(ov.zone == r.zone) & (ov.field_num == r.field_num)]
            if c.empty:
                continue
            lag = (c.date - r.date).dt.days
            i = lag.abs().idxmin()
            if abs(lag[i]) <= PAIR_DAYS:
                pairs.append(dict(zone=r.zone, field_num=r.field_num, satellite_date=r.date.date(), photo_date=c.date[i].date(),
                                  photo_minus_satellite_days=int(lag[i]), NDVI=r.NDVI, NDRE=r.NDRE,
                                  photo_green_fraction=c.green_fraction[i], photo_gcc=c.gcc[i], photo_file=c.file[i]))
        pd.DataFrame(pairs).to_csv(os.path.join(OUT, "ground_satellite_pairs.csv"), index=False)
        print("usable satellite looks with a ground photo within %d days: %d" % (PAIR_DAYS, len(pairs)))

    sar = rain = None
    if a.sar:
        sar = pd.read_csv(a.sar); sar["date"] = pd.to_datetime(sar["date"])
        sar = sar.dropna(subset=["RVI"])              # a scene that only borders the fields gives empty rows
    if a.rain:
        rain = pd.read_csv(a.rain); rain["date"] = pd.to_datetime(rain["date"])

    # ---- radar inside the longest optical gap ----
    if sar is not None:
        rows = []
        for (zone, f), g in full.groupby(["zone", "field_num"]):
            ok = sorted(g[g.usable_look & (g.days_after_sowing >= 0)].date)
            pts = [g.sown.iloc[0]] + ok + [end]
            a0, b0 = max(zip(pts[:-1], pts[1:]), key=lambda p: (p[1] - p[0]).days)
            sf = sar[(sar.zone == zone) & (sar.field_num == f)].sort_values("date")
            inside = sf[(sf.date > a0) & (sf.date < b0)]
            rows.append(dict(zone=zone, field_num=f, gap_start=a0.date(), gap_end=b0.date(), gap_days=(b0 - a0).days,
                             radar_passes_total=len(sf), radar_passes_in_gap=len(inside),
                             rvi_first_in_gap=round(inside.RVI.iloc[0], 2) if len(inside) else np.nan,
                             rvi_last_in_gap=round(inside.RVI.iloc[-1], 2) if len(inside) else np.nan,
                             rvi_min_in_gap=round(inside.RVI.min(), 2) if len(inside) else np.nan,
                             rvi_max_in_gap=round(inside.RVI.max(), 2) if len(inside) else np.nan))
        pd.DataFrame(rows).to_csv(os.path.join(OUT, "radar_in_optical_gap.csv"), index=False)

        # NDVI and RVI are different quantities, so each gets its own row of panels
        for zone in sorted(full.zone.unique()):
            z = full[(full.zone == zone) & full.usable_look]
            fl = sorted(full[full.zone == zone].field_num.unique())
            fig, axes = plt.subplots(2, len(fl), figsize=(2.6 * len(fl) + 1, 5), sharex=True, sharey="row",
                                     constrained_layout=True, squeeze=False)
            for j, f in enumerate(fl):
                g = z[z.field_num == f]; sf = sar[(sar.zone == zone) & (sar.field_num == f)].sort_values("date")
                sown = full[(full.zone == zone) & (full.field_num == f)].sown.iloc[0]
                axes[0, j].plot(g.date, g.NDVI, "o", color="#1f77b4", ms=6)
                axes[1, j].plot(sf.date, sf.RVI, "s-", color="#6a4c93", ms=5, lw=1.2)
                for ax in axes[:, j]:
                    ax.axvline(sown, color="#555555", ls=":", lw=1); ax.grid(alpha=0.2)
                axes[0, j].set_title(f"Field {f}", fontsize=10)
                axes[1, j].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
                axes[1, j].xaxis.set_major_locator(mdates.MonthLocator())
            axes[0, 0].set_ylabel("NDVI, usable optical looks"); axes[1, 0].set_ylabel("RVI, radar (one orbit)")
            axes[0, 0].set_ylim(0, 1); axes[1, 0].set_ylim(0, 1)
            fig.suptitle(f"{zone.capitalize()}: optical and radar series per field (dotted line = sowing)", fontsize=12)
            fig.savefig(os.path.join(OUT, f"optical_radar_series_{zone}.png"), dpi=160); plt.close(fig)

    # ---- rain on the day of each pass ----
    if rain is not None:
        rows = []
        for src in sorted(rain.source.unique()):
            m = full[full.days_after_sowing >= 0].merge(rain[rain.source == src][["zone", "date", "rain_mm"]], on=["zone", "date"])
            for zone, g in m.groupby("zone"):
                for lab, h in (("usable", g[g.usable_look]), ("not usable", g[~g.usable_look])):
                    rows.append(dict(source=src, zone=zone, field_pass=lab, field_passes=len(h),
                                     median_rain_mm=round(h.rain_mm.median(), 1) if len(h) else np.nan,
                                     share_with_rain_2p5mm=round((h.rain_mm >= 2.5).mean(), 2) if len(h) else np.nan))
        pd.DataFrame(rows).to_csv(os.path.join(OUT, "rain_on_pass_days.csv"), index=False)
        rain["month"] = rain.date.dt.strftime("%Y-%m")
        mon = rain.groupby(["source", "zone", "month"]).agg(days=("rain_mm", "size"), rain_mm=("rain_mm", "sum"),
                                                          days_2p5mm_or_more=("rain_mm", lambda x: int((x >= 2.5).sum()))).round(0).reset_index()
        mon.to_csv(os.path.join(OUT, "rain_by_month.csv"), index=False)

    # ---- one timeline per zone: every observation system on the same time axis ----
    for zone in sorted(full.zone.unique()):
        z = full[full.zone == zone]
        fields = sorted(z.field_num.unique())
        nrows = len(fields) + (1 if rain is not None else 0)
        fig, axes = plt.subplots(nrows, 1, figsize=(13, 1.25 * nrows + 1.6), sharex=True, constrained_layout=True,
                                 gridspec_kw=dict(height_ratios=[1] * len(fields) + ([1.3] if rain is not None else [])))
        axes = np.atleast_1d(axes)
        for ax, f in zip(axes, fields):
            g = z[z.field_num == f]
            ax.axvline(g.sown.iloc[0], color="#555555", lw=1, ls=":")
            no = g[~g.usable_look]; ok = g[g.usable_look]
            ax.scatter(no.date, [2] * len(no), s=38, facecolors="none", edgecolors="#9aa5b8", lw=1.1)
            ax.scatter(ok.date, [2] * len(ok), s=46, color="#1f77b4", zorder=3)
            old = g[g.kept_by_tile_rule]
            ax.scatter(old.date, [2] * len(old), s=130, facecolors="none", edgecolors="#d1495b", lw=1.0, zorder=2)
            if sar is not None:
                s = sar[(sar.zone == zone) & (sar.field_num == f)].drop_duplicates("date")
                ax.scatter(s.date, [1] * len(s), s=26, marker="s", color="#6a4c93")
            if photos is not None:
                p = photos[(photos.zone == zone) & (photos.slot == "overview") & (photos.field == str(f))]
                ax.scatter(p.date, [0] * len(p), s=46, marker="^", color="#3a7d44")
            ax.set_yticks([0, 1, 2]); ax.set_yticklabels(["ground photo", "Sentinel-1 radar", "Sentinel-2 optical"], fontsize=8)
            ax.set_ylim(-0.6, 2.6); ax.grid(axis="x", alpha=0.2)
            ax.set_title(f"Field {f}: {g.crops.iloc[0]}", loc="left", fontsize=10)
        if rain is not None:
            ax = axes[-1]
            for src, col in (("CHIRPS", "#2e86ab"), ("ERA5-Land", "#b5651d")):
                r = rain[(rain.zone == zone) & (rain.source == src)]
                ax.bar(r.date, r.rain_mm, width=0.9, color=col, alpha=0.6, label=src)
            ax.set_ylabel("rain (mm/day)", fontsize=8); ax.legend(frameon=False, fontsize=8, ncol=2)
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        handles = [plt.Line2D([], [], marker="o", ls="", color="#1f77b4", ms=7, label="pass, field usable"),
                   plt.Line2D([], [], marker="o", ls="", mfc="none", mec="#9aa5b8", ms=7, label="pass, field not usable"),
                   plt.Line2D([], [], marker="o", ls="", mfc="none", mec="#d1495b", ms=11, label="kept by the tile-wide 40% rule"),
                   plt.Line2D([], [], marker="s", ls="", color="#6a4c93", ms=6, label="radar pass"),
                   plt.Line2D([], [], marker="^", ls="", color="#3a7d44", ms=7, label="ground photo"),
                   plt.Line2D([], [], ls=":", color="#555555", label="sowing")]
        fig.legend(handles=handles, loc="outside lower center", ncol=6, frameon=False, fontsize=9)
        fig.suptitle(f"{zone.capitalize()}: every look at each field, from the ground and from orbit", fontsize=13)
        fig.savefig(os.path.join(OUT, f"observation_timeline_{zone}.png"), dpi=160)
        plt.close(fig)


if __name__ == "__main__":
    main()
