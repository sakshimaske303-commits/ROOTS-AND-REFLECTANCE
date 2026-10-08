// ROOTS & REFLECTANCE — daily rainfall at the two field zones
//
// The satellite goes blind when it rains, and the crop responds to when it rains. This
// pulls daily rainfall for both zones since sowing from two independent products:
//   CHIRPS daily   satellite + rain-gauge blend, about 5.5 km cells (arrives a few weeks late)
//   ERA5-Land      weather-model reanalysis, about 11 km cells (arrives about a week late)
// Neither is a rain gauge in my field. They are regional estimates and can disagree.

var zones = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Point([78.3505, 21.2221]), {zone: 'sawardoh'}),
  ee.Feature(ee.Geometry.Point([78.4012, 21.1587]), {zone: 'karanja'})
]);

var startDate = '2026-06-01';               // three weeks before sowing, to see the onset
var endDate = ee.Date(Date.now());

var chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
    .filterDate(startDate, endDate).select('precipitation');
var era5 = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR')
    .filterDate(startDate, endDate).select('total_precipitation_sum');

print('CHIRPS days:', chirps.size(), ' ERA5-Land days:', era5.size());

function sample(collection, source, scale, toMm) {
  return collection.map(function(image) {
    var date = image.date().format('YYYY-MM-dd');
    return image.multiply(toMm).rename('rain_mm').reduceRegions({
      collection: zones, reducer: ee.Reducer.first(), scale: scale
    }).map(function(f) { return f.set('date', date, 'source', source, 'rain_mm', f.get('first')); });
  }).flatten();
}

var rows = sample(chirps, 'CHIRPS', 5566, 1)
    .merge(sample(era5, 'ERA5-Land', 11132, 1000));     // ERA5-Land is in metres

Export.table.toDrive({
  collection: rows,
  description: 'roots_reflectance_rain',
  folder: 'ROOTS_REFLECTANCE',
  fileNamePrefix: 'roots_reflectance_rain',
  fileFormat: 'CSV',
  selectors: ['zone', 'date', 'source', 'rain_mm']
});
