"""Round 05: trace infusion scattering, broad frontal return, less aggressive tint."""
import bpy
from mathutils import Vector


def apply(s):
    for name in ['Cocktail | pale currant-stem Antini','Cocktail | absorption medium boundary']:
        m=bpy.data.materials[name];n=m.node_tree.nodes;l=m.node_tree.links
        absorption=n['Physical depth absorption'];absorption.inputs['Density'].default_value=3.8
        scatter=n.new('ShaderNodeVolumeScatter');scatter.name='Trace botanical infusion scattering'
        scatter.inputs['Density'].default_value=1.4
        scatter.inputs['Color'].default_value=(.86,.9,.66,1)
        scatter.inputs['Anisotropy'].default_value=.25
        add=n.new('ShaderNodeAddShader');add.name='Infusion volume'
        l.new(absorption.outputs[0],add.inputs[0]);l.new(scatter.outputs[0],add.inputs[1]);l.new(add.outputs[0],n.get('Material Output').inputs['Volume'])
    o=bpy.data.objects['Cocktail_Stage_FrontGentleFill'];o.location=(-.02,-.65,.31)
    o.rotation_euler=(Vector((0,0,.145))-o.location).to_track_quat('-Z','Y').to_euler()
    o.data.size=.65;o.data.size_y=.65;o.data.energy=.85
    # Keep the image readable against the darker field without painting highlights.
    for name in ['Cocktail_Ant_DarkBrownCuticle','Cocktail_Ant_GasterCuticle','Cocktail_Ant_Appendages']:
        p=bpy.data.materials[name].node_tree.nodes.get('Principled BSDF')
        rgba=p.inputs['Base Color'].default_value;p.inputs['Base Color'].default_value=tuple(x*1.75 for x in rgba[:3])+(1,)
    return {'changes':['trace physically scattering infusion','large low-radiance frontal bounce','less concentrated tint']}
