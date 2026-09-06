# Development Log — ROOTS & REFLECTANCE

A running log of how this project came together, from the first boundary walk
to the satellite cross-validation pipeline. Updated as the season progresses.

## Field mapping & naming

- Walked and GPS-mapped all 7 field boundaries by hand — 5 in Sawardoh, 2 in
  Karanja Ghadge, Dist. Wardha, Maharashtra.
- Renamed the boundaries from "Patch" to "Field" across the portfolio —
  a field is what it is on the ground, not a jargon label.
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
