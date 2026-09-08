"""Original eye-vessel geometry and procedural pigment, in Blender metres.

No photograph pixels are used. The iris image is a generated polar fiber field;
the body image is a generated graph of tapered capillaries beneath the finish.
Only build_eye(collection) is public. Central opening: r=.0158, z=.102 exactly.
"""
import bpy
import math
import random
import numpy as np
from mathutils import Vector
from mathutils.noise import noise

TAU=math.tau
BODY_RADIUS=.070
IRIS_RADIUS=.042
OPENING_RADIUS=.0158
OPENING_Z=.102
IRIS_EDGE_Z=.0918
BASE_Z=.002


def _mesh(name,verts,faces,col,mat,uv=None):
    me=bpy.data.meshes.new(name+' | explicit organic mesh')
    me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);col.objects.link(ob)
    me.materials.append(mat)
    for p in me.polygons:p.use_smooth=True
    if uv is not None:
        layer=me.uv_layers.new(name='PigmentUV')
        for p in me.polygons:
            for li in p.loop_indices:
                layer.data[li].uv=uv[me.loops[li].vertex_index]
    return ob


def _image(name,values):
    h,w=values.shape[:2]
    rgba=np.ones((h,w,4),dtype=np.float32)
    if values.ndim==2:rgba[:,:,:3]=values[:,:,None]
    else:rgba[:,:,:3]=values
    image=bpy.data.images.new(name,width=w,height=h,alpha=True,float_buffer=True)
    image.colorspace_settings.name='Non-Color'
    image.pixels.foreach_set(rgba.ravel());image.update();image.pack()
    image['origin']='Original procedural data, not the supplied photograph'
    return image


def _periodic_field(u,knots,seed):
    rng=np.random.default_rng(seed)
    values=rng.random(knots).astype(np.float32)
    q=u*knots
    lower=np.floor(q).astype(np.int32)
    f=q-lower
    f=f*f*(3-2*f)
    return values[lower%knots]*(1-f)+values[(lower+1)%knots]*f


def _iris_images():
    width,height=3072,1024
    u=np.arange(width,dtype=np.float32)[None,:]/width
    v=np.linspace(0,1,height,dtype=np.float32)[:,None]
    a=u*TAU
    # Each layer bends gently through the radial direction, rather than drawing
    # hundreds of straight spokes or a simple repeated radial sine wave.
    curvature=.0055*np.sin(v*8+2*np.sin(a*3))+.003*np.sin(v*17+a*7)*(np.sin(v*math.pi)**2)
    bent=u+curvature
    broad=_periodic_field(u,29,19)
    middle=_periodic_field(bent,175,51)
    fine=_periodic_field(bent+.0018*np.sin(v*14+a*9),487,75)
    finest=_periodic_field(bent+.00075*np.sin(v*24+a*13),1061,90)
    # Unequal sharp fiber cords, soft stroma between them, and occasional forks.
    cords=np.clip((middle-.32)/.50,0,1)**1.5
    fine_cords=np.clip((fine-.48)/.42,0,1)**1.8
    structure=.42*cords+.35*fine_cords+.23*finest
    base=np.array((.116,.145,.140),dtype=np.float32)
    gold=np.array((.345,.303,.185),dtype=np.float32)
    fiber_gold=np.clip(.12+.39*broad+.27*cords*(1-.55*v),0,.83)
    color=base[None,None,:]*(1-fiber_gold[:,:,None])+gold[None,None,:]*fiber_gold[:,:,None]
    color=color*(.61+.74*structure[:,:,None])
    pale_cords=np.clip((finest-.70)/.25,0,1)*(.20+.34*v)
    color+=pale_cords[:,:,None]*np.array((.22,.23,.16),dtype=np.float32)
    # Scalloped collarette varies in thickness and has fine radial dark crypts.
    scallop=.133+.034*np.sin(a*13+.7)+.023*np.sin(a*27-1.4)+.052*(_periodic_field(u,21,49)-.5)
    dark_edge=np.clip((scallop-v+.022)/.032,0,1)
    dark=np.array((.008,.012,.016),dtype=np.float32)
    color=color*(1-dark_edge[:,:,None]*.96)+dark[None,None,:]*(dark_edge[:,:,None]*.96)
    crypt=(np.clip((.25-middle)/.22,0,1)**2)*np.exp(-((v-scallop-.08)/.095)**2)
    color*=1-.66*crypt[:,:,None]
    # Sparse asymmetrical ochre / brown pigment flecks, following fibers.
    rng=np.random.default_rng(446)
    for k in range(21):
        au=float(rng.random());rv=float(rng.uniform(.25,.91))
        da=np.abs((u-au+.5)%1-.5)
        patch=np.exp(-(da/float(rng.uniform(.002,.007)))**2-((v-rv)/float(rng.uniform(.035,.105)))**2)
        pigment=np.array((.102,.061,.026),dtype=np.float32)
        weight=patch*float(rng.uniform(.22,.63))
        color=color*(1-weight[:,:,None])+pigment[None,None,:]*weight[:,:,None]
    limbus=np.clip((v-.947)/.050,0,1)
    color*=1-.48*limbus[:,:,None]
    # There is no painted illumination, highlight, contact shadow or camera view.
    return _image('Eye | original gray-green gold radial pigment',np.clip(color,.001,.8)),\
           _image('Eye | original iris fiber relief',np.clip(structure*(1-dark_edge*.7),0,1))


