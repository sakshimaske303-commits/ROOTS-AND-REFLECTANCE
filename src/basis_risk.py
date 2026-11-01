"""
ROOTS & REFLECTANCE: fall in margin per field against the claim paid.

Usage: python src/basis_risk.py
"""
import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def rupees(text):
    """'0 so far' -> 0, '1300' -> 1300, 'not known' or a range -> None."""
    s = str(text).strip().lower()
    if s in ("", "nan", "not known"):
        return None
    m = re.fullmatch(r"([0-9][0-9,]*)( so far)?", s)
    return float(m.group(1).replace(",", "")) if m else None


def main():
    fig = pd.read_csv(os.path.join(ROOT, "data", "season_figures_2026.csv"))
    ins = pd.read_csv(os.path.join(ROOT, "data", "insurance_check.csv"))
    ins = ins[["zone", "field", "crop_insured", "premium_rs", "loss_reported", "claim_paid_rs"]]
    d = fig.merge(ins, on=["zone", "field"], how="left")
    d["margin_fall_rs"] = ((d.margin_normal_year_rs_per_ha - d.margin_rs_per_ha) * d.area_ha).round(-2)
    d["paid_rs"] = d.claim_paid_rs.map(rupees)
    d["premium_rs_known"] = d.premium_rs.map(rupees)
    d["uncovered_rs"] = d.margin_fall_rs - d.paid_rs
    cols = ["zone", "field", "farmer_code", "area_ha", "crop_insured", "premium_rs", "margin_fall_rs",
            "claim_paid_rs", "paid_rs", "uncovered_rs"]
    d[cols].to_csv(os.path.join(ROOT, "output", "basis_risk.csv"), index=False)
    print(d[cols].to_string(index=False))
    known = d.dropna(subset=["paid_rs"])
    print(f"\nFall in margin, all seven fields: Rs {d.margin_fall_rs.sum():,.0f}")
    print(f"Paid so far, {len(known)} fields with a known answer: Rs {known.paid_rs.sum():,.0f} "
          f"against a fall of Rs {known.margin_fall_rs.sum():,.0f} on those fields")
    print(f"Premiums with a known amount: Rs {d.premium_rs_known.sum():,.0f}")


if __name__ == "__main__":
    main()
