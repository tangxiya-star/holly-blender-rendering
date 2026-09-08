import bpy, sys, math, random, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

# This is a dedicated new background scene; no existing user scene is removed.
scene=bpy.data.scenes.new('Copenhagen | Lille Nørregade');bpy.context.window.scene=scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.fps=24
road=mat('Blockout | asphalt',(.08,.085,.09),.85)
walk=mat('Blockout | pavement',(.38,.39,.38),.8)
building=mat('Blockout | facade',(.54,.50,.43),.85)
box('Surrounding ground',(0,20,-.25),(500,500,.35),'Context',mat('Earth ground',(.15,.16,.14),.95))
box('Main carriageway',(0,30,-.075),(5.6,190,.15),'Blockout_Roads',road)
segments=[(-65,-45.5),(-34.5,46.5),(57.5,125)]
for side in [-1,1]:
    for a,b in segments:
        mid=(a+b)/2
        box('Raised bicycle track',(side*4.2,mid,0),(2.5,b-a,.14),'Blockout_Roads',road)
        box('Sidewalk',(side*7.3,mid,.09),(3.4,b-a,.18),'Blockout_Roads',walk)
        box('Granite kerb',(side*5.525,mid,.09),(.15,b-a,.18),'Blockout_Roads',walk)
for y in [-40,52]:
    box('Connected side street',(0,y,-.075),(160,6.4,.15),'Blockout_Roads',road)
    for side in [-1,1]:
        for a,b in [(-80,-9),(9,80)]:
            box('Cross-street sidewalk',((a+b)/2,y+side*4.35,.09),(b-a,2.3,.18),'Blockout_Roads',walk)

rng=random.Random(20260908);registry=[]
colors=[(.57,.42,.22),(.46,.21,.15),(.66,.63,.53),(.35,.42,.37),(.61,.50,.34),(.40,.24,.17),(.54,.51,.47)]
shops=['BAGERI','KAFFE & BRØD','BØGER','ATELIER','CYKLER','VINHANDEL','BLOMSTER','KERAMIK','']
def row(a,b,origin_fn,rotation,prefix):
    length=b-a;n=max(1,round(length/11));widths=[rng.uniform(8.8,13.2) for _ in range(n)];total=sum(widths);widths=[w*length/total for w in widths]
    pos=a
    for i,w in enumerate(widths):
        origin=origin_fn(pos+w/2);floors=rng.choices([3,4,5],[1,6,3])[0];h=3.65+(floors-1)*3.05
        idx=len(registry);item={'id':prefix+str(i).zfill(2),'origin':[*origin,.18],'rotation':rotation,'width':w,'depth':12,'height':h,'floors':floors,'seed':308+idx*31,'style':'brick' if idx%4==2 else 'plaster','color':colors[idx%len(colors)],'shop':shops[idx%len(shops)]}
        registry.append(item)
        o=box('MASS_'+item['id'],(0,0,0),(w,12,h),'Blockout_Buildings',building)
        o.location=(origin[0]-math.sin(rotation)*6,origin[1]+math.cos(rotation)*6,.18+h/2);o.rotation_euler.z=rotation
        pos+=w
for side in [-1,1]:
    for j,(a,b) in enumerate(segments):row(a,b,lambda t,s=side:(s*9,t),math.pi/2 if side<0 else -math.pi/2,f'Hero_{side}_{j}_')
for cy in [-40,52]:
    for side in [-1,1]:
        for a,b in [(-80,-21),(21,80)]:
            row(a,b,lambda t,s=side,y=cy:(t,y+s*5.5),0 if side>0 else math.pi,f'Cross_{cy}_{side}_{a}_')
# Terminating street walls beyond playable route conceal the horizon at both ends.
row(-34,34,lambda t:(t,138),0,'North_close_')
row(-34,34,lambda t:(t,-79),math.pi,'South_close_')
(ROOT/'reports'/'building_registry.json').write_text(json.dumps(registry,indent=2))

camera('01 | Human eye street',(-6.7,-19,1.88),(-.6,27,4.1),32)
camera('02 | Walking perspective',(-6.6,18,1.88),(-2.8,48,3.1),32)
camera('03 | Establishing',(29,-29,26),(0,31,3),35)
camera('04 | Bakery approach',(-5.75,7,1.88),(-9,14,2.1),35)
camera('05 | Cross street',(-35,50.3,1.88),(4,52,3.0),32)
scene.camera=bpy.data.objects['01 | Human eye street']
for name,p,action in [('POI_Bakery',(-9,14,.18),'future_bakery_interior'),('POI_Courtyard',(9,29,.18),'future_courtyard'),('POI_Gallery',(-32,57.5,.18),'future_gallery_interior')]:
    o=bpy.data.objects.new(name,None);group('POI_Targets').objects.link(o);o.location=p;o.empty_display_type='ARROWS';o.empty_display_size=.8;o['destination']=action
lighting()
scene['design_basis']='Representative Copenhagen neighborhood; fictional street plan, reference-backed architectural language.'
scene['navigation']='Select a camera or use Shift+` Walk Navigation in 3D View. Ground-mode eye height 1.7 m above footway.'
scene['main_street_width_m']=18.;scene['cycle_track_width_m']=2.5
checks={'units':'meters','eye_height_above_sidewalk':1.7,'sidewalk_top':.18,'main_corridor_width':18,'road_width':5.6,'one_way_cycle_width':2.5,'sidewalk_width':3.4,'building_count':len(registry),'facade_width_range':[min(x['width'] for x in registry),max(x['width'] for x in registry)],'eave_height_range':[min(x['height'] for x in registry),max(x['height'] for x in registry)],'streets':3,'hero_length':190,'cross_street_lengths':[160,160],'status':'awaiting eye-level render review'}
(ROOT/'reports'/'01_scale_check.json').write_text(json.dumps(checks,indent=2))
save('copenhagen_01_blockout.blend')
