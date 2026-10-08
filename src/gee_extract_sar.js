// ROOTS & REFLECTANCE — Sentinel-1 SAR backup extraction
//
// Why this exists: the optical (Sentinel-2) extraction — see gee_extract_indices.js —
// has been stuck at 2 usable cloud-free dates (21 Jun, 14 Jul 2026) for 6+ weeks
// because Vidarbha's kharif monsoon cloud cover is blocking every pass in between
// (see DEVELOPMENT_LOG.md, 6 Sep 2026 entry). Radar (Sentinel-1 C-band SAR) sees
// through cloud cover, so it can fill exactly that gap instead of just waiting it out.
//
// This does NOT replace the NDVI/NDRE pipeline — optical vegetation indices are still
// the primary signal once passes clear. This is a secondary, cloud-proof cross-check
// for the stretch where optical has nothing, using the radar vegetation index (RVI),
// a standard VV/VH-based proxy for canopy structure and biomass.

// ---- 1. Field geometries (same 7 fields, same coordinates as gee_extract_indices.js) ----
var fields = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Polygon([[[78.3501074, 21.2230902], [78.3501135, 21.2233177], [78.3511170, 21.2230808], [78.3510103, 21.2229295], [78.3501074, 21.2230902]]]), {zone: 'sawardoh', field_num: 1, field_id: 'BACD', name: 'Cotton & Pigeon Pea (Tur)', area_ha: 0.2215, sown: '2026-06-22', crops: 'cotton,tur'}),
  ee.Feature(ee.Geometry.Polygon([[[78.3501074, 21.2230902], [78.3510103, 21.2229295], [78.3508953, 21.2221869], [78.3498298, 21.2223510], [78.3501074, 21.2230902]]]), {zone: 'sawardoh', field_num: 2, field_id: 'BDHG', name: 'Orange, Cotton & Pigeon Pea (Tur)', area_ha: 0.8792, sown: '2026-06-22', crops: 'cotton,tur,orange'}),
  ee.Feature(ee.Geometry.Polygon([[[78.3498298, 21.2223510], [78.3508953, 21.2221869], [78.3503374, 21.2213256], [78.3496810, 21.2219894], [78.3498298, 21.2223510]]]), {zone: 'sawardoh', field_num: 3, field_id: 'GHLJ', name: 'Cotton', area_ha: 0.7771, sown: '2026-06-22', crops: 'cotton'}),
  ee.Feature(ee.Geometry.Polygon([[[78.3511170, 21.2230808], [78.3508953, 21.2221869], [78.3517567, 21.2220694], [78.3519297, 21.2226489], [78.3518717, 21.2227811], [78.3511170, 21.2230808]]]), {zone: 'sawardoh', field_num: 4, field_id: 'CHIFE', name: 'Orange, Cotton, Pigeon Pea (Tur) & Turmeric', area_ha: 0.8226, sown: '2026-06-22', crops: 'cotton,tur,orange,turmeric'}),
  ee.Feature(ee.Geometry.Polygon([[[78.3496267, 21.2218309], [78.3492049, 21.2211202], [78.3501095, 21.2207714], [78.3503190, 21.2210368], [78.3496267, 21.2218309]]]), {zone: 'sawardoh', field_num: 5, field_id: 'KMON', name: 'Cotton', area_ha: 0.6585, sown: '2026-06-22', crops: 'cotton'}),
  ee.Feature(ee.Geometry.Polygon([[[78.4009879, 21.1595884], [78.4018892, 21.1592801], [78.4016370, 21.1586170], [78.4007550, 21.1588820], [78.4009879, 21.1595884]]]), {zone: 'karanja', field_num: 1, field_id: 'BAEF', name: 'Soyabean & Pigeon Pea (Tur)', area_ha: 0.786, sown: '2026-06-27', crops: 'soyabean,tur'}),
  ee.Feature(ee.Geometry.Polygon([[[78.4016370, 21.1586170], [78.4007550, 21.1588820], [78.4004545, 21.1579731], [78.4012324, 21.1577139], [78.4016370, 21.1586170]]]), {zone: 'karanja', field_num: 2, field_id: 'EFCD', name: 'Soyabean', area_ha: 0.9758, sown: '2026-06-27', crops: 'soyabean'})
]);