def _stroke(canvas,p0,p1,width,opacity):
    h,w=canvas.shape
    x0,y0=p0[0]*w,p0[1]*h;x1,y1=p1[0]*w,p1[1]*h
    sigma=max(.40,width)
    margin=int(math.ceil(sigma*3))+1
    for shift in (-w,0,w):
        xa,xb=x0+shift,x1+shift
        lo_x=max(0,int(min(xa,xb))-margin);hi_x=min(w,int(max(xa,xb))+margin+1)
        lo_y=max(0,int(min(y0,y1))-margin);hi_y=min(h,int(max(y0,y1))+margin+1)
        if hi_x<=lo_x or hi_y<=lo_y:continue
        yy,xx=np.mgrid[lo_y:hi_y,lo_x:hi_x]
        dx,dy=xb-xa,y1-y0
        t=np.clip(((xx-xa)*dx+(yy-y0)*dy)/(dx*dx+dy*dy+1e-8),0,1)
        d2=(xx-xa-t*dx)**2+(yy-y0-t*dy)**2
        brush=opacity*np.exp(-d2/(2*sigma*sigma))
        target=canvas[lo_y:hi_y,lo_x:hi_x]
        np.maximum(target,brush,out=target)


def _vein_image():
    width,height=3072,1536
    mask=np.zeros((height,width),dtype=np.float32)
    rng=random.Random(15491)
    def grow(start,finish,thickness,strength,seed,branch=True):
        rr=random.Random(seed)
        points=[]
        phase=rr.random()*TAU
        n=max(8,int(abs(start[1]-finish[1])*110))
        drift=rr.uniform(-.014,.014)
        for j in range(n+1):
            t=j/n
            u=start[0]*(1-t)+finish[0]*t+drift*math.sin(math.pi*t)+.0018*math.sin(13*t+phase)*math.sin(math.pi*t)
            v=start[1]*(1-t)+finish[1]*t
            points.append((u,v))
        for j in range(n):
            t=(j+.5)/n
            # Fade / taper to an embedded capillary, rather than a red wire.
            fade=(1-.66*t)*(.73+.27*math.sin(t*7+phase)**2)
            _stroke(mask,points[j],points[j+1],thickness*(1-.64*t),strength*fade)
        if branch:
            for k in range(rr.randint(2,4)):
                t=rr.uniform(.20,.76);idx=int(t*n);p=points[idx]
                end=(p[0]+rr.choice((-1,1))*rr.uniform(.008,.026),p[1]-rr.uniform(.07,.23))
                grow(p,end,thickness*.52,strength*.55,seed+101+k,False)
    for j in range(37):
        u=(j/37+rng.uniform(-.010,.010))%1
        start=(u,rng.uniform(.950,.990))
        finish=(u+rng.uniform(-.020,.020),rng.uniform(.18,.68))
        grow(start,finish,rng.uniform(.53,1.14),rng.uniform(.36,.80),1001+j)
    # A few longer fine capillaries from lower body quadrants, not a uniform halo.
    for j in range(9):
        u=rng.random()
        grow((u,.35),(u+rng.uniform(-.023,.023),.08),.61,.31,503+j,False)
    return _image('Eye | original tapered branching sub-surface veins',mask)


