// ROOTS & REFLECTANCE — Field Watch (rabi season, from October 2026)
//
// The kharif audit (gee_observability_audit.js) showed that no field had a usable
// optical look for 65 to 75 days of the monsoon. October to March is the clear
// season. This script asks a second question: on a clear pass, can 10 m pixels point
// at a weak patch INSIDE a field early enough for someone to walk there and look?
//
// It does not average a field. It exports every 10 m pixel inside each field, for
// every Sentinel-2 pass in the window, with the same field-level usability test as
// the audit. src/field_watch.py then finds the weak patches.
//
// One row per pass x field x pixel:
//   date, time_utc, image_id, zone, field_num, lon, lat (pixel centre)
//   NDVI           (B8 - B4) / (B8 + B4), both 10 m, NOT masked
//   cs             Cloud Score+ clear-sky score
//   usable         1 if this pixel passes the audit's test (cs >= 0.60, not cloud,
//                  cirrus or shadow in SCL), else 0
// NDRE is left out on purpose: Sawardoh field 1 has no pure 20 m pixel at all, and
// for the others the 20 m grid gives too few pixels to locate a patch.
//
// Run in the Earth Engine Code Editor, start the export from the Tasks tab, then
// download roots_reflectance_field_watch.csv from the ROOTS_REFLECTANCE Drive folder
// into data/.

// ---- 1. Field geometries (same polygons as data/field_boundaries.geojson) ----
var fields = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Polygon([[[78.3501074, 21.2230902], [78.3501135, 21.2233177], [78.3511170, 21.2230808], [78.3510103, 21.2229295], [78.3501074, 21.2230902]]]), {zone: 'sawardoh', field_num: 1}),
  ee.Feature(ee.Geometry.Polygon([[[78.3501074, 21.2230902], [78.3510103, 21.2229295], [78.3508953, 21.2221869], [78.3498298, 21.2223510], [78.3501074, 21.2230902]]]), {zone: 'sawardoh', field_num: 2}),
  ee.Feature(ee.Geometry.Polygon([[[78.3498298, 21.2223510], [78.3508953, 21.2221869], [78.3503374, 21.2213256], [78.3496810, 21.2219894], [78.3498298, 21.2223510]]]), {zone: 'sawardoh', field_num: 3}),
  ee.Feature(ee.Geometry.Polygon([[[78.3511170, 21.2230808], [78.3508953, 21.2221869], [78.3517567, 21.2220694], [78.3519297, 21.2226489], [78.3518717, 21.2227811], [78.3511170, 21.2230808]]]), {zone: 'sawardoh', field_num: 4}),
  ee.Feature(ee.Geometry.Polygon([[[78.3496267, 21.2218309], [78.3492049, 21.2211202], [78.3501095, 21.2207714], [78.3503190, 21.2210368], [78.3496267, 21.2218309]]]), {zone: 'sawardoh', field_num: 5}),
  ee.Feature(ee.Geometry.Polygon([[[78.4009879, 21.1595884], [78.4018892, 21.1592801], [78.4016370, 21.1586170], [78.4007550, 21.1588820], [78.4009879, 21.1595884]]]), {zone: 'karanja', field_num: 1}),
  ee.Feature(ee.Geometry.Polygon([[[78.4016370, 21.1586170], [78.4007550, 21.1588820], [78.4004545, 21.1579731], [78.4012324, 21.1577139], [78.4016370, 21.1586170]]]), {zone: 'karanja', field_num: 2})
]);
Map.centerObject(fields, 15);
Map.addLayer(fields, {color: 'orange'}, 'fields');

// ---- 2. Window ----
var startDate = '2026-10-01';              // start of the Field Watch season
var endDate = ee.Date(Date.now());         // today

var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(fields)
    .filterDate(startDate, endDate)
    .linkCollection(csPlus, ['cs_cdf']);
print('Sentinel-2 passes in the window:', s2.size());

// ---- 3. Per-pixel values (same usability test as the audit) ----
var CS_CLEAR = 0.60;

function pixelBands(image) {
  var scl = image.select('SCL');
  var cloud = scl.eq(8).or(scl.eq(9)).or(scl.eq(10));
  var shadow = scl.eq(3);
  var cs = image.select('cs_cdf').unmask(0).rename('cs');
  var usable = cs.gte(CS_CLEAR).and(cloud.not()).and(shadow.not()).rename('usable');
  var ndvi = image.select(['B8', 'B4']).divide(10000)
      .normalizedDifference(['B8', 'B4']).rename('NDVI');
  return ee.Image.cat([ndvi, cs, usable.toByte()]);
}

var rows = s2.map(function(image) {
  var bands = pixelBands(image);
  var proj = image.select('B4').projection();   // native 10 m grid, so points are pixel centres
  var props = {
    date: image.date().format('YYYY-MM-dd'),
    time_utc: image.date().format('HH:mm'),
    image_id: image.get('system:index')
  };
  return fields.map(function(f) {
    var pts = bands.sample({
      region: f.geometry(),
      projection: proj,
      scale: 10,
      geometries: true,
      dropNulls: true
    });
    return pts.map(function(p) {
      var c = p.geometry().coordinates();
      return p.set(props).set({
        zone: f.get('zone'),
        field_num: f.get('field_num'),
        lon: c.get(0),
        lat: c.get(1)
      });
    });
  }).flatten();
}).flatten();

print('First rows:', rows.limit(5));

// ---- 4. Export ----
Export.table.toDrive({
  collection: rows,
  description: 'roots_reflectance_field_watch',
  folder: 'ROOTS_REFLECTANCE',
  fileNamePrefix: 'roots_reflectance_field_watch',
  fileFormat: 'CSV',
  selectors: ['date', 'time_utc', 'image_id', 'zone', 'field_num', 'lon', 'lat', 'NDVI', 'cs', 'usable']
});
