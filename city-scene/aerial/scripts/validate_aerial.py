"""Read-only QA for the saved Copenhagen aerial scene.

Run in Blender after opening copenhagen_aerial.blend. The script evaluates the
complete 1..673 flight, checks its swept path against scene geometry, probes the
roof height from above (so a camera inside a building cannot pass), and writes
reports/scene_validation.json. Camera/frame selection is restored afterward.
No scene geometry, animation, or saved .blend file is changed.
"""
import json
import math
import time
import traceback
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
TARGET_XY = (1470.0, 490.0)
GROUND_Z = 2.0


def _load(path, default=None):
    if path.exists():
        return json.loads(path.read_text())
    return default


def _finite(values):
    return all(math.isfinite(float(v)) for v in values)


def _bounds(obj):
    points = [obj.matrix_world @ Vector(p) for p in obj.bound_box]
    return {"min":[min(p[i] for p in points) for i in range(3)],
            "max":[max(p[i] for p in points) for i in range(3)]}


def _percentiles(values):
    if len(values)==0:
        return None
    result = np.percentile(values,[0,5,25,50,75,95,99,100])
    return dict(zip(["min","p05","p25","median","p75","p95","p99","max"],
                    [round(float(v),3) for v in result]))


def _distance_bbox(point, bounds):
    return math.hypot(*[max(bounds["min"][i]-point[i],0,point[i]-bounds["max"][i]) for i in range(2)])


class _Report:
    def __init__(self):
        self.issues=[]
        self.checks=[]

    def issue(self,severity,code,message,action,details=None):
        value={"severity":severity,"code":code,"message":message,"action":action}
        if details is not None:
            value["details"]=details
        self.issues.append(value)

    def check(self,name,passed,details=None):
        value={"name":name,"status":"pass" if passed else "fail"}
        if details is not None:
            value["details"]=details
        self.checks.append(value)


