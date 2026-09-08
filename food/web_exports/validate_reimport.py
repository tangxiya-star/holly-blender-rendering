import bpy, json, hashlib, math, time
from pathlib import Path
from mathutils import Vector
import numpy as np
out=Path(__file__).resolve().parent
report=json.loads((out/'web_asset_report.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
started=time.time()
bpy.ops.import_scene.gltf(filepath=str(out/'food_web.gltf'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
triangles=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons)
assert triangles==report['geometry']['exported_triangles'], (triangles,report['geometry']['exported_triangles'])
assert len(meshes)==report['geometry']['source_mesh_objects']
points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
bounds={'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
original=report['geometry']['bounds_blender_Z_up_m']
delta=max(abs(bounds[k][i]-original[k][i]) for k in ['min','max'] for i in range(3))
assert delta<.00001,delta
audits=[]
for o in meshes:
    attrs=list(o.data.color_attributes)
    assert attrs, o.name+' has no baked colors after reimport'
    color=attrs[0]
    values=np.empty(len(color.data)*4,dtype=np.float32)
    color.data.foreach_get('color',values)
    values=values.reshape((-1,4))
    assert np.isfinite(values).all()
    assert values[:,:3].max()>0
    audits.append({'name':o.name,'color_attribute':color.name,'domain':color.domain,
                   'rgb_min':values[:,:3].min(axis=0).tolist(),'rgb_max':values[:,:3].max(axis=0).tolist()})
source=out.parent/'food_final.blend'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash==report['source_sha256_before']
validation={'status':'passed','imported_entry':'food_web.gltf','objects':len(meshes),'triangles':triangles,
            'materials':len(bpy.data.materials),'baked_color_objects':len(audits),
            'bounds_blender_Z_up_m':bounds,'maximum_bounds_difference_m':delta,
            'source_unchanged':True,'seconds':time.time()-started,'objects_color_audit':audits}
report['reimport_validation']=validation
(out/'web_asset_report.json').write_text(json.dumps(report,indent=2))
(out/'reimport_validation.json').write_text(json.dumps(validation,indent=2))
print('WEB_REIMPORT_PASSED',json.dumps({k:v for k,v in validation.items() if k!='objects_color_audit'}),flush=True)
