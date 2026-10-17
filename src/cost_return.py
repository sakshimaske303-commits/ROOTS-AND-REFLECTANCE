"""
ROOTS & REFLECTANCE — what the season cost and returned, per field and per hectare.

Input:  data/farm_ledger.csv, data/harvest_log.csv, data/field_boundaries.geojson
Output: output/cost_return_by_field.csv
        output/sales_vs_msp.csv

Rules
  - A cost written against several fields ("1;3") or "all" is shared by area, within
    the zone named on that row.
  - Paid costs and own inputs are kept apart. Family labour has no cash price; it is
    counted in person-days, and valued only if OWN_LABOUR_RS_PER_DAY is set (pass a
    local daily wage on the command line). Both versions are written, so the cash
    picture and the full-cost picture can be read side by side.
  - Revenue counts what was sold, at the price received. Produce kept at home is
    reported in kg and valued at the field's own average sale price for that crop,
    in a separate column.
  - MSP is the Centre's 2026-27 kharif minimum support price (PIB, 13 May 2026), used
    only as a reference line for the price received. Cotton is compared with the
    medium-staple MSP unless the harvest row says "long staple" in notes.

Usage:  python src/cost_return.py [OWN_LABOUR_RS_PER_DAY]
"""
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Rs per quintal, kharif marketing season 2026-27 (PIB release, 13 May 2026)
MSP_2026_27 = {
    "cotton": 8267,            # medium staple
    "cotton_long": 8667,       # long staple
    "soyabean": 5708,          # yellow
    "tur": 8450,
    "moong": 8780,
    "urad": 8200,
}


def field_areas():
    with open(os.path.join(ROOT, "data", "field_boundaries.geojson"), encoding="utf-8") as f:
        gj = json.load(f)
    return {(ft["properties"]["zone"], str(ft["properties"]["field_num"])): float(ft["properties"]["area_ha"])
            for ft in gj["features"]}


def split_rows(ledger, areas):
    """One output row per (ledger row, field), amount and quantity shared by area."""
    out = []
    for _, r in ledger.iterrows():
        zone = str(r["zone"]).strip().lower()
        spec = str(r["field"]).strip().lower()
        zone_fields = [f for (z, f) in areas if z == zone]
        targets = zone_fields if spec == "all" else [s.strip() for s in spec.split(";") if s.strip()]
        total = sum(areas[(zone, f)] for f in targets)
        for f in targets:
            share = areas[(zone, f)] / total
            out.append(dict(zone=zone, field=f, category=r["category"], item=r["item"],
                            unit=str(r["unit"]).strip().lower(),
                            quantity=pd.to_numeric(r["quantity"], errors="coerce") * share,
                            amount_rs=pd.to_numeric(r["amount_rs"], errors="coerce") * share,
                            paid_or_own=str(r["paid_or_own"]).strip().lower()))
    return pd.DataFrame(out)


def main():
    wage = float(sys.argv[1]) if len(sys.argv) > 1 else None
    areas = field_areas()
    ledger = pd.read_csv(os.path.join(ROOT, "data", "farm_ledger.csv"), dtype=str)
    harvest = pd.read_csv(os.path.join(ROOT, "data", "harvest_log.csv"), dtype=str)
    if ledger.empty and harvest.empty:
        sys.exit("farm_ledger.csv and harvest_log.csv are still empty. Nothing to compute yet.")

    costs = split_rows(ledger, areas) if not ledger.empty else pd.DataFrame(
        columns=["zone", "field", "category", "unit", "quantity", "amount_rs", "paid_or_own"])

    h = harvest.copy()
    for c in ("quantity_kg", "sold_kg", "price_rs_per_quintal"):
        h[c] = pd.to_numeric(h[c], errors="coerce")
    h["zone"] = h["zone"].str.strip().str.lower()
    h["field"] = h["field"].astype(str).str.strip()
    h["crop"] = h["crop"].str.strip().str.lower()
    h["revenue_rs"] = h["sold_kg"].fillna(0) / 100 * h["price_rs_per_quintal"].fillna(0)

    rows = []
    for (zone, f), area in sorted(areas.items()):
        c = costs[(costs["zone"] == zone) & (costs["field"] == f)]
        paid = c.loc[c["paid_or_own"] == "paid", "amount_rs"].sum()
        own_days = c.loc[(c["paid_or_own"] == "own") & (c["category"] == "labour") &
                         c["unit"].str.contains("day", na=False), "quantity"].sum()
        hh = h[(h["zone"] == zone) & (h["field"] == f)]
        revenue = hh["revenue_rs"].sum()
        kept_value = 0.0
        for crop, g in hh.groupby("crop"):
            sold = g["sold_kg"].sum()
            avg_price = (g["revenue_rs"].sum() / sold * 100) if sold else float("nan")
            kept = g["quantity_kg"].sum() - sold
            if kept > 0 and avg_price == avg_price:
                kept_value += kept / 100 * avg_price
        r = dict(zone=zone, field=f, area_ha=area,
                 paid_cost_rs=round(paid), own_labour_days=round(own_days, 1),
                 harvest_kg=round(hh["quantity_kg"].sum(), 1), sold_kg=round(hh["sold_kg"].sum(), 1),
                 revenue_rs=round(revenue), kept_produce_value_rs=round(kept_value),
                 cash_margin_rs=round(revenue - paid),
                 cash_margin_rs_per_ha=round((revenue - paid) / area))
        if wage is not None:
            full = paid + own_days * wage
            r["own_labour_value_rs"] = round(own_days * wage)
            r["margin_after_own_labour_rs_per_ha"] = round((revenue + kept_value - full) / area)
        rows.append(r)
    table = pd.DataFrame(rows)
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    table.to_csv(os.path.join(ROOT, "output", "cost_return_by_field.csv"), index=False)
    pd.set_option("display.width", 250)
    print(table.to_string(index=False))

    sales = h[h["sold_kg"].fillna(0) > 0].copy()
    if not sales.empty:
        def msp(row):
            if row["crop"] == "cotton" and "long" in str(row.get("notes", "")).lower():
                return MSP_2026_27["cotton_long"]
            return MSP_2026_27.get(row["crop"])
        sales["msp_rs_per_quintal"] = sales.apply(msp, axis=1)
        sales["price_minus_msp"] = sales["price_rs_per_quintal"] - sales["msp_rs_per_quintal"]
        sales[["date", "zone", "field", "crop", "sold_kg", "price_rs_per_quintal", "where_sold",
               "msp_rs_per_quintal", "price_minus_msp"]].to_csv(
            os.path.join(ROOT, "output", "sales_vs_msp.csv"), index=False)
        print("\nSales against MSP 2026-27 written to output/sales_vs_msp.csv")


if __name__ == "__main__":
    main()
