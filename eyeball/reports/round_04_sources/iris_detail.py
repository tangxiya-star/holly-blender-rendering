"""Layered original blue iris, prepared for a transparent cast-resin vessel.

All geometry is in the legacy 140 mm coordinate system; the caller performs the
verified 200 mm scale change. No source photograph pixels are used as texture.
The public function accepts the parent scene's exact iris surface callback.
"""
import bpy
import math
import random
import numpy as np
from mathutils import Vector

TAU=math.tau
SEED=682409


def _mesh(name,verts,faces,collection,materials,indices=None,uv=None):
    mesh=bpy.data.meshes.new(name+' | explicit layered geometry')
    mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj)
    for m in materials:mesh.materials.append(m)
    for p in mesh.polygons:
        p.use_smooth=True
        if indices:p.material_index=indices[p.index]
    if uv:
        layer=mesh.uv_layers.new(name='OriginalPolarPigmentUV')
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                layer.data[li].uv=uv[mesh.loops[li].vertex_index]
    return obj


def _mat(name,color,roughness=.45,sss=0,scale=.0001):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    bs=nodes.get('Principled BSDF')
    bs.name='Physically layered iris pigment'
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=roughness
    bs.inputs['IOR'].default_value=1.43
    bs.inputs['Subsurface Weight'].default_value=sss
    bs.inputs['Subsurface Scale'].default_value=scale
    bs.inputs['Subsurface Radius'].default_value=(.65,.9,1)
    return mat,nodes,links,bs


def _periodic(u,count,seed):
    rng=np.random.default_rng(seed)
    values=rng.random(count).astype(np.float32)
    q=u*count;i=np.floor(q).astype(np.int32);t=q-i;t=t*t*(3-2*t)
    return values[i%count]*(1-t)+values[(i+1)%count]*t


def _crypts(inner,outer):
    rng=random.Random(SEED+9)
    result=[]
    for k in range(48):
        angle=rng.random()*TAU
        r=inner+(outer-inner)*rng.uniform(.07,.73)
        result.append((angle,r,rng.uniform(.00042,.00165),
                       rng.uniform(.00013,.00038),rng.uniform(.00010,.00036)))
    return result


def _pigment_image(inner,outer,crypts):
    width,height=3072,1024
    u=np.arange(width,dtype=np.float32)[None,:]/width
    v=np.linspace(0,1,height,dtype=np.float32)[:,None]
    a=u*TAU
    # Only a quiet fine density bed is painted. The prominent fiber bundles are
    # actual raised, branching ribbon meshes above this underlying pigment.
    bend=.00045*np.sin(v*12+1.8*np.sin(a*7))
    large=_periodic(u,49,301)
    medium=_periodic(u+bend,413,601)
    fine=_periodic(u-bend*.47,1009,707)
    phase=_periodic(u,317,208)*TAU
    gates=.23+.77*np.maximum(0,np.sin(v*(23+37*_periodic(u,181,416))+phase))
    density=np.clip((medium-.30)/.62,0,1)*gates*.62+fine*.38
    radial_pale=np.exp(-((v-.45)/.45)**2)
    pale=np.clip(.12+.36*density+.16*radial_pale+.08*large,0,.79)
    blue=np.array((.014,.174,.257),dtype=np.float32)
    ice=np.array((.270,.455,.465),dtype=np.float32)
    color=blue[None,None,:]*(1-pale[:,:,None])+ice[None,None,:]*pale[:,:,None]
    color*=.87+.23*large[:,:,None]
    # Irregular soft collarette: non-periodic fraying, never repeated gear teeth.
    edge=.064+.099*_periodic(u,37,730)+.027*_periodic(u,79,193)
    dark=np.clip((edge-v+.014)/.025,0,1)
    charcoal=np.array((.0028,.012,.018),dtype=np.float32)
    color=color*(1-dark[:,:,None]*.98)+charcoal[None,None,:]*(dark[:,:,None]*.98)
    radial=inner+(outer-inner)*v
    for angle,r,radial_size,tangent_size,depth in crypts:
        da=np.abs((a-angle+math.pi)%TAU-math.pi)
        hole=np.exp(-((radial-r)/radial_size)**2-(da*r/tangent_size)**2)
        color*=1-hole[:,:,None]*.76
    # Sparse slate-blue pigment marks, partly veiled by the fiber layer.
    rng=np.random.default_rng(520)
    for k in range(13):
        au=float(rng.random());tv=float(rng.uniform(.28,.88))
        da=np.abs((u-au+.5)%1-.5)
        patch=np.exp(-(da/.0026)**2-((v-tv)/.027)**2)
        color=color*(1-.28*patch[:,:,None])
    # The limbal transition is softly teal, not a separate black outline.
    edge_factor=np.clip((v-.956)/.044,0,1)
    color*=1-.26*edge_factor[:,:,None]
    rgba=np.ones((height,width,4),dtype=np.float32)
    rgba[:,:,:3]=np.clip(color,.001,.72)
    image=bpy.data.images.new('Blue iris | original short radial pigment density',
                              width=width,height=height,alpha=True,float_buffer=True)
    image.colorspace_settings.name='Non-Color'
    image.pixels.foreach_set(rgba.ravel());image.update();image.pack()
    image['provenance']='Generated original polar pigment and crypt field; no source photograph pixels'
    return image


