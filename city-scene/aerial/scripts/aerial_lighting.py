import bpy, math
from aerial_common import group, box, ROOT

def build_lighting():
    s=bpy.context.scene;w=bpy.data.worlds.new('Scandinavian afternoon | physical sky');w.use_nodes=True;s.world=w
    n=w.node_tree.nodes;l=w.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputWorld');bg=n.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.55
    env=n.new('ShaderNodeTexEnvironment');env.name='Photographic cloud sky | CC0 Poly Haven'
    env.image=bpy.data.images.load(str(ROOT/'textures'/'overcast_soil_puresky_2k.hdr'),check_existing=True);env.image.pack()
    env.texture_mapping.rotation.z=math.radians(75)
    l.new(env.outputs[0],bg.inputs['Color']);l.new(bg.outputs[0],out.inputs['Surface'])
    light=bpy.data.lights.new('Soft southwest sun','SUN');o=bpy.data.objects.new(light.name,light);group('06_Daylight_and_Atmosphere').objects.link(o)
    light.energy=2.6;light.angle=math.radians(1.4);light.color=(1,.98,.95)
    o.rotation_euler=(math.radians(61),0,math.radians(218))
    m=bpy.data.materials.new('Atmosphere | altitude dependent haze');m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');v=n.new('ShaderNodeVolumePrincipled')
    v.inputs['Color'].default_value=(.83,.87,.89,1);v.inputs['Anisotropy'].default_value=.22
    pos=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(pos.outputs['Position'],sep.inputs[0])
    mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=-1/1000;l.new(sep.outputs['Z'],mult.inputs[0])
    exp=n.new('ShaderNodeMath');exp.operation='EXPONENT';l.new(mult.outputs[0],exp.inputs[0])
    den=n.new('ShaderNodeMath');den.operation='MULTIPLY';den.inputs[1].default_value=.000017;l.new(exp.outputs[0],den.inputs[0]);l.new(den.outputs[0],v.inputs['Density'])
    l.new(v.outputs['Volume'],out.inputs['Volume'])
    obj=box('Aerial haze | 28km extent',(0,0,2350),(28000,28000,4900),'06_Daylight_and_Atmosphere',m);obj.display_type='WIRE'
    s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.15
    s.render.film_transparent=False
    return {'sun_elevation_degrees':29,'base_haze_density':.000017,'haze_scale_height_m':1000,'sky':'packed CC0 Poly Haven overcast HDRI'}
