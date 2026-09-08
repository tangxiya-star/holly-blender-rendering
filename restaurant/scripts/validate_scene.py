"""Read-only architectural and walkthrough audit for an open Blender scene.

Usage:
  blender --background alchemist.blend --python validate_scene.py -- \
    --report restaurant/reports/validation.json

The current scene is inspected, never saved or edited. Animation evaluation
temporarily changes the current frame and restores it before writing the report.
Clearance is an approximation using radial rays and swept side rays, not a
physics simulation or an accessibility/building-code certification.
"""

import argparse
import json
import math
import os
from pathlib import Path
import sys
import traceback

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


SECTIONS = ("Architecture", "Dome", "Tables", "Seating", "Lighting",
            "Glassware", "Props", "InteractionTargets")
CAMERAS = ("CAM_Arrival", "CAM_Hero", "CAM_Dome", "CAM_Table", "CAM_Exit")
INTERACTIONS = ("entrance", "hero_table", "dome", "exit")
COLLISION_SECTIONS = {"architecture", "tables", "seating", "dome"}
EXCLUDED_SECTIONS = {"glassware", "props", "lighting", "interactiontargets"}
STRUCTURAL_WORDS = ("floor", "ground", "wall", "door", "column", "counter",
                    "chair", "seat", "table", "booth", "banquette", "stair",
                    "step", "ramp", "plinth", "platform", "partition", "railing")


def finite(values):
    return all(math.isfinite(float(value)) for value in values)


def rounded_vector(value):
    return [round(float(component), 5) for component in value]


def normalized_name(name):
    return name.lower().split(".")[0]


def lineage(obj):
    result = []
    current = obj
    while current is not None:
        result.append(current.name)
        current = current.parent
    return result


def tags_for(obj):
    return {normalized_name(name) for name in lineage(obj)} | {
        normalized_name(collection.name) for collection in obj.users_collection}


def classify_collision(obj):
    """Use authored groups first; names only support ungrouped structural meshes."""
    tags = tags_for(obj)
    if tags & EXCLUDED_SECTIONS:
        return None
    if "architecture" in tags:
        return "architecture"
    if tags & COLLISION_SECTIONS:
        return "furniture_or_dome"
    lower_name = obj.name.lower()
    if any(word in lower_name for word in STRUCTURAL_WORDS):
        return "architecture" if any(word in lower_name for word in (
            "floor", "ground", "wall", "stair", "step", "ramp", "plinth",
            "platform", "door", "column")) else "furniture_or_dome"
    return None


def check_hierarchy(scene):
    root = scene.objects.get("Restaurant")
    result = {"restaurant_root": None, "sections": {}, "cameras": {},
              "interaction_targets": {}, "walkthrough_camera": None,
              "walkthrough_path": None, "findings": []}
    if root:
        result["restaurant_root"] = {"type": root.type, "parent":
                                     root.parent.name if root.parent else None}
    if not root or root.type != "EMPTY":
        result["findings"].append("Expected Restaurant root empty is missing or has another type.")
    for name in SECTIONS:
        obj = scene.objects.get(name)
        result["sections"][name] = None if not obj else {
            "type": obj.type, "parent": obj.parent.name if obj.parent else None,
            "under_restaurant": "Restaurant" in lineage(obj)[1:]}
        if not obj or obj.type != "EMPTY" or "Restaurant" not in lineage(obj)[1:]:
            result["findings"].append("Section %s is missing, is not an empty, or is outside Restaurant." % name)
    for name in CAMERAS:
        obj = scene.objects.get(name)
        result["cameras"][name] = bool(obj and obj.type == "CAMERA")
        if not result["cameras"][name]:
            result["findings"].append("Expected camera %s is missing." % name)
    for name in INTERACTIONS:
        # Exact names are preferred; a case-insensitive lookup is still reported.
        obj = scene.objects.get(name)
        if obj is None:
            obj = next((item for item in scene.objects if item.type == "EMPTY"
                        and item.name.lower() == name), None)
        result["interaction_targets"][name] = None if not obj else {
            "name": obj.name, "type": obj.type,
            "under_interaction_targets": "InteractionTargets" in lineage(obj)[1:]}
        if not obj or obj.type != "EMPTY":
            result["findings"].append("Expected interaction empty %s is missing." % name)
        elif "InteractionTargets" not in lineage(obj)[1:]:
            result["findings"].append("Interaction empty %s is outside InteractionTargets." % name)
    for name, key, expected_type in (("WALKTHROUGH", "walkthrough_camera", "CAMERA"),
                                     ("PATH_Walkthrough", "walkthrough_path", "CURVE")):
        obj = scene.objects.get(name)
        result[key] = None if not obj else {"name": obj.name, "type": obj.type}
        if not obj or obj.type != expected_type:
            result["findings"].append("Expected %s %s is missing." % (expected_type.lower(), name))
    return result


