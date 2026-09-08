"""Build a separate, full-detail Cycles food photography study. No web export."""
import bpy, sys, math, json, time, shutil, hashlib
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
for name in ['renders','reports']: (ROOT/name).mkdir(parents=True,exist_ok=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
ROUND=args[0] if args else '01'
WIDTH=int(args[1]) if len(args)>1 else 1067
SAMPLES=int(args[2]) if len(args)>2 else 192
START=time.time()

def collection(name):
    c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);return c

def aim(o,at): o.rotation_euler=(Vector(at)-o.location).to_track_quat('-Z','Y').to_euler()

def area(c,name,pos,at,power,color,size,size_y):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color
    data.shape='RECTANGLE';data.size=size;data.size_y=size_y
    o=bpy.data.objects.new(name,data);c.objects.link(o);o.location=pos;aim(o,at);return o

def configure_cycles(s):
    s.render.engine='CYCLES'
    prefs=bpy.context.preferences.addons['cycles'].preferences
    device='CPU'
    try:
        prefs.compute_device_type='METAL';prefs.get_devices()
        for d in prefs.devices:d.use=d.type=='METAL'
        if any(d.use for d in prefs.devices):device='GPU'
    except Exception:pass
    s.cycles.device=device
    s.cycles.samples=SAMPLES;s.cycles.preview_samples=24
    s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.006
    s.cycles.adaptive_min_samples=64
    s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
    s.cycles.denoising_prefilter='ACCURATE'
    s.cycles.max_bounces=12;s.cycles.diffuse_bounces=5;s.cycles.glossy_bounces=6
    s.cycles.transmission_bounces=10;s.cycles.transparent_max_bounces=12
    s.cycles.sample_clamp_direct=0;s.cycles.sample_clamp_indirect=10
    s.cycles.blur_glossy=.2;s.cycles.seed=7283
    s.cycles.pixel_filter_type='BLACKMAN_HARRIS';s.cycles.filter_width=1.2
    s.render.resolution_x=WIDTH;s.render.resolution_y=round(WIDTH*1600/1067)
    s.render.resolution_percentage=100;s.render.film_transparent=False
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
    s.render.image_settings.color_depth='16';s.render.image_settings.compression=30
    s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
    s.view_settings.exposure=-.1;s.view_settings.gamma=1
    return device

def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene;s.name='Food study | caviar pastries on moss'
    s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
    s['reference']='Eatweek Guide photograph provided by user; references/reference_dish.jpg'
    s['scale_assumption']='Plate diameter 170 mm, estimated from photograph, not measured'
    s['purpose']='Full-detail Cycles hero photography realism test; no web optimization'
    s['round']=ROUND
    foodc=collection('01 | Food');supportc=collection('02 | Plating and surface')
    lightc=collection('03 | Photography lighting');camc=collection('04 | Camera')
    snapshot=ROOT/'reports'/f'round_{ROUND}_sources';snapshot.mkdir(exist_ok=True)
    source_hashes={}
    for filename in ['build_test.py','support.py','food.py']:
        src=ROOT/'scripts'/filename
        shutil.copyfile(src,snapshot/filename)
        source_hashes[filename]=hashlib.sha256(src.read_bytes()).hexdigest()
    from support import build_support
    from food import build_food
    support_info=build_support(supportc)
    food_info=build_food(foodc)
    w=bpy.data.worlds.new('Black photographic surroundings');s.world=w;w.use_nodes=True
    w.node_tree.nodes['Background'].inputs['Color'].default_value=(0,0,0,1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value=0
    area(lightc,'KEY | upper left softbox',(-.24,.035,.31),(0,0,.04),5.4,(1,.975,.94),.105,.16)
    area(lightc,'FILL | restrained neutral card',(.10,-.30,.19),(0,-.01,.055),.42,(.83,.90,1),.24,.20)
    # One photographic lens and true depth of field. Shift is left neutral until comparison.
    d=bpy.data.cameras.new('90mm macro | physical DOF');cam=bpy.data.objects.new('CAM_Food_Hero',d)
    camc.objects.link(cam);s.camera=cam
    target=Vector((.002,0,.038));elev=math.radians(27);distance=.733
    cam.location=target+Vector((0,-math.cos(elev)*distance,math.sin(elev)*distance))
    aim(cam,target);d.type='PERSP';d.lens=90;d.sensor_fit='VERTICAL';d.sensor_height=36
    d.clip_start=.005;d.clip_end=20
    focus=bpy.data.objects.new('FOCUS | front caviar and cream',None);camc.objects.link(focus)
    focus.location=(.003,-.031,.075);focus.empty_display_size=.006
    d.dof.use_dof=True;d.dof.focus_object=focus;d.dof.aperture_fstop=7.1
    d.dof.aperture_blades=9;d.dof.aperture_rotation=.15;d.dof.aperture_ratio=1
    device=configure_cycles(s)
    s.render.filepath=str(ROOT/'renders'/f'food_{ROUND}.png')
    for scr in bpy.data.screens:
        for a in scr.areas:
            if a.type=='VIEW_3D':
                a.spaces.active.region_3d.view_perspective='CAMERA'
                a.spaces.active.overlay.show_overlays=False
                a.spaces.active.shading.type='MATERIAL'
                a.spaces.active.shading.use_scene_world=True
                a.spaces.active.shading.use_scene_lights=True
    bpy.context.view_layer.update()
    metrics={'round':ROUND,'version':bpy.app.version_string,'device':device,'resolution':[s.render.resolution_x,s.render.resolution_y],
             'samples':SAMPLES,'adaptive_threshold':s.cycles.adaptive_threshold,'objects':len(s.objects),
             'mesh_vertices':sum(len(o.data.vertices) for o in s.objects if o.type=='MESH'),
             'base_mesh_faces':sum(len(o.data.polygons) for o in s.objects if o.type=='MESH'),
             'materials':len(bpy.data.materials),'build_seconds':time.time()-START,'source_sha256':source_hashes,
             'camera':{'lens_mm':d.lens,'sensor_fit':d.sensor_fit,'sensor_height_mm':d.sensor_height,'fstop':d.dof.aperture_fstop,'position':list(cam.location),'focus':list(focus.location)},
             'food_info':str(food_info),'support_info':str(support_info)}
    (ROOT/'reports'/f'round_{ROUND}_build.json').write_text(json.dumps(metrics,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'food_{ROUND}.blend'))
    print('BUILD_COMPLETE',json.dumps({k:v for k,v in metrics.items() if k not in ['food_info','support_info']}),flush=True)
    bpy.ops.render.render(write_still=True)
    # Keep linear floating-point radiance for independent inspection and final grading.
    s.render.image_settings.file_format='OPEN_EXR';s.render.image_settings.color_depth='16'
    bpy.data.images['Render Result'].save_render(str(ROOT/'renders'/f'food_{ROUND}_linear.exr'),scene=s)
    print('RENDER_COMPLETE',ROUND,'seconds',time.time()-START,flush=True)

if __name__=='__main__':build()
