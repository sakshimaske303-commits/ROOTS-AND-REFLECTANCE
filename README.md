# ROOTS & REFLECTANCE

**What can a satellite actually know about a sub-hectare monsoon field?**

Seven family fields in Wardha district, Vidarbha (five in Sawardoh, two in
Karanja Ghadge), sown on 22 and 27 June 2026 with cotton, pigeon pea,
soyabean and turmeric. The fields are 0.22 to about 1 ha. I visit them
every week and photograph each one; this repo measures how much of that
season the satellites could see, how many of their pixels really belong to
each field, and how the satellite record compares with what was on the
ground.

The question matters outside these seven fields. Crop monitoring, yield
estimation and satellite-indexed crop insurance all assume that a small
rain-fed field can be observed from orbit during the kharif season. Most
Vidarbha holdings are this size, and the season is the cloudiest part of
the year.

The full design is in `docs/RESEARCH_DESIGN.md`. The weekly field routine
is in `docs/FIELD_PROTOCOL.md`.

## Where the work stands (8 Oct 2026)

Done, from data already in this repo:

- **Pixel support.** How many Sentinel-2 pixels fall inside each field, and
  how many are pure (whole pixel inside the boundary). Field 1 in Sawardoh
  (0.22 ha) has 10 pure pixels at 10 m and none at 20 m, so a red-edge
  index for that field is always mixed with its neighbours.
  `output/pixel_purity.csv`, `output/pixel_grid_*.png`
- **Ground photo record.** 85 weekly photos from 23 Aug to 4 Oct, indexed
  by date, field and subject. Position and time are read from the stamp
  printed on each photo. 44 of 47 field-overview photos were taken within
  10 m of that field's usual spot. Every overview photo was taken within
  14 m of the field edge (median 2.8 m).
  `data/ground_photo_index.csv`, `data/ground_photo_positions.csv`,
  `output/photo_position_spread.csv`, `output/photo_positions_*.png`
- **Photo greenness.** Green share of each overview photo, as a rough
  ground-side greenness series. Lighting and framing vary, so this is
  indicative only. `data/ground_photo_greenness.csv`

- **Observability audit (run 8 Oct, passes to 2 Oct).** Sentinel-2 passed
  over the fields 25 or 26 times after sowing. Sawardoh fields 1 to 4 were
  usable on 4 of those passes, field 5 on 3, the Karanja fields on 5. No
  field had a usable look between 14 Jul and mid-September: 65 days at
  Karanja, 70 at Sawardoh fields 1 to 4, 75 at field 5. In that gap NDVI
  went from about 0.3 to about 0.7 or 0.8 with no observation of the rise.
  The tile-wide 40% rule did not drop any pass on which a field was usable;
  it kept one or two per Sawardoh field on which the field was not.
  `output/observability_by_field.csv`, `output/observability_passes.csv`,
  `output/observation_timeline_*.png`
- **Ground and satellite pairs.** 22 usable satellite looks have a ground
  photo within three days, all from 17 Sep onwards. In Karanja the same
  photo is paired with two satellite dates, so the pairs are not 22
  independent comparisons. `output/ground_satellite_pairs.csv`

- **Radar in the optical gap.** Sentinel-1 gave 8 passes from one orbit
  (28 Jun to 27 Sep, every 12 days), 6 of them inside each field's optical
  gap. RVI rises through the gap in the cotton fields (Sawardoh 3 and 5) and
  in Karanja. In Sawardoh field 1 it was already 0.75 six days after
  sowing, when the ground was bare, and in field 2 it stays near 0.6 all
  season. So radar fills the gap in time, but in the smallest field and
  the field with orange trees it is not reading the crop. No speckle
  filter is applied. `output/radar_in_optical_gap.csv`,
  `output/optical_radar_series_*.png`
- **Rainfall.** CHIRPS (to 31 Aug) and ERA5-Land (to 30 Sep) agree on June
  and July (about 350 to 380 mm in July) and disagree on August (about 100
  against 160 mm). More than half of the passes on which a field was not
  usable had 2.5 mm or more of rain that day. `output/rain_by_month.csv`,
  `output/rain_on_pass_days.csv`

Not started:

- Crop-stage log, harvest log and farm ledger (`data/*.csv` templates are
  empty).

## Known limits