def check_assets():
    checked, missing, packed = [], [], []

    def check(kind, datablock, filepath):
        if not filepath:
            return
        if getattr(datablock, "packed_file", None) or getattr(datablock, "packed_files", None):
            packed.append({"kind": kind, "name": datablock.name})
            return
        absolute = bpy.path.abspath(filepath, library=getattr(datablock, "library", None))
        absolute = os.path.expanduser(absolute)
        paths = [absolute]
        if "<UDIM>" in absolute:
            tiles = getattr(datablock, "tiles", [])
            paths = [absolute.replace("<UDIM>", str(tile.number)) for tile in tiles]
            if not paths:
                paths = [absolute.replace("<UDIM>", "1001")]
        for path in paths:
            entry = {"kind": kind, "name": datablock.name, "path": path,
                     "exists": os.path.isfile(path)}
            checked.append(entry)
            if not entry["exists"]:
                missing.append(entry)

    for image in bpy.data.images:
        if image.source not in {"GENERATED", "VIEWER"}:
            check("image", image, image.filepath)
    for kind, collection in (("library", bpy.data.libraries), ("sound", bpy.data.sounds),
                             ("movieclip", bpy.data.movieclips), ("font", bpy.data.fonts),
                             ("cache_file", bpy.data.cache_files)):
        for block in collection:
            path = getattr(block, "filepath", "")
            if path != "<builtin>":
                check(kind, block, path)
    return {"checked": checked, "packed": packed, "missing": missing,
            "scope": "File-backed images, libraries, sounds, movie clips, fonts and cache files; sequence checks cover the referenced file, not every frame."}


def check_transforms(scene):
    invalid, scaled, negative = [], [], []
    for obj in scene.objects:
        matrix_values = [value for row in obj.matrix_world for value in row]
        if not finite(matrix_values) or not finite(obj.location) or not finite(obj.scale):
            invalid.append(obj.name)
            continue
        if any(abs(value - 1.0) > 1e-5 for value in obj.scale):
            scaled.append({"object": obj.name, "type": obj.type,
                           "scale": rounded_vector(obj.scale)})
        if obj.matrix_world.to_3x3().determinant() < 0:
            negative.append(obj.name)
    return {"nonfinite_transforms": invalid, "unapplied_local_scales": scaled,
            "negative_world_determinant": negative,
            "note": "Non-unit scales are review items, not automatic defects; negative determinants may reverse orientation."}


class CollisionIndex:
    def __init__(self):
        self.vertices = []
        self.triangles = []
        self.object_names = []
        self.tree = None

    def add(self, vertices, triangles, name):
        offset = len(self.vertices)
        self.vertices.extend(vertices)
        self.triangles.extend(tuple(offset + vertex for vertex in triangle) for triangle in triangles)
        self.object_names.extend([name] * len(triangles))

    def build(self):
        if self.triangles:
            self.tree = BVHTree.FromPolygons(self.vertices, self.triangles, all_triangles=True)
        # BVH owns its coordinates. Retain only the face-to-object mapping.
        self.vertices = []
        self.triangles = []

    def cast(self, origin, direction, distance):
        if not self.tree or distance <= 1e-8:
            return None
        position, normal, polygon, hit_distance = self.tree.ray_cast(origin, direction, distance)
        if position is None:
            return None
        return {"object": self.object_names[polygon], "position": position,
                "normal": normal, "distance": float(hit_distance)}


