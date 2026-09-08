import bpy
import math
from mathutils import Vector
from pathlib import Path


OUT_BLEND = str(Path(__file__).resolve().parent / "alchemist_dome.blend")
OUT_RENDER = str(Path(__file__).resolve().parent / "alchemist_dome_preview.png")


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        pass


def mat_principled(name, base, metallic=0.0, roughness=0.45, emission=None, emission_strength=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*base, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return m


def make_dome_material():
    m = bpy.data.materials.new("Dome Projection — Aurora")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    tex = nt.nodes.new("ShaderNodeTexCoord")
    noise.inputs["Scale"].default_value = 1.25
    noise.inputs["Detail"].default_value = 5.5
    noise.inputs["Roughness"].default_value = 0.72
    noise.inputs["Distortion"].default_value = 1.8
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    colors = [
        (0.00, (0.003, 0.006, 0.025, 1)),
        (0.22, (0.012, 0.035, 0.12, 1)),
        (0.43, (0.015, 0.22, 0.42, 1)),
        (0.58, (0.12, 0.03, 0.30, 1)),
        (0.72, (0.02, 0.55, 0.72, 1)),
        (0.88, (0.42, 0.08, 0.55, 1)),
        (1.00, (0.01, 0.01, 0.05, 1)),
    ]
    first = ramp.color_ramp.elements[0]
    first.position, first.color = colors[0][0], colors[0][1]
    for pos, col in colors[1:]:
        e = ramp.color_ramp.elements.new(pos)
        e.color = col
    em.inputs["Strength"].default_value = 1.65
    nt.links.new(tex.outputs["Generated"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def assign(obj, material):
    obj.data.materials.append(material)


def cube(name, loc, scale, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new("Soft architectural edges", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    assign(o, material)
    return o


def cylinder(name, loc, radius, depth, material, vertices=64, fill="NGON"):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                       end_fill_type=fill, location=loc)
    o = bpy.context.object
    o.name = name
    assign(o, material)
    return o


def torus(name, loc, major, minor, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                    major_segments=96, minor_segments=20,
                                    location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    assign(o, material)
    return o


def make_open_dome(radius=14.0, base_z=3.0, height=8.6, rings=24, segments=128):
    verts = []
    faces = []
    for j in range(rings + 1):
        phi = (math.pi / 2.0) * (j / rings)
        rr = radius * math.cos(phi)
        z = base_z + height * math.sin(phi)
        for i in range(segments):
            a = 2 * math.pi * i / segments
            verts.append((rr * math.cos(a), rr * math.sin(a), z))
    for j in range(rings):
        for i in range(segments):
            ni = (i + 1) % segments
            a = j * segments + i
            b = j * segments + ni
            c = (j + 1) * segments + ni
            d = (j + 1) * segments + i
            faces.append((a, d, c, b))
    mesh = bpy.data.meshes.new("Projection Dome Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Immersive Planetarium Dome", mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, dome_mat)
    return obj


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_area(name, loc, energy, color, size, target):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = color
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    look_at(obj, target)
    return obj


def add_point(name, loc, energy, color, radius=0.25):
    data = bpy.data.lights.new(name, "POINT")
    data.energy = energy
    data.color = color
    data.shadow_soft_size = radius
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    return obj


clear_scene()

# Materials: dark industrial shell with Alchemist's blue / gold / purple palette.
floor_mat = mat_principled("Black polished terrazzo", (0.012, 0.014, 0.022), metallic=0.25, roughness=0.18)
black_metal = mat_principled("Blackened steel", (0.018, 0.022, 0.032), metallic=0.82, roughness=0.24)
bronze = mat_principled("Aged warm bronze", (0.24, 0.095, 0.025), metallic=0.92, roughness=0.26)
counter_mat = mat_principled("Honed black stone", (0.015, 0.018, 0.024), metallic=0.08, roughness=0.16)
fabric = mat_principled("Deep aubergine upholstery", (0.075, 0.012, 0.075), roughness=0.72)
wood = mat_principled("Charred oak", (0.035, 0.014, 0.009), roughness=0.65)
porcelain = mat_principled("Warm porcelain", (0.70, 0.67, 0.58), roughness=0.28)
chrome = mat_principled("Liquid chrome sculpture", (0.22, 0.26, 0.31), metallic=1.0, roughness=0.07)
cyan_emit = mat_principled("Cyan guide light", (0.0, 0.12, 0.18), roughness=0.25,
                           emission=(0.0, 0.45, 0.9), emission_strength=6.0)
gold_emit = mat_principled("Warm table light", (0.25, 0.08, 0.012), roughness=0.2,
                           emission=(1.0, 0.22, 0.025), emission_strength=5.0)
dome_mat = make_dome_material()

# Architectural shell.
cylinder("Polished circular floor", (0, 0, -0.22), 14.0, 0.44, floor_mat, 128)
cylinder("Raised dining plinth", (0, 0, 0.08), 7.0, 0.24, black_metal, 128)
cylinder("Industrial wall shell", (0, 0, 2.55), 14.15, 5.1, wood, 128, "NOTHING")
cylinder("Inner wall darkness", (0, 0, 2.58), 13.92, 5.05, black_metal, 128, "NOTHING")
make_open_dome()

# Bronze structural ribs at the base of the dome.
for i in range(32):
    a = 2 * math.pi * i / 32
    x, y = 13.82 * math.cos(a), 13.82 * math.sin(a)
    rib = cube(f"Bronze wall rib {i+1:02d}", (x, y, 2.55), (0.045, 0.13, 2.5), bronze, 0.025)
    rib.rotation_euler[2] = a

# Concentric inlaid light rings in the floor.
for r in (6.85, 8.65, 12.75):
    torus(f"Floor guide ring {r}", (0, 0, 0.035), r, 0.028, cyan_emit)

# Central culinary theatre and annular guest counter.
cylinder("Central culinary stage", (0, 0, 0.33), 3.15, 0.42, black_metal, 96)
torus("Monolithic guest counter", (0, 0, 1.18), 4.55, 0.68, counter_mat)
torus("Bronze counter reveal", (0, 0, 0.73), 4.55, 0.09, bronze)
torus("Counter underglow", (0, 0, 0.60), 4.5, 0.035, gold_emit)

# Central sculptural service island.
cylinder("Chef island base", (0, 0, 0.83), 1.42, 1.1, counter_mat, 96)
torus("Chef island bronze rim", (0, 0, 1.40), 1.16, 0.14, bronze)
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, location=(0, 0, 2.42), scale=(0.82, 0.82, 1.18))
sculpt = bpy.context.object
sculpt.name = "Reflective alchemical vessel"
assign(sculpt, chrome)
torus("Sculpture halo", (0, 0, 3.75), 1.5, 0.035, cyan_emit)

# Guest chairs, place settings and intimate pools of warm light.
guest_count = 18
for i in range(guest_count):
    a = 2 * math.pi * i / guest_count
    ca, sa = math.cos(a), math.sin(a)
    chair_r = 6.08
    x, y = chair_r * ca, chair_r * sa
    seat = cylinder(f"Guest chair pedestal {i+1:02d}", (x, y, 0.55), 0.34, 0.75, bronze, 32)
    seat_top = cube(f"Guest chair seat {i+1:02d}", (x, y, 0.98), (0.48, 0.48, 0.15), fabric, 0.20)
    bx, by = (chair_r + 0.28) * ca, (chair_r + 0.28) * sa
    back = cube(f"Wing chair back {i+1:02d}", (bx, by, 1.52), (0.53, 0.16, 0.68), fabric, 0.22)
    back.rotation_euler[2] = a + math.pi / 2

    # Porcelain plate and glowing tasting marker on the counter.
    pr = 4.56
    px, py = pr * ca, pr * sa
    cylinder(f"Porcelain plate {i+1:02d}", (px, py, 1.82), 0.24, 0.028, porcelain, 48)
    cylinder(f"Golden tasting light {i+1:02d}", (px, py, 1.85), 0.045, 0.025, gold_emit, 24)

    # Pendant pin light and short bronze stem.
    lr = 4.7
    lx, ly = lr * ca, lr * sa
    cylinder(f"Pendant stem {i+1:02d}", (lx, ly, 5.15), 0.018, 2.2, bronze, 16)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=(lx, ly, 4.02), scale=(0.12, 0.12, 0.18))
    bulb = bpy.context.object
    bulb.name = f"Pendant glow {i+1:02d}"
    assign(bulb, gold_emit)
    if i % 3 == 0:
        add_point(f"Table pool {i+1:02d}", (lx, ly, 3.65), 170, (1.0, 0.22, 0.055), 0.55)

# Sculptural service portals along the rear wall.
for idx, deg in enumerate((125, 145, 165)):
    a = math.radians(deg)
    r = 13.45
    x, y = r * math.cos(a), r * math.sin(a)
    frame = torus(f"Bronze portal {idx+1}", (x, y, 2.15), 1.25, 0.12, bronze, rot=(math.pi/2, 0, a + math.pi/2))
    inner = cube(f"Portal shadow {idx+1}", (x, y, 2.0), (1.0, 0.16, 1.65), black_metal, 0.45)
    inner.rotation_euler[2] = a + math.pi / 2

# Sparse low lounge tables in the outer ring.
for i, deg in enumerate((25, 75, 205, 255, 305)):
    a = math.radians(deg)
    r = 10.4
    x, y = r * math.cos(a), r * math.sin(a)
    cylinder(f"Outer cocktail table {i+1}", (x, y, 0.66), 0.58, 0.12, counter_mat, 48)
    cylinder(f"Outer table stem {i+1}", (x, y, 0.34), 0.11, 0.58, bronze, 24)

# Lighting: projected dome carries the cool ambient field; warm fixtures isolate diners.
add_area("Central softbox", (0, 0, 8.9), 1150, (0.13, 0.28, 1.0), 6.5, (0, 0, 0.8))
add_area("Warm key", (7.8, -7.0, 6.2), 900, (1.0, 0.19, 0.055), 4.0, (0, 0, 1.1))
add_area("Cool rim", (-8.5, 4.5, 6.8), 1250, (0.02, 0.34, 1.0), 4.5, (0, 0, 2.0))
add_area("Purple fill", (-3.5, -9.2, 5.0), 720, (0.40, 0.025, 0.62), 3.5, (0, 0, 1.0))

# Camera composition: wide architectural hero shot, slightly above eye level.
cam_data = bpy.data.cameras.new("Hero Camera")
cam = bpy.data.objects.new("Hero Camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (9.0, -9.0, 5.4)
cam_data.lens = 23
cam_data.sensor_width = 36
look_at(cam, (0.0, 0.0, 2.7))
bpy.context.scene.camera = cam

# Render and color management.
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUT_RENDER
scene.render.film_transparent = False
scene.render.image_settings.color_mode = "RGBA"
scene.world.color = (0.001, 0.001, 0.004)
scene.view_settings.look = "AgX - Medium High Contrast"

# Blender 5.2's compositor API is intentionally left untouched here so the
# scene remains portable across the legacy and new compositor backends.

# Organize objects into a meaningful scene hierarchy.
scene["design_reference"] = "Alchemist Copenhagen main planetarium dome — public-reference interpretation"
scene["design_notes"] = "52-seat immersive industrial venue; dark blue, gold and purple palette; central culinary theatre"

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print({"blend": OUT_BLEND, "render": OUT_RENDER, "objects": len(bpy.data.objects)})
