import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from entrance_detail import add_entrance_detail
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'alchemist_04b_furnished.blend'))
s=bpy.context.scene
stone=bpy.data.materials['PBR | honed blue-grey mineral stone'];metal=bpy.data.materials['PBR | satin blackened steel'];brass=bpy.data.materials['PBR | aged architectural bronze'];charcoal=bpy.data.materials['PBR | charcoal mineral plaster'];concrete=bpy.data.materials['PBR | weathered pale masonry']
# Top three review corrections: calmer projection, deeper glazing, broad warm pools.
proj=bpy.data.materials['PROJECTION | replace this image'];p=proj.node_tree.nodes.get('Principled BSDF')
proj.node_tree.nodes['REPLACEABLE_PROJECTION'].image=bpy.data.images.load(str(ROOT/'textures'/'projection_underwater_refined.png'),check_existing=True)
p.inputs['Emission Strength'].default_value=5
for o in s.objects:
    if o.type=='LIGHT' and o.name.startswith('TableExperience_'):
        o.data.energy=10;o.data.color=(1,.66,.30);o.data.spot_size=math.radians(98);o.data.spot_blend=.72
p=stone.node_tree.nodes.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.28;p.inputs['Coat Roughness'].default_value=.14
# The original island placeholder now becomes a dark pedestal and thin stone slab.
for i,y in enumerate([-3.5,0,3.5]):
    o=bpy.data.objects['Island_'+str(i)];o.data.materials.clear();o.data.materials.append(metal)
    for v in o.data.vertices:v.co.z*=.90
    o.location.z=.351
    box('Island_Stone_Slab_'+str(i),(0,y,.755),(1.05,1.4,.05),'Tables',stone,.013)
smoked=mat('PBR | smoked service glazing',(.21,.24,.28),.10,.12)
p=smoked.node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=.78;p.inputs['IOR'].default_value=1.48
for o in s.objects:
    if o.name.startswith('Service_Glazing'):o.data.materials.clear();o.data.materials.append(smoked)
    if o.name.startswith(('Service_Back_Wall','Service_Cabinet')):o.data.materials.clear();o.data.materials.append(metal)
    if o.type=='LIGHT' and o.name.startswith('Service_Warm_Glow'):o.data.energy=65;o.location.y=9.8;aim(o,(o.location.x,8.9,1))
for z in [1.15,1.72]:box('Service_Stainless_Rail',(0,9.95,z),(7.2,.045,.035),'Architecture',metal,.007)
light('Service_Oblique_Reflection',(-3.4,8.9,2.1),(1.5,8.13,1.5),90,(1,.67,.34),2)
light('Service_Oblique_Reflection',(3.4,8.9,1.9),(-1.5,8.13,1.3),70,(1,.74,.48),1.5)
# Round the top corners and add subdued fabric grazing response.
for o in s.objects:
    if o.type=='MESH' and o.name.startswith('ChairBack_'):
        for v in o.data.vertices:
            u=min(1,abs(v.co.x)/.28);h=max(0,min(1,(v.co.z-.63)/.34))
            v.co.x*=.88+.12*math.sin(math.pi*h);v.co.z-=.07*u**4*h
        sub=o.modifiers.new('Upholstery softened silhouette','SUBSURF');sub.levels=1;sub.render_levels=1
fabric=bpy.data.materials['PBR | midnight woven upholstery'];p=fabric.node_tree.nodes.get('Principled BSDF');p.inputs['Sheen Weight'].default_value=.3;p.inputs['Sheen Roughness'].default_value=.65
print(add_entrance_detail({'brass':brass,'concrete':concrete,'metal':metal}))
# Restrained, inferred Refshaleoen industrial street stub for enter/leave integration.
# This is connector context, not an asserted survey of the neighbouring buildings.
box('Street_Connector_Pavement',(0,-27,-.16),(24,12,.28),'Architecture',concrete,.02)
road=mat('PBR | fine asphalt',(.038,.042,.048),.86)
box('Street_Connector_Road',(0,-27,-.003),(24,3.4,.014),'Architecture',road)
for y in [-25.2,-28.8]:box('Street_Connector_Kerb',(0,y,.08),(24,.14,.16),'Architecture',concrete,.025)
for x in range(-11,12):box('Street_Paving_Joint',(x,-22,.005),(.006,5.7,.003),'Architecture',metal)
box('Street_Industrial_Backdrop',(0,-31.5,3.2),(24,.35,6.4),'Architecture',concrete,.025)
window=mat('PBR | dusk industrial glass',(.07,.10,.14),.22,.35)
p=window.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(.1,.15,.23,1);p.inputs['Emission Strength'].default_value=.25
for x in [-9,-5,-1,3,7,11]:
    box('Street_Window_Frame',(x,-31.28,3.2),(2.15,.12,3),'Architecture',metal,.012)
    box('Street_Window',(x,-31.19,3.2),(1.98,.035,2.83),'Architecture',window,.005)
    box('Street_Window_Crossbar',(x,-31.15,3.2),(2,.035,.025),'Architecture',metal)
    box('Street_Window_Mullion',(x,-31.15,3.2),(.025,.035,2.83),'Architecture',metal)
light('Street_Dusk_Wall_Wash',(0,-27,6.5),(0,-31.2,2.8),800,(.59,.71,1),10)
cyl('Street_Lamp_Post',(-5,-24.5,2.2),.045,4.4,'Architecture',metal,32,.006)
box('Street_Lamp_Canopy',(-5,-24.5,4.45),(.6,.6,.1),'Architecture',metal,.035)
light('Street_Practical',(-5,-24.5,4.35),(-5,-24.5,0),160,(1,.71,.44),.4)
# Camera compositions still remain at pedestrian height.
cam=bpy.data.objects['CAM_Dome'];cam.location=(5.2,-4.6,1.65);cam.data.lens=18;aim(cam,(0,2.5,3.5))
cam=bpy.data.objects['CAM_Arrival'];cam.location=(-.5,-24,1.7);cam.data.lens=25;aim(cam,(0,-18.3,2.3))
camera('CAM_Lounge',(2,-17.8,1.6),(-2.8,-14.3,1.6),26)
# UVs for newly introduced textured surfaces and packed portability.
for o in s.objects:
    if o.type=='MESH' and not o.data.uv_layers:
        uv=o.data.uv_layers.new(name='SurfaceUV');tile=o.data.materials[0].get('tile_m',1) if o.data.materials else 1
        for poly in o.data.polygons:
            dims=[i for i in range(3) if i!=max(range(3),key=lambda i:abs(poly.normal[i]))]
            for li in poly.loop_indices:
                v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v[dims[0]]/tile,v[dims[1]]/tile)
    if o.parent is None and o.users_collection:
        parent=bpy.data.objects.get(o.users_collection[0].name)
        if parent and parent!=o:o.parent=parent
s.cycles.max_bounces=8;s.cycles.diffuse_bounces=3;s.cycles.glossy_bounces=4;s.cycles.transmission_bounces=6
s.cycles.caustics_reflective=False;s.cycles.caustics_refractive=False
bpy.ops.file.pack_all();save('alchemist_04c_review.blend')
render('CAM_Hero','07_refined_hero.png',1400,64)
render('CAM_Table','07_refined_table.png',1100,48)
render('CAM_Arrival','07_refined_arrival.png',1100,40)
render('CAM_Dome','07_refined_dome.png',1100,40)
render('CAM_Exit','07_refined_exit.png',1100,32)
render('CAM_Lounge','07_refined_lounge.png',1100,32)
