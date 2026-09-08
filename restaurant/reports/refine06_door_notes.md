# Entrance bronze door refinement 06

Owner module: `scripts/refine06_door.py`. Entry point: `build_door(materials)`.
Importing the module changes nothing. Required material keys are `bronze`,
`recess`, and `edge`; the module does not modify their node trees.

## Reference interpretation

Visually studied `references/entrance.jpg`, the high resolution frontal entrance
photo. The actual sculpture has broad, twisting, folded trunks and sharply
layered bark, deliberate quiet recessed fields, a left upper oval knot, a more
forked right upper web, long lower trunks and a thin straight central seam.
The geometry traces the broad visible branch organization independently for
each leaf. It is a dimensional interpretation from a photograph, not a scan
or a claim to reproduce the artist's exact casting.

The module preserves the existing architectural opening: nominal combined leaf
width 3.2 m including 24 mm center seam, height 4.15 m. This is integration scale
inferred for this scene, not a measured dimension of the actual door. The latest
reference research reports the real entrance as approximately 4 m tall.

## Geometry

- 18 meshes and 2 hinged parents, under `Architecture`.
- 722,200 base vertices and 1,440,156 base triangles before frame bevels.
- Left: 26 primary cast roots, 158 raised bark lamellae, 40 forked splinters.
- Right: 28 primary cast roots, 156 raised bark lamellae, 44 forked splinters.
- Closed branch meshes have smoothly changing elliptical sections, swelling,
  taper, 7–11 asymmetric angular furrows, longitudinal drift and fine edge
  scalloping. Major roots use 48-sided sections at approximately 5 mm stations.
- Narrow lamellae supply additional actual relief along the trunk surface.
- Solid cast leaves provide a 139 mm fully backed panel assembly. Front inset
  fields have subtle geometric waviness and are supported by that continuous
  solid leaf; they are not detached image planes.
- Four recessed stories, mitred multiple-profile outer casting, horizontal
  root rails, worn bosses, four hinge pintles per leaf and rear reinforcing
  straps remain visible at oblique angles.
- Root bounds are softly compressed inside z = .065–4.155 m and depth
  y >= -.170 m in each hinge's local coordinates. This retains rounded organic
  transitions while preventing broad bottom root flares entering the ground.

Material attribute data exists on every created mesh as POINT FLOAT:

| Attribute | Meaning |
| --- | --- |
| `bronze_wear` | 0 = quiet sheltered metal; 1 = prominent exposed ridge |
| `bronze_cavity` | 0 = exposed surface; 1 = deep bark furrow or moulding recess |

These are authored geometric masks rather than baked ambient occlusion. A
physical patina/roughness shader can use them subtly; excessive high-contrast
color ramps will exaggerate the procedural bark into a zebra pattern.

## Preserved content and animation

The 16 legacy `Entrance_Bronze_Leaf*`, `Entrance_Leaf_Crossrail*`,
`Entrance_Leaf_Stile*`, and `Entry_Bronze_Root_Relief*` objects are retained with
viewport/render visibility disabled. No masonry or portal objects are removed.
Only this module's `REF06_Door_*` objects are replaced on a repeat call.

Hinge locations are (-1.6, -19.02, 0) and (1.6, -19.02, 0). The leaves are closed
on frames 1 and 40; on frame 85 their Z rotations are +90° and -90° respectively.
All detailed geometry follows those parent transforms. The function leaves the
scene on frame 1 for the closed entrance hero. It does not alter cameras,
navigation, rendering, lighting, scene frame range, or output paths.

## Validation

Python syntax check passed. Isolated background Blender 5.2.1 LTS loaded
`alchemist_05_final.blend`, called the function, returned the statistics above and
saved `/tmp/alchemist_door06_smoke.blend` successfully. No visible Blender session
was touched. Checked exposed root normals face -Y and frame-85 rotations match
the intended opening angles. A lower-right diagonal root flare found by the
initial bounds audit was corrected with smooth casting limits after that smoke
file was saved; root integration must use the current module.

Root owns the material, lighting and Cycles image review. This module does not
claim photorealism based only on mesh density or a viewport. Important rendering
checks: bronze should remain dark neutral rather than bright brass; raking light
should reveal folded bark without bright outlining every ridge; smooth negative
spaces should remain visible between trunks; examine both straight and oblique
views before approving the entrance.
