# Alchemist — immersive restaurant asset

## Download and quick start

From the repository root, run `python3 tools/restore_assets.py --archives restaurant-assets.zip`. This restores all restaurant Blender checkpoints, full renders, textures, references, and the web model into `restaurant/`. See the [root README](../README.md) for setup and the [release](https://github.com/tangxiya-star/holly-blender-rendering/releases/tag/v2026.09.08-projects) for direct downloads.

- `alchemist_05_final.blend`: complete editable scene with packed textures.
- `renders/alchemist_hero.png`: 1800 × 1012 hero view.
- `alchemist_web.glb`: separately optimized Three.js / React Three Fiber asset.
- `alchemist_web.blend`: optimized Blender copy.
- `textures/restaurant_environment.exr`: indoor environment lighting and reflections for the web model.
- `backups/restaurant_unsaved_backup_20260908_125825.blend`: separately preserved restaurant edits recovered while working on the eye dish; retained as a checkpoint, not the final scene.

In Blender, select the `WALKTHROUGH` scene camera, switch to camera view, and play frames 1–1441 for an approximately 60-second route through the entrance, arrival area, restaurant, dome, table, and exit. Static cameras are `CAM_Arrival`, `CAM_Hero`, `CAM_Dome`, `CAM_Table`, `CAM_Exit`, and `CAM_Lounge`.

This Alchemist-inspired scene is based on published photographs. Its single-level floor plan is inferred rather than surveyed. The separate original dome study is in [../dome/](../dome/README.md). The original dish and newer eye dish have their own folders: [food](../food/README.md) and [eyeball](../eyeball/README.md).

## Files and use

Milestones requested in the brief are retained: `alchemist_01_blockout.blend`, `alchemist_02_architecture.blend`, `alchemist_03_materials.blend`, `alchemist_04_lighting.blend`, `alchemist_05_final.blend`, `alchemist_web.blend`. Additional intermediate projection, furnishing and critique checkpoints are also retained.

Final rendered views are `renders/alchemist_{hero,arrival,dome,table,exit,lounge}.png`. Earlier numbered images document phase inspections and fixes. Blender source uses Cycles and AgX. Final source geometry and materials stay editable; the separate web copy evaluates and batches them.

The root hierarchy is `Restaurant` with `Architecture`, `Dome`, `Tables`, `Seating`, `Lighting`, `Glassware`, `Props` and `InteractionTargets`. Interaction empties are `entrance`, `hero_table`, `dome` and `exit`.

To replace the dome content, edit material **PROJECTION | replace this image**, image node **REPLACEABLE_PROJECTION**. Mapping uses azimuth U and hemisphere elevation V, with the seam at the entrance side. The original and refined generated image assets are both retained under `textures/`.

For web setup and measured export counts, see `reports/web_integration.md` and `reports/web_export.json`. Apply the HDR environment while inside the restaurant; transition back to the travel world's environment at exit. The GLB is an asset, not a standalone browser application. Cycles indirect lighting is approximated in the runtime with image-based lighting and a smaller punctual-light set; no device FPS claim is made.

## Evidence and rebuilding

- `reports/design_basis.md`: primary hero selection, known/inferred/unknown architecture, layout and phase notes.
- `reports/realism_review.md`: ten-question audit, ranked differences, fixes and remaining fidelity limits.
- `references/reference_sources.md`: source URLs and photo credits. Reference photographs are modeling guides, not projected content or exported texture assets.
- `reports/final_validation.json`: per-frame source camera/body/floor checks, finite geometry, scales, assets and hierarchy.
- `reports/instance_audit.json`: confirms the excluded generated lettering instance is above the navigation route.
- `reports/web_reimport_validation.json` and `renders/web_reimport_hero.png`: independent GLB reload, all-frame camera/floor checks and HDR-lit render. The missing non-rendering guide-curve warning is intentional; the 60-second animated camera is included.
- `reports/walkthrough.json`: frame timings, positions and look-at waypoints.
- `scripts/`: reproducible Blender phase drivers, PBR generation, geometry helpers, final threshold correction and web exporter.

The live MCP connection was unavailable and its CLI wrapper lacked the installed Blender path. Scene authoring and renders were completed with `bpy` through the installed Blender 5.2.1 executable. The user's requested interactive preview was launched on the review scene; the final scene was subsequently opened in another window, preserving previous files and the review window.
