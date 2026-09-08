"""Finish the MCP-built scene in native Cycles and prepare a reviewable .blend."""
import bpy, math, sys, json, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import render_control
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
label=args[0] if args else '08'
width=int(args[1]) if len(args)>1 else 1000
samples=int(args[2]) if len(args)>2 else 512
s=bpy.context.scene
assert s.name.startswith('Cocktail |'),s.name
start=time.time()
back=bpy.data.objects['Cocktail_Stage_CurvedBackdrop']
for v in back.data.vertices:v.co.y=1.5
n=back.data.materials[0].node_tree.nodes
subs=[q for q in n if q.bl_idname=='ShaderNodeMath' and q.operation=='SUBTRACT']
divs=[q for q in n if q.bl_idname=='ShaderNodeMath' and q.operation=='DIVIDE']
subs[1].inputs[1].default_value=.49
divs[0].inputs[1].default_value=.34
divs[1].inputs[1].default_value=.65
# Precisely seat the annular foot against the table's z=0 contact plane.
g=bpy.data.objects['Glass | Antini hand-drawn coupe']
for v in g.data.vertices:
    if v.co.z<.0015:v.co.z-=.0001*max(0,1-(v.co.z-.0001)/.0014)
# Existing restaurant panorama contributes only a quiet, irregular room return.
p=ROOT.parent/'restaurant'/'textures'/'restaurant_environment.exr'
im=bpy.data.images.load(str(p),check_existing=True)
import numpy as np
px=np.asarray(im.pixels[:],dtype=np.float32).reshape(-1,4)
mean=float(np.mean(px[:,:3]@np.array([.2126,.7152,.0722])))
wn=s.world.node_tree.nodes;wl=s.world.node_tree.links
bg=wn['Background'];env=wn.new('ShaderNodeTexEnvironment');env.image=im
coord=wn.new('ShaderNodeTexCoord');mapping=wn.new('ShaderNodeMapping')
mapping.inputs['Rotation'].default_value[2]=math.radians(38)
wl.new(coord.outputs['Generated'],mapping.inputs['Vector'])
# Environment coordinates use world direction; Generated is supported for World.
wl.new(mapping.outputs['Vector'],env.inputs['Vector']);wl.new(env.outputs['Color'],bg.inputs['Color'])
bg.inputs['Strength'].default_value=min(.12,.008/max(mean,.0001))
im.pack()
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
render_control.configure(s,width,samples)
s.cycles.adaptive_threshold=.004 if width>1200 else .006
s.cycles.adaptive_min_samples=128 if width>1200 else 64
s.cycles.device='GPU' if any(d.use for d in prefs.devices) else 'CPU'
s.render.filepath=str(ROOT/'renders'/f'cocktail_{label}.png')
bpy.context.view_layer.update()
# Save native file first so completed modeling is retained even if renderer fails.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'cocktail_{label}.blend'))
print('COCKTAIL_RENDER_START',label,s.cycles.device,width,samples,flush=True)
bpy.ops.render.render(write_still=True)
s.render.image_settings.file_format='OPEN_EXR';s.render.image_settings.color_depth='16'
bpy.data.images['Render Result'].save_render(str(ROOT/'renders'/f'cocktail_{label}_linear.exr'),scene=s)
s.render.image_settings.file_format='PNG'
# The reference environment is an existing project render, not a new stock asset.
im.save_render(str(ROOT/'references'/'restaurant_environment_preview.png'),scene=s)
# Model view opens in the hero camera with real materials/lighting, no overlays.
for scr in bpy.data.screens:
    for a in scr.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_perspective='CAMERA'
            a.spaces.active.region_3d.view_camera_zoom=10
            a.spaces.active.overlay.show_overlays=False
            a.spaces.active.shading.type='RENDERED'
s.cycles.preview_samples=48;s.cycles.use_preview_denoising=True
# Pack the finished image, available in Blender's image-editor dropdown.
review=bpy.data.images.load(s.render.filepath,check_existing=True);review.name='Cocktail | FINAL HERO';review.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'cocktail_{label}.blend'))
metrics={'label':label,'resolution':[s.render.resolution_x,s.render.resolution_y],
'samples':samples,'device':s.cycles.device,'seconds':time.time()-start,'objects':len(s.objects),
'world_source':str(p),'world_luminance_mean':mean,'world_strength':bg.inputs['Strength'].default_value,
'camera_lens_mm':s.camera.data.lens,'aperture_fstop':s.camera.data.dof.aperture_fstop}
(ROOT/'reports'/f'round_{label}_final.json').write_text(json.dumps(metrics,indent=2))
print('COCKTAIL_RENDER_COMPLETE',json.dumps(metrics),flush=True)
