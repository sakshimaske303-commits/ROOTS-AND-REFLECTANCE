# ROOTS & REFLECTANCE — Satellite Analysis

This is where I cross-validate my weekly ground-truth geotagged photos
against actual Sentinel-2 satellite vegetation indices (NDVI and NDRE), for
all 7 fields I've mapped — 5 in Sawardoh, 2 in Karanja Ghadge. It's the
companion analysis repo to the main ROOTS & REFLECTANCE project on my
portfolio (GEOSPATIAL-PORTFOLIO).

## What this shows

For each field, I track a canopy-vigour time series (NDVI) and a red-edge /
chlorophyll time series (NDRE) from sowing date to the present, pulled
directly from Sentinel-2 imagery. I can then compare fields with different
crop mixes (pure cotton vs. cotton+tur intercropped vs. soyabean+tur) side
by side to see whether intercropping changes the canopy-closure curve — a
genuine, ground-truthed remote sensing finding, not just a satellite pass
gimmick.

## Structure

```
src/
  fields.py                 Field boundary definitions (mirrors the portfolio's
                             index.html exactly — same corner coordinates)
  gee_extract_indices.js    Google Earth Engine Code Editor script — pulls
                             Sentinel-2, computes NDVI/NDRE, exports a CSV
  analyze.py                Python analysis of the exported CSV — produces
                             per-field charts, a cross-field comparison chart
                             per zone, and a summary table
data/
  field_boundaries.geojson  The 7 field polygons as GeoJSON (generated from
                             fields.py — regenerate with `python3 src/fields.py
                             > data/field_boundaries.geojson` if a boundary
                             is ever corrected on the portfolio side)
output/
  (created by analyze.py — charts + summary CSV land here)
```

## How to run it

**Step 1 — pull the satellite data (Google Earth Engine Code Editor):**

1. Open <https://code.earthengine.google.com/> and sign in with a Google
   account that has Earth Engine access (free non-commercial registration at
   <https://earthengine.google.com/signup/> if not already done).
2. Paste the full contents of `src/gee_extract_indices.js` into a new script.
3. Click **Run**. The Console will print the field count and how many
   cloud-filtered Sentinel-2 images were found.
4. Open the **Tasks** tab (top right) and click **Run** next to the export
   task (`roots_reflectance_ndvi_ndre`). This exports a CSV to a
   `ROOTS_REFLECTANCE` folder in your Google Drive.
5. Download that CSV from Drive.

**Step 2 — run the analysis:**

```
python3 src/analyze.py path/to/roots_reflectance_ndvi_ndre.csv
```

This writes per-field NDVI/NDRE charts, a per-zone comparison chart, and a
`field_summary.csv` into `output/`.

**Re-running later in the season:** my script's end date is always "today",
so whenever I re-run it, it just pulls whatever new Sentinel-2 passes have
come in since my last export — I don't touch the code. Each field keeps one
chart that accumulates every date I've collected so far, not a new chart
every week — running `analyze.py` again on a fresher CSV just redraws that
same chart with the new points added on. I plan to re-run this alongside my
weekly ground-photo log, though my satellite dates won't always land on the
same day as my photos — Sentinel-2 revisits roughly every 5 days, but only
the cloud-free passes are usable, so some weeks I get more than one date and
some weeks none.

## Why I use the Code Editor and not a local Python script

Earth Engine needs a live, OAuth-authenticated Google login to pull imagery.
I use the Code Editor because it already runs that login in my browser, so I
don't have to manage a separate credential setup — and it's the same Earth
Engine tooling I already use for the ESA/EO College coursework, so it
doubles as practice with it.