def inspect_geometry(scene, depsgraph):
    objects, failures, invalid_vertices = [], [], []
    collision, architecture = CollisionIndex(), CollisionIndex()
    triangle_total, vertex_total = 0, 0
    collision_names = []
    for obj in scene.objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = None
        try:
            mesh = evaluated.to_mesh()
            mesh.calc_loop_triangles()
            triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
            vertex_count = len(mesh.vertices)
            triangle_total += len(triangles)
            vertex_total += vertex_count
            kind = classify_collision(obj)
            objects.append({"object": obj.name, "vertices": vertex_count,
                            "evaluated_triangles": len(triangles), "collision_group": kind,
                            "hidden_render": bool(obj.hide_render)})
            if kind is None:
                # Finite mesh coordinates are checked even when excluded from collision.
                if any(not finite(vertex.co) for vertex in mesh.vertices):
                    invalid_vertices.append(obj.name)
                continue
            vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
            if any(not finite(vertex) for vertex in vertices):
                invalid_vertices.append(obj.name)
                continue
            collision.add(vertices, triangles, obj.name)
            if kind == "architecture":
                architecture.add(vertices, triangles, obj.name)
            collision_names.append(obj.name)
        except Exception as error:
            failures.append({"object": obj.name, "error": str(error)})
        finally:
            if mesh is not None:
                evaluated.to_mesh_clear()
    collision.build()
    architecture.build()
    instances = sum(1 for instance in depsgraph.object_instances if instance.is_instance)
    animated_collision = [name for name in collision_names if (
        scene.objects[name].animation_data or scene.objects[name].constraints or
        any(parent.animation_data or parent.constraints for parent in parents(scene.objects[name])))]
    return {"mesh_objects": len(objects), "evaluated_vertices": vertex_total,
            "evaluated_triangles": triangle_total, "objects": objects,
            "evaluation_errors": failures, "nonfinite_mesh_vertices": invalid_vertices,
            "additional_dependency_graph_instances": instances,
            "collision_objects": collision_names,
            "potentially_animated_collision_objects": animated_collision,
            "count_scope": "Evaluated scene mesh objects; additional collection/particle instances are counted separately and are not included in triangle totals or collision rays."}, collision, architecture


def parents(obj):
    parent = obj.parent
    while parent:
        yield parent
        parent = parent.parent


def event_ranges(samples, field):
    """Summarize consecutive flagged samples without hiding frame-level evidence."""
    result, current = [], None
    for sample in samples:
        value = sample.get(field)
        if value:
            if current is None:
                current = {"first_frame": sample["frame"], "last_frame": sample["frame"],
                           "sample_count": 0, "objects": set()}
                result.append(current)
            current["last_frame"] = sample["frame"]
            current["sample_count"] += 1
            if isinstance(value, list):
                current["objects"].update(item["object"] for item in value
                                          if isinstance(item, dict) and "object" in item)
        else:
            current = None
    for event in result:
        event["objects"] = sorted(event["objects"])
    return result


