import bpy, json
from pathlib import Path
out={"version":bpy.app.version_string,"devices":[],"principled_inputs":[]}
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='METAL'
    prefs.get_devices()
    out['devices']=[{'name':d.name,'type':d.type,'use':d.use} for d in prefs.devices]
except Exception as e:out['device_error']=str(e)
m=bpy.data.materials.new('Probe');m.use_nodes=True
out['principled_inputs']=[i.name for i in m.node_tree.nodes.get('Principled BSDF').inputs]
out['cycles_properties']=[p.identifier for p in bpy.context.scene.cycles.bl_rna.properties]
Path(__file__).resolve().parents[1].joinpath('reports','cycles_capabilities.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