def _material(name,color,roughness,sss=0,scale=.001):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    bs=nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=roughness
    bs.inputs['IOR'].default_value=1.43
    bs.inputs['Subsurface Weight'].default_value=sss
    bs.inputs['Subsurface Scale'].default_value=scale
    bs.inputs['Subsurface Radius'].default_value=(1,.55,.32)
    return mat,nodes,links,bs


def _materials():
    pigment,structure=_iris_images();veins=_vein_image()
    body,n,l,b=_material('Eye | warm pale body, capillaries beneath thin finish',(.72,.67,.565),.29,.075,.0011)
    im=n.new('ShaderNodeTexImage');im.image=veins;im.interpolation='Linear';im.extension='REPEAT'
    strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.53
    l.new(im.outputs['Color'],strength.inputs[0])
    mix=n.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.72,.675,.575,1);mix.inputs[2].default_value=(.41,.08,.095,1)
    l.new(strength.outputs[0],mix.inputs[0]);l.new(mix.outputs[0],b.inputs['Base Color'])
    tx=n.new('ShaderNodeTexCoord');ns=n.new('ShaderNodeTexNoise');ns.inputs['Scale'].default_value=105;ns.inputs['Detail'].default_value=2
    l.new(tx.outputs['Object'],ns.inputs['Vector'])
    rr=n.new('ShaderNodeMapRange');rr.inputs['From Min'].default_value=.2;rr.inputs['From Max'].default_value=.8;rr.inputs['To Min'].default_value=.24;rr.inputs['To Max'].default_value=.35
    l.new(ns.outputs['Fac'],rr.inputs['Value']);l.new(rr.outputs['Result'],b.inputs['Roughness'])
    b.inputs['Coat Weight'].default_value=.22;b.inputs['Coat Roughness'].default_value=.18

    iris,n,l,b=_material('Eye | gray-green gold radial stroma and crypts',(.16,.18,.13),.33,.025,.00023)
    im=n.new('ShaderNodeTexImage');im.name='Original polar iris pigment';im.image=pigment;im.interpolation='Cubic';im.extension='REPEAT'
    l.new(im.outputs['Color'],b.inputs['Base Color'])
    height=n.new('ShaderNodeTexImage');height.name='Coherent fiber microrelief';height.image=structure;height.interpolation='Cubic';height.extension='REPEAT'
    bump=n.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.00021;bump.inputs['Strength'].default_value=.27
    l.new(height.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs['Normal'],b.inputs['Normal'])

    clear,n,l,b=_material('Eye | 65 micron transparent surface film',(.985,.99,.995),.105)
    b.inputs['Transmission Weight'].default_value=1;b.inputs['IOR'].default_value=1.39
    tx=n.new('ShaderNodeTexCoord');ns=n.new('ShaderNodeTexNoise');ns.inputs['Scale'].default_value=170;ns.inputs['Detail'].default_value=2
    l.new(tx.outputs['Object'],ns.inputs['Vector'])
    rr=n.new('ShaderNodeMapRange');rr.inputs['From Min'].default_value=.2;rr.inputs['From Max'].default_value=.8;rr.inputs['To Min'].default_value=.085;rr.inputs['To Max'].default_value=.16
    l.new(ns.outputs['Fac'],rr.inputs['Value']);l.new(rr.outputs['Result'],b.inputs['Roughness'])
    well,n,l,b=_material('Eye | deeply shadowed inner opening wall',(.007,.009,.012),.29)
    return {'body':body,'iris':iris,'clear':clear,'well':well,'images':[pigment,structure,veins]}


_BODY_PROFILE=[(0,.002),(.025,.002),(.041,.0042),(.052,.010),(.061,.020),
               (.067,.035),(.070,.052),(.0676,.066),(.0612,.078),
               (.053,.0865),(.046,.0901),(.042,.0918)]


def _profile_points():
    pts=[]
    for j in range(len(_BODY_PROFILE)-1):
        p0=Vector(_BODY_PROFILE[max(0,j-1)]);p1=Vector(_BODY_PROFILE[j]);p2=Vector(_BODY_PROFILE[j+1]);p3=Vector(_BODY_PROFILE[min(len(_BODY_PROFILE)-1,j+2)])
        for k in range(16):
            t=k/16
            p=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
            pts.append((max(0,p.x),max(BASE_Z,p.y)))
    pts.append(_BODY_PROFILE[-1])
    return pts