def _geometry_report(report,geo):
    collection=bpy.data.collections.get("Copenhagen_City_Massing")
    objects=[o for o in collection.all_objects if o.type=="MESH"] if collection else []
    if not objects:
        report.issue("error","city_missing","No city massing meshes exist.",
                     "Open the completed aerial .blend or rerun the massing stage.")
        return {"mesh_objects":0}
    recorded=json.loads(bpy.context.scene.get("city_massing_stats","{}"))
    actual_count=sum(int(o.get("building_count",0)) for o in objects)
    source_count=len(geo.get("buildings",[])) if geo else recorded.get("source_buildings",81774)
    ratio=actual_count/max(source_count,1)
    count_ok=actual_count==recorded.get("buildings",actual_count) and .98<=ratio<=1.001
    report.check("Footprint inventory survives saved-scene batching",count_ok,
                 {"source_footprints":source_count,"scene_building_count":actual_count,
                  "recorded_building_count":recorded.get("buildings"),"retained_fraction":round(ratio,6)})
    if not count_ok:
        report.issue("error" if ratio<.95 or ratio>1.001 else "warning","building_inventory_mismatch",
                     "Scene building counts do not reconcile with the source footprint inventory.",
                     "Inspect massing skipped records and duplicate or missing tile meshes.",
                     {"source":source_count,"scene":actual_count,"recorded":recorded.get("buildings")})
    if recorded.get("skipped"):
        report.issue("warning","footprints_skipped","Some source footprints failed geometry conversion.",
                     "Review the listed polygons and repair or explicitly document omissions.",recorded["skipped"][:25])
    all_bounds=[];lod_counts={"1":0,"2":0,"3":0};lod3=[];roof_heights=[]
    bad_bounds=[];bad_materials=[];faces=vertices=0
    for obj in objects:
        bounds=_bounds(obj);all_bounds.append(bounds)
        if not _finite(bounds["min"]+bounds["max"]):
            bad_bounds.append(obj.name)
        lod=str(obj.get("lod",0));lod_counts[lod]=lod_counts.get(lod,0)+int(obj.get("building_count",0))
        if lod=="3":
            lod3.append({"name":obj.name,"buildings":int(obj.get("building_count",0)),"bounds":bounds})
        mesh=obj.data;faces+=len(mesh.polygons);vertices+=len(mesh.vertices)
        if not mesh.materials or any(m is None for m in mesh.materials):
            bad_materials.append(obj.name)
        roof_slots=[i for i,m in enumerate(mesh.materials) if m and "roof" in m.name.lower()
                    and "edge" not in m.name.lower()]
        if not roof_slots or not len(mesh.polygons):
            continue
        centers=np.empty(len(mesh.polygons)*3,dtype=np.float32)
        indices=np.empty(len(mesh.polygons),dtype=np.int32)
        mesh.polygons.foreach_get("center",centers)
        mesh.polygons.foreach_get("material_index",indices)
        centers=centers.reshape((-1,3));mask=np.isin(indices,roof_slots)
        row=np.array(tuple(obj.matrix_world[2])[:3],dtype=np.float64)
        heights=centers[mask]@row+obj.matrix_world[2][3]-GROUND_Z
        roof_heights.append(heights)
    bounds={"min":[min(b["min"][i] for b in all_bounds) for i in range(3)],
            "max":[max(b["max"][i] for b in all_bounds) for i in range(3)]}
    heights=np.concatenate(roof_heights) if roof_heights else np.array([])
    height_stats=_percentiles(heights)
    report.check("Massing has finite geographic bounds",not bad_bounds,bounds)
    if bad_bounds:
        report.issue("error","nonfinite_city_bounds","Some tile coordinates are not finite.",
                     "Repair corrupted source coordinates or nonfinite object transforms.",bad_bounds)
    if bounds["max"][0]-bounds["min"][0]<9000 or bounds["max"][1]-bounds["min"][1]<9000:
        report.issue("error","city_extent_too_small","The city mesh does not cover the intended roughly12km geographic extent.",
                     "Check input geography coverage and whether all massing tiles were linked to the scene.",bounds)
    if height_stats and (height_stats["min"]<.5 or height_stats["max"]>220):
        report.issue("warning","roof_height_outliers","Roof geometry contains implausible height outliers above the2m land datum.",
                     "Inspect unusually low service buildings, height units, landmark overrides, and the ground offset.",height_stats)
    datums={float(o.get("ground_datum_m",-999)) for o in objects}
    report.check("Building bases use the same2m datum as land",datums=={GROUND_Z},sorted(datums))
    if datums!={GROUND_Z}:
        report.issue("error","ground_datum_mismatch","Massing ground datum differs from the land and landmark datum.",
                     "Apply the shared2m ground offset in the massing builder and rebuild affected tiles.",sorted(datums))
    lod3_ok=bool(lod3) and all(_distance_bbox(TARGET_XY,o["bounds"])<=201 for o in lod3)
    report.check("Highest geometry detail is present around Nyhavn",lod3_ok,
                 {"target_xy":TARGET_XY,"lod_buildings":lod_counts,"lod3_tiles":len(lod3)})
    if not lod3_ok:
        report.issue("error","lod3_misplaced","Nyhavn lacks LOD3 geometry or some LOD3 tiles are far outside its200m neighborhood.",
                     "Check target_xy and whether camera and geographic coordinates use the same origin.",lod3)
    if bad_materials:
        report.issue("error","missing_city_materials","Some massing meshes have missing material slots.",
                     "Restore the shared facade and roof palette before saving.",bad_materials)
    if faces>6000000:
        report.issue("warning","city_mesh_budget","City massing exceeds six million polygons.",
                     "Reduce distant roof detail or unnecessary source-geometry subdivision.",{"faces":faces})
    return {"source_footprints":source_count,"scene_building_count":actual_count,
            "mesh_objects":len(objects),"faces":faces,"vertices":vertices,"world_bounds":bounds,
            "roof_face_height_percentiles_above_land_m":height_stats,
            "roof_faces_below_land":int(np.count_nonzero(heights<0)) if len(heights) else 0,
            "lod_building_counts":lod_counts,"lod3_tiles":lod3}


