# Food realism stress test — reference analysis before modeling

Authority: the exact photograph supplied by the user, saved as `references/reference_dish.jpg` (1067 × 1600). It controls silhouette, arrangement, visible surface response, light and framing. No synthetic replacement of the photograph is used. The test is one plated composition containing the two pastry pieces visible in the reference.

## Observations and bounded estimates

| Aspect | What is visible | Reconstruction consequence |
|---|---|---|
| Plate | Small ivory-white shallow ceramic dish, thick softly rolled front rim, slight unevenness, very dark shadow below | Model a continuous glazed profile and foot/contact; use 170 mm diameter as an unverified scale assumption |
| Main silhouette | Two squat golden choux-like rounds; front piece dominates, rear piece is left and occluded; shoulders are uneven and bases slightly compressed | Broad asymmetry and a baked shell rather than a sphere; front width about 0.41 of plate diameter |
| Crust | Blistered, pitted golden skin with paler ridges, darker shallow creases and a low horizontal baking crease | Geometry at 0.5–2 mm scale, finer bump below that, correlated browning and roughness |
| Thickness | Bun outline and topping edges vary; the cut ivory layer is relatively regular but its edge is not mathematically exact | Preserve intentional cut geometry while adding small edge variation and fine pores |
| Layers | Golden shell, narrow amber/brown collar, thick ivory cut disc, thin green/dark leaf-like perimeter, mound of dark roe; minute white flowers and magenta/burgundy tips | Separate overlapping layers with real contact; no extra ingredients |
| Dry versus wet | Crust is broadly dry with restrained sheen; roe has many small bright highlights; moss has scattered wet glints; cream is soft satin | Distinct roughness distributions, never one uniformly glossy food shader |
| Translucency | Roe reads deep brown/olive at lit edges, mostly almost black; petals are thin; cream is opaque but softly scattering | Restrained brown transmission/SSS in eggs, subtle thin petal response, millimetric cream scatter |
| Liquid behavior | No sauce puddle or poured liquid is visible. Moisture is local, especially on roe | Avoid invented drips/pools and thick clearcoat covering the pastry |
| Micro detail | Dense tiny crust pores, powder specks, fine moss leaflets, broken lichen flakes, rough bark | Detail must change silhouette or catch light at its own scale; avoid uniform noise over everything |
| Branch | Dark brown irregular branch lies along the right, receding toward upper left; front cut face visible. Chartreuse/yellow lichen forms discontinuous crust on upper bark | Custom loft, cut end and bark; irregular thin patches with exposed dark gaps |
| Plating | Moss fills the bowl and surrounds/supports the pastries; branch rests in it; front ceramic lip remains visible | Contact and compression are critical; avoid floating pieces or equally spaced decorative scatter |
| Light | Bright upper-left/front-left source; right-facing sides darker; small bright roe highlights, broad softer plate reflection; deep grounded shadows | One modest softbox near upper left, restrained fill and black surroundings; keep exposure on food |
| Shadow softness | Plate casts a strong near-contact shadow with a progressively softer edge. Fine roe occlusion remains deep | Real Cycles path tracing, appropriate source angular size and close physical contacts |
| View | Approx. 30–35 degrees above the surface, compressed perspective, plate cropped loosely inside frame | Portrait 2:3 camera, initial 85–90 mm full-frame equivalent; refine by projected landmarks |
| Focus | Front roe and pastry carry detail, rear pastry noticeably softer, foreground stone gradually loses definition | Physical camera DOF, focus at front topping; aperture estimated by rendered blur, not asserted as EXIF |
| Composition | Black upper area about 29% of image. Plate and food sit below center; tabletop crosses background obliquely | Match negative space and the direction of table boundary; no restaurant clutter |

The photograph alone cannot establish exact ingredient identities, recipe, absolute dimensions, hidden construction, or focal length. Descriptive object labels are visual interpretations, not culinary identification.

## Realism priorities, ranked before the first render

1. **Material separation at real scales:** dry baked crust versus wet dark roe, satin ivory filling, glazed ceramic and fine moist moss. Wrong size or strength of highlights immediately reads as plastic.
2. **Contact and silhouette:** squat irregular shell, credible topping support, closely packed roe with small occluded gaps, weight resting on moss.
3. **Baked microstructure:** irregular blister/porosity and natural browning, not a smooth yellow bun with generic noise.
4. **Photographic light and focus:** one plausible source, dark rich occlusion, rear piece optically softer; no uniform fill or fake blur mask.
5. **Supporting scale cues:** small flower petals, discontinuous green powder and lichen, fine moss rather than grass spikes, softened real ceramic thickness.

## Evaluation protocol

Render 01 is a Cycles material evaluation, not a viewport judgment. Freeze the ingredient inventory. Compare directly with the supplied photograph; rank five strongest CGI cues. Change the top three causes and render again. Repeat a second critique/fix/render cycle if remaining cues require it. Preserve all rounds and critique notes. The final one-second photographic plausibility judgment remains visual and subjective; do not substitute a polygon count or sampling number for success.
