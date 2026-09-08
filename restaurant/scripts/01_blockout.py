import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
setup()
gray=mat('Blockout | neutral plaster',(.36,.38,.40));furn=mat('Blockout | furniture',(.2,.22,.23));floor=mat('Blockout | floor',(.18,.20,.21))
cyl('Floor_Dining',(0,0,-.14),9.1,.28,'Architecture',floor,128)
box('Floor_Arrival',(0,-15.5,-.14),(9,7,.28),material=floor)
box('Floor_Transition',(0,-10.35,-.14),(3.3,3.4,.28),material=floor)
box('Street_Threshold',(0,-23,-.14),(14,8,.28),material=floor)
arc('Wall_Dining',(0,0),9,.22,1.35,2.7,-80,260,'Architecture',gray,n=144)
for x in [-1.7,1.7]:box('Wall_Transition', (x,-10.4,1.5),(.2,3.2,3),material=gray)
box('Ceiling_Transition',(0,-10.4,3.1),(3.6,3.2,.2),material=gray)
for x in [-4.6,4.6]:box('Wall_Arrival',(x,-15.5,2.4),(.2,7.2,4.8),material=gray)
for x in [-3.1,3.1]:
    box('Wall_Arrival_Back',(x,-12,2.4),(2.9,.2,4.8),material=gray)
    box('Facade_Wings',(x,-19,3),(2.9,.3,6),material=gray)
box('Portal_Lintel',(0,-19,5.1),(3.3,.4,1.8),material=gray)
box('Transition_Lintel',(0,-12,3.9),(3.5,.2,1.8),material=gray)
box('Ceiling_Arrival',(0,-15.5,4.9),(9.4,7.3,.2),material=gray)
# Upper hemisphere, no sphere bottom crossing the visitor space.
verts=[];faces=[];na=144;nr=48
for j in range(nr+1):
    t=(math.pi/2)*(j/nr);r=9*math.cos(t);z=2.7+5.7*math.sin(t)
    for i in range(na+1):
        a=2*math.pi*i/na;verts.append((r*math.cos(a),r*math.sin(a),z))
for j in range(nr):
    for i in range(na):k=j*(na+1)+i;faces.append((k,k+1,k+na+2,k+na+1))
dome=mesh('Dome_Projection',verts,faces,'Dome',gray,smooth=True)
dome['replaceable_projection']=True
# Paired U counters observed in both dome photographs; open towards center aisles.
for side in [-1,1]:
    for row in [0,5]:
        name=('West' if side<0 else 'East')+str(row)
        ribbon('Counter_'+name,counter_path(side,row),.74,.755,.05,'Tables',furn)
        ribbon('Base_'+name,counter_path(side,row),.53,.35,.66,'Tables',furn)
for i,(x,y,a) in enumerate(chair_positions()):
    o=box('Chair_%02d'%i,(x,y,.46),(.56,.56,.12),'Seating',furn);o.rotation_euler.z=a
    o=box('ChairBack_%02d'%i,(x-.23*math.sin(a),y+.23*math.cos(a),.76),(.56,.10,.52),'Seating',furn);o.rotation_euler.z=a
for i,y in enumerate([-3.5,0,3.5]):box('Island_%d'%i,(0,y,.39),(1.0,1.35,.78),'Tables',furn)
box('Arrival_Service_Counter',(-2.8,-15.0,.53),(1.15,3.6,1.06),'Tables',furn)
for y in [-16.8,-14]:
    box('Lounge_Seat',(3.2,y,.42),(.85,.85,.25),'Seating',furn)
    cyl('Lounge_Table',(2.2,y,.5),.4,.07,'Tables',furn)
camera('CAM_Arrival',(0,-22.5,1.65),(0,-16,2.1),26)
camera('CAM_Hero',(0,-6.8,1.65),(0,1.3,3.0),20)
camera('CAM_Dome',(0,-1.0,1.65),(0,4,6.8),18)
camera('CAM_Table',(1.2,1.1,1.45),(3.4,2.05,.8),35)
camera('CAM_Exit',(0,-15.5,1.65),(0,-22,1.65),26)
plan=camera('CAM_Plan',(20,-32,30),(0,-7,0),40);plan.data.type='ORTHO';plan.data.ortho_scale=38
walkthrough()
light('Blockout_Soft_Dome',(0,0,7),(0,0,0),2200,(1,1,1),8)
light('Blockout_Arrival',(0,-15.5,4.4),(0,-15.5,0),700,(1,1,1),4)
light('Blockout_Transition',(0,-10.5,2.9),(0,-10.5,0),200,(1,1,1),2)
light('Blockout_Street',(0,-23,7),(0,-19,1),1800,(1,1,1),8)
bpy.context.scene.camera=bpy.data.objects['CAM_Hero']
save('alchemist_01_blockout.blend')
for name in ['Dome_Projection','Ceiling_Arrival','Ceiling_Transition']:bpy.data.objects[name].hide_render=True
render('CAM_Plan','01_blockout_plan.png',1200,16)
for name in ['Dome_Projection','Ceiling_Arrival','Ceiling_Transition']:bpy.data.objects[name].hide_render=False
render('CAM_Hero','01_blockout_hero.png',1100,24)
render('CAM_Arrival','01_blockout_arrival.png',900,16)
print('PHASE 1 COMPLETE: blockout and three audit views saved')
