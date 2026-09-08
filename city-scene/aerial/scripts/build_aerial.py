import sys, json, time, traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import bpy
from aerial_common import palette, cycles, render
from aerial_surfaces import build_surfaces, build_vegetation, polygon_mesh
from aerial_lighting import build_lighting
from aerial_cameras import build_cameras, FLIGHT
from city_massing import build_city_massing

def progress(message):print('CPH_AERIAL: '+message,flush=True)

def build():
    start=time.time();progress('Loading real OSM geography')
    geo=json.loads((ROOT/'data'/'copenhagen_geo.json').read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene;s.name='Copenhagen | CITY AERIAL + World Labs descent'
    s.unit_settings.system='METRIC';s.unit_settings.length_unit='METERS'
    s['data_attribution']='© OpenStreetMap contributors, ODbL 1.0'
    s['coordinate_origin']='12.5683 E, 55.6761 N; local east north meters'
    s['scope']='Real coastline and building footprints; approximate heights and roof silhouettes; aerial LOD only'
    materials=palette();stats={}
    progress('Land, harbor, canals, road network')
    context_path=ROOT/'data'/'context_geography.json'
    if context_path.exists():
        context=json.loads(context_path.read_text())
        polygon_mesh('Regional real shoreline | distant context',context['land'],1.91,'01_Real_Geography',materials['ground'])
        stats['regional_context']=True
    stats['geography']=build_surfaces(geo,materials)
    progress('Batched footprint city massing')
    stats['buildings']=build_city_massing(geo,materials,target_xy=(1470,490),flight_points=[p[1][:2] for p in FLIGHT])
    progress('Instanced park canopy')
    stats['vegetation']=build_vegetation(geo,materials)
    progress('Landmark roof accents')
    try:
        from landmarks import build_landmarks
        stats['landmarks']=build_landmarks(materials)
    except ImportError:stats['landmarks']='pending'
    progress('Cinematic lighting and altitude dependent haze')
    stats['lighting']=build_lighting();stats['cameras']=build_cameras()
    cycles(64);s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG'
    s.render.use_motion_blur=True;s.render.motion_blur_shutter=.36
    for screen in bpy.data.screens:
        for a in screen.areas:
            if a.type=='VIEW_3D':
                a.spaces.active.clip_end=80000;a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.overlay.show_overlays=False
                a.spaces.active.shading.type='SOLID';a.spaces.active.shading.color_type='MATERIAL'
    txt=bpy.data.texts.new('READ ME | Copenhagen aerial + World Labs')
    txt.write('CITY SCALE COPENHAGEN\nReal OSM coast, harbor, canals and81,774 building footprints.\nCamera01 HERO. Camera05 CINEMATIC DIVE,frames1-673,24fps.\nFrame649 is the54m World Labs match frame. External World Labs footage is not included.\nUse rendered previews in renders/. Geometry is optimized for aerial use only.\nGeodata© OpenStreetMap contributors ODbL; sources and handoff metadata in reports/.\n')
    stats['build_seconds']=round(time.time()-start,2);stats['objects']=len(s.objects);stats['mesh_faces']=sum(len(o.data.polygons) for o in s.objects if o.type=='MESH')
    (ROOT/'reports'/'build_stats.json').write_text(json.dumps(stats,indent=2,default=str))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'copenhagen_aerial.blend'))
    progress('Saved aerial scene; rendering first Cycles hero')
    render(bpy.data.objects['01 | HERO - Copenhagen from the southeast'],'hero_initial.png',1440,32)
    progress('DONE')

if __name__=='__main__':
    try:build()
    except Exception:
        (ROOT/'reports'/'build_error.txt').write_text(traceback.format_exc());raise
