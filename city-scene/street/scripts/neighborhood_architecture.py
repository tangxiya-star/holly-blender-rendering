"""Add an inhabited eastern street and open both connecting intersections.

This module owns only Architecture_Neighborhood_Additions and the twenty
replaced eastern Cross buildings. The original registry remains untouched.
"""
import json
import math
import random
from pathlib import Path

import bpy
import architecture as arch
import corner_returns

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = "Architecture_Neighborhood_Additions"
BOUNDARIES = (-45.5, -34.5, 46.5, 57.5)


def _collection():
    result = bpy.data.collections.get(COLLECTION)
    if result is None:
        result = bpy.data.collections.new(COLLECTION)
        bpy.context.scene.collection.children.link(result)
    return result


def _tree(root):
    return [root] + list(root.children_recursive)


def _own(root):
    collection = _collection()
    for obj in _tree(root):
        if collection not in obj.users_collection:
            collection.objects.link(obj)
        for previous in list(obj.users_collection):
            if previous != collection:
                previous.objects.unlink(obj)
        obj["neighborhood_addition"] = True


def _delete_tree(root):
    if root:
        for obj in reversed(_tree(root)):
            bpy.data.objects.remove(obj, do_unlink=True)


def _spec(ident, origin, rotation, width, serial, quiet=False):
    palette = [
        ("brick", [.36, .155, .078]),
        ("brick", [.48, .37, .185]),
        ("plaster", [.63, .625, .52]),
        ("brick", [.285, .115, .062]),
        ("plaster", [.55, .405, .20]),
        ("brick", [.42, .30, .145]),
    ]
    style, color = palette[serial % len(palette)]
    floors = 3 if quiet and serial % 4 == 1 else 4
    return {
        "id": ident, "origin": [*origin, .18], "rotation": rotation,
        "width": width, "depth": 12, "height": 3.65 + (floors-1)*3.05,
        "floors": floors, "seed": 49003 + serial*137,
        "style": style, "color": color,
        "shop": ["ATELIER", "GALLERI", "BOGHANDEL", "KAFFE"][serial % 4],
        "neighborhood": "eastern residential street" if quiet else "connecting cross street",
        "residential_ground": quiet and serial % 3 != 0,
    }


def neighborhood_specs():
    """Deterministic parcels, with a clear 14 m street between x=57 and 71."""
    specs = []
    # The central 81 m block has eight narrow parcels per side. The outside
    # rows close the views beyond both junctions without sealing the loop.
    spans = [(-65, -45.5, [9.4, 10.1]),
             (-34.5, 46.5, [9.3, 11.2, 8.8, 10.7, 9.8, 11.3, 9.9, 10.0]),
             (57.5, 82, [12.0, 12.5])]
    for side, x, rotation in [(-1, 57, math.pi/2), (1, 71, -math.pi/2)]:
        for segment, (start, end, widths) in enumerate(spans):
            assert abs(sum(widths)-(end-start)) < 1e-6
            cursor = start
            for i, width in enumerate(widths):
                specs.append(_spec("Neighborhood_Quiet_%s_%s_%02d" % (side, segment, i),
                                   (x, cursor+width/2), rotation, width, len(specs), True))
                cursor += width
    # Facade returns occupy x=45..57 and x=71..83. New perpendicular
    # buildings therefore stop before those existing corner volumes.
    for street_y in (-40, 52):
        for side in (-1, 1):
            y = street_y + side*5.5
            rotation = math.pi if side < 0 else 0
            for parcel, (start, end) in enumerate([(21, 32.5), (32.5, 45), (83, 94)]):
                specs.append(_spec("Neighborhood_Cross_%s_%s_%s" % (street_y, side, parcel),
                                   ((start+end)/2, y), rotation, end-start, len(specs)))
    for end, y, rotation in [("South", -78, math.pi), ("North", 95, 0)]:
        specs.append(_spec("Neighborhood_End_"+end, (64, y), rotation, 28, len(specs), True))
    return specs


