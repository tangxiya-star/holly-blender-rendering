import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'alchemist_05_final.blend'))
o=box('Floor_Threshold_Bridge',(0,-19,-.002),(3.15,.38,.012),'Architecture',bpy.data.materials['PBR | aged architectural bronze'],.002)
o.parent=bpy.data.objects['Architecture']
save('alchemist_05_final.blend')
