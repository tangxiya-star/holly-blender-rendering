# Alchemist dish — food photography stress test

One photographed plate, containing the two topped pastry pieces visible in the supplied reference. The study is separate from the restaurant environment. It uses editable original geometry, procedural Principled BSDF materials, physical depth of field and Cycles lighting. A later web export preserves the full 3,688,277 evaluated triangles with baked vertex colors and browser material approximations. The interactive viewer is in [web-preview/](web-preview/README.md).

## Download

From the repository root, restore all five source scenes, renders, references, and web exports from [the project release](https://github.com/tangxiya-star/holly-blender-rendering/releases/tag/v2026.09.08-projects):

```sh
python3 tools/restore_assets.py --archives food-assets.zip
```

The script also copies the split glTF/BIN files into `food/web-preview/public/model/`. See the [repository README](../README.md) for installation and download options.

Final deliverables: **`food_final.blend`**, **`renders/food_final.png`** (1600 × 2399), and **`renders/food_final_linear.exr`**. Five Cycles versions and four correction passes are preserved.

**Result: the strict one-second photograph test is not passed.** The final render improves substantially over the first version but still has visible CG cues in pastry shape/crust, moss and the branch. See `reports/critique.md` for the ranked evidence. Treat this as a completed stress test with a failed realism criterion, not an approved photographic hero asset.

## Review the evidence

- `references/reference_dish.jpg`: exact supplied Eatweek Guide photograph, unmodified.
- `reports/reference_analysis.md`: visual analysis completed before modeling, including dimensions/camera estimates and material priorities.
- `reports/critique.md`: ranked visual failures and changes after each render.
- `food_01.blend`, `food_02.blend`, and subsequent numbered scenes: preserved iteration states.
- `renders/food_01.png`, `renders/food_02.png`, and subsequent renders: Cycles comparisons; matching `_linear.exr` files retain floating-point scene radiance.
- `scripts/build_test.py`, `scripts/food.py`, `scripts/support.py`: reproducible scene construction and materials. From round 02 onward, `reports/round_XX_sources/` stores the exact source scripts used for that build, with SHA-256 recorded in the build report.

## Scope and assumptions

Plate diameter is estimated at 170 mm. The source image has no EXIF block, so the camera is fitted by visual comparison. Ingredient names in the scene describe appearance; the photograph alone does not establish a recipe. The photo is never used as a foreground image plane, food texture or composited background. The table, plate, moss, branch, pastry, roe and tiny garnishes are rendered geometry.

The original reference and credit are retained under `references/`; see `references/reference_sources.md`. The user-provided photograph controls the composition, not a generic alternate food reference.

## Rebuild a numbered review render

From this workspace root, use the installed Blender executable:

```sh
blender --background --factory-startup \
  --python food/scripts/build_test.py -- 04 1067 224
```

Arguments after `--` are the round name, pixel width and maximum Cycles samples. Height preserves the original 1067:1600 ratio. A new round name preserves prior results. The build selects available Metal GPU devices, uses adaptive sampling and denoising, and writes a source `.blend`, PNG, linear EXR, source snapshot and build report.

Use the hero camera for evaluation. In Blender, Numpad 0 toggles camera view. The focus empty and two named area lights remain editable. The test's quality judgment is visual; high sample counts alone do not establish photographic realism.
