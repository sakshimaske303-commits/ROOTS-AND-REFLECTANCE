"""
ROOTS & REFLECTANCE: monsoon blind spot across Vidarbha, kharif 2019-2026.

Per point, field size and season: usable looks, longest gap, looks 15 Jul-15 Sep.
Regressions: field size (point x season FE), rainfall (point and season FE), errors clustered by point.

Usage: python src/regional_observability.py
"""
import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data", "regional")
OUT = os.path.join(ROOT, "output", "regional")

USABLE_MIN = 0.80
SEASON = ("06-22", "10-15")
GROWTH = ("07-15", "09-15")
LONG_GAP = 60      # days; my fields had 65 to 75


def season_bounds(year, md):
    return pd.Timestamp(f"{year}-{md[0]}"), pd.Timestamp(f"{year}-{md[1]}")


def longest_gap(dates, start, end):
    pts = [start] + sorted(dates) + [end]
    return max((b - a).days for a, b in zip(pts[:-1], pts[1:]))


def load_passes():
    files = sorted(glob.glob(os.path.join(DATA, "regional_s2_passes_*.csv")))
    if not files:
        raise SystemExit("no data/regional/regional_s2_passes_<year>.csv found")
    d = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    d["date"] = pd.to_datetime(d["date"])
    d["year"] = d["date"].dt.year
    d["usable"] = d["usable"].fillna(0.0)
    # overlapping tiles give the same field twice on one day: keep the better scene
    return d.groupby(["pid", "size_ha", "year", "date"], as_index=False)["usable"].max()


def summarise(d):
    rows = []
    for (pid, size, year), g in d.groupby(["pid", "size_ha", "year"]):
        s0, s1 = season_bounds(year, SEASON)
        g0, g1 = season_bounds(year, GROWTH)
        g = g[(g.date >= s0) & (g.date <= s1)]
        seen = g.loc[g.usable >= USABLE_MIN, "date"]
        rows.append({
            "pid": pid, "size_ha": size, "year": year,
            "pass_days": g.date.nunique(),
            "looks": len(seen),
            "looks_growth": int(((seen >= g0) & (seen <= g1)).sum()),
            "longest_gap_days": longest_gap(list(seen), s0, s1),
        })
    return pd.DataFrame(rows)


def own_fields():
    """My seven fields through the same window and rule (whole field, 2026)."""
    path = os.path.join(ROOT, "data", "roots_reflectance_s2_audit.csv")
    a = pd.read_csv(path)
    a = a[(a.footprint == "full") & a.cs.notna()].copy()
    a["date"] = pd.to_datetime(a["date"])
    a["usable"] = a["usable"].fillna(0.0)
    a = a[a.covered.fillna(0) >= 0.99]
    a = a.groupby(["zone", "field_num", "area_ha", "date"], as_index=False)["usable"].max()
    s0, s1 = season_bounds(2026, SEASON)
    g0, g1 = season_bounds(2026, GROWTH)
    out = []
    for (zone, num, area), g in a.groupby(["zone", "field_num", "area_ha"]):
        g = g[(g.date >= s0) & (g.date <= s1)]
        seen = g.loc[g.usable >= USABLE_MIN, "date"]
        out.append({"zone": zone, "field": num, "area_ha": area, "looks": len(seen),
                    "looks_growth": int(((seen >= g0) & (seen <= g1)).sum()),
                    "longest_gap_days": longest_gap(list(seen), s0, s1)})
    return pd.DataFrame(out)


# ---- regression with fixed effects absorbed and errors clustered by point ----

def demean(df, cols, groups, tol=1e-10, max_iter=500):
    """Subtract group means for one or more sets of fixed effects (alternating projections)."""
    x = df[cols].astype(float).copy()
    for _ in range(max_iter):
        before = x.copy()
        for g in groups:
            x = x - x.groupby(df[g]).transform("mean")
        if (x - before).abs().to_numpy().max() < tol:
            break
    return x


def fe_ols(df, y, xs, groups, cluster):
    df = df.dropna(subset=[y] + xs).reset_index(drop=True)
    z = demean(df, [y] + xs, groups)
    Y = z[y].to_numpy()
    X = z[xs].to_numpy()
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ Y
    u = Y - X @ b
    meat = np.zeros((len(xs), len(xs)))
    for _, idx in df.groupby(cluster).indices.items():
        s = X[idx].T @ u[idx]
        meat += np.outer(s, s)
    n, k, G = len(Y), len(xs), df[cluster].nunique()
    V = XtX_inv @ meat @ XtX_inv * (G / (G - 1)) * ((n - 1) / (n - k))
    se = np.sqrt(np.diag(V))
    t = b / se
    p = 2 * stats.t.sf(np.abs(t), G - 1)
    ci = stats.t.ppf(0.975, G - 1) * se
    return pd.DataFrame({"term": xs, "coef": b, "se": se, "ci_low": b - ci, "ci_high": b + ci,
                         "p": p, "n": n, "clusters": G})


