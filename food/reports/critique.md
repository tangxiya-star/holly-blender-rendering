# Cycles realism critique and revision record

Reference: the exact user-supplied Eatweek Guide photograph. Assessment is visual at both full-frame viewing size and ingredient-detail scale. Ingredient inventory remains fixed throughout: two pastries with the visible topping layers and tiny flowers, moss, branch, white ceramic and stone surface.

## Round 01 — first full material render

`renders/food_01.png`, 1067 × 1600, Cycles Metal, 192 maximum samples, adaptive threshold 0.006; saved editable scene `food_01.blend`. Build 2.84 seconds; full build/render 155.47 seconds. The reference is not mapped onto geometry or used as a composited background.

**Verdict: clearly CGI; does not pass the one-second photographic plausibility test.**

Five strongest visible cues, ranked:

1. **Moss coverage and scale.** Thin isolated grass-like tufts sit on an exposed dark green sheet. The reference has a continuous, deep, finely branching carpet, with tips and gaps at several scales. This also makes the food look less grounded.
2. **Food surface hierarchy.** Broad pale ochre relief reads as sculpted clay/foam. The reference has a golden toasted skin with smaller brittle blisters, darker pores and powder. The ivory collar is too chalky and too roughly embossed. The sloping shoulder reads somewhat pear-shaped.
3. **Stone texture.** Regular cellular/Voronoi boundaries look like embossed tiles. The photograph has irregular worn stone, pits and discontinuous clefts, with a few large seams rather than an all-over cell network.
4. **Roe packing and response.** Bright reflections exist, but too many similarly exposed, smoothly rounded chocolate-brown beads read as a manufactured scatter. Reference roe is darker, more closely crowded, more varied and locally wet.
5. **Plate and branch finish.** The plate reads as a thin saucer rather than a bowl with a broad curved white front wall. The log end has a conspicuous radial rosette; yellow lichen looks scattered rather than a connected broken crust.

### First correction loop

- Replace sparse moss with dense overlapping curled-leaf structure and uneven cushions; reshape the existing ceramic wall to establish believable depth/contact.
- Reduce broad crust relief, introduce finer clustered baked blisters and toasted color contrast, broaden the pastry shoulders, quiet and warm the ivory cut layer. Adjust existing roe color, packing and membrane roughness as part of the food-surface correction.
- Remove the stone's cellular pattern in favor of irregular pitting and broken fissures. The existing branch is refined without adding ingredients.

Camera and lighting are held stable for the next comparison so these surface changes can be assessed. A second critique gate will decide further fixes to framing, focus, highlight size and remaining detail.

## Round 02 — first corrected Cycles render

`renders/food_02.png`, 1067 × 1600, Cycles Metal, 224 maximum samples, same camera and lighting. Full build/render 23.93 seconds with the GPU already initialized. Dense moss coverage, noncellular stone and darker more crowded roe are improvements. **Verdict: still clearly CGI.**

Five strongest remaining cues:

1. **Visible geometry error:** orange crumb rings encircle both bun bases. Inspection found a loop variable reusing the pastry height parameter, collapsing most blister and powder placement onto the bottom plane. This also explains the missing fine detail on the actual pastry shoulder. It must be corrected in geometry, not hidden with framing or compositing.
2. **Glossy spherical shell:** without its correctly placed fine detail, the broad shell reads as polished orange skin. It is too tall/full relative to the photograph's squat pastry. Broad highlights are too dominant.
3. **Moss height uniformity:** coverage is fixed, but the result resembles clipped turf. The reference has curved branching cushions, dark valleys and variable exposed heights.
4. **Repeated roe highlights:** color and density are closer, but round similarly exposed grains with repeated small reflections still read as beadwork. More of the wet contact response and natural shape variation needs to survive.
5. **Camera and overlap:** the front caviar and plate are too low while the rear caviar is close to the correct image height. The rendered front topping ellipse is approximately 0.58 high/wide versus about 0.50 in the photo, supporting a lower camera angle rather than a uniform image shift.

### Second correction loop

- Fix the height-variable collision and verify blister/powder heights. Reduce pastry body height slightly while keeping its base grounded and lowering its existing topping stack consistently; retain its ingredients.
- Give the dense moss a 4–7 mm varying cushion structure and curved longer fronds. Add sparse real shallow scars to the stone, preserving the corrected noncellular material.
- Lower the camera elevation from 32° to 27° and adjust framing target from 45 mm to 38 mm above the plate origin. These are working fit parameters, not claimed source EXIF. Lighting remains stable until the corrected geometry is visible.

## Round 03 — second corrected Cycles render

