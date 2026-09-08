"""Round 02: correct source reflections, transmitted fill, and focus. No new objects."""
import bpy, math
from mathutils import Vector


def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()


def apply(scene):
    specs=[
      ('KeyLeftSoftbox',(-.24,-.05,.205),(0,0,.145),1.05,.026,.20,(1,.94,.84),55),
      ('RightRearStrip',(.24,.08,.19),(0,0,.145),1.35,.018,.18,(.86,.94,1),55),
      ('TopLiquidLight',(0,.18,.32),(0,.12,0),1.2,.30,.20,(1,.97,.89),65),
      ('FrontGentleFill',(.11,-.38,.21),(0,0,.145),.13,.35,.35,(1,.98,.94),90),
    ]
    for name,pos,target,power,sx,sy,color,spread in specs:
        o=bpy.data.objects['Cocktail_Stage_'+name];o.location=pos;aim(o,target)
        d=o.data;d.energy=power;d.size=sx;d.size_y=sy;d.color=color;d.spread=math.radians(spread)
    fill=bpy.data.objects['Cocktail_Stage_FrontGentleFill'];fill.data.shape='DISK'
    scene.camera.data.dof.focus_object.location=(.004,-.0435,.145)
    scene.camera.data.dof.aperture_fstop=16
    # Background reveal is retained but recedes into darkness.
    arc=bpy.data.objects['Cocktail_Stage_DistantBronzeCurve']
    p=arc.data.materials[0].node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(.012,.007,.0038,1)
    p.inputs['Roughness'].default_value=.58
    stone=bpy.data.materials['Cocktail_Stage_BlueGrayPolishedStone']
    ramp=stone.node_tree.nodes.get('Restrained blue-gray stone range').color_ramp
    ramp.elements[0].color=(.009,.013,.016,1)
    ramp.elements[1].color=(.019,.024,.028,1)
    scene.cycles.transparent_max_bounces=32
    return {'changes':['source reflection area reduced','transmitted return behind cocktail','front bowl f16 focus','darker stone and bronze']}
