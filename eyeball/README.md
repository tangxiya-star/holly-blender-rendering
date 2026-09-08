# Eyeball dish — Blender material and realism study

Open **`eye_07.blend`** for the latest editable 3D asset. Round 07 combines a modeled resin vessel, curved iris, and food insert with a reference-guided iris color texture. It includes a Cycles hero render and two additional camera angles. The iris improved, but the complete dish has not passed the project's photorealism review.

## Download the complete asset

The Blender scenes, full-resolution renders, textures, and reference images are in **`eyeball-assets.zip`** on [Release v2026.09.08-projects](https://github.com/tangxiya-star/holly-blender-rendering/releases/tag/v2026.09.08-projects). Source scripts and reports are in this folder in Git.

After cloning the repository, run this command **from the repository root**:

```bash
python3 tools/restore_assets.py --archives eyeball-assets.zip
```

The restore tool downloads and verifies the archive, then restores the files under `eyeball/`. Alternatively, download `eyeball-assets.zip` from the Release and extract it into the repository root, preserving its `eyeball/` folder. Downloading the repository ZIP alone does not include these large assets.

## Main files

| Path | Contents |
| --- | --- |
| `eye_07.blend` | Latest full 3D material trial, with packed textures. |
| `renders/eye_07.png` | 1600 × 2000 Cycles hero render. |
| `renders/eye_07_linear.exr` | Linear, floating-point hero render. |
| `renders/eye_07_orbit_135.png` | 960 × 1200 view at 135° azimuth and 45° elevation. |
| `renders/eye_07_orbit_255.png` | 960 × 1200 view at 255° azimuth and 28° elevation. |
| `eye_01.blend` through `eye_06.blend` | Earlier iterations, with corresponding PNG and EXR renders. Round 06 is the baseline for the latest material trial. |
| `textures/iris_07_albedo.png` | 1254 × 1254 iris color texture used in round 07. |
| `textures/iris_07_prompt.txt` | Full prompt used to generate the iris texture. |
| `scripts/` | Current construction, material, geometry cleanup, and optional Blender GUI helper scripts. |
| `reports/rotation_material_workflow.md` | Round 07 method, assessment, limitations, and next steps. |
| `reports/critique.md` | Iteration reviews and realism assessments. |
| `reports/reference_analysis.md` | Reference analysis and the revised blue-eye direction. |
| `reports/round_07_build.json` and `reports/round_07_topology.json` | Rendering and geometry cleanup records. |
| `reports/round_07_manifest.json` | Original round 07 asset checksums. |
| `reports/round_01_sources/` through `reports/round_07_sources/` | Historical source snapshots retained for comparison. |

Some historical reports remain in their original language. `reports/deliverable_manifest.json` records **round 06**, not the latest release. Historical manifests describe the files at the time of the experiment; the repository's asset restore manifest covers the published archives.

The restaurant session backup that was previously stored beside the eye study is now grouped with the restaurant project at `restaurant/backups/restaurant_unsaved_backup_20260908_125825.blend`, in the restaurant asset archive. It is separate from the eyeball asset.

## View the model

Restore the archive, then open `eyeball/eye_07.blend` in Blender. The scene is named `Eye 07 | full 3D material reconstruction`. The asset has full geometry and can be viewed from different angles; the saved camera provides the hero composition. Cycles material preview may initially appear noisy while it converges. Use the rendered PNGs when assessing the recorded result.

The scripts in `reports/round_*_sources/` are historical snapshots rather than standalone launch locations. Run the current entry points in `scripts/` when rebuilding.

## Rebuild

Use Blender with its bundled Python environment; these scripts import `bpy`, `mathutils`, and NumPy. The original build reports record Blender 5.2.1 LTS. The round 07 material script selects **Cycles Metal on GPU**, so its render configuration requires a matching setup. Other devices have not been validated for this archive.

After restoring the assets, run the following from the repository root, with `blender` available on your command line:

```bash
# Rebuild and render the round 06 baseline.
blender --background --python eyeball/scripts/build_eye_test.py -- 06 1600 768

# Load round 06, apply the round 07 texture and geometry cleanup, and render.
blender --background --python eyeball/scripts/build_material_trial07.py
```

**These commands overwrite the corresponding round 06 or round 07 Blender files, renders, build reports, and source snapshots.** Make a separate working copy before experimenting. The second command can use the restored `eye_06.blend` directly, without running the first. Calling `build_eye_test.py` without arguments defaults to round `01` and would overwrite that iteration.

Optional GUI helpers preserve their original purpose:

- `scripts/show_eye_07_visible.py` saves and verifies a backup of the open Blender session, then opens round 07.
- `scripts/show_latest_in_visible_blender.py` is the **historical round 06 helper**, despite its filename. It appends round 06 and saves a separate review project.
- `scripts/start_visible_mcp.py` requires the separately installed Blender MCP extension; it is not needed to open or render the asset.

## Method, limitations, and credits

The vessel is reconstructed as transparent resin with layered iris and sclera details. The [manufacturer, 10 Tons](https://www.10tons.dk/eyeball), describes a 200 mm diameter and layered construction embedded in resin. This study follows that vessel scale and does not establish the realism of arbitrary food materials. The food insert reconstructs the roe and wet surfaces visible inside the pupil; unseen recipe layers are not documented.

The principal blue-eye reference is stored as `references/reference_blue_newyorker.jpg` and comes from [The New Yorker photograph supplied in the user's reference](https://media.newyorker.com/photos/66e995fe2651982b1f8d8ed3/master/w_1600%2Cc_limit/r44894.jpg). The earlier purple-lit reference, `references/reference_eye.jpg`, comes from [supertaster Mel's Alchemist restaurant account](https://www.supertastermel.com/2022/07/copenhagen-alchemist-rasmus-munk.html).

Round 07 uses an iris color interpretation generated with the built-in image generation tool, mapped onto the curved iris beneath the modeled resin. It is not measured albedo, a photogrammetric scan, or a finished photograph projected onto the model. Cycles calculates the geometry's lighting, reflections, and refraction. Surfaces absent from the reference photographs are inferred reconstructions.

The iris material improved and was checked from three angles. Remaining issues include the sclera and vein treatment, separated roe particles, overly regular edges and reflections, and procedural patterns in the stone. **The full dish still fails the photorealism gate.** No web optimization or GLB export has been performed for this study.
