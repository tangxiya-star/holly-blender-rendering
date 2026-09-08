# Initial aerial realism review

Reviewed `renders/hero_initial.png` at its full 1440 × 810 resolution, using the reduce-ai-image-look diagnostic order: physical/spatial plausibility, camera, light, materials, then finishing. This is a review of the Blender render, not a proposed image-generation replacement.

The geographic footprint density and overall composition already read as a large city. Photographic realism does not pass yet: the strongest problems are the visible boundary of the detailed city, cyan lighting, missing inland water from the old context layer, and excessively white water reflection.

## Five largest visible CGI cues

| Priority | Visible cue and location | Cause | Smallest useful correction |
| --- | --- | --- | --- |
| 1 | The dense city ends abruptly along conspicuously straight edges across the upper third. A nearly featureless surface continues beyond it. | The camera sees beyond the detailed geographic extract. The original hero is pitched down only about 21°, so the top of the frame reaches roughly 20 km away. | Use the proposed hero `(4400, -3900, 3300)` aimed at `(550, 900, 0)`, 48 mm. This retains a high city view while steepening the downward angle and keeping the visible ground within the detailed city. Do not manufacture a ring of arbitrary additional city blocks. |
| 2 | Almost every roof, façade, road, and water surface shares a pale cyan cast. Near and far neighborhoods have similarly weak shadow separation, giving the appearance of a blue architectural model. | Environment radiance and blue volume scattering overwhelm the material palette; the large sun angle further softens shape. | The proposed neutral overcast HDRI at strength 0.55, neutral sun at energy 2.6 and angle 1.4°, and haze density reduction from 0.000037 to 0.000017 are appropriate first corrections. Preserve a mild increase of haze with distance; do not add uniform blur or grain to hide the issue. |
| 3 | The lake chain behind the historic center is pale/land-colored instead of reading as connected blue water bodies. Smaller inland canal regions also lose geographic clarity. | Known initial-scene bug: the original context land lies underneath the detailed land's holes but above the water plane, filling the lakes visually. | Replace context land with the updated `data/context_geography.json`. Its entire core rectangle is removed, and its intersection with the core interior was verified as exactly 0 m². Keep the core land and water geometry unchanged. |
| 4 | A bright white, angular reflection band follows the harbor and canals near the center. It pulls attention away from the city and looks like a graphics overlay. | The initial scene has overlapping ocean and water-polygon surfaces with different elevations. Root inspection identified this inconsistent water layering as the first cause to correct; concentrated sun reflection is also visually dominant and nearly clipped. | Remove the redundant water-polygon overlay and let a single physical water surface show through the real GIS holes. Reassess after the environment change; only if glare remains, raise water roughness to roughly 0.32–0.36, set Metallic to 0, and retain IOR 1.333 and directional small-wave normals. |
| 5 | Foreground and middle-distance neighborhoods are very clean, pale extrusions with weak separation between streets, façades, and roof types. Large paved areas also share one uninterrupted mineral response. | The first render largely hides the intended material hierarchy; broad surfaces and roofs have limited readable variation after the cyan lighting wash. This is a material/readability issue more than a missing-building issue. | First inspect the same scene under the corrected neutral lighting. If necessary, modestly deepen asphalt and flat-roof values, recover restrained terracotta/copper/slate distinctions, and add low-amplitude roughness variation at block/building scale. Preserve the real footprint density and heights where mapped. Defer additional geometry until this lighting/material pass is assessed. |

## Geographic sanity check

The major land/water relationships agree with the GIS diagnostic map: Amager occupies the foreground/right, the historic city lies beyond the diagonal inner harbor, Christianshavn's island and canal structure sit on the near side of that harbor, and harbor docks extend to the right. Street orientations and closed urban blocks agree with the real footprint extract. The sharp end of visible building density is an extract/camera artifact, not a real coastline.

The exception visible in this initial scene is the known inland-water infill. The source GIS is correct: all six fixed checks in `data/harbour_control_points.json` pass, including Nyhavn water at local `(1409.188, 409.658)` and Christianshavns Kanal water at `(1414.103, -408.678)`. Individual narrow Nyhavn quays cannot be independently verified at this render's scale; the local diagnostic map provides that verification.

## QC decision

- Composition/spatial scale: usable; crop needs correction to conceal the extract boundary.
- Geographic geometry: passes at macro scale, except the known old context-layer overlap.
- Focus hierarchy: weak; white water and the city boundary compete with the historic center.
- Motivated light: does not pass yet; neutral lighting and thinner haze are the next iteration.
- Materials: usable geometry but weak photographic separation under the initial light.
- Color response: does not pass yet; global cyan wash is excessive.
- Anatomy/performance: not applicable to this altitude and subject.

Recommended next iteration: render the tighter hero with corrected context land and neutral environment first. Judge roof/terrain richness in that render before committing to further massing or vegetation work. The existing 81,774 real footprints provide sufficient macro density; additional arbitrary buildings would reduce geographic fidelity.
