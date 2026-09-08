"""Conservative seam cleanup for the reconstructed eye's enclosing surfaces.

Works on a loaded scene. It changes only coincident topology, never fills the
intentional body/iris/well interface loops, and excludes all fiber ribbons.
UV coordinates and material indices are retained as per-loop / per-face data.
"""
import bpy
import bmesh
import math
from mathutils import Vector


WELD_DISTANCE_LOCAL_M=1e-7
DEGENERATE_DISTANCE_LOCAL_M=1e-10

# Exact stable prefixes are intentionally narrower than "Eye" or "Blue iris".
TARGET_PREFIXES=(
    'Eye vessel | continuous pale body and flattened contact base',
    'Blue iris | recessed layered stromal foundation',
    'Eye iris | shallow closed clear cast-resin encasement',
    'Eye vessel | recessed central food opening',
)


def _bounds(points):
    if not points:return {'min':[0.0]*3,'max':[0.0]*3}
    return {'min':[min(p[i] for p in points) for i in range(3)],
            'max':[max(p[i] for p in points) for i in range(3)]}


def _delta(a,b):
    return max(abs(a[k][i]-b[k][i]) for k in ('min','max') for i in range(3))


def _boundary_components(bm):
    remaining={e for e in bm.edges if e.is_boundary}
    components=[]
    while remaining:
        start=remaining.pop();stack=[start];edges={start};verts=set(start.verts)
        while stack:
            edge=stack.pop()
            for vertex in edge.verts:
                for neighbor in vertex.link_edges:
                    if neighbor in remaining and neighbor.is_boundary:
                        remaining.remove(neighbor);stack.append(neighbor)
                        edges.add(neighbor);verts.update(neighbor.verts)
        degrees={v:sum(e in edges for e in v.link_edges) for v in verts}
        components.append({'edges':len(edges),'vertices':len(verts),
                           'closed_loop':all(d==2 for d in degrees.values()),
                           'local_bounds':_bounds([v.co.copy() for v in verts])})
    return sorted(components,key=lambda x:(x['local_bounds']['min'][2],x['edges']))


def _stats(bm):
    tiny=DEGENERATE_DISTANCE_LOCAL_M
    return {'vertices':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces),
            'zero_length_edges':sum(e.calc_length()<=tiny for e in bm.edges),
            'degenerate_faces':sum(f.calc_area()<=tiny*tiny for f in bm.faces),
            'boundary_edges':sum(e.is_boundary for e in bm.edges),
            'wire_edges':sum(e.is_wire for e in bm.edges),
            'nonmanifold_nonboundary_edges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges),
            'boundary_components':_boundary_components(bm),
            'local_bounds':_bounds([v.co.copy() for v in bm.verts]),
            'uv_layers':list(bm.loops.layers.uv.keys()),
            'material_indices':sorted({f.material_index for f in bm.faces})}


