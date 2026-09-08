"""Reusable, meter-scale Alchemist seating and restrained table details.

Importing this module does not create or change scene objects. Call
add_chairs(materials) and add_table_experience(materials) from the phase driver.
The angles returned by common.chair_positions use Blender's standard Z rotation;
the diner faces local -Y, so forward in world space is (sin(a), -cos(a)).
"""

import math

import bpy
from mathutils import Vector

from common import chair_positions, finish, group, mesh


def _remove_owned(prefixes):
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefixes):
            bpy.data.objects.remove(obj, do_unlink=True)


def _attach(obj, category):
    parent = bpy.data.objects.get(category)
    if parent and parent.type == "EMPTY":
        # location/rotation writes do not immediately refresh matrix_world.
        # Resolve them before preserving the world transform across parenting.
        bpy.context.view_layer.update()
        world = obj.matrix_world.copy()
        obj.parent = parent
        obj.matrix_world = world
    return obj


def _place(obj, origin, angle, category):
    obj.location = origin
    obj.rotation_euler[2] = angle
    return _attach(obj, category)


def _world(local, origin, angle):
    x, y, z = local
    cosine, sine = math.cos(angle), math.sin(angle)
    return Vector((origin[0] + cosine * x - sine * y,
                   origin[1] + sine * x + cosine * y,
                   origin[2] + z))


def _tapered_between(name, start, end, bottom_radius, top_radius,
                     material, category):
    start, end = Vector(start), Vector(end)
    delta = end - start
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=bottom_radius,
                                    radius2=top_radius, depth=delta.length,
                                    location=(start + end) * 0.5)
    obj = finish(bpy.context.object, name, category, material, bevel=0.0018)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    for polygon in obj.data.polygons:
        polygon.use_smooth = len(polygon.vertices) == 4
    return _attach(obj, category)


def _lathe(name, profile, material, category, origin, angle=0.0, segments=64):
    """Revolve a closed material cross-section, with real single-vertex poles."""
    vertices, rings, faces = [], [], []
    for radius, height in profile:
        if abs(radius) < 1e-9:
            rings.append([len(vertices)])
            vertices.append((0, 0, height))
        else:
            ring = []
            for index in range(segments):
                phi = math.tau * index / segments
                ring.append(len(vertices))
                vertices.append((radius * math.cos(phi), radius * math.sin(phi), height))
            rings.append(ring)
    for lower, upper in zip(rings, rings[1:]):
        if len(lower) == 1 and len(upper) == 1:
            continue
        for index in range(segments):
            following = (index + 1) % segments
            if len(lower) == 1:
                faces.append((lower[0], upper[following], upper[index]))
            elif len(upper) == 1:
                faces.append((lower[index], lower[following], upper[0]))
            else:
                faces.append((lower[index], lower[following], upper[following], upper[index]))
    obj = mesh(name, vertices, faces, category, material, smooth=True)
    return _place(obj, origin, angle, category)


def _seat(name, origin, angle, material):
    # Soft perimeter, thin cushion and a shallow dished sitting surface.
    # Overall plan dimensions are exactly 560 x 550 mm; height is 460–520 mm.
    rings = [(0.89, 0.460), (0.98, 0.467), (1.00, 0.482),
             (0.99, 0.501), (0.94, 0.516), (0.82, 0.520),
             (0.53, 0.518), (0.20, 0.515)]
    count, vertices, faces = 64, [], []
    for radius, height in rings:
        for index in range(count):
            phi = math.tau * index / count
            cosine, sine = math.cos(phi), math.sin(phi)
            # Exponent 2/3 gives a rounded rectangle without square chair corners.
            x = 0.280 * math.copysign(abs(cosine) ** (2 / 3), cosine) * radius
            y = 0.275 * math.copysign(abs(sine) ** (2 / 3), sine) * radius
            vertices.append((x, y, height))
    faces.append(tuple(reversed(range(count))))
    for ring in range(len(rings) - 1):
        for index in range(count):
            following = (index + 1) % count
            faces.append((ring * count + index, ring * count + following,
                          (ring + 1) * count + following, (ring + 1) * count + index))
    center = len(vertices)
    vertices.append((0, 0, 0.514))
    last = (len(rings) - 1) * count
    for index in range(count):
        faces.append((last + index, last + (index + 1) % count, center))
    obj = mesh(name, vertices, faces, "Seating", material, smooth=True)
    obj["seat_base_height_m"] = 0.46
    obj["seat_top_height_m"] = 0.52
    obj["nominal_dimensions_m"] = [0.56, 0.55, 0.06]
    return _place(obj, origin, angle, "Seating")


