import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from furniture import add_table_experience
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'alchemist_04_lighting.blend'))
mat('PBR | warm ivory porcelain',(.66,.63,.55),.2)
mat('PBR | restrained olive tasting form',(.065,.08,.018),.4)
M={k:bpy.data.materials[n] for k,n in {'brass':'PBR | aged architectural bronze','porcelain':'PBR | warm ivory porcelain','glass':'PBR | fine crystal','metal':'PBR | satin blackened steel','food':'PBR | restrained olive tasting form','emitter':'PBR | warm opal light'}.items()}
for o in list(bpy.context.scene.objects):
    if o.name.startswith('Table_Preview_Pool'):bpy.data.objects.remove(o,do_unlink=True)
print(add_table_experience(M))
for o in bpy.context.scene.objects:
    if o.parent is None and o.users_collection:
        p=bpy.data.objects.get(o.users_collection[0].name)
        if p and p!=o:o.parent=p
bpy.ops.file.pack_all();save('alchemist_04b_furnished.blend')
render('CAM_Hero','06_furniture_hero.png',1400,64)
render('CAM_Table','06_furniture_table.png',1100,48)
