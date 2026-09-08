# Alchemist — immersive restaurant asset

完整 Blender、纹理、模型与渲染保存在新仓库的 [Release](https://github.com/tangxiya-star/holly-blender-rendering/releases/tag/v2026.09.08)。先按[根目录说明](../README.md)恢复所需文件：餐厅源场景在 `restaurant-assets.zip`，全部渲染在 `renders.zip`，餐厅 web Blender/GLB 与环境 EXR 在 `web-assets.zip`。另有独立的[菜品交互网页](food_web_preview/README.md)。下文关于 GLB 非独立网页应用的描述专指餐厅模型。

## 快速查看

- `alchemist_05_final.blend`：可编辑的完整场景，贴图已打包。
- `renders/alchemist_hero.png`：1800 × 1012 主视角。
- `alchemist_web.glb`：单独优化的 Three.js / React Three Fiber 资产。
- `alchemist_web.blend`：优化后的 Blender 副本。
- `textures/restaurant_environment.exr`：网页室内环境照明与反射贴图。

Blender 中选择场景相机 `WALKTHROUGH`，切换到相机视角并播放第 1–1441 帧，即可查看约 60 秒的入口 → 到达 → 餐厅 → 穹顶 → 餐桌 → 出口路线。静态相机为 `CAM_Arrival`、`CAM_Hero`、`CAM_Dome`、`CAM_Table`、`CAM_Exit`，另有 `CAM_Lounge`。

这是依据公开照片制作的 Alchemist-inspired 场景；完整平面关系采用单层推断布局，并非实测还原。原先工作区中的 `alchemist_dome.blend` 没有修改。

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
