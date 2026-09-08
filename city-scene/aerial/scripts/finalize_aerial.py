import bpy, sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from aerial_common import render

fixed={}
for obj in bpy.data.collections['01_Real_Geography'].objects:
    if obj.type!='MESH':continue
    count=0
    for poly in obj.data.polygons:
        if poly.normal.z<-.5:poly.flip();count+=1
    obj.data.update();fixed[obj.name]=count
water=bpy.data.materials['Water | Baltic harbor blue green'];shader=water.node_tree.nodes.get('Principled BSDF')
shader.inputs['Metallic'].default_value=0;shader.inputs['Roughness'].default_value=.28;shader.inputs['Transmission Weight'].default_value=.04
bpy.context.view_layer.update()
s=bpy.context.scene;s.camera=bpy.data.objects['01 | HERO - Copenhagen from the southeast'];s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'copenhagen_aerial.blend'))
render(s.camera,'hero_aerial.png',1920,64)
render(bpy.data.objects['02 | Harbor and historic center'],'harbor_aerial.png',1600,48)
render(bpy.data.objects['03 | Nyhavn - handoff approach'],'nyhavn_handoff.png',1440,48)
s.camera=bpy.data.objects['05 | CINEMATIC DIVE - World Labs handoff'];s.frame_set(505)
render(s.camera,'dive_0505.png',1280,40)
s.frame_set(673);render(s.camera,'transition_0673.png',1280,32)
s.camera=bpy.data.objects['01 | HERO - Copenhagen from the southeast'];s.frame_set(1)
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
s['realism_fixes']='Real shore context cutout; upward GIS surface normals; neutral packed HDRI; smooth per-frame descent; aerial facade rhythm only near Nyhavn'
stats=json.loads((ROOT/'reports'/'build_stats.json').read_text());stats['final_refinements']={'surface_normals_fixed':fixed,'camera_start_altitude_m':3300,'sky':'packed CC0 Poly Haven overcast HDRI','haze_density':.000017,'water_metallic':0,'water_roughness':.28,'window_rhythm_radius_m':230}
(ROOT/'reports'/'build_stats.json').write_text(json.dumps(stats,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'copenhagen_aerial.blend'))
from validate_aerial import validate_aerial
validate_aerial()
