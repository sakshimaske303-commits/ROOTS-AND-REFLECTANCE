// ROOTS & REFLECTANCE — Sentinel-2 observability audit
//
// My first script (gee_extract_indices.js) kept a Sentinel-2 image only if the whole
// 110 km tile was less than 40% cloudy. My fields are a few hundred metres across, so
// that rule can throw away a pass on which the fields themselves were clear, and it
// tells me nothing about the passes it drops.
//
// This script keeps EVERY Sentinel-2 pass over the fields since sowing and records,
// for each pass and each field, what the satellite could see there:
//   covered        share of the field that the image covers at all
//   scl_clear      share classified vegetation or bare soil by the scene classification (SCL 4, 5)
//   scl_cloud      share classified cloud or cirrus (SCL 8, 9, 10)
//   scl_shadow     share classified cloud shadow (SCL 3)
//   cs             mean Cloud Score+ clear-sky score (0 = cloud, 1 = clear)
//   usable         share of the field that passes my field-level test (see USABLE below)
//   NDVI, NDRE     mean over the usable pixels only (empty when nothing is usable)
//   tile_cloud_pct the tile-wide cloud percentage my first script filtered on
// Each field is written twice: footprint 'full' (the whole boundary) and footprint
// 'inner' (the boundary pulled in by 10 m, to keep pixels that mix in the bund or road out).
//
// NDRE here is (B8A - B5) / (B8A + B5): both bands are 20 m. My first script used the
// 10 m B8 with the 20 m B5, so NDRE values from the two scripts are not the same quantity.

// ---- 1. Field geometries ----
var fields = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Polygon([[[78.3501074, 21.2230902], [78.3501135, 21.2233177], [78.3511170, 21.2230808], [78.3510103, 21.2229295], [78.3501074, 21.2230902]]]), {zone: 'sawardoh', field_num: 1, field_id: 'BACD', name: 'Cotton & Pigeon Pea (Tur)', area_ha: 0.2215, sown: '2026-06-22', crops: 'cotton,tur'}),
  ee.Feature(ee.Geometry.Polygon([[[78.3501074, 21.2230902], [78.3510103, 21.2229295], [78.3508953, 21.2221869], [78.3498298, 21.2223510], [78.3501074, 21.2230902]]]), {zone: 'sawardoh', field_num: 2, field_id: 'BDHG', name: 'Orange, Cotton & Pigeon Pea (Tur)', area_ha: 0.8792, sown: '2026-06-22', crops: 'cotton,tur,orange'}),
  ee.Feature(ee.Geometry.Polygon([[[78.3498298, 21.2223510], [78.3508953, 21.2221869], [78.3503374, 21.2213256], [78.3496810, 21.2219894], [78.3498298, 21.2223510]]]), {zone: 'sawardoh', field_num: 3, field_id: 'GHLJ', name: 'Cotton', area_ha: 0.7771, sown: '2026-06-22', crops: 'cotton'}),
  ee.Feature(ee.Geometry.Polygon([[[78.3511170, 21.2230808], [78.3508953, 21.2221869], [78.3517567, 21.2220694], [78.3519297, 21.2226489], [78.3518717, 21.2227811], [78.3511170, 21.2230808]]]), {zone: 'sawardoh', field_num: 4, field_id: 'CHIFE', name: 'Orange, Cotton, Pigeon Pea (Tur) & Turmeric', area_ha: 0.8226, sown: '2026-06-22', crops: 'cotton,tur,orange,turmeric'}),
  ee.Feature(ee.Geometry.Polygon([[[78.3496267, 21.2218309], [78.3492049, 21.2211202], [78.3501095, 21.2207714], [78.3503190, 21.2210368], [78.3496267, 21.2218309]]]), {zone: 'sawardoh', field_num: 5, field_id: 'KMON', name: 'Cotton', area_ha: 0.6585, sown: '2026-06-22', crops: 'cotton'}),
  ee.Feature(ee.Geometry.Polygon([[[78.4009879, 21.1595884], [78.4018892, 21.1592801], [78.4016370, 21.1586170], [78.4007550, 21.1588820], [78.4009879, 21.1595884]]]), {zone: 'karanja', field_num: 1, field_id: 'BAEF', name: 'Soyabean & Pigeon Pea (Tur)', area_ha: 0.786, sown: '2026-06-27', crops: 'soyabean,tur'}),
  ee.Feature(ee.Geometry.Polygon([[[78.4016370, 21.1586170], [78.4007550, 21.1588820], [78.4004545, 21.1579731], [78.4012324, 21.1577139], [78.4016370, 21.1586170]]]), {zone: 'karanja', field_num: 2, field_id: 'EFCD', name: 'Soyabean', area_ha: 0.9758, sown: '2026-06-27', crops: 'soyabean'})
]);

