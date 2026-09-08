"""Read-only static and animated-door audit; no render, scene save, or BVH rebuild.

From the repository root:
blender --background restaurant/alchemist_06a_refine.blend --python restaurant/scripts/validate_refine06.py
The report is the sole written artifact. Existing source validation is retained
as a provenance baseline, not represented as a fresh full-room collision test.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from validate_scene import check_assets, check_hierarchy, check_transforms


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def coordinates(mesh):
    co = np.empty(len(mesh.vertices)*3, dtype=np.float32)
    mesh.vertices.foreach_get('co', co)
    return co.reshape((-1,3))


def distance_to_box(point, low, high):
    return math.hypot(max(low[0]-point.x, 0, point.x-high[0]),
                      max(low[1]-point.y, 0, point.y-high[1]))


def inspect(scene):
    began = time.time()
    original_frame, original_subframe = scene.frame_current, scene.frame_subframe
    current_file = Path(bpy.data.filepath)
    current_hash = digest(current_file)
    build = json.loads((ROOT/'reports/refine06_build.json').read_text())
    baseline_file = ROOT/'reports/final_validation.json'
    baseline = json.loads(baseline_file.read_text())
    old_samples = {row['frame']:Vector(row['position_m']) for row in baseline['walkthrough']['samples']}
    source = ROOT/build['source']
    issues = []
    source_match = digest(source) == build['source_sha256']
    if not source_match: issues.append({'severity':'error','code':'source_hash_changed'})
    snapshots = {}
    for name in ('refine06_door.py','refine06_furniture.py','refine06_surfaces.py','build_refine06.py'):
        live, saved = ROOT/'scripts'/name, ROOT/'reports/refine06_sources'/name
        snapshots[name] = {'current_sha256':digest(live),'build_snapshot_sha256':digest(saved),
                           'current_matches_build_snapshot':digest(live)==digest(saved)}
    door_snapshot = (ROOT/'reports/refine06_sources/refine06_door.py').read_text()
    bound_code = all(text in door_snapshot for text in ('z=soft_max(z,.065,.003)',
                                                      'z=-soft_max(-z,-4.155,.003)',
                                                      'y=soft_max(y,-.170,.002)'))
    scene.frame_set(1)
    hierarchy, assets, transforms = check_hierarchy(scene), check_assets(), check_transforms(scene)
    invalid_mesh, invalid_curves, empty_mesh = [], [], []
    vertices = triangles = mesh_count = 0
    door_bounds = {}
    for obj in scene.objects:
        if obj.type == 'MESH':
            mesh_count += 1
            co = coordinates(obj.data)
            vertices += len(co)
            triangles += sum(max(0,len(p.vertices)-2) for p in obj.data.polygons)
            if not len(co): empty_mesh.append(obj.name); continue
            if not np.isfinite(co).all(): invalid_mesh.append(obj.name)
            if obj.name.startswith('REF06_Door_'):
                door_bounds[obj.name] = {'local_min':co.min(axis=0).tolist(),
                                         'local_max':co.max(axis=0).tolist(),
                                         'parent':obj.parent.name if obj.parent else None,
                                         'vertices':len(co)}
        elif obj.type == 'CURVE':
            for spline in obj.data.splines:
                points = spline.bezier_points if spline.type == 'BEZIER' else spline.points
                if any(not all(math.isfinite(c) for c in point.co) for point in points):
                    invalid_curves.append(obj.name); break
    if invalid_mesh or invalid_curves or transforms['nonfinite_transforms']:
        issues.append({'severity':'error','code':'nonfinite_geometry_or_transform'})
    if assets['missing']: issues.append({'severity':'error','code':'missing_assets'})
    if hierarchy['findings']: issues.append({'severity':'error','code':'hierarchy'})
    if not bound_code: issues.append({'severity':'warning','code':'door_snapshot_lacks_soft_bounds'})

    hinges = [scene.objects.get('REF06_Door_'+side+'_Hinge') for side in ('Left','Right')]
    if not all(hinges): raise RuntimeError('Expected two animated entrance hinges are absent.')
    boxes = {}
    for hinge in hinges:
        children = [o for o in scene.objects if o.parent == hinge and o.type == 'MESH']
        transformed = []
        for child in children:
            co = coordinates(child.data)
            mat = np.array(child.matrix_local, dtype=np.float64)
            transformed.append(co @ mat[:3,:3].T + mat[:3,3])
        all_co = np.concatenate(transformed)
        boxes[hinge.name] = (all_co.min(axis=0).tolist(),all_co.max(axis=0).tolist())
    bridge = scene.objects.get('Floor_Threshold_Bridge')
    bridge_info = None
    if bridge:
        world = [bridge.matrix_world@Vector(v) for v in bridge.bound_box]
        bridge_info = {'name':bridge.name,'world_min':[min(p[a] for p in world) for a in range(3)],
                       'world_max':[max(p[a] for p in world) for a in range(3)],
                       'hidden_render':bridge.hide_render,'hidden_viewport':bridge.hide_viewport}
    else: issues.append({'severity':'error','code':'threshold_bridge_missing'})
    zmin = min(bounds[0][2] for bounds in boxes.values())
    zmax = max(bounds[1][2] for bounds in boxes.values())
    if bridge_info and zmin < bridge_info['world_max'][2]:
        issues.append({'severity':'error','code':'closed_door_below_threshold_top'})

    camera = scene.objects['WALKTHROUGH']
    radius = .25
    samples, contacts, poses, path_drift = [], [], {}, []
    minima = {h.name:{'clearance_m':float('inf'),'sample_frame':None} for h in hinges}
    continuous_bound = {'clearance_m':float('inf'),'sample_interval':None}
    previous = None
    # Half-frame evaluations conservatively cover both every rendered frame and
    # the intervening motion; each leaf is replaced by its full depth envelope.
    for tick in range((scene.frame_end-scene.frame_start)*2+1):
        stamp = scene.frame_start+tick/2
        frame = int(stamp)
        scene.frame_set(frame, subframe=stamp-frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        person = camera.evaluated_get(depsgraph).matrix_world.translation.copy()
        if not all(math.isfinite(c) for c in person):
            issues.append({'severity':'error','code':'nonfinite_camera','frame':stamp}); continue
        row = {'frame':stamp,'camera_m':[round(c,6) for c in person],'leaf_clearance_m':{}}
        corner_sets = {}
        for hinge in hinges:
            matrix = hinge.evaluated_get(depsgraph).matrix_world.copy()
            local = matrix.inverted()@person
            low, high = boxes[hinge.name]
            # Standing collision cylinder spans 0.10..1.85 m above route ground.
            ground = person.z-1.65
            overlaps_z = high[2] >= ground+.10 and low[2] <= ground+1.85
            gap = distance_to_box(local,low,high)-radius if overlaps_z else float('inf')
            row['leaf_clearance_m'][hinge.name] = round(gap,6)
            if gap < minima[hinge.name]['clearance_m']:
                minima[hinge.name] = {'clearance_m':gap,'sample_frame':stamp}
            if gap < 0: contacts.append({'frame':stamp,'leaf':hinge.name,'clearance_m':gap})
            corner_sets[hinge.name] = [matrix@Vector((x,y,0)) for x in (low[0],high[0]) for y in (low[1],high[1])]
            if previous:
                movement = (person-previous['person']).length
                angular_chord = max((a-b).length for a,b in zip(corner_sets[hinge.name],previous['corners'][hinge.name]))
                # Adding full endpoint displacement is conservative for these tiny
                # monotone half-frame rotations; report a bound, not mesh contact.
                lower = min(gap,previous['gaps'][hinge.name])-movement-angular_chord
                if lower < continuous_bound['clearance_m']:
                    continuous_bound = {'clearance_m':lower,'sample_interval':[previous['frame'],stamp]}
        if tick%2 == 0:
            samples.append(row)
            if frame in old_samples:
                drift = (person-old_samples[frame]).length
                if drift > .00002: path_drift.append({'frame':frame,'meters':drift})
            if frame in (1,40,85,110):
                poses[str(frame)] = {h.name:round(math.degrees(h.rotation_euler.z),6) for h in hinges}
        previous = {'frame':stamp,'person':person,'corners':corner_sets,
                    'gaps':{k:float(v) for k,v in row['leaf_clearance_m'].items()}}
    if contacts: issues.append({'severity':'error','code':'dynamic_door_clearance_contact','count':len(contacts)})
    if continuous_bound['clearance_m'] <= 0:
        issues.append({'severity':'warning','code':'inter_sample_door_clearance_not_proven'})
    if path_drift: issues.append({'severity':'error','code':'walkthrough_changed_from_source','count':len(path_drift)})
    scene.frame_set(original_frame, subframe=original_subframe)
    unchanged_file = digest(current_file) == current_hash
    return {'scene_file':str(current_file),'scene_sha256':current_hash,'blender_version':bpy.app.version_string,
            'read_only_scene_file_unchanged':unchanged_file,'elapsed_seconds':round(time.time()-began,2),
            'source_baseline':{'source':str(source),'source_sha256':digest(source),
                               'matches_build_source_sha256':source_match,
                               'validation_report':str(baseline_file),'validation_sha256':digest(baseline_file),
                               'inherited_static_events':baseline['walkthrough']['events'],
                               'baseline_is_reused_not_a_new_full_room_collision_test':True},
            'script_snapshots':snapshots,'door_soft_bound_correction_in_build_snapshot':bound_code,
            'hierarchy':hierarchy,'assets':assets,'transforms':transforms,
            'geometry':{'objects':len(scene.objects),'mesh_objects':mesh_count,'base_vertices':vertices,
                        'base_triangles':triangles,'nonfinite_meshes':invalid_mesh,
                        'nonfinite_curves':invalid_curves,'empty_meshes':empty_mesh},
            'door':{'mesh_bounds':door_bounds,'hinge_local_full_geometry_envelopes':boxes,
                    'overall_z_min_m':zmin,'overall_z_max_m':zmax,'hinge_poses_degrees':poses,
                    'threshold_bridge':bridge_info,
                    'root_relief_bounds_corrected':all(v['local_min'][2]>=.06499 and v['local_max'][2]<=4.15501
                                                      and v['local_min'][1]>=-.17001 for k,v in door_bounds.items()
                                                      if k.endswith('TwistedTrunksAndCarvedBark'))},
            'dynamic_walkthrough':{'sampled_integer_frames':len(samples),'half_frame_evaluations':tick+1,
                                   'clearance_radius_m':radius,'minimum_leaf_clearance':minima,
                                   'conservative_inter_sample_bound':continuous_bound,
                                   'contacts':contacts,'path_drift_from_validated_source':path_drift,'samples':samples},
            'limitations':['Moving-door test uses a conservative complete local rectangle for each full leaf and standing vertical cylinder; decorative voids are treated as solid.',
                           'Static room clearance uses the preserved source validation baseline; this pass checks geometry finiteness, hierarchy, threshold presence and unchanged sampled camera path, not every altered furnishing collision.',
                           'Local door envelope assumes the existing Z-axis hinge animation with no scaling or tilting.',
                           'Base mesh finiteness is checked; shader appearance, future edits and physical building-code compliance are outside this audit.'],
            'issues':issues,'status':'pass' if not issues else 'review'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report',default=str(ROOT/'reports/refine06_validation.json'))
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    assert bpy.app.background, 'Use an isolated background process.'
    result = inspect(bpy.context.scene)
    Path(args.report).write_text(json.dumps(result,indent=2))
    print('REFINE06_VALIDATION',json.dumps({k:result[k] for k in ('scene_file','status','issues','elapsed_seconds')}),flush=True)
    print('DYNAMIC_CLEARANCE',json.dumps(result['dynamic_walkthrough']['minimum_leaf_clearance']),flush=True)
