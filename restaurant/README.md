# Alchemist — immersive restaurant asset

Open **`alchemist_06c_refine.blend`** for the latest saved editable scene. The 06 series refines the sculpted bronze entrance, chair upholstery, interior surfaces, and practical lighting. Pass 06c adds denser bark relief and a packed, generated microheight texture over the modeled bronze. The earlier **05 scene and web export remain the baseline for the existing full-room validation and browser asset**.

![Restaurant entrance, refinement 06c](renders/refine06_entry_review_c.png)

## Download and quick start

From the repository root, run:

```sh
python3 tools/restore_assets.py --archives restaurant-assets.zip
```

The restore tool automatically includes **`restaurant-refinements.zip`** and its extension **`restaurant-reference-updates.zip`**. The latest extension is on [Release v2026.09.08-workspace-snapshot](https://github.com/tangxiya-star/holly-blender-rendering/releases/tag/v2026.09.08-workspace-snapshot); the manifest retains the earlier releases for the original and 06-series archives. Together, they restore the original checkpoints, latest saved 06a/06b/06c scenes, completed renders, textures, references, and baseline web model into `restaurant/`, plus the unbuilt 07 relief experiment described below. The restore tool verifies each archive and its files. See the [root README](../README.md) for installation and manual download instructions.

| File | Recorded stage |
| --- | --- |
| `alchemist_06c_refine.blend` | Latest saved bronze-entrance and interior refinement, with packed microheight texture |
| `alchemist_06b_refine.blend` | Earlier narrower portal, darker patinated bronze, and weathered brick pass |
| `alchemist_06a_refine.blend` | First entrance/interior refinement; covered by `reports/refine06_validation.json` |
| `alchemist_05_final.blend` | Earlier complete restaurant and source of the existing web export |
| `alchemist_web.glb` and `alchemist_web.blend` | Optimized copies of the 05 baseline; not exports of the 06 refinements |
| `textures/restaurant_environment.exr` | Environment lighting and reflections for the baseline web model |
| `backups/restaurant_unsaved_backup_20260908_125825.blend` | Restaurant edits recovered while working on the eye dish; a separate checkpoint |

The latest completed entrance views are `renders/refine06_entry_review_c.png`, `renders/refine06_detail_review_c.png`, and `renders/refine06_oblique_review_c.png`. Pass 06b has the corresponding `_b` views. `refine06_hero_review.png` and `refine06_table_review.png` show the earlier 06a interior pass. The original `alchemist_{hero,arrival,dome,table,exit,lounge}.png` views belong to the 05 delivery.

## Explore the scene

The latest file opens at `CAM_Entry_Hero` with the entrance closed. `CAM_Entry_Detail` and `CAM_Entry_Oblique` show the relief at closer and angled viewpoints. The modeled doors remain closed through frame 40 and rotate open by frame 85.

Select the `WALKTHROUGH` scene camera, switch to camera view, and play frames 1–1441 for the approximately 60-second route through the entrance, arrival area, restaurant, dome, table, and exit. Original static cameras are `CAM_Arrival`, `CAM_Hero`, `CAM_Dome`, `CAM_Table`, `CAM_Exit`, and `CAM_Lounge`. The latest build retains the walkthrough, but its saved render is not a new full-route collision validation.

This Alchemist-inspired scene is based on published photographs. Its single-level floor plan and unseen geometry are inferred rather than surveyed. The 06b/06c portal uses a modeled 4.15 m leaf height and 2.624 m opening width, with width inferred from photographs. The separate [dome](../dome/README.md), [food](../food/README.md), [eyeball](../eyeball/README.md), and [cocktail](../cocktail/README.md) studies have their own project folders.

## Bronze relief and sources

Pass 06c uses actual sculpted geometry for the large roots, bark plates, cavities, silhouettes, and parallax. [Its build report](reports/refine06c_build.json) records 906 scene objects and 3,600,525 base vertices, including the detailed entrance geometry. The finish also retains the narrowed portal and weathered brick changes from pass 06b.

`textures/bronze_bark_microheight_06.png` is a **1254 × 1254 generated interpretation** of fine bark casting texture. `scripts/refine06_microtexture.py` loads it as Non-Color data, packs it, and maps it using each branch's `bark_coordinate` attribute. It contributes a bump response with a configured distance of **0.00085 m**; it is not measured height data or a replacement for the modeled relief. The full generation prompt is retained in `textures/bronze_bark_microheight_06_prompt.txt`.

The entrance references and credits are preserved in [door provenance](references/door_refine06/provenance.json) and [modeling observations](references/door_refine06/modeling_observations.md), including the supplied Eatweek Guide image and Dinesen/CHART references. These photographs guide reconstruction; they are not foreground cards or projected door materials. The original project credits remain in [reference_sources.md](references/reference_sources.md).

## Unbuilt 07 relief experiment

The final workspace snapshot also contains `scripts/refine07_relief.py`, `textures/door_relief07_height.png`, and `textures/door_relief07_height_prompt.txt`. **There is no saved 07 restaurant scene, render, or validation result in this delivery.** The latest completed scene remains 06c; the 07 height map has not been integrated into that file.

The module exposes `build_relief(height_path, materials, scene, ...)` for a future two-leaf bronze bas-relief and does no work when imported. Its 994 × 1582 scalar height image is a generated interpretation of the supplied entrance photograph, not measured depth or a scan. The proposed geometry can create parallax and shadows, but a single-valued height map cannot recover hidden surfaces or undercuts. No 07 rebuild or validation is represented as completed.

[New reference provenance](references/door_refine06/new_user_reference_provenance.json) records the later reference request. The exact ResearchGate image download returned blocked HTML; the separately retained Lex photograph by Søren Gammelmark is identified as an accessible reference, without claiming that it is the same image. Source links and credits remain in that provenance record.

## Rebuild the latest refinement

Restore the restaurant archives first. The recorded build used Blender 5.2.1 LTS, and the refinement driver explicitly selects Cycles with a Metal GPU. Use a separate working copy if you want to keep the delivered scenes, renders, build reports, and source snapshots unchanged.

From the repository root, with `blender` available on the command line:

```sh
blender --background --python restaurant/scripts/build_refine06.py -- --pass-c --render entry,detail,oblique
```

This loads the 05 baseline, rebuilds pass 06c, saves `alchemist_06c_refine.blend`, and renders the three review views. `--pass-c` includes the pass 06b finish and the microheight integration. Adding `--quality` increases resolution and sample settings and uses `_final_c` output names; those optional outputs are not claimed as delivered files.

The six construction modules used for the saved 06c build are retained under `reports/refine06c_sources/`, alongside the active modules in `scripts/`. Earlier `refine06_sources/` and `refine06b_sources/` remain historical snapshots.

## Validation and baseline web use

[refine06_validation.json](reports/refine06_validation.json) reports a pass for **06a only**. It checks static geometry, assets, hierarchy, the moving-door envelope, and unchanged sampled camera positions while reusing the 05 static-room validation baseline. `scripts/validate_refine06.py` still reads the 06a build report and source snapshot; it is not a 06b/06c validation entry point. No new 06c full-room clearance or photorealism pass is claimed.

The earlier evidence remains available:

- `reports/design_basis.md`: known, inferred, and unknown architecture and layout assumptions.
- `reports/realism_review.md`: original visual audit, corrections, and fidelity limits.
- `reports/final_validation.json`: 05 camera/body/floor checks, geometry, assets, and hierarchy.
- `reports/instance_audit.json`: original lettering-instance and navigation-route check.
- `reports/web_reimport_validation.json` and `renders/web_reimport_hero.png`: independent reload and verification of the baseline GLB.
- `reports/walkthrough.json`: original frame timings, positions, and look-at waypoints.

The hierarchy is `Restaurant`, with `Architecture`, `Dome`, `Tables`, `Seating`, `Lighting`, `Glassware`, `Props`, and `InteractionTargets`. Interaction empties are `entrance`, `hero_table`, `dome`, and `exit`. To replace dome content, edit material **PROJECTION | replace this image**, image node **REPLACEABLE_PROJECTION**. Mapping uses azimuth U and hemisphere elevation V, with the seam at the entrance side. The original and refined projection images remain under `textures/`.

For baseline web setup and measured export counts, see `reports/web_integration.md` and `reports/web_export.json`. Apply the HDR environment inside the restaurant and transition back to the travel world's environment at exit. The GLB is an asset rather than a standalone browser application. Its image-based lighting and reduced punctual-light set approximate Cycles indirect lighting; no device FPS claim is made. The 06 refinements have not been regenerated as a web export.
