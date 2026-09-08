"""Original weathered tabletop with real recessed relief at several scales.

The reference reads as etched, worn mineral islands, not uniform fine noise.
Coordinates remain in the original build's metres; root controls global scale.
"""
import bpy, math, random
import numpy as np

def material():
    m=bpy.data.materials.new('Stone | worn limestone islands, irregular etched recesses');m.use_nodes=True
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
    low=nz(21,3);mid=nz(590,3);fine=nz(2450,2)
    color=ramp(low.outputs['Fac'],[.18,.48,.8],[(.061,.069,.054),(.119,.13,.109),(.178,.188,.162)])
    depth=n.new('ShaderNodeAttribute');depth.attribute_name='Stone recess depth'
    weathering=ramp(depth.outputs['Fac'],[0,.35,1],[(1.04,1.04,1.02),(.81,.82,.78),(.55,.57,.52)])
    mixed=n.new('ShaderNodeMixRGB');mixed.blend_type='MULTIPLY';mixed.inputs[0].default_value=1
    l.new(color.outputs[0],mixed.inputs[1]);l.new(weathering.outputs[0],mixed.inputs[2]);l.new(mixed.outputs[0],b.inputs['Base Color'])
    # Submillimetric grain supplements real geometry; no thresholded contour map.
    bump=n.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.00017;bump.inputs['Strength'].default_value=.43
    l.new(mid.outputs['Fac'],bump.inputs['Height'])
    micro=n.new('ShaderNodeBump');micro.inputs['Distance'].default_value=.000045;micro.inputs['Strength'].default_value=.24
    l.new(fine.outputs['Fac'],micro.inputs['Height']);l.new(bump.outputs['Normal'],micro.inputs['Normal']);l.new(micro.outputs['Normal'],b.inputs['Normal'])
    rough=ramp(low.outputs['Fac'],[.22,.78],[(.49,)*3,(.76,)*3]);l.new(rough.outputs[0],b.inputs['Roughness'])
    return m


def _noise_grid(x,y,scale,seed):
    """Vectorized smooth value noise, rotated per octave in the callers."""
    xx=x*scale+seed*.173;yy=y*scale-seed*.317
    ix=np.floor(xx);iy=np.floor(yy);fx=xx-ix;fy=yy-iy
    fx=fx*fx*(3-2*fx);fy=fy*fy*(3-2*fy)
    def h(a,b):
        val=np.sin(a*127.1+b*311.7+seed*53.4)*43758.5453123
        return val-np.floor(val)
    return ((h(ix,iy)*(1-fx)+h(ix+1,iy)*fx)*(1-fy)+
            (h(ix,iy+1)*(1-fx)+h(ix+1,iy+1)*fx)*fy)*2-1