print('Fields loaded:', fields.size());
Map.centerObject(fields, 14);
Map.addLayer(fields, {color: 'orange'}, 'ROOTS & REFLECTANCE fields');

// ---- 2. Footprints: whole field, and field pulled in by 10 m ----
var INSET_M = 10;
var full = fields.map(function(f) { return f.set('footprint', 'full'); });
var inner = fields.map(function(f) {
  return f.setGeometry(f.geometry().buffer(-INSET_M, 1)).set('footprint', 'inner');
});
var footprints = full.merge(inner);

// ---- 3. Every Sentinel-2 pass since sowing, with Cloud Score+ attached ----
var startDate = '2026-06-20';               // just before the earliest sowing date
var endDate = ee.Date(Date.now());          // today

var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(fields)
    .filterDate(startDate, endDate)
    .linkCollection(csPlus, ['cs_cdf']);

print('Sentinel-2 passes over the fields, no cloud filter:', s2.size());
print('...of which the tile is under 40% cloudy (my old rule):',
      s2.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40)).size());

// ---- 4. What can be seen in each pass ----
// USABLE: Cloud Score+ at least 0.60 (the threshold its authors suggest as a default),
// and not classified cloud, cirrus or cloud shadow by SCL.
var CS_CLEAR = 0.60;

function describe(image) {
  var scl = image.select('SCL');
  var covered = image.select('B8').mask().gt(0).rename('covered');
  var sclClear = scl.eq(4).or(scl.eq(5)).unmask(0).rename('scl_clear');
  var sclCloud = scl.eq(8).or(scl.eq(9)).or(scl.eq(10)).unmask(0).rename('scl_cloud');
  var sclShadow = scl.eq(3).unmask(0).rename('scl_shadow');
  var cs = image.select('cs_cdf').rename('cs');
  var usable = cs.gte(CS_CLEAR).unmask(0)
      .and(sclCloud.not()).and(sclShadow.not()).and(covered)
      .rename('usable');
  var refl = image.select(['B4', 'B5', 'B8', 'B8A']).divide(10000);
  var ndvi = refl.normalizedDifference(['B8', 'B4']).updateMask(usable).rename('NDVI');
  var ndre = refl.normalizedDifference(['B8A', 'B5']).updateMask(usable).rename('NDRE');
  return ee.Image.cat([covered, sclClear, sclCloud, sclShadow, cs, usable, ndvi, ndre]);
}

var results = s2.map(function(image) {
  var stats = describe(image).reduceRegions({
    collection: footprints,
    reducer: ee.Reducer.mean(),
    scale: 10
  });
  var props = {
    date: image.date().format('YYYY-MM-dd'),
    time_utc: image.date().format('HH:mm'),
    satellite: image.get('SPACECRAFT_NAME'),
    tile: image.get('MGRS_TILE'),
    rel_orbit: image.get('SENSING_ORBIT_NUMBER'),
    tile_cloud_pct: image.get('CLOUDY_PIXEL_PERCENTAGE'),
    image_id: image.get('system:index')
  };
  return stats.map(function(f) { return f.set(props); });
}).flatten();

print('Rows to export (pass x field x footprint):', results.size());

// ---- 5. Export to Drive as CSV ----
Export.table.toDrive({
  collection: results,
  description: 'roots_reflectance_s2_audit',
  folder: 'ROOTS_REFLECTANCE',
  fileNamePrefix: 'roots_reflectance_s2_audit',
  fileFormat: 'CSV',
  selectors: ['zone', 'field_num', 'field_id', 'name', 'area_ha', 'sown', 'crops', 'footprint',
              'date', 'time_utc', 'satellite', 'tile', 'rel_orbit', 'tile_cloud_pct', 'image_id',
              'covered', 'scl_clear', 'scl_cloud', 'scl_shadow', 'cs', 'usable', 'NDVI', 'NDRE']
});