def _atmosphere(obj):
    if "haze" in obj.name.lower() or "atmosphere" in obj.name.lower():
        return True
    materials=[slot.material for slot in obj.material_slots if slot.material]
    if not materials:
        return False
    for material in materials:
        if not material.use_nodes:
            return False
        output=next((n for n in material.node_tree.nodes if n.type=="OUTPUT_MATERIAL" and n.is_active_output),None)
        if output is None or output.inputs["Surface"].is_linked or not output.inputs["Volume"].is_linked:
            return False
    return True


def _ray(scene,depsgraph,origin,direction,distance):
    origin=Vector(origin);direction=Vector(direction).normalized();travelled=0.0
    for _ in range(12):
        hit,location,normal,index,obj,matrix=scene.ray_cast(depsgraph,origin,direction,distance=distance-travelled)
        if not hit:
            return None
        travelled+=(location-origin).length
        if obj and obj.type=="MESH" and not _atmosphere(obj) and not obj.hide_render:
            return {"location":[float(v) for v in location],"distance":float(travelled),
                    "object":obj.name,"face_index":int(index),"normal":[float(v) for v in normal]}
        origin=location+direction*.02;travelled+=.02
        if travelled>=distance:
            return None
    return None


def _roof_probe(scene,depsgraph,xy,camera_z):
    # Start above all solid buildings, including the camera when it is high.
    # Probing from the camera alone would incorrectly pass an embedded camera.
    top=max(500.0,camera_z+50)
    return _ray(scene,depsgraph,(xy[0],xy[1],top),(0,0,-1),top+100)


