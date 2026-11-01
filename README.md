# ROOTS & REFLECTANCE

**What can a satellite actually know about a sub-hectare monsoon field?**

Seven fields in Wardha district, Vidarbha (five in Sawardoh, two in
Karanja Ghadge, both villages in Karanja taluka), cultivated by five farmers: Sawardoh 2 and 3 by my family,
Sawardoh 1 and 4 by one neighbouring farmer, and Sawardoh 5, Karanja Ghadge 1 and
Karanja Ghadge 2 by one farmer each. They were sown on 22 and 27 June 2026 with cotton, pigeon pea
and soyabean. The fields are 0.22 to about 1 ha. I visit them
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

## Where the work stands (1 Nov 2026)

Done, from data already in this repo:

- **Pixel support.** How many Sentinel-2 pixels fall inside each field, and
  how many are pure (whole pixel inside the boundary). Field 1 in Sawardoh
  (0.22 ha) has 10 pure pixels at 10 m and none at 20 m, so a red-edge
  index for that field is always mixed with its neighbours.
  `output/pixel_purity.csv`, `output/pixel_grid_*.png`
- **Ground photo record.** 85 weekly photos from 23 Aug to 4 Oct (82 of them indexed; three are repeats or extras), indexed
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

Farm records (from 11 Oct):

- Who farms each field (codes only), the input bills kept for our fields, crop
  stage notes and an insurance check are in `data/`. Around 14 Oct I handed each
  of the five farmers their field map, measured area and season figures in
  person (`data/farmer_feedback.csv`). Soyabean was harvested in early October;
  cotton picking began in late October and tur is still standing.
- Farmer survey (25 Oct, a few figures checked again on 1 Nov): each farmer
  answered a two-page Marathi form in person with their own figures for cost,
  harvest, a normal year, insurance and government support, and signed or put a
  thumb impression under their answers. Answers in
  `data/farmer_survey_2026.csv`; the typed forms, with signatures blurred, in
  `docs/evidence/farmer_survey_2026_marathi.pdf` and
  `docs/evidence/farmer_survey_2026_english.pdf`.
- Cost and return per field from the survey (none of the five keeps written
  accounts): `data/season_figures_2026.csv`. Across all seven fields the
  combined margin is a loss of about Rs 65,150 this season against about
  Rs 2.83 lakh in a normal year; six of the seven fields are at a loss, and
  only field 5, which gets some canal water, is slightly positive. Cotton and
  tur figures are for the expected harvest. Labour is hired, at Rs 600 a day
  (cotton picking Rs 300 a day).
- Insurance (`data/insurance_check.csv`): every field is insured, field 2 for its
  orange trees only. All five farmers reported the drought loss at the
  agriculture office on 1 Oct and a panchnama was done; no claim has been paid yet.

Land records (from 24 Oct):

- Certified 7/12 and 8-A extracts from July 2025 for four Sawardoh survey numbers,
  with the village crop register (form 12) for 2022-23 to 2024-25. In this repo they
  appear only as records L1 to L4 with area and crops (`data/land_record_crops.csv`);
  the extracts themselves stay in `private/`.
- Matching fields to records by crop history (`src/gee_crop_history.js`,
  `src/crop_history.py`, 145 to 148 clear Sentinel-2 passes per field, June 2022 to May 2025).
  Soyabean is bare by late October while cotton is still green, and wheat is still
  green in late February when gram has been cut.
  - Field 5, whose record is known, reads as cotton in all three kharif seasons, as
    the register says. This is the check on the method, and it passes.
  - Field 3 is record L1 on all four seasons tested: cotton 2022, soyabean 2023,
    cotton 2024, wheat in rabi 2024-25. Its record area is 0.78 ha; walked, 0.777 ha.
  - Fields 2 and 4 do not fit record L2. Both were bare by October 2022 and both
    carried cotton through November 2024, where L2 lists cotton in 2022 and soyabean in
    2024. So records L2 (0.55 ha) and L3 (0.72 ha) cannot yet be tied to fields 2
    (0.88 ha) and 4 (0.82 ha), and their areas are 0.1 to 0.3 ha smaller than walked.
  - The satellite also shows crops the register does not list: a rabi crop on field
    3 after the 2023 soyabean, and summer crops on fields 2 and 4. The register
    entries are marked as made through the mobile app.
  `output/crop_history_match.csv`, `output/crop_history_sawardoh.png`
