"""Original worn-stone tabletop; world-space detail in meters."""
import bpy, math, random
from mathutils import Vector
from mathutils.noise import noise

def material():
    m=bpy.data.materials.new('Stone | worn warm limestone, mineral pits and soft sheen');m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;b=n.get('Principled BSDF')
    b.inputs['Roughness'].default_value=.68
    tex=n.new('ShaderNodeTexCoord')
    def nz(scale,detail):
        t=n.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=scale;t.inputs['Detail'].default_value=detail;t.inputs['Roughness'].default_value=.72
        l.new(tex.outputs['Object'],t.inputs['Vector']);return t
    def ramp(source,positions,colors):
        r=n.new('ShaderNodeValToRGB')
        for i,(p,c) in enumerate(zip(positions,colors)):
            e=r.color_ramp.elements[i] if i<2 else r.color_ramp.elements.new(p)
            e.position=p;e.color=(*c,1)
        l.new(source,r.inputs[0]);return r
    low=nz(34,5);mid=nz(230,5);fine=nz(1900,3)
    color=ramp(low.outputs['Fac'],[.18,.48,.8],[(.038,.043,.033),(.125,.135,.116),(.235,.242,.215)])
    l.new(color.outputs[0],b.inputs['Base Color'])
    pits=ramp(mid.outputs['Fac'],[.32,.48,.53,.68],[(.03,)*3,(.08,)*3,(.66,)*3,(.76,)*3])
    bump=n.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.0007;bump.inputs['Strength'].default_value=.85
    l.new(pits.outputs[0],bump.inputs['Height'])
    micro=n.new('ShaderNodeBump');micro.inputs['Distance'].default_value=.00009;micro.inputs['Strength'].default_value=.45
    l.new(fine.outputs['Fac'],micro.inputs['Height']);l.new(bump.outputs['Normal'],micro.inputs['Normal']);l.new(micro.outputs['Normal'],b.inputs['Normal'])
    rough=ramp(mid.outputs['Fac'],[.25,.75],[(.42,)*3,(.81,)*3]);l.new(rough.outputs[0],b.inputs['Roughness'])
    return m

def build_stage(collection):
    rng=random.Random(61924);scars=[]
    for i in range(420):
        x=rng.uniform(-.22,.22);y=rng.uniform(-.25,.30)
        if x*x+y*y<.072**2:continue
        a=rng.uniform(-math.pi,math.pi)
        scars.append((x,y,math.cos(a),math.sin(a),rng.uniform(.002,.011),rng.uniform(.0006,.0025),rng.uniform(.00014,.0008)))
    count=501;verts=[];faces=[]
    for j in range(count):
        y=-.35+j*.8/(count-1)
        active=[s for s in scars if abs(y-s[1])<s[4]+s[5]]
        for i in range(count):
            x=-.4+i*.8/(count-1)
            z=-.00010+.00004*noise(Vector((x*55,y*55,9)))
            if x*x+y*y>.068**2:
                for cx,cy,cc,ss,length,width,depth in active:
                    dx=x-cx;dy=y-cy
                    if abs(dx)>length+width:continue
                    u=(dx*cc+dy*ss)/length;v=(-dx*ss+dy*cc)/width
                    q=u*u+v*v+.12*noise(Vector((x*950,y*950,3)))
                    if q<1:z-=depth*min(1,(1-q)*3)
            verts.append((x,y,z))
    for j in range(count-1):
        for i in range(count-1):
            a=j*count+i;faces.append((a,a+1,a+count+1,a+count))
    mesh=bpy.data.meshes.new('Stone surface mesh');mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new('Stage | worn stone tabletop',mesh);collection.objects.link(obj);mesh.materials.append(material())
    for p in mesh.polygons:p.use_smooth=True
    return {'surface':obj.name,'scars':len(scars),'vertices':len(verts)}