def build_stage(collection):
    rng=random.Random(61924);scars=[]
    # Broad density regions leave genuine quiet worn islands between busy etched
    # zones. Each cluster has its own direction, scale and depth distribution.
    for ci in range(138):
        cx=rng.uniform(-.39,.39);cy=rng.uniform(-.34,.44)
        spread=rng.uniform(.013,.040);direction=rng.uniform(-math.pi,math.pi)
        weight=rng.uniform(.7,1.5)
        for pi in range(rng.randint(22,57)):
            x=cx+rng.gauss(0,spread);y=cy+rng.gauss(0,spread*.72)
            if not(-.399<x<.399 and -.349<y<.449):continue
            if x*x+y*y<.071**2:continue
            a=direction+rng.uniform(-1.2,1.2)
            length=rng.uniform(.0021,.0088)*rng.uniform(.75,1.2)
            width=length*rng.uniform(.21,.65)
            depth=rng.uniform(.00035,.00125)*weight
            scars.append((x,y,math.cos(a),math.sin(a),length,width,depth,rng.uniform(0,20)))
    # Scattered smaller recesses keep quiet islands mineral rather than plastic.
    for i in range(1100):
        x=rng.uniform(-.395,.395);y=rng.uniform(-.345,.445)
        if x*x+y*y<.071**2:continue
        a=rng.uniform(-math.pi,math.pi)
        length=rng.uniform(.0012,.0035);width=length*rng.uniform(.35,.85)
        scars.append((x,y,math.cos(a),math.sin(a),length,width,rng.uniform(.0002,.00065),rng.uniform(0,20)))
    # A few connected but broken clefts at a larger scale; deliberately neither
    # a uniform network nor straight incised scratches.
    for i in range(46):
        cx=rng.uniform(-.32,.32);cy=rng.uniform(-.27,.36);a=rng.uniform(-math.pi,math.pi)
        if cx*cx+cy*cy<.082**2:continue
        step=rng.uniform(.003,.006);bend=rng.uniform(-.8,.8)
        for k in range(rng.randint(4,8)):
            if rng.random()<.16:continue
            theta=a+bend*math.sin(k*.74)
            x=cx+math.cos(a)*step*k-math.sin(a)*math.sin(k*.8)*step*.65
            y=cy+math.sin(a)*step*k+math.cos(a)*math.sin(k*.8)*step*.65
            scars.append((x,y,math.cos(theta),math.sin(theta),rng.uniform(.003,.006),
                          rng.uniform(.00065,.0018),rng.uniform(.00065,.0014),rng.uniform(0,20)))

    count=961;step=.8/(count-1)
    xs=np.linspace(-.4,.4,count,dtype=np.float64)
    ys=np.linspace(-.35,.45,count,dtype=np.float64)
    x,y=np.meshgrid(xs,ys)
    edge_noise=_noise_grid(x,y,580,4)*.34+_noise_grid(.8*x-.6*y,.6*x+.8*y,1280,11)*.18
    floor_noise=_noise_grid(.6*x+.8*y,-.8*x+.6*y,430,29)
    recess=np.zeros_like(x);lip=np.zeros_like(x)
    for cx,cy,cc,ss,length,width,depth,phase in scars:
        bound=(length+width)*1.25
        xa=max(0,int((cx-bound+.4)/step));xb=min(count,int((cx+bound+.4)/step)+2)
        ya=max(0,int((cy-bound+.35)/step));yb=min(count,int((cy+bound+.35)/step)+2)
        if xa>=xb or ya>=yb:continue
        dx=x[ya:yb,xa:xb]-cx;dy=y[ya:yb,xa:xb]-cy
        u=(dx*cc+dy*ss)/length;v=(-dx*ss+dy*cc)/width
        q=u*u+v*v+edge_noise[ya:yb,xa:xb]+.13*np.sin(u*8+v*3+phase)
        # Abrupt, uneven chip shoulders and irregular bottoms catch real light.
        cut=np.clip((1-q)*6.5,0,1)*depth*(.88+.12*floor_noise[ya:yb,xa:xb])
        recess[ya:yb,xa:xb]=np.maximum(recess[ya:yb,xa:xb],cut)
        chipped_lip=.00008*np.exp(-((q-1.025)/.12)**2)
        lip[ya:yb,xa:xb]=np.maximum(lip[ya:yb,xa:xb],chipped_lip)
    # Preserve the original contact plane and ease relief in outside its footprint.
    r=np.sqrt(x*x+y*y);contact=np.clip((r-.068)/.005,0,1)
    contact=contact*contact*(3-2*contact)
    micro_relief=.00006*_noise_grid(x,y,270,7)
    z=-.00010+contact*(micro_relief+lip-recess)

    co=np.column_stack((x.ravel(),y.ravel(),z.ravel())).astype(np.float32)
    grid=np.arange(count*count,dtype=np.int32).reshape(count,count)
    quads=np.column_stack((grid[:-1,:-1].ravel(),grid[:-1,1:].ravel(),
                           grid[1:,1:].ravel(),grid[1:,:-1].ravel()))
    mesh=bpy.data.meshes.new('Stone surface mesh')
    mesh.vertices.add(co.shape[0]);mesh.vertices.foreach_set('co',co.ravel())
    mesh.loops.add(quads.size);mesh.loops.foreach_set('vertex_index',quads.ravel())
    mesh.polygons.add(quads.shape[0])
    mesh.polygons.foreach_set('loop_start',np.arange(0,quads.size,4,dtype=np.int32))
    mesh.polygons.foreach_set('loop_total',np.full(quads.shape[0],4,dtype=np.int32))
    mesh.polygons.foreach_set('use_smooth',np.ones(quads.shape[0],dtype=bool))
    mesh.update(calc_edges=True)
    attr=mesh.attributes.new('Stone recess depth','FLOAT','POINT')
    attr.data.foreach_set('value',np.clip(recess.ravel()/.0014,0,1).astype(np.float32))
    obj=bpy.data.objects.new('Stage | worn stone tabletop',mesh)
    collection.objects.link(obj);mesh.materials.append(material())
    obj['detail']='Irregular clustered physical recesses, deep crevices, chipped shoulders, quiet worn islands; fine grain is secondary.'
    obj['unscaled_contact_height_m']=-.00010
    return {'surface':obj.name,'scars':len(scars),'vertices':co.shape[0],
            'grid':count,'triangles':quads.shape[0]*2,
            'maximum_unscaled_recess_m':float(recess.max()),
            'contact_height_m':-.00010}
