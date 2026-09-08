"""Photographic dish support: ceramic, moss, lichen branch and slate.

All geometry is original and expressed in metres. The photograph is an observation
reference, never an image plane or a material. Call build_support(collection).
"""
import bpy
import math
import random
from mathutils import Vector
from mathutils.noise import noise

TAU = 2.0 * math.pi


def _mesh(name, verts, faces, collection, materials=(), indices=None, uv=None):
    mesh = bpy.data.meshes.new(name + ' mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    for mat in materials:
        mesh.materials.append(mat)
    for i, poly in enumerate(mesh.polygons):
        poly.use_smooth = True
        if indices:
            poly.material_index = indices[i]
    if uv:
        layer = mesh.uv_layers.new(name='SurfaceUV')
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                layer.data[li].uv = uv[mesh.loops[li].vertex_index]
    return obj


def _mat(name, color, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    return mat, nodes, mat.node_tree.links, bsdf


def _noise(nodes, links, scale, detail=3, rough=.65, vector=None):
    n = nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    if vector is not None:
        links.new(vector, n.inputs['Vector'])
    return n


def _ramp(nodes, links, source, colors, positions=None):
    n = nodes.new('ShaderNodeValToRGB')
    r = n.color_ramp
    while len(r.elements) > 2:
        r.elements.remove(r.elements[-1])
    if positions is None:
        positions = [i/(len(colors)-1) for i in range(len(colors))]
    for i, color in enumerate(colors):
        elem = r.elements[i] if i < 2 else r.elements.new(positions[i])
        elem.position = positions[i]
        elem.color = (*color, 1)
    links.new(source, n.inputs['Fac'])
    return n


def _bump(nodes, links, height, bsdf, distance, strength=.2):
    b = nodes.new('ShaderNodeBump')
    b.inputs['Distance'].default_value = distance
    b.inputs['Strength'].default_value = strength
    links.new(height, b.inputs['Height'])
    links.new(b.outputs['Normal'], bsdf.inputs['Normal'])
    return b


def _materials():
    mats = {}
    m,n,l,b = _mat('Dish | warm porcelain and a thin clear glaze', (.71,.69,.65), .22)
    b.inputs['IOR'].default_value = 1.49
    b.inputs['Coat Weight'].default_value = .24
    b.inputs['Coat Roughness'].default_value = .13
    tex = n.new('ShaderNodeTexCoord')
    ns = _noise(n,l,2700,2,vector=tex.outputs['Object'])
    _bump(n,l,ns.outputs['Fac'],b,.000012,.16)
    nr = _noise(n,l,300,2,vector=tex.outputs['Object'])
    r = _ramp(n,l,nr.outputs['Fac'],[(.19,)*3,(.28,)*3])
    l.new(r.outputs['Color'],b.inputs['Roughness'])
    mats['porcelain'] = m

    greens = [(.025,.085,.0018),(.047,.12,.003),(.017,.047,.0008),
              (.06,.14,.005),(.023,.067,.002),(.038,.11,.003)]
    mats['moss'] = []
    for i,c in enumerate(greens):
        m,n,l,b = _mat('Moss | chlorophyll leaf variation %02d'%i,c,.34)
        b.inputs['Subsurface Weight'].default_value = .065
        b.inputs['Subsurface Radius'].default_value = (.45,1,.2)
        b.inputs['Subsurface Scale'].default_value = .00035
        b.inputs['Transmission Weight'].default_value = .1
        b.inputs['IOR'].default_value = 1.38
        b.inputs['Coat Weight'].default_value = .2
        b.inputs['Coat Roughness'].default_value = .19
        tex = n.new('ShaderNodeTexCoord')
        no = _noise(n,l,1700,2,vector=tex.outputs['Object'])
        ramp = _ramp(n,l,no.outputs['Fac'],[tuple(x*.47 for x in c),tuple(x*1.4 for x in c)])
        l.new(ramp.outputs['Color'],b.inputs['Base Color'])
        rr = _ramp(n,l,no.outputs['Fac'],[(.24,)*3,(.48,)*3])
        l.new(rr.outputs['Color'],b.inputs['Roughness'])
        _bump(n,l,no.outputs['Fac'],b,.000027,.25)
        mats['moss'].append(m)
    m,n,l,b = _mat('Moss | dark interstitial substrate',(.006,.022,.001),.7)
    tex=n.new('ShaderNodeTexCoord')
    ns = _noise(n,l,1400,5,vector=tex.outputs['Object'])
    _bump(n,l,ns.outputs['Fac'],b,.0007,.6)
    mats['substrate'] = m

    m,n,l,b = _mat('Branch | weathered fissured bark',(.026,.011,.004),.82)
    tex = n.new('ShaderNodeTexCoord')
    mapping = n.new('ShaderNodeVectorMath'); mapping.operation = 'MULTIPLY'
    mapping.inputs[1].default_value = (15,3,8)
    l.new(tex.outputs['Generated'],mapping.inputs[0])
    ns = _noise(n,l,6,6,vector=mapping.outputs['Vector'])
    ramp = _ramp(n,l,ns.outputs['Fac'],[(.0035,.0017,.0008),(.03,.012,.003),(.068,.033,.01)],[.23,.48,.77])
    l.new(ramp.outputs['Color'],b.inputs['Base Color'])
    _bump(n,l,ns.outputs['Fac'],b,.0008,.66)
    mats['bark'] = m

    m,n,l,b = _mat('Branch | aged warm cut wood with uneven growth rings',(.09,.033,.009),.57)
    tex = n.new('ShaderNodeTexCoord'); sep=n.new('ShaderNodeSeparateXYZ')
    l.new(tex.outputs['UV'],sep.inputs[0])
    ns = _noise(n,l,12,4,vector=tex.outputs['UV'])
    mul = n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=.06
    l.new(ns.outputs['Fac'],mul.inputs[0])
    add = n.new('ShaderNodeMath');add.operation='ADD'
    l.new(sep.outputs['Y'],add.inputs[0]);l.new(mul.outputs[0],add.inputs[1])
    freq=n.new('ShaderNodeMath');freq.operation='MULTIPLY';freq.inputs[1].default_value=92
    l.new(add.outputs[0],freq.inputs[0])
    sine=n.new('ShaderNodeMath');sine.operation='SINE';l.new(freq.outputs[0],sine.inputs[0])
    ramp = _ramp(n,l,sine.outputs[0],[(.075,.028,.012),(.092,.037,.016)],[.12,.7])
    l.new(ramp.outputs['Color'],b.inputs['Base Color'])
    grain = _noise(n,l,1900,2,vector=tex.outputs['Object'])
    _bump(n,l,grain.outputs['Fac'],b,.000045,.42)
    mats['wood'] = m

    mats['lichen'] = []
    for i,c in enumerate([(.32,.255,.012),(.42,.30,.008),(.19,.18,.004),(.47,.34,.017)]):
        m,n,l,b = _mat('Lichen | ochre foliose crust %02d'%i,c,.88)
        b.inputs['Subsurface Weight'].default_value = .035
        b.inputs['Subsurface Scale'].default_value = .00012
        tex=n.new('ShaderNodeTexCoord')
        ns=_noise(n,l,3100,3,vector=tex.outputs['Object'])
        ramp=_ramp(n,l,ns.outputs['Fac'],[tuple(v*.6 for v in c),tuple(v*1.15 for v in c)])
        l.new(ramp.outputs['Color'],b.inputs['Base Color'])
        _bump(n,l,ns.outputs['Fac'],b,.00006,.44)
        mats['lichen'].append(m)

    m,n,l,b = _mat('Slate | graphite stone, shallow pores and mineral clefts',(.045,.044,.043),.74)
    tex=n.new('ShaderNodeTexCoord')
    low=_noise(n,l,31,5,vector=tex.outputs['Object'])
    fine=_noise(n,l,2300,4,vector=tex.outputs['Object'])
    mid=_noise(n,l,430,6,vector=tex.outputs['Object'])
    ramp=_ramp(n,l,low.outputs['Fac'],[(.018,.02,.023),(.045,.047,.052),(.073,.077,.082)],[.14,.51,.84])
    l.new(ramp.outputs['Color'],b.inputs['Base Color'])
    # Weathered stone is platey and pitted: no regular Voronoi pavement polygons.
    eroded=_ramp(n,l,mid.outputs['Fac'],[(.05,)*3,(.20,)*3,(.76,)*3,(.8,)*3], [.34,.47,.54,.73])
    broad=_noise(n,l,75,5,vector=tex.outputs['Object'])
    worn=_ramp(n,l,broad.outputs['Fac'],[(.3,)*3,(.9,)*3],[.32,.65])
    comb=n.new('ShaderNodeMath');comb.operation='MULTIPLY'
    l.new(eroded.outputs['Color'],comb.inputs[0]);l.new(worn.outputs['Color'],comb.inputs[1])
    bump=_bump(n,l,comb.outputs[0],b,.00085,.83)
    micro=n.new('ShaderNodeBump');micro.inputs['Distance'].default_value=.00009;micro.inputs['Strength'].default_value=.45
    l.new(fine.outputs['Fac'],micro.inputs['Height']);l.new(bump.outputs['Normal'],micro.inputs['Normal']);l.new(micro.outputs['Normal'],b.inputs['Normal'])
    rough=_ramp(n,l,mid.outputs['Fac'],[(.36,)*3,(.76,)*3],[.32,.62]);l.new(rough.outputs['Color'],b.inputs['Roughness'])
    mats['slate']=m
    return mats


def _plate(col, mats):
    # Radial cross-section runs from bottom centre around rounded foot/rim to bowl.
    controls=[(0,.0027),(.060,.0027),(.067,.0025),(.069,.0007),(.073,.0007),
              (.077,.0017),(.080,.003),(.0823,.0051),(.0838,.0082),(.0846,.0115),
              (.085,.0145),(.0848,.016),(.084,.0168),(.0828,.0169),
              (.0815,.0163),(.0807,.0148),(.078,.012),(.072,.010),
              (.056,.0085),(.028,.00825),(0,.00825)]
    profile=[]
    for j in range(len(controls)-1):
        p0=Vector(controls[max(0,j-1)]);p1=Vector(controls[j]);p2=Vector(controls[j+1]);p3=Vector(controls[min(len(controls)-1,j+2)])
        for k in range(6):
            t=k/6
            p=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
            profile.append((max(0,p.x),p.y))
    profile.append(controls[-1])
    v=[];f=[];segments=320
    for j,(radius,z) in enumerate(profile):
        for k in range(segments):
            a=TAU*k/segments
            asym=1+.003*math.sin(3*a+.8)+.0015*math.sin(7*a)
            dz=(.000075*math.sin(4*a+.5)+.00005*math.sin(9*a))*min(1,radius/.07)
            v.append((radius*math.cos(a)*asym,radius*math.sin(a)*asym,z+dz))
    for j in range(len(profile)-1):
        for k in range(segments):
            a=j*segments+k;bb=j*segments+(k+1)%segments
            f.append((a,bb,bb+segments,a+segments))
    return _mesh('Support | handmade porcelain bowl',v,f,col,[mats['porcelain']])


def _moss(col, mats):
    rng=random.Random(43761)
    # Low organic undergrowth beneath individual twigs; hidden by most of carpet.
    v=[(0,0,.018)];f=[];seg=240;rings=56
    for j in range(1,rings+1):
        rad=.078*j/rings
        for k in range(seg):
            a=TAU*k/seg
            x=rad*math.cos(a);y=rad*math.sin(a)
            z=.018+.0014*noise(Vector((x*170,y*170,3)))+.0007*noise(Vector((x*630,y*630,7)))
            v.append((x,y,z))
    for k in range(seg):f.append((0,1+k,1+(k+1)%seg))
    for j in range(rings-1):
        start=1+j*seg
        for k in range(seg):
            a=start+k;b=start+(k+1)%seg;f.append((a,b,b+seg,a+seg))
    _mesh('Support | moss bed shadow substrate',v,f,col,[mats['substrate']])
    v=[];f=[];mi=[]

    def tube(points,radius,idx):
        start=len(v); sides=5
        for j,p in enumerate(points):
            direction=points[min(len(points)-1,j+1)]-points[max(0,j-1)]
            direction.normalize();side=direction.cross(Vector((0,1,0))).normalized();up=direction.cross(side).normalized()
            rr=radius*(1-.65*j/(len(points)-1))
            for k in range(sides):
                a=TAU*k/sides;v.append(p+rr*(math.cos(a)*side+math.sin(a)*up))
        for j in range(len(points)-1):
            for k in range(sides):
                a=start+j*sides+k;b=start+j*sides+(k+1)%sides
                f.append((a,b,b+sides,a+sides));mi.append(idx)

    def leaf(root, direction, length, width, twist, idx):
        direction=direction.normalized()
        tangent=direction.cross(Vector((0,0,1)))
        if tangent.length < .01:tangent=Vector((1,0,0))
        tangent.normalize()
        lift=Vector((0,0,1))
        start=len(v)
        # Eight-vertex curved, keeled lanceolate leaflet with narrow imperfect tip.
        p0=root
        p1=root+direction*(length*.32)+lift*(length*.07)
        p2=root+direction*(length*.69)+lift*(length*.16)
        p3=root+direction*length+lift*(length*(.15+twist))
        v.extend([p0,p1-tangent*width*.48,p1+lift*width*.13,p1+tangent*width*.39,
                  p2-tangent*width*.32,p2+lift*width*.16,p2+tangent*width*.26,p3])
        for tri in [(0,1,2),(0,2,3),(1,4,5,2),(2,5,6,3),(4,7,5),(5,7,6)]:
            f.append(tuple(start+i for i in tri));mi.append(idx)

    # The first render exposed large gaps between clusters. Establish a jittered
    # continuous basal mat first, then layer irregular taller clumps over it.
    # Leaf span is 1.3-2.6 mm; basal shoot spacing 1.45 mm gives overlapping cover.
    clusters=[]
    spacing=.00145
    for gy in range(-55,56):
        for gx in range(-55,56):
            x=(gx+rng.uniform(-.43,.43))*spacing
            y=(gy+rng.uniform(-.43,.43))*spacing
            if x*x+y*y < .079**2:
                hh=.0045+.0017*noise(Vector((x*105,y*105,2)))
                clusters.append((x,y,.0002,hh,1))
    for i in range(220):
        rad=.077*math.sqrt(rng.random());a=rng.uniform(0,TAU)
        clusters.append((rad*math.cos(a),rad*math.sin(a),rng.uniform(.001,.0028),rng.uniform(.005,.0085),rng.randint(6,10)))
    shoots=0
    for cx,cy,spread,height,number in clusters:
        for kk in range(number):
            x=cx+rng.gauss(0,spread*.48);y=cy+rng.gauss(0,spread*.48)
            if x*x+y*y > .0795**2:continue
            # Density preserved at object contact; only deeply occluded interiors culled.
            hidden=((x-.003)**2+(y+.026)**2<.026**2 or (x+.032)**2+(y-.031)**2<.024**2)
            if hidden and rng.random()<.96:continue
            z=.0181+.0014*noise(Vector((x*170,y*170,3)))+.0007*noise(Vector((x*630,y*630,7)))
            hh=height*rng.uniform(.8,1.12)
            lean=rng.uniform(0,TAU);curl=rng.uniform(.0015,.0042)
            points=[]
            for j in range(5):
                t=j/4
                points.append(Vector((x+math.cos(lean)*curl*t*t,y+math.sin(lean)*curl*t*t,z+hh*(t-.13*t*t))))
            idx=rng.choices(range(6),[2,2,2,1,2,1])[0]
            tube(points,rng.uniform(.000065,.00013),idx)
            for j in range(6):
                t=.14+j*.14
                p=Vector((x+math.cos(lean)*curl*t*t,y+math.sin(lean)*curl*t*t,z+hh*(t-.13*t*t)))
                az=lean+j*2.41+rng.uniform(-.28,.28)
                for sign in [-1,1]:
                    aa=az+(0 if sign==1 else math.pi+rng.uniform(-.15,.15))
                    direct=Vector((math.cos(aa),math.sin(aa),rng.uniform(-.15,.62)))
                    length=rng.uniform(.0013,.0026)*(1-.26*t)
                    leaf(p,direct,length,length*rng.uniform(.38,.61),rng.uniform(-.3,.35),idx)
            shoots+=1
    obj=_mesh('Support | individual curled moss shoots and leaflets',v,f,col,mats['moss'],mi)
    obj['shoot_count']=shoots
    return obj


def _branch(col,mats):
    rng=random.Random(6113)
    near=Vector((.064,-.034,.036));far=Vector((.030,.065,.038));axis=(far-near).normalized()
    side=axis.cross(Vector((0,0,1))).normalized();up=side.cross(axis).normalized()
    def centre(t):
        return near+(far-near)*t+up*(.0015*math.sin(t*math.pi))+side*(.0014*math.sin(t*TAU))
    def radius(t,a):
        base=.0103*(1-.16*t)
        flutes=.045*noise(Vector((math.cos(a)*3,math.sin(a)*3,t*8)))+.027*noise(Vector((math.cos(a)*11,math.sin(a)*11,t*20)))+.015*math.sin(a*3+t*2)
        undulate=.039*math.sin(t*24+a*4)+.025*math.sin(t*91+a*3)
        return base*(1+flutes+undulate)
    nr=208;nl=122;v=[];f=[]
    for j in range(nl):
        t=j/(nl-1)
        for k in range(nr):
            a=TAU*k/nr;direction=side*math.cos(a)+up*math.sin(a)
            rr=radius(t,a)+.00014*noise(Vector((math.cos(a)*19,math.sin(a)*19,t*80)))
            v.append(centre(t)+direction*rr)
    for j in range(nl-1):
        for k in range(nr):
            a=j*nr+k;b=j*nr+(k+1)%nr;f.append((a,a+nr,b+nr,b))
    _mesh('Support | irregular fallen branch bark',v,f,col,[mats['bark']])
    v=[near-axis*.00008];uv=[(.5,0)];f=[];rings=28
    for j in range(1,rings+1):
        frac=j/rings
        for k in range(nr):
            a=TAU*k/nr
            d=side*math.cos(a)+up*math.sin(a)
            offset=.000012*noise(Vector((frac*20,math.cos(a)*12,math.sin(a)*12)))
            v.append(near+d*radius(0,a)*frac*.963-axis*(.00008+offset));uv.append((a/TAU,frac))
    for k in range(nr):f.append((0,1+k,1+(k+1)%nr))
    for j in range(rings-1):
        start=1+j*nr
        for k in range(nr):
            a=start+k;b=start+(k+1)%nr;f.append((a,a+nr,b+nr,b))
    _mesh('Support | exposed warm cut end and fine growth rings',v,f,col,[mats['wood']],uv=uv)

    # Discrete low foliose crust: broad connected patches separated by dark bark.
    v=[];f=[];mi=[]
    for i in range(5100):
        t=rng.uniform(.025,.99);a=rng.uniform(-.08,math.pi+.10)
        patch=noise(Vector((t*11,math.cos(a)*3,math.sin(a)*3)))
        if patch < -.10 or rng.random()<.025:continue
        radial=side*math.cos(a)+up*math.sin(a)
        tangent=-side*math.sin(a)+up*math.cos(a)
        ctr=centre(t)+radial*(radius(t,a)+rng.uniform(.000055,.00014))
        size=rng.uniform(.00055,.00145)
        lobes=rng.randint(7,12);idx=rng.choices(range(4),[3,4,1,1])[0]
        start=len(v);v.append(ctr)
        radii=[size*rng.uniform(.5,1.15) for k in range(lobes)]
        for j,frac in enumerate([.45,1.]):
            for k in range(lobes):
                phi=TAU*k/lobes
                r=radii[k]*frac
                curl=(.000045+.00009*rng.random())*frac*frac
                v.append(ctr+axis*math.cos(phi)*r+tangent*math.sin(phi)*r*.78+radial*curl)
        for k in range(lobes):
            nxt=(k+1)%lobes
            f.append((start,start+1+k,start+1+nxt));mi.append(idx)
            f.append((start+1+k,start+1+lobes+k,start+1+lobes+nxt,start+1+nxt));mi.append(idx)
    obj=_mesh('Support | overlapping mustard yellow lichen flakes',v,f,col,mats['lichen'],mi)
    obj['description']='Irregular foliose crust; many separate curled lobes, patchy bark exposure.'


def _slate(col,mats):
    # Finite oblique rear edge matches the reference's descending black boundary.
    # Root can move this named surface without changing any food support geometry.
    v=[];f=[];count=140;size=1.4
    for j in range(count+1):
        for i in range(count+1):
            x=-size/2+size*i/count
            rear_y=.19-.45*x
            y=-.7+(rear_y+.7)*j/count
            z=-.00015+.00006*noise(Vector((x*70,y*70,4)))
            v.append((x,y,z))
    for j in range(count):
        for i in range(count):
            a=j*(count+1)+i;f.append((a,a+1,a+count+2,a+count+1))
    obj=_mesh('Support | graphite slate photographic tabletop',v,f,col,[mats['slate']])
    obj['reference_rear_edge']='y = .19 - .45*x; front y=-.7; x=+/- .7 metres'
    return obj


def build_support(collection):
    mats=_materials()
    _slate(collection,mats)
    plate=_plate(collection,mats)
    moss=_moss(collection,mats)
    _branch(collection,mats)
    objects=[o for o in collection.objects if o.name.startswith('Support |')]
    return {'objects':len(objects),'vertices':sum(len(o.data.vertices) for o in objects if o.type=='MESH'),
            'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects if o.type=='MESH'),
            'plate_outer_diameter_m':.17,'moss_shoots':moss['shoot_count'],
            'plate_name':plate.name,'notes':'Handmade ceramic, original procedural leafy moss, patchy lichen branch and slate; no reference pixels in shading.'}
