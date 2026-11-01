// ROOTS & REFLECTANCE: monsoon blind spot on random cropland points across Vidarbha, kharif 2019-2026.
// Three square fields (0.25, 1, 4 ha) per point. Same usable rule as my field audit.
// Save the exports in data/regional/

// ---- 1. Vidarbha districts ----
var DISTRICTS = ['Akola', 'Amravati', 'Bhandara', 'Buldana', 'Chandrapur', 'Gadchiroli',
                 'Gondiya', 'Nagpur', 'Wardha', 'Washim', 'Yavatmal'];

var maharashtra = ee.FeatureCollection('FAO/GAUL/2015/level2')
    .filter(ee.Filter.eq('ADM1_NAME', 'Maharashtra'));
var districts = maharashtra.filter(ee.Filter.inList('ADM2_NAME', DISTRICTS));

// if fewer than 11 are found, I fix the spelling from the full list
print('All Maharashtra districts in GAUL:', maharashtra.aggregate_array('ADM2_NAME').sort());
print('Vidarbha districts found (should be 11):', districts.aggregate_array('ADM2_NAME'));

var region = districts.geometry();
Map.centerObject(districts, 7);
Map.addLayer(districts, {color: 'grey'}, 'Vidarbha');

// ---- 2. Random cropland points, the same number in each district ----
var N_PER_DISTRICT = 100;
var cropland = ee.ImageCollection('ESA/WorldCover/v200').first().select('Map').eq(40);
var districtImg = districts
    .reduceToImage({properties: ['ADM2_CODE'], reducer: ee.Reducer.first()})
    .rename('district')
    .updateMask(cropland);

var sampled = districtImg.stratifiedSample({
  numPoints: N_PER_DISTRICT,
  classBand: 'district',
  region: region,
  scale: 30,
  seed: 2026,
  geometries: true,
  tileScale: 8
});
var sampledList = sampled.toList(5000);
var points = ee.FeatureCollection(ee.List.sequence(0, sampled.size().subtract(1)).map(function(i) {
  var f = ee.Feature(sampledList.get(i));
  var xy = f.geometry().coordinates();
  var name = districts.filter(ee.Filter.eq('ADM2_CODE', f.get('district'))).first().get('ADM2_NAME');
  return f.set({pid: i, lon: xy.get(0), lat: xy.get(1), district_name: name});
}));
print('Cropland points:', points.size());
Map.addLayer(points, {color: 'orange'}, 'points');

// ---- 3. Three square fields around each point ----
var SIZES_HA = [0.25, 1, 4];
var fields = ee.FeatureCollection(SIZES_HA.map(function(ha) {
  var half = Math.sqrt(ha * 10000) / 2;
  return points.map(function(p) {
    return ee.Feature(p.geometry().buffer(half).bounds(), {pid: p.get('pid'), size_ha: ha});
  });
})).flatten();

// ---- 4. The points with their district and kharif rainfall (June to September) ----
var YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026];

var rainRows = ee.FeatureCollection(YEARS.map(function(y) {
  var rain = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
      .filterDate(y + '-06-01', y + '-10-01').sum().rename('rain_jjas_mm');
  return rain.reduceRegions({collection: points, reducer: ee.Reducer.first().setOutputs(['rain_jjas_mm']), scale: 5566})
      .map(function(f) { return f.set('year', y); });
})).flatten();

Export.table.toDrive({
  collection: rainRows,
  description: 'regional_points',
  folder: 'ROOTS_REFLECTANCE',
  fileNamePrefix: 'regional_points',
  fileFormat: 'CSV',
  selectors: ['pid', 'district_name', 'lon', 'lat', 'year', 'rain_jjas_mm']
});

// ---- 5. Every Sentinel-2 pass of each kharif season, usable share per field ----
var CS_CLEAR = 0.60;
var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');

function usableShare(image) {
  var scl = image.select('SCL');
  var bad = scl.eq(3).or(scl.eq(8)).or(scl.eq(9)).or(scl.eq(10));
  // outside the scene counts as not usable; python keeps the better scene of the day
  return image.select('cs_cdf').gte(CS_CLEAR).and(bad.not()).unmask(0).rename('usable');
}

YEARS.forEach(function(y) {
  var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(region)
      .filterDate(y + '-06-20', y + '-10-16')
      .linkCollection(csPlus, ['cs_cdf']);

  var rows = s2.map(function(image) {
    var inScene = fields.filterBounds(image.geometry());
    return usableShare(image).reduceRegions({
      collection: inScene,
      reducer: ee.Reducer.mean().setOutputs(['usable']),
      scale: 10,
      tileScale: 4
    }).map(function(f) {
      return f.set({date: image.date().format('YYYY-MM-dd'), tile: image.get('MGRS_TILE')});
    });
  }).flatten();

  Export.table.toDrive({
    collection: rows,
    description: 'regional_s2_passes_' + y,
    folder: 'ROOTS_REFLECTANCE',
    fileNamePrefix: 'regional_s2_passes_' + y,
    fileFormat: 'CSV',
    selectors: ['pid', 'size_ha', 'date', 'tile', 'usable']
  });
});
