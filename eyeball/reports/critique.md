# 1984 eye dish — Cycles critique and correction record

Ingredient inventory is frozen after render 01. More geometry for the same roe, vessel and stone is refinement, not additional ingredients. Rounds 01–03 use the original 600 × 600 source. From round 04 onward, the user's clearer blue-eye screenshot and its 1600 × 2000 New Yorker photograph are the primary visual target; no generated substitute is used.

## Render 01 — 1200 × 1200, Cycles Metal, 256 maximum samples

**Verdict: clearly CGI; photographic criterion not passed.** The body silhouette, overall framing and food opening are broadly close. They should not be rebuilt indiscriminately.

Five strongest cues, ranked:

1. **Iris structure/optics:** dark, wavy woodgrain or satin under excessive clean reflection. The source has much lighter gray-green/beige radial fibers with interruptions, sector variation and a soft outer transition.
2. **Outer body:** clean ivory ball with faint scratch-like longitude lines. The source shows a fine branching pink vascular network and diffuse pink/red lower-body coloration.
3. **Food:** isolated gold pins on a flat purple surface. Too much liquid is exposed; the source is a crowded dark brown/amber granular surface with occluded wet contacts.
4. **Illumination:** the lavender studio wash is too bright. The source has deep blue-violet background, warm left illumination, and stronger grounding shadow.
5. **Surface perfection:** large pristine iris reflections, sharp circular material boundaries and evenly fine stone produce product-CG polish.

### Correction loop 1

- Lighten and desaturate iris stroma, greatly reduce coherent wave bending, introduce broken fine radial fibers and a softer outer blend. Keep a dark scalloped pupil annulus and reduce dominating clear-film reflection.
- Add finer second/third-order vein branches, varied directions and soft rose lower-body coloration while retaining the pale upper band. Preserve measured silhouette ratios.
- Densify the existing roe until grains dominate the exposed surface, mute gold coloration, reduce the large purple gel reflection and vary cap heights. Adjust violet lighting/exposure supporting these material corrections, move a smaller key reflection closer to the pupil, and seat the existing assembly on the stone.

No first-render photographic pass is claimed.

## Render 02 — 1200 × 1200, Cycles Metal, 320 maximum samples

**Verdict: still CGI.** The iris no longer reads primarily as wavy woodgrain, the food has much better coverage, and the background is darker. A lighting correction introduced a new failure: the narrowed softbox beam concentrates illumination and cuts sharply across the vessel. The resulting highlights prevent fair material evaluation.

Five remaining cues, ranked:

1. **Overexposure and beam cutoff:** white upper body, bleached stone and an abrupt oval boundary across the vessel, instead of the source's smooth cream/pink/violet transition.
2. **Food highlights:** dense roe now reads silver/beige because too many caps are dominated by white reflections. Packing should be retained.
3. **Iris glare:** a broad white reflection washes out the improved gray/olive fibers and dark pupil annulus.
4. **Vein layout:** branching exists, but too many long vertical paths still suggest hanging strings. Finer shorter irregular trees and stronger diffuse pink coloration are needed.
5. **Surface uniformity:** clean circular boundary and uniformly fine stone texture still resemble a product render.

### Correction loop 2

- Replace the narrow bright beam with a broader lower-power warm source so illumination falls off smoothly across the body. Retain darker violet ambience.
- Keep the denser existing roe and evaluate it under reduced illumination rather than darkening all materials to compensate for an overpowered light.
- Control iris reflection with a small separate neutral source near the pupil and quieter clear-film response. Preserve the corrected fibers and dark annulus. Refine the existing vascular pigment where it remains too sparse or directional.

The photographic criterion remains a visual gate after the next render, not a consequence of completing two loops.


## Render 03 — 1200 × 1200, Cycles Metal, 384 maximum samples

**Verdict: still visibly CGI; user also rejected the realism.** The hard lighting cutoff is gone and food is darker, but the fundamental iris construction remains inadequate.

Ranked cues: (1) uninterrupted brown-gray radial lines resembling printed vinyl, (2) beige body and insufficient irregular vascular blush, (3) washed-out mauve ground, (4) similarly exposed glossy grains, and (5) exact material edges and uniformly fine stone.

### Correction loop 3 — based on the user's clearer blue reference

- Replace the flat iris treatment with a new layered blue/cyan pigment bed, actual branching fiber geometry, irregular crypts and a closed clear resin layer. Use the maker's verified physical scale.
- Rework the body color by height into pale sclera and a mottled pink/red lower transition, with embedded vascular lines and a physically plausible outer resin finish.
- Re-light with neutral directional illumination and restrained fill; quiet most food-grain highlights, create correlated immersion/color patches, and introduce larger worn stone depressions. Keep the same ingredient inventory.

## Render 04 — 1400 × 1750, Cycles Metal, 384 maximum samples

**Verdict: improved construction, still visibly CGI.** Review uses the blue New Yorker reference. The maker's 200 mm diameter and cast-resin construction are now reflected in the scene.

Five strongest cues, ranked:

1. **Iris signal at hero scale:** thousands of fine fibers remain nearly subpixel and too uniformly teal. The reference is dominated by broader milky-blue, branching bundles and pale crypt regions.
2. **Stone relief:** fine uniform contour noise dominates. The reference has larger broken recesses and cracks separated by quiet worn islands.
3. **Sclera pigment:** too immaculate and beige, with most veins faint and uniformly narrow. The reference has several visible wavy trunks, branching fine vessels and an irregular pink-red base.
4. **Lighting:** excess fill keeps the left face and cast shadow too light relative to the reference.
5. **Food and central rim:** the grains are individually too legible and the black insert edge too manufactured.

### Correction loop 4

