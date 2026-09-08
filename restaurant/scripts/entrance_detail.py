"""Compact entry refinement; call add_entrance_detail(materials) from Blender.

Owns Entry_* objects only. Geometry is authored in world coordinates, then parented
without changing its transform. The door relief is an original rooted motif based
on the architectural character of the entrance reference, not its exact sculpture.
"""

import math


def _brick_geometry():
    """Running bond veneer with a 3 mm front chamfer; no bevel modifiers needed."""
    vertices, faces, slots = [], [], []
    count = 0
    pitch_x, pitch_z = .248, .083

    def brick(x0, x1, z0, z1, slot):
        nonlocal count
        if x1 - x0 < .014 or z1 - z0 < .010:
            return
        b = min(.003, (x1 - x0) / 5, (z1 - z0) / 5)
        # Exterior faces -Y. The veneer overlaps the original facade slightly.
        back, shoulder, front = -19.174, -19.201, -19.204
        corners = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        inset = [(x0+b, z0+b), (x1-b, z0+b),
                 (x1-b, z1-b), (x0+b, z1-b)]
        offset = len(vertices)
        vertices.extend((x, back, z) for x, z in corners)
        vertices.extend((x, shoulder, z) for x, z in corners)
        vertices.extend((x, front, z) for x, z in inset)
        local = [(3, 2, 1, 0), (8, 9, 10, 11)]
        for i in range(4):
            j = (i + 1) % 4
            local.extend([(i, j, j+4, i+4), (i+4, j+4, j+8, i+8)])
        faces.extend(tuple(offset+i for i in f) for f in local)
        slots.extend([slot] * len(local))
        count += 1

    for row in range(73):
        z0 = row * pitch_z
        z1 = min(z0 + .075, 6.0)
        if z0 >= 6:
            break
        shift = .124 if row % 2 else 0
        for col in range(-1, 39):
            x0 = max(-4.55, -4.55 + col*pitch_x - shift)
            x1 = min(4.55, -4.55 + col*pitch_x - shift + .24)
            if x1 <= x0:
                continue
            # Three restrained limestone tones, arranged deterministically.
            pattern = (row*11 + col*7) % 19
            slot = 1 if pattern in (0, 5, 12) else 2 if pattern in (3, 15) else 0
            if z0 >= 4.25:
                brick(x0, x1, z0, z1, slot)
            else:
                # Clip rather than bridge any part of the 3.5 m wide portal.
                brick(x0, min(x1, -1.75), z0, z1, slot)
                brick(max(x0, 1.75), x1, z0, z1, slot)
                if z1 > 4.25:
                    brick(max(x0, -1.75), min(x1, 1.75), 4.25, z1, slot)
    return vertices, faces, slots, count


