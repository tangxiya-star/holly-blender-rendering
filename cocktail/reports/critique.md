# Antini — Cycles realism iterations

All images in this folder are rendered in Blender Cycles through Blender MCP.
No AI image generation, web baking, GLB conversion or retouching was used.
The scene contains one modeled cocktail. No props were added after the first render.
The source Alchemist photo controls the coupe, pale green liquid and ant; the user
brief controls the dark photographic setting. Dimensions are inferred.

## 01 — first render, 1000 × 1250, 384 samples

Why does this still look like CGI? Ranked visible problems:
1. Several hard rectangular source reflections compete across the rim and bowl.
2. The liquid presents as a green surface above an apparently empty, dark cavity.
3. The reference-defining ant is out of focus and its anatomy is unreadable.
4. The uniformly bright blue-gray table looks more like a studio sweep than dark stone.
5. The straight dry upper band and repeated highlights make the lip look heavy.

Top-three correction: narrow/reposition source lights, aim a return behind the drink,
and move true lens focus to the front ant with f/16. Also dim stone and bronze.
Glass is watertight, 0.85 mm at the lip, with a continuous solid stem and foot. Liquid
is a separate watertight 143 ml volume following the inner bowl, not a colored cylinder.
The glass/liquid interface uses relative IOR; clear side boundaries avoid duplicate
refraction. No ice, consistent with the reference.

## 02 — focus improved; lighting too dark

1. Liquid still reads empty against black transmitted surroundings.
2. Repeated rectangular reflections persist on the upper band.
3. Stem disappears into black, weakening scale and continuous silhouette.
4. Table remains brighter than the important bowl.
5. Ant is now focused but lacks enough light to read its brown cuticle.

Corrections: feather actual emitter radiance with a Gaussian node mask, restore a
rear source, and add faint illumination on the distant backdrop. No objects added.

## 03 — rejected lighting balance

1. The rear source forms an oversized white crescent refracted in the lower bowl.
2. Upper rim still catches overly literal source shapes.
3. A background/table transition cuts across the composition.
4. Liquid depth remains hard to read.
5. The background arc competes with the glass silhouette.

Corrections: redirect the existing rear source onto stone behind the drink, extend
the existing table and move the existing background farther away, raise the camera
to a 21-degree elevation similar to the reference's visible liquid ellipse. Suppress
the arc and tune absorption. No added objects or props.

## 04 — continuous photographic field

1. The body of the liquid remains too dark to demonstrate optical depth.
2. Ant cuticle is underlit against the dark body.
3. The liquid surface is too strongly green relative to the rest of the liquid.
4. The right source remains a conspicuous upright patch.
5. Lower stem/foot focus is softer than ideal for the complete product portrait.

Corrections for 05: lower absorption to 3.8/m, use trace physically based botanical
infusion scattering (1.4/m), and enlarge/lower-radiance the existing front return.
Ant cuticle is slightly warmer/brighter. No props added.

## 05 — volume present, transparency compromised

1. Trace scattering makes the drink too cloudy compared with the clear reference.
2. The central dark curved region still separates from the bright top surface.
3. A hard right-side source border remains visible.
4. Ant is small and dark at the overview size, though focused.
5. Stem/base remain very uniformly polished and somewhat soft in the overview.

The visible volume in 05 is an improvement, but increased scattering is not the
right primary solution. Corrective priorities: place a real luminous return behind
the drink, reduce scattering to .25/m, and use exactly zero-edged source masks.

## 06 — return background is in the wrong height range

1. A bright background halo is visible directly behind the glass but the body is dark.
2. The table/backdrop join is now obvious.
3. Top-surface olive tint remains stronger than the reference.
4. The right side has a hot reflection.
5. Ant body contours are still somewhat rigid at close inspection.

Independent meridional Snell-law tracing found that the front bowl sends transmitted
rays upward by approximately 4–29 degrees after exiting its rear wall. The initial
return placement followed the direct camera rays, which was the wrong direction.
Move the EXISTING backdrop to y=.8 m and center its broad luminous pool at z=.32 m;
this allows the body to see a pale return while the camera predominantly sees dark
stone. Lower scatter to .08/m and absorption to 2.4/m; reduce the right source and
smooth existing ant body meshes. All are modifications to existing objects.
