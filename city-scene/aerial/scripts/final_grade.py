import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from aerial_common import render
from apply_orthophoto import atlas_material
s=bpy.context.scene
water=bpy.data.materials['Water | Baltic harbor blue green'].node_tree.nodes.get('Principled BSDF')
water.inputs['Roughness'].default_value=.42;water.inputs['Specular IOR Level'].default_value=.22;water.inputs['Transmission Weight'].default_value=0
for m in bpy.data.materials:
    if m.name.startswith('CPH | roof'):
        for n in m.node_tree.nodes:
            if n.bl_idname=='ShaderNodeMath' and n.operation=='MULTIPLY' and n.inputs[0].is_linked:
                if n.inputs[0].links[0].from_node.name=='Real Copenhagen orthophoto':n.inputs[1].default_value=.45
    elif m.name.startswith('CPH | facade'):
        p=m.node_tree.nodes.get('Principled BSDF');base=p.inputs['Base Color']
        if base.links:
            previous=base.links[0].from_socket
            mult=m.node_tree.nodes.new('ShaderNodeMixRGB');mult.name='Restrained facade reflectance';mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1;mult.inputs[2].default_value=(.68,.68,.68,1)
            m.node_tree.links.new(previous,mult.inputs[1]);m.node_tree.links.new(mult.outputs[0],base)
s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.18
for obj in s.objects:
    if obj.type=='LIGHT' and obj.data.type=='SUN':obj.data.energy=3.1
local_path=ROOT/'data'/'nyhavn_imagery.jpg'
if local_path.exists():
    local=bpy.data.images.load(str(local_path),check_existing=True);local.pack()
    for mat in bpy.data.materials:
        if not (mat.name.startswith('CPH | roof') or mat.name in ['Ground | weathered urban mineral','Green areas | restrained late summer','Roads | asphalt','Park paths | gravel']):continue
        n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF')
        pos=n.new('ShaderNodeNewGeometry');offset=n.new('ShaderNodeVectorMath');offset.operation='SUBTRACT';offset.inputs[1].default_value=(1100,100,0);l.new(pos.outputs['Position'],offset.inputs[0])
        scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(1/750,1/750,0);l.new(offset.outputs[0],scale.inputs[0])
        tex=n.new('ShaderNodeTexImage');tex.name='Nyhavn only | detailed orthophoto';tex.image=local;tex.extension='CLIP';l.new(scale.outputs[0],tex.inputs['Vector'])
        mix=n.new('ShaderNodeMixRGB');old=p.inputs['Base Color'].links[0].from_socket;l.new(old,mix.inputs[1]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(tex.outputs['Alpha'],mix.inputs[0]);l.new(mix.outputs[0],p.inputs['Base Color'])
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.region_3d.view_camera_zoom=0
s.camera=bpy.data.objects['01 | HERO - Copenhagen from the southeast'];s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'copenhagen_aerial_final.blend'))
render(s.camera,'hero_aerial.png',1920,64)
render(bpy.data.objects['02 | Harbor and historic center'],'harbor_aerial.png',1600,48)
render(bpy.data.objects['03 | Nyhavn - handoff approach'],'nyhavn_handoff.png',1440,48)
s.camera=bpy.data.objects['05 | CINEMATIC DIVE - World Labs handoff'];s.frame_set(505);render(s.camera,'dive_0505.png',1280,40)
s.frame_set(673);render(s.camera,'transition_0673.png',1280,32)
s.frame_set(1);s.camera=bpy.data.objects['01 | HERO - Copenhagen from the southeast'];s.render.resolution_x=1920;s.render.resolution_y=1080
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'copenhagen_aerial_final.blend'))
from validate_aerial import validate_aerial
validate_aerial()