def _back(name, origin, angle, material):
    # A 28 mm upholstered curved shell wraps forward around the sitter.
    # The central back is at local +Y ~= .22 m, with a small comfortable recline.
    columns, rows = 24, 8
    vertices, faces = [], []
    stride = columns + 1
    side_count = stride * (rows + 1)
    for side in (-1, 1):
        for row in range(rows + 1):
            v = row / rows
            for column in range(columns + 1):
                u = 2 * column / columns - 1
                normal = Vector((0.82 * u, 1, -0.12)).normalized()
                point = Vector((0.271 * u,
                                0.201 + 0.040 * v - 0.105 * u * u,
                                0.650 + 0.310 * v - 0.017 * u * u * v))
                vertices.append(tuple(point + normal * side * 0.014))
    for row in range(rows):
        for column in range(columns):
            base = row * stride + column
            faces.append((base, base + 1, base + stride + 1, base + stride))
            base += side_count
            faces.append((base, base + stride, base + stride + 1, base + 1))
    perimeter = list(range(stride))
    perimeter += [row * stride + columns for row in range(1, rows + 1)]
    perimeter += [rows * stride + column for column in range(columns - 1, -1, -1)]
    perimeter += [row * stride for row in range(rows - 1, 0, -1)]
    for first, second in zip(perimeter, perimeter[1:] + perimeter[:1]):
        faces.append((first, first + side_count, second + side_count, second))
    obj = mesh(name, vertices, faces, "Seating", material, bevel=0.010, smooth=True)
    obj["construction"] = "Thin concave upholstered shell; soft rolled edges"
    return _place(obj, origin, angle, "Seating")


def add_chairs(materials):
    """Replace only Chair_/ChairBack_ components; preserve lounge seating."""
    fabric, timber, metal = materials["fabric"], materials["wood"], materials["metal"]
    _remove_owned(("Chair_", "ChairBack_"))
    positions = chair_positions()
    built = 0
    for index, (x, y, angle) in enumerate(positions, 1):
        origin = (x, y, 0)
        prefix = "Chair_%02d" % index
        _seat(prefix + "_UpholsteredSeat", origin, angle, fabric)
        _back("ChairBack_%02d_CurvedShell" % index, origin, angle, fabric)
        built += 2
        for leg_index, (side, front_back) in enumerate(((-1, -1), (1, -1),
                                                       (-1, 1), (1, 1)), 1):
            bottom = _world((side * 0.228, front_back * 0.221, 0.025), origin, angle)
            top = _world((side * 0.189, front_back * 0.166, 0.477), origin, angle)
            _tapered_between(prefix + "_TaperedLeg_%d" % leg_index, bottom, top,
                             0.011, 0.020, timber, "Seating")
            built += 1
        for side in (-1, 1):
            start = _world((side * 0.193, 0.175, 0.447), origin, angle)
            end = _world((side * 0.195, 0.159, 0.724), origin, angle)
            _tapered_between(prefix + "_BackSupport_%s" % ("L" if side < 0 else "R"),
                             start, end, 0.011, 0.010, metal, "Seating")
            built += 1
    return {"chairs": len(positions), "mesh_objects": built,
            "seat_top_height_m": 0.52, "replacement_prefixes": ["Chair_", "ChairBack_"]}