print('Fields loaded:', fields.size(), fields);
Map.centerObject(fields, 15);
Map.addLayer(fields, {color: 'cyan'}, 'ROOTS & REFLECTANCE fields');

// ---- 2. Sentinel-1 GRD, IW mode, VV+VH, same start date as the optical script ----
var startDate = '2026-06-20';               // just before the earliest sowing date
var endDate = ee.Date(Date.now());          // today

var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
    .filterBounds(fields)
    .filterDate(startDate, endDate)
    .filter(ee.Filter.eq('instrumentMode', 'IW'))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'));

print('Sentinel-1 IW scenes found (all orbits/passes):', s1.size());

// Ascending and descending passes, and different relative orbits, see the canopy from
// different geometries, so their backscatter isn't directly comparable. I export every
// pass and write the pass direction and relative orbit on each row, so the analysis can
// keep each viewing geometry as its own series instead of me choosing one here.
print('Ascending:', s1.filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING')).size(),
      ' Descending:', s1.filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING')).size());

// ---- 3. Radar Vegetation Index (RVI) ----
// RVI = 4 * VH / (VV + VH) — a standard, unitless (~0-1) proxy for canopy structure
// and biomass from dual-pol C-band SAR. Higher RVI generally tracks denser/more
// structurally complex canopy, the radar analogue of what NDVI tracks optically.
function addRVI(image) {
  var vv = image.select('VV');
  var vh = image.select('VH');
  // GRD backscatter here is already in dB (linear-to-dB done by the archive); convert
  // to linear power before the ratio, since RVI is defined on linear backscatter.
  var vvLin = ee.Image(10).pow(vv.divide(10));
  var vhLin = ee.Image(10).pow(vh.divide(10));
  var rvi = vhLin.multiply(4).divide(vvLin.add(vhLin)).rename('RVI');
  return image.addBands(rvi).copyProperties(image, ['system:time_start']);
}

var s1indices = s1.map(addRVI);

// ---- 4. Per-image, per-field zonal mean ----
// scale: 20m (not 10) — Sentinel-1 GRD's native IW resolution is ~10x10m but with a
// larger effective footprint than that; 20m keeps the per-field pixel count reasonable
// for these small (0.2-1 ha) fields while still resolving field-to-field differences.
var results = s1indices.map(function(image) {
  var date = image.date().format('YYYY-MM-dd');
  var stats = image.select(['VV', 'VH', 'RVI']).reduceRegions({
    collection: fields,
    reducer: ee.Reducer.mean(),
    scale: 20
  });
  return stats.map(function(f) {
    return f.set('date', date, 'orbit_pass', image.get('orbitProperties_pass'),
                 'rel_orbit', image.get('relativeOrbitNumber_start'));
  });
}).flatten();

print('Total field-date SAR rows to export:', results.size());

// ---- 5. Export to Drive as CSV ----
Export.table.toDrive({
  collection: results,
  description: 'roots_reflectance_sar',
  folder: 'ROOTS_REFLECTANCE',
  fileNamePrefix: 'roots_reflectance_sar',
  fileFormat: 'CSV',
  selectors: ['zone', 'field_num', 'field_id', 'name', 'area_ha', 'sown', 'crops', 'date', 'orbit_pass', 'rel_orbit', 'VV', 'VH', 'RVI']
});

// ---- Notes for next time I run this ----
// - Every pass is exported with its pass direction and relative orbit. I compare dates
//   only within one (orbit_pass, rel_orbit) pair.
// - Multiple images on the same date (adjacent relative orbits) are handled the same
//   way as the optical script: I average them down to one row per field per date
//   rather than treating them as independent readings.
// - This is intentionally a *separate* CSV/export from the NDVI/NDRE one — keeping the
//   optical and radar pipelines independent means a bug or a weird value in one can't
//   silently contaminate the other.
