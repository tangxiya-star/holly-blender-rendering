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
    m,ns,ls,b=_material('Eye food | dark flexible insert edge',(.006,.0031,.0021),.34)
    b.inputs['IOR'].default_value=1.43
    b.inputs['Coat Weight'].default_value=.11;b.inputs['Coat Roughness'].default_value=.22
    tc=ns.new('ShaderNodeTexCoord');n=_noise(ns,ls,tc.outputs['Object'],3100,3)
    rr=_ramp(ns,ls,n.outputs['Fac'],(.25,)*3,(.43,)*3)
    ls.new(rr.outputs['Color'],b.inputs['Roughness'])
    bp=ns.new('ShaderNodeBump');bp.inputs['Distance'].default_value=.000014;bp.inputs['Strength'].default_value=.18
    ls.new(n.outputs['Fac'],bp.inputs['Height']);ls.new(bp.outputs['Normal'],b.inputs['Normal'])
    wall=m

    m,ns,ls,b=_material('Eye food | dark viscous liquid and local menisci',(.003,.0011,.00065),.37)
    b.inputs['IOR'].default_value=1.33;b.inputs['Transmission Weight'].default_value=.04
    b.inputs['Coat Weight'].default_value=.025;b.inputs['Coat Roughness'].default_value=.29
    tc=ns.new('ShaderNodeTexCoord');n=_noise(ns,ls,tc.outputs['Object'],950,3)
    rr=_ramp(ns,ls,n.outputs['Fac'],(.30,)*3,(.43,)*3)
    ls.new(rr.outputs['Color'],b.inputs['Roughness'])
    cr=_ramp(ns,ls,n.outputs['Fac'],(.0015,.0008,.00045),(.0055,.0023,.0013))
    ls.new(cr.outputs['Color'],b.inputs['Base Color'])
    gel=m

    roe=[]
    palette=[(.017,.0073,.0043),(.026,.0118,.0067),(.038,.0188,.010),
             (.0095,.0048,.0034),(.023,.013,.0087),(.049,.025,.014)]
    for i,c in enumerate(palette):
        m,ns,ls,b=_material('Eye food | amber roe membrane %02d'%i,c,.34)
        b.inputs['IOR'].default_value=1.37
        b.inputs['Subsurface Weight'].default_value=.065
        b.inputs['Subsurface Radius'].default_value=(1,.48,.19)
        b.inputs['Subsurface Scale'].default_value=.00028
        b.inputs['Transmission Weight'].default_value=.085
        b.inputs['Coat Weight'].default_value=.045
        b.inputs['Coat Roughness'].default_value=.22
        tc=ns.new('ShaderNodeTexCoord');n=_noise(ns,ls,tc.outputs['Object'],2350,3)
        cr=_ramp(ns,ls,n.outputs['Fac'],tuple(v*.71 for v in c),tuple(v*1.22 for v in c))
        ls.new(cr.outputs['Color'],b.inputs['Base Color'])
        rr=_ramp(ns,ls,n.outputs['Fac'],(.255,)*3,(.42,)*3)
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
             (.01531,.10465),(.01529,.10505),(.01518,.10523),
             (.01496,.10527),(.01482,.1051),(.01475,.10495),(.01472,.10225)]
    for j,(radius,z) in enumerate(profile):
        for i in range(segments):
            a=TAU*i/segments
            irregular=.00010*math.sin(a*3+.5)+.000065*noise(Vector((math.cos(a)*7,math.sin(a)*7,4)))
            hvar=.000055*math.sin(a*5+.3)+.000026*math.sin(a*11)
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
    # Crowded sequential packing; shape and immersion vary rather than forming a
    # repeated array of polished, isolated beads. Projected cap coverage ~82%.
    for attempt in range(65000):
        if len(particles)>=198:break
        radius=rng.uniform(.00092,.00132)
        if rng.random()<.11:radius*=.81
        rad=(FOOD_RADIUS-radius*.84)*math.sqrt(rng.random());a=rng.uniform(0,TAU)
        x=rad*math.cos(a);y=rad*math.sin(a)
        if any((x-p[0])**2+(y-p[1])**2 < ((radius+p[2])*.75)**2 for p in particles):continue
        particles.append((x,y,radius))
    return particles


def _roe(collection,materials,gel):
    rng=random.Random(18731);particles=_packing()
    verts=[];faces=[];indices=[];menv=[];menf=[]
    nlon=26;nlat=17
    for pindex,(x,y,radius) in enumerate(particles):
        seed=rng.uniform(1,100);angle=rng.uniform(0,TAU)
        ellipse=rng.uniform(.86,1.12);zscale=rng.uniform(.68,.93)
        immersion=rng.uniform(.12,.34)
        base=_fluid_height(x,y)
        cz=base-radius*zscale*immersion
        index=rng.choices(range(6),[5,5,3,5,3,1])[0]
        start=len(verts)
        for j in range(nlat+1):
            phi=math.pi*j/nlat
            for k in range(nlon):
                theta=TAU*k/nlon
                direction=Vector((math.sin(phi)*math.cos(theta),math.sin(phi)*math.sin(theta),math.cos(phi)))
                asym=1+.093*noise(direction*2.7+Vector((seed,4,6)))+.024*noise(direction*8.1+Vector((3,seed,9)))
                rx=radius*ellipse*direction.x*asym
                ry=radius/ellipse*direction.y*asym
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

        # Very low meniscus, tapering back into liquid. Visibility is interrupted
        # by neighbours and by the particle itself, so it does not form bright rings.
        offset=len(menv);count=28
        contact=math.sqrt(1-immersion*immersion)
        for j,(extension,rise) in enumerate([(0,.000035),(.000085,.000013),(.00016,-.000008)]):
            for k in range(count):
                a=TAU*k/count
                rr=radius*contact+extension
                xx=rr*ellipse*math.cos(a);yy=rr/ellipse*math.sin(a)
                px=x+xx*math.cos(angle)-yy*math.sin(angle)
                py=y+xx*math.sin(angle)+yy*math.cos(angle)
                uneven=.55+.45*math.sin(a*3+seed)**2
                menv.append((px,py,_fluid_height(px,py)+rise*uneven))
        for j in range(2):
            for k in range(count):
                a=offset+j*count+k;b=offset+j*count+(k+1)%count
                menf.append((a,a+count,b+count,b))
    obj=_mesh('Eye food | partly immersed deformed amber roe',verts,faces,collection,materials,indices)
    obj['particle_count']=len(particles)
    obj['visible_geometry']='Unequal custom lobed closed grains; crowded wet caps with 12–34 percent radial immersion and nonuniform cap height.'
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
