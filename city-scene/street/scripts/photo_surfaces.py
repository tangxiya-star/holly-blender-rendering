"""Scanned asphalt detail, CC0 Rob Tuytel / Poly Haven, 3m tile scale."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def apply_photo_surfaces():
    for o in bpy.data.objects:
        if o.type!='MESH':continue
        if not o.data.materials:continue
        m=o.data.materials[0]
        if m.name not in ['CPH_Surface_Asphalt','CPH_Surface_Cycle_asphalt']:continue
        mesh=o.data
        uv=mesh.uv_layers.get('Scan_3m') or mesh.uv_layers.new(name='Scan_3m')
        for loop in mesh.loops:
            v=mesh.vertices[loop.vertex_index].co
            uv.data[loop.index].uv=(v.x/3,v.y/3)
    for key in ['Asphalt','Cycle_asphalt']:
        m=bpy.data.materials.get('CPH_Surface_'+key)
        if not m:continue
        n=m.node_tree.nodes;l=m.node_tree.links;p=next(x for x in n if x.type=='BSDF_PRINCIPLED')
        if n.get('Scanned asphalt diffuse'):continue
        uv=n.new('ShaderNodeUVMap');uv.uv_map='Scan_3m'
        def tex(suffix,space):
            t=n.new('ShaderNodeTexImage');t.name='Scanned asphalt '+suffix
            t.image=bpy.data.images.load(str(ROOT/'textures'/('asphalt_02_'+suffix+'_2k.jpg')),check_existing=True)
            t.image.colorspace_settings.name=space;t.image.pack();l.new(uv.outputs[0],t.inputs[0]);return t
        diffuse=tex('diff','sRGB');diffuse.name='Scanned asphalt diffuse'
        rough=tex('rough','Non-Color');normal=tex('nor_gl','Non-Color')
        # Keep the quieter clean-track palette, retain photographed aggregate and repairs.
        color=n.new('ShaderNodeMixRGB');color.blend_type='MIX';color.inputs[0].default_value=.62 if key=='Cycle_asphalt' else .22
        color.inputs[2].default_value=(.09,.092,.089,1);l.new(diffuse.outputs['Color'],color.inputs[1]);l.new(color.outputs[0],p.inputs['Base Color'])
        l.new(rough.outputs['Color'],p.inputs['Roughness'])
        normal_map=n.new('ShaderNodeNormalMap');normal_map.uv_map='Scan_3m';normal_map.inputs['Strength'].default_value=.42
        l.new(normal.outputs['Color'],normal_map.inputs['Color']);l.new(normal_map.outputs['Normal'],p.inputs['Normal'])
        m['texture_source']='Poly Haven Asphalt 02 / Rob Tuytel / CC0 / 3m tile'
