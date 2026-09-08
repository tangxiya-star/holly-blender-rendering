"""Faithful geometry / baked-color web packaging of the completed food study.

Run in a separate background Blender process. The source blend is never saved.
This exports all final mesh geometry, including the unmodified slate tabletop.
Procedural base colors are baked with Cycles to dense linear vertex colors.
"""
import bpy
import hashlib
import json
import math
import struct
import time
from pathlib import Path
from mathutils import Vector
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'web_exports'
OUT.mkdir(exist_ok=True)
SOURCE=ROOT/'food_final.blend'
COLOR='WEB_BASECOLOR'
START=time.time()


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def bounds(objects):
    pts=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
    return {'min':[min(p[i] for p in pts) for i in range(3)],
            'max':[max(p[i] for p in pts) for i in range(3)]}


def roughness(name, fallback):
    if 'baked choux crust' in name:return .60
    if 'ivory cut layer' in name:return .42
    if 'thin amber filling' in name:return .30
    if 'dark leaf wrapper' in name:return .31
    if 'roe membrane' in name:
        return [.195,.275,.170,.305,.22,.265][int(name.split('membrane ')[1][:2])]
    if 'chlorophyll leaf variation' in name:return .305
    if 'porcelain' in name:return .235
    if 'Slate |' in name:return .58
    return fallback


def report_stage(stage, **kwargs):
    print('FOOD_WEB_STAGE',stage,json.dumps(kwargs),flush=True)