def inspect_walkthrough(scene, collision, ground, args, meters_per_unit):
    camera = scene.objects.get("WALKTHROUGH")
    result = {"camera": "WALKTHROUGH", "sample_step_frames": args.frame_step,
              "clearance_radius_m": args.radius, "reference_eye_height_m": args.eye_height,
              "samples": [], "findings": [],
              "method": "Evaluated camera positions; 16 horizontal radial rays at four body heights, swept center/side rays between samples, and five downward ground probes. Geometry is frozen at the first sampled frame.",
              "limitations": ["Ray sampling approximates a standing capsule and can miss fully enclosed penetration, diagonal corners or moving geometry.",
                              "Small props, glassware, lighting and non-mesh helpers are excluded.",
                              "Downward support probes use Architecture geometry, accept either normal winding, and identify support height; they do not infer semantic walkable surfaces."]}
    if not camera or camera.type != "CAMERA":
        result["findings"].append("Walkthrough camera is unavailable; clearance was not evaluated.")
        return result
    if collision.tree is None or ground.tree is None:
        result["findings"].append("Collision or architectural support geometry is empty; missing probe hits are inconclusive.")
    unit = 1.0 / meters_per_unit
    radius = args.radius * unit
    eye_height = args.eye_height * unit
    body_offsets = [(height - args.eye_height) * unit
                    for height in (0.25, 0.85, 1.40, args.eye_height)]
    directions = [Vector((math.cos(index * math.tau / 16),
                          math.sin(index * math.tau / 16), 0)) for index in range(16)]
    frames = list(range(scene.frame_start, scene.frame_end + 1, args.frame_step))
    if frames[-1] != scene.frame_end:
        frames.append(scene.frame_end)
    previous, previous_ground, total_length = None, None, 0.0
    all_positions = []
    for frame in frames:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        matrix = camera.evaluated_get(depsgraph).matrix_world
        position = matrix.translation.copy()
        sample = {"frame": frame, "position_m": rounded_vector(position * meters_per_unit)}
        if not finite(position):
            sample["invalid_camera_position"] = True
            result["samples"].append(sample)
            previous = None
            continue
        all_positions.append(position.copy())
        camera_right = matrix.to_3x3() @ Vector((1, 0, 0))
        camera_right.z = 0
        if camera_right.length < 1e-6:
            camera_right = Vector((1, 0, 0))
        camera_right.normalize()
        forward = Vector((-camera_right.y, camera_right.x, 0))
        contacts = {}
        for offset in body_offsets:
            origin = position + Vector((0, 0, offset))
            for direction in directions:
                hit = collision.cast(origin, direction, radius)
                if hit and hit["distance"] < radius - 0.001 * unit:
                    name = hit["object"]
                    entry = contacts.setdefault(name, {"object": name,
                                                       "minimum_clearance_m": args.radius,
                                                       "body_heights_m": []})
                    entry["minimum_clearance_m"] = round(min(entry["minimum_clearance_m"],
                                                               hit["distance"] * meters_per_unit), 4)
                    height = round((offset + eye_height) * meters_per_unit, 3)
                    if height not in entry["body_heights_m"]:
                        entry["body_heights_m"].append(height)
        sample["clearance_contacts"] = list(contacts.values())
        sweep_hits = {}
        if previous is not None:
            delta = position - previous
            total_length += delta.length * meters_per_unit
            sample["travel_since_previous_sample_m"] = round(delta.length * meters_per_unit, 5)
            if delta.length > 1e-8:
                sweep_side = Vector((-delta.y, delta.x, 0))
                if sweep_side.length > 1e-8:
                    sweep_side.normalize()
                else:
                    sweep_side = camera_right
                for side in (-radius, 0, radius):
                    for offset in body_offsets:
                        start = previous + sweep_side * side + Vector((0, 0, offset))
                        hit = collision.cast(start, delta.normalized(), delta.length)
                        if hit:
                            sweep_hits[hit["object"]] = {"object": hit["object"],
                                                         "position_m": rounded_vector(hit["position"] * meters_per_unit)}
        sample["sweep_contacts"] = list(sweep_hits.values())
        supports, missing_probes = [], []
        probes = (("center", Vector((0, 0, 0))), ("left", -camera_right * radius),
                  ("right", camera_right * radius), ("front", forward * radius),
                  ("back", -forward * radius))
        for label, offset in probes:
            hit = ground.cast(position + offset, Vector((0, 0, -1)), 4.0 * unit)
            if not hit or abs(hit["normal"].z) < 0.55:
                missing_probes.append(label)
                continue
            supports.append({"probe": label, "object": hit["object"],
                             "ground_z_m": round(hit["position"].z * meters_per_unit, 4),
                             "eye_height_m": round(hit["distance"] * meters_per_unit, 4)})
        sample["ground_supports"] = supports
        sample["missing_ground_probes"] = missing_probes
        sample["ground_height_discontinuity"] = False
        sample["eye_height_outside_review_band"] = False
        central = next((support for support in supports if support["probe"] == "center"), None)
        if central:
            sample["eye_height_outside_review_band"] = not 1.10 <= central["eye_height_m"] <= 2.20
            if previous_ground is not None:
                change = abs(central["ground_z_m"] - previous_ground)
                sample["ground_step_since_previous_sample_m"] = round(change, 4)
                sample["ground_height_discontinuity"] = change > 0.22
            previous_ground = central["ground_z_m"]
        else:
            previous_ground = None
        if supports:
            sample["ground_height_spread_m"] = round(max(item["ground_z_m"] for item in supports)
                                                      - min(item["ground_z_m"] for item in supports), 4)
            if sample["ground_height_spread_m"] > 0.22:
                sample["ground_height_discontinuity"] = True
        previous = position.copy()
        result["samples"].append(sample)
    result["sample_count"] = len(result["samples"])
    result["path_length_m"] = round(total_length, 4)
    if all_positions:
        result["camera_bounds_m"] = {
            "min": [round(min(point[axis] for point in all_positions) * meters_per_unit, 4) for axis in range(3)],
            "max": [round(max(point[axis] for point in all_positions) * meters_per_unit, 4) for axis in range(3)]}
    result["events"] = {field: event_ranges(result["samples"], field) for field in (
        "clearance_contacts", "sweep_contacts", "missing_ground_probes",
        "ground_height_discontinuity", "eye_height_outside_review_band", "invalid_camera_position")}
    if total_length < 0.05 and len(frames) > 1:
        result["findings"].append("WALKTHROUGH camera moves less than 5 cm over the scene frame range; verify path animation and constraints.")
    return result


