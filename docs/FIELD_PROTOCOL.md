# Field protocol: weekly round

I do the same round every week, so that one week can be compared with the next.

## At each field

Every field has a fixed **point A** at its edge, where I have taken the overview photo so far
(positions in `data/photo_points.csv`, taken from the stamps on the existing photos). From this
season's remaining rounds onward I add a **point B inside each field**, at least 15 m in from
every boundary, marked with a stake. I write the position of B into `photo_points.csv` the first
time.

Why B: all 47 overview photos up to 4 October were taken within about 14 m of the field edge
(half of them within 3 m). A satellite pixel that lies wholly inside the field starts 10 m in
from the edge. My photos and the satellite have been looking at different parts of the field.

| Shot | Where | How | Why |
|---|---|---|---|
| 1. Overview | Point A | Standing, camera level, **same compass direction every week** (noted in `photo_points.csv`) | Continues the existing series |
| 2. Straight down | Point B | Arm stretched out at chest height, camera pointing straight down, no feet or shadow in frame | The share of green pixels in a straight-down photo is canopy cover. This is the number that can be compared with NDVI |
| 3. Straight down, second spot | 10 steps along the row from B | Same | One spot can sit on a gap or a tree |

- Same time of day where I can. Most rounds so far were between 8 and 10 in the morning, and I keep to that.
- The position stamp stays on, because the scripts read position and time from it.
- File names as before (`4oct1.jpeg`, ...). Each file goes into `data/ground_photo_index.csv`
  with its date, zone, field and slot (`overview`, `down1`, `down2`, `cotton`, `tur`, `soyabean`, `soil`).

## Once per round, per field: crop stage

I write one row in `data/crop_stage_log.csv`: what stage each crop is at (for cotton: vegetative, squaring,
flowering, boll formation, boll opening, picking), plant height by eye, and anything unusual
(waterlogging, pest, weeding done, spraying, picking).

## When money or work goes into a field: ledger

I write one row in `data/farm_ledger.csv` on the day, not from memory at the end of the season. If a
cost covers several fields, `all` (or the field numbers) goes under `field` and it is shared by area.
Harvest and sale go into `data/harvest_log.csv`.

## After the round

1. I add the photos to `geotagged_images/` and the rows to `data/ground_photo_index.csv`.
2. I run the three Earth Engine scripts in the Code Editor and download the three CSVs into `data/`
   (see README).
3. Then:
   ```
   python3 src/photo_metadata.py
   python3 src/photo_greenness.py
   python3 src/observability.py data/roots_reflectance_s2_audit.csv --sar data/roots_reflectance_sar.csv --rain data/roots_reflectance_rain.csv
   ```