def run():
    source_hash=sha(SOURCE)
    if Path(bpy.data.filepath)!=SOURCE:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene=bpy.context.scene
    source_meshes=[o for o in scene.objects if o.type=='MESH']
    original_bounds=bounds(source_meshes)
    original_faces=sum(len(o.data.polygons) for o in source_meshes)
    original_vertices=sum(len(o.data.vertices) for o in source_meshes)
    source_eval_triangles=0
    deps=bpy.context.evaluated_depsgraph_get()
    for o in source_meshes:
        eval_ob=o.evaluated_get(deps)
        mesh=eval_ob.to_mesh()
        source_eval_triangles+=sum(len(p.vertices)-2 for p in mesh.polygons)
        eval_ob.to_mesh_clear()
    report_stage('source',objects=len(source_meshes),vertices=original_vertices,
                 base_faces=original_faces,evaluated_triangles=source_eval_triangles)

    # Apply only the existing four petal Solidify modifiers as evaluated geometry.
    # No decimation, cleanup, remeshing, cropping or material-dependent cuts.
    modified=[]
    for o in source_meshes:
        if o.modifiers:
            evaluated=o.evaluated_get(deps)
            converted=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=deps)
            o.modifiers.clear()
            o.data=converted
            modified.append(o.name)
    bpy.context.view_layer.update()
    mats={m for o in source_meshes for m in o.data.materials if m}
    descriptions=[]
    parameters={}
    for mat in mats:
        nt=mat.node_tree
        bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
        parameters[mat.name]={name:float(bs.inputs[name].default_value) for name in
                            ['Roughness','Metallic','IOR','Coat Weight','Coat Roughness','Transmission Weight','Subsurface Weight']}
        parameters[mat.name]['Roughness']=roughness(mat.name,parameters[mat.name]['Roughness'])
        parameters[mat.name]['base_color_procedural']=bool(bs.inputs['Base Color'].is_linked)
        parameters[mat.name]['normal_procedural']=bool(bs.inputs['Normal'].is_linked)
        output=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
        emission=nt.nodes.new('ShaderNodeEmission')
        emission.name='WEB BAKE | original procedural base color only'
        emission.inputs['Strength'].default_value=1
        if bs.inputs['Base Color'].is_linked:
            nt.links.new(bs.inputs['Base Color'].links[0].from_socket,emission.inputs['Color'])
        else:
            emission.inputs['Color'].default_value=bs.inputs['Base Color'].default_value
        nt.links.new(emission.outputs[0],output.inputs['Surface'])

    # Shader evaluation at real mesh vertices, including the source's wood UVs.
    # Baking emission removes all photographed lighting from the reusable asset.
    bpy.ops.object.select_all(action='DESELECT')
    for o in source_meshes:
        o.hide_set(False)
        o.hide_render=False
        o.select_set(True)
        attr=o.data.color_attributes.get(COLOR)
        if attr:o.data.color_attributes.remove(attr)
        attr=o.data.color_attributes.new(name=COLOR,type='FLOAT_COLOR',domain='POINT')
        o.data.color_attributes.active_color=attr
        o.data.color_attributes.render_color_index=o.data.color_attributes.find(COLOR)
    bpy.context.view_layer.objects.active=source_meshes[0]
    scene.render.engine='CYCLES'
    pref=bpy.context.preferences.addons['cycles'].preferences
    pref.compute_device_type='METAL'
    pref.refresh_devices()
    for dev in pref.devices:dev.use=dev.type=='METAL'
    scene.cycles.device='GPU'
    scene.cycles.samples=1
    scene.cycles.use_denoising=False
    scene.render.bake.target='VERTEX_COLORS'
    scene.render.bake.use_clear=True
    scene.render.bake.use_selected_to_active=False
    scene.render.bake.margin=0
    report_stage('base_color_bake_started')
    bpy.ops.object.bake(type='EMIT')
    report_stage('base_color_bake_finished',seconds=time.time()-START)

    color_audit=[]
    for o in source_meshes:
        attr=o.data.color_attributes.get(COLOR)
        a=np.empty(len(attr.data)*4,dtype=np.float32)
        attr.data.foreach_get('color',a)
        a=a.reshape((-1,4))
        # Opaque base colors. Transmission remains a material property.
        a[:,3]=1
        if not np.isfinite(a).all():raise RuntimeError('Non-finite baked color: '+o.name)
        if a[:,:3].max()<=0:raise RuntimeError('Empty / black bake: '+o.name)
        color_audit.append({'object':o.name,'color_domain':attr.domain,'colors':len(a),
                            'linear_rgb_min':a[:,:3].min(axis=0).tolist(),
                            'linear_rgb_max':a[:,:3].max(axis=0).tolist(),
                            'linear_rgb_mean':a[:,:3].mean(axis=0).tolist()})
        attr.data.foreach_set('color',a.ravel())

    # Every exported material consumes COLOR_0. Keep meaningful Principled PBR
    # constants and supported physical extensions without unexportable nodes.
    for mat in mats:
        p=parameters[mat.name]
        nt=mat.node_tree
        nt.nodes.clear()
        out=nt.nodes.new('ShaderNodeOutputMaterial')
        bs=nt.nodes.new('ShaderNodeBsdfPrincipled')
        bs.name='Web PBR | original finish approximation'
        out.location=(540,0);bs.location=(260,0)
        vc=nt.nodes.new('ShaderNodeVertexColor')
        vc.name='Original Cycles base color | baked at source vertices'
        vc.layer_name=COLOR
        vc.location=(-40,0)
        nt.links.new(vc.outputs['Color'],bs.inputs['Base Color'])
        nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
        for name in ['Roughness','Metallic','IOR','Coat Weight','Coat Roughness','Transmission Weight']:
            bs.inputs[name].default_value=p[name]
        bs.inputs['Subsurface Weight'].default_value=0
        mat.diffuse_color=(1,1,1,1)
        mat.use_backface_culling=False
        mat['web_base_color']='Cycles emission bake into linear COLOR_0; no reference photograph pixels'
        mat['web_roughness']=p['Roughness']
        mat['source_subsurface_weight']=p['Subsurface Weight']
        mat['web_micro_bump']='Actual geometry retained; procedural shader-only micro bump omitted'
        descriptions.append({'name':mat.name,**p})
    # No lights/cameras/focus objects from the photograph shoot in the GLB.
    omitted=[]
    for o in list(scene.objects):
        if o.type!='MESH':
            omitted.append({'name':o.name,'type':o.type})
            bpy.data.objects.remove(o,do_unlink=True)
    root=bpy.data.objects.new('Alchemist | complete food study',None)
    scene.collection.objects.link(root)
    root['units']='meters'
    root['plate_diameter_m']=.17
    root['dish_focus_blender_xyz']=[0,0,.043]
    root['source']='food_final.blend'
    root['web_material_approximation']='Baked base colors, representative material roughness, original mesh detail, no shader SSS'
    for o in source_meshes:o.parent=root
    bpy.context.view_layer.update()
    packed_bounds=bounds(source_meshes)
    if original_bounds!=packed_bounds:raise RuntimeError('Geometry bounds changed during packaging')
    packaged_triangles=sum(len(p.vertices)-2 for o in source_meshes for p in o.data.polygons)
    if packaged_triangles!=source_eval_triangles:raise RuntimeError('Evaluated triangle count changed')
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active=source_meshes[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'food_web.blend'))
    report_stage('export_started',triangles=packaged_triangles)
    bpy.ops.export_scene.gltf(filepath=str(OUT/'food_web.glb'),export_format='GLB',
        use_selection=True,export_cameras=False,export_lights=False,export_extras=True,
        export_animations=False,export_apply=False,export_yup=True,
        export_texcoords=False,export_normals=True,export_tangents=False,
        export_vertex_color='NAME',export_vertex_color_name=COLOR,export_all_vertex_colors=False,
        export_materials='EXPORT',export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,export_draco_position_quantization=20,
        export_draco_normal_quantization=14,export_draco_color_quantization=12,
        export_draco_texcoord_quantization=16,export_draco_generic_quantization=16)
    asset=OUT/'food_web.glb'
    raw=asset.read_bytes()
    magic,version,total=struct.unpack_from('<III',raw,0)
    jlen,jtyp=struct.unpack_from('<II',raw,12)
    gltf=json.loads(raw[20:20+jlen])
    primitive_count=sum(len(m['primitives']) for m in gltf.get('meshes',[]))
    colored=sum('COLOR_0' in p['attributes'] for m in gltf.get('meshes',[]) for p in m['primitives'])
    actual_triangles=sum(gltf['accessors'][p['indices']]['count']//3 for m in gltf.get('meshes',[]) for p in m['primitives'])
    if colored!=primitive_count:raise RuntimeError('Some exported primitives have no baked vertex colors')
    if actual_triangles!=source_eval_triangles:raise RuntimeError('glTF triangle count does not match source')
    report={'source':str(SOURCE),'source_sha256_before':source_hash,'source_sha256_after':sha(SOURCE),
        'source_unchanged':sha(SOURCE)==source_hash,'asset':str(asset),'asset_sha256':sha(asset),
        'bytes':asset.stat().st_size,'MiB':asset.stat().st_size/(1024*1024),
        'geometry':{'source_mesh_objects':len(source_meshes),'source_vertices':original_vertices,
                    'source_base_faces':original_faces,'source_evaluated_triangles':source_eval_triangles,
                    'exported_triangles':actual_triangles,'glb_meshes':len(gltf.get('meshes',[])),
                    'glb_material_primitives':primitive_count,'all_primitives_have_COLOR_0':colored==primitive_count,
                    'bounds_blender_Z_up_m':packed_bounds,'modifiers_applied_as_evaluated_geometry':modified,
                    'decimation':False,'slate_tabletop':'Entire original mesh retained, no cropping'},
        'materials':sorted(descriptions,key=lambda d:d['name']),'color_audit':color_audit,
        'images':len(gltf.get('images',[])),'materials_count':len(gltf.get('materials',[])),
        'extensions_used':gltf.get('extensionsUsed',[]),'extensions_required':gltf.get('extensionsRequired',[]),
        'draco':{'compression_level':6,'position_bits':20,'normal_bits':14,'color_bits':12},
        'omitted_non_mesh_photography_helpers':omitted,
        'viewer':{'requires':'Three.js GLTFLoader with DRACOLoader','units':'meters','up':'Y',
                  'focus_gltf_xyz':[0,.043,0],'plate_diameter_m':.17,
                  'slate_node':'Support | graphite slate photographic tabletop',
                  'source_to_gltf':'(x,y,z) -> (x,z,-y)'},
        'material_limitations':['Base color variation is evaluated by Cycles and baked per source vertex; no photograph is used as a texture.',
             'Representative per-material roughness preserves distinct dry crust, wet roe, moss, bark and ceramic finishes; high-frequency procedural roughness is not transferred.',
             'All actual blister, grain, pore, moss leaf, bark and plate geometry is retained. Shader-only microscopic bump is omitted.',
             'glTF IOR, transmission and clearcoat extensions are retained where used. Cycles subsurface scattering is omitted in this web approximation.',
             'Web appearance depends on viewer lighting and environment; the photographic source lighting is intentionally excluded.'],
        'seconds':time.time()-START,'reimport_validation':'pending'}
    (OUT/'web_asset_report.json').write_text(json.dumps(report,indent=2))
    report_stage('complete',bytes=report['bytes'],MiB=report['MiB'],triangles=actual_triangles,
                 colored_primitives=colored,source_unchanged=report['source_unchanged'],seconds=report['seconds'])


if __name__=='__main__':run()
