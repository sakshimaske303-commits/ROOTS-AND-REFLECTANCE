"""
Field boundary definitions for ROOTS & REFLECTANCE.

I copied these coordinates straight from my portfolio (GEOSPATIAL-PORTFOLIO/index.html,
RR_SAWARDOH_POINTS / RR_SAWARDOH_PATCHES / RR_KARANJA_POINTS / RR_KARANJA_PATCHES) so my
satellite analysis always lines up with what I've mapped there. If I ever correct a
boundary on the portfolio side, I mirror the change here too.

Coordinate format: [latitude, longitude] — same convention I use for Leaflet on the portfolio.
"""

SAWARDOH_POINTS = {
    'A': [21.2233177, 78.3501135], 'B': [21.2230902, 78.3501074],
    'C': [21.2230808, 78.3511170], 'D': [21.2229295, 78.3510103],
    'E': [21.2227811, 78.3518717], 'F': [21.2226489, 78.3519297],
    'G': [21.2223510, 78.3498298], 'H': [21.2221869, 78.3508953],
    'I': [21.2220694, 78.3517567], 'J': [21.2219894, 78.3496810],
    'K': [21.2218309, 78.3496267], 'L': [21.2213256, 78.3503374],
    'M': [21.2211202, 78.3492049], 'N': [21.2210368, 78.3503190],
    'O': [21.2207714, 78.3501095],
}

SAWARDOH_PATCHES = [
    {'num': 1, 'id': 'BACD', 'name': 'Cotton & Pigeon Pea (Tur)',
     'corners': ['B', 'A', 'C', 'D'], 'area_ha': 0.2215,
     'sown': '2026-06-22', 'crops': ['cotton', 'tur']},
    {'num': 2, 'id': 'BDHG', 'name': 'Orange, Cotton & Pigeon Pea (Tur)',
     'corners': ['B', 'D', 'H', 'G'], 'area_ha': 0.8792,
     'sown': '2026-06-22', 'crops': ['cotton', 'tur', 'orange']},
    {'num': 3, 'id': 'GHLJ', 'name': 'Cotton',
     'corners': ['G', 'H', 'L', 'J'], 'area_ha': 0.7771,
     'sown': '2026-06-22', 'crops': ['cotton']},
    {'num': 4, 'id': 'CHIFE', 'name': 'Orange, Cotton & Pigeon Pea (Tur)',
     'corners': ['C', 'H', 'I', 'F', 'E'], 'area_ha': 0.8226,
     'sown': '2026-06-22', 'crops': ['cotton', 'tur', 'orange']},  # turmeric was last year's crop; a few plants remain
    {'num': 5, 'id': 'KMON', 'name': 'Cotton',
     'corners': ['K', 'M', 'O', 'N'], 'area_ha': 0.6585,
     'sown': '2026-06-22', 'crops': ['cotton']},
]

KARANJA_POINTS = {
    'A': [21.1592801, 78.4018892], 'B': [21.1595884, 78.4009879],
    'C': [21.1579731, 78.4004545], 'D': [21.1577139, 78.4012324],
    'E': [21.158617, 78.401637], 'F': [21.158882, 78.400755],
}

KARANJA_PATCHES = [
    {'num': 1, 'id': 'BAEF', 'name': 'Soyabean & Pigeon Pea (Tur)',
     'corners': ['B', 'A', 'E', 'F'], 'area_ha': 0.786,
     'sown': '2026-06-27', 'crops': ['soyabean', 'tur']},
    {'num': 2, 'id': 'EFCD', 'name': 'Soyabean',
     'corners': ['E', 'F', 'C', 'D'], 'area_ha': 0.9758,
     'sown': '2026-06-27', 'crops': ['soyabean']},
]


def patch_to_geojson_polygon(points, patch):
    """Turn one field's corner-point letters into a GeoJSON Polygon (lon/lat order)."""
    ring = [[points[c][1], points[c][0]] for c in patch['corners']]  # lon, lat
    ring.append(ring[0])  # close the ring
    return {
        'type': 'Feature',
        'properties': {
            'zone': None,  # filled in by caller
            'field_num': patch['num'],
            'field_id': patch['id'],
            'name': patch['name'],
            'area_ha': patch['area_ha'],
            'sown': patch['sown'],
            'crops': patch['crops'],
        },
        'geometry': {'type': 'Polygon', 'coordinates': [ring]},
    }


def all_fields_geojson():
    """Give back a GeoJSON FeatureCollection covering all 7 of my fields (both zones)."""
    features = []
    for patch in SAWARDOH_PATCHES:
        feat = patch_to_geojson_polygon(SAWARDOH_POINTS, patch)
        feat['properties']['zone'] = 'sawardoh'
        features.append(feat)
    for patch in KARANJA_PATCHES:
        feat = patch_to_geojson_polygon(KARANJA_POINTS, patch)
        feat['properties']['zone'] = 'karanja'
        features.append(feat)
    return {'type': 'FeatureCollection', 'features': features}


if __name__ == '__main__':
    import json
    print(json.dumps(all_fields_geojson(), indent=2))
