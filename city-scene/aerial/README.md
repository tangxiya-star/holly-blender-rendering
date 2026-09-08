# Copenhagen — city aerial and cinematic descent

Open **`copenhagen_aerial_final.blend`** in Blender 5.2 or newer. This is the large-scale city scene. The separate four-street prototype is in [street/](../street/README.md).

The city uses **81,774 actual OpenStreetMap building footprints** over approximately **146 km²**, including Copenhagen's real harbor edge, canals, islands, historic blocks, parks, and road alignments. Surrounding real coastline continues over a roughly 41 × 47 km region. Heights and roof forms are approximate where OSM does not specify them; this is an aerial representation, not a survey-grade digital twin.

## Restore the assets

From the repository root, run:

```sh
python3 tools/restore_assets.py --archives city-aerial-assets.zip
```

The script downloads and verifies the aerial archive from [Release v2026.09.08-projects](https://github.com/tangxiya-star/holly-blender-rendering/releases/tag/v2026.09.08-projects), then restores its Blender scenes, full-size renders, geographic datasets, orthophoto imagery, and HDRI under `city-scene/aerial/`. This archive includes its own HDRI and can be restored independently of the street project. Python 3 and GitHub CLI (`gh`) are required for the download command. See the [repository README](../../README.md) for the full restore instructions.

After restoration, the main views are `renders/hero_aerial.png`, `renders/harbor_aerial.png`, and `renders/nyhavn_handoff.png`. The descent review frames are `renders/dive_0505.png` and `renders/transition_0673.png`.

## Views and animation

| Camera | Purpose |
|---|---|
| 01 · HERO | Primary southeast aerial, active when the file opens |
| 02 · Harbor and historic center | Closer city and water composition |
| 03 · Nyhavn | World Labs handoff approach |
| 04 · Geographic inspection | North-up inspection view |
| 05 · CINEMATIC DIVE | Animated descent, frames 1–673 at 24 fps |

To play the dive, select camera **05** in the Outliner and use **View → Cameras → Set Active Object as Camera**, then press Space. The timeline markers identify overview, harbor, descent, and handoff. Camera view is Numpad 0. Solid viewport shading is preset for responsive navigation; the saved PNG renders show Cycles lighting.

## World Labs handoff

Nyhavn is the selected target. Frame **649** is the camera match frame at **180 m** above the harbor datum, with a **40 mm** lens on a **36 mm** sensor. Frame 673 ends the Blender approach at 160 m. The original 54 m test exposed simplified facades, so the handoff was raised before that geometry dominates. The last second is reserved for a focus pull and transition into the detailed street environment.

Exact camera position, look direction, frame samples, and coordinate origin are in [camera_handoff.json](reports/camera_handoff.json). The World Labs scene or footage has not been provided, so it is **not connected or included**. The Blender file supplies the animated approach and a named handoff anchor; an actual seamless composite still requires that external environment and a matched view.

## Scope and performance

- 77,538 distant buildings use simple mass and roofs; 4,034 flight-area buildings receive additional roof variation; 202 buildings around Nyhavn use the highest aerial LOD.
- The buildings are combined into 770 tile meshes, rather than 81,774 separate objects. Roof/facade materials are shared.
- 38,000 canopies instance four reusable tree meshes in real green areas and mapped courtyards.
- Six skyline accents use real landmark coordinates: Marble Church, Our Saviour's Church, Christiansborg, City Hall, Rosenborg, and the Opera House. Amalienborg retains its real palace footprints.
- Cycles renders use reflective dark blue-green water, a packed photographic HDRI sky, soft directional light, and altitude-dependent atmospheric haze.
- No citywide interiors, storefronts, street furniture, or pedestrian models are included.

The Nyhavn approach also uses a separate 2048 × 2048 local atlas (0.366 m/texel), confined to a 750 m square.

The final scene also projects a shared 8192 × 8192 GeoDanmark orthophoto atlas onto roofs, roads, and terrain. It preserves real macro color and texture without unique materials for individual buildings. Imagery contains capture lighting and is therefore a visual approximation of albedo.

## Data and attribution

Geographic data **© [OpenStreetMap contributors](https://www.openstreetmap.org/copyright)**, available under the [Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Downloaded from Overpass on 8 September 2026. Cached queries, raw data, source metadata, derived geometry, map previews, and water/land control checks are in `data/`. Retain attribution when distributing the scene or rendered work.

Orthophoto imagery **© Klimadatastyrelsen / GeoDanmark**, **CC BY 4.0**. Provider, service restrictions, exact mapping, and source links are recorded in [imagery_sources.md](reports/imagery_sources.md). The Septima delivery endpoint was used for local evaluation; production delivery should use an appropriate licensed service.

The packed sky is **Overcast Soil (Pure Sky)**, original photography by Sergej Majboroda with sky edits by Jarod Guest, from [Poly Haven](https://polyhaven.com/a/overcast_soil_puresky), **CC0**. The aerial asset archive includes `textures/overcast_soil_puresky_2k.hdr` for independent rebuilds.

Origin: **12.5683° E, 55.6761° N**. Blender X points east and Y points north, in metres. Projection uses local equirectangular coordinates; Z=0 is harbor water, with the simplified urban ground at Z=2 m. Terrain elevation is deliberately simplified.

## Rebuild and validate

Restore the aerial archive first. Opening the supplied final Blender scene requires no Python packages outside Blender. To regenerate geographic inputs, see [Geographic data sources](data/SOURCES.md): preprocessing uses Python with Shapely >= 2.1 and Pillow. Image acquisition and its service constraints are documented in [Orthophoto sources](reports/imagery_sources.md). The archive includes the cached inputs, so the Blender rebuild below does not download imagery or geographic data.

Run from the repository root with Blender 5.2 or newer available as `blender`. These commands regenerate the scene files and review renders; run the stages once in order from the initial build:

```sh
cd city-scene/aerial
blender --factory-startup --background --python scripts/build_aerial.py
blender --factory-startup --background copenhagen_aerial.blend --python scripts/refine_aerial.py
blender --factory-startup --background copenhagen_aerial.blend --python scripts/finalize_aerial.py
blender --factory-startup --background copenhagen_aerial.blend --python scripts/apply_orthophoto.py
blender --factory-startup --background copenhagen_aerial_final.blend --python scripts/final_grade.py
blender --factory-startup --background copenhagen_aerial_final.blend --python scripts/validate_aerial.py
```

`copenhagen_aerial.blend` preserves the earlier city-massing stage; `copenhagen_aerial_final.blend` is the final orthophoto and local-grade delivery. The imagery is packed into the final scene, and the original files remain available in the asset archive for editing and rebuilding.

Final grade/local atlas: `scripts/final_grade.py`. City atlas: `scripts/apply_orthophoto.py`. Build: `scripts/build_aerial.py`. Refine/render: `scripts/refine_aerial.py`. Verification: `scripts/validate_aerial.py`. Build statistics, scene validation, landmark sources, and realism review are in `reports/`. The [final visual review](reports/final_realism_review.md) records remaining CGI cues; the scene is a geographic aerial prototype rather than indistinguishable photographic footage.
