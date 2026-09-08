"""High detail entrance and interior pass; preserves all previous milestones."""
import bpy,sys,json,time,hashlib,shutil,argparse
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from common import camera,aim
from refine06_surfaces import bronze_materials,interior_materials,lighting_refine,entry_lighting
from refine06_furniture import refine_furniture
from refine06_door import build_door

parser=argparse.ArgumentParser();parser.add_argument('--render',default='entry');parser.add_argument('--load');parser.add_argument('--quality',action='store_true');parser.add_argument('--pass-b',action='store_true')
a=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
start=time.time()
assert bpy.app.background,'Isolated source build only'
if a.load:
    bpy.ops.wm.open_mainfile(filepath=str(R/a.load));s=bpy.context.scene
else:
    source=R/'alchemist_05_final.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene
    report={'source':'alchemist_05_final.blend','source_sha256':digest,'reference':'references/door_refine06/user_entrance_eatweek.jpg','reference_interpretation':'Photo-guided bronze relief reconstruction; unseen geometry and exact dimensions inferred. Real editable geometry, no photo cards.'}
    materials=bronze_materials();report['door']=build_door(materials)
    report['furniture']=refine_furniture(s);report['materials']=interior_materials(s);report['lighting']=lighting_refine(s);entry_lighting(s,materials)
    camera('CAM_Entry_Hero',(-.18,-26.5,2.47),(0,-19.03,2.20),58)
    camera('CAM_Entry_Detail',(1.05,-21.30,2.90),(-.42,-19.16,2.73),72)
    camera('CAM_Entry_Oblique',(3.25,-25.2,2.50),(0,-19.03,2.20),55)
    if a.pass_b:
        from refine06_entry_finish import apply_entry_finish
        report['entry_second_review_fixes']=apply_entry_finish(s)
    s.name='Alchemist | refined bronze entrance and dining'
    s['refinement']='06: sculpted hinged bronze entrance, upholstery, mineral stone, practical lighting'
    s['entry_animation']='Door hinges closed at frames1–40, open85 onward. WALKTHROUGH remains1–1441.'
    s['door_reference']='https://eatweekguide.com/alchemist/ ; user Google shared front photo'
    if not a.pass_b:s['door_dimensions']='4.15m leaf height,3.2m opening width retained for existing inferred scene. Width not a site measurement.'
    s.camera=bpy.data.objects['CAM_Entry_Hero'];s.frame_set(1)
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    s.render.engine='CYCLES';s.cycles.device='GPU';s.cycles.samples=384;s.cycles.preview_samples=32
    s.cycles.use_denoising=True;s.cycles.use_preview_denoising=True;s.cycles.max_bounces=10;s.cycles.diffuse_bounces=4;s.cycles.glossy_bounces=5;s.cycles.transmission_bounces=8
    s.render.resolution_x=1800;s.render.resolution_y=2160;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_depth='16'
    for screen in bpy.data.screens:
        for area in screen.areas:
            for space in area.spaces:
                if space.type=='VIEW_3D':
                    space.region_3d.view_perspective='CAMERA';space.region_3d.view_camera_zoom=8
                    space.shading.type='RENDERED';space.overlay.show_overlays=False
    outname='alchemist_06b_refine.blend' if a.pass_b else 'alchemist_06a_refine.blend'
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/outname))
    report['build_seconds']=time.time()-start;report['objects']=len(s.objects);report['total_base_vertices']=sum(len(o.data.vertices) for o in s.objects if o.type=='MESH')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    (R/('reports/refine06b_build.json' if a.pass_b else 'reports/refine06_build.json')).write_text(json.dumps(report,indent=2))
    snap=R/('reports/refine06b_sources' if a.pass_b else 'reports/refine06_sources');snap.mkdir(exist_ok=True)
    for name in ['build_refine06.py','refine06_surfaces.py','refine06_door.py','refine06_furniture.py','refine06_entry_finish.py']:shutil.copyfile(R/'scripts'/name,snap/name)
    print('REFINE06_SAVED',json.dumps({'objects':report['objects'],'vertices':report['total_base_vertices'],'seconds':report['build_seconds']}),flush=True)

jobs={'entry':('CAM_Entry_Hero',1,1100,1320),'detail':('CAM_Entry_Detail',1,1200,1200),'oblique':('CAM_Entry_Oblique',1,1100,1320),'open':('CAM_Arrival',110,1200,900),'hero':('CAM_Hero',110,1280,720),'table':('CAM_Table',110,1200,800),'dome':('CAM_Dome',110,1200,750)}
for key in a.render.split(','):
    if key=='none':continue
    name,frame,w,h=jobs[key];s.camera=bpy.data.objects[name];s.frame_set(frame)
    s.render.resolution_x=round(w*1.5) if a.quality else w;s.render.resolution_y=round(h*1.5) if a.quality else h
    s.cycles.samples=384 if a.quality else 96;s.cycles.adaptive_threshold=.01 if a.quality else .025
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_depth='16'
    tag=('final' if a.quality else 'review')+('_b' if a.pass_b else '')
    s.render.filepath=str(R/'renders'/f'refine06_{key}_{tag}.png')
    t=time.time();bpy.ops.render.render(write_still=True);print('REFINE06_RENDER',key,round(time.time()-t,2),flush=True)
