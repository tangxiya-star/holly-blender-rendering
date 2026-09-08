"""Reference-guided generated microheight, used only on an actual sculpted casting."""
import bpy
from pathlib import Path

def apply_microtexture(scene):
    path=Path(__file__).resolve().parents[1]/'textures/bronze_bark_microheight_06.png'
    image=bpy.data.images.load(str(path),check_existing=True)
    image.colorspace_settings.name='Non-Color';image.pack()
    image['provenance']='Built-in imagegen; interpretive scalar bark texture, not measured height. Prompt stored alongside.'
    mat=bpy.data.materials['REF06 | cast bronze with ridge wear'];n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF')
    attr=n.new('ShaderNodeAttribute');attr.attribute_name='bark_coordinate';attr.name='Physical coordinates along each sculpted branch'
    sep=n.new('ShaderNodeSeparateXYZ');l.new(attr.outputs['Vector'],sep.inputs[0])
    xy=n.new('ShaderNodeCombineXYZ');l.new(sep.outputs['Y'],xy.inputs['X']);l.new(sep.outputs['X'],xy.inputs['Y'])
    scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs['Scale'].default_value=4.5;l.new(xy.outputs[0],scale.inputs[0])
    tex=n.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Cubic';tex.extension='REPEAT';tex.name='Fine cast wrinkles | interpretive microheight'
    l.new(scale.outputs[0],tex.inputs['Vector'])
    bump=n.new('ShaderNodeBump');bump.name='Submillimeter cast grain over physical bark';bump.inputs['Strength'].default_value=.48;bump.inputs['Distance'].default_value=.00085
    old=p.inputs['Normal'].links[0].from_socket;l.new(old,bump.inputs['Normal']);l.new(tex.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
    mat['microtexture_note']='Generated interpretation contributes only fine normal response. Large relief/occlusion/parallax remains real sculpted mesh.'
    return {'texture':str(path),'resolution':list(image.size),'height_distance_m':.00085,'tool':'built-in imagegen','prompt':'textures/bronze_bark_microheight_06_prompt.txt'}
