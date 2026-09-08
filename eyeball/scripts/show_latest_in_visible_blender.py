"""Append the historical round 06 study without discarding visible-session edits.

Run from the visible Blender Python Console after eye_06.blend is finished.
The previous scene remains in the scene selector, and both scenes are saved to
a separate review file. The original source files are not overwritten.
"""
import bpy
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
assert not bpy.app.background, 'This handoff must run in the visible application'
source = root / 'eye_06.blend'
assert source.is_file(), source
previous_scene = bpy.context.window.scene
previous_scene['review_preserved_from_file'] = bpy.data.filepath
previous_scene['review_preserved_before_switch'] = True
previous_scene.name = 'Previous model | preserved user session'
with bpy.data.libraries.load(str(source), link=False) as (available, loaded):
    loaded.scenes = available.scenes
new_scene = loaded.scenes[0]
new_scene.name = 'LATEST | Eye dish 06 | Cycles'
bpy.context.window.scene = new_scene
new_scene.cycles.preview_samples = 32
new_scene.cycles.use_preview_denoising = True
for screen in bpy.data.screens:
    for area in screen.areas:
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.region_3d.view_perspective = 'CAMERA'
                space.region_3d.view_camera_zoom = 45
                space.overlay.show_overlays = False
                space.shading.type = 'RENDERED'
review_path = root / 'eye_review_session.blend'
if bpy.context.area and bpy.context.area.type == 'CONSOLE':
    bpy.context.area.type = 'VIEW_3D'
# Saving a new review project also preserves any edits to the previous scene.
bpy.ops.wm.save_as_mainfile(filepath=str(review_path))
(root / 'reports' / 'visible_handoff.json').write_text(json.dumps({
    'background': bpy.app.background, 'filepath': bpy.data.filepath,
    'active_scene': new_scene.name, 'new_scene_objects': len(new_scene.objects),
    'preserved_scene': previous_scene.name, 'preserved_objects': len(previous_scene.objects),
    'scenes': [s.name for s in bpy.data.scenes],
}, indent=2))
print('VISIBLE_REVIEW_READY', str(review_path), 'PRESERVED_SCENE', previous_scene.name)
