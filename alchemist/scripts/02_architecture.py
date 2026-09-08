import sys,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from furniture import add_chairs
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'alchemist_01_blockout.blend'))
gray=bpy.data.materials['Blockout | neutral plaster'];furn=bpy.data.materials['Blockout | furniture']
def remove(name):
    o=bpy.data.objects.get(name)
    if o:bpy.data.objects.remove(o,do_unlink=True)
remove('Wall_Dining')
for n,a,b in [('East',-80,63),('West',117,260)]:arc('Wall_Dining_'+n,(0,0),9,.24,1.35,2.7,a,b,'Architecture',gray,n=80,bevel=.015)
arc('Dome_Rim',(0,0),8.99,.12,2.69,.08,0,360,'Architecture',furn,n=192,bevel=.008)
for o in list(bpy.context.scene.objects):
    if o.type=='MESH' and o.name!='Dome_Projection' and not o.modifiers:
        m=o.modifiers.new('Edge highlight','BEVEL');m.width=.012 if 'Counter' in o.name else .02;m.segments=3
        o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    if o.name.startswith('Base_'):
        # Lift the cabinet off the floor, as in the photographs.
        for v in o.data.vertices:v.co.z=.16+(v.co.z-.02)*.78
for side in [-1,1]:
    for row in [0,5]:
        ribbon('Counter_Underslab',counter_path(side,row),.84,.695,.055,'Tables',furn,.018)
        for x,y in [(2.45,-3.25),(5.65,-3.25),(6.4,-1.6),(5.65,0),(2.45,0)]:
            box('Counter_Leg',(side*x,y+row,.105),(.045,.045,.21),'Tables',furn,.007)
# Ground-level adaptation of the photographically supported shadow service bay.
box('Floor_Service',(0,9.2,-.14),(8.4,2.8,.28),material=gray)
box('Service_Back_Wall',(0,10.5,1.4),(8.4,.2,2.8),material=gray,bevel=.02)
for x in [-4.25,4.25]:box('Service_Side_Wall',(x,9.15,1.4),(.2,2.7,2.8),material=gray)
box('Ceiling_Service',(0,9.1,2.85),(8.6,3,.2),material=furn)
box('Service_Sill',(0,8.15,.34),(8.1,.24,.68),material=furn,bevel=.015)
box('Service_Lintel',(0,8.15,2.42),(8.1,.28,.52),material=furn,bevel=.012)
for i in range(6):
    x=-3.4+i*1.36
    box('Service_Glazing_%d'%i,(x,8.16,1.44),(1.32,.016,1.52),material=gray,bevel=.002)
    box('Service_Mullion_%d'%i,(x-.67,8.13,1.44),(.025,.055,1.55),material=furn,bevel=.005)
box('Service_Worktop',(0,9.3,.9),(7.4,.8,.06),'Tables',furn,.015)
box('Service_Shelf',(0,10.2,1.65),(7.5,.3,.045),'Tables',furn,.009)
for x in [-3.4,-1.7,0,1.7,3.4]:box('Service_Cabinet',(x,9.4,.44),(1.4,.6,.8),'Architecture',gray,.015)
# Bronze leaves stand open at the jambs, preserving the full portal opening.
for side in [-1,1]:
    x=side*1.62
    o=box('Entrance_Bronze_Leaf_'+str(side),(x,-18.23,2.1),(.16,1.53,4.18),material=furn,bevel=.025)
    for z in [.35,1.45,2.65,3.85]:box('Entrance_Leaf_Crossrail',(x-side*.095,-18.23,z),(.035,1.4,.035),material=furn,bevel=.01)
    for y in [-18.94,-17.52]:box('Entrance_Leaf_Stile',(x-side*.095,y,2.1),(.035,.035,3.85),material=furn,bevel=.008)
    box('Portal_Bronze_Jamb',(side*1.67,-19.08,2.12),(.12,.1,4.24),material=furn,bevel=.012)
box('Portal_Bronze_Head',(0,-19.08,4.23),(3.46,.13,.12),material=furn,bevel=.012)
# Regular panel joints and skirtings supply architectural scale.
for side in [-1,1]:
    for j in range(10):box('Arrival_Panel_Joint',(side*4.48,-18.6+j*.68,2.2),(.015,.015,4.3),material=furn,bevel=.003)
    box('Arrival_Skirting',(side*4.46,-15.5,.085),(.045,6.9,.13),material=furn,bevel=.007)
    box('Transition_Reveal',(side*1.59,-11.95,1.5),(.035,.25,3),material=furn,bevel=.005)
# Arrival bar with a stone slab and floating plinth.
box('Arrival_Bar_Stone',(-2.8,-15,1.085),(1.22,3.7,.05),'Tables',gray,.018)
box('Arrival_Bar_Plinth',(-2.8,-15,.09),(.87,3.35,.18),'Architecture',furn,.012)
box('Arrival_Bar_Backdrop',(-4.43,-15,1.92),(.07,4.2,2.1),'Architecture',gray,.015)
for o in list(bpy.context.scene.objects):
    if o.name.startswith('Lounge_Table'):
        cyl('Lounge_Table_Stem',(o.location.x,o.location.y,.25),.035,.5,'Tables',furn,32,.006)
        cyl('Lounge_Table_Foot',(o.location.x,o.location.y,.025),.23,.05,'Tables',furn,48,.01)
    if o.name.startswith('Lounge_Seat'):
        box('Lounge_Back',(o.location.x+.32,o.location.y,.82),(.15,.86,.8),'Seating',furn,.12)
        for xx in [-.28,.28]:
            for yy in [-.28,.28]:cyl('Lounge_Leg',(o.location.x+xx,o.location.y+yy,.15),.027,.3,'Seating',furn,24,.004)
add_chairs({'fabric':furn,'metal':furn,'wood':furn})
root=bpy.data.objects.new('Restaurant',None);bpy.context.scene.collection.objects.link(root)
root['description']='Alchemist-inspired single-level spatial adaptation; public photographs, inferred plan'
for name in ['Architecture','Dome','Tables','Seating','Lighting','Glassware','Props','InteractionTargets']:
    parent=bpy.data.objects.new(name,None);group(name).objects.link(parent);parent.parent=root
    for o in list(group(name).objects):
        if o!=parent and o.parent is None:o.parent=parent
save('alchemist_02_architecture.blend')
render('CAM_Hero','02_architecture_hero.png',1100,24)
render('CAM_Table','02_architecture_table.png',1000,24)
render('CAM_Arrival','02_architecture_arrival.png',1000,20)