- Field 5 (record L4): 0.59 ha on the record, 0.66 ha walked.
- The register also shows the fields moving from rain-fed to well or borewell
  irrigation in 2023-24.

## Beyond the seven fields (1 Nov 2026)

**Is the blind spot usual?** The same usable-look rule on 1,000 random cropland points
(ESA WorldCover) in ten of the eleven Vidarbha districts, kharif 2019 to 2026, with a
0.25, 1 and 4 ha square field at each point. Gadchiroli is spelled differently in the
boundary dataset and was not matched. Window: 22 June to 15 October.
`src/gee_regional_observability.js`, `src/regional_observability.py`, `output/regional/`

- For a 1 ha field the longest stretch without a usable look had a median of 63 days
  over all 8,000 point-seasons, and was 60 days or more in 58% of them. The median by
  season ran from 50 days (2021) to 69 (2024).
- 2026: median 67 days; 55% of points had a stretch at least as long as my shortest
  field (65 days). This in a season with a median of about 770 mm of June to September
  rain (CHIRPS), against 1,010 to 1,460 mm in the other seasons.
- In 19% of point-seasons a 1 ha field had no usable look at all between 15 July and
  15 September. All seven of my fields were in that group in 2026; 26% of points were.
- Field size, at the same point in the same season: a 0.25 ha field had 0.13 more
  usable looks than a 1 ha field and a longest stretch 1.1 days shorter; a 4 ha field
  0.22 fewer and 1.7 days longer (p < 0.001, errors clustered by point). Size hardly
  changes how often a field is seen; it changes how many pure pixels the look rests on.
- Rainfall, with point and season fixed effects: 100 mm more June to September rain at a
  point goes with 0.13 fewer usable looks (95% interval 0.08 to 0.17) and no clear
  change in the longest stretch.
- Sentinel-2 passed more often in 2025 and 2026 (a median of 28 to 29 pass days against
  23 to 24 before), so counts of looks are not like for like across seasons. The longest
  stretch did not get shorter.

**Did the satellite see the loss the farmers reported?** Each field's NDVI from
15 September to 5 October 2026 against the same field in past seasons with the same kind
of crop, read from late-October greenness (`src/gee_ndvi_history.js`,
`src/loss_proxy.py`, `output/loss_proxy.csv`, `output/loss_proxy.png`).

- September NDVI in 2026 was between 15% below and 14% above each field's past seasons.
  The harvest the farmers reported is 49% to 77% below a normal year.
- A greenness reading in September would not have shown this loss. NDVI is not yield,
  cotton and tur are still standing, and Karanja 2 has only one past soyabean season
  (2024) to compare with.

**What has insurance covered?** The fall in margin per field against the claim paid
(`src/basis_risk.py`, `output/basis_risk.csv`). As of 1 Nov 2026 the seven fields' margin
is about Rs 3.48 lakh below a normal year; on the five fields where the farmer knows the
answer, nothing has been paid yet (a fall of Rs 2.06 lakh on those fields). Crop
insurance pays on a yield shortfall, not on margin, so the two are not expected to match.
The table is rerun when a claim is settled.

## The policy setting this season

- Under PMFBY, technology-based yield estimation (YES-TECH) began with paddy and
  wheat in Kharif 2023 and was extended to soybean from Kharif 2024, with 30%
  weightage to be given to the YES-TECH yield (Lok Sabha Unstarred Question 383,
  22 July 2025). I have not confirmed how it is applied in Wardha district.
- In 2025 Maharashtra ended its Rs 1 crop insurance premium; farmers now pay the
  central rates (2% of the sum insured for kharif crops, 5% for cotton). The state
  also dropped four add-on covers, including localised calamity and mid-season
  adversity, so losses are paid on the yield measured by crop-cutting
  experiments, and for cotton half of that yield is to come from technology-based
  estimates (Agrowon, 11 May 2025).
