"""Feathered physical softboxes and a faint luminous Alchemist dome backdrop."""
import bpy, math
from mathutils import Vector


def feather(light,falloff=4):
    d=light.data;d.use_nodes=True;n=d.node_tree.nodes;l=d.node_tree.links
    g=n.new('ShaderNodeNewGeometry');g.name='Actual emitter planar coordinates'
    sep=n.new('ShaderNodeSeparateXYZ');l.new(g.outputs['Parametric'],sep.inputs[0])
    squares=[]
    for axis in ['X','Y']:
        sub=n.new('ShaderNodeMath');sub.operation='SUBTRACT';sub.inputs[1].default_value=.5;l.new(sep.outputs[axis],sub.inputs[0])
        sq=n.new('ShaderNodeMath');sq.operation='MULTIPLY';l.new(sub.outputs[0],sq.inputs[0]);l.new(sub.outputs[0],sq.inputs[1]);squares.append(sq)
    add=n.new('ShaderNodeMath');add.operation='ADD';l.new(squares[0].outputs[0],add.inputs[0]);l.new(squares[1].outputs[0],add.inputs[1])
    mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=-4*falloff;l.new(add.outputs[0],mul.inputs[0])
    exp=n.new('ShaderNodeMath');exp.operation='EXPONENT';l.new(mul.outputs[0],exp.inputs[0])
    gain=n.new('ShaderNodeMath');gain.operation='MULTIPLY';gain.inputs[1].default_value=3.2;l.new(exp.outputs[0],gain.inputs[0])
    l.new(gain.outputs[0],n.get('Emission').inputs['Strength'])


def apply(scene):
    specs=[
      ('KeyLeftSoftbox',(-.20,-.10,.23),(0,0,.14),3.4,.13,.30,(1,.95,.86),120),
      ('RightRearStrip',(.20,.14,.19),(0,0,.14),3.3,.07,.28,(.91,.96,1),100),
      ('TopLiquidLight',(0,.25,.30),(0,0,.14),3.0,.24,.20,(1,.97,.89),120),
      ('FrontGentleFill',(0,-.30,.23),(0,0,.14),.045,.30,.30,(1,.98,.94),120),
    ]
    for name,pos,target,power,sx,sy,color,spread in specs:
        o=bpy.data.objects['Cocktail_Stage_'+name];o.location=pos
        o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
        d=o.data;d.shape='RECTANGLE';d.energy=power;d.size=sx;d.size_y=sy;d.color=color;d.spread=math.radians(spread)
        feather(o,4)
    world=scene.world.node_tree.nodes['Background'];world.inputs['Strength'].default_value=.06
    backdrop=bpy.data.materials['Cocktail_Stage_CoolCharcoalBackground'].node_tree.nodes.get('Principled BSDF')
    backdrop.inputs['Emission Color'].default_value=(.018,.024,.029,1)
    backdrop.inputs['Emission Strength'].default_value=.8
    scene.camera.data.dof.aperture_fstop=16
    return {'changes':['Gaussian feathered emitter radiance','rear transmission source','faint dome ambient backdrop']}