def _catmull(points, steps=6):
    points = [Vector(point) for point in points]
    result = []
    for index in range(len(points) - 1):
        p0, p1 = points[max(index - 1, 0)], points[index]
        p2, p3 = points[index + 1], points[min(index + 2, len(points) - 1)]
        for sample in range(steps):
            t = sample / steps
            result.append(0.5 * ((2 * p1) + (-p0 + p2) * t
                                 + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                 + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    result.append(points[-1])
    return result


def _tube(name, points, radius, material, origin, angle):
    points = _catmull(points, steps=7)
    vertices, faces, sides = [], [], 12
    for index, point in enumerate(points):
        tangent = (points[min(index + 1, len(points) - 1)] - points[max(index - 1, 0)]).normalized()
        normal = tangent.cross(Vector((0, 1, 0))).normalized()
        binormal = tangent.cross(normal).normalized()
        for side in range(sides):
            phi = math.tau * side / sides
            vertices.append(tuple(point + radius * (normal * math.cos(phi) + binormal * math.sin(phi))))
    for ring in range(len(points) - 1):
        for side in range(sides):
            following = (side + 1) % sides
            faces.append((ring * sides + side, ring * sides + following,
                          (ring + 1) * sides + following, (ring + 1) * sides + side))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple((len(points) - 1) * sides + side for side in range(sides)))
    return _place(mesh(name, vertices, faces, "Lighting", material, smooth=True),
                  origin, angle, "Lighting")


def _cutlery(name, outline, local_x, material, origin, angle):
    # Tiny real edge radii prevent razor-like highlights on the two utensils.
    area = sum(point[0] * outline[(index + 1) % len(outline)][1]
               - outline[(index + 1) % len(outline)][0] * point[1]
               for index, point in enumerate(outline))
    if area < 0:
        outline = list(reversed(outline))
    vertices = [(x + local_x, y, z) for z in (0.780, 0.7825) for x, y in outline]
    count = len(outline)
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    for index in range(count):
        following = (index + 1) % count
        faces.append((index, following, count + following, count + index))
    return _place(mesh(name, vertices, faces, "Props", material, bevel=0.0011),
                  origin, angle, "Props")


def _wine_glass(name, material, origin, angle):
    # Continuous solid foot + stem + hollow bowl. Inner bowl is offset by 1.4 mm
    # along the meridian normal, rather than faking glass with a solid sphere.
    wall = 0.0014
    outer = _catmull([(0.008, 0.104), (0.020, 0.113), (0.033, 0.128),
                      (0.039, 0.150), (0.038, 0.177), (0.033, 0.202),
                      (0.028, 0.2293)], steps=6)
    inner = []
    for index, point in enumerate(outer):
        tangent = (outer[min(index + 1, len(outer) - 1)] - outer[max(index - 1, 0)]).normalized()
        normal = Vector((tangent.y, -tangent.x))
        inner.append(point - wall * normal)
    # A half-round polished rim joins both walls without capping the opening.
    rim = [(0.0273 + 0.0007 * math.cos(math.pi * index / 8),
            0.2293 + 0.0007 * math.sin(math.pi * index / 8)) for index in range(1, 9)]
    profile = [(0, 0.000), (0.024, 0.000), (0.032, 0.0010),
               (0.034, 0.0025), (0.032, 0.0040), (0.021, 0.0055),
               (0.007, 0.0070), (0.0032, 0.011), (0.0026, 0.029),
               (0.0026, 0.092), (0.0038, 0.100)]
    profile += [tuple(point) for point in outer]
    profile += rim
    profile += [tuple(point) for point in reversed(inner[:-1])]
    profile += [(0.003, 0.1065), (0, 0.1065)]
    glass = _lathe(name, profile, material, "Glassware", origin, angle, segments=64)
    glass["height_m"] = 0.23
    glass["bowl_wall_thickness_m"] = wall
    glass["construction"] = "Closed glass material shell with an open hollow bowl, continuous stem and solid foot"
    return glass


def _lamp(prefix, materials, origin, angle):
    base = (-0.278, -0.130, 0.780)
    _lathe(prefix + "_Base", [(0, 0), (0.027, 0), (0.030, 0.003),
                              (0.029, 0.010), (0.021, 0.012), (0, 0.012)],
           materials["brass"], "Lighting", _world(base, origin, angle), angle, segments=40)
    neck = [(-0.278, -0.130, 0.790), (-0.279, -0.130, 0.960),
            (-0.270, -0.126, 1.067), (-0.223, -0.115, 1.110),
            (-0.157, -0.100, 1.113), (-0.097, -0.082, 1.082),
            (-0.067, -0.065, 1.048)]
    _tube(prefix + "_ArchedBrassNeck", neck, 0.0042, materials["brass"], origin, angle)
    start = _world(neck[-1], origin, angle)
    target = _world((0, 0, 0.797), origin, angle)
    axis = (target - start).normalized()
    end = start + axis * 0.035
    _tapered_between(prefix + "_Shade", start, end, 0.008, 0.016,
                     materials["brass"], "Lighting")
    _tapered_between(prefix + "_WarmLens", end, end + axis * 0.0015, 0.0125, 0.0125,
                     materials["emitter"], "Lighting")
    data = bpy.data.lights.new(prefix + "_Pool", "SPOT")
    obj = bpy.data.objects.new(prefix + "_Pool", data)
    group("Lighting").objects.link(obj)
    obj.location = end + axis * 0.004
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()
    data.energy = 5.0
    data.color = (1.0, 0.76, 0.47)
    data.spot_size = math.radians(63)
    data.spot_blend = 0.82
    data.shadow_soft_size = 0.012
    _attach(obj, "Lighting")
    obj["purpose"] = "Localized warm tasting-plate light"
    return {"mesh_objects": 4, "light_objects": 1}


def add_table_experience(materials):
    """Build one slim lamp, plate, tasting bite, two utensils and hollow glass per chair.

    Materials: brass, porcelain, glass, metal, food and emitter. The tabletop is
    at Z=.78 m; the setting center is .80 m forward from each chair center.
    Calling again replaces only objects owned by the TableExperience_ prefix.
    """
    for name in ("brass", "porcelain", "glass", "metal", "food", "emitter"):
        materials[name]  # Fail before mutation if the caller omitted a required material.
    _remove_owned(("TableExperience_",))
    knife = [(-0.004, 0.087), (0.004, 0.087), (0.005, 0.019),
             (0.009, -0.039), (0.007, -0.080), (0.003, -0.089),
             (-0.004, -0.084), (-0.004, -0.017)]
    fork = [(-0.004, 0.086), (0.004, 0.086), (0.005, 0.015),
            (0.008, -0.030), (0.013, -0.050), (0.013, -0.087),
            (0.009, -0.087), (0.009, -0.060), (0.003, -0.060),
            (0.003, -0.088), (-0.001, -0.088), (-0.001, -0.060),
            (-0.007, -0.060), (-0.007, -0.086), (-0.011, -0.086),
            (-0.011, -0.050), (-0.007, -0.028), (-0.004, 0.015)]
    positions = chair_positions()
    meshes, lamps = 0, 0
    for index, (x, y, angle) in enumerate(positions, 1):
        # Standard Blender yaw: rotating local -Y gives (sin(a), -cos(a)).
        origin = (x + 0.8 * math.sin(angle), y - 0.8 * math.cos(angle), 0)
        prefix = "TableExperience_%02d" % index
        plate = _lathe(prefix + "_PorcelainPlate",
                       [(0, 0.780), (0.065, 0.780), (0.080, 0.784),
                        (0.103, 0.789), (0.109, 0.792), (0.110, 0.794),
                        (0.108, 0.796), (0.102, 0.795), (0.079, 0.790),
                        (0.068, 0.789), (0, 0.789)],
                       materials["porcelain"], "Props", origin, angle, segments=64)
        plate["tabletop_height_m"] = 0.78
        _cutlery(prefix + "_Knife", knife, 0.140, materials["metal"], origin, angle)
        _cutlery(prefix + "_Fork", fork, -0.140, materials["metal"], origin, angle)
        glass_origin = _world((0.185, -0.145, 0.780), origin, angle)
        _wine_glass(prefix + "_HollowWineGlass", materials["glass"], glass_origin, angle)
        bite_origin = _world((-0.007, 0.0, 0.795), origin, angle)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=bite_origin)
        bite = bpy.context.object
        bite.scale = (0.024, 0.011, 0.007)
        bite.rotation_euler[2] = angle + 0.28
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        finish(bite, prefix + "_TastingBite", "Props", materials["food"])
        for polygon in bite.data.polygons:
            polygon.use_smooth = True
        _attach(bite, "Props")
        lamp_counts = _lamp(prefix + "_TaskLamp", materials, origin, angle)
        meshes += 5 + lamp_counts["mesh_objects"]
        lamps += lamp_counts["light_objects"]
    return {"settings": len(positions), "mesh_objects": meshes, "light_objects": lamps,
            "hollow_wine_glasses": len(positions), "tabletop_height_m": 0.78,
            "task_light_watts_each": 5.0, "replacement_prefix": "TableExperience_"}