def _smooth_path(points, subdivisions=3):
    """Clamped Catmull-Rom interpolation, in the door's local YZ plane."""
    result = []
    for i in range(len(points) - 1):
        p0, p1 = points[max(i-1, 0)], points[i]
        p2, p3 = points[i+1], points[min(i+2, len(points)-1)]
        for step in range(subdivisions):
            t = step / subdivisions
            result.append(tuple(.5*((2*p1[k]) + (-p0[k]+p2[k])*t
                + (2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*t*t
                + (-p0[k]+3*p1[k]-3*p2[k]+p3[k])*t*t*t)
                for k in range(2)))
    result.append(tuple(points[-1]))
    return result


def _relief_geometry(side):
    """All winding stems and raised bark veins for one leaf in a single mesh."""
    vertices, faces = [], []
    stem_count = 0

    def stem(points, width, phase=0, vein=False):
        nonlocal stem_count
        path = _smooth_path(points)
        offset = len(vertices)
        ring = 6 if vein else 8
        for i, (y, z) in enumerate(path):
            prev, nxt = path[max(0, i-1)], path[min(len(path)-1, i+1)]
            dy, dz = nxt[0]-prev[0], nxt[1]-prev[1]
            length = max(math.hypot(dy, dz), 1e-8)
            normal_y, normal_z = -dz/length, dy/length
            t = i / (len(path)-1)
            taper = .18 + .82 * math.sin(math.pi*(.10+.83*t))**.75
            in_plane = width*taper
            # Back half embeds into the leaf. Front stands roughly 10-40 mm
            # proud of its 1.515 m inward face, fading gently at branch tips.
            depth = (.026 + .030*taper) if not vein else .006
            center_x = 1.536 if not vein else 1.536-(.026+.030*taper)+.005
            for j in range(ring):
                a = 2*math.pi*j/ring
                fluting = 1 + .07*math.sin(3*a + phase + t*7)
                vertices.append((side*(center_x-depth*math.cos(a)),
                    y + normal_y*in_plane*math.sin(a)*fluting,
                    z + normal_z*in_plane*math.sin(a)*fluting))
        for i in range(len(path)-1):
            for j in range(ring):
                a = offset+i*ring+j
                b = offset+i*ring+(j+1)%ring
                faces.append((a, b, b+ring, a+ring))
        faces.append(tuple(offset+j for j in reversed(range(ring))))
        end = offset+(len(path)-1)*ring
        faces.append(tuple(end+j for j in range(ring)))
        stem_count += 1

    # Panel gaps avoid the existing crossrails at .35, 1.45, 2.65 and 3.85 m.
    panels = [(.42, 1.38), (1.52, 2.58), (2.72, 3.78)]
    for panel, (bottom, top) in enumerate(panels):
        height = top-bottom
        flip = -1 if (panel + (1 if side > 0 else 0)) % 2 else 1

        def point(u, v):
            return (-18.23 + flip*(u-.5)*1.18, bottom+v*height)

        trunk = [(0.42, .035), (.55, .24), (.43, .48), (.56, .71), (.49, .97)]
        stem([point(u, v) for u, v in trunk], .050, panel*.9)
        # Seven branching roots. Each emerges from the broad central stem and
        # opens into a legible irregular fan, leaving large quiet panel areas.
        branches = [
            [(0.55,.24),(.33,.20),(.20,.085),(.075,.045)],
            [(0.43,.48),(.27,.37),(.16,.22),(.085,.17)],
            [(0.43,.48),(.66,.38),(.77,.19),(.91,.085)],
            [(0.56,.71),(.70,.62),(.81,.44),(.92,.40)],
            [(0.56,.71),(.32,.65),(.18,.75),(.08,.86)],
            [(0.49,.97),(.36,.88),(.28,.79),(.14,.79)],
            [(0.56,.71),(.67,.79),(.75,.88),(.88,.955)],
        ]
        for n, branch in enumerate(branches):
            stem([point(u, v) for u, v in branch], .018 + .004*(n % 3), panel+n*.6)
        # Fine raised bark creases on the dominant stem, not separate objects.
        for drift in [-.017, .018]:
            points = [point(u+drift+.007*math.sin(v*13+panel), v) for u, v in trunk]
            stem(points, .0035, panel, vein=True)
    if side < 0:
        faces = [tuple(reversed(face)) for face in faces]
    return vertices, faces, stem_count


def add_entrance_detail(materials):
    """Create three meshes and return object/brick/stem/triangle statistics.

    materials must contain brass, concrete and metal. The latter is accepted for
    the shared architecture palette; existing rails already supply the dark metal.
    Repeated calls replace only this module's Entry_* objects.
    """
    import bpy

    for key in ("brass", "concrete", "metal"):
        if key not in materials:
            raise KeyError("Entrance detail requires material: " + key)
    category = bpy.data.collections.get("Architecture")
    parent = bpy.data.objects.get("Architecture")
    if category is None or parent is None or parent.type != 'EMPTY':
        raise RuntimeError("Run architecture phase first: Architecture collection/empty required")
    for obj in list(category.objects):
        if obj.name.startswith("Entry_"):
            old_mesh = obj.data if obj.type == 'MESH' else None
            bpy.data.objects.remove(obj, do_unlink=True)
            if old_mesh is not None and old_mesh.users == 0:
                bpy.data.meshes.remove(old_mesh)

    def stone_material(name, color):
        material = bpy.data.materials.get(name)
        if material is None:
            material = materials['concrete'].copy()
            material.name = name
        material.use_nodes = True
        bsdf = next((n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf:
            for link in list(bsdf.inputs['Base Color'].links):
                material.node_tree.links.remove(link)
            bsdf.inputs['Base Color'].default_value = (*color, 1)
            bsdf.inputs['Roughness'].default_value = .85
            bsdf.inputs['Metallic'].default_value = 0
        material.diffuse_color = (*color, 1)
        return material

    masonry = [stone_material('Entry_Pale_limestone', (.49, .465, .407)),
               stone_material('Entry_Warm_limestone', (.43, .395, .33)),
               stone_material('Entry_Cool_limestone', (.55, .535, .488))]
    created = []

    def make(name, vertices, faces, palette, indices=None, smooth=False):
        data = bpy.data.meshes.new(name)
        data.from_pydata(vertices, [], faces)
        data.update()
        obj = bpy.data.objects.new(name, data)
        category.objects.link(obj)
        for material in palette:
            data.materials.append(material)
        for i, face in enumerate(data.polygons):
            face.use_smooth = smooth and len(face.vertices) == 4
            if indices is not None:
                face.material_index = indices[i]
        bpy.context.view_layer.update()
        world = obj.matrix_world.copy()
        obj.parent = parent
        obj.matrix_world = world
        created.append(obj)
        return obj

    verts, faces, indices, brick_count = _brick_geometry()
    wall = make('Entry_Brick_Veneer', verts, faces, masonry, indices)
    wall['brick_count'] = brick_count
    wall['nominal_brick_m'] = '0.240 × 0.075; mortar 0.008; front chamfer 0.003'
    stems = 0
    for side in (-1, 1):
        verts, faces, count = _relief_geometry(side)
        leaf = make('Entry_Bronze_Root_Relief_' + ('Left' if side < 0 else 'Right'),
                    verts, faces, [materials['brass']], smooth=True)
        leaf['reference_interpretation'] = 'Original branching rooted relief, not exact entrance sculpture'
        leaf['stem_count'] = count
        stems += count
    bpy.context.view_layer.update()
    triangles = sum(sum(len(p.vertices)-2 for p in obj.data.polygons) for obj in created)
    if triangles >= 60000:
        raise RuntimeError('Entry detail triangle budget exceeded: %d' % triangles)
    return {'objects': [o.name for o in created], 'brick_count': brick_count,
            'relief_stems': stems, 'triangles': triangles,
            'portal_clear_width_m': 3.5, 'portal_clear_height_m': 4.25}