`renders/food_03.png`, 1067 × 1600, Cycles Metal, 256 maximum samples. Geometry-placement assertions passed; the collapsed detail rings are gone. Moss has depth, the pastry is shorter, and the camera/plate framing is substantially closer to the photograph. **Verdict: materially improved, but still visibly CGI.**

Five remaining cues:

1. **Crust response:** broad glossy patches and isolated small bumps still resemble orange skin. Reference crust is mostly covered in finer brittle blistering with broken dry highlights. The green shoulder powder is too weak.
2. **Roe and flowers:** dark crowded roe is closer, but repeated tiny highlights and disconnected bead-like contacts remain. Petal silhouettes are too regular and thick.
3. **Moss repetition:** the dense carpet has volume, but repeated directional fronds and a narrow leaf-size range make some regions look combed.
4. **Lighting and grounding:** the reference casts a deeper, longer shadow in front of/below the plate. The current frontal key gives a large smooth bun highlight and a short plate shadow. The background/table boundary is also too shallow and visually clean.
5. **Branch and plate regularity:** the cut face, lichen islands and pristine ceramic remain more regular than the photograph. They are now lower priorities than the hero food.

### Third focused correction loop

- Increase shallow irregular baked-cell coverage, raise dry crust roughness, and make powder visibly particulate over a wider, patchier shoulder area. Preserve food placements and dimensions. Add sparse wet contacts between existing roe and less regular folded petal outlines.
- Shift the key toward rear-left, make its reflection shape less dot-like, and use a restrained frontal fill for legibility. Keep neutral highlights and let the food carry its own warm color. Adjust the physical tabletop's rear-edge slope to the reference.
- Break directional repetition in the existing moss with azimuth and regional size variation. No ingredients are introduced.

## Round 04 — third corrected Cycles render

`renders/food_04.png`, 1067 × 1600, Cycles Metal, 256 maximum samples, build/render 23.86 seconds. The baked detail no longer collapses, powder is visible, roe highlights vary more, and the plate has a longer grounding shadow. **Verdict: the scene remains a visibly computer-generated recreation and does not pass the requested one-second photograph test.**

Remaining five cues, ranked:

1. **Bun regularity:** a near-spherical outline, continuous pebbled skin and broad green upper region resemble textured green-orange solids. Reference crust has less uniform brittle structure and more irregular powder coverage.
2. **Moss:** dense but still compressed and repetitive at fine scales, with more glossy leaf-carpet character than the reference's branching cushions.
3. **Branch:** the clean circular cut end and cylindrical body remain too regular; lichen still forms comparatively flat separated islands.
4. **Small garnish and roe:** wetness improved, but flowers still have repeated tidy silhouettes and many grains retain similarly exposed reflections.
5. **Ceramic and stone:** clean wall/profile and relatively smooth tabletop lack some of the photographed object's surface irregularity and large worn clefts.

### Final bounded correction and high-resolution evaluation

Reduce the broad green deposit by about 40–50%, preserve discrete powder, vary baked-cell coverage in larger irregular patches, and add small distinct outline/shoulder asymmetries to the two buns. These address the strongest remaining hero-food cue. Render at 1600 × 2399 and 512 maximum Cycles samples for final inspection. Higher resolution is for assessment, not a claim that sampling alone makes the image photographic.

## Final high-resolution assessment

`renders/food_final.png` and `food_final.blend`: 1600 × 2399, Cycles Metal, 512 maximum samples with adaptive sampling and denoising; build/render 66.33 seconds. The source contains 65 objects, 2,554,037 mesh vertices, 2,210,876 base mesh faces and 37 materials. A floating-point linear EXR is also retained. These are technical records, not realism scores.

The final image was visually inspected after rendering. The broad green coating is less uniform, the two bodies differ subtly in outline, baked-cell coverage is less even, and wet roe is more convincing than the first pass. Four correction passes followed the initial render; no ingredients were added after the first full composition.

**Stress-test outcome: FAIL against the strict one-second photographic criterion.** It is a coherent detailed CG reconstruction, but I would not represent it as indistinguishable from the supplied food photograph or approve this procedural-only result for a hero dish on that basis.

The final five remaining cues are (1) still-regular bun volume and artificial-looking blister distribution, (2) compressed repetitive moss microstructure, (3) clean cylindrical branch and separated lichen islands, (4) overly tidy blossoms and some repeated roe reflections, and (5) ceramic/stone surfaces that remain more even than the reference. The first three dominate the result. The source reference's particularly convincing brittle crust and tangled moss were not fully reproduced.

The useful outcome is an editable, reproducible material/geometry test and documented failure evidence before committing the restaurant's hero-food workflow. No web optimization was performed. This assessment is deliberately separate from successful file generation and Cycles execution.
