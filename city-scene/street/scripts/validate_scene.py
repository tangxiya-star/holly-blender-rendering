import bpy, json, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
s=bpy.context.scene
assert s.name.startswith('Copenhagen')
registry=json.loads((ROOT/'reports'/'building_registry.json').read_text())
nav=json.loads((ROOT/'reports'/'navigation.json').read_text())
collisions=[]
for i in range(len(nav['route'])-1):
    a=Vector(nav['route'][i]['position']);b=Vector(nav['route'][i+1]['position'])
    for j in range(21):
        p=a.lerp(b,j/20)
        for block in registry:
            ox,oy,_=block['origin'];r=block['rotation'];dx=p.x-ox;dy=p.y-oy
            x=math.cos(r)*dx+math.sin(r)*dy;y=-math.sin(r)*dx+math.cos(r)*dy
            if abs(x)<block['width']/2-.02 and .02<y<block['depth']-.02:collisions.append([i,j,block['id']])
missing=[]
for im in bpy.data.images:
    if im.source=='FILE' and not im.packed_file and im.filepath and not Path(bpy.path.abspath(im.filepath)).exists():missing.append(im.filepath)
cameras=[{'name':o.name,'lens_mm':o.data.lens,'position':list(o.location)} for o in s.objects if o.type=='CAMERA']
report={'scene':s.name,'file':bpy.data.filepath,'engine':s.render.engine,'metric_scale':s.unit_settings.scale_length,'buildings':len(registry),'scene_objects':len(s.objects),'mesh_objects':sum(o.type=='MESH' for o in s.objects),'mesh_faces':sum(len(o.data.polygons) for o in s.objects if o.type=='MESH'),'materials':len(bpy.data.materials),'bicycle_instances':sum(o.get('asset_type')=='upright_city_bicycle' for o in s.objects),'cameras':cameras,'walk_route_building_collisions':collisions,'missing_external_images':missing,'packed_images':[i.name for i in bpy.data.images if i.packed_file],'poi_targets':[{'name':o.name,'position':list(o.location),'destination':o.get('destination')} for o in bpy.data.collections['POI_Targets'].objects],'renders':{p.name:p.stat().st_size for p in (ROOT/'renders').glob('copenhagen_*.png')},'limitations':['Blender native walk/fly navigation and camera previews; no game controller or full collision physics.','Destination interiors are deferred.','Representative street plan, not a geographic digital twin.','Photographic realism remains a visual approval decision; see ranked critique.']}
assert not collisions,collisions
assert not missing,missing
assert len(cameras)>=7
assert report['bicycle_instances']==26
assert len(report['renders'])>=5
assert len(bpy.data.collections['Architecture_Corner_Returns'].objects)>0
assert len(json.loads((ROOT/'reports'/'corner_returns_report.json').read_text()))==8
assert len([o for o in s.objects if o.name.startswith('Building_Context_end_') and o.type=='EMPTY'])==4
assert 'asphalt_02_diff_2k.jpg' in report['packed_images']
report['status']='PASS'
(ROOT/'reports'/'final_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
