import sys,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'alchemist_03b_projection.blend'))
s=bpy.context.scene
for o in list(s.objects):
    if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
s.world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.21,.3,1)
s.world.node_tree.nodes['Background'].inputs[1].default_value=.035
s.view_settings.exposure=.5
# Broad reflected projection fill, with dark interstitial spaces left intact.
for x,y in [(-4,0),(4,0),(0,4)]:light('Dome_Bounce',(x,y,6),(x,y,0),100,(.19,.36,1),5)
for i,(x,y,a) in enumerate(chair_positions()):
    if i%2==0:light('Table_Preview_Pool',(x+math.sin(a)*.75,y-math.cos(a)*.75,1.12),(x+math.sin(a)*.75,y-math.cos(a)*.75,.76),5,(1,.63,.29),.12)
for i,y in enumerate([-3.5,0,3.5]):
    light('Island_Warm_Pool',(0,y,1.25),(0,y,.78),4,(1,.67,.35),.3)
    # A shallow recessed tray gives the island's small warm reflection line.
    box('Island_Tray_%d'%i,(0,y+.2,.786),(.72,.32,.012),'Props',bpy.data.materials['PBR | aged architectural bronze'],.012)
for x in [-3,-1,1,3]:light('Service_Warm_Glow',(x,9.0,2.35),(x,9.3,.7),45,(1,.7,.4),1.2)
for side in [-1,1]:
    for row in [0,5]:
        for y in [-2.4+row,-.5+row]:light('Counter_Indirect',(side*4.5,y,.14),(side*4.5,y-.5,0),2,(1,.63,.3),1)
# Arrival localized brass pendants and grazing wall light.
brass=bpy.data.materials['PBR | aged architectural bronze'];emit=mat('PBR | warm opal light',(.7,.48,.2),.25)
p=emit.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.64,.28,1);p.inputs['Emission Strength'].default_value=4
for i,y in enumerate([-16.4,-15,-13.6]):
    cyl('Arrival_Pendant_Tube',(-2.7,y,3.5),.025,1.4,'Lighting',brass,32,.003)
    cyl('Arrival_Pendant_Lens',(-2.7,y,2.792),.024,.012,'Lighting',emit,32)
    light('Arrival_Pendant_Light',(-2.7,y,2.77),(-2.7,y,0),35,(1,.73,.46),.22)
light('Arrival_Bar_Wash',(-3.9,-15,3.6),(-4.45,-15,1.5),100,(1,.73,.45),3.5)
light('Arrival_Lounge_Fill',(2.5,-15.5,3.9),(2.8,-15.5,.5),85,(1,.8,.57),2.5)
light('Arrival_Soft_Orientation',(0,-17,3.8),(0,-14,1),35,(1,.76,.52),2)
for y in [-11.5,-9.3]:light('Transition_Recessed',(0,y,2.97),(0,y,0),12,(1,.66,.33),.2)
for x in [-1.7,1.7]:light('Portal_Uplight',(x,-19.55,.15),(x,-18.5,2.5),30,(1,.76,.51),.18)
light('Street_Overcast',(0,-24,8),(0,-19,1),900,(.64,.75,1),9)
# Label provides a recognizable travel-world entry, with discreet scale.
d=bpy.data.curves.new('Entrance lettering','FONT');d.body='A L C H E M I S T';d.align_x='CENTER';d.size=.17;d.extrude=.001
o=bpy.data.objects.new('Entrance_Lettering',d);group('Architecture').objects.link(o);o.location=(0,-19.23,4.65);o.rotation_euler=(math.pi/2,0,0);d.materials.append(brass)
for o in s.objects:
    if o.parent is None and o.users_collection:
        p=bpy.data.objects.get(o.users_collection[0].name)
        if p and p!=o:o.parent=p
bpy.ops.file.pack_all();save('alchemist_04_lighting.blend')
render('CAM_Hero','05_lighting_hero.png',1200,48)
render('CAM_Arrival','05_lighting_arrival.png',1000,40)
render('CAM_Exit','05_lighting_exit.png',1000,32)
