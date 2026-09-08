# Holly — Blender Rendering

A collection of Blender projects, organized by the work: an eye dish, Copenhagen street and aerial scenes, the Alchemist restaurant, a plated dish with a web viewer, and the original dome study.

**[Download the latest complete assets](https://github.com/tangxiya-star/holly-blender-rendering/releases/tag/v2026.09.08-projects)** · **[Browse the asset manifest](docs/assets-manifest.json)**

This repository is public. Code, project guides, reports, and one preview per project are in Git. Full Blender scenes, renders, textures, model exports, and large geographic datasets are in the release. **Cloning or downloading the repository alone does not include these large assets.**

## Projects

| Folder | Project | Latest scene or entry point |
| --- | --- | --- |
| [eyeball/](eyeball/README.md) | Editable eye dish and seven material/geometry iterations | `eyeball/eye_07.blend` |
| [city-scene/street/](city-scene/street/README.md) | Copenhagen street and expanded neighborhood | `city-scene/street/copenhagen_neighborhood.blend` |
| [city-scene/aerial/](city-scene/aerial/README.md) | Geographic Copenhagen city aerial and cinematic descent | `city-scene/aerial/copenhagen_aerial_final.blend` |
| [restaurant/](restaurant/README.md) | Alchemist-inspired restaurant, walkthrough, and web model | `restaurant/alchemist_05_final.blend` |
| [food/](food/README.md) | Plated dish study and interactive web preview | `food/food_final.blend`; `food/web-preview/` |
| [dome/](dome/README.md) | Original dome study | `dome/alchemist_dome.blend` |

Each project keeps its own scripts, reports, references, and asset paths. Earlier scene and render iterations are preserved in its asset package. Historical source snapshots and validation reports remain records of their original builds; their old local paths and hashes are not rewritten to imply a new validation run.

## Previews

### Eye dish — iteration 07

<img src="eyeball/renders/eye_07.png" width="360" alt="Eye dish, iteration 07 Cycles render" />

### Copenhagen neighborhood

![Expanded Copenhagen neighborhood](city-scene/street/renders/neighborhood_overview.png)

### Copenhagen city aerial

![Copenhagen city aerial](city-scene/aerial/renders/hero_aerial.png)

### Alchemist restaurant

![Alchemist restaurant hero view](restaurant/renders/alchemist_hero.png)

### Plated dish

<img src="food/renders/food_final.png" width="360" alt="Final Cycles render of the plated dish" />

The [dome project](dome/README.md) has its own preview. These are the existing renders, not new renders produced during this archive update.

## Download by project

The six ZIP packages total **1,623.50 MiB (about 1.59 GiB)** and contain **32 Blender scenes**, original renders, textures, references, web models, and geographic data. Each archive preserves the new paths relative to the repository root.

| Release asset | Size | Contents |
| --- | ---: | --- |
| [eyeball-assets.zip](https://github.com/tangxiya-star/holly-blender-rendering/releases/download/v2026.09.08-projects/eyeball-assets.zip) | 594.94 MiB | Seven eye scenes, main and orbit renders, linear EXRs, iris texture, and reference images |
| [city-street-assets.zip](https://github.com/tangxiya-star/holly-blender-rendering/releases/download/v2026.09.08-projects/city-street-assets.zip) | 154.99 MiB | Five street/neighborhood scenes, renders, CC0 road textures and HDR, reference images |
| [city-aerial-assets.zip](https://github.com/tangxiya-star/holly-blender-rendering/releases/download/v2026.09.08-projects/city-aerial-assets.zip) | 292.46 MiB | Two aerial scenes, renders, raw and derived OSM data, imagery atlases, diagnostic images, and its own HDR |
| [restaurant-assets.zip](https://github.com/tangxiya-star/holly-blender-rendering/releases/download/v2026.09.08-projects/restaurant-assets.zip) | 108.04 MiB | Restaurant checkpoints, separately recovered restaurant edits, all restaurant renders, textures, references, and web Blender/GLB |
| [food-assets.zip](https://github.com/tangxiya-star/holly-blender-rendering/releases/download/v2026.09.08-projects/food-assets.zip) | 471.34 MiB | Five dish scenes, renders, reference, web Blender/GLB, and split glTF/BIN for the viewer |
| [dome-assets.zip](https://github.com/tangxiya-star/holly-blender-rendering/releases/download/v2026.09.08-projects/dome-assets.zip) | 1.73 MiB | Original dome Blender scene and render |

The release includes `assets-manifest.json` with every asset path, size, and SHA-256, and `SHA256SUMS.txt` with archive checksums. The food viewer's identical model copies are uploaded once and recreated by the restore script. The aerial package includes its own HDR so it can be restored independently of the street package.

Automatic `.blend1` backups, dependency folders, build caches, and local runtime/debug logs are omitted. The separately recovered restaurant scene is retained under `restaurant/backups/`. The local Chinese-named eye shortcut points to `eye_07.blend` and is not duplicated.

## Restore everything

Install Python 3.8 or later and GitHub CLI, then run:

```sh
gh auth login
gh repo clone tangxiya-star/holly-blender-rendering
cd holly-blender-rendering
python3 tools/restore_assets.py
```

This downloads the pinned release `v2026.09.08-projects`, verifies each archive and file, and restores the complete folder structure. Identical files are skipped; different existing files cause an error instead of being overwritten. Use `--destination /path/to/empty-folder` to restore into a fresh location.

For just the eye dish or the city scenes:

```sh
python3 tools/restore_assets.py --archives eyeball-assets.zip
python3 tools/restore_assets.py --archives city-street-assets.zip city-aerial-assets.zip
```

You can also download ZIPs directly from the public release page without signing in. Extract them at the repository root, or verify and restore downloaded ZIPs offline:

```sh
python3 tools/restore_assets.py --from-dir /path/to/downloads
```

For an offline subset, add `--archives` with the names you downloaded. With a manual food restore, also copy `food/web_exports/food_web.gltf` and `food_web_*.bin` into `food/web-preview/public/model/`; the script does this automatically.

## Run the food viewer

After restoring `food-assets.zip`, use Node.js 22.13.0 or later:

```sh
cd food/web-preview
npm ci
npm run dev
```

The existing Sites configuration is preserved. This update archives the latest local code and saved assets and fixes paths affected by the folder move; it does not redeploy the viewer, regenerate web exports, or rerender scenes. Follow each project's README for Blender build steps and platform requirements. Rebuild in a separate working copy if you want to retain the delivered files.

## Scope and sources

The eye and plated-dish studies retain their original realism assessments: visible CG cues remain, and they are not claimed to pass the strict photographic realism test. The street layout is representative and fictional; the aerial scene uses geographic footprints with approximate heights and roof forms. The aerial World Labs handoff is a camera anchor and animation, with no external World Labs scene included.

Reference photographs are modeling guides, not scene textures. Preserve the source credits in each project's references and reports. City geographic data is © OpenStreetMap contributors under ODbL; the orthophoto atlas is © GeoDanmark / Klimadatastyrelsen under CC BY 4.0. See the [city overview](city-scene/README.md) and [imagery provenance](city-scene/aerial/reports/imagery_sources.md) for source and delivery-service details.

## Previous layout

The original [v2026.09.08 release](https://github.com/tangxiya-star/holly-blender-rendering/releases/tag/v2026.09.08) remains unchanged and uses the old `alchemist/` layout. Its [manifest](docs/releases/v2026.09.08/assets-manifest.json) is retained for reference. Use that tag's code to restore that version; the current restore script uses the new project folders.

| Previous workspace path | Current repository folder |
| --- | --- |
| `alchemist/eye_food_stress_test/` | `eyeball/` |
| `copenhagen/` | `city-scene/street/` |
| `copenhagen_aerial/` | `city-scene/aerial/` |
| `alchemist/` restaurant files | `restaurant/` |
| `alchemist/food_stress_test/` | `food/` |
| `alchemist/food_web_preview/` | `food/web-preview/` |
| Root dome files | `dome/` |

For future updates, keep code and small previews in Git and publish full assets in a new release per milestone. Preserve existing release assets and checksums so teammates can recover an exact version.
