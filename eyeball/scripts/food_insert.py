"""Visible food in the eye's pupil, reconstructed at photographic scale.

Original custom geometry and Principled shaders; no photographed pixels are used
as texture. The supplied photograph does not resolve the buried recipe layers.
Call build_food_insert(collection). Coordinates are metres, Z up.
"""
import bpy
import math
import random
from mathutils import Vector
from mathutils.noise import noise

TAU=2*math.pi
RIM_RADIUS=.0153
FOOD_RADIUS=.01463


def _mesh(name,vertices,faces,collection,materials,indices=None):
    mesh=bpy.data.meshes.new(name+' mesh')
    mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj)
    for mat in materials:mesh.materials.append(mat)
    for i,p in enumerate(mesh.polygons):
        p.use_smooth=True
        if indices is not None:p.material_index=indices[i]
    return obj


def _material(name,color,roughness):
    m=bpy.data.materials.new(name);m.use_nodes=True
    ns=m.node_tree.nodes;ls=m.node_tree.links;b=ns.get('Principled BSDF')
    b.inputs['Base Color'].default_value=(*color,1)
    b.inputs['Roughness'].default_value=roughness
    return m,ns,ls,b


def _noise(ns,ls,vector,scale,detail=2):
    n=ns.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=scale
    n.inputs['Detail'].default_value=detail;n.inputs['Roughness'].default_value=.67
    ls.new(vector,n.inputs['Vector']);return n


def _ramp(ns,ls,socket,lo,hi,start=.2,end=.8):
    r=ns.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=start
    r.color_ramp.elements[0].color=(*lo,1);r.color_ramp.elements[1].position=end
    r.color_ramp.elements[1].color=(*hi,1);ls.new(socket,r.inputs['Fac']);return r


def _materials():
    m,ns,ls,b=_material('Eye food | dark flexible insert edge',(.0038,.0021,.0015),.40)
    b.inputs['IOR'].default_value=1.43
    b.inputs['Coat Weight'].default_value=.025;b.inputs['Coat Roughness'].default_value=.31
    tc=ns.new('ShaderNodeTexCoord');n=_noise(ns,ls,tc.outputs['Object'],3100,3)
    rr=_ramp(ns,ls,n.outputs['Fac'],(.33,)*3,(.49,)*3)
    ls.new(rr.outputs['Color'],b.inputs['Roughness'])
    bp=ns.new('ShaderNodeBump');bp.inputs['Distance'].default_value=.000014;bp.inputs['Strength'].default_value=.18
    ls.new(n.outputs['Fac'],bp.inputs['Height']);ls.new(bp.outputs['Normal'],b.inputs['Normal'])
    wall=m

    m,ns,ls,b=_material('Eye food | dark viscous liquid and local menisci',(.0018,.0008,.00045),.31)
    b.inputs['IOR'].default_value=1.33;b.inputs['Transmission Weight'].default_value=.025
    b.inputs['Specular IOR Level'].default_value=.32
    b.inputs['Coat Weight'].default_value=.015;b.inputs['Coat Roughness'].default_value=.27
    tc=ns.new('ShaderNodeTexCoord');n=_noise(ns,ls,tc.outputs['Object'],950,3)
    rr=_ramp(ns,ls,n.outputs['Fac'],(.25,)*3,(.38,)*3)
    ls.new(rr.outputs['Color'],b.inputs['Roughness'])
    cr=_ramp(ns,ls,n.outputs['Fac'],(.0008,.0004,.00022),(.0032,.0014,.0007))
    ls.new(cr.outputs['Color'],b.inputs['Base Color'])
    gel=m

    roe=[]
    palette=[(.013,.0068,.0025),(.022,.012,.0042),(.031,.016,.0055),
             (.0045,.0027,.0011),(.016,.009,.0032),(.027,.013,.0048)]
    for i,c in enumerate(palette):
        m,ns,ls,b=_material('Eye food | amber roe membrane %02d'%i,c,.44)
        b.inputs['IOR'].default_value=1.34
        b.inputs['Metallic'].default_value=0
        b.inputs['Specular IOR Level'].default_value=.42 if i==5 else (.14 if i==3 else .23)
        b.inputs['Subsurface Weight'].default_value=.065
        b.inputs['Subsurface Radius'].default_value=(1,.48,.19)
        b.inputs['Subsurface Scale'].default_value=.00028
        b.inputs['Transmission Weight'].default_value=.035
        # Only a small minority of grains has a clean exposed wet membrane.
        # The majority reads through turbid gel and has a softer reflection.
        b.inputs['Coat Weight'].default_value=.045 if i==5 else .006
        b.inputs['Coat Roughness'].default_value=.18 if i==5 else .37
        tc=ns.new('ShaderNodeTexCoord');n=_noise(ns,ls,tc.outputs['Object'],2350,3)
        cr=_ramp(ns,ls,n.outputs['Fac'],tuple(v*.78 for v in c),tuple(v*1.12 for v in c))
        patch=_noise(ns,ls,tc.outputs['Object'],205,2)
        patch_color=_ramp(ns,ls,patch.outputs['Fac'],(.30,.40,.20),(1.20,1.16,.85),.26,.74)
        mix=ns.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
        ls.new(cr.outputs['Color'],mix.inputs[1]);ls.new(patch_color.outputs['Color'],mix.inputs[2])
        ls.new(mix.outputs['Color'],b.inputs['Base Color'])
        lo,hi=(.18,.27) if i==5 else ((.44,.55) if i==3 else (.32,.46))
        rr=_ramp(ns,ls,n.outputs['Fac'],(lo,)*3,(hi,)*3)
        ls.new(rr.outputs['Color'],b.inputs['Roughness'])
        micro=_noise(ns,ls,tc.outputs['Object'],10000,2)
        bp=ns.new('ShaderNodeBump');bp.inputs['Distance'].default_value=.000005
        bp.inputs['Strength'].default_value=.13
        ls.new(micro.outputs['Fac'],bp.inputs['Height']);ls.new(bp.outputs['Normal'],b.inputs['Normal'])
        roe.append(m)
    return wall,gel,roe


