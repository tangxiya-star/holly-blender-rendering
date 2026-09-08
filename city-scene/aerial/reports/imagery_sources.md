# Copenhagen orthophoto atlas

The scene texture is genuine GeoDanmark spring orthophotography, delivered through Septima OSMtools' MapProxy WMS. It is not generated imagery, an Esri basemap, or a reconstructed satellite-like texture.

**Attribution:** Orthophoto © GeoDanmark / Klimadatastyrelsen, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); delivered via Septima OSMtools; cropped, mosaicked and resampled for a Blender visualization.

## Source and permissions

- [Septima's own service description](https://osmtools.septima.dk/) identifies its ortho imagery as a wrapper/cache around GeoDanmark data. The WMS layer is `DAF_ortoforaar`, at `https://osmtools.septima.dk/mapproxy/service`.
- [Klimadatastyrelsen's official data terms](https://www.klimadatastyrelsen.dk/om-klimadatastyrelsen/vilkaar-og-priser) state that its open geographic data and GeoDanmark data use CC BY 4.0, allowing download, sharing and adaptation with attribution. The page also identifies GeoDanmark orthophotos as freely available.
- The service's own WMS capabilities, retained at `data/aerial_imagery_capabilities.xml`, say: “This service is intended for private and evaluation use only.” This is a restriction on access to Septima's delivery service and must not be confused with an unrestricted production-hosting entitlement. The current acquisition is a finite, one-off local prototype/evaluation download. A deployed application should not hotlink this WMS or assume continuing production access; obtain imagery directly through an authorized GeoDanmark/Dataforsyningen service for that use.
- The live layer does not report a per-tile flight date. No capture year is asserted. The retrieval timestamp and exact request URLs are recorded in `data/aerial_imagery.json`.

## Atlas and mapping

The atlas is 8192 × 8192 pixels, north up. Sixteen 2048 × 2048 WMS requests use version 1.1.1 and `EPSG:4326`, so the bounding-box order is longitude/latitude. Their exact mosaic covers west 12.48°, south 55.625°, east 12.67°, north 55.735°.

The scene's local projection is affine in longitude and latitude, so mapping the resulting geographic image onto world XY uses the same geographic bounds exactly:

```text
u = (world_x - min_x) / (max_x - min_x)
v = (world_y - min_y) / (max_y - min_y)
```

The numerical local bounds, using origin 12.5683° E / 55.6761° N, are in `aerial_imagery.json`. Blender's UV origin is bottom left; the image's top row is north. No vertical UV flip is needed when this formula is used with a normal Blender image texture. A 4096 × 4096 derivative is also saved for lighter previews.

The atlas retains photographed lighting, ground shadows, source markings and capture-era differences from current OSM. Use it as a restrained roof/ground color contribution; it is not a physically neutral albedo scan. Aerial images cannot supply unseen façade details or establish surveyed building heights.

## Reproduce

With Pillow installed, run from the repository root:

```sh
python3 city-scene/aerial/scripts/fetch_imagery.py --size 8192
```

The script caches downloaded tiles and uses at most two concurrent requests. It does not require a private token or copy credentials from another application.

## Completed visual QA

The complete north-up atlas was inspected after all sixteen requests completed. Major coastlines, the lake chain, harbor islands, Christianshavn canals, and the Amager/mainland relationship match the prepared GIS diagnostic map. No artificial tile-grid seams or blank tiles were visible. The full atlas is 8192 × 8192 pixels (40,037,406 bytes); the mapping metadata records all sixteen request bounds. Photographed construction/capture-era differences remain possible and are not corrected or invented.

## Local Nyhavn atlas

`data/nyhavn_imagery.jpg` adds one 2048 × 2048 export over local X=1100–1850 m and Y=100–850 m. It improves the local sampling to approximately 0.366 m/texel. A single 4096-pixel request was not used because the service advertises a 4000-pixel maximum. Its exact geographic bounds, request URL, and the same source/license metadata are in `nyhavn_imagery.json`. The local atlas was visually checked: Nyhavn, Kongens Nytorv's edge, Sankt Annæ Plads, adjacent blocks, and the harbor are correctly oriented.

Local UV: `u=(world_x−1100)/750`, `v=(world_y−100)/750`. It is north up and requires no vertical UV flip in Blender. The image improves local roof/ground color resolution; it still contains capture shadows and cannot reconstruct façades or boats as geometry.
