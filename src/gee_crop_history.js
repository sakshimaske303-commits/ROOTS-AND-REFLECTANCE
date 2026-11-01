// ROOTS & REFLECTANCE: crop history of the Sawardoh fields, June 2022 to May 2025.
//
// The village crop register (7/12, form 12) lists the crop on each survey number for the
// last three years. Two of the survey numbers swapped soyabean and cotton between 2023 and
// 2024, and their rabi crops differ (wheat on one, gram on the other). Soyabean is cut by
// early October and cotton stays green until December, so the past Sentinel-2 record of
// each field should show which survey number it is. I export every pass so the matching is
// done in src/crop_history.py, not here.
//
// Run in the Earth Engine Code Editor, then Tasks > RUN. Save the CSV as
// data/roots_reflectance_crop_history.csv

// ---- 1. Field geometries (same as src/fields.py) ----
var fields = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Polygon([[[78.3501074, 21.2230902], [78.3501135, 21.2233177], [78.3511170, 21.2230808], [78.3510103, 21.2229295], [78.3501074, 21.2230902]]]), {field_num: 1}),
  ee.Feature(ee.Geometry.Polygon([[[78.3501074, 21.2230902], [78.3510103, 21.2229295], [78.3508953, 21.2221869], [78.3498298, 21.2223510], [78.3501074, 21.2230902]]]), {field_num: 2}),
  ee.Feature(ee.Geometry.Polygon([[[78.3498298, 21.2223510], [78.3508953, 21.2221869], [78.3503374, 21.2213256], [78.3496810, 21.2219894], [78.3498298, 21.2223510]]]), {field_num: 3}),
  ee.Feature(ee.Geometry.Polygon([[[78.3511170, 21.2230808], [78.3508953, 21.2221869], [78.3517567, 21.2220694], [78.3519297, 21.2226489], [78.3518717, 21.2227811], [78.3511170, 21.2230808]]]), {field_num: 4}),
  ee.Feature(ee.Geometry.Polygon([[[78.3496267, 21.2218309], [78.3492049, 21.2211202], [78.3501095, 21.2207714], [78.3503190, 21.2210368], [78.3496267, 21.2218309]]]), {field_num: 5})
]).map(function(f) {
  // I step 5 m in from the walked edge so bunds and the neighbour's crop count less.
  return f.setGeometry(f.geometry().buffer(-5));
});

Map.centerObject(fields, 17);
Map.addLayer(fields, {color: 'orange'}, 'Sawardoh fields (5 m inside the edge)');

// ---- 2. Sentinel-2 with Cloud Score+ per pixel ----
var START = '2022-06-01';
var END = '2025-06-01';

var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(fields)
    .filterDate(START, END)
    .linkCollection(csPlus, ['cs_cdf']);

// ---- 3. One row per pass and field ----
var rows = s2.map(function(img) {
  var clear = img.select('cs_cdf').gte(0.6);
  var ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI').updateMask(clear);
  var counts = clear.rename('clear').addBands(ee.Image.constant(1).rename('all'));

  // First count clear and total pixels per field, then add the median NDVI of the clear ones.
  var withCounts = counts.reduceRegions({
    collection: fields, reducer: ee.Reducer.sum(), scale: 10
  });
  var stats = ndvi.reduceRegions({
    collection: withCounts, reducer: ee.Reducer.median().setOutputs(['NDVI']), scale: 10
  });

  var date = img.date().format('YYYY-MM-dd');
  return stats.map(function(f) {
    return f.set({date: date});
  });
}).flatten();

print('Rows to export (passes x fields):', rows.size());

// ---- 4. Export ----
Export.table.toDrive({
  collection: rows,
  description: 'roots_reflectance_crop_history',
  folder: 'ROOTS_REFLECTANCE',
  fileNamePrefix: 'roots_reflectance_crop_history',
  fileFormat: 'CSV',
  selectors: ['field_num', 'date', 'NDVI', 'clear', 'all']
});
