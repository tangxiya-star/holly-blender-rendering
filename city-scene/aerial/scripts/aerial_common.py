import bpy, math, random
from mathutils import Vector
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def group(name):
    c=bpy.data.collections.get(name)
    if c is None:
        c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c)
    return c

def mesh(name,verts,faces,collection,materials=None,indices=None):
    d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update()
    o=bpy.data.objects.new(name,d);group(collection).objects.link(o)
    for mat in materials or []:d.materials.append(mat)
    if indices:
        for p,i in zip(d.polygons,indices):p.material_index=i
    return o

def box(name,center,size,collection,material=None):
    x,y,z=(a/2 for a in size)
    v=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    o=mesh(name,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],collection,[material] if material else [])
    o.location=center;return o

def material(name,color,rough=.75,metal=0,noise_scale=None):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if noise_scale:
        n=m.node_tree.nodes;l=m.node_tree.links
        pos=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=noise_scale
        noise.inputs['Detail'].default_value=3
        l.new(pos.outputs['Position'],noise.inputs['Vector']);r=n.new('ShaderNodeValToRGB')
        r.color_ramp.elements[0].color=(*(c*.72 for c in color),1)
        r.color_ramp.elements[1].color=(*(min(c*1.14,1) for c in color),1)
        l.new(noise.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Base Color'])
    return m

def palette():
    return {
      'facades':[material('CPH | facade '+str(i),c) for i,c in enumerate([(0.51,.47,.39),(.43,.40,.35),(.36,.26,.20),(.53,.46,.31),(.59,.57,.50),(.40,.42,.41),(.46,.35,.27),(.57,.53,.43)])],
      'roofs':[material('CPH | roof '+str(i),c,.77,0 if i<3 else .25,.23) for i,c in enumerate([(.28,.092,.048),(.35,.13,.065),(.19,.06,.034),(.105,.12,.12),(.21,.22,.22),(.13,.24,.205)])],
      'ground':material('Ground | weathered urban mineral',(.255,.25,.223),.92,noise_scale=.02),
      'quay':material('Quays | granite',(.26,.285,.29),.91,noise_scale=.2),
      'roads':material('Roads | asphalt',(.095,.104,.112),.86,noise_scale=.14),
      'paths':material('Park paths | gravel',(.4,.37,.29),.93),
      'park':material('Green areas | restrained late summer',(.125,.18,.075),.94,noise_scale=.04),
      'foliage':[material('Canopy | '+str(i),c,.88) for i,c in enumerate([(.055,.095,.029),(.078,.13,.037),(.10,.15,.056),(.047,.085,.043)])],
      'trunk':material('Trees | bark',(.115,.083,.058),.96),
    }

def aim(obj,at):obj.rotation_euler=(Vector(at)-obj.location).to_track_quat('-Z','Y').to_euler()

def camera(name,loc,at,lens=45):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);group('05_Cameras_and_Flight').objects.link(o)
    o.location=loc;d.lens=lens;d.sensor_width=36;d.clip_start=1;d.clip_end=80000;aim(o,at)
    return o

def cycles(samples=48):
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=samples;s.cycles.use_denoising=True
    s.cycles.max_bounces=6;s.cycles.diffuse_bounces=2;s.cycles.glossy_bounces=3;s.cycles.transmission_bounces=3;s.cycles.volume_bounces=0
    try:
        p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
        for d in p.devices:d.use=d.type=='METAL'
        if any(d.type=='METAL' for d in p.devices):s.cycles.device='GPU'
    except Exception:pass

def render(cam,name,width=1440,samples=48):
    s=bpy.context.scene;s.camera=cam;cycles(samples)
    s.render.resolution_x=width;s.render.resolution_y=round(width*9/16);s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.filepath=str(ROOT/'renders'/name)
    bpy.ops.render.render(write_still=True)
