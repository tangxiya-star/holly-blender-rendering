import bpy,sys,runpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'alchemist_web.glb'))
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1;s.render.fps=24
s.frame_start=0;s.frame_end=1440;s.frame_set(0)
s['reimport_source']=str(ROOT/'alchemist_web.glb')
sys.argv=['blender','--','--report',str(ROOT/'reports'/'web_reimport_validation.json')]
runpy.run_path(str(ROOT/'scripts'/'validate_scene.py'),run_name='__main__')
world=bpy.data.worlds.new('Delivered HDR environment');world.use_nodes=True;s.world=world
n=world.node_tree.nodes;l=world.node_tree.links
tex=n.new('ShaderNodeTexEnvironment');tex.image=bpy.data.images.load(str(ROOT/'textures'/'restaurant_environment.exr'))
l.new(tex.outputs['Color'],n.get('Background').inputs['Color']);n.get('Background').inputs['Strength'].default_value=.7
s.camera=bpy.data.objects['CAM_Hero'];s.render.engine='CYCLES';s.cycles.samples=40;s.cycles.use_denoising=True
s.cycles.max_bounces=8;s.view_settings.view_transform='AgX';s.view_settings.exposure=.5
s.render.resolution_x=1200;s.render.resolution_y=675;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.filepath=str(ROOT/'renders'/'web_reimport_hero.png')
bpy.ops.render.render(write_still=True)
print('GLB REIMPORT: structural and full animation-path validation complete; HDR-lit audit render saved')
