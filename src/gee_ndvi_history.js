// ROOTS & REFLECTANCE: NDVI of all seven fields, every pass June-December since 2019.
// Save the export as data/roots_reflectance_ndvi_history.csv

// ---- 1. Field geometries (same as src/fields.py), 5 m inside the walked edge ----
var fields = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Polygon([[[78.3501074, 21.2230902], [78.3501135, 21.2233177], [78.3511170, 21.2230808], [78.3510103, 21.2229295], [78.3501074, 21.2230902]]]), {zone: 'sawardoh', field_num: 1}),
  ee.Feature(ee.Geometry.Polygon([[[78.3501074, 21.2230902], [78.3510103, 21.2229295], [78.3508953, 21.2221869], [78.3498298, 21.2223510], [78.3501074, 21.2230902]]]), {zone: 'sawardoh', field_num: 2}),
  ee.Feature(ee.Geometry.Polygon([[[78.3498298, 21.2223510], [78.3508953, 21.2221869], [78.3503374, 21.2213256], [78.3496810, 21.2219894], [78.3498298, 21.2223510]]]), {zone: 'sawardoh', field_num: 3}),
  ee.Feature(ee.Geometry.Polygon([[[78.3511170, 21.2230808], [78.3508953, 21.2221869], [78.3517567, 21.2220694], [78.3519297, 21.2226489], [78.3518717, 21.2227811], [78.3511170, 21.2230808]]]), {zone: 'sawardoh', field_num: 4}),
  ee.Feature(ee.Geometry.Polygon([[[78.3496267, 21.2218309], [78.3492049, 21.2211202], [78.3501095, 21.2207714], [78.3503190, 21.2210368], [78.3496267, 21.2218309]]]), {zone: 'sawardoh', field_num: 5}),
  ee.Feature(ee.Geometry.Polygon([[[78.4009879, 21.1595884], [78.4018892, 21.1592801], [78.4016370, 21.1586170], [78.4007550, 21.1588820], [78.4009879, 21.1595884]]]), {zone: 'karanja', field_num: 1}),
  ee.Feature(ee.Geometry.Polygon([[[78.4016370, 21.1586170], [78.4007550, 21.1588820], [78.4004545, 21.1579731], [78.4012324, 21.1577139], [78.4016370, 21.1586170]]]), {zone: 'karanja', field_num: 2})
]).map(function(f) {
  return f.setGeometry(f.geometry().buffer(-5));
});

Map.centerObject(fields, 14);
Map.addLayer(fields, {color: 'orange'}, 'fields (5 m inside the edge)');

// ---- 2. Sentinel-2 with Cloud Score+ per pixel ----
var START = '2019-06-01';
var END = ee.Date(Date.now());
var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(fields)
    .filterDate(START, END)
    .filter(ee.Filter.calendarRange(6, 12, 'month'))
    .linkCollection(csPlus, ['cs_cdf']);

// ---- 3. One row per pass and field ----
var rows = s2.map(function(img) {
  var clear = img.select('cs_cdf').gte(0.6);
  var ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI').updateMask(clear);
  var counts = clear.rename('clear').addBands(ee.Image.constant(1).rename('all'));
  var withCounts = counts.reduceRegions({collection: fields, reducer: ee.Reducer.sum(), scale: 10});
  var stats = ndvi.reduceRegions({
    collection: withCounts, reducer: ee.Reducer.median().setOutputs(['NDVI']), scale: 10
  });
  var date = img.date().format('YYYY-MM-dd');
  return stats.map(function(f) { return f.set({date: date}); });
}).flatten();

print('Rows to export (passes x fields):', rows.size());

// ---- 4. Export ----
Export.table.toDrive({
  collection: rows,
  description: 'roots_reflectance_ndvi_history',
  folder: 'ROOTS_REFLECTANCE',
  fileNamePrefix: 'roots_reflectance_ndvi_history',
  fileFormat: 'CSV',
  selectors: ['zone', 'field_num', 'date', 'NDVI', 'clear', 'all']
});