def _body(col,mat):
    profile=_profile_points();segments=512
    verts=[];uv=[];faces=[]
    for j,(r,z) in enumerate(profile):
        v=j/(len(profile)-1)
        for i in range(segments+1):
            a=TAU*i/segments
            # The reference is a designed convex vessel, with restrained physical
            # manufacturing variation rather than a conspicuously lumpy sculpture.
            soft=math.sin(math.pi*v)**1.4
            rr=r*(1+soft*(.006*math.cos(a+.7)+.003*math.sin(3*a-.8)))
            zz=z+soft*.00024*math.sin(2*a+.5)
            verts.append((rr*math.cos(a),rr*math.sin(a),max(BASE_Z,zz)))
            uv.append((i/segments,v))
    for j in range(len(profile)-1):
        for i in range(segments):
            q=j*(segments+1)+i
            # Profile travels upward around the external body; outward winding.
            faces.append((q,q+1,q+segments+2,q+segments+1))
    ob=_mesh('Eye vessel | continuous pale body and flattened contact base',verts,faces,col,mat,uv)
    ob['estimated_width_m']=.14;ob['base_z_m']=BASE_Z
    return ob


def iris_surface(r,a):
    t=max(0,min(1,(r-OPENING_RADIUS)/(IRIS_RADIUS-OPENING_RADIUS)))
    z=OPENING_Z-(OPENING_Z-IRIS_EDGE_Z)*t**1.36
    z+=.00007*math.sin(6*a+.5)*math.sin(math.pi*t)**2
    return z


def _iris(col,mat,name,offset=0,clear=False):
    rings,segments=144,1024
    verts=[];uv=[];faces=[]
    for j in range(rings+1):
        t=j/rings;r=OPENING_RADIUS+(IRIS_RADIUS-OPENING_RADIUS)*t
        for i in range(segments+1):
            a=TAU*i/segments
            z=iris_surface(r,a)+offset
            verts.append((r*math.cos(a),r*math.sin(a),z))
            uv.append((i/segments,t))
    for j in range(rings):
        for i in range(segments):
            q=j*(segments+1)+i
            faces.append((q+segments+1,q+segments+2,q+1,q))
    ob=_mesh(name,verts,faces,col,mat,uv)
    if clear:
        solid=ob.modifiers.new('Actual thin surface film, no enlarged glass dome','SOLIDIFY')
        solid.thickness=.000065;solid.offset=0
    return ob


def _well(col,mat):
    n=256;verts=[];faces=[]
    for z,r in [(OPENING_Z,OPENING_RADIUS),(.0955,OPENING_RADIUS),(.089,.0148)]:
        for i in range(n):
            a=TAU*i/n;verts.append((r*math.cos(a),r*math.sin(a),z))
    for j in range(2):
        for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    c=len(verts);verts.append((0,0,.089))
    for i in range(n):faces.append((c,2*n+i,2*n+(i+1)%n))
    return _mesh('Eye vessel | recessed central food opening',verts,faces,col,mat)


def build_eye(collection):
    mats=_materials()
    body=_body(collection,mats['body'])
    iris=_iris(collection,mats['iris'],'Eye vessel | radial fibrous iris and scalloped collarette')
    film=_iris(collection,mats['clear'],'Eye vessel | thin clear finish over iris',.000105,True)
    well=_well(collection,mats['well'])
    return {'objects':[body,iris,film,well],
            'body_width_m':BODY_RADIUS*2,'base_z_m':BASE_Z,
            'iris_outer_radius_m':IRIS_RADIUS,'iris_outer_edge_z_m':IRIS_EDGE_Z,
            'opening_radius_m':OPENING_RADIUS,'opening_edge_z_m':OPENING_Z,
            'food_interface':'Insert top supplied separately at .1055 m; clear roe surface .106 m',
            'packed_original_images':[im.name for im in mats['images']],
            'materials':mats,'mesh_vertices':sum(len(o.data.vertices) for o in [body,iris,film,well]),
            'notes':'Original custom loft, polar fiber pigment, tapered vein graph, actual thin finish; no source-photo mapping.'}
