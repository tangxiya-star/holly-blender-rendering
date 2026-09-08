import bpy, math, json
from common import *
import architecture

def finish_context():
    registry=json.loads((ROOT/'reports'/'building_registry.json').read_text())
    palette=architecture._palette()
    for side in [-1,1]:
        for cy in [-40,52]:
            ident=f'Context_end_{side}_{cy}'
            spec={'id':ident,'origin':[side*94,cy,.18],'rotation':math.pi/2 if side<0 else -math.pi/2,'width':26.,'height':12.8,'depth':10,'floors':4,'seed':9001+cy+side,'style':'brick' if cy==52 else 'plaster','color':[.47,.36,.25] if cy==52 else [.48,.47,.40],'shop':'BOGHANDEL' if cy==52 else 'KAFFE'}
            if not bpy.data.objects.get('Building_'+ident):architecture._build_one(spec,palette)
            if not any(x['id']==ident for x in registry):registry.append(spec)
            for sign in [-1,1]:
                name=f'Context_return_walk_{side}_{cy}_{sign}'
                if not bpy.data.objects.get(name):box(name,(side*86.5,cy+sign*4.35,.09),(15,2.3,.18),'Context',material_noise('Context_paving',(.29,.30,.29),70,.88,.002))
            name=f'Context_road_extension_{side}_{cy}'
            if not bpy.data.objects.get(name):box(name,(side*87,cy,-.09),(14,6.4,.18),'Context',bpy.data.materials['CPH_Surface_Asphalt'])
    (ROOT/'reports'/'building_registry.json').write_text(json.dumps(registry,indent=2))
    cam=bpy.data.objects['03 | Establishing'];cam.location=(3,-12,19);cam.data.lens=32;aim(cam,(0,46,3))