def sanitize(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", type=Path,
                        default=Path(__file__).resolve().parents[1] / "reports" / "validation.json")
    parser.add_argument("--frame-step", type=int, default=1,
                        help="Sample every N frames; default 1 checks every frame.")
    parser.add_argument("--radius", type=float, default=0.25, help="Horizontal body clearance radius in meters.")
    parser.add_argument("--eye-height", type=float, default=1.65, help="Standing eye height used to estimate body sample heights.")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    if args.frame_step < 1 or args.radius <= 0 or args.eye_height <= 0:
        parser.error("frame-step, radius and eye-height must be positive")
    scene = bpy.context.scene
    original_frame, original_subframe = scene.frame_current, scene.frame_subframe
    scale = float(scene.unit_settings.scale_length)
    meters_per_unit = scale if math.isfinite(scale) and scale > 0 else 1.0
    report = {
        "schema_version": 1, "scene_file": bpy.data.filepath,
        "blender_version": bpy.app.version_string, "scene": scene.name,
        "usage": "blender --background <scene.blend> --python restaurant/scripts/validate_scene.py -- --report restaurant/reports/validation.json",
        "read_only": "No scene datablocks are changed or saved; the original frame/subframe is restored.",
        "units": {"system": scene.unit_settings.system, "meters_per_blender_unit": meters_per_unit,
                  "length_unit": scene.unit_settings.length_unit},
        "frame_range": [scene.frame_start, scene.frame_end], "issues": []}
    try:
        scene.frame_set(scene.frame_start)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        report["hierarchy"] = check_hierarchy(scene)
        report["assets"] = check_assets()
        report["transforms"] = check_transforms(scene)
        report["geometry"], collision, ground = inspect_geometry(scene, depsgraph)
        report["walkthrough"] = inspect_walkthrough(scene, collision, ground, args, meters_per_unit)

        def issue(severity, code, detail, count=None):
            item = {"severity": severity, "code": code, "detail": detail}
            if count is not None:
                item["count"] = count
            report["issues"].append(item)

        for finding in report["hierarchy"]["findings"]:
            issue("warning", "hierarchy", finding)
        if report["assets"]["missing"]:
            issue("error", "missing_assets", "Referenced external files are missing.", len(report["assets"]["missing"]))
        for key in ("nonfinite_transforms",):
            if report["transforms"][key]:
                issue("error", key, "Invalid numeric transforms require correction.", len(report["transforms"][key]))
        if report["transforms"]["unapplied_local_scales"]:
            issue("info", "unapplied_scales", "Review non-unit object scales before export.", len(report["transforms"]["unapplied_local_scales"]))
        for key in ("evaluation_errors", "nonfinite_mesh_vertices"):
            if report["geometry"][key]:
                issue("error", key, "Some mesh geometry could not be validated.", len(report["geometry"][key]))
        if report["geometry"]["additional_dependency_graph_instances"]:
            issue("warning", "unmeasured_instances", "Additional instances are outside mesh and collision coverage.", report["geometry"]["additional_dependency_graph_instances"])
        if report["geometry"]["potentially_animated_collision_objects"]:
            issue("warning", "static_collision_snapshot", "Potentially animated collision geometry was sampled only at the first frame.", len(report["geometry"]["potentially_animated_collision_objects"]))
        if scene.unit_settings.system != "METRIC" or abs(meters_per_unit - 1.0) > 1e-5:
            issue("warning", "unit_convention", "Scene differs from the expected metric / one Blender unit per meter convention; probes were converted using scale_length.")
        for finding in report["walkthrough"]["findings"]:
            issue("warning", "walkthrough_setup", finding)
        for field, events in report["walkthrough"].get("events", {}).items():
            if events:
                issue("error" if field == "invalid_camera_position" else "warning",
                      field, "Review the frame ranges and probe evidence in walkthrough.events.",
                      sum(event["sample_count"] for event in events))
    except Exception as error:
        report["issues"].append({"severity": "error", "code": "validation_exception", "detail": str(error)})
        report["exception_traceback"] = traceback.format_exc()
    finally:
        scene.frame_set(original_frame, subframe=original_subframe)
    counts = {level: sum(issue["severity"] == level for issue in report["issues"])
              for level in ("error", "warning", "info")}
    report["summary"] = {"status": "errors" if counts["error"] else "review" if counts["warning"] else "pass",
                         "issue_counts": counts,
                         "note": "Warnings identify review items; absence of ray hits is not proof of a fully collision-free route."}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(sanitize(report), indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"validation_report": str(args.report.resolve()), **report["summary"]}))


if __name__ == "__main__":
    main()
