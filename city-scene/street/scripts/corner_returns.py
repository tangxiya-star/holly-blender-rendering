"""Windowed corner returns for the eight exposed ends of the hero blocks.

Call build_corner_returns() after architecture has been built/loaded.  It edits
only the corresponding original side-shell faces and creates facade detail;
the existing building volume, floor elevations and roof remain unchanged.
"""
import json
import math
import random
from pathlib import Path

import bpy

import architecture as arch

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = "Architecture_Corner_Returns"
BOUNDARIES = [-45.5, -34.5, 46.5, 57.5]


def _collection():
    collection=bpy.data.collections.get(COLLECTION)
    if collection is None:
        collection=bpy.data.collections.new(COLLECTION)
        bpy.context.scene.collection.children.link(collection)
    return collection


def _own(obj):
    collection=_collection()
    if collection not in obj.users_collection:
        collection.objects.link(obj)
    for other in list(obj.users_collection):
        if other != collection:
            other.objects.unlink(obj)


def _cut_side_shell(spec, boundary):
    original=bpy.data.objects.get("Building_"+str(spec["id"]))
    if original is None:
        raise RuntimeError("Missing detailed building: "+str(spec["id"]))
    material_name="CPH_Arch_Facade_"+str(spec["id"])
    wall_obj=next((obj for obj in original.children
                   if obj.type=="MESH" and any(mat and mat.name==material_name for mat in obj.data.materials)),None)
    if wall_obj is None:
        raise RuntimeError("Missing original facade material mesh: "+material_name)
    # Original Batch order is side wall at local negative X, then positive X.
    # Derive the exposed local edge from the source rotation, not world side.
    width=float(spec["width"])
    rotation=float(spec["rotation"])
    center_y=float(spec["origin"][1])
    edge=min([-1,1],key=lambda sign:abs(center_y+math.sin(rotation)*sign*width/2-boundary))
    start=0 if edge<0 else 8
    doomed=set(range(start,start+8))
    data=wall_obj.data
    vertices=[tuple(v.co) for v in data.vertices]
    faces=[tuple(poly.vertices) for poly in data.polygons
           if not set(poly.vertices).issubset(doomed)]
    removed=len(data.polygons)-len(faces)
    # Keep all source vertex indices, making a second invocation a no-op cut.
    if removed:
        data.clear_geometry()
        data.from_pydata(vertices,[],faces)
        data.update()
    original["corner_return_side"]=edge
    original["corner_return_boundary_y"]=boundary
    return wall_obj.data.materials[0],removed


def _return(spec,boundary,p):
    wall,removed=_cut_side_shell(spec,boundary)
    ident=str(spec["id"])
    rng=random.Random(int(spec["seed"])+68013)
    side=-1 if float(spec["origin"][0])<0 else 1
    depth=float(spec.get("depth",12))
    width=depth
    height=float(spec["height"])
    floors=int(spec["floors"])
    ground=3.65
    storey=(height-ground)/max(floors-1,1)
    # North-of-intersection walls face south; south walls face north.
    rotation=0 if float(spec["origin"][1])>boundary else math.pi
    root=bpy.data.objects.new("Corner_Return_"+ident,None)
    _collection().objects.link(root)
    root.location=(side*(9+depth/2),boundary,float(spec["origin"][2]))
    root.rotation_euler.z=rotation
    root["source_building"]=ident
    root["facade_width_m"]=width
    root["genuine_window_openings"]=True
    root["existing_roof_retained"]=True
    batch=arch.Batch()
    frame=rng.choice([p["frame_cream"],p["ivory"],p["frame_gray"]])
    trim=p["trim"]
    source_shop=str(spec.get("shop","")).strip()
    if not source_shop:
        source_shop="KAFFE" if side<0 else "ATELIER"
    arch._shop(batch,p,rng,width,height,source_shop,root,"Return_"+ident)
    batch.box(p["stone"],(0,.18,.17),(width,.40,.34))
    # Five narrow Copenhagen bays across the existing 12 m side shell.
    bays=5 if width>=11 else 4
    margin=1.13
    pitch=(width-2*margin)/(bays-1)
    win_width=min(1.17,pitch-.72)
    centers=[-width/2+margin+i*pitch for i in range(bays)]
    for level in range(floors-1):
        base=ground+level*storey
        wh=min(1.94 if level==0 else 1.89,storey-.98)
        bottom=base+.50
        top=bottom+wh
        batch.box(wall,(0,.17,(base+bottom)/2),(width,.34,bottom-base))
        batch.box(wall,(0,.17,(top+base+storey)/2),(width,.34,base+storey-top))
        edge=-width/2
        for x in centers:
            left=x-win_width/2
            if left>edge:
                batch.box(wall,((edge+left)/2,.17,(bottom+top)/2),(left-edge,.34,wh))
            arch._window(batch,p,rng,x,bottom,win_width,wh,frame,False)
            edge=x+win_width/2
        if edge<width/2:
            batch.box(wall,((edge+width/2)/2,.17,(bottom+top)/2),(width/2-edge,.34,wh))
        if level==0:
            batch.box(trim,(0,.055,base+.055),(width+.025,.25,.055))
    # Continue the restrained eave moulding around the corner without adding
    # a second roof or a second solid building box.
    for z,depth_trim,thickness in [(height-.19,.30,.10),(height-.09,.39,.075),(height+.035,.49,.12)]:
        batch.box(trim,(0,.025,z),(width+.06,depth_trim,thickness))
    objects=batch.finish("Corner_Return_"+ident,root)
    for child in list(root.children):
        _own(child)
    return {"source":ident,"boundary_y":boundary,"rotation":rotation,
            "width":width,"height":height,"removed_shell_faces":removed,
            "mesh_objects":len(objects)}


def build_corner_returns():
    registry=json.loads((ROOT/"reports"/"building_registry.json").read_text())
    if isinstance(registry,dict):
        registry=registry.get("buildings",registry.get("registry",[]))
    owned=bpy.data.collections.get(COLLECTION)
    if owned:
        for obj in list(owned.objects):
            bpy.data.objects.remove(obj,do_unlink=True)
    palette=arch._palette()
    results=[]
    for spec in registry:
        if not str(spec["id"]).startswith("Hero_"):
            continue
        for boundary in BOUNDARIES:
            distance=min(abs(float(spec["origin"][1])+sign*float(spec["width"])/2-boundary)
                         for sign in [-1,1])
            if distance<.015:
                results.append(_return(spec,boundary,palette))
    if len(results)!=8:
        raise RuntimeError("Expected eight exposed corner returns, found "+str(len(results)))
    bpy.context.view_layer.update()
    (ROOT/"reports"/"corner_returns_report.json").write_text(json.dumps(results,indent=2))
    print("Corner returns complete:",len(results),"facades",flush=True)
    return results


if __name__=="__main__":
    build_corner_returns()
