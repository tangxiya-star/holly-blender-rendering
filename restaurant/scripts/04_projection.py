import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'alchemist_03_materials.blend'))
dome=bpy.data.objects['Dome_Projection']
import bmesh
bm=bmesh.new();bm.from_mesh(dome.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(dome.data);bm.free()
uv=dome.data.uv_layers.new(name='ProjectionUV')
na=144;nr=48
for p in dome.data.polygons:
    for li in p.loop_indices:
        idx=dome.data.loops[li].vertex_index;j=idx//(na+1);i=idx%(na+1)
        uv.data[li].uv=(i/na+.25,j/nr)
m=mat('PROJECTION | replace this image',(.001,.001,.002),1,0);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
t=n.new('ShaderNodeTexImage');t.name='REPLACEABLE_PROJECTION';t.label='Swap image / movie here; 2:1 hemisphere artwork'
t.image=bpy.data.images.load(str(ROOT/'textures'/'projection_underwater.png'),check_existing=True)
l.new(t.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=3.5
dome.data.materials.clear();dome.data.materials.append(m)
m['projection_mapping']='U azimuth; V elevation. Seam at entrance/south. Replace REPLACEABLE_PROJECTION image.'
for o in list(bpy.data.objects):
    if o.name.startswith('Blockout_Soft_Dome'):bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.file.pack_all();save('alchemist_03b_projection.blend')
render('CAM_Hero','04_projection_hero.png',1100,40)
render('CAM_Dome','04_projection_dome.png',1000,32)