- Add 156 broad forked pale-blue fiber bundles beneath the clear resin, their branches and frayed tips; retain fine fibers as secondary detail. Lighten inner/middle iris and break the continuous inner border.
- Rebuild stone as a 961 × 961 physical surface with clustered multi-scale pits, broken clefts, chipped shoulders and quieter islands. Reduce fine bump prominence.
- Add a sparse set of wider, irregular embedded vascular trunks with faint surrounding haze; broaden and mottle the lower pink-red transition. Reduce fill one stop and make a small framing shift to follow the blue reference.

No additional ingredients, source-photo projection or image-generation substitution. Round 05 must be judged from its actual Cycles output.

## Render 05 — 1600 × 2000, Cycles Metal, 512 maximum samples

**Verdict: not a photographic pass.** Wider iris fibers are visible, but still too dark and narrow. The new stone geometry introduced overly smooth, large amoeba-like cavities. New principal veins are visible but too straight. These failures are visible at normal viewing size, so extra render samples alone would not resolve them.

Five strongest cues, ranked:

1. Iris remains a dark radial disc rather than a pale layered blue structure.
2. Stone has large smooth depressions and insufficient small sharp chipped pits.
3. Lighting/projection is too frontal and filled, with a shallower view into the pupil and weaker left shadow than the reference.
4. Sclera veins are long, straight, evenly tapered paths; vascular coloration lacks the reference's warmer irregular base.
5. Roe reads as individually distinct flat discs above a pristine manufactured black rim.

### Correction loop 5

- Increase broad iris fiber widths roughly threefold and substantially raise pale pigment reflectance. Keep the blue outer ring, interwoven fine fibers, crypt recesses and clear resin volume.
- Halve the large stone depression amplitude, introduce clustered smaller chipped pits with cavity color and roughness variation, and retain quieter worn areas.
- Raise the camera to 55 degrees to better match the iris and pupil ellipse, set f/11, lower the right key position and reduce fill. Widen the visible iris slightly, make principal veins more irregular, and warm the basal pigment. Refine the existing roe geometry to reduce flattened-disc appearance; keep the same food inventory.

The visible restaurant session was preserved to `restaurant_unsaved_backup_20260908_125825.blend` before opening the eye study. A separate Blender process successfully read that backup and verified the restaurant scene, 804 objects and 720 meshes.

## Render 06 — 1600 × 2000, Cycles Metal, 768 maximum samples

**Final test verdict: FAIL — still visibly CGI in a one-second inspection.** This is a recognizable, improved editable recreation. It should not be described as photorealistic or used as evidence that the restaurant's hero-food pipeline has passed. Both the primary visual review and an independent reference comparison reached this conclusion.

Five remaining cues, ranked:

1. **Iris:** pale geometry now reads as opaque brush strokes with crisp overlapping edges. The reference has softer, partially translucent bundled fibers and crypt structure; increasing width and brightness solved visibility but did not reproduce the material.
2. **Sclera:** veins still resemble drawn paths on a clean uniform body. The source's ivory, vascular haze and rusty basal mottling are more varied and optically integrated.
3. **Stone:** the surface retains a consistent procedural scale and density. The reference mixes fine broken cavities, quieter worn islands and occasional coarse seams.
4. **Food:** roundedness improved, but grains remain individually isolated with dark gaps and an overly clean circular rim. The source's partly immersed granular mass has less distinct boundaries.
5. **Finish and light:** pristine highlights and orderly shading still give a product-render appearance. Reference reflections, scattering and roughness vary more locally.

### What was actually verified

- Six preserved Cycles renders and five critique/correction loops; no web optimization.
- Round 06: 25 scene objects, 1,719,010 base mesh vertices, 24 materials, measured vessel width approximately 200.02 mm.
- 101 modeled roe grains, layered iris with 176 broad bundles plus fine branching fibers, embedded vascular pigment and displaced stone.
- 85 mm camera, 55-degree elevation, physical f/11 depth of field; 1600 × 2000 PNG and linear half-float EXR.
- Standalone source file opens. Both original procedural texture images are packed, with no linked material/image/object dependencies and no missing external files.
- User-visible Blender was verified showing `eye_04.blend`. It later changed to `copenhagen_final.blend` while work continued. The latest `eye_06.blend` is ready; the user was asked whether to switch the foreground away from that street scene.

More samples would not fix the remaining appearance errors. A further production attempt needs a different iris/pigment authoring approach and closer matching of measured surface detail, rather than accepting the present procedural look. This study provides a concrete negative result for the proposed one-second realism gate.

## Render 07 — new material method, 1600 × 2000, 768 maximum samples

After the user asked what to do next and prioritized a freely rotatable object with only web references available, a bounded material trial replaced the visible procedural iris ribbons with a reference-guided, AI-assisted diffuse pigment texture on the existing curved 3D iris. The actual resin, geometry, lighting and final image remain Blender/Cycles. The generated texture is not a scan or a generated substitute for the final dish render. Full prompt, asset and provenance are retained.

**Method result: iris structure improved substantially. Whole-object photo gate: still FAIL.** Actual additional Cycles views at azimuth 135°/elevation 45° and azimuth 255°/elevation 28° confirm that the texture is attached to the object and specular response changes with viewpoint. This is not a camera-facing image.

Remaining cues, ranked: (1) clean line-art sclera veins and overly uniform body pigmentation, (2) regular procedural stone detail, (3) isolated food beads with excessive low-angle highlights and a pristine rim, (4) iris too dark/saturated compared with the reference, and (5) overly orderly finish and lighting gradients. The successful iris trial supports changing the remaining material-authoring method; it does not establish full photographic realism.

See `rotation_material_workflow.md` for the completed geometry cleanup, image provenance, checks, scope limits and proposed continuation.
