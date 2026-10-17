# farm_ledger.csv, harvest_log.csv, crop_stage_log.csv

All three started empty. I fill them in by hand as things happen.

## farm_ledger.csv: one row per cost or piece of work

| Column | What goes in it |
|---|---|
| date | YYYY-MM-DD |
| zone | sawardoh or karanja |
| field | field number, several numbers separated by `;`, or `all` (shared by area) |
| category | seed, fertiliser, manure, pesticide, herbicide, labour, machinery, irrigation, transport, other |
| item | what exactly (for labour: the job, such as sowing, weeding, spraying, picking) |
| quantity, unit | for example 2 bags, 6 person-days, 3 hours |
| amount_rs | money paid. For family labour or own inputs I leave it empty and write `own` in the next column |
| paid_or_own | `paid` or `own` |
| notes | anything else |

## harvest_log.csv: one row per picking or sale

date, zone, field, crop, quantity_kg, sold_kg, price_rs_per_quintal, where_sold, notes

## crop_stage_log.csv: one row per field per weekly round

date, zone, field, crop, stage, height_cm, notes

## field_owners.csv: who cultivates each field (codes only)

zone, field, farmer_code (A, B, C ...), cultivated_by (`my family` or `other farmer`), notes.
Names never go in this repo. The key from code to name lives in `private/`, which is not in git.

## farmer_feedback.csv: one row each time I show a farmer something

date, farmer_code, zone, field, what_i_showed, what_they_said (a one-line summary in my words,
no quotes with names), decision, follow_up_on, outcome, notes. If someone does not want to take
part, the row says `declined` and nothing else is recorded for them.

## insurance_check.csv: crop insurance, per field, only with the farmer's permission

farmer_code, zone, field, season, enrolled (yes/no/unknown), crop_insured, insured_area_ha,
mapped_area_ha (from field_boundaries.geojson), premium_rs, loss_reported, claim_paid_rs,
payment_date, notes. No policy, Aadhaar, bank or land-record numbers.

## field_alerts.csv: Field Watch alerts (see docs/FIELD_WATCH.md)

Written by `src/field_watch.py`. The first twelve columns are filled by the script; the rest
after the ground visit.

## season_figures_2026.csv: cost and return per field, kharif 2026

Worked out with each farmer from regional costs (Vidarbha reports), normal yields from
published state figures reduced by about 45% for this drought season, and 2026-27 MSP /
early-October market prices, then gone through and confirmed by the farmer. None of the
four farmers keeps written accounts, so these are not recorded figures. Each row is
replaced by recorded figures when the farmer's own records arrive.
