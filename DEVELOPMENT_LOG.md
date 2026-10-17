# Development Log — ROOTS & REFLECTANCE

A running log of how this project came together, from the first boundary walk
to the satellite cross-validation pipeline. Updated as the season progresses.

## Field mapping & naming

- Walked and GPS-mapped all 7 field boundaries by hand — 5 in Sawardoh, 2 in
  Karanja Ghadge, Dist. Wardha, Maharashtra.
- Corrected Field 4 (Sawardoh) to include the turmeric rows sown alongside
  cotton, tur, and orange. Turmeric's exact sowing date is still pending
  confirmation and is marked accordingly until then.

## Weekly ground-truth log

- Built a weekly photo log per field: an overview photo for each of the 7
  fields, plus shared crop-condition photos (cotton, tur, soyabean) and a
  shared soil-texture photo. Kept these shared rather than per-field, since
  sowing happened in the same week across each zone — repeating seven
  near-identical photos would only clutter the log, not add information.
- Arranged the log table so the shared columns sit beside each field's
  overview instead of in a separate scrollable section, with a divider and a
  short note making clear which columns are per-field and which are shared
  across the zone.
- First full week logged for both zones: 23 Aug 2026.

## Satellite cross-validation

- Ground photos alone only show what a week apart looks like — wanted an
  actual quantitative cross-check, so added a Sentinel-2 NDVI/NDRE pipeline
  alongside the photo log.
- Mirrored the exact field boundaries into this standalone repo, so the
  satellite geometry always matches the map on the portfolio.
- Wrote the Earth Engine Code Editor script: cloud-masks Sentinel-2 SR using
  the QA60 band, computes NDVI (B8/B4) and NDRE (B8/B5) per field, and
  exports one CSV per run.
- Chose the Code Editor over a local script deliberately — Earth Engine
  needs a live Google login to pull imagery, and the Code Editor already
  runs that login in the browser, so there's no separate credential setup to
  manage. It's also the same Earth Engine tooling the EO College coursework
  already uses.
- Ran the first extraction: all 7 fields loaded correctly, with cloud-free
  passes limited to 2 usable dates so far — expected, given how much cloud
  cover the Vidarbha monsoon puts over June–August passes.
- Wrote the analysis script: averages out duplicate readings from adjacent
  Sentinel-2 orbit tiles landing on the same date, then produces one
  accumulating NDVI/NDRE chart per field, a cross-field comparison chart per
  zone, and a summary table.
- Generated the first real charts from the first export and reviewed them.
- Put the repo on GitHub for version control — it gets re-run and rebuilt
  most weeks as new satellite passes clear.
- Added a satellite cross-validation section to the portfolio itself,
  showing the zone comparison charts alongside a link to this repo.

## What's next

- Re-run the extraction script roughly weekly (same cadence as the ground
  photo log) so the NDVI/NDRE curves keep filling in through the season.
- Once turmeric's sowing date is confirmed, update Field 4's entry here and
  on the portfolio.
- Compare the NDVI growth curve against the ground photos week by week to
  see whether the intercropped fields (cotton + tur) show a different
  canopy-closure pattern than the single-crop fields.

## Weekly entries

Dated log of each Sunday round — ground-photo side and satellite side
tracked separately, since they don't run on the same schedule (satellite
extraction is a manual Earth Engine Code Editor step, not automatic).

**23 Aug 2026**
- First full ground-truth photo week logged for both zones — overview shot
  per field, plus shared cotton/tur/soil (Sawardoh) and soyabean/tur/soil
  (Karanja) photos.
- Ran the satellite extraction for the first time: pulled Sentinel-2 from
  20 Jun through today's run date, cloud-masked, found only 2 usable
  cloud-free dates in that whole window — 21 Jun and 14 Jul — because of how
  much cloud cover the Vidarbha monsoon puts over June–August passes.
- Ran `analyze.py` on that export: produced the 7 per-field NDVI/NDRE
  charts, the 2 cross-field comparison charts (one per zone), and
  `field_summary.csv`. Added the 2 comparison charts to the portfolio's
  satellite cross-validation section.

**30 Aug 2026** — *entry written retroactively on 6 Sep, not logged at the time*
- Ground-truth photos taken and logged for both zones (field overviews +
  shared crop/soil photos).
- Satellite extraction was not re-run this week. The Earth Engine script
  still needs a manual run in the Code Editor each time — it doesn't happen
  on its own — and that step was skipped. NDVI/NDRE data still stops at
  14 Jul.

**6 Sep 2026**
- Ground-truth photos taken and logged for both zones — full round, all 13
  slots (5 Sawardoh field overviews + cotton/tur/soil shared; 2 Karanja
  field overviews + soyabean/tur/soil shared).
- Re-ran the satellite extraction for the first time since 23 Aug —
  opened the Code Editor, ran `gee_extract_indices.js` fresh (end date
  automatically today), exported `roots_reflectance_ndvi_ndre2.csv`.
