// ROOTS & REFLECTANCE — Sentinel-2 NDVI/NDRE extraction
// I cloud-mask Sentinel-2 SR over all 7 of my field boundaries, compute NDVI + NDRE
// per field per date, and export it all as one CSV table.

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

print('Fields loaded:', fields.size(), fields);
Map.centerObject(fields, 15);
Map.addLayer(fields, {color: 'orange'}, 'ROOTS & REFLECTANCE fields');

// ---- 2. Sentinel-2 Harmonized SR, cloud-masked ----
function maskS2clouds(image) {
  var qa = image.select('QA60');
  var cloudBitMask = 1 << 10;
  var cirrusBitMask = 1 << 11;
  var mask = qa.bitwiseAnd(cloudBitMask).eq(0).and(qa.bitwiseAnd(cirrusBitMask).eq(0));
  return image.updateMask(mask)
      .divide(10000)
      .copyProperties(image, ['system:time_start']);
}

var startDate = '2026-06-20';               // just before the earliest sowing date
var endDate = ee.Date(Date.now());          // today

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(fields)
    .filterDate(startDate, endDate)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
    .map(maskS2clouds);

print('Cloud-filtered Sentinel-2 images found:', s2.size());

// ---- 3. NDVI + NDRE ----
function addIndices(image) {
  var ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI');   // NIR, Red
  var ndre = image.normalizedDifference(['B8', 'B5']).rename('NDRE');   // NIR, Red-edge
  return image.addBands([ndvi, ndre]).copyProperties(image, ['system:time_start']);
}

var s2indices = s2.map(addIndices);

// ---- 4. Per-image, per-field zonal mean ----
var results = s2indices.map(function(image) {
  var date = image.date().format('YYYY-MM-dd');
  var stats = image.select(['NDVI', 'NDRE']).reduceRegions({
    collection: fields,
    reducer: ee.Reducer.mean(),
    scale: 10
  });
  return stats.map(function(f) {
    return f.set('date', date);
  });
}).flatten();

print('Total field-date rows to export:', results.size());

// ---- 5. Export to Drive as CSV ----
Export.table.toDrive({
  collection: results,
  description: 'roots_reflectance_ndvi_ndre',
  folder: 'ROOTS_REFLECTANCE',
  fileNamePrefix: 'roots_reflectance_ndvi_ndre',
  fileFormat: 'CSV',
  selectors: ['zone', 'field_num', 'field_id', 'name', 'area_ha', 'sown', 'crops', 'date', 'NDVI', 'NDRE']
});
