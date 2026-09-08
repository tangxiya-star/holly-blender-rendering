"""Make an optimized glTF delivery from the reviewed source, never save over it.

Run with Blender in background mode. Source images/meshes are changed in this
separate process only; the resulting copy is saved as alchemist_web.blend.
"""
import hashlib
import json
import math
import struct
from collections import defaultdict
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "alchemist_05_final.blend"
WEB_BLEND = ROOT / "alchemist_web.blend"
WEB_GLB = ROOT / "alchemist_web.glb"
REPORT = ROOT / "reports" / "web_export.json"
CATEGORIES = ("Architecture", "Dome", "Tables", "Seating", "Lighting", "Glassware", "Props", "InteractionTargets")
CAMERAS = ("CAM_Arrival", "CAM_Hero", "CAM_Dome", "CAM_Table", "CAM_Exit", "WALKTHROUGH")
TARGETS = ("entrance", "hero_table", "dome", "exit")
TRIANGLE_TARGET = 350000
report = {"source": str(SOURCE), "web_blend": str(WEB_BLEND), "web_glb": str(WEB_GLB),
          "targets": {"triangles": TRIANGLE_TARGET, "meshes": 120, "bytes": 20000000},
          "warnings": [], "texture_adjustments": [], "light_approximations": []}


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def triangles(obj):
    if obj.type != "MESH":
        return 0
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def scene_counts():
    objects = list(bpy.context.scene.objects)
    return {"objects": len(objects), "mesh_objects": sum(o.type == "MESH" for o in objects),
            "triangles": sum(triangles(o) for o in objects),
            "lights": sum(o.type == "LIGHT" for o in objects),
            "cameras": [o.name for o in objects if o.type == "CAMERA"]}


