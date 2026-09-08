import bpy, sys, json, importlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
from common import ROOT
import architecture, surfaces, furniture

assert bpy.context.scene.name.startswith('Copenhagen'), 'Open the Copenhagen blockout first.'

for name in ['Blockout_Buildings','Blockout_Roads']:
    c=bpy.data.collections.get(name)
    if c:
        for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(c)
architecture.build_architecture()
surfaces.build_surfaces()
furniture.build_furniture()
for o in list(bpy.data.collections['Lighting'].objects):bpy.data.objects.remove(o,do_unlink=True)
common.lighting()
import navigation
navigation.build_navigation()
bpy.context.scene.camera=bpy.data.objects['01 | Human eye street']
reviewed='--reviewed' in sys.argv
common.save('copenhagen_03_refined.blend' if reviewed else 'copenhagen_02_detailed.blend')
common.render('01 | Human eye street','03_refined_street.png' if reviewed else '02_first_street.png',1200,48)
