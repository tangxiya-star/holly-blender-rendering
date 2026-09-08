# Alchemist dish viewer

Interactive web preview of the existing Blender dish model. Drag to orbit, scroll/pinch to zoom, use the switch for automatic rotation, and restore the original view with the reset button or R while the canvas is focused.

The split glTF package preserves the exported geometry and baked procedural color. The source has 61 mesh objects and 3,688,277 evaluated triangles. Browser materials approximate shader-only micro bump, spatial roughness and Cycles subsurface scattering; the browser preview is not a Cycles render.

From the repository root, run `python3 tools/restore_assets.py --archives food-assets.zip` to restore the model and its three BIN files into `food/web-preview/public/model/`. The Draco decoders are already included in Git. With Node.js >=22.13.0, run `npm ci` and `npm run dev` from `food/web-preview/` for local development. Use `npm run build` for the Sites Worker output. The existing Sites configuration is preserved; reorganizing this repository does not redeploy the viewer.

WebMCP optionally exposes `reset_dish_view` with an empty-object schema. Its live contract has not been verified because no supported browser/WebMCP context is available in this environment. The visible controls do not depend on WebMCP.

Validation: the production build, TypeScript check and targeted application lint pass. Full scaffold lint currently reports pre-existing issues in generated shadcn components and hooks. Vendor Draco decoders are excluded from linting. Model reimport validation confirms all exported geometry and baked color attributes; no browser visual QA was performed.
