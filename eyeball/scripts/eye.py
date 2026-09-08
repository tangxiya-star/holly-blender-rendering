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
IRIS_RADIUS=.0425
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
    curvature=.0011*np.sin(v*8+2*np.sin(a*3))+.0006*np.sin(v*17+a*7)*(np.sin(v*math.pi)**2)
    bent=u+curvature
    broad=_periodic_field(u,29,19)
    middle=_periodic_field(bent,175,51)
    fine=_periodic_field(bent+.00036*np.sin(v*14+a*9),487,75)
    finest=_periodic_field(bent+.00015*np.sin(v*24+a*13),1061,90)
    # Unequal sharp fiber cords, soft stroma between them, and occasional forks.
    cords=np.clip((middle-.32)/.50,0,1)**1.5
    fine_cords=np.clip((fine-.48)/.42,0,1)**1.8
    phase=_periodic_field(u,389,422)*TAU
    frequency=18+20*_periodic_field(u,211,993)
    short_fibers=.32+.68*np.clip(np.sin(v*frequency+phase),0,1)
    fine_cords*=short_fibers
    cords*=.68+.32*short_fibers
    structure=.20*cords+.47*fine_cords+.33*finest*(.60+.40*short_fibers)
    base=np.array((.250,.290,.275),dtype=np.float32)
    gold=np.array((.530,.480,.330),dtype=np.float32)
    fiber_gold=np.clip(.12+.39*broad+.27*cords*(1-.55*v),0,.83)
    color=base[None,None,:]*(1-fiber_gold[:,:,None])+gold[None,None,:]*fiber_gold[:,:,None]
    color=color*(.83+.35*structure[:,:,None])
    pale_cords=np.clip((finest-.70)/.25,0,1)*(.20+.34*v)
    color+=pale_cords[:,:,None]*np.array((.17,.18,.13),dtype=np.float32)
    # Scalloped collarette varies in thickness and has fine radial dark crypts.
    scallop=.158+.020*np.sin(a*13+.7)+.014*np.sin(a*27-1.4)+.033*(_periodic_field(u,21,49)-.5)
    dark_edge=np.clip((scallop-v+.013)/.021,0,1)
    dark=np.array((.008,.012,.016),dtype=np.float32)
    color=color*(1-dark_edge[:,:,None]*.96)+dark[None,None,:]*(dark_edge[:,:,None]*.96)
    crypt=(np.clip((.25-middle)/.22,0,1)**2)*np.exp(-((v-scallop-.08)/.095)**2)
    color*=1-.36*crypt[:,:,None]
    # Sparse asymmetrical ochre / brown pigment flecks, following fibers.
    rng=np.random.default_rng(446)
    for k in range(21):
        au=float(rng.random());rv=float(rng.uniform(.25,.91))
        da=np.abs((u-au+.5)%1-.5)
        patch=np.exp(-(da/float(rng.uniform(.002,.007)))**2-((v-rv)/float(rng.uniform(.035,.105)))**2)
        pigment=np.array((.102,.061,.026),dtype=np.float32)
        weight=patch*float(rng.uniform(.22,.63))
        color=color*(1-weight[:,:,None])+pigment[None,None,:]*weight[:,:,None]
    limbus=np.clip((v-.956)/.044,0,1)
    limbus=limbus*limbus*(3-2*limbus)
    ivory=np.array((.72,.675,.575),dtype=np.float32)
    color=color*(1-.80*limbus[:,:,None])+ivory[None,None,:]*(.80*limbus[:,:,None])
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
    def grow(start,finish,thickness,strength,seed,depth=3):
        rr=random.Random(seed)
        points=[]
        phase=rr.random()*TAU
        n=max(8,int(abs(start[1]-finish[1])*110))
        drift=rr.uniform(-.020,.020)
        for j in range(n+1):
            t=j/n
            waviness=.0058 if thickness>1.8 else .0025
            u=start[0]*(1-t)+finish[0]*t+drift*math.sin(math.pi*t)+waviness*math.sin(24*t+phase)*math.sin(math.pi*t)+waviness*.28*math.sin(63*t-phase)*math.sin(math.pi*t)
            v=start[1]*(1-t)+finish[1]*t
            points.append((u,v))
        for j in range(n):
            t=(j+.5)/n
            # Fade / taper to an embedded capillary, rather than a red wire.
            fade=(1-.66*t)*(.73+.27*math.sin(t*7+phase)**2)
            if thickness > 1.8:
                _stroke(mask,points[j],points[j+1],thickness*3.6*(1-.45*t),strength*fade*.08)
            _stroke(mask,points[j],points[j+1],thickness*(1-.64*t),strength*fade)
        if depth>0:
            for k in range(rr.randint(2,3)):
                t=rr.uniform(.20,.76);idx=int(t*n);p=points[idx]
                side=rr.choice((-1,1))
                downward=rr.uniform(.023,.11) if depth>1 else rr.uniform(-.035,.052)
                end=(p[0]+side*rr.uniform(.009,.036)/max(1,4-depth),p[1]-downward)
                grow(p,end,thickness*.63,strength*.71,seed+101+k,depth-1)
    for j in range(59):
        u=(j/59+rng.uniform(-.008,.008))%1
        start=(u,rng.uniform(.950,.990))
        # Most trees stay near the limbus, with a minority reaching farther down.
        finish_v=rng.uniform(.38,.64) if j%5==0 else rng.uniform(.73,.90)
        finish=(u+rng.uniform(-.019,.019),finish_v)
        grow(start,finish,rng.uniform(.63,1.16),rng.uniform(.59,.96),1001+j,3)
    # Disconnected-looking lower branches follow oblique, varied local routes;
    # avoid one family of long meridional strings from iris to contact base.
    for j in range(19):
        u=rng.random()
        v=rng.uniform(.31,.62)
        grow((u,v),(u+rng.choice((-1,1))*rng.uniform(.013,.034),v-rng.uniform(.05,.16)),.62,.42,503+j,2)
    # Sparse visible trunks at the hero-facing side, embedded with softer
    # peripheral pigment rather than raising the veins above the resin.
    for j,(u,v,end) in enumerate([(.615,.895,.47),(.678,.96,.53),(.747,.92,.39),(.814,.87,.48),(.883,.935,.59)]):
        grow((u,v),(u+rng.uniform(-.024,.027),end),rng.uniform(2.2,3.3),rng.uniform(.72,.92),7200+j,3)
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
    veins=_vein_image()
    body,n,l,b=_material('Eye | warm pale body, capillaries beneath thin finish',(.72,.67,.565),.29,.075,.0011)
    im=n.new('ShaderNodeTexImage');im.image=veins;im.interpolation='Linear';im.extension='REPEAT'
    strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.76
    l.new(im.outputs['Color'],strength.inputs[0])
    mix=n.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.72,.675,.575,1);mix.inputs[2].default_value=(.36,.048,.073,1)
    l.new(strength.outputs[0],mix.inputs[0])
    tx=n.new('ShaderNodeTexCoord');ns=n.new('ShaderNodeTexNoise');ns.inputs['Scale'].default_value=105;ns.inputs['Detail'].default_value=2
    l.new(tx.outputs['Object'],ns.inputs['Vector'])
    sep=n.new('ShaderNodeSeparateXYZ');l.new(tx.outputs['Object'],sep.inputs['Vector'])
    lower=n.new('ShaderNodeMapRange');lower.clamp=True
    lower.inputs['From Min'].default_value=.002;lower.inputs['From Max'].default_value=.092
    lower.inputs['To Min'].default_value=0;lower.inputs['To Max'].default_value=1
    l.new(sep.outputs['Z'],lower.inputs['Value'])
    mottles=n.new('ShaderNodeTexNoise');mottles.name='Quiet subsurface rose mottling';mottles.inputs['Scale'].default_value=57;mottles.inputs['Detail'].default_value=3
    l.new(tx.outputs['Object'],mottles.inputs['Vector'])
    base=n.new('ShaderNodeValToRGB');base.name='Layered resin: vascular lower edge through warm white sclera'
    palette=[(0,(.19,.015,.019)),(.22,(.36,.035,.022)),(.40,(.62,.22,.14)),(.58,(.82,.58,.43)),(.76,(.84,.80,.70)),(1,(.80,.72,.62))]
    for i,(pos,col) in enumerate(palette):
        e=base.color_ramp.elements[i] if i<2 else base.color_ramp.elements.new(pos);e.position=pos;e.color=(*col,1)
    pigment_warp=n.new('ShaderNodeMath');pigment_warp.operation='MULTIPLY_ADD';pigment_warp.inputs[1].default_value=.15;pigment_warp.inputs[2].default_value=-.075
    l.new(mottles.outputs['Fac'],pigment_warp.inputs[0])
    pigment_height=n.new('ShaderNodeMath');pigment_height.operation='ADD'
    l.new(lower.outputs['Result'],pigment_height.inputs[0]);l.new(pigment_warp.outputs[0],pigment_height.inputs[1])
    base.color_ramp.interpolation='B_SPLINE';l.new(pigment_height.outputs[0],base.inputs[0])
    variation=n.new('ShaderNodeMapRange');variation.inputs['To Min'].default_value=.85;variation.inputs['To Max'].default_value=1.05
    l.new(mottles.outputs['Fac'],variation.inputs['Value'])
    cloud=n.new('ShaderNodeMixRGB');cloud.blend_type='MULTIPLY';cloud.inputs[0].default_value=1
    l.new(base.outputs[0],cloud.inputs[1]);l.new(variation.outputs['Result'],cloud.inputs[2])
    l.new(cloud.outputs[0],mix.inputs[1]);l.new(mix.outputs[0],b.inputs['Base Color'])
    rr=n.new('ShaderNodeMapRange');rr.inputs['From Min'].default_value=.2;rr.inputs['From Max'].default_value=.8;rr.inputs['To Min'].default_value=.24;rr.inputs['To Max'].default_value=.35
    l.new(ns.outputs['Fac'],rr.inputs['Value']);l.new(rr.outputs['Result'],b.inputs['Roughness'])
    b.inputs['Coat Weight'].default_value=.80;b.inputs['Coat Roughness'].default_value=.11
    polish=n.new('ShaderNodeTexNoise');polish.inputs['Scale'].default_value=5200;polish.inputs['Detail'].default_value=2
    l.new(tx.outputs['Object'],polish.inputs['Vector'])
    micro=n.new('ShaderNodeBump');micro.inputs['Distance'].default_value=.000007;micro.inputs['Strength'].default_value=.13
    l.new(polish.outputs['Fac'],micro.inputs['Height']);l.new(micro.outputs['Normal'],b.inputs['Coat Normal'])

    well,n,l,b=_material('Eye | deeply shadowed inner opening wall',(.007,.009,.012),.29)
    return {'body':body,'well':well,'images':[veins]}


