import bpy, json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
scene=bpy.context.scene
info={'version':bpy.app.version_string,'bake_targets':list(bpy.types.BakeSettings.bl_rna.properties['target'].enum_items.keys()),
      'objects':[{'name':o.name,'type':o.type,'vertices':len(o.data.vertices) if o.type=='MESH' else 0,'modifiers':[m.type for m in o.modifiers]} for o in scene.objects]}
props=bpy.ops.export_scene.gltf.get_rna_type().properties
info['gltf']={n:list(props[n].enum_items.keys()) if props[n].type=='ENUM' else props[n].default for n in ['export_vertex_color','export_all_vertex_colors','export_draco_mesh_compression_enable','export_draco_position_quantization','export_draco_normal_quantization','export_draco_color_quantization']}
(root/'web_exports'/'probe_export.json').write_text(json.dumps(info,indent=2))
print('PROBE',json.dumps(info),flush=True)
