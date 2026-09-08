"""Validate actual geometry, rather than assumptions about generated profiles."""
import bpy, bmesh, json
from pathlib import Path


def audit(scene):
    result={}
    for obj in scene.objects:
        if obj.type!='MESH' or not obj.name.startswith(('Glass |','Liquid |','Garnish |','Ice |')):
            continue
        bm=bmesh.new();bm.from_mesh(obj.data)
        result[obj.name]={
            'vertices':len(bm.verts),'faces':len(bm.faces),
            'boundary_edges':sum(e.is_boundary for e in bm.edges),
            'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
            'signed_volume_m3':bm.calc_volume(signed=True),
            'dimensions_m':list(obj.dimensions),
        }
        bm.free()
    p=Path(__file__).resolve().parents[1]/'reports'/'geometry_audit.json'
    p.write_text(json.dumps(result,indent=2))
    return result
