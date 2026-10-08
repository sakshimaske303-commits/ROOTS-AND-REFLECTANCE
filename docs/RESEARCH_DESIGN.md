# Research design

## The question

During a monsoon season, what can a satellite actually know about a field of less than one hectare,
when, and how far can that be trusted?

I can answer this for my own fields because I hold three things that satellite studies of large
areas usually do not: the sowing date of each field, the field boundary walked on the ground, and
a look at the crop from the ground every week.

This replaces the question the project started with ("do intercropped fields close their canopy
differently?"). Seven fields cannot answer that one. Fields 2 and 4 in Sawardoh carry orange
trees, which are green all year, so crop mix and tree cover cannot be separated, and there is no
replication. The crop-mix comparison stays in the project as description, not as a finding.

## Four measurements

| # | Measurement | What it shows | Where |
|---|---|---|---|
| 1 | **Pixel support** | How many Sentinel-2 pixels a field mean rests on, and how many of them lie wholly inside the field | `src/pixel_purity.py` |
| 2 | **Observability** | Of every Sentinel-2 pass since sowing, on how many each field was usable; what a tile-wide cloud filter keeps and drops; how long the blind stretches are and which weeks of crop growth fall in them | `src/gee_observability_audit.js`, `src/observability.py` |
| 3 | **Ground record** | Where and when each weekly photo was taken (read from the stamp on the photo), how repeatable the photo positions are, and a greenness number from each photo | `src/photo_metadata.py`, `src/photo_greenness.py` |
| 4 | **Agreement** | For satellite looks that have a ground photo within three days: does the satellite index move with what is seen on the ground? Radar (Sentinel-1) is carried alongside as the sensor that cloud does not stop | `src/observability.py`, `src/gee_extract_sar.js` |

Rainfall (`src/gee_extract_rain.js`) is the context for both: it is why the optical sensor is blind
and it is what the crop responds to.

## The same work, read as economics

Satellite data is increasingly proposed as the basis for crop insurance payouts, yield estimates
and advisories for small farms. All of these assume the field can be observed when it matters.
Measurement 2 tests that assumption directly, on fields where the truth is known.

- **Basis risk.** If an index (a satellite greenness value, say) is used to decide a payout, the
  farmer carries the risk that the index and the real loss differ. Blind stretches during the
  monsoon, and field means built mostly from boundary pixels on small plots, are two concrete
  sources of that difference. This project measures both for seven real fields.
- **Farm ledger.** `data/farm_ledger.csv` and `data/harvest_log.csv` record costs, labour, harvest
  and prices per field. They give cost and return per hectare for each crop mix: a description of
  intercropping as a way of spreading risk on a smallholding. With seven fields in one season it
  is a case description, not an estimate of an effect.

I write statements about how Indian crop insurance uses satellite data only after checking them
against the scheme's own documents or government statements.

## What this project cannot show

- Anything about cause. There is no control, no replication and one season.
- Canopy cover in absolute terms from the photos taken so far. They are oblique and were all
  taken from the field edge (see Development Log). Photos taken straight down at fixed points
  (see `docs/FIELD_PROTOCOL.md`) are needed for that.
- Yield from satellite data. The harvest log will give the yields; relating them to the
  satellite series with seven fields would be curve-fitting.
- Anything beyond these seven fields in two villages.
