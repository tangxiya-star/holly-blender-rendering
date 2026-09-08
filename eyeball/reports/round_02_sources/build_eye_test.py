"""Build a separate, full-detail Cycles food photography study. No web export."""
import bpy, sys, math, json, time, shutil, hashlib
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
for name in ['renders','reports']: (ROOT/name).mkdir(parents=True,exist_ok=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
ROUND=args[0] if args else '01'
WIDTH=int(args[1]) if len(args)>1 else 1200
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
    s.render.resolution_x=WIDTH;s.render.resolution_y=WIDTH
    s.render.resolution_percentage=100;s.render.film_transparent=False
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
    s.render.image_settings.color_depth='16';s.render.image_settings.compression=30
    s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
    s.view_settings.exposure=0;s.view_settings.gamma=1
    return device

def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene;s.name='Food study | 1984 eye dish'
    s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
    s['reference']='Supertaster Mel 1984 eye photograph linked by user; references/reference_eye.jpg'
    s['scale_assumption']='Eye vessel width 140 mm, estimated from photograph, not measured'
    s['purpose']='Full-detail Cycles hero photography realism test; no web optimization'
    s['round']=ROUND
    foodc=collection('01 | Pupil food');eyec=collection('02 | Eye vessel');supportc=collection('03 | Stone')
    lightc=collection('04 | Photography lighting');camc=collection('05 | Camera')
    snapshot=ROOT/'reports'/f'round_{ROUND}_sources';snapshot.mkdir(exist_ok=True)
    source_hashes={}
    for filename in ['build_eye_test.py','stage.py','eye.py','food_insert.py']:
        src=ROOT/'scripts'/filename
        shutil.copyfile(src,snapshot/filename)
        source_hashes[filename]=hashlib.sha256(src.read_bytes()).hexdigest()
    from stage import build_stage
    from eye import build_eye
    from food_insert import build_food_insert
    support_info=build_stage(supportc)
    eye_info=build_eye(eyec)
    food_info=build_food_insert(foodc)
    # Seat the modeled 2 mm base on the actual stone rather than leaving a gap.
    for obj in list(eyec.objects)+list(foodc.objects):obj.location.z-=.0019
    w=bpy.data.worlds.new('Black photographic surroundings');s.world=w;w.use_nodes=True
    w.node_tree.nodes['Background'].inputs['Color'].default_value=(0,0,0,1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value=0
    key=area(lightc,'KEY | warm left photographic source',(-.10,.13,.37),(0,0,.07),4.7,(1,.77,.58),.025,.036)
    key.data.spread=math.radians(65)
    area(lightc,'FILL | violet restaurant illumination',(.20,.015,.21),(0,0,.05),.25,(.24,.045,1),.18,.22)
    area(lightc,'WASH | blue-violet stone ambience',(.04,.28,.22),(0,.16,0),.55,(.14,.03,1),.26,.19)
    area(lightc,'BOUNCE | subdued front warm card',(-.12,-.25,.13),(0,0,.055),.055,(1,.63,.47),.22,.18)
    # One photographic lens and true depth of field. Shift is left neutral until comparison.
    d=bpy.data.cameras.new('85mm macro | physical DOF');cam=bpy.data.objects.new('CAM_Eye_Hero',d)
    camc.objects.link(cam);s.camera=cam
    target=Vector((0,0,.057));elev=math.radians(38);distance=.42
    cam.location=target+Vector((0,-math.cos(elev)*distance,math.sin(elev)*distance))
    aim(cam,target);d.type='PERSP';d.lens=85;d.sensor_fit='VERTICAL';d.sensor_height=36
    d.clip_start=.005;d.clip_end=20
    focus=bpy.data.objects.new('FOCUS | pupil food and forward iris',None);camc.objects.link(focus)
    focus.location=(0,-.008,.101);focus.empty_display_size=.006
    d.dof.use_dof=True;d.dof.focus_object=focus;d.dof.aperture_fstop=9
    d.dof.aperture_blades=9;d.dof.aperture_rotation=.15;d.dof.aperture_ratio=1
    device=configure_cycles(s)
    s.render.filepath=str(ROOT/'renders'/f'eye_{ROUND}.png')
    for scr in bpy.data.screens:
        for a in scr.areas:
            if a.type=='VIEW_3D':
                a.spaces.active.region_3d.view_perspective='CAMERA'
                a.spaces.active.overlay.show_overlays=False
                a.spaces.active.shading.type='MATERIAL'
                a.spaces.active.shading.use_scene_world=True
                a.spaces.active.shading.use_scene_lights=True
    bpy.context.view_layer.update()
    for obj in eyec.objects:
        if obj.type=='MESH':
            obj.select_set(True);bpy.context.view_layer.objects.active=obj;break
    bpy.ops.file.pack_all()
    metrics={'round':ROUND,'version':bpy.app.version_string,'device':device,'resolution':[s.render.resolution_x,s.render.resolution_y],
             'samples':SAMPLES,'adaptive_threshold':s.cycles.adaptive_threshold,'objects':len(s.objects),
             'mesh_vertices':sum(len(o.data.vertices) for o in s.objects if o.type=='MESH'),
             'base_mesh_faces':sum(len(o.data.polygons) for o in s.objects if o.type=='MESH'),
             'materials':len(bpy.data.materials),'build_seconds':time.time()-START,'source_sha256':source_hashes,
             'camera':{'lens_mm':d.lens,'sensor_fit':d.sensor_fit,'sensor_height_mm':d.sensor_height,'fstop':d.dof.aperture_fstop,'position':list(cam.location),'focus':list(focus.location)},
             'food_info':food_info,'support_info':support_info,'eye_info':eye_info}
    metrics=json.loads(json.dumps(metrics,default=lambda value:getattr(value,'name',str(value))))
    (ROOT/'reports'/f'round_{ROUND}_build.json').write_text(json.dumps(metrics,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'eye_{ROUND}.blend'))
    print('BUILD_COMPLETE',json.dumps({k:v for k,v in metrics.items() if k not in ['food_info','support_info']}),flush=True)
    bpy.ops.render.render(write_still=True)
    # Keep linear floating-point radiance for independent inspection and final grading.
    s.render.image_settings.file_format='OPEN_EXR';s.render.image_settings.color_depth='16'
    bpy.data.images['Render Result'].save_render(str(ROOT/'renders'/f'eye_{ROUND}_linear.exr'),scene=s)
    print('RENDER_COMPLETE',ROUND,'seconds',time.time()-START,flush=True)

if __name__=='__main__':build()