- Enrolment in Maharashtra fell from 76.6 lakh farmers in Kharif 2024 to 46.0 lakh
  in Kharif 2025 (PIB, 29 August 2026).
- On 25 September 2026 the state declared drought in 265 of its 358 talukas
  (Down To Earth). Karanja, the taluka of both villages, was not on that list; it
  was among 40 talukas added in mid-October, which brought the total to 305
  (Deccan Herald; The Hitavada, 15 Oct 2026). I still have to read the GR itself.
- The state's crop-loan waiver of up to Rs 2 lakh per farmer (Punyashlok
  Ahilyadevi Holkar Shetkari Karjmafi Yojana) covers crop loans taken between
  April 2019 and March 2025; beneficiary lists have come out in rounds since
  August 2026 (Agrowon).

So for these fields the yield estimate is the only route to an insurance payout,
and the satellite part of that estimate faced the 65 to 75 days without a usable
look measured above.

## Season two: back to the field (from October 2026)

The kharif work measured what the satellite could not see. The rabi season is clear,
so the second part of the project takes the results back to the people farming these
fields and records what happens. Everything here is set up; the results are filled in
as they come.

- **Field Watch** (`docs/FIELD_WATCH.md`). Every clear Sentinel-2 pass is searched for
  weak patches inside each field. Each alert is committed before anyone walks there,
  then checked on the ground and shown to the farmer. Scored at the end of the season
  as alerts issued, confirmed and acted on, with the false-alarm rate.
  `src/gee_field_watch.js`, `src/field_watch.py`, `data/field_alerts.csv`.
  Status, 1 Nov: the seven alerts from the passes of 2 to 12 October were flagged on
  22 October, after the three-day window for a ground check, so they are kept as a
  record of the method and not scored. Farmers A and E will not sow rabi this year
  (no rain); B, C and D have not decided. Scoring starts with the first rabi pass
  that is flagged and walked within three days.
- **What the season cost.** Cost and return per field and per hectare from the farm
  ledger and harvest log, with family labour counted in days and, separately, valued at
  a local wage; prices received set against the 2026-27 MSP.
  `src/cost_return.py`, `output/cost_return_by_field.csv`, `output/sales_vs_msp.csv`
- **Insurance check.** With each farmer's permission: was the crop insured, for what
  area, against the area mapped on the ground, and was anything paid.
  `data/insurance_check.csv`
- **Field cards.** One printed page per field, in Marathi, for the person farming it: the
  walked boundary and its area (hectare, H-R as on the 7/12, acre, guntha), the days
  the satellite could and could not see the field, the season's cost and return, what
  is known about insurance, and a box for what is said and decided.
  `src/field_card.py` writes them to `private/field_cards/`, outside git, because each
  holds one farmer's money figures.
- **Feedback.** What was shown to whom, what they said and decided, in one line each.
  `data/farmer_feedback.csv`
- **Farmer survey.** A two-page printed form in Marathi for each farmer, filled in on a
  visit: harvest and sale, crop insurance (crop, area, premium, claim), the e-crop survey,
  the drought declaration and the loan waiver, what they did after seeing their card, and
  a signed receipt for the map and figures. `src/feedback_form.py` prints the forms into
  `private/feedback_forms/`; answers go into `data/farmer_survey_2026.csv` under the same
  question ids.
- **Policy note.** Two pages to the taluka agriculture office and the Krishi Vigyan
  Kendra, Wardha (`docs/POLICY_NOTE.md`, not sent yet). The date sent and any reply go
  in `data/outreach_log.csv`.
- **Comparison.** How India's YES-TECH and the EU's satellite monitoring of farm
  parcels under the Common Agricultural Policy deal with small parcels and cloud.
  First draft: `docs/COMPARISON_EU_CAP.md`.

Farmers appear only as codes (A, B, …). No names, faces, phone numbers or document
numbers are kept in this repo. The input bills for our fields are in `docs/evidence/`
with names removed; the
originals and any notes stay in `private/`, which is not in git.

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
  in `data/field_boundaries.geojson`. It is a shed (confirmed on the ground,
  Oct 2026), so it is correctly left out.