def _wall(collection,material):
    verts=[];faces=[];segments=208
    # Softened thin edge has measurable wall thickness, without a separate CG ring.
    profile=[(.01455,.1020),(.0151,.1020),(.0153,.10225),
             (.01527,.10465),(.01514,.10505),(.01504,.10523),
             (.01491,.10527),(.01484,.1051),(.01475,.10495),(.01472,.10225)]
    for j,(radius,z) in enumerate(profile):
        for i in range(segments):
            a=TAU*i/segments
            irregular=.00010*math.sin(a*3+.5)+.00012*noise(Vector((math.cos(a)*7,math.sin(a)*7,4)))
            hvar=.00008*math.sin(a*5+.3)+.00007*noise(Vector((math.cos(a)*12,math.sin(a)*12,8)))
            verts.append(((radius+irregular)*math.cos(a),(radius+irregular)*math.sin(a),z+hvar))
    for j in range(len(profile)):
        nxt=(j+1)%len(profile)
        for i in range(segments):
            a=j*segments+i;b=j*segments+(i+1)%segments
            faces.append((a,b,nxt*segments+(i+1)%segments,nxt*segments+i))
    obj=_mesh('Eye food | irregular low insert wall',verts,faces,collection,[material])
    obj['visible_wall_height_m']=.0032
    return obj


def _fluid_height(x,y):
    r=math.sqrt(x*x+y*y)/FOOD_RADIUS
    return .10546+.00013*r*r+.000075*noise(Vector((x*240,y*240,11)))


def _fluid(collection,material):
    verts=[(0,0,_fluid_height(0,0))];faces=[]
    radial=42;segments=192
    for j in range(1,radial+1):
        r=FOOD_RADIUS*j/radial
        for k in range(segments):
            a=TAU*k/segments;x=r*math.cos(a);y=r*math.sin(a)
            verts.append((x,y,_fluid_height(x,y)))
    for k in range(segments):faces.append((0,1+k,1+(k+1)%segments))
    for j in range(radial-1):
        start=1+j*segments
        for k in range(segments):
            a=start+k;b=start+(k+1)%segments
            faces.append((a,a+segments,b+segments,b))
    # Closed opaque bottom gives transmission a physical backing and volume.
    lower=len(verts);verts.append((0,0,.1037))
    start=1+(radial-1)*segments
    for k in range(segments):faces.append((lower,start+(k+1)%segments,start+k))
    return _mesh('Eye food | shallow dark immersed surface',verts,faces,collection,[material])


def _packing():
    rng=random.Random(184209);particles=[]
    # Fewer larger grains, with room for a continuous dark liquid interface.
    # Slightly overlapping buried bodies do not inflate the exposed cap footprint.
    for attempt in range(65000):
        if len(particles)>=124:break
        radius=rng.uniform(.00120,.00165)
        if rng.random()<.08:radius*=.88
        rad=(FOOD_RADIUS-radius*1.13-.00010)*math.sqrt(rng.random());a=rng.uniform(0,TAU)
        x=rad*math.cos(a);y=rad*math.sin(a)
        if any((x-p[0])**2+(y-p[1])**2 < ((radius+p[2])*.76)**2 for p in particles):continue
        particles.append((x,y,radius))
    return particles


