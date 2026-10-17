# Field Watch (rabi 2026–27)

The kharif audit asked what a satellite can see of these fields during the monsoon. The
answer was not much: no usable optical look for 65 to 75 days. October to March is the
clear season. Field Watch asks the next question:

**On a clear pass, can 10 m pixels point to a weak patch inside a field early enough for
someone to walk there, find out what it is, and for the farmer to act?**

## The loop

| Step | What happens | Where it is recorded |
|---|---|---|
| 1. Export | `src/gee_field_watch.js` exports every 10 m pixel inside each field for every Sentinel-2 pass since 1 Oct | `data/roots_reflectance_field_watch.csv` |
| 2. Flag | `src/field_watch.py` keeps usable passes (80% rule), interior pixels only (whole pixel inside the boundary), and flags groups of 3 or more touching pixels whose NDVI is 0.10 or more below the field median | `output/field_watch/`, new rows in `data/field_alerts.csv` |
| 3. Commit first | `data/field_alerts.csv` is committed **before** the ground visit, so the commit time shows the satellite call came first | git history |
| 4. Ground check | Within 3 days I walk to the patch centre (lat/lon in the alert), take a straight-down photo and one of the surroundings, and write what is there | `visited_on`, `found_on_ground`, `ground_photos` |
| 5. Tell the farmer | I show the map and what I found. I write what they decided, if anything | `farmer_told_on`, `farmer_action`, `action_cost_rs` |
| 6. Score | Alerts issued, confirmed on the ground, acted on | end-of-season summary |

`found_on_ground` uses one of: `pest`, `disease`, `waterlogging`, `dry_patch`, `gap_in_stand`,
`weeds`, `harvested`, `nothing_visible`, `other` (described in notes).

## Limits set in advance

- Sawardoh field 1 has about 10 interior pixels. A 3-pixel patch there is a third of the field.
  Alerts for field 1 are recorded but read with that in mind.
- Fields 2 and 4 carry orange trees, which stay green. They can raise the field median and make
  crop rows look weak by comparison. Patches there are checked against the tree rows first.
- A one-pass patch can be haze or a shadow the masks missed. A patch seen on two usable passes
  in a row is marked `repeat`.
- As cotton is picked and soyabean cut, NDVI falls for reasons that are not problems.
  `harvested` is a valid ground finding, and the score is reported with and without those.
- `nothing_visible` is a result, not a failure. The share of alerts that turn out to be nothing
  is the false-alarm rate, and it is reported.

## What gets published and what does not

Published: alert table, maps, ground photos of the crop (no people), scores, farmer codes (A, B, …).
Not published: farmer names, faces, phone numbers, land record or bank details, interview notes.
Those stay in `private/`, which is not in git.
