import sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import bpy
from aerial_common import render
from aerial_surfaces import polygon_mesh

def target_facade_rhythm():
    for m in [m for m in bpy.data.materials if m.name.startswith('CPH | facade')]:
        n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
        if n.get('Nyhavn only | aerial facade rhythm'):continue
        def mathnode(op,a=None,b=None):
            x=n.new('ShaderNodeMath');x.operation=op
            for i,v in enumerate([a,b]):
                if v is None:continue
                if isinstance(v,(float,int)):x.inputs[i].default_value=v
                else:l.new(v,x.inputs[i])
            return x.outputs[0]
        g=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(g.outputs['Position'],sep.inputs[0])
        tangent=n.new('ShaderNodeVectorMath');tangent.operation='CROSS_PRODUCT';l.new(g.outputs['Normal'],tangent.inputs[0]);tangent.inputs[1].default_value=(0,0,1)
        dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';l.new(g.outputs['Position'],dot.inputs[0]);l.new(tangent.outputs['Vector'],dot.inputs[1])
        u=mathnode('FLOORED_MODULO',dot.outputs['Value'],2.75);z=mathnode('FLOORED_MODULO',sep.outputs['Z'],3.1)
        mask=mathnode('MULTIPLY',mathnode('GREATER_THAN',u,.43),mathnode('LESS_THAN',u,1.52))
        mask=mathnode('MULTIPLY',mask,mathnode('GREATER_THAN',z,.72));mask=mathnode('MULTIPLY',mask,mathnode('LESS_THAN',z,2.37))
        distance=n.new('ShaderNodeVectorMath');distance.operation='DISTANCE';l.new(g.outputs['Position'],distance.inputs[0]);distance.inputs[1].default_value=(1470,490,12)
        mask=mathnode('MULTIPLY',mask,mathnode('LESS_THAN',distance.outputs['Value'],230));mask=mathnode('MULTIPLY',mask,mathnode('GREATER_THAN',sep.outputs['Z'],4))
        mix=n.new('ShaderNodeMixRGB');mix.name='Nyhavn only | aerial facade rhythm';mix.inputs[1].default_value=(*m.diffuse_color[:3],1);mix.inputs[2].default_value=(.045,.062,.068,1)
        l.new(mask,mix.inputs[0]);l.new(mix.outputs[0],p.inputs['Base Color'])
        rough=mathnode('SUBTRACT',.8,mathnode('MULTIPLY',mask,.40));l.new(rough,p.inputs['Roughness'])
        bump=n.new('ShaderNodeBump');bump.invert=True;bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.10;l.new(mask,bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])

def refine():
    context=json.loads((ROOT/'data'/'context_geography.json').read_text())
    old=bpy.data.objects.get('Regional real shoreline | distant context')
    if old:bpy.data.objects.remove(old,do_unlink=True)
    polygon_mesh('Regional real shoreline | distant context',context['land'],1.91,'01_Real_Geography',bpy.data.materials['Ground | weathered urban mineral'])
    target_facade_rhythm()
    # Landmark script was refined against mapped building parts after initial construction.
    from landmarks import build_landmarks
    build_landmarks({})
    from aerial_cameras import build_cameras
    for o in list(bpy.data.collections['05_Cameras_and_Flight'].objects):bpy.data.objects.remove(o,do_unlink=True)
    bpy.context.scene.timeline_markers.clear()
    build_cameras()
    from aerial_lighting import build_lighting
    for o in list(bpy.data.collections['06_Daylight_and_Atmosphere'].objects):bpy.data.objects.remove(o,do_unlink=True)
    build_lighting()
    water=bpy.data.materials['Water | Baltic harbor blue green'];water.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.3
    s=bpy.context.scene;s.camera=bpy.data.objects['01 | HERO - Copenhagen from the southeast'];s.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'copenhagen_aerial.blend'))
    render(s.camera,'hero_refined_check.png',1440,32)
    render(s.camera,'hero_aerial.png',1920,64)
    render(bpy.data.objects['02 | Harbor and historic center'],'harbor_aerial.png',1600,48)
    render(bpy.data.objects['03 | Nyhavn - handoff approach'],'nyhavn_handoff.png',1440,48)
    s.camera=bpy.data.objects['01 | HERO - Copenhagen from the southeast'];s.frame_set(1)
    s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'copenhagen_aerial.blend'))

if __name__=='__main__':refine()
