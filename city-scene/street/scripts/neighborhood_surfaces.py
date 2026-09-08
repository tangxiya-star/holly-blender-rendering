"""Fourth street and precise openings through the two existing cross footways.

Call build_neighborhood_surfaces() after loading the finished scene.  Existing
material nodes and per-corner texture coordinates are retained by the cuts.
"""
import bpy
import random
from surfaces import _Batch, _paving, _kerb_run, _intervals, _bicycle_mark, _drain, _manhole

JUNCTIONS = (-40.0, 52.0)


def _half_plane(poly, axis, limit, keep_greater):
    """Clip (local point, world point, UV tuples) vertices; interpolate UVs."""
    if not poly:
        return []
    out = []
    previous = poly[-1]
    before = previous[1][axis] >= limit if keep_greater else previous[1][axis] <= limit
    for current in poly:
        after = current[1][axis] >= limit if keep_greater else current[1][axis] <= limit
        if after != before:
            t = (limit - previous[1][axis]) / (current[1][axis] - previous[1][axis])
            local = tuple(a + t * (b-a) for a, b in zip(previous[0], current[0]))
            world = tuple(a + t * (b-a) for a, b in zip(previous[1], current[1]))
            uvs = tuple(tuple(a+t*(b-a) for a,b in zip(uv0,uv1))
                        for uv0,uv1 in zip(previous[2],current[2]))
            out.append((local, world, uvs))
        if after:
            out.append(current)
        previous, before = current, after
    # Clipped vertical faces can collapse to repeated vertices on the boundary.
    clean = []
    for vertex in out:
        if not clean or sum((a-b)**2 for a,b in zip(vertex[0],clean[-1][0])) > 1e-16:
            clean.append(vertex)
    if len(clean)>1 and sum((a-b)**2 for a,b in zip(clean[0][0],clean[-1][0])) < 1e-16:
        clean.pop()
    return clean if len(clean) >= 3 else []


def _subtract_rectangle(poly, rect):
    x0,x1,y0,y1 = rect
    xs = [v[1][0] for v in poly]
    ys = [v[1][1] for v in poly]
    if max(xs) <= x0 or min(xs) >= x1 or max(ys) <= y0 or min(ys) >= y1:
        return [poly]
    # Four disjoint exterior strips; the final interior is discarded.
    result = []
    rest = poly
    for axis, limit, outside_greater in ((0,x0,False),(0,x1,True),(1,y0,False),(1,y1,True)):
        outside = _half_plane(rest, axis, limit, outside_greater)
        if outside:
            result.append(outside)
        rest = _half_plane(rest, axis, limit, not outside_greater)
        if not rest:
            break
    return result


def _cut_existing_pavements(rectangles):
    original = bpy.data.collections.get('CPH_Street_Surfaces')
    if original is None:
        raise RuntimeError('The original CPH_Street_Surfaces collection must exist')
    edited = []
    for obj in list(original.objects):
        if obj.type != 'MESH' or not obj.data.materials:
            continue
        mat_name = obj.data.materials[0].name
        if not any(mat_name.startswith('CPH_Surface_' + key)
                   for key in ('Slab_', 'Sett_', 'Kerb_', 'Joint_bed')):
            continue
        source = obj.data
        vertices, faces, face_uvs, material_ids, smooth = [], [], [], [], []
        layers = list(source.uv_layers)
        matrix = obj.matrix_world
        changed = 0
        for face in source.polygons:
            poly = []
            for index in face.loop_indices:
                point = source.vertices[source.loops[index].vertex_index].co
                poly.append((tuple(point), tuple(matrix @ point),
                             tuple(tuple(layer.data[index].uv) for layer in layers)))
            pieces = [poly]
            for rect in rectangles:
                pieces = [piece for p in pieces for piece in _subtract_rectangle(p, rect)]
            if len(pieces) != 1 or pieces[0] != poly:
                changed += 1
            for piece in pieces:
                first = len(vertices)
                vertices.extend(v[0] for v in piece)
                faces.append(tuple(range(first, first+len(piece))))
                face_uvs.append([v[2] for v in piece])
                material_ids.append(face.material_index)
                smooth.append(face.use_smooth)
        if not changed:
            continue
        mesh = bpy.data.meshes.new(source.name + '_FourthStreetOpenings')
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        for material in source.materials:
            mesh.materials.append(material)
        for layer_index, source_layer in enumerate(layers):
            destination = mesh.uv_layers.new(name=source_layer.name)
            for face, uvs in zip(mesh.polygons, face_uvs):
                for loop_index, corner in zip(face.loop_indices, uvs):
                    destination.data[loop_index].uv = corner[layer_index]
            destination.active_render = source_layer.active_render
        for face, material_id, use_smooth in zip(mesh.polygons, material_ids, smooth):
            face.material_index = material_id
            face.use_smooth = use_smooth
        obj.data = mesh
        if source.users == 0:
            bpy.data.meshes.remove(source)
        edited.append({'object': obj.name, 'cut_faces': changed})
    return edited


