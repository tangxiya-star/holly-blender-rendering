"""Render/save utilities called from Blender MCP. No external render substitute."""
import bpy, json, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def configure(scene,width=1000,samples=384):
    scene.render.engine='CYCLES'
    scene.cycles.device='GPU'
    scene.cycles.samples=samples
    scene.cycles.use_adaptive_sampling=True
    scene.cycles.adaptive_threshold=.006
    scene.cycles.adaptive_min_samples=64
    scene.cycles.use_denoising=True
    scene.cycles.denoiser='OPENIMAGEDENOISE'
    scene.cycles.denoising_prefilter='ACCURATE'
    scene.cycles.max_bounces=24
    scene.cycles.transmission_bounces=20
    scene.cycles.glossy_bounces=12
    scene.cycles.diffuse_bounces=4
    scene.cycles.transparent_max_bounces=32
    scene.cycles.volume_bounces=2
    scene.cycles.sample_clamp_direct=0
    scene.cycles.sample_clamp_indirect=20
    scene.cycles.blur_glossy=.0
    scene.cycles.seed=90826
    scene.cycles.use_light_tree=True
    scene.cycles.caustics_reflective=True
    scene.cycles.caustics_refractive=True
    scene.cycles.pixel_filter_type='BLACKMAN_HARRIS'
    scene.cycles.filter_width=1.2
    scene.render.resolution_x=width
    scene.render.resolution_y=round(width*1.25)
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGB'
    scene.render.image_settings.color_depth='16'
    scene.render.film_transparent=False
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=0
    scene.view_settings.gamma=1


def save(scene,round_name):
    path=ROOT/f'cocktail_{round_name}.blend'
    # Write only the standalone new scene and dependencies. Previous scenes untouched.
    bpy.data.libraries.write(str(path),{scene},path_remap='ABSOLUTE',fake_user=True,compress=True)
    report={
      'scene':scene.name,'round':round_name,'blender':bpy.app.version_string,
      'engine':scene.render.engine,'device':scene.cycles.device,
      'resolution':[scene.render.resolution_x,scene.render.resolution_y],
      'samples':scene.cycles.samples,'transmission_bounces':scene.cycles.transmission_bounces,
      'objects':len(scene.objects),'camera_lens':scene.camera.data.lens,
      'fstop':scene.camera.data.dof.aperture_fstop,
      'lights':{o.name:{'energy':o.data.energy,'position':list(o.location),'color':list(o.data.color)} for o in scene.objects if o.type=='LIGHT'},
      'meshes':{o.name:{'vertices':len(o.data.vertices),'dimensions':list(o.dimensions)} for o in scene.objects if o.type=='MESH'},
    }
    (ROOT/'reports'/f'round_{round_name}.json').write_text(json.dumps(report,indent=2))
    return str(path)


def start(scene,round_name,width=1000,samples=384):
    configure(scene,width,samples)
    scene.render.filepath=str(ROOT/'renders'/f'cocktail_{round_name}.png')
    path=save(scene,round_name)
    bpy.ops.render.render('INVOKE_DEFAULT',write_still=True,scene=scene.name)
    return {'blend':path,'render':scene.render.filepath,'started':True}
