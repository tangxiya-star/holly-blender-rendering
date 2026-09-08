import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from furniture import add_chairs
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'alchemist_02_architecture.blend'))

def pbr(name,key,metal=0,tile=1):
    m=mat(name,(.2,.2,.2));n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Metallic'].default_value=metal
    for kind,socket in [('basecolor','Base Color'),('roughness','Roughness'),('normal',None)]:
        tex=n.new('ShaderNodeTexImage');tex.name=key+'_'+kind;tex.label=key+' | '+kind
        tex.image=bpy.data.images.load(str(ROOT/'textures'/('pbr_'+key+'_'+kind+'.png')),check_existing=True)
        if kind!='basecolor':tex.image.colorspace_settings.name='Non-Color'
        if kind=='normal':
            norm=n.new('ShaderNodeNormalMap');norm.inputs['Strength'].default_value=.25;l.new(tex.outputs['Color'],norm.inputs['Color']);l.new(norm.outputs['Normal'],p.inputs['Normal'])
        else:l.new(tex.outputs['Color'],p.inputs[socket])
    m['tile_m']=tile
    return m

M={
'stone':pbr('PBR | honed blue-grey mineral stone','stone',.05,2.0),
'charcoal':pbr('PBR | charcoal mineral plaster','charcoal',0,1.5),
'brass':pbr('PBR | aged architectural bronze','brass',.83,1.0),
'wood':pbr('PBR | dark smoked oak','oak',0,1.4),
'fabric':pbr('PBR | midnight woven upholstery','fabric',0,.5),
'concrete':pbr('PBR | weathered pale masonry','concrete',0,1.5),
'metal':mat('PBR | satin blackened steel',(.015,.018,.023),.29,.83),
'porcelain':mat('PBR | warm ivory porcelain',(.66,.63,.55),.2,0),
'glass':mat('PBR | fine crystal',(.94,.98,1),.07,0),
'floor':pbr('PBR | dark polished dining floor','charcoal',.08,2.0),
'food':mat('PBR | restrained olive tasting form',(.065,.08,.018),.4,0),
'emitter':mat('PBR | warm opal light',(.7,.48,.2),.25,0)}
p=M['glass'].node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=1;p.inputs['IOR'].default_value=1.46
p=M['emitter'].node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.64,.28,1);p.inputs['Emission Strength'].default_value=4
# Floor has broad restrained specular response, independent from the rough plaster.
n=M['floor'].node_tree.nodes;l=M['floor'].node_tree.links;p=n.get('Principled BSDF')
for link in list(p.inputs['Roughness'].links):l.remove(link)
p.inputs['Roughness'].default_value=.24
for link in list(p.inputs['Base Color'].links):l.remove(link)
p.inputs['Base Color'].default_value=(.024,.029,.039,1)

def assign(o,m):
    if o.type not in ['MESH','CURVE','FONT']:return
    o.data.materials.clear();o.data.materials.append(m)

for o in list(bpy.context.scene.objects):
    name=o.name
    if o.type!='MESH' or name=='Dome_Projection':continue
    m=M['charcoal']
    if name.startswith(('Counter_','Island_','Arrival_Bar_Stone','Lounge_Table')):m=M['stone']
    if name.startswith(('Base_','Counter_Underslab','Counter_Leg','Service_Mullion','Service_Lintel','Service_Sill','Dome_Rim','Transition_Reveal','Arrival_Panel','Arrival_Skirting')):m=M['metal']
    if name.startswith(('Floor_Dining','Floor_Transition','Floor_Service')):m=M['floor']
    if name.startswith(('Floor_Arrival','Lounge_Leg')):m=M['wood']
    if name.startswith(('Facade','Street_','Portal_Lintel')):m=M['concrete']
    if name.startswith(('Entrance_','Portal_Bronze','Arrival_Service_Counter','Arrival_Bar_Backdrop')):m=M['brass']
    if name.startswith(('Service_Glazing',)):m=M['glass']
    if name.startswith(('Service_Worktop','Service_Shelf')):m=M['metal']
    if name.startswith(('Lounge_Back','Lounge_Seat')):m=M['fabric']
    assign(o,m)
add_chairs(M)

def uv_project(o):
    if o.type!='MESH' or o.name=='Dome_Projection':return
    tile=o.data.materials[0].get('tile_m',1) if o.data.materials else 1
    uv=o.data.uv_layers.get('SurfaceUV') or o.data.uv_layers.new(name='SurfaceUV')
    for poly in o.data.polygons:
        axis=max(range(3),key=lambda i:abs(poly.normal[i]));dims=[i for i in range(3) if i!=axis]
        for li in poly.loop_indices:
            v=o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=(v[dims[0]]/tile,v[dims[1]]/tile)
for o in bpy.context.scene.objects:uv_project(o)
# Add subtle physical board joints over the inferred arrival floor.
for i in range(18):
    x=-4.25+i*.5
    box('Oak_Board_Joint',(x,-15.5,.001),(.003,6.98,.002),'Architecture',M['metal'])
for o in bpy.context.scene.objects:
    if o.parent is None and o.type=='MESH':
        category=o.users_collection[0].name
        if bpy.data.objects.get(category):o.parent=bpy.data.objects[category]
bpy.ops.file.pack_all();save('alchemist_03_materials.blend')
render('CAM_Hero','03_materials_hero.png',1100,32)
render('CAM_Table','03_materials_table.png',1000,32)
print('PHASE 3 materials use image-based PBR maps, packed in source')