def cleanup_orbit_geometry(scene):
    """Weld only four enclosing-surface types and return a JSON-safe audit.

    No save, UI operation, decimation, triangulation, hole fill or new material
    is performed. The caller chooses the working copy and save destination.
    """
    selected=[obj for obj in scene.objects if obj.type=='MESH' and
              any(obj.name.startswith(prefix) for prefix in TARGET_PREFIXES)]
    report={'operation':'Conservative coincident seam weld and degenerate cleanup',
            'weld_distance_local_m':WELD_DISTANCE_LOCAL_M,
            'dissolve_degenerate_distance_local_m':DEGENERATE_DISTANCE_LOCAL_M,
            'selection_prefixes':list(TARGET_PREFIXES),'objects':[],
            'holes_filled':False,'decimation':False,'fiber_ribbons_untouched':True,
            'status':'passed'}
    found={prefix:any(o.name.startswith(prefix) for o in selected) for prefix in TARGET_PREFIXES}
    report['missing_expected_prefixes']=[p for p,yes in found.items() if not yes]
    if report['missing_expected_prefixes']:
        report['status']='review'
    for obj in selected:
        mesh=obj.data
        before_material_names=[m.name if m else None for m in mesh.materials]
        before_world=_bounds([obj.matrix_world@v.co for v in mesh.vertices])
        bm=bmesh.new();bm.from_mesh(mesh)
        try:
            before=_stats(bm)
            # Custom data (including UV loops) is maintained by the BMesh ops.
            # This threshold is far below the 15–380 μm physical layer spacing.
            bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=WELD_DISTANCE_LOCAL_M)
            bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),
                                          dist=DEGENERATE_DISTANCE_LOCAL_M)
            degenerate=[f for f in bm.faces if len(f.verts)<3 or
                        f.calc_area()<=DEGENERATE_DISTANCE_LOCAL_M**2]
            if degenerate:
                bmesh.ops.delete(bm,geom=degenerate,context='FACES_ONLY')
            # Remove only newly unreferenced zero-length remnants, not boundary
            # edges. The intended annuli remain open at their interfaces.
            wires=[e for e in bm.edges if e.is_wire and e.calc_length()<=DEGENERATE_DISTANCE_LOCAL_M]
            if wires:bmesh.ops.delete(bm,geom=wires,context='EDGES')
            loose=[v for v in bm.verts if not v.link_edges and not v.link_faces]
            if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
            if bm.faces:bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
            bm.normal_update()
            after=_stats(bm)
            local_drift=_delta(before['local_bounds'],after['local_bounds'])
            after_world=_bounds([obj.matrix_world@v.co for v in bm.verts])
            world_drift=_delta(before_world,after_world)
            # Check preservation before committing the temporary BMesh.
            if local_drift>WELD_DISTANCE_LOCAL_M*1.01:
                raise RuntimeError(obj.name+': bounds changed beyond the weld tolerance')
            if before['uv_layers']!=after['uv_layers']:
                raise RuntimeError(obj.name+': UV layer names changed')
            if not set(after['material_indices']).issubset(before['material_indices']):
                raise RuntimeError(obj.name+': unexpected material assignment')
            warnings=[]
            if after['degenerate_faces'] or after['zero_length_edges']:
                warnings.append('Degenerate topology remains')
            if 'cast-resin encasement' in obj.name and after['boundary_edges']:
                warnings.append('The resin volume unexpectedly has boundary edges')
            if 'cast-resin encasement' not in obj.name:
                if any(not c['closed_loop'] for c in after['boundary_components']):
                    warnings.append('A remaining interface boundary is not a closed loop')
            if after['nonmanifold_nonboundary_edges']:
                warnings.append('Non-manifold interior edges remain')
            # Avoid changing another object's linked mesh data accidentally.
            if mesh.users>1:
                mesh=mesh.copy();obj.data=mesh
            bm.to_mesh(mesh);mesh.update()
            if before_material_names!=[m.name if m else None for m in mesh.materials]:
                raise RuntimeError(obj.name+': material slots changed')
            entry={'object':obj.name,'before':before,'after':after,
                   'vertices_removed':before['vertices']-after['vertices'],
                   'faces_removed':before['faces']-after['faces'],
                   'maximum_local_bounds_difference_m':local_drift,
                   'maximum_world_bounds_difference_m':world_drift,
                   'uv_layers_preserved':True,'material_slots_preserved':True,
                   'warnings':warnings}
            report['objects'].append(entry)
            if warnings:report['status']='review'
        finally:
            bm.free()
    report['objects_processed']=len(report['objects'])
    report['vertices_removed']=sum(x['vertices_removed'] for x in report['objects'])
    report['remaining_degenerate_faces']=sum(x['after']['degenerate_faces'] for x in report['objects'])
    report['remaining_zero_length_edges']=sum(x['after']['zero_length_edges'] for x in report['objects'])
    report['maximum_world_bounds_difference_m']=max(
        [x['maximum_world_bounds_difference_m'] for x in report['objects']] or [0.0])
    return report
