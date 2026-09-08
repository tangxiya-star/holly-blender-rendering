# Antini cocktail — Blender study

Open **`cocktail_08.blend`** for the latest saved iteration. This editable study includes a glass coupe, pale straw-green liquid, an ant garnish, and a dark stone-table lighting setup. **Eight numbered Blender scenes, eight completed 1000 × 1250 Cycles PNGs, and a round 08 linear EXR** are preserved. A separate review workspace is also included. These saved results do not establish photographic realism.

![Cocktail, iteration 08](renders/cocktail_08.png)

## Download

From the repository root, run:

```sh
python3 tools/restore_assets.py --archives cocktail-assets.zip
```

The restore tool automatically includes **`cocktail-finalization.zip`** from [Release v2026.09.08-workspace-snapshot](https://github.com/tangxiya-star/holly-blender-rendering/releases/tag/v2026.09.08-workspace-snapshot). This extension adds the completed 08 scene and outputs to the earlier cocktail archive. The manifest pins both archives to their own releases. Source modules, reference notes, and reports are tracked in Git. See the [root README](../README.md) for setup and verification instructions.

The 08 Blender file packs the restaurant environment image and its completed hero PNG. Opening the supplied file does not require separately restoring the restaurant. Rebuilding round 08 from source does require the restaurant environment EXR, as described below.

## Files and recorded setup

- `cocktail_01.blend` through `cocktail_08.blend`: eight separate scene iterations.
- `renders/cocktail_01.png` through `renders/cocktail_08.png`: completed Cycles results.
- `renders/cocktail_08_linear.exr`: round 08 floating-point render for further image work.
- `cocktail_current_review.blend`: a separate review workspace built from **round 07** and its packed PNG; it is not a copy of round 08. Its `Hero Render` workspace shows the image, and `3D Model` provides model inspection.
- `references/restaurant_environment_preview.png`: preview of the existing restaurant environment used in round 08.
- [reports/round_08_final.json](reports/round_08_final.json): native round 08 completion metrics, written after rendering and the final save.
- `reports/round_01.json` through `reports/round_07.json`: earlier scene, camera, render settings, and geometry records, written before each render started.
- [reports/critique.md](reports/critique.md): recorded visual critiques through round 06 and the resulting round 07 corrections.
- `reports/round_01_sources/`: the original source snapshot, preserved as historical evidence.

The scene is named `Cocktail | Alchemist photographic test`. Round 08's completion report records 60 objects, GPU rendering configured for 512 samples, a 95 mm lens at f/20, and approximately 60.3 seconds for the native finalization/render operation. The source retains 20 transmission bounces. No web export or texture bake is included.

Round 07 adjusted the existing backdrop, source reflections, liquid scattering and absorption, and ant body contours. Round 08 further adjusts the backdrop and glass-foot contact and adds a restrained, irregular room reflection from the existing restaurant panorama. The retained critique does not include a completed round 08 visual assessment, and no photorealism pass is claimed.

## Native round 08 finalization

`scripts/finalize_native.py` runs in native Blender against an already loaded cocktail scene. It was used with the saved round 07 scene, explicitly selects the **Metal** Cycles backend, renders synchronously, writes PNG and EXR outputs, packs the environment and completed PNG, and saves the final scene. It requires a Blender build that supports Metal and its bundled NumPy; selecting the Metal backend itself is not portable to an unsupported platform. The recorded Blender version for this study is 5.2.1 LTS.

The source dependency is `restaurant/textures/restaurant_environment.exr`, restored by the restaurant asset package. From the repository root:

```sh
python3 tools/restore_assets.py --archives cocktail-assets.zip restaurant-assets.zip
blender --background --factory-startup cocktail/cocktail_07.blend --python cocktail/scripts/finalize_native.py -- 08 1000 512
```

Arguments after `--` are the output label, width, and sample limit. Height is 1.25 times the width. This command rebuilds the 08 result from 07 and replaces files using that label, including its PNG, EXR, completion report, and environment preview. Use a separate working copy to preserve the delivered results.

`scripts/make_review_file.py` is a separate helper that loads `cocktail_07.blend` and `renders/cocktail_07.png`, builds the image/model review workspaces, and saves `cocktail_current_review.blend`. It uses Blender window, workspace, and editor context. Its hard-coded source remains round 07 even though the latest numbered asset is now 08.

## Earlier GUI/MCP modules

Construction uses `photo_stage`, `build_cocktail`, and `ant_garnish`. The numbered `refine_02.apply(scene)` through `refine_07.apply(scene)` functions edit the appropriate preceding scene; they are not independent constructors. Running `blender --background --python scripts/build_cocktail.py` only defines functions and does not build the delivered scene.

`render_control.start(scene, "07", samples=512)` configures rendering, saves the selected scene and its settings report, then invokes a GUI render. It depends on an interactive Blender context and the configured GPU backend. For these earlier modules, a saved `.blend` or round report alone does not prove the render finished.

The pre-cocktail session checkpoint is archived separately under `eyeball/backups/pre_cocktail_session_20260908_140658.blend`. Embedded scene labels identify eye-study scenes; its full session contents have not been reopened and validated for this publication. It is not a cocktail iteration or a required build input.

## Reference and limits

The cocktail reference photograph is credited to Alchemist and documented in [reference_notes.md](references/reference_notes.md), with links to InsideHook. The inferred 91 mm bowl diameter, 166 mm vessel height, and 0.85 mm rim thickness are visual reconstruction assumptions rather than manufacturer measurements. That external reference photograph itself is not included in this project. The separate environment preview comes from this repository's restaurant render, not a newly sourced photograph.

The geometry audit records closed glass and liquid meshes for the checked objects. It does not establish photographic realism or recipe accuracy. The source and rendered iterations remain available for further review.