def _flight_report(report):
    scene=bpy.context.scene
    camera=next((o for o in scene.objects if o.type=="CAMERA" and o.name.startswith("05 |")),None)
    cameras=[o.name for o in scene.objects if o.type=="CAMERA"]
    if camera is None:
        report.issue("error","flight_camera_missing","Camera05 CINEMATIC DIVE is missing.",
                     "Run the aerial camera builder and save the scene.")
        return {"camera_names":cameras}
    range_ok=scene.frame_start<=1 and scene.frame_end>=673
    report.check("Full673-frame dive is available",range_ok,
                 {"scene_range":[scene.frame_start,scene.frame_end],"camera":camera.name})
    if not range_ok:
        report.issue("error","flight_frame_range","The timeline does not include the full descent.",
                     "Restore frames1–673 and check the animated camera action.")
    if not camera.animation_data or not camera.animation_data.action:
        report.issue("error","flight_not_animated","Camera05 has no active object animation action.",
                     "Rebuild or reconnect its location and orientation keyframes.")
    fps=scene.render.fps/max(scene.render.fps_base,.001)
    samples=[];collisions=[];near_misses=[];missing_ground=[];path_hits=[];surroundings={}
    previous=None;previous_q=None;previous_speed=None
    max_speed=max_acceleration=max_rotation=0.0;uphill=[]
    started=time.time()
    for frame in range(1,674):
        scene.frame_set(frame);depsgraph=bpy.context.evaluated_depsgraph_get()
        evaluated=camera.evaluated_get(depsgraph);matrix=evaluated.matrix_world
        position=matrix.translation.copy();quaternion=matrix.to_quaternion()
        if not _finite(position):
            report.issue("error","nonfinite_camera","The flight contains a nonfinite camera position.",
                         "Repair the animation keys or interpolation.",{"frame":frame})
            continue
        below=_roof_probe(scene,depsgraph,position[:2],position.z)
        clearance=position.z-below["location"][2] if below else None
        sample={"frame":frame,"position":[round(float(v),4) for v in position],
                "lens_mm":round(float(evaluated.data.lens),4),
                "clearance_below_m":round(clearance,4) if clearance is not None else None,
                "surface_below":below["object"] if below else None}
        if below is None:
            missing_ground.append(frame)
        elif clearance<1:
            collisions.append({"frame":frame,"clearance_m":clearance,"surface":below})
        elif clearance<5:
            near_misses.append({"frame":frame,"clearance_m":clearance,"surface":below["object"]})
        if previous is not None:
            delta=position-previous;speed=delta.length*fps;max_speed=max(max_speed,speed)
            if previous_speed is not None:
                max_acceleration=max(max_acceleration,abs(speed-previous_speed)*fps)
            if delta.length>.0001:
                obstacle=_ray(scene,depsgraph,previous,delta,delta.length)
                if obstacle:
                    path_hits.append({"from_frame":frame-1,"to_frame":frame,"hit":obstacle})
            if delta.z>.1:
                uphill.append({"frame":frame,"rise_m":float(delta.z)})
            rotation=quaternion.rotation_difference(previous_q).angle
            rotation=min(rotation,abs(2*math.pi-rotation))*fps*180/math.pi
            max_rotation=max(max_rotation,rotation)
            previous_speed=speed
        if frame in (577,625,649,661,673):
            probes=[]
            for radius in (1.0,3.0,10.0,25.0):
                for i in range(8):
                    angle=i*math.tau/8;xy=(position.x+radius*math.cos(angle),position.y+radius*math.sin(angle))
                    roof=_roof_probe(scene,depsgraph,xy,position.z)
                    probes.append({"radius_m":radius,"azimuth_degrees":i*45,"xy":xy,
                                   "clearance_m":float(position.z-roof["location"][2]) if roof else None,
                                   "object":roof["object"] if roof else None})
            close=[p for p in probes if p["radius_m"]<=3 and p["clearance_m"] is not None and p["clearance_m"]<1]
            if close:
                collisions.append({"frame":frame,"camera_body_near_structure":close})
            direction=quaternion@Vector((0,0,-1))
            forward=_ray(scene,depsgraph,position,direction,10000)
            near_plane=[]
            for corner in evaluated.data.view_frame(scene=scene):
                # Camera view_frame corners are at an arbitrary local depth;
                # scale them to the actual near clipping plane before testing.
                local=corner*(evaluated.data.clip_start/max(-corner.z,.0001))
                end=matrix@local;ray=end-position
                hit=_ray(scene,depsgraph,position,ray,ray.length)
                if hit:
                    near_plane.append(hit)
            if near_plane:
                collisions.append({"frame":frame,"near_clip_plane_obstructions":near_plane})
            surroundings[str(frame)]={"position":sample["position"],"probes":probes,
                                      "forward_first_surface":forward,"near_clip_obstructions":near_plane}
        samples.append(sample);previous=position;previous_q=quaternion
        if frame%112==0:
            print("Aerial validation: flight geometry",frame,"/673",flush=True)
    report.check("Flight stays above solid roofs and terrain",not collisions,
                 {"collision_samples":len(collisions),"minimum_clearance_m":min(
                     (s["clearance_below_m"] for s in samples if s["clearance_below_m"] is not None),default=None)})
    report.check("Swept flight segments avoid scene surfaces",not path_hits,{"intersections":len(path_hits)})
    if collisions or path_hits:
        report.issue("error","camera_collision","The descent intersects or approaches a solid surface within1m.",
                     "Raise or move the indicated flight keys, then rerun the entire path validation.",
                     {"samples":collisions[:20],"path_segments":path_hits[:20]})
    if near_misses:
        report.issue("warning","camera_low_clearance","The descent has less than5m vertical clearance.",
                     "Review these frames in Cycles and raise the approach if the tight clearance is unintended.",near_misses[:20])
    if missing_ground:
        report.issue("warning","flight_outside_geography","Some flight samples have no solid surface underneath.",
                     "Check coastline/water coverage and confirm the approach does not expose an empty world edge.",missing_ground[:25])
    if max_speed>500 or max_acceleration>500 or max_rotation>120:
        report.issue("warning","flight_motion_discontinuity","The flight has unusually fast movement or sharp interpolation changes.",
                     "Inspect the camera curve and neighboring keys around the reported peaks.",
                     {"max_speed_m_s":max_speed,"max_acceleration_m_s2":max_acceleration,"max_rotation_deg_s":max_rotation})
    if samples:
        descent=samples[0]["position"][2]-samples[-1]["position"][2]
        travel=math.dist(samples[0]["position"],samples[-1]["position"])
        report.check("Camera performs a city-to-Nyhavn descent",descent>2500 and travel>5000,
                     {"descent_m":descent,"start_to_end_distance_m":travel,"final_altitude_m":samples[-1]["position"][2]})
        if descent<=2500 or travel<=5000:
            report.issue("error","flight_motion_missing","The camera does not execute the expected large-scale descent.",
                         "Check that Camera05 was animated and its saved action is evaluated.")
    return {"camera":camera.name,"camera_names":cameras,"fps":fps,"samples":samples,
            "surroundings":surroundings,"collision_samples":collisions,"swept_path_hits":path_hits,
            "near_misses":near_misses,"missing_ground_frames":missing_ground,
            "max_speed_m_s":round(max_speed,3),"max_acceleration_m_s2":round(max_acceleration,3),
            "max_rotation_deg_s":round(max_rotation,3),"upward_steps":uphill,
            "validation_seconds":round(time.time()-started,2)}


