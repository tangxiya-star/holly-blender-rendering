import bpy, sys, math, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

assert bpy.context.scene.name.startswith('Copenhagen')
s=bpy.context.scene
from context_finish import finish_context
finish_context()
from corner_returns import build_corner_returns
build_corner_returns()
from photo_surfaces import apply_photo_surfaces
apply_photo_surfaces()
# Align the exterior approach with the generated bakery threshold.
bpy.context.view_layer.update()
entry=bpy.data.objects.get('Entrance_Hero_-1_1_04')
if entry:
    bpy.data.objects['POI_Bakery'].location=entry.matrix_world.translation
    cam=bpy.data.objects['04 | Bakery approach'];cam.location=(-4.2,13,1.77)
    aim(cam,(-9,20.3,2.3));cam.data.lens=32
for target,source in [('POI_Gallery','Entrance_Cross_52_1_-80_04'),('POI_Courtyard','Entrance_Hero_1_1_05')]:
    marker=bpy.data.objects.get(source)
    if marker:bpy.data.objects[target].location=marker.matrix_world.translation
# Destination markers resolve to actual local shop thresholds generated in each parcel.
for o in bpy.data.collections['POI_Targets'].objects:
    o['phase']='Exterior approach prepared; destination interior to be authored separately'
s['navigation']='Choose a named camera in Scene properties. In the 3D View press Shift+` for Walk Navigation: WASD, mouse look; wheel adjusts speed.'
s['quality_review']='See reports/realism_review.md for ranked first-pass issues and corrections.'
s['build_version']='Copenhagen reference-driven street prototype, reviewed second pass'
# Opening this file starts in a useful eye-level material view.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.region_3d.view_perspective='CAMERA'
            space.overlay.show_overlays=False;space.clip_end=600;space.lens=32
            space.shading.type='MATERIAL';space.shading.use_scene_world=True;space.shading.use_scene_lights=True
            space.region_3d.view_camera_zoom=0
s.camera=bpy.data.objects['01 | Human eye street']
s.cycles.preview_samples=16
s.render.resolution_x=1600;s.render.resolution_y=1067;s.cycles.samples=64
save('copenhagen_final.blend')
render('01 | Human eye street','copenhagen_street.png',1600,64)
render('04 | Bakery approach','copenhagen_bakery.png',1400,64)
render('02 | Walking perspective','copenhagen_walking.png',1400,48)
render('03 | Establishing','copenhagen_establishing.png',1400,48)
render('05 | Cross street','copenhagen_cross_street.png',1400,48)
s.camera=bpy.data.objects['01 | Human eye street'];s.frame_set(1)
save('copenhagen_final.blend')