- Genuine finding, not a good one: the new export is byte-identical to the
  23 Aug export. Zero new cloud-free Sentinel-2 passes turned up anywhere
  in the 6+ weeks between 14 Jul and today. Every 7 fields are still
  sitting at exactly 2 usable dates — 21 Jun and 14 Jul. Re-ran
  `analyze.py` on the new CSV to confirm — same 7 per-field charts, same 2
  zone-comparison charts, same `field_summary.csv`, same numbers down to
  the decimal. Nothing on the portfolio needed updating because there is
  genuinely nothing new to show yet.
- This isn't a script problem — `CLOUDY_PIXEL_PERCENTAGE < 40` is already a
  reasonably generous threshold, and Sentinel-2 revisits this area every ~5
  days, so in 6+ weeks it should have found at least a few clear-enough
  passes. Vidarbha's kharif monsoon running long this year is the most
  likely explanation, but this hasn't been independently checked against
  local rainfall/cloud records — noting that as a gap rather than
  asserting it as fact.
- Keeping the weekly Code Editor re-run going regardless of whether it
  finds anything — a documented run of "still nothing" each week is itself
  useful evidence of exactly how much of this season the monsoon cloud
  cover has actually blocked satellite observation, separate from the
  NDVI/NDRE story itself.

**8 Oct 2026** — *project question changed*
- Stopped framing this as "does intercropping change the canopy-closure
  curve". With one field per crop mix, and the fields also differing in
  size, soil and village, that comparison cannot be separated from
  everything else. New question: what can a satellite know about a
  sub-hectare monsoon field, measured as observability, pixel support and
  agreement with the ground record. Written up in
  `docs/RESEARCH_DESIGN.md`.
- Pixel support (`src/pixel_purity.py`). Pure 10 m pixels per field:
  Sawardoh F1 10, F2 65, F3 56, F4 61, F5 44; Karanja F1 58, F2 72. Pure
  20 m pixels: 0, 13, 10, 12, 7, 10, 13. Sawardoh field 1 has no pure 20 m
  pixel, so its red-edge value always includes neighbouring land.
- Ground photo record. Indexed the weekly photos from 23 Aug to 4 Oct
  (`data/ground_photo_index.csv`) and read position and time from the stamp
  on each photo (`src/photo_metadata.py`, 85 of 85 read). 44 of 47 overview
  photos are within 10 m of the field's usual spot. The three that are not:
  Karanja F1 on 30 Aug (69 m), Sawardoh F2 on 23 Aug (75 m), Sawardoh F4 on
  20 Sep (46 m).
- Every overview photo was taken within 14 m of the field edge, median
  2.8 m. Pure pixels start 10 m inside. So far the photos and the pixels
  describe different parts of each field. Added a second, interior,
  straight-down photo point to the weekly routine
  (`docs/FIELD_PROTOCOL.md`).
- Photo greenness series from the overview photos
  (`src/photo_greenness.py`). Noisy because lighting and framing change
  week to week; kept as indicative only.
- Three problems found in the first extraction. (1) The cloud filter is
  tile-wide (`CLOUDY_PIXEL_PERCENTAGE < 40`), which is not a test of
  whether a 1 ha field was clear; my 6 Sep note that the threshold was
  "reasonably generous" was wrong about what it tests. (2) NDRE used B8
  (10 m) with B5 (20 m). (3) The 21 Jun pass is the day before sowing, so
  only 14 Jul is a crop observation.
- Wrote `src/gee_observability_audit.js` (every pass, per field, Cloud
  Score+ and scene classification, full field and a 10 m inner footprint),
  `src/gee_extract_rain.js` (CHIRPS and ERA5-Land) and changed
  `src/gee_extract_sar.js` to export every pass with its orbit. Wrote
  `src/observability.py` for the tables and timelines. None of these has
  been run on real data yet.
- Boundary check: a 356 m² triangle between Sawardoh fields 1, 2 and 4 is
  in no field polygon. To verify on the ground.
- `29sep6.jpeg` and `29sep13.jpeg` are the same file. `13sept12.jpeg` and
  `23aug4.jpeg` are not in the weekly log.
- Added empty templates for the crop-stage log, harvest log and farm
  ledger.

**8 Oct 2026** — *observability audit, first run*
- Ran `src/gee_observability_audit.js` in the Code Editor and exported
  `data/roots_reflectance_s2_audit.csv`: 28 pass dates from 21 Jun to
  7 Oct, every field on every pass. Ran `src/observability.py` on it.
- The 7 Oct pass had no Cloud Score+ value yet. The script first counted
  it as not usable, which is wrong (its tile cloud is 0%), so
  `observability.py` now leaves out passes that have no score and prints
  their dates. Results below run to 2 Oct.
- Usable looks after sowing: Sawardoh fields 1 to 4, 4 of 26 passes (14 Jul,
  22 Sep, 27 Sep, 2 Oct); Sawardoh field 5, 3 of 26 (on 22 Sep only 55% of
  it was usable); Karanja fields, 5 of 25 (14 Jul, 17, 22, 27 Sep, 2 Oct).
- Longest stretch with no usable look: 65 days at Karanja, 70 at Sawardoh
  fields 1 to 4, 75 at field 5. It runs from 14 Jul to mid-September. NDVI
  was about 0.3 before it and 0.63 to 0.84 after it; the whole rise is
  unobserved.
