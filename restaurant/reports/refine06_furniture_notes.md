# Dining upholstery refinement 06

Module: `scripts/refine06_furniture.py`; entry point `refine_furniture(scene)`.

Only the 28 dining seat meshes and 28 dining back meshes are assigned the new neutral charcoal textile. Chair legs, supports, transforms, layout, lounge seating, lights and other existing materials are untouched. The editable original cushions receive inward compression up to 1.1 mm. Matching 0.9 mm diameter piping is fitted onto evaluated cushion surfaces, inside the source local bounding envelopes. No change to the existing 0.52 m seat height or navigation layout.

The cloth has meter-based UV coordinates, 0.68/0.72 mm crossed yarn pitch, 65 micrometer bump distance at strength 0.23, roughness variation from 0.61 to 0.79, restrained sheen and small per-object color variation. This is an authored fabric approximation, not a measured scan. It intentionally avoids strong wrinkles or conspicuous contrasting stitching on the smooth tailored furniture.

Isolated Blender 5.2.1 background audit on `alchemist_05_final.blend` completed successfully without rendering or saving the source. Results: 28 seats, 28 backs, 56 seam curves; largest inward vertex change 0.0010989904 m; source mesh envelope expansion 0; all world transforms unchanged. Root integration render remains the visual acceptance check.
