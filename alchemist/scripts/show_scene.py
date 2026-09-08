import bpy,json
from pathlib import Path
s=bpy.context.scene
s.camera=bpy.data.objects.get('CAM_Hero') or s.camera
s.cycles.preview_samples=12
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.region_3d.view_perspective='CAMERA'
            space.region_3d.view_camera_zoom=0
            space.overlay.show_overlays=False
            space.shading.type='RENDERED'
            space.shading.use_scene_world=True
            space.shading.use_scene_lights=True
Path(__file__).resolve().parents[1].joinpath('reports/gui_opened.json').write_text(json.dumps({'file':bpy.data.filepath,'camera':s.camera.name,'windows':len(bpy.context.window_manager.windows),'view':'rendered camera'},indent=2))