def select_only(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.hide_set(False)
        obj.select_set(True)
    if objects:
        bpy.context.view_layer.objects.active = objects[0]


def category(obj):
    parent = obj.parent
    while parent:
        if parent.name in CATEGORIES:
            return parent.name
        parent = parent.parent
    for collection in obj.users_collection:
        if collection.name in CATEGORIES:
            return collection.name
    return "Architecture"


def reparent(obj, parent):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world


def protected(obj):
    return (obj.name == "Dome_Projection" or obj.name == "Counter_East5"
            or obj.name.startswith(("Entrance_Bronze_Leaf_", "Entrance_Leaf_", "Entry_Bronze_Root_Relief_"))
            or obj.get("web_keep_hero_detail", False))


def resolve_image(socket, multiplier=1.0):
    if not socket.is_linked:
        return None
    node = socket.links[0].from_node
    if node.type == "TEX_IMAGE" and node.image:
        return node, multiplier
    if node.type == "MATH" and node.operation == "MULTIPLY":
        linked = [i for i in node.inputs[:2] if i.is_linked]
        scalar = [i for i in node.inputs[:2] if not i.is_linked]
        if len(linked) == len(scalar) == 1:
            return resolve_image(linked[0], multiplier * scalar[0].default_value)
    return None


def resolve_roughness_math():
    for material in bpy.data.materials:
        if not material.use_nodes:
            continue
        bsdf = next((n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if not bsdf:
            continue
        socket = bsdf.inputs["Roughness"]
        resolved = resolve_image(socket)
        if not resolved or abs(resolved[1] - 1.0) < 1e-8:
            continue
        source_node, factor = resolved
        source = source_node.image
        pixels = np.empty(len(source.pixels), dtype=np.float32)
        source.pixels.foreach_get(pixels)
        pixels = pixels.reshape((-1, 4))
        pixels[:, :3] = np.clip(pixels[:, :3] * factor, 0, 1)
        image = bpy.data.images.new("WEB | " + source.name + " | resolved roughness", width=source.size[0], height=source.size[1], alpha=False)
        image.colorspace_settings.name = "Non-Color"
        image.pixels.foreach_set(pixels.ravel())
        image.update()
        image.file_format = "PNG"
        image.pack()
        node = material.node_tree.nodes.new("ShaderNodeTexImage")
        node.name = "WEB_RESOLVED_ROUGHNESS"
        node.image = image
        node.interpolation = source_node.interpolation
        node.extension = source_node.extension
        if source_node.inputs["Vector"].is_linked:
            material.node_tree.links.new(source_node.inputs["Vector"].links[0].from_socket, node.inputs["Vector"])
        for link in list(socket.links):
            material.node_tree.links.remove(link)
        material.node_tree.links.new(node.outputs["Color"], socket)
        socket.default_value = 1.0
        report["texture_adjustments"].append({"material": material.name, "source_image": source.name,
             "derived_image": image.name, "roughness_multiplier_baked": factor,
             "resolution": list(image.size), "packed": bool(image.packed_file)})


def simplify_object(obj, ratio):
    if ratio >= .999 or triangles(obj) < 150:
        return
    modifier = obj.modifiers.new("Web density reduction", "DECIMATE")
    modifier.decimate_type = "COLLAPSE"
    modifier.ratio = ratio
    modifier.use_collapse_triangulate = True
    select_only([obj])
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def prepare_meshes():
    # Keep the closest complete table setting alongside the separately named slab.
    target = bpy.data.objects["hero_table"].matrix_world.translation
    for obj in bpy.context.scene.objects:
        if obj.name.startswith("TableExperience_") and obj.type != "LIGHT":
            if (obj.matrix_world.translation.xy - target.xy).length < .72:
                obj["web_keep_hero_detail"] = True
    curves = [o for o in bpy.context.scene.objects if o.type in ("CURVE", "FONT", "SURFACE")]
    if curves:
        select_only(curves)
        bpy.ops.object.convert(target="MESH")
    bpy.context.view_layer.update()
    source_names = {}
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for obj in meshes:
        obj["web_source_name"] = obj.name
        source_names[obj.name] = {"category": category(obj), "world_matrix": [list(row) for row in obj.matrix_world]}
        for modifier in list(obj.modifiers):
            if obj.name.startswith("ChairBack_") and modifier.name == "Upholstery softened silhouette":
                obj.modifiers.remove(modifier)
                continue
            if modifier.type == "BEVEL" and not protected(obj):
                modifier.segments = min(modifier.segments, 1 if "Leg" in obj.name and obj.name.startswith("Chair") else 2)
        if obj.modifiers:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            evaluated = obj.evaluated_get(depsgraph)
            data = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
            old = obj.data
            obj.modifiers.clear()
            obj.data = data
            if old.users == 0:
                bpy.data.meshes.remove(old)
        ratio = 1.0
        if not protected(obj):
            if "HollowWineGlass" in obj.name:
                ratio = .26
            elif obj.name.startswith("ChairBack_"):
                ratio = .38
            elif obj.name.startswith("Chair_") and "Seat" in obj.name:
                ratio = .58
            elif "PorcelainPlate" in obj.name:
                ratio = .48
            elif obj.name.startswith("TableExperience_"):
                ratio = .66
        simplify_object(obj, ratio)
        select_only([obj])
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        obj.data.validate(verbose=False, clean_customdata=False)
    report["after_initial_simplification"] = scene_counts()
    count = report["after_initial_simplification"]["triangles"]
    if count > TRIANGLE_TARGET:
        candidates = [o for o in meshes if not protected(o) and o.name.startswith(("Chair", "TableExperience_", "Lounge_"))]
        reducible = sum(triangles(o) for o in candidates)
        ratio = max(.30, min(.95, (TRIANGLE_TARGET * .97 - (count - reducible)) / max(1, reducible)))
        for obj in candidates:
            simplify_object(obj, ratio)
        report["second_density_pass_ratio"] = ratio
    report["source_mesh_transforms"] = source_names


def merge_static():
    # Split uncommon multi-material meshes before material batching (brick veneer).
    for obj in list(bpy.context.scene.objects):
        if obj.type != "MESH" or protected(obj) or len(obj.data.materials) <= 1:
            continue
        used = {p.material_index for p in obj.data.polygons}
        if len(used) > 1:
            select_only([obj])
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.separate(type="MATERIAL")
            bpy.ops.object.mode_set(mode="OBJECT")
    batches = defaultdict(list)
    for obj in list(bpy.context.scene.objects):
        if obj.type != "MESH" or protected(obj):
            continue
        used = {p.material_index for p in obj.data.polygons}
        material = obj.data.materials[next(iter(used))] if used and obj.data.materials else None
        batches[(category(obj), material.name if material else "unassigned")].append(obj)
    mapping = defaultdict(list)
    for (group_name, material_name), objects in batches.items():
        names = sorted({o.get("web_source_name", o.name) for o in objects})
        select_only(objects)
        if len(objects) > 1:
            bpy.ops.object.join()
        obj = bpy.context.view_layer.objects.active
        short = material_name.replace("PBR | ", "").replace(" ", "_")
        obj.name = group_name + "__" + short
        obj["web_source_names"] = json.dumps(names)
        obj["web_static_batch"] = True
        reparent(obj, bpy.data.objects[group_name])
        select_only([obj])
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        for name in names:
            mapping[name].append(obj.name)
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and protected(obj):
            mapping[obj.get("web_source_name", obj.name)].append(obj.name)
    report["source_to_web_meshes"] = dict(mapping)


def runtime_lights():
    lights = [o for o in bpy.context.scene.objects if o.type == "LIGHT"]
    selected = []
    def add_prefix(prefix, limit):
        candidates = sorted((o for o in lights if o.name.startswith(prefix)), key=lambda o: o.name)
        for obj in candidates[:limit]:
            if obj not in selected:
                selected.append(obj)
    dome = [o for o in lights if o.name.startswith("Dome_Bounce")]
    if dome:
        selected.append(min(dome, key=lambda o: abs(o.matrix_world.translation.x)))
    add_prefix("Island_Warm_Pool", 3)
    table = sorted((o for o in lights if o.name.startswith("TableExperience_")), key=lambda o: o.name)
    hero = bpy.data.objects["hero_table"].matrix_world.translation
    if table:
        nearest = min(table, key=lambda o: (o.matrix_world.translation-hero).length)
        selected.append(nearest)
        indices = [0, len(table)//4, len(table)//2, len(table)*3//4, len(table)-1]
        for i in indices:
            if table[i] not in selected:
                selected.append(table[i])
        while sum(o in table for o in selected) < min(6, len(table)):
            remaining = [o for o in table if o not in selected]
            previous = [o for o in selected if o in table]
            selected.append(max(remaining, key=lambda o: min((o.matrix_world.translation-p.matrix_world.translation).length for p in previous)))
    add_prefix("Arrival_Bar_Wash", 1)
    add_prefix("Arrival_Lounge_Fill", 1)
    add_prefix("Portal_Uplight", 1)
    add_prefix("Service_Warm_Glow", 1)
    add_prefix("Street_Overcast", 1)
    add_prefix("Street_Practical", 1)
    selected = selected[:16]
    kept = {o.name for o in selected}
    for obj in lights:
        if obj.name not in kept:
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        original_type = obj.data.type
        original_energy = obj.data.energy
        if original_type == "AREA":
            old = obj.data
            data = bpy.data.lights.new(obj.name + " | web point", "POINT")
            data.color = old.color
            data.energy = old.energy * (2.0 if obj.name.startswith("Island_Warm_Pool") else .5)
            data.shadow_soft_size = .15
            obj.data = data
        obj.data.use_shadow = False
        obj["castShadow"] = False
        obj["runtime_lighting_approximation"] = True
        report["light_approximations"].append({"name": obj.name, "source_type": original_type,
              "web_type": obj.data.type, "source_blender_watts": original_energy,
              "web_blender_watts": obj.data.energy, "castShadow": False})


def validate_scene():
    scene = bpy.context.scene
    for name in ("Restaurant",) + CATEGORIES + CAMERAS + TARGETS + ("Dome_Projection", "Counter_East5"):
        if name not in scene.objects:
            raise RuntimeError("Required named node is missing: " + name)
    invalid = [o.name for o in scene.objects if o.type == "MESH" and (not o.data.vertices or not o.data.polygons)]
    if invalid:
        raise RuntimeError("Empty mesh objects: " + ", ".join(invalid))
    report["optimized_blender"] = scene_counts()
    report["missing_uvs"] = [o.name for o in scene.objects if o.type == "MESH" and not o.data.uv_layers]
    report["protected_meshes"] = [o.name for o in scene.objects if o.type == "MESH" and protected(o)]
    report["interaction_targets"] = {name: {"blender_position_m": list(scene.objects[name].matrix_world.translation),
                                     "interaction": scene.objects[name].get("interaction")} for name in TARGETS}
    report["animation"] = {"name": "Walkthrough_60s", "fps": scene.render.fps,
                            "frame_start": scene.frame_start, "frame_end": scene.frame_end,
                            "duration_seconds": (scene.frame_end-scene.frame_start)/scene.render.fps}
    for key, target in (("triangles", TRIANGLE_TARGET), ("mesh_objects", 120)):
        if report["optimized_blender"][key] > target:
            report["warnings"].append("Optimization target exceeded: " + key)


def export_glb():
    properties = {p.identifier: p for p in bpy.ops.export_scene.gltf.get_rna_type().properties}
    requested = {"filepath": str(WEB_GLB), "export_format": "GLB", "use_selection": False,
         "use_visible": False, "use_renderable": False, "export_yup": True,
         "export_apply": False, "export_normals": True, "export_texcoords": True,
         "export_materials": "EXPORT", "export_image_format": "AUTO",
         "export_cameras": True, "export_lights": True, "export_extras": True,
         "export_animations": True, "export_frame_range": True, "export_frame_step": 1,
         "export_anim_slide_to_zero": True,
         "export_force_sampling": True, "export_animation_mode": "ACTIONS",
         "export_optimize_animation_size": True, "export_draco_mesh_compression_enable": False,
         "export_shared_accessors": True, "export_lighting_mode": "SPEC"}
    accepted = {}
    for key, value in requested.items():
        prop = properties.get(key)
        if prop is None:
            continue
        if prop.type == "ENUM" and value not in {item.identifier for item in prop.enum_items}:
            continue
        accepted[key] = value
    report["export_parameters"] = accepted
    bpy.ops.export_scene.gltf(**accepted)
    raw = WEB_GLB.read_bytes()
    magic, version, byte_length = struct.unpack_from("<4sII", raw, 0)
    if magic != b"glTF" or version != 2 or byte_length != len(raw):
        raise RuntimeError("Malformed GLB header")
    length, kind = struct.unpack_from("<II", raw, 12)
    if kind != 0x4E4F534A:
        raise RuntimeError("Missing GLB JSON chunk")
    gltf = json.loads(raw[20:20+length])
    primitive_count, triangle_count = 0, 0
    for mesh in gltf.get("meshes", []):
        for primitive in mesh["primitives"]:
            primitive_count += 1
            if primitive.get("mode", 4) == 4:
                accessor = primitive.get("indices", primitive["attributes"]["POSITION"])
                triangle_count += gltf["accessors"][accessor]["count"] // 3
    names = {n.get("name") for n in gltf.get("nodes", [])}
    missing = sorted(set(("Restaurant",) + CATEGORIES + CAMERAS + TARGETS + ("Dome_Projection", "Counter_East5")) - names)
    if missing:
        raise RuntimeError("GLB dropped required nodes: " + ", ".join(missing))
    if any("bufferView" not in image for image in gltf.get("images", [])):
        raise RuntimeError("The GLB contains an external image dependency")
    animations = []
    for animation in gltf.get("animations", []):
        durations = [gltf["accessors"][s["input"]].get("max", [0])[0] for s in animation["samplers"]]
        animations.append({"name": animation.get("name"), "duration_seconds": max(durations, default=0),
                           "channels": len(animation.get("channels", []))})
    report["glb"] = {"bytes": len(raw), "megabytes_decimal": len(raw)/1000000,
         "nodes": len(gltf.get("nodes", [])), "meshes": len(gltf.get("meshes", [])),
         "primitives_estimated_draw_calls": primitive_count, "triangles": triangle_count,
         "materials": len(gltf.get("materials", [])), "images": len(gltf.get("images", [])),
         "embedded_images": sum("bufferView" in i for i in gltf.get("images", [])),
         "cameras": len(gltf.get("cameras", [])), "animations": animations,
         "punctual_lights": len(gltf.get("extensions", {}).get("KHR_lights_punctual", {}).get("lights", [])),
         "extensions_used": gltf.get("extensionsUsed", []),
         "sha256": hashlib.sha256(raw).hexdigest()}
    if len(raw) > 20000000:
        report["warnings"].append("20 MB file-size target exceeded")
    if not animations:
        raise RuntimeError("The GLB contains no walkthrough animation")


def integration_notes():
    summary = report["glb"]
    text = f"""# Web integration

`alchemist_web.glb` is the optimized delivery; `alchemist_web.blend` is its editable web copy. The reviewed high-quality source remains `alchemist_05_final.blend`.

- Actual GLB: {summary['triangles']:,} triangles, {summary['meshes']} meshes, {summary['primitives_estimated_draw_calls']} material primitives, {summary['megabytes_decimal']:.2f} MB. Counts are asset counts, not a performance guarantee.
- glTF uses **Y up, meters**. Blender source is Z up. Let GLTFLoader apply the export axis conversion; do not add another X rotation. Keep the Restaurant root at unit scale for the authored 1.65 m pedestrian camera height.
- Hierarchy: Restaurant → Architecture, Dome, Tables, Seating, Lighting, Glassware, Props, InteractionTargets. Named cameras are CAM_Arrival, CAM_Hero, CAM_Dome, CAM_Table, CAM_Exit, and WALKTHROUGH. Static batches retain source object names in `userData.web_source_names` as a JSON string; the report contains the complete source-to-batch mapping and original mesh transforms.
- `Walkthrough_60s` animates the WALKTHROUGH camera for 60 seconds. Use an AnimationMixer on the loaded scene and render through that camera. Static camera choices do not require animation. Set perspective camera aspect and call updateProjectionMatrix on viewport changes.
- Interaction empties `entrance`, `hero_table`, `dome`, and `exit` retain `userData.interaction`. Get their world positions with getWorldPosition. Empties have no raycast surface: add application-owned invisible hit proxies or raycast the named door leaves, Counter_East5, and Dome_Projection. Navigation/collision logic and door-opening animation belong to the host application; this asset supplies spatial targets and the camera tour.
- Door leaves and sculptural reliefs, the hero counter/nearby setting, and projection dome remain separate. Other static surfaces are combined by category and material to reduce draw calls. The camera-guide curve PATH_Walkthrough and planning camera are excluded.
- Image base color, roughness, normal maps, transmission, clearcoat, sheen, and emission are retained in GLB. The stone roughness Multiply ×0.68 was resolved to a packed derived Non-Color image, rather than discarding its texture. The projection material is `PROJECTION | replace this image`; replace its emissiveMap for a different show while preserving its UV mapping.
- There are {summary['punctual_lights']} shadowless punctual runtime lights. The selection retains one central dome bounce, all three centerline island pools, six representative table spots, two arrival lights, one portal light, one service light, and two street lights. Area lights have been approximated as points at half their source Blender wattage, except the island pools, which use twice the source wattage (8 W each) to preserve the warm centerline depth. Table spots retain the authored warm color and cone. All visible lamp meshes remain. Set `castShadow=false` after load. Tune intensity/exposure for the host renderer; Cycles light visibility flags and area shape are not supported by glTF punctual lights.
- **Interior environment required:** load `textures/restaurant_environment.exr` with EXRLoader and PMREMGenerator, and assign the PMREM texture to `scene.environment` while inside the restaurant. Do not set it as the background: the dome and architecture supply the visible room. On exit, restore the travel world's environment. The environment supplies broad interior reflection/ambient color, not spatially correct baked GI. Browser glass, contacts, reflections, and shadows will differ from the Cycles reference renders.
- The environment EXR is a separate integration artifact and is not embedded in GLB. No Draco decoder is required. glTF material extensions require a GLTFLoader version that supports the extensions listed in reports/web_export.json.

Three.js structure (equivalent R3F useGLTF/useFrame integration):

```js
const asset = await new GLTFLoader().loadAsync('/alchemist_web.glb');
scene.add(asset.scene);
asset.scene.traverse(o => {{ if (o.isLight) o.castShadow = false; }});
const camera = asset.scene.getObjectByName('WALKTHROUGH');
const mixer = new THREE.AnimationMixer(asset.scene);
const clip = asset.animations.find(a => a.name === 'Walkthrough_60s') || asset.animations[0];
const action = mixer.clipAction(clip);
action.setLoop(THREE.LoopOnce, 1);
action.clampWhenFinished = true;
action.play();
const exr = await new EXRLoader().loadAsync('/textures/restaurant_environment.exr');
const pmrem = new THREE.PMREMGenerator(renderer);
const interiorEnvironment = pmrem.fromEquirectangular(exr).texture;
const exteriorEnvironment = scene.environment;
scene.environment = interiorEnvironment; // restore exteriorEnvironment on exit
// Each frame: mixer.update(deltaSeconds); renderer.render(scene, camera);
```

GLB structural validation is recorded in web_export.json. A separate loader/reimport validation and any browser performance measurements must be reported separately. No browser performance claim is made here.
"""
    (ROOT / "reports" / "web_integration.md").write_text(text)


if __name__ == "__main__":
    if not SOURCE.is_file():
        raise SystemExit("Reviewed final source is not ready; no output written")
    source_hash = file_hash(SOURCE)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.preferences.filepaths.save_version = 0
    report["blender_version"] = bpy.app.version_string
    report["source_sha256"] = source_hash
    report["source_counts_before_evaluation"] = scene_counts()
    for obj in list(scene.objects):
        if obj.name == "PATH_Walkthrough" or (obj.type == "CAMERA" and obj.name not in CAMERAS):
            bpy.data.objects.remove(obj, do_unlink=True)
    for name in CAMERAS:
        reparent(bpy.data.objects[name], bpy.data.objects["Restaurant"])
    resolve_roughness_math()
    runtime_lights()
    prepare_meshes()
    print("WEB_MESH_REDUCTION " + json.dumps(scene_counts()), flush=True)
    merge_static()
    validate_scene()
    scene.camera = bpy.data.objects["CAM_Hero"]
    scene.frame_set(1)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(WEB_BLEND))
    export_glb()
    if file_hash(SOURCE) != source_hash:
        raise RuntimeError("Reviewed source file changed during web export")
    report["source_file_unchanged"] = True
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    integration_notes()
    print("WEB_EXPORT_COMPLETE " + json.dumps(report["glb"]))
