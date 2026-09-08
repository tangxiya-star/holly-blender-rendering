# Alchemist-inspired environment — design basis

No reference images accompanied the pasted brief. Five public photographs were acquired and visually inspected before scene construction. The previous `alchemist_dome.blend` is preserved outside this deliverable folder.

## Primary references

1. **Hero:** `references/reference_dome.jpg`, Claes Bech Poulsen / Vanity Fair. Blue underwater projection, restrained warm pools across stone, centered camera, dark lower architecture.
2. `references/reference_room_03.jpg`, Claus Troelsgaard / Dinesen. Clearest counter and chair arrangement, rear service glazing and floor response.
3. `references/entrance.jpg`, Dinesen. Tall bronze relief double doors, pale industrial masonry and shallow concrete threshold.

Supplementary: `reference_lounge_01.jpg` shows the balcony lounge, not the arrival room. `reference_lounge_02.jpg` shows oak grain, broad boards and restrained imperfections. See reference_sources.md for links and credits.

## Known / inferred / unknown

**Known from photographs:** rounded squared-U dining counters in paired rows; centerline rectangular service islands; slim individual arched task lamps; dark curved upholstered chairs; blue-gray mottled polished stone; dark cabinetry with small undercounter gaps; warm reflection through rear glazing; smooth continuous dome above a level rim; bronze entry relief; pale masonry; dark broad timber boards and gold finishes in balcony lounge. The Dinesen article describes an 18 m diameter dome.

**Inferred:** 0.78 m dining surfaces, 0.46 m seats, 1.65 m visitor eye height, 2.7 m dome rim and 8.4 m apex; four counter groups, 28 modeled seats; 9 x 7 m arrival room; 3.2 m wide transition; 3.2 x 4.2 m entry opening. Seating count and plan are modeling decisions, not claims about the venue.

**Unknown:** exact building survey, stair and lift arrangement, route lengths, backstage rooms, full entrance art, circulation between actual levels. This hackathon scene compresses the experience onto a single accessible plane. It does not claim to reproduce the real multi-level floor plan.

## Spatial sequence and detail allocation

Street threshold at Y -22 → bronze portal Y -19 → warm arrival Y -15.5 → dark connector Y -10.4 → main dining/dome at origin → hero table at (2.8, 1.75) → return along the same navigable route. Dome dining is one space. Main circulation runs beside central islands rather than through them.

High detail: entry doors, main dining stone and chairs, projection dome, hero table. Medium: arrival bar/lounge, transition reveals. Low: street connector and rear service silhouettes. No large invented secondary rooms or decorative filler.

## Phase 1 inspection

Reviewed plan, eye-level dining and entrance renders. The room is coherent, with an actual open entrance and connector. The paired U counters and central islands correspond to the reference composition. Table and seat scale are human-sized. Detected side-chair orientation error in helper; corrected before architecture. Simple blockout edge joints and floating lounge placeholder furniture are intentionally resolved in Phase 2. Saved complete blockout before refinement.

## Phase 2 inspection

Reviewed neutral hero, table and entry renders. Curved chairs, reachable counters, stanchions, door reveals and shadow service glazing hold up at eye level. Replaced lounge placeholders with supported furniture. Avoided multi-floor claims. Confirmed no need to enlarge the dining room or add more tables.

## Phase 3 inspection and correction

First material render exposed stale parent-transform evaluation when rebuilding chair upholstery. The seat/back meshes accumulated at the origin. Fixed the shared furniture attachment helper to update the dependency graph before preserving world matrices. Rerendered and visually confirmed the upholstery is correctly placed. Stone, steel, woven upholstery and timber remain materially distinct; textures use real image PBR inputs and are packed in the Blender source.
