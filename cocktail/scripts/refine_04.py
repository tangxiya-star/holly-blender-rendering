"""Round 04: photographed camera elevation, continuous stone field, controlled rear return."""
import bpy,math
from mathutils import Vector


def apply(s):
    cam=s.camera;target=Vector((0,0,.084));a=math.radians(21);distance=.60
    cam.location=target+Vector((0,-math.cos(a)*distance,math.sin(a)*distance))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.dof.focus_object.location=(.004,-.0435,.145);cam.data.dof.aperture_fstop=16
    # A single continuous table field removes the artificial horizon near the bowl.
    table=bpy.data.objects['Cocktail_Stage_StoneTable'];table.scale.y=2.5;table.location.y=1.0
    bpy.data.objects['Cocktail_Stage_CurvedBackdrop'].location.y=3
    bpy.data.objects['Cocktail_Stage_DistantBronzeCurve'].hide_render=True
    specs=[
      ('KeyLeftSoftbox',(-.25,.02,.23),(0,0,.14),3.1,.14,.32,(1,.95,.87)),
      ('RightRearStrip',(.25,.14,.24),(0,0,.14),1.8,.022,.28,(.93,.96,1)),
      ('TopLiquidLight',(0,.24,.38),(0,.28,0),2.3,.25,.20,(1,.97,.9)),
      ('FrontGentleFill',(0,-.45,.30),(0,0,.14),.045,.40,.40,(1,.98,.94)),
    ]
    for name,pos,at,power,sx,sy,col in specs:
        o=bpy.data.objects['Cocktail_Stage_'+name];o.location=pos
        o.rotation_euler=(Vector(at)-o.location).to_track_quat('-Z','Y').to_euler()
        o.data.energy=power;o.data.size=sx;o.data.size_y=sy;o.data.color=col
    s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.12
    for name in ['Cocktail | pale currant-stem Antini','Cocktail | absorption medium boundary']:
        bpy.data.materials[name].node_tree.nodes['Physical depth absorption'].inputs['Density'].default_value=7.0
    return {'changes':['21 degree hero camera','continuous distant stone ground','bounce light aimed behind glass','subtle deeper absorption']}