def _roe(collection,materials,gel):
    rng=random.Random(18731);particles=_packing()
    verts=[];faces=[];indices=[];menv=[];menf=[]
    nlon=26;nlat=17
    for pindex,(x,y,radius) in enumerate(particles):
        seed=rng.uniform(1,100);angle=rng.uniform(0,TAU)
        ellipse=rng.uniform(.93,1.075)
        region=max(0,min(1,.5+.85*noise(Vector((x*190,y*190,17)))))
        zscale=rng.uniform(.84,1.03)
        immersion=max(.24,min(.72,.30+.35*region+rng.uniform(-.12,.12)))
        # True rounded bodies emerge as differently sized curved caps; no XY
        # compensation, which previously made every buried grain a broad disk.
        contact_scale=1.0
        base=_fluid_height(x,y)
        cz=base-radius*zscale*immersion
        weights=[5,5,3,6,4,.7] if region<.62 else [4,3,2,13,5,.2]
        index=rng.choices(range(6),weights)[0]
        start=len(verts)
        for j in range(nlat+1):
            phi=math.pi*j/nlat
            for k in range(nlon):
                theta=TAU*k/nlon
                direction=Vector((math.sin(phi)*math.cos(theta),math.sin(phi)*math.sin(theta),math.cos(phi)))
                asym=1+.055*noise(direction*2.7+Vector((seed,4,6)))+.014*noise(direction*8.1+Vector((3,seed,9)))
                rx=radius*ellipse*direction.x*asym*contact_scale
                ry=radius/ellipse*direction.y*asym*contact_scale
                rz=radius*zscale*direction.z*asym
                # A small side-to-side shear prevents repeated polished bead profiles.
                rx+=radius*.045*direction.z*direction.z*math.sin(seed)
                px=x+rx*math.cos(angle)-ry*math.sin(angle)
                py=y+rx*math.sin(angle)+ry*math.cos(angle)
                verts.append((px,py,cz+rz))
        for j in range(nlat):
            for k in range(nlon):
                a=start+j*nlon+k;b=start+j*nlon+(k+1)%nlon
                faces.append((a,a+nlon,b+nlon,b));indices.append(index)

        # Broken, near-flat menisci remain part of the same liquid pool; do not
        # outline every grain with a complete reflective ring.
        offset=len(menv);count=28
        contact=math.sqrt(1-immersion*immersion)
        for j,(extension,rise) in enumerate([(0,.000018),(.000065,.000007),(.00012,-.000009)]):
            for k in range(count):
                a=TAU*k/count
                rr=radius*contact*contact_scale+extension
                xx=rr*ellipse*math.cos(a);yy=rr/ellipse*math.sin(a)
                px=x+xx*math.cos(angle)-yy*math.sin(angle)
                py=y+xx*math.sin(angle)+yy*math.cos(angle)
                uneven=.55+.45*math.sin(a*3+seed)**2
                menv.append((px,py,_fluid_height(px,py)+rise*uneven))
        for j in range(2):
            for k in range(count):
                if math.sin(TAU*k/count*2+seed)<.1:continue
                a=offset+j*count+k;b=offset+j*count+(k+1)%count
                menf.append((a,a+count,b+count,b))
    obj=_mesh('Eye food | partly immersed deformed amber roe',verts,faces,collection,materials,indices)
    obj['particle_count']=len(particles)
    obj['visible_geometry']='Rounded 2.4–3.3 mm ellipsoidal grains, regionally varying 24–72 percent radial immersion, continuous dark liquid between caps, and sparse clean wet membrane highlights.'
    _mesh('Eye food | thin local liquid contact menisci',menv,menf,collection,[gel])
    return obj


def build_food_insert(collection):
    wall,gel,roe=_materials()
    _wall(collection,wall);_fluid(collection,gel);grains=_roe(collection,roe,gel)
    objects=[o for o in collection.objects if o.name.startswith('Eye food |')]
    return {'objects':len(objects),'roe_grains':grains['particle_count'],
            'vertices':sum(len(o.data.vertices) for o in objects),
            'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects),
            'insert_outer_radius_m':RIM_RADIUS,'insert_top_z_m':.10527,
            'food_surface_z_m':.10546,
            'interpretation':'Only exposed dark roe and moist interfaces reconstructed. Buried asparagus cream/fish layers are not visibly resolved by the photograph.'}