def _assets_report(report):
    images=[];missing=[]
    for image in bpy.data.images:
        if image.source not in {"FILE","TILED","MOVIE","SEQUENCE"}:
            continue
        packed=bool(image.packed_file) or bool(getattr(image,"packed_files",[]))
        path=Path(bpy.path.abspath(image.filepath,library=image.library)) if image.filepath else None
        exists=bool(path and path.exists())
        if path and image.source=="TILED" and "<UDIM>" in str(path):
            exists=any(path.parent.glob(path.name.replace("<UDIM>","[0-9][0-9][0-9][0-9]")))
        entry={"image":image.name,"path":str(path) if path else None,"packed":packed,"exists":exists}
        images.append(entry)
        if not packed and not exists:
            missing.append(entry)
    report.check("External image assets are available or packed",not missing,{"image_assets":len(images)})
    if missing:
        report.issue("error","missing_textures","The scene references missing, unpacked image files.",
                     "Restore the listed files or pack the images before delivery.",missing)
    materials=len(bpy.data.materials)
    if materials>256:
        report.issue("warning","material_count_high","The scene has an unexpectedly large material inventory.",
                     "Check for accidentally unique materials per building; retain a shared aerial palette.",{"materials":materials})
    report.check("Aerial materials remain shared",materials<=256,{"material_count":materials})
    return {"materials":materials,"images":images,"missing_images":missing,
            "scene_objects":len(bpy.context.scene.objects),"cameras":sum(o.type=="CAMERA" for o in bpy.context.scene.objects)}


def validate_aerial():
    scene=bpy.context.scene;old_frame=scene.frame_current;old_camera=scene.camera
    report=_Report();started=time.time()
    result={"scene":scene.name,"blend_file":bpy.data.filepath,
            "validation_scope":"Saved mesh inventory, city bounds/roof heights, all673 camera frames and swept segments, final approach neighborhood and asset availability"}
    try:
        geo=_load(ROOT/"data"/"copenhagen_geo.json",{})
        result["geometry"]=_geometry_report(report,geo)
        result["assets"]=_assets_report(report)
        result["flight"]=_flight_report(report)
    except Exception as error:
        report.issue("error","validation_runtime_error","A validation stage could not complete: "+str(error),
                     "Fix the reported validation/runtime error and rerun QA; an incomplete audit is not a pass.",
                     traceback.format_exc())
        raise
    finally:
        scene.frame_set(old_frame);scene.camera=old_camera
        result["checks"]=report.checks;result["issues"]=report.issues
        result["status"]="fail" if any(i["severity"]=="error" for i in report.issues) else (
            "review" if report.issues else "pass")
        result["elapsed_seconds"]=round(time.time()-started,2)
        (ROOT/"reports").mkdir(parents=True,exist_ok=True)
        (ROOT/"reports"/"scene_validation.json").write_text(json.dumps(result,indent=2,ensure_ascii=False))
        print("Aerial scene validation:",result["status"],";",len(report.issues),"issues; report:",
              str(ROOT/"reports"/"scene_validation.json"),flush=True)
    return result


if __name__=="__main__":
    validate_aerial()
