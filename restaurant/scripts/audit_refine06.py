import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
report={}
for file in ['alchemist_05_final.blend','alchemist_04c_review.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(R/file))
    s=bpy.context.scene
    report[file]={'objects':len(s.objects),'vertices':sum(len(o.data.vertices) for o in s.objects if o.type=='MESH'),'cameras':{o.name:{'location':list(o.location),'rotation':list(o.rotation_euler),'lens':o.data.lens} for o in s.objects if o.type=='CAMERA'},'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'location':list(o.location),'color':list(o.data.color)} for o in s.objects if o.type=='LIGHT'],'materials':[m.name for m in bpy.data.materials],'object_names':sorted(o.name for o in s.objects),'images':[{'name':i.name,'packed':bool(i.packed_file),'size':list(i.size)} for i in bpy.data.images]}
(R/'reports/refine06_baseline.json').write_text(json.dumps(report,indent=2))
print('AUDIT06',json.dumps({k:{kk:vv for kk,vv in v.items() if kk in ['objects','vertices','cameras']} for k,v in report.items()}))
