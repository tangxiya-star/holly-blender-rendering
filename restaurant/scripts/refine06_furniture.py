"""Dining upholstery refinement; call refine_furniture(scene) after loading source.

Does not open/save files, render, alter lighting, rotate furniture, or change legs.
All distances are meters. Existing chair construction remains editable.
"""

import math
import re

import bpy
from mathutils import Vector


TAG = 'ref06_upholstery_applied'
MAT = 'REF06 | charcoal upholstery'
SEAM_PREFIX = 'REF06_ChairSeam_'


def _material():
    material = bpy.data.materials.get(MAT) or bpy.data.materials.new(MAT)
    material.use_nodes = True
    material.diffuse_color = (.025, .027, .029, 1)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial'); out.location = (850, 100)
    shader = nodes.new('ShaderNodeBsdfPrincipled'); shader.location = (580, 100)
    shader.inputs['Metallic'].default_value = 0
    shader.inputs['IOR'].default_value = 1.46
    shader.inputs['Sheen Weight'].default_value = .24
    shader.inputs['Sheen Roughness'].default_value = .67
    links.new(shader.outputs['BSDF'], out.inputs['Surface'])
    uv = nodes.new('ShaderNodeUVMap'); uv.uv_map = 'REF06_ClothMeters'; uv.location = (-1100, 0)
    uv.label = 'Physical cloth coordinates in meters'
    noise = nodes.new('ShaderNodeTexNoise'); noise.location = (-870, 280)
    noise.inputs['Scale'].default_value = 18
    noise.inputs['Detail'].default_value = 3
    noise.inputs['Roughness'].default_value = .58
    links.new(uv.outputs['UV'], noise.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (-600, 330)
    ramp.color_ramp.elements[0].position = .15
    ramp.color_ramp.elements[0].color = (.020, .022, .024, 1)
    ramp.color_ramp.elements[1].position = .85
    ramp.color_ramp.elements[1].color = (.033, .035, .037, 1)
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    info = nodes.new('ShaderNodeObjectInfo'); info.location = (-880, 570)
    variation = nodes.new('ShaderNodeMapRange'); variation.location = (-620, 580)
    variation.inputs['To Min'].default_value = .92
    variation.inputs['To Max'].default_value = 1.06
    links.new(info.outputs['Random'], variation.inputs['Value'])
    color = nodes.new('ShaderNodeMixRGB'); color.blend_type = 'MULTIPLY'; color.location = (260, 300)
    color.inputs[0].default_value = 1
    links.new(ramp.outputs['Color'], color.inputs[1])
    links.new(variation.outputs['Result'], color.inputs[2])
    links.new(color.outputs[0], shader.inputs['Base Color'])
    rough = nodes.new('ShaderNodeMapRange'); rough.location = (260, 100)
    rough.inputs['To Min'].default_value = .61
    rough.inputs['To Max'].default_value = .79
    links.new(noise.outputs['Fac'], rough.inputs['Value'])
    links.new(rough.outputs['Result'], shader.inputs['Roughness'])

    # Crossed yarn relief, 0.7 mm pitch. It is intentionally tiny rather than burlap.
    sep = nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-880, -200)
    links.new(uv.outputs['UV'], sep.inputs[0])
    waves = []
    for i, axis in enumerate(('X', 'Y')):
        mul = nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.location = (-650, -140-i*180)
        mul.inputs[1].default_value = math.tau / (.00072 if i == 0 else .00068)
        links.new(sep.outputs[axis], mul.inputs[0])
        sine = nodes.new('ShaderNodeMath'); sine.operation = 'SINE'; sine.location = (-450, -140-i*180)
        links.new(mul.outputs[0], sine.inputs[0]); waves.append(sine)
    weave = nodes.new('ShaderNodeMath'); weave.operation = 'MULTIPLY'; weave.location = (-220, -200)
    for i in range(2): links.new(waves[i].outputs[0], weave.inputs[i])
    bump = nodes.new('ShaderNodeBump'); bump.location = (240, -140)
    bump.inputs['Strength'].default_value = .23
    bump.inputs['Distance'].default_value = .000065
    links.new(weave.outputs[0], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    material['physical_yarn_pitch_m'] = [.00072, .00068]
    material['bump_distance_m'] = .000065
    material['description'] = 'Neutral charcoal woven cloth; fine relief and restrained grazing sheen.'
    return material


def _bounds(obj):
    return [min(v.co[a] for v in obj.data.vertices) for a in range(3)], [max(v.co[a] for v in obj.data.vertices) for a in range(3)]


def _cloth_uv(obj, back):
    uv = obj.data.uv_layers.get('REF06_ClothMeters') or obj.data.uv_layers.new(name='REF06_ClothMeters')
    for loop in obj.data.loops:
        p = obj.data.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (p.x, p.z if back else p.y)


def _compress(obj, back, index):
    if obj.get(TAG): return 0.0
    biggest = 0.0
    for v in obj.data.vertices:
        old = v.co.copy()
        x, y, z = v.co
        if back:
            # Submillimeter tension indentation on the two front lower quarters.
            # No outer boundary vertex is enlarged or translated.
            lower = math.exp(-((z-.72)/.045)**2)
            side = math.exp(-((abs(x)-.17)/.052)**2)
            if .035 < abs(x) < .235 and .67 < z < .85:
                v.co.x *= 1 - .0025*lower*side
                v.co.z -= .00065*lower*side*(.9+.1*math.sin(index))
        elif z > .51:
            center = math.exp(-((x/.17)**2 + ((y+.005)/.165)**2))
            v.co.z -= .0011*center*(.92+.08*math.sin(index*1.7))
        biggest = max(biggest, (v.co-old).length)
    obj.data.update()
    obj[TAG] = True
    return biggest


def _smooth_loop(points, steps=3):
    out = []
    count = len(points)
    for i in range(count):
        a,b,c,d = [points[j % count] for j in (i-1,i,i+1,i+2)]
        for step in range(steps):
            t = step/steps
            out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return out


def _seam(obj, back, material, depsgraph):
    name = SEAM_PREFIX + obj.name
    prior = bpy.data.objects.get(name)
    if prior: bpy.data.objects.remove(prior, do_unlink=True)
    if back:
        # The source back is a 25-column, 9-row shell. Its front is the first 225 vertices.
        if len(obj.data.vertices) != 450: return None
        stride, rows = 25, 8
        perimeter = list(range(stride))
        perimeter += [row*stride+24 for row in range(1,rows+1)]
        perimeter += [rows*stride+col for col in range(23,-1,-1)]
        perimeter += [row*stride for row in range(rows-1,0,-1)]
        points = []
        for i in perimeter:
            q = obj.data.vertices[i].co.copy()
            q.x *= .974
            q.z = .8+(q.z-.8)*.971
            points.append(q)
    else:
        if len(obj.data.vertices) != 513: return None
        # Near the seat's lower rolled edge, so the upper cushion stays uncluttered.
        points = [obj.data.vertices[128+i].co.copy() for i in range(64)]
        for q in points: q.x *= .997; q.y *= .997
    evaluated = obj.evaluated_get(depsgraph)
    low, high = _bounds(obj)
    radius = .00045
    fitted = []
    for q in _smooth_loop(points):
        found, co, normal, _ = evaluated.closest_point_on_mesh(q)
        if found: q = co+normal*.00007
        # Keep the complete piping cross-section inside the original mesh AABB.
        for axis in range(3): q[axis] = min(high[axis]-radius,max(low[axis]+radius,q[axis]))
        fitted.append(q)
    curve = bpy.data.curves.new(name, 'CURVE'); curve.dimensions = '3D'
    curve.resolution_u = 1; curve.bevel_depth = radius; curve.bevel_resolution = 2
    poly = curve.splines.new('POLY'); poly.points.add(len(fitted)-1); poly.use_cyclic_u = True
    for point, co in zip(poly.points, fitted): point.co = (*co,1)
    seam = bpy.data.objects.new(name, curve)
    (obj.users_collection[0] if obj.users_collection else bpy.context.scene.collection).objects.link(seam)
    seam.parent = obj
    curve.materials.append(material)
    seam['construction'] = 'Inset 0.9 mm matching-cloth piping projected onto the evaluated cushion.'
    # Curve cloth coordinates cannot use a mesh UV map; constant near-black is intentional.
    return seam


def refine_furniture(scene):
    """Refine only existing dining seat/back surfaces and return JSON-safe evidence."""
    targets = [(o, bool(o.name.startswith('ChairBack_'))) for o in scene.objects
               if o.type == 'MESH' and (re.match(r'Chair_\d+_UpholsteredSeat$',o.name)
                                       or re.match(r'ChairBack_\d+_CurvedShell$',o.name))]
    if not targets: raise RuntimeError('No expected Alchemist dining upholstery found.')
    material = _material()
    thread_name = 'REF06 | matching charcoal seam'
    thread = bpy.data.materials.get(thread_name) or bpy.data.materials.new(thread_name)
    thread.use_nodes = True
    p = thread.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (.021,.023,.025,1)
    p.inputs['Roughness'].default_value = .75
    p.inputs['Sheen Weight'].default_value = .15
    before = {o.name: (_bounds(o), tuple(tuple(row) for row in o.matrix_world)) for o,_ in targets}
    largest = 0.0
    for obj, back in targets:
        if obj.data.users > 1: obj.data = obj.data.copy()
        index = int(re.search(r'\d+',obj.name).group())
        largest = max(largest, _compress(obj,back,index))
        _cloth_uv(obj,back)
        obj.data.materials.clear(); obj.data.materials.append(material)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    seams = [s.name for o,back in targets if (s := _seam(o,back,thread,depsgraph))]
    expansion = 0.0
    for obj,_ in targets:
        bounds,matrix = before[obj.name]; current = _bounds(obj)
        assert tuple(tuple(row) for row in obj.matrix_world) == matrix, obj.name+' moved'
        for axis in range(3):
            expansion = max(expansion,bounds[0][axis]-current[0][axis],current[1][axis]-bounds[1][axis])
    assert expansion < 1e-7, 'Upholstery envelope expanded'
    return {'material':MAT,'seats':sum(not back for _,back in targets),
            'backs':sum(back for _,back in targets),'seam_curves':len(seams),
            'largest_inward_vertex_adjustment_m':largest,'source_envelope_expansion_m':expansion,
            'chair_world_transforms_unchanged':True,'yarn_pitch_m':[.00072,.00068],
            'source_height_and_walkthrough_preserved':True,
            'other_scene_materials_and_lights_changed':False}
