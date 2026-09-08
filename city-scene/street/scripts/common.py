import bpy, math, json, random
from pathlib import Path
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]

def group(name):
    c=bpy.data.collections.get(name)
    if not c:
        c=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c)
    return c

def mesh(name,verts,faces,category,material=None,bevel=0):
    d=bpy.data.meshes.new(name); d.from_pydata(verts,[],faces);d.update()
    o=bpy.data.objects.new(name,d);group(category).objects.link(o)
    if material:d.materials.append(material)
    if bevel:
        m=o.modifiers.new('Soft manufactured edges','BEVEL');m.width=bevel;m.segments=2
    return o

def box(name,loc,size,category,material=None,bevel=0):
    x,y,z=(s/2 for s in size)
    v=[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)]
    f=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
    o=mesh(name,v,f,category,material,bevel);o.location=loc;return o

def mat(name,color,rough=.5,metal=0):
    m=bpy.data.materials.get(name)
    if m:return m
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m

def material_noise(name,color,scale=4,rough=.7,bump=.01):
    m=mat(name,color,rough); n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale
    noise.inputs['Detail'].default_value=3;l.new(geo.outputs['Position'],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=(*(c*.78 for c in color),1)
    ramp.color_ramp.elements[1].color=(*(min(c*1.13,1) for c in color),1)
    l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],p.inputs['Base Color'])
    fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=160
    l.new(geo.outputs['Position'],fine.inputs['Vector']);b=n.new('ShaderNodeBump')
    b.inputs['Strength'].default_value=.24;b.inputs['Distance'].default_value=bump
    l.new(fine.outputs['Fac'],b.inputs['Height']);l.new(b.outputs['Normal'],p.inputs['Normal']);return m

def curve(name,points,radius,category,material):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=radius;c.bevel_resolution=2
    s=c.splines.new('POLY');s.points.add(len(points)-1)
    for p,v in zip(s.points,points):p.co=(*v,1)
    o=bpy.data.objects.new(name,c);group(category).objects.link(o)
    if material:c.materials.append(material)
    return o

def text_obj(name,body,loc,size,category,material,rotation=(math.pi/2,0,0)):
    d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=size;d.align_x='CENTER';d.extrude=.001
    o=bpy.data.objects.new(name,d);group(category).objects.link(o);o.location=loc;o.rotation_euler=rotation
    if material:d.materials.append(material)
    return o

def instance(name,source,loc,category):
    o=source.copy();o.data=source.data;group(category).objects.link(o);o.name=name;o.location=loc;return o

def aim(o,at):o.rotation_euler=(Vector(at)-o.location).to_track_quat('-Z','Y').to_euler()

def camera(name,loc,at,lens=32):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);group('Cameras').objects.link(o)
    o.location=loc;d.lens=lens;d.sensor_width=36;d.clip_start=.05;d.clip_end=600;aim(o,at);return o

def save(filename):
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/filename))

def render(cam,filename,width=1100,samples=32):
    s=bpy.context.scene;s.camera=bpy.data.objects[cam];s.render.engine='CYCLES';s.cycles.samples=samples
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
        for d in prefs.devices:d.use=d.type=='METAL'
        if any(d.type=='METAL' for d in prefs.devices):s.cycles.device='GPU'
    except Exception:pass
    s.cycles.use_denoising=True;s.render.resolution_x=width;s.render.resolution_y=round(width*.667)
    s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(ROOT/'renders'/filename)
    bpy.ops.render.render(write_still=True)

def lighting():
    s=bpy.context.scene;s.world=bpy.data.worlds.new('Copenhagen | cool cloud-filtered daylight');s.world.use_nodes=True
    n=s.world.node_tree.nodes;l=s.world.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputWorld');bg=n.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.7
    sky=n.new('ShaderNodeTexSky');sky.sky_type='MULTIPLE_SCATTERING';sky.sun_elevation=math.radians(37);sky.sun_rotation=math.radians(135)
    sky.sun_intensity=.13;sky.air_density=1.2;sky.aerosol_density=.4;sky.ozone_density=1.3
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[0].default_value=.94;mix.inputs[2].default_value=(.65,.69,.73,1)
    l.new(sky.outputs[0],mix.inputs[1]);l.new(mix.outputs[0],bg.inputs[0]);l.new(bg.outputs[0],out.inputs[0])
    d=bpy.data.lights.new('Cloud-filtered sun','SUN');o=bpy.data.objects.new(d.name,d);group('Lighting').objects.link(o)
    d.energy=.22;d.angle=math.radians(35);o.rotation_euler=(math.radians(24),math.radians(-30),math.radians(-25))
    s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.4
    hdri=ROOT/'textures'/'overcast_soil_puresky_2k.hdr'
    if hdri.exists():
        env=n.new('ShaderNodeTexEnvironment');env.name='Photographic overcast sky | CC0 Poly Haven'
        env.image=bpy.data.images.load(str(hdri),check_existing=True);env.image.pack()
        env.texture_mapping.rotation.z=math.radians(75)
        l.new(env.outputs['Color'],bg.inputs['Color']);bg.inputs['Strength'].default_value=.85
        d.energy=0
        s.view_settings.exposure=.65
    s.render.engine='CYCLES';s.cycles.samples=40;s.cycles.use_denoising=True
    s.cycles.max_bounces=7;s.cycles.diffuse_bounces=3;s.cycles.glossy_bounces=4;s.cycles.transmission_bounces=6
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
        for d in prefs.devices:d.use=d.type=='METAL'
        if any(d.type=='METAL' for d in prefs.devices):s.cycles.device='GPU'
    except Exception:pass
