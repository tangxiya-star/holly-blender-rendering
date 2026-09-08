# Holly — Blender Rendering

Alchemist restaurant scenes, dish modeling and rendering, and an interactive web preview of the dish. This repository contains scripts, web source code, validation reports, and two final previews. Complete Blender scenes, full-resolution PNG/EXR renders, textures, and model exports are available in GitHub Releases.

**[Download all assets · v2026.09.08](https://github.com/tangxiya-star/holly-blender-rendering/releases/tag/v2026.09.08)**

This repository is public. Anyone can browse the source code and download the complete assets from the release page without an invitation or access approval.

## Final previews

![Alchemist restaurant hero view](alchemist/renders/alchemist_hero.png)

<img src="alchemist/food_stress_test/renders/food_final.png" width="400" alt="Final Cycles render of the dish" />

The dish is a completed modeling stress test. The original review found that it still shows visible CG cues and did not pass the strict photographic realism test. See [critique.md](alchemist/food_stress_test/reports/critique.md) for the full assessment.

## Choose an asset package

All archives preserve paths relative to the repository root. The four packages total **573.30 MiB** and contain **17 Blender scenes, 41 render files**, textures, reference images, and web models. Automatic `.blend1` backups, dependency directories, build caches, and local runtime logs are excluded.

| Release asset | Size | Contents |
| --- | ---: | --- |
| [renders.zip](https://github.com/tangxiya-star/holly-blender-rendering/releases/download/v2026.09.08/renders.zip) | 85.31 MiB | All restaurant, dish, and original dome renders, including PNG iterations and linear EXR files for the dish |
| [restaurant-assets.zip](https://github.com/tangxiya-star/holly-blender-rendering/releases/download/v2026.09.08/restaurant-assets.zip) | 51.22 MiB | Final and milestone restaurant Blender scenes, the original dome scene, textures, and reference images |
| [food-scenes.zip](https://github.com/tangxiya-star/holly-blender-rendering/releases/download/v2026.09.08/food-scenes.zip) | 276.47 MiB | Five editable Blender iterations of the dish and its reference image |
| [web-assets.zip](https://github.com/tangxiya-star/holly-blender-rendering/releases/download/v2026.09.08/web-assets.zip) | 160.30 MiB | Restaurant and dish GLBs, their corresponding web Blender scenes, split glTF/BIN files for the dish, and the restaurant environment EXR |

The release also includes `assets-manifest.json` with per-file sizes, SHA-256 hashes, original paths, and duplicate-file mappings, plus `SHA256SUMS.txt` with checksums for the release assets. The web preview uses the same glTF/BIN files as the export directory, so only one copy is uploaded. The restore script recreates the copies needed by the viewer, saving approximately 26.76 MiB of duplicate data.

## Restore all assets

Install GitHub CLI and Python 3.8 or later, then run the commands below. This command-line workflow uses GitHub CLI authentication; downloading assets directly from the release page does not require signing in.

```sh
gh auth login
gh repo clone tangxiya-star/holly-blender-rendering
cd holly-blender-rendering
python3 tools/restore_assets.py
```

The script downloads the pinned release `v2026.09.08`, verifies each archive and file against its SHA-256 hash, and restores the original folder structure. Identical existing files are skipped. If an existing file has different contents, the script reports an error to protect your edits. Use `--destination /path/to/empty-folder` to restore into a different directory.

To restore only the renders or only the web models:

```sh
python3 tools/restore_assets.py --archives renders.zip
python3 tools/restore_assets.py --archives web-assets.zip
```

If you have already downloaded the archives from the release, you can restore them offline:

```sh
python3 tools/restore_assets.py --from-dir /path/to/downloads
```

For a manual restore, extract the required ZIP files at the repository root. To run the dish viewer, also copy `alchemist/food_stress_test/web_exports/food_web.gltf` and the `food_web_*.bin` files from the same directory into `alchemist/food_web_preview/public/model/`. The restore script handles this step automatically.

## Open the scenes and run the viewer

- Final editable restaurant scene: `alchemist/alchemist_05_final.blend`.
- Final editable dish scene: `alchemist/food_stress_test/food_final.blend`.
- Restaurant usage, cameras, and rebuild instructions: [alchemist/README.md](alchemist/README.md).
- Dish render iterations and rebuild instructions: [food_stress_test/README.md](alchemist/food_stress_test/README.md).
- Interactive dish viewer instructions: [food_web_preview/README.md](alchemist/food_web_preview/README.md).

After restoring the web models, use Node.js 22.13.0 or later to run the viewer:

```sh
cd alchemist/food_web_preview
npm ci
npm run dev
```

The viewer retains its existing Sites project configuration. This release archives the existing web source and models; the viewer was not redeployed as part of the release. Browser materials approximate the original Cycles materials. When using the restaurant GLB, also load `alchemist/textures/restaurant_environment.exr`.

Historical reports and build snapshots preserve the original local paths, results, and source hashes as a record of the work. A few absolute workspace paths in the active scripts have been replaced with paths derived from each script's location. The scenes were not rendered again for this release.

## Future asset updates

Keep scripts, documentation, reports, and a small selection of final previews in Git. Publish Blender scenes, models, full-resolution images, and videos in a new release for each milestone, preserving previously published assets and checksum manifests. Each GitHub Release asset must be smaller than 2 GiB ([official documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)).

Consider Git LFS for source scenes that multiple collaborators edit frequently. It counts each complete file version toward storage and meters download bandwidth, so account for the applicable quotas ([Git LFS billing](https://docs.github.com/en/billing/concepts/product-billing/git-lfs)). Releases suit this project's milestone-based asset archives.
