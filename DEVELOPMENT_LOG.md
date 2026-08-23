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

## Certifications

- Added the two EO College courses completed without an issued certificate,
  shown with a plain status note instead of a broken certificate link.
- Added two further completed-course certificates with their real
  verification IDs.

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
