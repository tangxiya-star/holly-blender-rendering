"""Round 06: actual luminous diffusion backdrop behind the glass, no added objects."""
import bpy, math


def apply(s):
    back=bpy.data.objects['Cocktail_Stage_CurvedBackdrop'];back.location=(0,0,0)
    # Move the existing broad backdrop into the compact tabletop photography set.
    # It remains a real visible scene surface, not a camera/transmission ray trick.
    for i,v in enumerate(back.data.vertices):
        x=-1.1+2.2*(i//2)/64
        v.co=(x,.35,-.02 if i%2==0 else 1.0)
    m=back.data.materials[0];n=m.node_tree.nodes;l=m.node_tree.links
    n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission')
    geom=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geom.outputs['Position'],sep.inputs[0])
    # Diffused oval background pool: dark field outside, pale return through liquid.
    sq=[]
    for output,center,scale in [('X',-.016,.115),('Z',.055,.135)]:
        sub=n.new('ShaderNodeMath');sub.operation='SUBTRACT';sub.inputs[1].default_value=center;l.new(sep.outputs[output],sub.inputs[0])
        div=n.new('ShaderNodeMath');div.operation='DIVIDE';div.inputs[1].default_value=scale;l.new(sub.outputs[0],div.inputs[0])
        mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(div.outputs[0],mul.inputs[0]);l.new(div.outputs[0],mul.inputs[1]);sq.append(mul)
    add=n.new('ShaderNodeMath');add.operation='ADD';l.new(sq[0].outputs[0],add.inputs[0]);l.new(sq[1].outputs[0],add.inputs[1])
    neg=n.new('ShaderNodeMath');neg.operation='MULTIPLY';neg.inputs[1].default_value=-2.5;l.new(add.outputs[0],neg.inputs[0])
    exp=n.new('ShaderNodeMath');exp.operation='EXPONENT';l.new(neg.outputs[0],exp.inputs[0])
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';l.new(exp.outputs[0],mix.inputs[0])
    mix.inputs[1].default_value=(.007,.01,.012,1);mix.inputs[2].default_value=(.35,.37,.34,1)
    l.new(mix.outputs[0],em.inputs['Color']);em.inputs['Strength'].default_value=1
    l.new(em.outputs[0],out.inputs['Surface'])
    for name in ['Cocktail | pale currant-stem Antini','Cocktail | absorption medium boundary']:
        m=bpy.data.materials[name];m.node_tree.nodes['Trace botanical infusion scattering'].inputs['Density'].default_value=.25
        m.node_tree.nodes['Physical depth absorption'].inputs['Density'].default_value=3.0
    # Feather sources to actual zero radiance at the boundary, eliminating hot edges.
    for o in s.objects:
        if o.type!='LIGHT':continue
        n=o.data.node_tree.nodes;l=o.data.node_tree.links
        math_nodes=[q for q in n if q.bl_idname=='ShaderNodeMath']
        add=next(q for q in math_nodes if q.operation=='ADD')
        mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=4;l.new(add.outputs[0],mul.inputs[0])
        sub=n.new('ShaderNodeMath');sub.operation='SUBTRACT';sub.inputs[0].default_value=1;l.new(mul.outputs[0],sub.inputs[1]);sub.use_clamp=True
        sq=n.new('ShaderNodeMath');sq.operation='MULTIPLY';l.new(sub.outputs[0],sq.inputs[0]);l.new(sub.outputs[0],sq.inputs[1])
        gain=n.new('ShaderNodeMath');gain.operation='MULTIPLY';gain.inputs[1].default_value=3.0;l.new(sq.outputs[0],gain.inputs[0]);l.new(gain.outputs[0],n['Emission'].inputs['Strength'])
    s.camera.data.dof.aperture_fstop=18
    return {'changes':['real gradient diffusion background for transmitted rays','clearer infusion','zero-edge elliptical sources']}
