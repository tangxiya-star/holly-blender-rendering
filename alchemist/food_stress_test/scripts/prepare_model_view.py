import bpy, math, json
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'food_final.blend'))
s=bpy.context.scene
for o in s.objects:o.select_set(False)
plate=bpy.data.objects.get('Support | handmade porcelain bowl')
if plate:
    plate.hide_set(False);plate.select_set(True);bpy.context.view_layer.objects.active=plate
for screen in bpy.data.screens:
    candidates=[a for a in screen.areas if a.type in {'VIEW_3D','IMAGE_EDITOR','CONSOLE'}]
    if not candidates:continue
    a=max(candidates,key=lambda a:a.width*a.height);a.type='VIEW_3D'
    space=a.spaces.active
    space.shading.type='MATERIAL';space.shading.use_scene_world=False;space.shading.use_scene_lights=False
    space.shading.studiolight_rotate_z=.4;space.shading.studiolight_background_alpha=0
    space.overlay.show_overlays=True;space.overlay.show_floor=False
    space.overlay.show_axis_x=False;space.overlay.show_axis_y=False
    space.clip_start=.001;space.clip_end=100
    region=space.region_3d;region.view_perspective='PERSP'
    region.view_location=(0,0,.045);region.view_distance=.33
    region.view_rotation=(Vector((.12,-.23,.17))-Vector((0,0,.045))).to_track_quat('Z','Y')
    space.lens=50
s['view_help']='3D model view: middle mouse orbit; wheel zoom; Shift+middle mouse pan. Editable source with material preview.'
target=ROOT/'food_model_view.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(target))
(ROOT/'reports'/'model_view_ready.json').write_text(json.dumps({'file':str(target),'view':'VIEW_3D','shading':'MATERIAL','camera_lock':False,'mesh_objects':sum(o.type=='MESH' for o in s.objects),'active_object':plate.name if plate else None},indent=2))
print('MODEL_VIEW_READY',str(target),flush=True)
