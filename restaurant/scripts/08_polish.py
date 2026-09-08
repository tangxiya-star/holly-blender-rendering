import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'alchemist_04c_review.blend'))
s=bpy.context.scene
# Correct oversized reflected area-light disks with actual narrow strip sources.
for o in s.objects:
    if o.type=='LIGHT' and o.name.startswith('Service_'):
        o.data.shape='RECTANGLE';o.data.size=1.1;o.data.size_y=.035
        o.data.energy=25 if 'Oblique' in o.name else 40
        o.visible_glossy=False
        o.visible_transmission=False
# Glossy rays still see the lit architectural surfaces and their warm reflection.
for x in [-2.7,0,2.7]:
    o=box('Service_Physical_Luminaire',(x,9.9,2.37),(1.3,.13,.04),'Lighting',bpy.data.materials['PBR | satin blackened steel'],.009)
    e=mat('PBR | dim amber service lens',(.4,.24,.1),.4)
    p=e.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.52,.18,1);p.inputs['Emission Strength'].default_value=.7
    box('Service_Lens',(x,9.82,2.345),(1.1,.08,.008),'Lighting',e,.003)
# Slightly quieter blue fill, stronger warm pools and a more polished stone finish.
for o in s.objects:
    if o.type=='LIGHT' and o.name.startswith('Dome_Bounce'):o.data.energy*=.65
    if o.type=='LIGHT' and o.name.startswith('TableExperience_'):o.data.energy=13;o.data.color=(1,.57,.21)
m=bpy.data.materials['PBR | honed blue-grey mineral stone'];p=m.node_tree.nodes.get('Principled BSDF')
n=m.node_tree.nodes;l=m.node_tree.links
old=p.inputs['Roughness'].links[0].from_socket
for link in list(p.inputs['Roughness'].links):l.remove(link)
factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';factor.inputs[1].default_value=.68;factor.name='Polish roughness adjustment';l.new(old,factor.inputs[0]);l.new(factor.outputs[0],p.inputs['Roughness'])
p.inputs['Coat Weight'].default_value=.18
# The lettering sits proud of the veneer rather than behind it.
if bpy.data.objects.get('Entrance_Lettering'):bpy.data.objects['Entrance_Lettering'].location.y=-19.3
for o in s.objects:
    if o.parent is None and o.users_collection:
        parent=bpy.data.objects.get(o.users_collection[0].name)
        if parent and parent!=o:o.parent=parent
s.camera=bpy.data.objects['CAM_Hero'];s.frame_set(1)
if bpy.data.objects['WALKTHROUGH'].animation_data:bpy.data.objects['WALKTHROUGH'].animation_data.action.name='Walkthrough_60s'
save('alchemist_04d_polished.blend')
render('CAM_Hero','08_polished_hero.png',1200,48)
render('CAM_Table','08_polished_table.png',1100,40)