def build_neighborhood_surfaces():
    """Add the eastern shared street at x=64; return measurable geometry data."""
    old = bpy.data.collections.get('CPH_Neighborhood_Surfaces')
    if old:
        for obj in list(old.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    collection = bpy.data.collections.new('CPH_Neighborhood_Surfaces')
    bpy.context.scene.collection.children.link(collection)
    collection['description'] = 'Fourth street: connected quiet residential street, shared cycling, accessible crossings'
    apertures = [(60.8,67.2,cy-5.51,cy+5.51) for cy in JUNCTIONS]
    # A 2.3 m transition at each side of both intersections lowers the east
    # pedestrian route from 18 cm to road level, without a vertical kerb.
    for cy in JUNCTIONS:
        apertures.extend([(68.1,70.4,cy-5.5,cy-3.2), (68.1,70.4,cy+3.2,cy+5.5)])
    edited = _cut_existing_pavements(apertures)
    batch, rng = _Batch(), random.Random(640409)
    for y0,y1 in _intervals(-56,68,[(cy-3.2,cy+3.2) for cy in JUNCTIONS]):
        batch.box('Asphalt',60.8,67.2,y0,y1,-.18,0)
    for y0,y1 in _intervals(-56,68,[(cy-5.5,cy+5.5) for cy in JUNCTIONS]):
        _paving(batch,rng,57,60.63,y0,y1)
        _paving(batch,rng,67.37,71,y0,y1)
        _kerb_run(batch,rng,60.63,60.8,y0,y1,.185)
        _kerb_run(batch,rng,67.2,67.37,y0,y1,.185)
    for cy in JUNCTIONS:
        for direction in (-1,1):
            near,far = cy+direction*3.2, cy+direction*5.5
            vertices = [(68.1,near,.005),(70.4,near,.005),(70.4,far,.18),(68.1,far,.18)]
            batch.mesh('Slab_2',vertices,[(0,1,2,3)] if direction==1 else [(3,2,1,0)])
        # Small crossing on the eastern walking route, uninterrupted by kerbs.
        for index in range(7):
            y0 = cy-2.96 + index*.90
            batch.quad('Road_paint',68.1,70.4,y0,y0+.40,.006)
    _bicycle_mark(batch,65.6,-15,1)
    _bicycle_mark(batch,62.4,28,-1)
    # The helper is specified for the original 7 cm cycle track. Move only its
    # stencil geometry onto this shared street, leaving crossing paint intact.
    paint_vertices = batch.data['Road_paint'][0]
    for i,(x,y,z) in enumerate(paint_vertices):
        if abs(z-.073)<1e-6:
            paint_vertices[i] = (x,y,.005)
    for y in (-27,8,37):
        _drain(batch,61.06,y)
        _drain(batch,66.94,y+2)
    _manhole(batch,64.4,13)
    mats = {}
    for key in batch.data:
        material = bpy.data.materials.get('CPH_Surface_'+key)
        if material is None:
            raise RuntimeError('Required existing surface material missing: '+key)
        mats[key] = material
    faces = batch.finish(collection,mats)
    for obj in collection.objects:
        obj.name = 'CPH_Neighborhood_' + obj.name.removeprefix('CPH_')
        obj['street_id'] = 'Oestergade'
    collection['road_width_m'] = 6.4
    collection['footway_width_m'] = 3.8
    collection['curb_level_m'] = .18
    collection['intersection_centres'] = '64,-40;64,52'
    return {'collection':collection.name,'faces':faces,'cut_existing':edited,
            'road_width_m':6.4,'sidewalk_width_m':3.8,'curb_ramps':4,
            'road_openings':[(64,cy-4.4,0) for cy in JUNCTIONS]+[(64,cy+4.4,0) for cy in JUNCTIONS],
            'pedestrian_crossings':[(69.25,cy,0) for cy in JUNCTIONS]}
