# Copenhagen aerial — final realism review

Reviewed the latest `hero_aerial.png` and `nyhavn_handoff.png` after `final_grade.log` recorded their new saves, and compared them with the initial and first orthophoto-pass renders. Earlier review also covered the harbor and descent compositions. This review reflects the final local-atlas/grade pass rather than the older images with the same filenames.

**Assessment:** The result is a geographically grounded, large-scale Copenhagen aerial visualization and camera-handoff asset. City structure and local texture clarity are substantially improved. It still visibly reads as CGI/urban massing rather than a photograph; the Nyhavn handoff is not a finished photographic street environment.

## Five completed fixes verified

| Change | Verified result | Practical limit |
| --- | --- | --- |
| Tighter, more downward-facing hero camera | The detailed city now fills almost the entire frame. The conspicuous straight city cutoff from the initial image is greatly reduced. | The scene remains a finite geographic extract; an unrestricted camera can still expose its limits. |
| Neutral environment and revised haze/light | The strong initial cyan veil is largely gone. Roof, façade, street, and greenery colors separate more clearly. | Overall gray/brown massing and reflective water still prevent a fully photographic appearance. |
| Context-land cutout and one physical water surface | The surrounding context no longer fills the core's inland-water holes, and the duplicate water-polygon layer is removed. Source GIS checks remain valid. | Bright lake/harbor appearance remains after those geometry corrections; it must not be reported as fully solved. |
| Real 8192 × 8192 GeoDanmark orthophoto atlas | Roofs and ground now use actual Copenhagen color/land-cover information, with appropriate geographic mapping and retained attribution. | At about 1.46 × 1.49 m per texel, this citywide atlas is intended for high aerial viewing. |
| Dedicated 2048 × 2048 Nyhavn atlas | The latest handoff shows visibly sharper roofs and quay surfaces than the prior cloudy/blurry version. The local 750 × 750 m patch samples at about 0.366 m per texel. | Higher-resolution overhead imagery does not supply missing façade geometry or make the scene a complete street-level reconstruction. |

## Five remaining visible CGI cues

| Cue | Evidence in the reviewed images | Appropriate future correction |
| --- | --- | --- |
| Generic façade massing and repeated windows | The high views show clean beige/white extruded wall planes; the handoff exposes very regular dark window grids and broad unarticulated façades. | Keep the current asset focused on high aerial use. For a closer shot, replace the visible Nyhavn frontage with distinct façade assets, correct ground floors, opening proportions, cornices, and material variation. |
| Very bright, flat-looking lake/harbor reflection | The lake chain remains almost white compared with the dark-green harbor, even after the final roughness/specular adjustment. | Revisit the reflected HDRI region and water response in a targeted lighting test. Preserve a plausible glint while reducing the large white patch; another global exposure shift would also darken the already restrained city. |
| Projected photography does not fully match the roof geometry | The sharper local image reveals captured shadows and roof details lying across estimated roof planes. Some close surfaces still read as imagery laid over simple solids. | Match local roof forms to their photographs and use imagery appropriate to those forms. Align scene lighting with the source's shadow direction or reduce baked-shadow influence; the orthophoto is a lit image, not neutral albedo. |
| Simplified and repeated near-camera vegetation | The descent views expose oval, low-detail canopy shapes and a limited range of tree silhouettes. | Retain lightweight instances at city scale, but use a small varied set of realistic crowns near the actual camera route, positioned and sized to the local imagery. Increasing the whole city's tree count is unnecessary. |
| Sparse close-range quay and canal detail | The handoff's quay edges and water lack much of the moored-vessel, railing, mast, furniture, and incidental activity visible in the source orthophoto. | If the handoff must read as a real place at lower altitude, add only the recognizable local quay/vessel structures and necessary close-camera detail. Keep the transition higher until those assets exist. |

## Geographic sanity check

The inner-harbor diagonal, Christianshavn island/canal organization, historic city beyond it, northwest lake chain, and eastern harbor docks agree with the prepared GIS and the north-up GeoDanmark atlas. The six fixed source land/water checks pass, including Nyhavn and Christianshavns Kanal. The remaining white-water issue is now a rendered appearance problem rather than a justification for altering the real coastline.

The scene has real footprint positions and shoreline geometry. Estimated heights, generic roofs, simplified landmark accents, and façade patterns are not surveyed architectural accuracy. Imagery and OSM may also reflect different capture/edit dates.

## Delivery limits and QC decision

Suitable now for editable city-scale visualization, aerial camera planning, and a transition asset. Camera composition and macro geographic layout pass for that purpose. Photographic materials, faithful close façades, near-ground street detail, and close-range scene richness do not yet pass.

The camera metadata defines a 180 m handoff altitude, but no external World Labs world or footage is connected. A transition camera is not a completed external-world integration.

GeoDanmark/Klimadatastyrelsen CC BY 4.0 attribution and Septima's private/evaluation service-access statement are recorded in `imagery_sources.md`. The imagery retains source markings. The delivered Blender file should be described as a real-layout aerial scene with photographic roof/ground textures, with the remaining CGI and external-handoff limits stated plainly.
