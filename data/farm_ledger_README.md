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
