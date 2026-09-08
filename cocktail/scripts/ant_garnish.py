"""A small leaf-cutter-ant-inspired glass garnish. No scene execution on import.

The ant faces local +X (tangent to the glass rim); local Y crosses the rim.
Local +Z points away from the contact surface. Defaults to a broadly splayed
bowl-clinging pose; grip='rim' places feet on either side of a narrow glass rim.
Canonical dimensions are millimeters, converted to Blender meters below.
"""

import math
import bpy
from mathutils import Vector


def _cuticle(name, color, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    shader = tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.27
    noise = tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 76000.0
    noise.inputs["Detail"].default_value = 2.0
    tex = tree.nodes.new("ShaderNodeTexCoord")
    bump = tree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.0000008
    tree.links.new(tex.outputs["Object"], noise.inputs["Vector"])
    tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    tree.links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat


def build_ant(scene, collection, position=(0, 0, 0.17), yaw=0, length=0.012,
              grip="bowl", leg_span_ratio=1.8):
    """Build one posed ant; yaw is radians and length is meters.

    Returns {'root': root_name, 'objects': [...], 'contact_points': [...], ...}.
    Local contact points describe the upper foot contacts at the default size;
    multiply by length/0.009 for other sizes. No render/save/scene clearing.
    """
    if length <= 0:
        raise ValueError("Ant length must be positive")
    if collection is None:
        collection = scene.collection
    if isinstance(collection, str):
        collection = bpy.data.collections[collection]
    root = bpy.data.objects.new("Cocktail_Ant_RimGarnish", None)
    collection.objects.link(root)
    root.location = position
    root.rotation_euler.z = yaw
    root.scale = (length / 0.009,) * 3
    root.empty_display_size = 0.002
    root["description"] = "Single dark leaf-cutter-ant-inspired garnish gripping glass"
    root["anatomy"] = "Head, paired antennae, mandibles, mesosoma, two waist nodes, gaster, six jointed legs"
    root["local_orientation"] = "+X head; +Z away from glass; z=0 contact surface"
    cuticle = _cuticle("Cocktail_Ant_DarkBrownCuticle", (0.019, 0.0085, 0.0044), 0.47)
    gaster_mat = _cuticle("Cocktail_Ant_GasterCuticle", (0.012, 0.006, 0.0032), 0.41)
    appendage_mat = _cuticle("Cocktail_Ant_Appendages", (0.048, 0.014, 0.0055), 0.48)
    eye_mat = _cuticle("Cocktail_Ant_TinyMatteEyes", (0.005, 0.0035, 0.0027), 0.36)
    objects = []

    def mesh_object(name, vertices, faces, material):
        mesh = bpy.data.meshes.new("Cocktail_Ant_" + name + "_Mesh")
        mesh.from_pydata([tuple(v * 0.001 for v in p) for p in vertices], [], faces)
        mesh.update()
        obj = bpy.data.objects.new("Cocktail_Ant_" + name, mesh)
        collection.objects.link(obj)
        obj.parent = root
        mesh.materials.append(material)
        for face in mesh.polygons:
            face.use_smooth = True
        objects.append(obj.name)
        return obj

    def shell(name, rings, material, sides=24, phase=0.0):
        # Rings: x, y-center, z-center, y-radius, z-radius. All in mm.
        if name == "Gaster":
            rings = [(-2.0 + (x + 2.0) * .87, y * .77,
                      .95 + (z - .95) * .82, ry * .77, rz * .82)
                     for x, y, z, ry, rz in rings]
        vertices, faces = [], []
        for ri, (x, y, z, ry, rz) in enumerate(rings):
            for j in range(sides):
                angle = 2 * math.pi * j / sides + phase
                # Minute asymmetry breaks pristine synthetic body ellipsoids.
                asymmetry = 1.0 + 0.012 * math.sin(3 * angle + ri * 0.43)
                vertices.append((x, y + ry * math.cos(angle) * asymmetry,
                                 z + rz * math.sin(angle) * asymmetry))
            if ri:
                for j in range(sides):
                    a = (ri - 1) * sides + j
                    b = (ri - 1) * sides + (j + 1) % sides
                    faces.append((a, b, ri * sides + (j + 1) % sides, ri * sides + j))
        faces.append(tuple(reversed(range(sides))))
        faces.append(tuple((len(rings) - 1) * sides + j for j in range(sides)))
        return mesh_object(name, vertices, faces, material)

    def tube(name, points, radii, material=appendage_mat, sides=8):
        points = [Vector(p) for p in points]
        vertices, faces = [], []
        for i, point in enumerate(points):
            tangent = (points[min(i + 1, len(points) - 1)] -
                       points[max(0, i - 1)]).normalized()
            axis = Vector((0, 0, 1))
            if abs(tangent.dot(axis)) > 0.95:
                axis = Vector((0, 1, 0))
            u = tangent.cross(axis).normalized()
            v = tangent.cross(u).normalized()
            for j in range(sides):
                angle = 2 * math.pi * j / sides
                q = point + radii[i] * (math.cos(angle) * u + math.sin(angle) * v)
                vertices.append(tuple(q))
            if i:
                for j in range(sides):
                    a = (i - 1) * sides + j
                    b = (i - 1) * sides + (j + 1) % sides
                    faces.append((a, b, i * sides + (j + 1) % sides, i * sides + j))
        faces.append(tuple(reversed(range(sides))))
        faces.append(tuple((len(points) - 1) * sides + j for j in range(sides)))
        return mesh_object(name, vertices, faces, material)

    # Heart-shaped flattened head and tapered armored mesosoma, not bead spheres.
    shell("Head", [
        (1.18, 0.00, 0.98, .13, .18),
        (1.40, 0.00, 1.00, .57, .36),
        (1.80, -.018, 1.02, .80, .46),
        (2.28, -.025, 1.00, .85, .48),
        (2.73, -.015, .96, .72, .41),
        (3.08, .015, .91, .50, .29),
        (3.33, .02, .89, .23, .16)], cuticle)
    shell("Mesosoma", [
        (-1.22, 0, .91, .14, .18),
        (-.93, .005, .97, .30, .32),
        (-.54, .008, 1.02, .42, .43),
        (-.20, 0, 1.03, .46, .40),
        (.12, -.015, 1.01, .37, .30),
        (.47, -.020, 1.06, .50, .43),
        (.85, -.01, 1.05, .48, .42),
        (1.17, 0, 1.02, .25, .24),
        (1.32, 0, 1.00, .12, .13)], cuticle)
    shell("Petiole", [(-1.70, 0, .94, .09, .10), (-1.56, 0, 1.07, .23, .27),
                      (-1.38, 0, 1.05, .22, .25), (-1.20, 0, .94, .10, .10)], cuticle, 16)
    shell("Postpetiole", [(-2.10, 0, .97, .10, .11), (-1.94, .01, 1.01, .29, .25),
                          (-1.75, .01, .99, .24, .22), (-1.63, 0, .96, .10, .10)], cuticle, 16)
    shell("Gaster", [
        (-4.55, -.07, .78, .018, .022),
        (-4.39, -.06, .84, .28, .28),
        (-4.09, -.05, .94, .49, .43),
        (-3.69, -.035, 1.01, .64, .53),
        (-3.20, -.02, 1.06, .71, .58),
        (-2.76, .00, 1.06, .67, .56),
        (-2.36, .01, 1.03, .47, .42),
        (-2.12, .01, .98, .22, .24),
        (-1.99, 0, .96, .09, .12)], gaster_mat)

    # Six articulated legs: fine, long limbs span ~1.8 times body length.
    contacts = []
    leg_specs = [
        ("Front", .77, 1.58, 1.57, 1.30, 1.78),
        ("Middle", .10, -.04, 1.91, .67, .10),
        ("Rear", -.68, -1.53, 1.76, .88, -1.33),
    ]
    for side in (-1, 1):
        label = "L" if side > 0 else "R"
        for index, (name, start_x, knee_x, knee_y, knee_z, foot_x) in enumerate(leg_specs):
            asym = 0.045 * side * (index - 1)
            if grip == "rim":
                foot_y = side * .65
                tarsus_y, near_foot_y = side * .94, side * .73
            else:
                spread = 9.0 * leg_span_ratio / 2.0
                knee_y *= spread / 1.91
                knee_x = (3.00, -.12, -3.13)[index]
                foot_x = (3.97, -.24, -4.18)[index] + .14 * side
                foot_y = side * spread * (.54, .78, .63)[index]
                tarsus_y = foot_y + side * .40
                near_foot_y = foot_y + side * .12
            points = [
                (start_x, side * .34, .96),
                (start_x + .07, side * .61, .82),
                (knee_x + asym, side * knee_y, knee_z),
                (knee_x + asym + .02, side * (knee_y + .02), knee_z - .10),
                (foot_x + .16 * side, tarsus_y, .31),
                (foot_x + .10 * side, near_foot_y, .12),
                (foot_x, foot_y, .025),
                (foot_x - .06, foot_y - side * .06, -.105),
            ]
            tube(label + name + "Leg", points,
                 [.090, .077, .068, .061, .045, .034, .023, .005])
            contacts.append((foot_x * .001, foot_y * .001, 0.0))
            tube(label + name + "FootClaw",
                 [(foot_x, foot_y, .02), (foot_x + .07, foot_y - side * .05, -.035),
                  (foot_x + .04, foot_y - side * .08, -.095)], [.020, .012, .003], sides=6)

    # Elbowed antennae retain a long scape and finer curved flagellum.
    for side in (-1, 1):
        label = "L" if side > 0 else "R"
        shift = 0.12 if side > 0 else -.04
        tube(label + "BentAntenna", [
            (2.68, side * .32, 1.25),
            (3.35, side * .80, 1.52),
            (3.54, side * .96, 1.58),
            (3.77 + shift, side * .76, 1.61),
            (4.15 + shift, side * .56, 1.56),
            (4.38 + shift, side * .40, 1.45)],
            [.050, .042, .041, .033, .024, .012])
        tube(label + "Mandible", [(3.16, side * .28, .90),
                                  (3.50, side * .43, .82),
                                  (3.82, side * .34, .77),
                                  (3.98, side * .14, .79)],
             [.12, .105, .073, .012], cuticle, 10)
        # Small recessed compound eyes: an irregular shallow patch on each side.
        shell(label + "Eye", [(2.16, side * .790, 1.075, .010, .023),
                              (2.22, side * .812, 1.075, .039, .080),
                              (2.31, side * .813, 1.070, .039, .078),
                              (2.37, side * .792, 1.065, .008, .020)], eye_mat, 12)
        # Leaf-cutter-like mesosoma spines, subtle at life size.
        for k, (x, z, rise) in enumerate([(.73, 1.38, .24), (.31, 1.33, .20), (-.67, 1.31, .22)]):
            tube(label + "ThoraxSpine" + str(k),
                 [(x, side * .29, z), (x - .11, side * .37, z + rise)],
                 [.049, .003], cuticle, 7)

    root["nominal_length_m"] = length
    root["grip"] = grip
    root["contact_width_m"] = (.00130 * length / .009 if grip == "rim"
                                else length * leg_span_ratio * .78)
    return {"root": root.name, "objects": objects,
            "contact_points": contacts, "nominal_length_m": length,
            "position": list(position), "yaw": yaw, "grip": grip,
            "leg_span_ratio": leg_span_ratio}