def _materials(image):
    base,n,l,b=_mat('Blue iris | deep cyan pigment bed and recessed crypts',(.025,.18,.24),.52,.025,.00016)
    tex=n.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Cubic';tex.extension='REPEAT'
    l.new(tex.outputs['Color'],b.inputs['Base Color'])
    coords=n.new('ShaderNodeTexCoord');grain=n.new('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value=7800;grain.inputs['Detail'].default_value=2
    l.new(coords.outputs['Object'],grain.inputs['Vector'])
    bump=n.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.000008;bump.inputs['Strength'].default_value=.16
    l.new(grain.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],b.inputs['Normal'])
    fibers=[]
    for i,color in enumerate([(.225,.420,.435),(.350,.515,.505),(.165,.335,.380),
                             (.465,.565,.505),(.085,.255,.320),(.290,.445,.455),
                             (.070,.175,.207),(.004,.020,.029)]):
        m,n,l,b=_mat('Blue iris | stromal fiber pigment %02d'%i,color,.46,.055,.000065)
        fibers.append(m)
    resin,n,l,b=_mat('Eye iris | clear cast resin, shallow enclosing volume',(.995,.998,1),.083)
    b.inputs['IOR'].default_value=1.49
    b.inputs['Transmission Weight'].default_value=1
    b.inputs['Coat Weight'].default_value=0
    coord=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=115;noise.inputs['Detail'].default_value=2
    l.new(coord.outputs['Object'],noise.inputs['Vector'])
    rough=n.new('ShaderNodeMapRange');rough.clamp=True
    rough.inputs['From Min'].default_value=.20;rough.inputs['From Max'].default_value=.80
    rough.inputs['To Min'].default_value=.060;rough.inputs['To Max'].default_value=.105
    l.new(noise.outputs['Fac'],rough.inputs['Value']);l.new(rough.outputs['Result'],b.inputs['Roughness'])
    return base,fibers,resin


def _crypt_lookup(crypts):
    bins=[[] for _ in range(96)]
    for crypt in crypts:
        index=int(crypt[0]/TAU*96)%96
        for d in (-1,0,1):bins[(index+d)%96].append(crypt)
    return bins


def _depression(r,a,near):
    result=0
    for ca,cr,rs,ts,depth in near:
        dr=(r-cr)/rs
        if abs(dr)>2.7:continue
        da=abs((a-ca+math.pi)%TAU-math.pi)*r/ts
        if da>2.7:continue
        result+=depth*math.exp(-dr*dr-da*da)
    return result


