# Copenhagen geographic data

© OpenStreetMap contributors. This geographic database is derived from OpenStreetMap and is available under the Open Database License (ODbL) 1.0. Attribution and license: https://www.openstreetmap.org/copyright . ODbL text: https://opendatacommons.org/licenses/odbl/1-0/ .

- Primary data: OpenStreetMap, fetched through https://overpass-api.de/api/interpreter . The exact core query is retained in `overpass_query.txt`, and server/base timestamps and acquisition metadata are in `fetch_metadata.json`.
- API documentation: https://wiki.openstreetmap.org/wiki/Overpass_API .
- Shoreline semantics: https://wiki.openstreetmap.org/wiki/Tag:natural%3Dcoastline . Directed shoreline has land on the left and sea on the right.

The 12 km core extract contains genuine mapped building footprints, roads, railways, parks, canals, lakes, coastlines, and harbor islands. Geographic geometry is not a generated city grid. Heights and building styles remain only OSM tags at this stage; the Blender scene may estimate missing building heights and details, which should not be presented as surveyed architecture.

Core bounds: longitude 12.48–12.67, latitude 55.625–55.735. Origin: 12.5683° E, 55.6761° N. Local metres use x=(longitude−origin longitude) × 111320 × cos(origin latitude), y=(latitude−origin latitude) × 111320. x points east, y north, z up. This is a local visualization projection rather than a surveyed national-grid transformation.

Broad context bounds: longitude 12.25–12.90, latitude 55.50–55.92. This adds real coastlines only, with no invented additional buildings. Both extracts share the same coordinate origin. Land polygons are closed only along the actual map clipping boundary; the harbor, mainland, islands, and ocean boundary follow OSM coastlines.

`copenhagen_geo.json` and `context_geography.json` include outer rings, holes, and constrained triangles for surface polygons. Building polygons with courtyards also include constrained roof triangles. Rings omit the repeated closing vertex. Minor simplification is recorded in the JSON processing metadata; coordinates are quantized to millimetres.

`geography_preview.png` and `harbour_preview.png` are diagnostic maps derived from these exact polygons. The six fixed harbor samples in `harbour_control_points.json` check water/land classification around Nyhavn, Christianshavns Kanal, the inner harbor and Kongens Nytorv. `landmarks_osm.json` retains named main-building footprints, while `landmark_parts_raw.json` contains a focused extract of central mapped building parts and towers.

## Reproduce

Use Python with Shapely >=2.1 (`pip install shapely`) and Pillow for preview PNGs (`pip install pillow`). Run from the repository root:

```sh
python3 city-scene/aerial/scripts/fetch_geography.py
python3 city-scene/aerial/scripts/prepare_geography.py
python3 city-scene/aerial/scripts/prepare_geography.py --preview
python3 city-scene/aerial/scripts/fetch_geography.py --parts
python3 city-scene/aerial/scripts/fetch_geography.py --context
python3 city-scene/aerial/scripts/prepare_geography.py --context
```

Downloads are cached, and rerunning a fetch reads the cache. The context and landmark requests are intentionally separate small requests. Core geometry preparation does not depend on Blender.