def main():
    os.makedirs(OUT, exist_ok=True)
    pts = pd.read_csv(os.path.join(DATA, "regional_points.csv"))
    panel = summarise(load_passes()).merge(pts, on=["pid", "year"], how="left")
    panel.to_csv(os.path.join(OUT, "regional_point_seasons.csv"), index=False)

    # how the region looked each season, for a 1 ha field
    one = panel[panel.size_ha == 1.0]
    by_year = one.groupby("year").agg(
        points=("pid", "nunique"),
        pass_days_median=("pass_days", "median"),
        looks_median=("looks", "median"),
        longest_gap_median=("longest_gap_days", "median"),
        longest_gap_p25=("longest_gap_days", lambda s: s.quantile(0.25)),
        longest_gap_p75=("longest_gap_days", lambda s: s.quantile(0.75)),
        share_gap_60_or_more=("longest_gap_days", lambda s: (s >= LONG_GAP).mean()),
        share_no_look_in_growth=("looks_growth", lambda s: (s == 0).mean()),
        rain_jjas_mm_median=("rain_jjas_mm", "median"),
    ).round(3).reset_index()
    by_year.to_csv(os.path.join(OUT, "regional_by_season.csv"), index=False)

    by_district = one.groupby("district_name").agg(
        longest_gap_median=("longest_gap_days", "median"),
        share_gap_60_or_more=("longest_gap_days", lambda s: (s >= LONG_GAP).mean()),
        share_no_look_in_growth=("looks_growth", lambda s: (s == 0).mean()),
    ).round(3).reset_index()
    by_district.to_csv(os.path.join(OUT, "regional_by_district.csv"), index=False)

    # 1. field size, same point and season
    panel["point_season"] = panel["pid"].astype(str) + "_" + panel["year"].astype(str)
    panel["size_0_25ha"] = (panel.size_ha == 0.25).astype(float)
    panel["size_4ha"] = (panel.size_ha == 4.0).astype(float)
    m1 = pd.concat([
        fe_ols(panel, outcome, ["size_0_25ha", "size_4ha"], ["point_season"], "pid").assign(outcome=outcome)
        for outcome in ("looks", "looks_growth", "longest_gap_days")])

    # 2. kharif rainfall, 1 ha fields, point and season fixed effects
    one = one.assign(rain_100mm=one.rain_jjas_mm / 100.0)
    m2 = pd.concat([
        fe_ols(one, outcome, ["rain_100mm"], ["pid", "year"], "pid").assign(outcome=outcome)
        for outcome in ("looks", "looks_growth", "longest_gap_days")])

    models = pd.concat([m1.assign(model="1 field size (point x season FE; base 1 ha)"),
                        m2.assign(model="2 rainfall (point and season FE; 1 ha)")])
    cols = ["model", "outcome", "term", "coef", "se", "ci_low", "ci_high", "p", "n", "clusters"]
    models[cols].round(4).to_csv(os.path.join(OUT, "regional_models.csv"), index=False)

    mine = own_fields()
    mine.to_csv(os.path.join(OUT, "own_fields_same_window.csv"), index=False)
    share_as_long = (one[one.year == 2026].longest_gap_days >= mine.longest_gap_days.min()).mean()

    # figures
    years = sorted(one.year.unique())
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.boxplot([one[one.year == y].longest_gap_days for y in years], showfliers=False, widths=0.55)
    ax.set_xticks(range(1, len(years) + 1), [str(y) for y in years])
    if 2026 in years:
        x = years.index(2026) + 1
        ax.scatter(np.full(len(mine), x) + np.linspace(-0.15, 0.15, len(mine)), mine.longest_gap_days,
                   color="#c0392b", zorder=3, s=22, label="my seven fields, 2026")
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), frameon=False)
    ax.axhline(LONG_GAP, color="grey", lw=0.8, ls="--")
    ax.set_ylabel("longest stretch without a usable look (days)")
    ax.set_title("Vidarbha cropland, 1 ha fields: longest blind stretch of each kharif season "
                 "(22 June to 15 October)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "regional_gap_by_season.png"), dpi=150)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    for size, col in ((0.25, "#c0392b"), (1.0, "#2f5d1e"), (4.0, "#2b6cb0")):
        s = panel[panel.size_ha == size].groupby("year")["looks_growth"].apply(lambda v: (v == 0).mean())
        ax.plot(s.index, s.values, "o-", color=col, label=f"{size:g} ha")
    ax.set_ylabel("share of points with no usable look\n15 July to 15 September")
    ax.set_ylim(0, 1)
    ax.set_title("Vidarbha cropland: fields never seen in the main growing weeks, by field size")
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "regional_no_look_by_size.png"), dpi=150)

    print(by_year.to_string(index=False))
    print("\nBy district (1 ha):")
    print(by_district.to_string(index=False))
    print("\nRegressions (errors clustered by point):")
    print(models[cols].round(3).to_string(index=False))
    print("\nMy seven fields, same window and rule:")
    print(mine.to_string(index=False))
    print(f"\nShare of 1 ha points in 2026 with a gap at least as long as my shortest ({mine.longest_gap_days.min()} days): "
          f"{share_as_long:.2f}")


if __name__ == "__main__":
    main()