- The satellite series in `data/roots_reflectance_ndvi_ndre.csv` has two
  dates, 21 Jun and 14 Jul. The first is the day before sowing, so it is a
  bare-soil baseline, not a crop observation.
- Ground photos start on 23 Aug and the first usable satellite look after
  that is 17 Sep, so the two records overlap only for the last three weeks.
- The pass of 7 Oct had no Cloud Score+ value at export time and is left
  out until the next export.
- That first extraction kept a pass only if the whole 110 km tile was under
  40% cloud. A pass can fail that test and still be clear over a 1 ha
  field, and the reverse. The audit script replaces it with a field-level
  test.
- The NDRE in that file pairs a 10 m band (B8) with a 20 m band (B5). The
  audit script uses B8A and B5, both 20 m.
- The ground photos are taken from the field edge. Pure pixels start 10 m
  inside the boundary. The two records describe different parts of the
  field until the straight-down interior photos in the field protocol
  begin.
- The fields differ in crop mix, size, soil and village at the same time,
  with one field per combination. This design cannot say whether
  intercropping changes the canopy curve, and the project does not claim
  it.
- A 356 m² triangle between Sawardoh fields 1, 2 and 4 belongs to no field
  in `data/field_boundaries.geojson`. It needs a check on the ground.
- Seven fields, one family, one season. This is a measured case, not a
  sample of Vidarbha.

## Structure

```
docs/
  RESEARCH_DESIGN.md         Question, measurements, what would count as a result
  FIELD_PROTOCOL.md          Weekly photo and record routine
src/
  fields.py                  Field boundary definitions
  pixel_purity.py            Pixel counts and pure-pixel share per field
  photo_metadata.py          Reads position and time from the photo stamps
  photo_greenness.py         Green share of each overview photo
  gee_observability_audit.js Earth Engine: every Sentinel-2 pass, per field
  gee_extract_sar.js         Earth Engine: Sentinel-1 RVI, every pass
  gee_extract_rain.js        Earth Engine: CHIRPS and ERA5-Land daily rain
  observability.py           Usable passes, gaps, ground-satellite pairs
  gee_extract_indices.js     First extraction (tile-wide cloud filter); kept for the record
  analyze.py                 Charts for the first extraction
data/
  field_boundaries.geojson   The 7 field polygons
  ground_photo_index.csv     One row per photo: date, zone, field, subject
  ground_photo_positions.csv Position and time from each stamp
  ground_photo_greenness.csv Green share per overview photo
  photo_points.csv           Fixed photo point A per field
  crop_stage_log.csv         Weekly crop stage (template)
  harvest_log.csv            Pickings and harvest weights (template)
  farm_ledger.csv            Costs and sales per field (template)
output/                      Tables and charts written by the scripts
```

`geotagged_images/` holds the original photos.

## Run order

```
pip install -r requirements.txt        # photo_metadata.py also needs Tesseract

python src/pixel_purity.py
python src/photo_metadata.py
python src/photo_greenness.py
```

Then I run `gee_observability_audit.js`, `gee_extract_sar.js` and
`gee_extract_rain.js` in the Earth Engine Code Editor
(<https://code.earthengine.google.com/>), start each export from the Tasks
tab, and download the three CSVs from the `ROOTS_REFLECTANCE` Drive folder
into `data/`.

```
python src/observability.py data/roots_reflectance_s2_audit.csv \
    --sar data/roots_reflectance_sar.csv --rain data/roots_reflectance_rain.csv
```

This writes `observability_by_field.csv`, `observability_passes.csv`,
`ground_satellite_pairs.csv`, `radar_in_optical_gap.csv`,
`rain_on_pass_days.csv`, `rain_by_month.csv`, one timeline chart and one
optical/radar chart per zone into `output/`.

## How a pass is judged usable

A Sentinel-2 pass counts for a field when at least 80% of the field's
pixels have a Cloud Score+ value (`cs_cdf`) of 0.60 or more and are not
flagged cloud or shadow in the scene classification. Both thresholds are
set at the top of the scripts, so the counts can be rerun at other
settings.

## Why a radar series

Sentinel-1 is not blocked by cloud. Its Radar Vegetation Index measures
canopy structure, which is a different quantity from NDVI, so it is plotted
separately and never used to fill NDVI gaps. Passes are kept apart by orbit
direction and relative orbit because viewing geometry changes the value.

## License

MIT, see `LICENSE`.
