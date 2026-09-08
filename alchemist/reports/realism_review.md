# Visual critique and corrections

## Representative renders reviewed

Phase 1: plan, entry and eye-level dining. Phase 2: hero, counter and entry. Phase 3: hero and counter, repeated after a chair-transform fix. Phase 4: dome and hero. Phase 5: hero, entry and exit. Phase 6: furnished hero and table. Phase 7–8: hero/table correction rounds plus entrance, dome, lounge and exit. Final: high-resolution hero and six station renders.

## Ten-question audit

1. **Toy-like?** Human scale and softened architectural silhouettes replace the earlier oversized torus/stage. Close inspection still reveals authored CG furniture and simplified secondary spaces.
2. **Low-poly?** No conspicuous low-poly dome or furniture facets in the final source views. Web simplification retains the principal curves and edge radii.
3. **Most artificial material?** Upholstery and entrance bronze lack the rich wear, grain and local imperfections of photographed objects. Textured PBR, restrained sheen and roughness reduce the flat appearance; they do not substitute for scanned materials.
4. **Most visibly CG geometry?** Repeated chairs and the interpreted bronze relief. Rounded back silhouettes improve the former; the latter is an original abstraction, not an exact copy of the photographed sculpture.
5. **Edges too sharp?** Stone, metal trim, cabinetry, door reveals and furniture have physical edge radii. Small props use thinner suitable radii.
6. **Lighting too flat?** Dining uses localized warm pools, cool dome contribution, dark transitions and a subdued service bay. The initial uniformly lit blockout is not the final lighting.
7. **Reflections believable?** Cycles traces glass, metal, stone and floor response. Oversized white reflected light disks found in review were corrected with narrow concealed sources. Web illumination is an approximation and requires the delivered HDR environment.
8. **Human scale?** Dining surface 0.78 m, seat top 0.52 m, eye height 1.65 m; room and circulation are meter-scaled.
9. **Environmental depth?** Entry, warm arrival, compressed corridor, dome dining, glazed service bay and exterior connector provide distinct depth layers.
10. **Reference quality?** Recognizable composition and theatrical atmosphere are achieved as a cinematic architectural visualization. It is not a measured or photographically exact reproduction. The actual venue's multi-level plan, complex bronze artwork and precise furniture are not fully reconstructed.

## Ranked five largest differences after the first furnished render

1. Excessively busy, crisp projection and a dark lower band.
2. Flat beige service backdrop instead of dark glazed depth and warm reflections.
3. Weak warm spill onto the polished stone; broad blue surfaces dominated.
4. Stone-block island bases instead of dark pedestal bases.
5. Rectangular chair backs compared with the more rounded photographed silhouettes.

## Corrections and second review

- Edited original projection artwork to five large organisms with quieter water and a quiet pole region; adjusted emitted luminance. Kept replaceable image UV mapping.
- Introduced tinted service glass, darkened the rear surfaces and layered structural worktop/rail reflections. Second review caught oversized source reflections; replaced them with narrow sources and concealed strip geometry, then rerendered.
- Broadened and warmed task-light cones, adjusted stone roughness while preserving variation, and added restrained coating response.
- Replaced island material blocks with thin stone slabs over dark bases.
- Rounded chair-back outlines and softened upholstery grazing response.
- Replaced the exit void with a restrained industrial street connector. Added bronze relief and masonry at the entrance, then corrected a lounge camera that initially looked through an open door leaf.

## Spatial/technical audit

The final walkthrough was sampled at all 1,441 frames: 60 seconds, approximately 46.47 m total travel, 0.25 m clearance radius, five ground probes. No sampled body collisions or unsupported floor probes remain. Two entrance-seam misses were fixed with a thin physical threshold bridge. The source validator's remaining informational review warning is generated entrance lettering: a FONT evaluated into mesh geometry at 4.65–4.77 m height, outside its mesh-only census and far above the walking route. See final_validation.json and instance_audit.json for evidence and ray-sampling limitations.

The street and arrival connections are inferred. Exact venue floor plan, stairs/lifts, backstage areas, humans, moving projection video and browser navigation/collision-controller implementation remain outside this asset package. Named targets, cameras, geometry and animation are delivered for integration.
