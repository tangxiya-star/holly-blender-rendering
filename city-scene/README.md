# City scenes — Copenhagen

Two editable Blender projects cover Copenhagen at different scales. Open each project guide for the latest scene, navigation, rebuild commands, and source attribution.

| Project | Latest scene after asset restoration | Contents |
|---|---|---|
| [Street neighborhood](street/README.md) | `street/copenhagen_neighborhood.blend` | Four connected fictional streets, 104 reference-based buildings, and a closed walking route |
| [City aerial](aerial/README.md) | `aerial/copenhagen_aerial_final.blend` | Real OSM layout with 81,774 building footprints, orthophoto textures, and an animated descent toward Nyhavn |

Both projects use Blender 5.2 or newer. Source code, project documentation, and reports are in Git; the large Blender files, renders, textures, references, and geographic datasets are in [Release v2026.09.08-projects](https://github.com/tangxiya-star/holly-blender-rendering/releases/tag/v2026.09.08-projects).

## Restore one project or both

From the repository root, with Python 3 and GitHub CLI (`gh`) installed:

```sh
# Street neighborhood only
python3 tools/restore_assets.py --archives city-street-assets.zip

# City aerial only
python3 tools/restore_assets.py --archives city-aerial-assets.zip

# Both city projects
python3 tools/restore_assets.py --archives city-street-assets.zip city-aerial-assets.zip
```

Each archive restores its original filenames beneath the corresponding project folder and includes the assets required by that project. The aerial archive includes its own HDRI, so it does not require the street archive. See the [repository README](../README.md) for download and verification details.

## Scope and sources

The street neighborhood uses a representative fictional plan and reference-based architecture. Its [reference analysis](street/references/reference_analysis.md) and [asset provenance](street/references/assets.md) distinguish modeling assumptions, material sources, and photographs used only for visual analysis.

The aerial project uses geographic data **© OpenStreetMap contributors, ODbL 1.0**, orthophoto imagery **© Klimadatastyrelsen / GeoDanmark, CC BY 4.0**, and a **CC0 Poly Haven** sky. Preserve the attribution and read the [geographic source notes](aerial/data/SOURCES.md) and [imagery source and service-use notes](aerial/reports/imagery_sources.md). Missing building heights and roof forms are estimated; the scene is an aerial visualization rather than a survey-grade digital twin.

The aerial animation provides a World Labs handoff camera, but the external World Labs environment or footage is not connected or included. The street and aerial projects are separate scene files, and the [aerial guide](aerial/README.md) explains the remaining compositing and visual limitations.