- I expected the tile-wide 40% rule to have thrown away passes on which my
  fields were clear. It did not: every usable look was also under 40% tile
  cloud. The rule failed the other way. On 17 Sep the tile was 28% cloudy
  and passed the rule, but the Sawardoh fields were not usable, while the
  Karanja fields 8 km away were. So the two exports that stopped at 14 Jul
  were right that nothing usable existed up to 6 Sep.
- Whole-field and inner-footprint NDVI differ by 0.01 to 0.03 on average.
- Ground and satellite: 22 usable looks have a photo within three days, all
  from 17 Sep on. Karanja field 2 (soyabean) fell from NDVI 0.80 on 17 Sep
  to 0.44 on 2 Oct, and the green share of its overview photo fell from
  0.93 (20 Sep) to 0.51 (29 Sep). That is one field and two photos; I am
  noting it, not calling it validation.
- Radar and rainfall scripts are still to be run.

**8 Oct 2026** — *radar and rainfall added*
- Ran `src/gee_extract_sar.js` and `src/gee_extract_rain.js`, exported
  `data/roots_reflectance_sar.csv` and `data/roots_reflectance_rain.csv`,
  and re-ran `src/observability.py` with both.
- Radar: 8 Sentinel-1 passes over the fields, all descending, relative
  orbit 165, 28 Jun to 27 Sep, 12 days apart. Half the exported rows are
  empty (a second scene that only borders the fields); the script drops
  them. 6 of the 8 passes fall inside every field's optical gap.
- What RVI shows in the gap: Karanja field 2 0.37 to 0.82, Sawardoh field 3
  0.50 to 0.67, field 5 0.48 to 0.68. These rise the way a growing canopy
  should.
- What it does not show: Sawardoh field 1 reads 0.75 on 28 Jun, six days
  after sowing, when the optical NDVI a week earlier was 0.13. At 0.22 ha
  that field is a handful of radar pixels and the value cannot be the
  crop. Field 2 (with orange trees) stays between 0.52 and 0.69 all
  season. So radar closes the gap in time, not necessarily in meaning, and
  the smaller or more mixed the field the less it says. No speckle filter
  is applied, and with one orbit there is no second geometry to check
  against.
- Rain: CHIRPS runs to 31 Aug, ERA5-Land to 30 Sep. July total 371 to
  384 mm (CHIRPS) and 349 to 360 mm (ERA5-Land). August 95 to 100 mm
  against 158 to 160 mm: the two products disagree by about 60 mm, and
  neither is a gauge in my field.
- Rain on pass days (ERA5-Land): 55% of the field-passes that were not
  usable had 2.5 mm or more of rain that day, against 25 to 29% of the
  usable ones. Those rain cells are about 11 km wide and the usable group
  is small, so this is a description, not a test.
- New outputs: `radar_in_optical_gap.csv`, `optical_radar_series_*.png`,
  `rain_on_pass_days.csv`, `rain_by_month.csv`; the timelines now carry the
  radar passes and a rain panel.

**11 Oct 2026** — *season two set up: taking the results back to the field*
- Corrected how the fields are described. Not all seven are my family's:
  some are farmed by neighbouring farmers in the two villages. The README,
  research design and portfolio text now say so. Farmers appear only as
  codes (A, B, ...); names and any notes stay in `private/`, outside git.
- Added Field Watch for the rabi season (`docs/FIELD_WATCH.md`):
  `src/gee_field_watch.js` exports every 10 m pixel per field and pass from
  1 Oct; `src/field_watch.py` flags weak patches inside a field and appends
  them to `data/field_alerts.csv`, which is committed before each ground
  visit. Tested on made-up pixels only; no real export has been run yet.
- Added `src/cost_return.py` (cost and return per field and per hectare,
  sales against the 2026-27 MSP) and empty templates for
  `field_owners.csv`, `farmer_feedback.csv` and `insurance_check.csv`.
- Context I checked this week, to be confirmed against the GR before it goes
  on the portfolio: the state's drought declaration of 25 Sep 2026 lists 7 of
  Wardha's 8 talukas, and press reports say Karanja, where both villages lie,
  is the one left out.

**11–17 Oct 2026** — *farm records and the farmers' side*
- Recorded who cultivates which field (four farmers, codes A to D), the
  17 Sep input bill, crop stages, an insurance check for Farmer A and the
  first round of feedback. Orange is in fields 2 and 4; the trees are young
  and start bearing next year. No turmeric was sown this year.
- Cotton hybrids sown in Sawardoh (mixed): Ankur, Rasi 779, Mahyco Jungee and
  Kabaddi. Cotton and tur are still standing; cotton is picked in January.
  Soyabean was harvested after the 29 Sep round. The 28 q reported for
  Karanja 2 is well above usual yields and is being rechecked.
- Worked out cost and return per field for this season with each farmer,
  from regional costs, the 2026-27 MSP and early-October prices, since none
  keeps written accounts. Each farmer went through their field's figures and
  confirmed them: `data/season_figures_2026.csv`.
- Gave each farmer their field map, measured area and season timeline. They
  agreed to keep records of costs and harvests from now on.
