"""Small photographic stage for a single luxury cocktail, in meters.

Call build_stage(scene), then build_lighting(scene), then setup_camera(scene).
No render, save, scene clear, or external dependency is performed by this module.
All lighting powers are watts; camera focal length is millimeters.
"""

import math
import bpy
from mathutils import Vector


PREFIX = "Cocktail_Stage_"


def _collection(scene):
    name = PREFIX + "Collection"
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    if collection.name not in scene.collection.children:
        scene.collection.children.link(collection)
    return collection


def _link(scene, obj):
    collection = _collection(scene)
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def _material(name, color, roughness, metallic=0.0):
    mat = bpy.data.materials.new(PREFIX + name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat, bsdf


def _stone_material():
    mat, bsdf = _material("BlueGrayPolishedStone", (0.033, 0.044, 0.052), 0.265)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    tex = nodes.new("ShaderNodeTexCoord")
    tex.location = (-720, 100)
    mineral = nodes.new("ShaderNodeTexNoise")
    mineral.name = "Subdued mineral clouds - 45 mm"
    mineral.location = (-510, 160)
    mineral.inputs["Scale"].default_value = 22.0
    mineral.inputs["Detail"].default_value = 3.0
    mineral.inputs["Roughness"].default_value = 0.55
    links.new(tex.outputs["Object"], mineral.inputs["Vector"])
    palette = nodes.new("ShaderNodeValToRGB")
    palette.name = "Restrained blue-gray stone range"
    palette.location = (-280, 160)
    palette.color_ramp.elements[0].position = 0.15
    palette.color_ramp.elements[0].color = (0.024, 0.033, 0.041, 1)
    palette.color_ramp.elements[1].position = 0.85
    palette.color_ramp.elements[1].color = (0.043, 0.054, 0.063, 1)
    links.new(mineral.outputs["Fac"], palette.inputs["Fac"])
    links.new(palette.outputs["Color"], bsdf.inputs["Base Color"])
    rough = nodes.new("ShaderNodeMapRange")
    rough.name = "Polished stone roughness 0.25-0.30"
    rough.location = (-40, -110)
    rough.inputs["To Min"].default_value = 0.25
    rough.inputs["To Max"].default_value = 0.30
    links.new(mineral.outputs["Fac"], rough.inputs["Value"])
    links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    micro = nodes.new("ShaderNodeTexNoise")
    micro.location = (-500, -260)
    micro.inputs["Scale"].default_value = 1600.0
    micro.inputs["Detail"].default_value = 2.0
    links.new(tex.outputs["Object"], micro.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.name = "Polish microstructure - 5 microns"
    bump.location = (-230, -230)
    bump.inputs["Strength"].default_value = 0.14
    bump.inputs["Distance"].default_value = 0.000005
    links.new(micro.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.location = (230, 160)
    return mat


def _cube(scene, name, location, dimensions, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = PREFIX + name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    _link(scene, obj)
    if bevel:
        mod = obj.modifiers.new("Soft machined edge", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        obj.modifiers.new("Face normals", "WEIGHTED_NORMAL")
    return obj


def _arc(scene, material):
    """A distant incomplete curved bronze reveal, not an additional prop."""
    curve = bpy.data.curves.new(PREFIX + "BronzeRevealCurve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = 0.006
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    count = 65
    spline.points.add(count - 1)
    for i, point in enumerate(spline.points):
        angle = math.radians(35 + 112 * i / (count - 1))
        point.co = (0.60 * math.cos(angle) + 0.12,
                    0.77 + 0.04 * math.sin(angle),
                    -0.45 + 0.60 * math.sin(angle), 1.0)
    obj = bpy.data.objects.new(PREFIX + "DistantBronzeCurve", curve)
    _collection(scene).objects.link(obj)
    curve.materials.append(material)
    obj["purpose"] = "Subtle defocused Alchemist architectural hint"
    return obj


def build_stage(scene, tabletop_width=1.30, tabletop_depth=1.70,
                background_hint=True, world_strength=0.018):
    """Create the tabletop and distant environment; returns names/parameters.

    Table top is exactly z=0. Cocktail origin is (0,0,0). The tabletop extends
    well beyond the camera frame so no artificial horizon bisects the stem.
    A quiet distant curve is optional via background_hint=False.
    """
    stone = _stone_material()
    table = _cube(scene, "StoneTable", (0, 0.20, -0.018),
                  (tabletop_width, tabletop_depth, 0.036), stone, bevel=0.002)
    # A broad curved matte surface prevents an apparent room corner.
    background_mat, _ = _material("CoolCharcoalBackground", (0.009, 0.014, 0.021), 0.86)
    vertices, faces = [], []
    for i in range(65):
        angle = math.radians(-80 + 160 * i / 64)
        x = 1.55 * math.sin(angle)
        y = 0.90 + 0.45 * (1 - math.cos(angle))
        vertices.extend([(x, y, -0.07), (x, y, 1.20)])
        if i:
            k = 2 * i
            faces.append((k - 2, k, k + 1, k - 1))
    mesh = bpy.data.meshes.new(PREFIX + "BackgroundMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    backdrop = bpy.data.objects.new(PREFIX + "CurvedBackdrop", mesh)
    _collection(scene).objects.link(backdrop)
    mesh.materials.append(background_mat)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    objects = [table.name, backdrop.name]
    if background_hint:
        bronze, _ = _material("MutedBronzeReveal", (0.071, 0.041, 0.021), 0.40, 0.65)
        objects.append(_arc(scene, bronze).name)
    world = bpy.data.worlds.new(PREFIX + "PhotographicWorld")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.21, 0.28, 0.42, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = world_strength
    scene.world = world
    return {"objects": objects, "world": world.name,
            "world_strength": world_strength, "tabletop_z": 0.0,
            "tabletop_material": stone.name}


def _aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_area_light(scene, name, location, target, watts, size_x, size_y, color):
    data = bpy.data.lights.new(PREFIX + name, "AREA")
    data.shape = "RECTANGLE"
    data.energy = watts
    data.size = size_x
    data.size_y = size_y
    data.color = color
    obj = bpy.data.objects.new(PREFIX + name, data)
    _collection(scene).objects.link(obj)
    obj.location = location
    _aim(obj, target)
    return obj


def build_lighting(scene, hero_height=0.18, energy_scale=1.0):
    """Create asymmetric reflection shaping lights. Return editable parameters.

    A narrow warm left key and cooler right rear edge describe the glass.
    Top light reveals liquid; much weaker broad front fill prevents dead glass.
    Names allow direct subsequent edits, e.g. bpy.data.objects[name].data.energy.
    """
    focus = hero_height * 0.56
    settings = [
        {"name": "KeyLeftSoftbox", "location": (-0.28, -0.15, 0.29),
         "target": (0, 0, focus), "watts": 6.0,
         "size_x": 0.13, "size_y": 0.32, "color": (1.0, 0.90, 0.77)},
        {"name": "RightRearStrip", "location": (0.24, 0.20, 0.25),
         "target": (0, 0, focus), "watts": 8.0,
         "size_x": 0.055, "size_y": 0.32, "color": (0.74, 0.85, 1.0)},
        {"name": "TopLiquidLight", "location": (-0.025, 0.055, 0.48),
         "target": (0, 0, hero_height * 0.78), "watts": 2.5,
         "size_x": 0.22, "size_y": 0.16, "color": (1.0, 0.93, 0.83)},
        {"name": "FrontGentleFill", "location": (0.11, -0.38, 0.21),
         "target": (0, 0, focus), "watts": 0.65,
         "size_x": 0.26, "size_y": 0.30, "color": (0.84, 0.90, 1.0)},
    ]
    result = []
    for setting in settings:
        setting = dict(setting)
        setting["watts"] *= energy_scale
        obj = add_area_light(scene, **setting)
        setting["object"] = obj.name
        result.append(setting)
    return result


def setup_camera(scene, hero_height=0.18, focus_z=None, lens_mm=95.0,
                 location=(0.0, -0.70, 0.32), fstop=8.0,
                 resolution=(960, 1200)):
    """Create a portrait full-frame camera and focus target, returning metadata.

    Vertical 36 mm sensor represents a rotated full-frame sensor. Adjust
    location or lens_mm to reframe, and focus_z to place focus on the garnish.
    """
    if focus_z is None:
        focus_z = hero_height * 0.57
    focus = bpy.data.objects.new(PREFIX + "FocusTarget", None)
    _collection(scene).objects.link(focus)
    focus.empty_display_type = "PLAIN_AXES"
    focus.empty_display_size = 0.015
    focus.location = (0.0, 0.0, focus_z)
    camera_data = bpy.data.cameras.new(PREFIX + "PortraitCamera")
    camera = bpy.data.objects.new(PREFIX + "PortraitCamera", camera_data)
    _collection(scene).objects.link(camera)
    camera.location = location
    _aim(camera, (0, 0, hero_height * 0.52))
    camera_data.lens = lens_mm
    camera_data.sensor_fit = "VERTICAL"
    camera_data.sensor_width = 24.0
    camera_data.sensor_height = 36.0
    camera_data.clip_start = 0.005
    camera_data.clip_end = 20.0
    camera_data.dof.use_dof = True
    camera_data.dof.focus_object = focus
    camera_data.dof.aperture_fstop = fstop
    camera_data.dof.aperture_blades = 9
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    return {"camera": camera.name, "focus_object": focus.name,
            "lens_mm": lens_mm, "fstop": fstop, "focus_z": focus_z,
            "location": list(location), "resolution": list(resolution)}
