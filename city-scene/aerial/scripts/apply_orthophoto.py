import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from aerial_common import render
from aerial_cameras import build_cameras

def atlas_material(mat,image,weight):
    n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF')
    if n.get('Real Copenhagen orthophoto'):return
    pos=n.new('ShaderNodeNewGeometry')
    subtract=n.new('ShaderNodeVectorMath');subtract.operation='SUBTRACT';subtract.inputs[1].default_value=(-5542.597573906,-5688.452,0);l.new(pos.outputs['Position'],subtract.inputs[0])
    scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(1/11926.314145437,1/12245.2,0);l.new(subtract.outputs[0],scale.inputs[0])
    tex=n.new('ShaderNodeTexImage');tex.name='Real Copenhagen orthophoto';tex.image=image;tex.extension='CLIP';tex.interpolation='Linear';l.new(scale.outputs[0],tex.inputs['Vector'])
    mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=weight;l.new(tex.outputs['Alpha'],mul.inputs[0])
    mix=n.new('ShaderNodeMixRGB');l.new(mul.outputs[0],mix.inputs[0])
    if p.inputs['Base Color'].links:l.new(p.inputs['Base Color'].links[0].from_socket,mix.inputs[1])
    else:mix.inputs[1].default_value=p.inputs['Base Color'].default_value
    l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])

def apply():
    img=bpy.data.images.load(str(ROOT/'data'/'aerial_imagery.jpg'),check_existing=True);img.pack()
    for m in bpy.data.materials:
        if m.name.startswith('CPH | roof'):atlas_material(m,img,.92)
        elif m.name in ['Ground | weathered urban mineral','Green areas | restrained late summer','Roads | asphalt','Park paths | gravel']:atlas_material(m,img,.96)
    # One physical water surface serves all holes in the true land polygons.
    old=bpy.data.objects.get('Real inland lakes and canals')
    if old:bpy.data.objects.remove(old,do_unlink=True)
    w=bpy.context.scene.world.node_tree.nodes.get('Background');w.inputs['Strength'].default_value=.32
    for o in list(bpy.data.collections['05_Cameras_and_Flight'].objects):bpy.data.objects.remove(o,do_unlink=True)
    bpy.context.scene.timeline_markers.clear();build_cameras()
    s=bpy.context.scene;s.camera=bpy.data.objects['01 | HERO - Copenhagen from the southeast'];s.frame_set(1)
    s['imagery_attribution']='GeoDanmark orthophotos © Klimadatastyrelsen / GeoDanmark, CC BY4.0; acquired via Septima for local evaluation'
    s['handoff_altitude_m']=180
    for t in bpy.data.texts:
        if t.name.startswith('READ ME'):t.clear();t.write('Copenhagen city-scale aerial.81,774 real OSM footprints; realGeoDanmark orthoatlas.\nCamera01hero,05animateddiveframes1-673/24fps.\nHandoffframe649 at180m; cameraends160m. World Labs externalworldnotyetprovided.\nSeeREADME and reports/camera_handoff.json.\n© OpenStreetMapcontributors ODbL. Orthophoto© Klimadatastyrelsen/GeoDanmark CC BY4.0.\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'copenhagen_aerial_final.blend'))
    render(s.camera,'hero_aerial.png',1920,64)
    render(bpy.data.objects['02 | Harbor and historic center'],'harbor_aerial.png',1600,48)
    render(bpy.data.objects['03 | Nyhavn - handoff approach'],'nyhavn_handoff.png',1440,48)
    s.camera=bpy.data.objects['05 | CINEMATIC DIVE - World Labs handoff'];s.frame_set(505);render(s.camera,'dive_0505.png',1280,40)
    s.frame_set(673);render(s.camera,'transition_0673.png',1280,32)
    s.frame_set(1);s.camera=bpy.data.objects['01 | HERO - Copenhagen from the southeast']
    s.render.resolution_x=1920;s.render.resolution_y=1080
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'copenhagen_aerial_final.blend'))
    from validate_aerial import validate_aerial
    validate_aerial()

if __name__=='__main__':apply()