- Seven fields, two villages, one season. The fields were chosen because I can
  reach them every week: two are my family's and five belong to neighbouring
  farmers who agreed to take part. They are not a random sample, and the farm
  figures describe these fields only. The regional audit takes the observability
  question, and only that question, to random cropland points in ten Vidarbha
  districts.
- The farm figures are the farmers' own answers; none of them keeps written
  accounts. Cotton and tur are still standing, so their harvest is what the
  farmer expects; actual weights and sale prices replace it as they come in.

## Structure

```
docs/
  RESEARCH_DESIGN.md         Question, measurements, what would count as a result
  FIELD_PROTOCOL.md          Weekly photo and record routine
  FIELD_WATCH.md             Rabi-season alert loop: flag, commit, check, tell, score
  POLICY_NOTE.md             Two-page note to the agriculture office and KVK (draft)
  COMPARISON_EU_CAP.md       YES-TECH and the EU's Area Monitoring System, side by side
src/
  fields.py                  Field boundary definitions
  pixel_purity.py            Pixel counts and pure-pixel share per field
  photo_metadata.py          Reads position and time from the photo stamps
  photo_greenness.py         Green share of each overview photo
  gee_observability_audit.js Earth Engine: every Sentinel-2 pass, per field
  gee_extract_sar.js         Earth Engine: Sentinel-1 RVI, every pass
  gee_extract_rain.js        Earth Engine: CHIRPS and ERA5-Land daily rain
  observability.py           Usable passes, gaps, ground-satellite pairs
  gee_field_watch.js         Earth Engine: every 10 m pixel per field, rabi passes
  field_watch.py             Weak patches inside a field; writes the alert log
  cost_return.py             Cost and return per field; sales against MSP
  field_card.py              One printable Marathi page per field for the farmer
  feedback_form.py           Two-page Marathi survey and receipt per farmer
  gee_crop_history.js        Earth Engine: every Sentinel-2 pass on the Sawardoh fields, 2022-25
  crop_history.py            Matches each field to a land record by its past crops
  gee_regional_observability.js  Earth Engine: random cropland points across Vidarbha, kharif 2019-26
  regional_observability.py  Blind stretches by season and district; field size and rainfall regressions
  gee_ndvi_history.js        Earth Engine: every pass on all seven fields since 2019
  loss_proxy.py              September NDVI against past seasons, beside the farmers' reported loss
  basis_risk.py              Fall in margin per field against the claim paid
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
  field_owners.csv           Farmer code and family/other per field (no names)
  field_alerts.csv           Field Watch alerts and what was found on the ground
  farmer_feedback.csv        What was shown, what was said and decided
  insurance_check.csv        Insured crop and area against mapped area
  season_figures_2026.csv    Cost and return per field, from the farmer survey
  outreach_log.csv           Policy note: sent to whom, when, and any reply
  farmer_survey_2026.csv     Answers to the printed survey, one row per farmer
  land_record_crops.csv      Area and crops 2022-25 per land record (L1 to L4, no names or numbers)
  regional/                  Exports of gee_regional_observability.js (points and passes per season)
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

Field Watch and the farm figures:

```
python src/field_watch.py data/roots_reflectance_field_watch.csv
python src/cost_return.py 600        # local daily wage (Rs 600 in these villages), used to value any family labour
python src/field_card.py             # Marathi field cards into private/field_cards/, one file per farmer
python src/feedback_form.py          # Marathi survey forms into private/feedback_forms/
```

Land records: run `gee_crop_history.js` in the Code Editor, save the export as
`data/roots_reflectance_crop_history.csv`, then

```
python src/crop_history.py
```

Beyond the seven fields: run `gee_regional_observability.js` (one export for the points
and one per season, saved in `data/regional/`) and `gee_ndvi_history.js` (saved as
`data/roots_reflectance_ndvi_history.csv`), then

```
python src/regional_observability.py
python src/loss_proxy.py
python src/basis_risk.py
```

The observability step writes `observability_by_field.csv`, `observability_passes.csv`,
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
