import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'alchemist_04d_polished.blend'))
s=bpy.context.scene
# A discreet physical under-shelf strip is visible through the tinted service glass.
e=mat('PBR | concealed warm service strip',(.25,.1,.035),.5)
p=e.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.46,.15,1);p.inputs['Emission Strength'].default_value=3
for x in [-2.7,-.9,.9,2.7]:
    o=box('Service_Concealed_Strip',(x,9.8,1.67),(1.4,.025,.016),'Lighting',e,.002);o.parent=bpy.data.objects['Lighting']
cam=bpy.data.objects['CAM_Lounge'];cam.location=(2.6,-16.8,1.6);cam.data.lens=25;aim(cam,(-2.8,-14.7,1.6))
s.camera=bpy.data.objects['CAM_Hero'];s.frame_set(1)
s.render.resolution_x=1800;s.render.resolution_y=1012;s.render.resolution_percentage=100;s.cycles.samples=128
s.render.filepath=str(ROOT/'renders'/'alchemist_hero.png')
s['design_basis']='Alchemist-inspired, photograph-guided, inferred single-level layout. See reports/design_basis.md.'
s['walkthrough']='WALKTHROUGH camera, frames 1-1441 at 24 fps, 60 seconds. Main aisle radius tested at 0.25 m.'
s['projection']='Original generated image; replace material PROJECTION | replace this image > REPLACEABLE_PROJECTION.'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.overlay.show_overlays=False
            area.spaces.active.shading.type='MATERIAL'
            area.spaces.active.shading.use_scene_world=True
            area.spaces.active.shading.use_scene_lights=True
bpy.ops.file.pack_all();save('alchemist_05_final.blend')
render('CAM_Hero','alchemist_hero.png',1800,128,.5625)
render('CAM_Table','alchemist_table.png',1280,64,.625)
render('CAM_Arrival','alchemist_arrival.png',1280,48,.625)
render('CAM_Dome','alchemist_dome.png',1400,64,.5625)
render('CAM_Exit','alchemist_exit.png',1100,40,.625)
render('CAM_Lounge','alchemist_lounge.png',1100,40,.625)
# HDR light/reflection capture for the web's image-based lighting.
env=camera('TEMP_Environment_Capture',(1.2,.9,1.6),(1.2,-5,1.6),25)
env.data.type='PANO';env.data.panorama_type='EQUIRECTANGULAR';s.camera=env
s.render.resolution_x=1024;s.render.resolution_y=512;s.cycles.samples=48
s.render.image_settings.file_format='OPEN_EXR';s.render.image_settings.color_depth='16'
s.render.filepath=str(ROOT/'textures'/'restaurant_environment.exr');bpy.ops.render.render(write_still=True)
print('FINAL: source, hero and walkthrough station renders, HDR environment written')
