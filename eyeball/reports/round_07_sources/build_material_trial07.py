"""Test a new iris texture on the complete 3D asset, preserving source round 06.

The input image is an AI-assisted diffuse pigmentation interpretation, not a
scan or the finished render. Cycles still computes all 3D light/refraction.
"""
import bpy, sys, json, math, hashlib, shutil, time
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
assert bpy.app.background, 'Run this isolated material test in background Blender'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'eye_06.blend'))
scene=bpy.context.scene
scene.name='Eye 07 | full 3D material reconstruction'
scene['round']='07'
scene['reference_limit']='Only web photographs available. Unseen sides are inferred reconstruction.'
scene['iris_texture_provenance']='Built-in imagegen: original reference-guided diffuse texture interpretation. Not a photogrammetric scan or source-photo projection.'
scene['comparison']='Hero camera and lights held at round 06 settings; new iris pigmentation and conservative seam cleanup.'
scene['purpose']='Full-detail 360-degree asset and Cycles material test; no GLB or web optimization yet.'
from cleanup_orbit_geometry import cleanup_orbit_geometry
topology=cleanup_orbit_geometry(scene)
(ROOT/'reports'/'round_07_topology.json').write_text(json.dumps(topology,indent=2))

# Keep the older ribbon construction in the file, disabled, for comparison.
hidden=[]
for obj in scene.objects:
    if obj.name.startswith(('Blue iris | broad pale forked','Blue iris | actual overlapping')):
        obj.hide_render=True;obj.hide_viewport=True;hidden.append(obj.name)
bed=next(o for o in scene.objects if o.name.startswith('Blue iris | recessed layered'))
uv=bed.data.uv_layers.new(name='Iris07_PlanarColor')
outer_radius=.0425
for poly in bed.data.polygons:
    for li in poly.loop_indices:
        co=bed.data.vertices[bed.data.loops[li].vertex_index].co
        uv.data[li].uv=(.5+co.x/outer_radius*.464,.5+co.y/outer_radius*.464)
image=bpy.data.images.load(str(ROOT/'textures'/'iris_07_albedo.png'),check_existing=False)
image.name='Iris07 | reference-guided diffuse pigment interpretation'
image.colorspace_settings.name='sRGB';image.pack()
image['origin']='Built-in imagegen, prompt in textures/iris_07_prompt.txt; not measured albedo'
mat=bed.data.materials[0];nodes=mat.node_tree.nodes;links=mat.node_tree.links
tex=next(n for n in nodes if n.type=='TEX_IMAGE')
tex.image=image;tex.interpolation='Cubic';tex.extension='EXTEND'
coords=nodes.new('ShaderNodeUVMap');coords.uv_map=uv.name
links.new(coords.outputs['UV'],tex.inputs['Vector'])
bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
relief=nodes.new('ShaderNodeBump');relief.name='Shallow art-directed pigment microrelief'
relief.inputs['Distance'].default_value=.000018;relief.inputs['Strength'].default_value=.19
old_normal=list(bs.inputs['Normal'].links)
if old_normal:links.new(old_normal[0].from_socket,relief.inputs['Normal'])
links.new(tex.outputs['Color'],relief.inputs['Height'])
links.new(relief.outputs['Normal'],bs.inputs['Normal'])

prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='METAL'
scene.cycles.device='GPU'
scene.cycles.samples=768;scene.cycles.preview_samples=32
scene.cycles.use_preview_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=2000
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_depth='16'
scene.render.filepath=str(ROOT/'renders'/'eye_07.png')
for screen in bpy.data.screens:
    for area in screen.areas:
        for space in area.spaces:
            if space.type=='VIEW_3D':
                space.region_3d.view_perspective='CAMERA'
                space.region_3d.view_camera_zoom=40
                space.shading.type='RENDERED'
                space.overlay.show_overlays=False
bpy.ops.file.pack_all()
snapshot=ROOT/'reports'/'round_07_sources';snapshot.mkdir(exist_ok=True)
for name in ['build_material_trial07.py','cleanup_orbit_geometry.py']:
    shutil.copyfile(ROOT/'scripts'/name,snapshot/name)
report={'round':'07','source_blend':'eye_06.blend','geometry_cleanup_status':topology['status'],
        'hidden_legacy_ribbon_objects':hidden,'texture_size':list(image.size),
        'texture_sha256':hashlib.sha256((ROOT/'textures'/'iris_07_albedo.png').read_bytes()).hexdigest(),
        'material_method':'Reference-guided AI-assisted diffuse pigment texture on curved iris bed beneath closed 3D resin',
        'geometry_full_circumference':True,'unseen_surfaces':'inferred, not documented by supplied photographs',
        'hero_resolution':[1600,2000],'hero_max_samples':768,
        'hero_camera_lighting':'same as round 06','renders':[]}
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'eye_07.blend'))
print('ROUND07_SAVED',json.dumps({k:v for k,v in report.items() if k!='renders'}),flush=True)
start=time.time()
bpy.ops.render.render(write_still=True)
report['renders'].append({'file':'renders/eye_07.png','type':'hero','seconds':time.time()-start})
scene.render.image_settings.file_format='OPEN_EXR';scene.render.image_settings.color_depth='16'
bpy.data.images['Render Result'].save_render(str(ROOT/'renders'/'eye_07_linear.exr'),scene=scene)
scene.render.image_settings.file_format='PNG'

# Real new viewpoints: texture remains fixed on the object; all lighting moves
# with the camera only through reflection/view direction, never image warping.
camera=scene.camera
scene.render.resolution_x=960;scene.render.resolution_y=1200;scene.cycles.samples=192
target=Vector((0,0,.057*10/7));distance=.69*10/7
for azimuth,elevation in [(135,45),(255,28)]:
    a=math.radians(azimuth);e=math.radians(elevation)
    camera.location=target+Vector((math.sin(a)*math.cos(e)*distance,-math.cos(a)*math.cos(e)*distance,math.sin(e)*distance))
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.shift_x=0;camera.data.shift_y=.02
    scene.render.filepath=str(ROOT/'renders'/f'eye_07_orbit_{azimuth}.png')
    start=time.time();bpy.ops.render.render(write_still=True)
    report['renders'].append({'file':f'renders/eye_07_orbit_{azimuth}.png','type':'orbit','azimuth':azimuth,'elevation':elevation,'seconds':time.time()-start})
    print('ORBIT_COMPLETE',azimuth,flush=True)
(ROOT/'reports'/'round_07_build.json').write_text(json.dumps(report,indent=2))
print('ROUND07_COMPLETE',flush=True)
