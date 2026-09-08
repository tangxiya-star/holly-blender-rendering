# 1984 eye dish — analysis before geometry

Reference: `references/reference_eye.jpg`, 600 × 600 pixels, resolved from the user's new Google image share. The source photograph is by supertaster Mel: https://www.supertastermel.com/2022/07/copenhagen-alchemist-rasmus-munk.html . This is a different composition from the earlier pastry study. That study remains unchanged.

The source describes food served in the pupil of the eye: white asparagus cream, lumpfish roe, smoked lumpfish, caviar and cod-eye gel. Only the exposed upper food surface is modeled. The eye body's material is not established by the photo or caption; appearance is reconstructed without claiming its manufacturing recipe.

## Visible evidence and initial reconstruction decisions

| Aspect | Observation | Decision / uncertainty |
|---|---|---|
| Serving vessel | One convex eyeball-like vessel, about 470 px wide; a small dark contact base, no separate conventional plate | Estimate 140 mm width, about 100 mm height; absolute scale is unknown. Build a closed custom profile with a softly flattened contact base. |
| Silhouette | Broad rounded body, subtly asymmetric, iris integrated into its crown | A regular dome is intentional here, but avoid a stock sphere silhouette, faceting and sharp seam lines. |
| Iris | About 280 px wide (~60% body); gray-green/blue-gray with pale gold fibers and sparse brown marks | Outer radius ~42 mm; nonuniform radial fiber lengths, tangles, limbal softness and a dark scalloped collarette. |
| Central food | Dark insert about 106 px across (~23% body width), raised slightly above surrounding iris | Opening radius ~15.5 mm; thin irregular sidewall and crowded irregular amber/brown-black roe, not a smooth dark disk. |
| Layers | Pale outer body, buried-looking veins, fibrous iris, clear/wet surface, irregular dark pupil region, food opening and roe | Separate shallow layered surfaces and real occlusion. Hidden recipe layers need not be detailed. |
| Thickness | Pupil insert has visible but low wall; iris surface slopes away into dome | Avoid making the eye a stack of cylinders or concentric decorative rings. |
| Dry / wet | Stone is dry/rough. Body is smooth satin-to-gloss. Iris has a localized sharp wet reflection. Food has small wet glints | Use distinct Principled roughness distributions rather than uniform gloss. |
| Translucency | Veins and iris fibers appear beneath a surface; pale body has soft light response | A thin coat/clear shell over pigment and restrained scattering, rather than a thick glass eyeball. Exact material unknown. |
| Roughness | Broad quiet body reflection versus small bright iris highlight | Body ~0.23–0.38 initial roughness, iris wet layer ~0.10–0.20, variable roe membrane ~0.16–0.30; all tuned in Cycles. |
| Subsurface | Warm softness around illuminated outer body; food grains remain dark | Low millimetric body scatter as an appearance hypothesis; subtle roe transmission/SSS only. No waxy uniform glow. |
| Liquid | Roe looks close-packed and partially immersed; no external sauce pool or drips | Small local menisci between grains, no invented pouring or spill. |
| Microstructure | Radial iris fibers, sparse branching tiny veins, grain size variation, fine mottled stone | Prioritize coherent anatomical-looking structure over generic noise. Features finer than source pixels are plausible reconstruction, not recovered evidence. |
| Composition | Single eye fills about 78% width, displaced slightly downward; modest upper space | Square hero frame; entire body and its contact shadow visible. |
| Light | Warm/cream left illumination, violet right/back ambience; bright highlight below-left of pupil | Warm relatively small soft source plus purple fill and background wash. Avoid replacing the specific reference with a generic neutral studio scene. |
| Shadows | Strong dark contact and cast shadow on right/back, increasingly soft away from contact | Ground the vessel physically; use actual Cycles shadows, no painted shadow decal. |
| Camera | Iris apparent height/width suggests roughly 35–40° viewing elevation | Start 38° above table, ~85 mm lens as an estimate. Fit projected landmarks after first render. |
| Focus | Iris/food are relatively crisp; stone and far background soften | Physical DOF focused near pupil/iris transition. Start f/7.1, tune blur against reference. |

## Highest realism contributions

1. Correct body/iris/opening proportions and camera projection.
2. Coherent nonuniform radial iris structure and fine branching veins under the outer finish.
3. Layered wet reflections with believable depth, rather than a flat painted eye or solid glass ball.
4. Reference-specific warm/violet illumination, dark grounding, and physical focus falloff.
5. Densely packed natural food grains with varied size, immersion and highlights.

## Test protocol

Build one full-resolution Blender/Cycles study, no web optimization or external replacement render. Freeze the ingredient inventory after the first render. For each iteration, visually compare with the reference, rank five CGI cues, fix the top three, then render again. Complete at least two correction loops when the image still looks synthetic. Preserve the initial and corrected scenes and images. A successful build or high sample count is not a photographic pass. This reference largely tests a designed vessel, so even a convincing result cannot alone validate a general hero-food workflow.


## Supplemental blue-eye evidence supplied during review

The user rejected the early result as insufficiently realistic and supplied clearer images of a blue/cyan iris. The matching photograph is retained as `references/reference_blue_newyorker.jpg` (1600 × 2000), from https://media.newyorker.com/photos/66e995fe2651982b1f8d8ed3/master/w_1600%2Cc_limit/r44894.jpg . Its shorter interwoven pale fibers, dark crypt gaps, pink vascular transitions and deeply colored, partly submerged food are better resolved than in the first 600-pixel photograph.

The maker, 10 Tons, documents a 200 mm diameter and a multi-layer three-dimensional iris and sclera embedded in clear resin: https://www.10tons.dk/eyeball . This supersedes the initial 140 mm scale estimate and uncertain vessel material. The new construction retains the authored geometry coordinates then scales the scene by 10/7, with camera/light size and energy adjusted consistently.

The next pass uses the user's blue version as the intrinsic-material reference and a neutral right-side key with more restrained fill. The portrait camera follows the supplemental photograph more closely. The original purple-lit reference and every earlier render remain available for comparison. A successful eye-vessel recreation would still need separate evaluation on food-dominated hero dishes.