def _residential_front(spec, palette):
    """Quiet homes have linen behind the ground windows and discreet numbers."""
    root = bpy.data.objects["Building_"+spec["id"]]
    green = arch._material("Neighborhood_Door_green", (.055, .105, .075), .54, texture="paint")
    for obj in root.children:
        if obj.type == "MESH":
            for index, material in enumerate(obj.data.materials):
                if material and material.name.startswith("CPH_Arch_Shop_paint_"):
                    obj.data.materials[index] = green
    if not spec.get("residential_ground"):
        return
    for obj in list(root.children):
        if obj.type == "FONT" and obj.name.endswith("_shop_sign"):
            bpy.data.objects.remove(obj, do_unlink=True)
    batch = arch.Batch()
    width = float(spec["width"])
    bays = max(3, round(width/2.65))
    pitch = width/bays
    door_x = float(root.get("doorway_local_x", 0))
    for i in range(bays):
        x = -width/2+(i+.5)*pitch
        if abs(x-door_x) < .1:
            continue
        for sign in (-1, 1):
            arch._curtain(batch, palette["curtain_white"], x+sign*pitch*.27,
                          .63, .57, pitch*.29, 2.02, i*.9)
    batch.finish("Residential_Linen_"+spec["id"], root)
    arch._sign("Residential_Number_"+spec["id"], str(8+spec["seed"]%40),
               (door_x, -.13, 3.16), .21, palette["sign"], root)


def build_neighborhood_architecture():
    source = json.loads((ROOT/"reports"/"building_registry.json").read_text())
    if isinstance(source, dict):
        source = source.get("buildings", source.get("registry", []))
    replace = [spec for spec in source
               if str(spec["id"]).startswith("Cross_") and float(spec["origin"][0]) > 21]
    if len(replace) != 20:
        raise RuntimeError("Expected 20 eastern cross-street buildings; found %s" % len(replace))
    old = bpy.data.collections.get(COLLECTION)
    if old:
        for obj in list(old.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    for spec in replace:
        _delete_tree(bpy.data.objects.get("Building_"+str(spec["id"])))
    removed_ids = {spec["id"] for spec in replace}
    retained = [spec for spec in source if spec["id"] not in removed_ids]
    additions = neighborhood_specs()
    palette = arch._palette()
    details = []
    for spec in additions:
        details.append(arch._build_one(spec, palette))
        if spec["neighborhood"] == "eastern residential street":
            _residential_front(spec, palette)
        _own(bpy.data.objects["Building_"+spec["id"]])
    returns = []
    for spec in additions:
        if not spec["id"].startswith("Neighborhood_Quiet_"):
            continue
        for boundary in BOUNDARIES:
            edge_distance = min(abs(spec["origin"][1]+sign*spec["width"]/2-boundary)
                                for sign in (-1, 1))
            if edge_distance > .015:
                continue
            result = corner_returns._return(spec, boundary, palette)
            root = bpy.data.objects["Corner_Return_"+spec["id"]]
            root.location.x = 51 if spec["origin"][0] == 57 else 77
            doorway_x = float(root.get("doorway_local_x", 0))
            root["doorway_world_xyz"] = [root.location.x+math.cos(root.rotation_euler.z)*doorway_x,
                                          root.location.y+math.sin(root.rotation_euler.z)*doorway_x,
                                          root.location.z+.15]
            result["origin"] = list(root.location)
            _own(root)
            returns.append(result)
    if len(returns) != 8:
        raise RuntimeError("Expected eight eastern corner returns; found %s" % len(returns))
    registry = retained+additions
    (ROOT/"reports"/"neighborhood_registry.json").write_text(json.dumps(registry, indent=2))
    bpy.context.scene["neighborhood_buildings"] = len(registry)
    bpy.context.scene["neighborhood_fourth_street_x"] = 64.0
    bpy.context.view_layer.update()
    summary = {"buildings": len(registry), "retained_buildings": len(retained),
               "removed_buildings": len(replace), "added_buildings": len(additions),
               "corner_returns": returns, "details": details}
    print("Neighborhood architecture complete:", len(registry), "buildings;",
          len(additions), "added;", len(returns), "windowed corner returns", flush=True)
    return summary


if __name__ == "__main__":
    build_neighborhood_architecture()
