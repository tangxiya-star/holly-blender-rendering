import bpy, sys, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from neighborhood_architecture import build_neighborhood_architecture
from neighborhood_surfaces import build_neighborhood_surfaces
from neighborhood_navigation import build_neighborhood_navigation
from photo_surfaces import apply_photo_surfaces

assert bpy.context.scene.name.startswith('Copenhagen')
s=bpy.context.scene;s.name='Copenhagen | FOUR CONNECTED STREETS'
architecture_report=build_neighborhood_architecture()
surface_report=build_neighborhood_surfaces()
nav_report=build_neighborhood_navigation()
apply_photo_surfaces()
s.camera=bpy.data.objects['08 | FOUR STREETS - overview']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.region_3d.view_perspective='CAMERA'
            space.region_3d.view_camera_zoom=8;space.overlay.show_overlays=False
            space.shading.type='MATERIAL';space.shading.use_scene_world=True;space.shading.use_scene_lights=True
save('copenhagen_neighborhood.blend')
render('08 | FOUR STREETS - overview','neighborhood_overview.png',1500,40)
render('09 | North street - eastbound','neighborhood_north_street.png',1400,48)
render('10 | East street - southbound','neighborhood_east_street.png',1400,48)
render('11 | South street - westbound','neighborhood_south_street.png',1400,48)
render('12 | TURN HERE - north intersection','neighborhood_turn.png',1400,48)
s.camera=bpy.data.objects['08 | FOUR STREETS - overview'];s.frame_set(1)
save('copenhagen_neighborhood.blend')
(ROOT/'reports'/'neighborhood_build.json').write_text(json.dumps({'architecture':architecture_report,'surfaces':surface_report,'navigation':nav_report},indent=2))
