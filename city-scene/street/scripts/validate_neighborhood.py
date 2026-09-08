import bpy, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
s=bpy.context.scene
assert s.name=='Copenhagen | FOUR CONNECTED STREETS'
registry=json.loads((ROOT/'reports'/'neighborhood_registry.json').read_text())
if isinstance(registry,dict):registry=registry.get('buildings',registry.get('registry',[]))
nav=json.loads((ROOT/'reports'/'neighborhood_navigation.json').read_text())
collisions=[];points=[]
for a,b in zip(nav['route_points'],nav['route_points'][1:]):
    a=Vector(a);b=Vector(b)
    for i in range(max(2,math.ceil((b-a).length/.5))):
        p=a.lerp(b,i/max(1,math.ceil((b-a).length/.5)-1));points.append(p)
        for block in registry:
            ox,oy,_=block['origin'];r=block['rotation'];dx=p.x-ox;dy=p.y-oy
            x=math.cos(r)*dx+math.sin(r)*dy;y=-math.sin(r)*dx+math.cos(r)*dy
            if abs(x)<block['width']/2-.04 and .04<y<block['depth']-.04:collisions.append([tuple(p),block['id']])
nav_lines=[o for o in s.objects if o.type=='CURVE' and ('LOOP |' in o.name or 'route |' in o.name)]
for o in nav_lines:o.hide_viewport=True
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
ground_issues=[]
for p in points:
    hit,pos,normal,index,obj,matrix=s.ray_cast(deps,Vector((p.x,p.y,.55)),Vector((0,0,-1)),distance=1)
    if not hit or abs(pos.z-.18)>.045:ground_issues.append({'point':list(p),'height':pos.z if hit else None,'object':obj.name if hit else None})
road_checks=[]
for x,y in [(64,-40),(64,-35),(64,52),(64,47),(64,5)]:
    hit,pos,normal,index,obj,matrix=s.ray_cast(deps,Vector((x,y,.5)),Vector((0,0,-1)),distance=1)
    road_checks.append({'xy':[x,y],'hit':hit,'z':pos.z if hit else None,'object':obj.name if hit else None})
for o in nav_lines:o.hide_viewport=False
missing=[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file and i.filepath and not Path(bpy.path.abspath(i.filepath)).exists()]
report={'file':bpy.data.filepath,'streets':4,'buildings':len(registry),'loop_closed':nav['route_points'][0]==nav['route_points'][-1],'loop_length_m':nav['length_m'],'walking_surface_samples':len(points),'building_collisions':collisions,'walking_surface_issues':ground_issues,'road_junctions':road_checks,'missing_images':missing,'camera_count':sum(o.type=='CAMERA' for o in s.objects),'renders':[p.name for p in (ROOT/'renders').glob('neighborhood_*.png')]}
assert not collisions,collisions[:10]
assert not ground_issues,ground_issues[:10]
assert not missing
assert all(r['hit'] and abs(r['z'])<.025 for r in road_checks),road_checks
assert report['loop_closed']
assert len(report['renders'])>=5
report['status']='PASS';(ROOT/'reports'/'neighborhood_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