def _bed(collection,surface,inner,outer,material,crypts):
    sectors,rings=1024,176
    bins=_crypt_lookup(crypts)
    verts=[];uv=[];faces=[]
    for j in range(rings+1):
        t=j/rings;r=inner+(outer-inner)*t
        for i in range(sectors+1):
            a=TAU*i/sectors
            depression=_depression(r,a,bins[int((a%TAU)/TAU*96)%96])
            # Preserve exact inner and outer interface positions.
            fade=min(1,t*30,(1-t)*30)
            z=surface(r,a)-(depression+.000025)*max(0,fade)
            verts.append((r*math.cos(a),r*math.sin(a),z));uv.append((i/sectors,t))
    for j in range(rings):
        for i in range(sectors):
            q=j*(sectors+1)+i
            faces.append((q+sectors+1,q+sectors+2,q+1,q))
    return _mesh('Blue iris | recessed layered stromal foundation',verts,faces,collection,[material],uv=uv)


def _append_ribbon(verts,faces,ids,surface,inner,outer,r0,r1,a0,drift,width,level,idx,phase):
    length=abs(r1-r0)
    steps=max(9,min(38,int(length/.00024)+1))
    offset=len(verts)
    for j in range(steps+1):
        s=j/steps
        r=r0+(r1-r0)*s
        # Short local curves and a gentle fork, not long sinusoidal spokes.
        lateral=drift*s + .000045*math.sin(s*4.2+phase)*math.sin(math.pi*s)
        a=a0+lateral/max(r,.01)
        envelope=math.sin(math.pi*s)**.55
        half=width*.5*envelope*(.82+.18*math.sin(s*7+phase))
        rim_fade=min(1,max(.04,(outer-r)/((outer-inner)*.04)))
        z=surface(r,a)+(level+.000044*math.sin(math.pi*s))*rim_fade
        across=Vector((-math.sin(a),math.cos(a),0))
        center=Vector((r*math.cos(a),r*math.sin(a),z))
        # A physical raised fiber cross section, not a zero-thickness color line.
        for side in (-1,0,1):
            point=center+across*(side*half)
            point.z+=(.000011*(1-abs(side))*envelope+.000009*side*math.sin(s*5+phase))*rim_fade
            verts.append(tuple(point))
    for j in range(steps):
        for k in range(2):
            q=offset+j*3+k
            faces.append((q,q+3,q+4,q+1));ids.append(idx)


def _fibers(collection,surface,inner,outer,materials):
    rng=random.Random(SEED+13)
    verts=[];faces=[];ids=[]
    count=0
    for k in range(2220):
        a=rng.random()*TAU
        r0=inner+(outer-inner)*rng.uniform(.025,.91)
        length=rng.uniform(.0011,.0078)
        r1=min(outer-.00016,r0+length)
        if r1-r0<.00055:continue
        drift=rng.uniform(-.00036,.00036)
        width=rng.uniform(.000044,.00012)
        if k%9==0:width*=rng.uniform(1.5,2.2)
        level=rng.uniform(.000035,.000205)
        idx=rng.choices(range(7),[3,4,3,2,2,3,1])[0]
        phase=rng.random()*TAU
        _append_ribbon(verts,faces,ids,surface,inner,outer,r0,r1,a,drift,width,level,idx,phase)
        count+=1
        if rng.random()<.44:
            start=r0+(r1-r0)*rng.uniform(.34,.72)
            end=min(outer-.00018,start+rng.uniform(.0008,.0035))
            branch_a=a+drift*.58/max(start,.01)
            side=rng.choice((-1,1))
            _append_ribbon(verts,faces,ids,surface,inner,outer,start,end,branch_a,
                           drift*.3+side*rng.uniform(.00013,.00048),width*.62,
                           level+.000008,idx,phase+1.2)
            count+=1
    # Interlaced oblique short links near the inner stroma break radial barcode.
    for k in range(330):
        a=rng.random()*TAU
        r0=inner+(outer-inner)*rng.uniform(.09,.70)
        r1=min(outer-.0002,r0+rng.uniform(.00042,.0020))
        _append_ribbon(verts,faces,ids,surface,inner,outer,r0,r1,a,
                       rng.choice((-1,1))*rng.uniform(.00028,.00091),
                       rng.uniform(.00004,.000105),rng.uniform(.00007,.00021),
                       rng.choice((0,1,2,5)),rng.random()*TAU)
        count+=1
    # Fraying around the dark pupil border is uneven and locally absent.
    for k in range(255):
        a=rng.random()*TAU
        if math.sin(a*3+.5)+math.sin(a*7-1.1)<-.95:continue
        r0=inner+rng.uniform(.00005,.0016)
        r1=r0+rng.uniform(.0003,.0026)
        _append_ribbon(verts,faces,ids,surface,inner,outer,r0,r1,a,
                       rng.uniform(-.00018,.00018),rng.uniform(.000065,.00021),
                       rng.uniform(.000015,.000090),7,rng.random()*TAU)
        count+=1
    obj=_mesh('Blue iris | actual overlapping branching fiber ribbons',verts,faces,collection,materials,ids)
    obj['individual_short_fibers']=count
    obj['vertical_layers_legacy_m']=[.000015,.000270]
    return obj,count


