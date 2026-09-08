"""Place the return exactly in the bowl's transmitted view, based on ray tracing."""
import bpy


def apply(s):
    back=bpy.data.objects['Cocktail_Stage_CurvedBackdrop']
    for v in back.data.vertices:v.co.y=.8
    n=back.data.materials[0].node_tree.nodes
    # Existing shader's first center is X, second is Z.
    subtract=[q for q in n if q.bl_idname=='ShaderNodeMath' and q.operation=='SUBTRACT']
    divide=[q for q in n if q.bl_idname=='ShaderNodeMath' and q.operation=='DIVIDE']
    subtract[0].inputs[1].default_value=-.035
    subtract[1].inputs[1].default_value=.32
    divide[0].inputs[1].default_value=.23
    divide[1].inputs[1].default_value=.42
    mix=next(q for q in n if q.bl_idname=='ShaderNodeMixRGB')
    mix.inputs[2].default_value=(.31,.34,.33,1)
    bpy.data.objects['Cocktail_Stage_RightRearStrip'].data.energy=.72
    for name in ['Cocktail | pale currant-stem Antini','Cocktail | absorption medium boundary']:
        m=bpy.data.materials[name];m.node_tree.nodes['Trace botanical infusion scattering'].inputs['Density'].default_value=.08
        m.node_tree.nodes['Physical depth absorption'].inputs['Density'].default_value=2.4
    # Body shells catch light naturally; subdivision adds no decorative geometry.
    for o in s.objects:
        if o.type=='MESH' and o.name.startswith('Cocktail_Ant_') and any(p in o.name for p in ['Head','Mesosoma','Gaster','Petiole','Postpetiole']):
            mod=o.modifiers.new('Fine organic cuticle silhouette','SUBSURF');mod.levels=2;mod.render_levels=2
    s.camera.data.dof.aperture_fstop=20
    return {'changes':['rear return follows upward refracted bowl rays','reduced right source','nearly clear infusion','smooth ant body contours']}
