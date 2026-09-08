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
    s.cycles.samples=SAMPLES;s.cycles.preview_samples=32
    s.cycles.use_preview_denoising=True
    s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.006
    s.cycles.adaptive_min_samples=64
    s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
    s.cycles.denoising_prefilter='ACCURATE'
    s.cycles.max_bounces=12;s.cycles.diffuse_bounces=5;s.cycles.glossy_bounces=6
    s.cycles.transmission_bounces=10;s.cycles.transparent_max_bounces=12
    s.cycles.sample_clamp_direct=0;s.cycles.sample_clamp_indirect=10
    s.cycles.blur_glossy=.2;s.cycles.seed=7283
    s.cycles.pixel_filter_type='BLACKMAN_HARRIS';s.cycles.filter_width=1.2
    s.render.resolution_x=WIDTH;s.render.resolution_y=round(WIDTH*1.25)
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
    s['reference']='User supplemental blue-eye reference; references/reference_blue_newyorker.jpg, manufacturer 10tons.dk/eyeball'
    s['scale_assumption']='Manufacturer verified vessel diameter 200 mm; original 140 mm construction globally scaled by 10/7'
    s['purpose']='Full-detail Cycles hero photography realism test; no web optimization'
    s['round']=ROUND
    foodc=collection('01 | Pupil food');eyec=collection('02 | Eye vessel');supportc=collection('03 | Stone')
    lightc=collection('04 | Photography lighting');camc=collection('05 | Camera')
    snapshot=ROOT/'reports'/f'round_{ROUND}_sources';snapshot.mkdir(exist_ok=True)
    source_hashes={}
    for filename in ['build_eye_test.py','stage.py','eye.py','food_insert.py','iris_detail.py']:
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
    for obj in list(eyec.objects)+list(foodc.objects):obj.location.z-=.0021
    w=bpy.data.worlds.new('Black photographic surroundings');s.world=w;w.use_nodes=True
    w.node_tree.nodes['Background'].inputs['Color'].default_value=(0,0,0,1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value=0
    area(lightc,'KEY | neutral right window',(.26,-.12,.23),(0,0,.06),3.8,(1,.96,.89),.035,.055)
    area(lightc,'FILL | restrained cool wall bounce',(-.18,-.10,.20),(0,0,.05),.016,(.67,.80,1),.25,.28)
    area(lightc,'AMBIENCE | quiet overhead room bounce',(.03,.25,.32),(0,.10,0),.04,(.79,.86,1),.36,.32)
    # A small divided window makes a real reflected pattern through the resin.
    for row in range(3):
        for col in range(3):
            area(lightc,f'WINDOW | pane {row}-{col}',(-.095+(col-1)*.010,.16,.34+(row-1)*.010),(0,-.015,.10),.018,(.91,.97,1),.0075,.0075)
    # One photographic lens and true depth of field. Shift is left neutral until comparison.
    d=bpy.data.cameras.new('85mm macro | physical DOF');cam=bpy.data.objects.new('CAM_Eye_Hero',d)
    camc.objects.link(cam);s.camera=cam
    target=Vector((0,0,.057));elev=math.radians(55);distance=.69
    cam.location=target+Vector((0,-math.cos(elev)*distance,math.sin(elev)*distance))
    aim(cam,target);d.type='PERSP';d.lens=85;d.sensor_fit='VERTICAL';d.sensor_height=36
    d.shift_x=-.04;d.shift_y=.02
    d.clip_start=.005;d.clip_end=20
    focus=bpy.data.objects.new('FOCUS | pupil food and forward iris',None);camc.objects.link(focus)
    focus.location=(0,-.008,.101);focus.empty_display_size=.006
    d.dof.use_dof=True;d.dof.focus_object=focus;d.dof.aperture_fstop=11
    d.dof.aperture_blades=9;d.dof.aperture_rotation=.15;d.dof.aperture_ratio=1
    # Preserve composition while matching the maker's actual 200 mm diameter.
    physical_scale=10/7
    for obj in s.objects:
        obj.location*=physical_scale
        if obj.type=='LIGHT':
            obj.data.energy*=physical_scale**2
            obj.data.size*=physical_scale;obj.data.size_y*=physical_scale
        elif obj.type=='CAMERA':
            obj.data.clip_start*=physical_scale;obj.data.clip_end*=physical_scale
        else:obj.scale*=physical_scale
    device=configure_cycles(s)
    s.render.filepath=str(ROOT/'renders'/f'eye_{ROUND}.png')
    for scr in bpy.data.screens:
        for a in scr.areas:
            if a.type=='VIEW_3D':
                a.spaces.active.region_3d.view_perspective='CAMERA'
                a.spaces.active.region_3d.view_camera_zoom=45
                a.spaces.active.overlay.show_overlays=False
                a.spaces.active.shading.type='RENDERED'
                a.spaces.active.shading.use_scene_world=True
                a.spaces.active.shading.use_scene_lights=True
    bpy.context.view_layer.update()
    for obj in eyec.objects:
        if obj.type=='MESH':
            obj.select_set(True);bpy.context.view_layer.objects.active=obj;break
    bpy.ops.file.pack_all()
    body_object=eye_info['objects'][0]
    metrics={'round':ROUND,'version':bpy.app.version_string,'device':device,'resolution':[s.render.resolution_x,s.render.resolution_y],
             'physical_scale_factor':physical_scale,'body_world_dimensions_m':list(body_object.dimensions),
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