def _resin(collection,surface,inner,outer,material):
    sectors,rings=768,112
    verts=[];faces=[]
    stride=sectors
    for layer in (0,1):
        for j in range(rings+1):
            t=j/rings;r=inner+(outer-inner)*t
            # Bulk resin over the relief, tapering gently into the outer surface.
            taper=min(1,max(.08,(1-t)/.035))
            offset=(-.000035 if layer==0 else .000345*taper)
            for i in range(sectors):
                a=TAU*i/sectors
                verts.append((r*math.cos(a),r*math.sin(a),surface(r,a)+offset))
    per=(rings+1)*stride
    for layer in (0,1):
        base=layer*per
        for j in range(rings):
            for i in range(sectors):
                q=base+j*stride+i
                nxt=base+j*stride+(i+1)%sectors
                face=(q+stride,nxt+stride,nxt,q)
                faces.append(face if layer==1 else tuple(reversed(face)))
    # Close both circular walls. The seam vertices share positions consistently.
    for i in range(sectors):
        nxt=(i+1)%sectors
        faces.append((i,per+i,per+nxt,nxt))
        q=rings*stride+i
        outer_next=rings*stride+nxt
        faces.append((q,outer_next,per+outer_next,per+q))
    obj=_mesh('Eye iris | shallow closed clear cast-resin encasement',verts,faces,collection,[material])
    obj['IOR']=1.49
    obj['bulk_thickness_legacy_m']=.00038
    obj['purpose']='Encases real fiber relief; not an enlarged glass dome'
    return obj


def build_iris_detail(collection,surface_fn,inner_radius=.0158,outer_radius=.0405):
    """Build the complete iris assembly, including its transparent resin finish.

    surface_fn(r,angle) returns the parent vessel's Z value in legacy meters.
    Do not add the old iris or thin clear film in addition to this assembly.
    """
    if not callable(surface_fn):raise TypeError('surface_fn must be callable')
    if not 0<inner_radius<outer_radius:raise ValueError('Invalid iris radii')
    crypts=_crypts(inner_radius,outer_radius)
    image=_pigment_image(inner_radius,outer_radius,crypts)
    base_material,fiber_materials,resin_material=_materials(image)
    bed=_bed(collection,surface_fn,inner_radius,outer_radius,base_material,crypts)
    fibers,count=_fibers(collection,surface_fn,inner_radius,outer_radius,fiber_materials)
    resin=_resin(collection,surface_fn,inner_radius,outer_radius,resin_material)
    objects=[bed,fibers,resin]
    return {'objects':objects,'inner_radius_m':inner_radius,'outer_radius_m':outer_radius,
            'inner_surface_z_m':float(surface_fn(inner_radius,0)),
            'outer_surface_z_m':float(surface_fn(outer_radius,0)),
            'fiber_ribbons':count,'recessed_crypts':len(crypts),'packed_image':image.name,
            'materials':[m.name for m in [base_material]+fiber_materials+[resin_material]],
            'vertices':sum(len(o.data.vertices) for o in objects),
            'faces':sum(len(o.data.polygons) for o in objects),
            'resin_ior':1.49,'resin_bulk_thickness_legacy_m':.00038,
            'legacy_scale':'Caller scales complete assembly 10/7 with the rest of the vessel',
            'notes':'Original cyan stroma, actual branching layered fibers and recessed crypts under closed resin; no source-image mapping.'}