_BODY_PROFILE=[(0,.002),(.025,.002),(.041,.0042),(.052,.010),(.061,.020),
               (.067,.035),(.070,.052),(.0676,.066),(.0612,.078),
               (.053,.0865),(.046,.0901),(IRIS_RADIUS,.0918)]


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
    from iris_detail import build_iris_detail
    detail=build_iris_detail(collection,iris_surface,inner_radius=OPENING_RADIUS,outer_radius=IRIS_RADIUS)
    well=_well(collection,mats['well'])
    objects=[body,well]+detail['objects']
    return {'objects':objects,
            'body_width_m':BODY_RADIUS*2,'base_z_m':BASE_Z,
            'iris_outer_radius_m':IRIS_RADIUS,'iris_outer_edge_z_m':IRIS_EDGE_Z,
            'opening_radius_m':OPENING_RADIUS,'opening_edge_z_m':OPENING_Z,
            'food_interface':'Insert top supplied separately at .1055 m; clear roe surface .106 m',
            'packed_original_images':[im.name for im in mats['images']],
            'materials':mats,'mesh_vertices':sum(len(o.data.vertices) for o in objects if o.type=='MESH'),
            'iris_detail':{k:v for k,v in detail.items() if k!='objects'},
            'notes':'Resin vessel with actual layered iris fibers and embedded vascular pigment; verified physical scale applied by build script.'}
