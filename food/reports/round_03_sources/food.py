"""Hero-only, meter-scale reconstruction of the two pastry / roe bites.

This is deliberately dense food geometry, with no web-export compromises.
The supplied reference, not an ingredient claim, determines the materials.
Entry point: build_food(collection). No operators or external dependencies.
"""
import bpy
import math
import random
from mathutils import Vector
from mathutils.noise import noise as coherent_noise

TAU = math.tau
FOOD_DETAIL = 1.0


def _noise(p, scale=1.0):
    return coherent_noise(Vector((p[0] * scale, p[1] * scale, p[2] * scale)), noise_basis='PERLIN_ORIGINAL')


def _mesh(name, verts, faces, collection, materials, indices=None, smooth=True):
    mesh = bpy.data.meshes.new(name + ' | organic surface')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(name, mesh)
    collection.objects.link(ob)
    for mat in materials:
        mesh.materials.append(mat)
    if indices:
        for poly, idx in zip(mesh.polygons, indices):
            poly.material_index = idx
    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True
    return ob


def _mat(name, color, roughness=.45, sss=0.0, sss_scale=.001, transmission=0.0, ior=1.45):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    out = tree.nodes.new('ShaderNodeOutputMaterial')
    out.location = (880, 60)
    principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
    principled.name = 'Food | physically plausible body'
    principled.location = (590, 60)
    principled.inputs['Base Color'].default_value = (*color, 1)
    principled.inputs['Roughness'].default_value = roughness
    principled.inputs['IOR'].default_value = ior
    principled.inputs['Subsurface Weight'].default_value = sss
    principled.inputs['Subsurface Radius'].default_value = (1.0, .5, .22)
    principled.inputs['Subsurface Scale'].default_value = sss_scale
    principled.inputs['Transmission Weight'].default_value = transmission
    tree.links.new(principled.outputs['BSDF'], out.inputs['Surface'])
    tex = tree.nodes.new('ShaderNodeTexCoord')
    tex.name = 'Meters | object coordinates'
    tex.location = (-1050, 40)
    return material, tree, principled, tex


def _noise_node(tree, tex, name, scale, detail=3, roughness=.7, location=(-800, 50)):
    node = tree.nodes.new('ShaderNodeTexNoise')
    node.name = name
    node.label = name
    node.location = location
    node.inputs['Scale'].default_value = scale
    node.inputs['Detail'].default_value = detail
    node.inputs['Roughness'].default_value = roughness
    tree.links.new(tex.outputs['Object'], node.inputs['Vector'])
    return node


def _ramp(tree, socket, name, values, location=(-380, 80)):
    node = tree.nodes.new('ShaderNodeValToRGB')
    node.name = name
    node.label = name
    node.location = location
    ramp = node.color_ramp
    while len(ramp.elements) > 2:
        ramp.elements.remove(ramp.elements[-1])
    ramp.elements[0].position, ramp.elements[0].color = values[0]
    ramp.elements[1].position, ramp.elements[1].color = values[-1]
    for pos, col in values[1:-1]:
        ramp.elements.new(pos).color = col
    tree.links.new(socket, node.inputs['Fac'])
    return node


def _map(tree, socket, from_min, from_max, to_min, to_max, name, location=(-80, -150)):
    node = tree.nodes.new('ShaderNodeMapRange')
    node.name = name
    node.location = location
    node.inputs['From Min'].default_value = from_min
    node.inputs['From Max'].default_value = from_max
    node.inputs['To Min'].default_value = to_min
    node.inputs['To Max'].default_value = to_max
    node.clamp = True
    tree.links.new(socket, node.inputs['Value'])
    return node


def _build_materials():
    mats = {}
    m, nt, bs, tx = _mat('Food | baked choux crust · dry porous amber', (.43, .145, .014), .48, .018, .00018)
    broad = _noise_node(nt, tx, 'Uneven oven browning · 10 mm', 98, 2, .68, (-840, 450))
    pore = _noise_node(nt, tx, 'Baked cells · 0.32 mm', 3100, 2, .69, (-840, 110))
    color = _ramp(nt, broad.outputs['Fac'], 'Honey to toasted crust', [
        (.12, (.10, .020, .001, 1)), (.35, (.28, .081, .005, 1)),
        (.58, (.58, .235, .025, 1)), (.83, (.85, .46, .11, 1))], (-565, 440))
    grain_color = _ramp(nt, pore.outputs['Fac'], 'Raised pore edges catch the light', [
        (.15, (.42, .22, .07, 1)), (.54, (.89, .74, .43, 1)),
        (.90, (1, .91, .66, 1))], (-575, 170))
    multiply = nt.nodes.new('ShaderNodeMixRGB')
    multiply.name = 'Fine toasted cell variation'
    multiply.blend_type = 'MULTIPLY'
    multiply.inputs[0].default_value = .26
    multiply.location = (-270, 380)
    nt.links.new(color.outputs['Color'], multiply.inputs[1])
    nt.links.new(grain_color.outputs['Color'], multiply.inputs[2])
    # A shallow, broken herb-powder color deposit under the actual dust grains.
    # Coordinates are meters and all generated food vertices share local origin.
    separate = nt.nodes.new('ShaderNodeSeparateXYZ')
    separate.name = 'Shoulder height in meters'
    nt.links.new(tx.outputs['Object'], separate.inputs['Vector'])
    shoulder = _map(nt, separate.outputs['Z'], .048, .065, 0, .91,
                    'Powder deposit follows the upper shoulder', (-230, 640))
    patch = _map(nt, broad.outputs['Fac'], .18, .84, .12, 1.0,
                 'Powder falls in incomplete patches', (-230, 770))
    powder_mask = nt.nodes.new('ShaderNodeMath')
    powder_mask.operation = 'MULTIPLY'
    powder_mask.name = 'Broken dust deposit'
    nt.links.new(shoulder.outputs['Result'], powder_mask.inputs[0])
    nt.links.new(patch.outputs['Result'], powder_mask.inputs[1])
    dust = nt.nodes.new('ShaderNodeMixRGB')
    dust.name = 'Dry green powder over golden crust'
    dust.location = (200, 420)
    nt.links.new(powder_mask.outputs[0], dust.inputs[0])
    nt.links.new(multiply.outputs['Color'], dust.inputs[1])
    dust.inputs[2].default_value = (.205, .275, .027, 1)
    nt.links.new(dust.outputs['Color'], bs.inputs['Base Color'])
    rough = _map(nt, pore.outputs['Fac'], .15, .84, .32, .59, 'Crust absorbs unevenly')
    nt.links.new(rough.outputs['Result'], bs.inputs['Roughness'])
    bumps = nt.nodes.new('ShaderNodeBump')
    bumps.name = 'Submillimeter baked pores'
    bumps.location = (310, -220)
    bumps.inputs['Strength'].default_value = .25
    bumps.inputs['Distance'].default_value = .00009
    nt.links.new(pore.outputs['Fac'], bumps.inputs['Height'])
    nt.links.new(bumps.outputs['Normal'], bs.inputs['Normal'])
    mats['crust'] = m

    m, nt, bs, tx = _mat('Food | fissure · toasted bread interior', (.12, .032, .004), .76, .015, .00012)
    ns = _noise_node(nt, tx, 'Fissure porous walls', 2900, 2)
    br = nt.nodes.new('ShaderNodeBump')
    br.inputs['Strength'].default_value = .42
    br.inputs['Distance'].default_value = .00022
    nt.links.new(ns.outputs['Fac'], br.inputs['Height'])
    nt.links.new(br.outputs['Normal'], bs.inputs['Normal'])
    mats['fissure'] = m

    mats['powder'] = []
    for i, c in enumerate([(.20, .245, .038), (.32, .33, .055), (.13, .18, .014), (.47, .43, .082)]):
        m, nt, bs, tx = _mat('Food | moss-green dust grain %02d' % i, c, .79, .01, .00006)
        mats['powder'].append(m)

    m, nt, bs, tx = _mat('Food | ivory cut layer · porous emulsion', (.58, .49, .315), .42, .10, .00085, 0, 1.40)
    big = _noise_node(nt, tx, 'Quiet natural cream variation · 5 mm', 180, 2, .6, (-830, 350))
    color = _ramp(nt, big.outputs['Fac'], 'Pale ivory interior', [
        (.10, (.37, .29, .16, 1)), (.48, (.60, .51, .33, 1)),
        (.89, (.76, .66, .48, 1))], (-540, 350))
    nt.links.new(color.outputs['Color'], bs.inputs['Base Color'])
    micro = _noise_node(nt, tx, 'Cut-face air cells · 0.2 mm', 4700, 2, .65, (-830, 0))
    rr = _map(nt, micro.outputs['Fac'], .15, .80, .34, .49, 'Dry cut-face roughness')
    nt.links.new(rr.outputs['Result'], bs.inputs['Roughness'])
    br = nt.nodes.new('ShaderNodeBump')
    br.name = 'Emulsion micro-porosity'
    br.inputs['Strength'].default_value = .13
    br.inputs['Distance'].default_value = .000035
    nt.links.new(micro.outputs['Fac'], br.inputs['Height'])
    nt.links.new(br.outputs['Normal'], bs.inputs['Normal'])
    mats['cream'] = m

    m, nt, bs, tx = _mat('Food | thin amber filling · moist edge', (.32, .092, .016), .29, .09, .0005, .035, 1.40)
    nn = _noise_node(nt, tx, 'Amber filling uneven moistness', 350, 2)
    col = _ramp(nt, nn.outputs['Fac'], 'Caramelized amber filling', [
        (.13, (.15, .024, .003, 1)), (.47, (.38, .11, .018, 1)),
        (.88, (.64, .26, .04, 1))])
    nt.links.new(col.outputs['Color'], bs.inputs['Base Color'])
    rr = _map(nt, nn.outputs['Fac'], .1, .9, .21, .41, 'Localized moist edge')
    nt.links.new(rr.outputs['Result'], bs.inputs['Roughness'])
    bs.inputs['Coat Weight'].default_value = .10
    bs.inputs['Coat Roughness'].default_value = .25
    mats['amber'] = m

    m, nt, bs, tx = _mat('Food | dark leaf wrapper · broken wet surface', (.017, .032, .003), .29, .03, .00013, .03, 1.40)
    nn = _noise_node(nt, tx, 'Leaf fibrous color · 1 mm', 860, 3)
    col = _ramp(nt, nn.outputs['Fac'], 'Dark olive leaf', [
        (.08, (.001, .0015, .0002, 1)), (.47, (.004, .007, .0006, 1)),
        (.78, (.016, .024, .002, 1))])
    nt.links.new(col.outputs['Color'], bs.inputs['Base Color'])
    rr = _map(nt, nn.outputs['Fac'], .2, .8, .19, .47, 'Wrinkled leaf wetness')
    nt.links.new(rr.outputs['Result'], bs.inputs['Roughness'])
    br = nt.nodes.new('ShaderNodeBump')
    br.name = 'Leaf microfolds'
    br.inputs['Strength'].default_value = .48
    br.inputs['Distance'].default_value = .00020
    nt.links.new(nn.outputs['Fac'], br.inputs['Height'])
    nt.links.new(br.outputs['Normal'], bs.inputs['Normal'])
    mats['leaf'] = m

    mats['roe'] = []
    for i, (c, r) in enumerate([
        ((.012, .007, .004), .16), ((.019, .012, .007), .24),
        ((.006, .0045, .003), .135), ((.022, .013, .006), .27),
        ((.013, .014, .0055), .185), ((.008, .007, .005), .23)]):
        m, nt, bs, tx = _mat('Food | roe membrane %02d · dark brown olive' % i, c, r, .065, .00032, .14, 1.365)
        bs.inputs['Subsurface Radius'].default_value = (1, .45, .18)
        bs.inputs['Coat Weight'].default_value = .035
        bs.inputs['Coat Roughness'].default_value = .16
        fine = _noise_node(nt, tx, 'Roe localized membrane roughness', 1150, 2, .65)
        rr = _map(nt, fine.outputs['Fac'], .25, .78, r - .055, r + .13, 'Wetness is not uniform')
        nt.links.new(rr.outputs['Result'], bs.inputs['Roughness'])
        br = nt.nodes.new('ShaderNodeBump')
        br.name = 'Microscopic membrane'
        br.inputs['Strength'].default_value = .035
        br.inputs['Distance'].default_value = .000009
        nt.links.new(fine.outputs['Fac'], br.inputs['Height'])
        nt.links.new(br.outputs['Normal'], bs.inputs['Normal'])
        mats['roe'].append(m)

    m, nt, bs, tx = _mat('Food | ivory edible blossom · thin petals', (.90, .87, .77), .44, .18, .00016, .07, 1.38)
    bs.inputs['Subsurface Radius'].default_value = (1, .7, .48)
    ns = _noise_node(nt, tx, 'Subtle petal grain', 1800, 1)
    br = nt.nodes.new('ShaderNodeBump')
    br.inputs['Strength'].default_value = .15
    br.inputs['Distance'].default_value = .000027
    nt.links.new(ns.outputs['Fac'], br.inputs['Height'])
    nt.links.new(br.outputs['Normal'], bs.inputs['Normal'])
    mats['petal'] = m
    mats['pollen'] = _mat('Food | flower heart · pale yellow green', (.28, .255, .039), .7)[0]
    mats['stamen'] = _mat('Food | flower heart · narrow dark anthers', (.065, .049, .008), .55)[0]
    mats['magenta'] = _mat('Food | tiny magenta flower buds', (.45, .008, .125), .38, .16, .00015)[0]
    mats['burgundy'] = _mat('Food | burgundy microleaf · thin curled', (.105, .004, .009), .45, .13, .00013, .04)[0]
    mats['stem'] = _mat('Food | garnish stems', (.14, .014, .011), .52, .05, .0001)[0]
    return mats


# Radius profile is intentionally not a sphere: broad shoulder, small foot,
# flattened asymmetric crown and shallow ragged expansion crease near its foot.
_PROFILE = [(0, .60), (.04, .74), (.12, .875), (.23, .961),
            (.35, .996), (.47, 1.00), (.61, .991), (.73, .946),
            (.84, .855), (.93, .735), (1, .615)]


def _profile(t):
    for j in range(len(_PROFILE)-1):
        a, b = _PROFILE[j], _PROFILE[j+1]
        if t <= b[0]:
            w = (t-a[0])/(b[0]-a[0])
            # Tangents continue through control points, avoiding lathed rings.
            prev = _PROFILE[max(0, j-1)]
            nex = _PROFILE[min(len(_PROFILE)-1, j+2)]
            m0 = (b[1]-prev[1])/(b[0]-prev[0])
            m1 = (nex[1]-a[1])/(nex[0]-a[0])
            dt = b[0]-a[0]
            return ((2*w**3-3*w*w+1)*a[1] + (w**3-2*w*w+w)*dt*m0
                    + (-2*w**3+3*w*w)*b[1] + (w**3-w*w)*dt*m1)
    return _PROFILE[-1][1]


def _pastry_point(t, a, center, radius, z0, height, seed, relief=True):
    c, s = math.cos(a), math.sin(a)
    # Larger, non-repeating asymmetry; intentionally restrained rather than rocky.
    phase = seed * 1.183
    lobes = .021*math.sin(3*a + phase) + .018*math.sin(5*a-.9+phase) + .014*math.cos(7*a+phase*.23)
    warp = .0008*math.sin(a*2 + phase) * math.sin(math.pi*t)
    z = z0 + height*t + warp
    r = radius * _profile(t) * (1 + lobes)
    base = (center[0] + r*c, center[1] + r*s, z)
    coarse = _noise((base[0]+seed*.013, base[1], base[2]), 150)
    r += coarse * .00042 * math.sin(math.pi*max(.035, min(.965, t)))
    # Bake split occurs low on the reference pastry, not as an equator seam.
    seam_t = .247 + .025*math.sin(a*4+phase) + .012*math.sin(a*9-phase)
    seam = math.exp(-((t-seam_t)/.019)**2)
    # The split is locally absent, as a real expansion crack would be.
    seam_presence = max(.14, .66 + .42*math.sin(2*a+phase))
    r -= .00062*seam*seam_presence
    if relief:
        q = (base[0]+seed*.27, base[1]-seed*.08, base[2])
        mid = _noise(q, 730)
        fine = _noise(q, 1970)
        # Unequal baked cells join the continuous crust instead of bead-like blobs.
        cell = max(0, mid + .10)**1.35
        r += .00031*cell + .00008*fine
        z += .00008*fine * (t*.65+.25)
    return (center[0]+r*c + .00048*math.sin(t*3.6+phase),
            center[1]+r*s + .00039*math.sin(t*4.2+phase*2), z)


def _pastry(name, center, radius, z0, body_height, seed, collection, mats):
    N, M = int(416*FOOD_DETAIL), int(164*FOOD_DETAIL)
    verts, faces, ids = [], [], []
    for k in range(M+1):
        t = k/M
        for i in range(N):
            verts.append(_pastry_point(t, TAU*i/N, center, radius, z0, body_height, seed))
    for k in range(M):
        t = (k+.5)/M
        for i in range(N):
            a = TAU*(i+.5)/N
            faces.append((k*N+i, k*N+(i+1)%N, (k+1)*N+(i+1)%N, (k+1)*N+i))
            seam_t = .247 + .025*math.sin(a*4+seed*1.183) + .012*math.sin(a*9-seed*1.183)
            # A patchy toast line, not a continuous black wire.
            ids.append(int(abs(t-seam_t) < .006 and math.sin(a*2+seed*1.183) > -.1))
    bottom, top = len(verts), len(verts)+1
    verts.extend([(center[0], center[1], z0), (center[0], center[1], z0+body_height-.0005)])
    for i in range(N):
        faces.append((bottom, (i+1)%N, i)); ids.append(0)
        faces.append((top, M*N+i, M*N+(i+1)%N)); ids.append(0)
    body = _mesh(name+' | irregular baked body', verts, faces, collection, [mats['crust'], mats['fissure']], ids)

    # Crust scale plates are shallow chips attached to the pastry, with rough
    # uneven perimeters. They are NOT separate spherical lumps.
    rng = random.Random(seed+784)
    fv, ff, fi = [], [], []
    for k in range(int(1600*FOOD_DETAIL)):
        t = rng.uniform(.08, .97)
        a = rng.uniform(0, TAU)
        p = Vector(_pastry_point(t, a, center, radius, z0, body_height, seed))
        tangent = Vector((-math.sin(a), math.cos(a), 0))
        up = Vector(_pastry_point(min(.999, t+.002), a, center, radius, z0, body_height, seed, False))-Vector(_pastry_point(max(.001, t-.002), a, center, radius, z0, body_height, seed, False))
        up.normalize()
        normal = tangent.cross(up).normalized()
        sx = rng.uniform(.00028, .00104)
        sy = sx*rng.uniform(.52, 1.02)
        h = rng.uniform(.000055, .00022)
        seg = rng.randint(7, 10)
        off = len(fv)
        fv.append(tuple(p+normal*h))
        irregular=[rng.uniform(.74, 1.18) for _ in range(seg)]
        for ring,cap_height in [(.46,h*.83),(.78,h*.38),(1,-.00007)]:
            for i in range(seg):
                ang = TAU*i/seg
                rad = irregular[i]*ring
                fv.append(tuple(p+tangent*(math.cos(ang)*sx*rad)+up*(math.sin(ang)*sy*rad)+normal*cap_height))
        for i in range(seg):
            ff.append((off, off+1+i, off+1+(i+1)%seg)); fi.append(0)
        for ring in range(2):
            for i in range(seg):
                ff.append((off+1+ring*seg+i,off+1+(ring+1)*seg+i,
                           off+1+(ring+1)*seg+(i+1)%seg,off+1+ring*seg+(i+1)%seg));fi.append(0)
    flakes = _mesh(name+' | shallow baked crust flakes', fv, ff, collection, [mats['crust']], fi)
    # A previous loop-variable collision collapsed these details onto the base.
    # Check the complete distribution, not just the very first valid blister.
    blister_z=sorted(v[2] for v in fv)
    assert blister_z[int(len(blister_z)*.50)] > z0+body_height*.36, 'Blister median collapsed toward the bun base'
    assert blister_z[int(len(blister_z)*.95)] > z0+body_height*.84, 'Blister caps do not reach the shoulder'
    flakes['validated_z_range_m']=(blister_z[0],blister_z[-1])

    # Patchy dry dust follows shoulder geometry. Unequal tetrahedral grains
    # preserve dry particulate highlights rather than a smooth green wash.
    gv, gf, gi = [], [], []
    for k in range(int(12500*FOOD_DETAIL)):
        t = rng.uniform(.59, .997)
        a = rng.uniform(0, TAU)
        p = Vector(_pastry_point(t, a, center, radius, z0, body_height, seed))
        patch = _noise((p.x+seed*.006, p.y, p.z), 330)
        if rng.random() > (.30+.48*(t-.59)/.407 + .24*patch):
            continue
        grain = rng.uniform(.000045, .000135)
        tangent = Vector((-math.sin(a), math.cos(a), 0))
        up = Vector(_pastry_point(min(.999, t+.002), a, center, radius, z0, body_height, seed, False))-Vector(_pastry_point(max(.001, t-.002), a, center, radius, z0, body_height, seed, False))
        up.normalize()
        normal = tangent.cross(up).normalized()
        o = len(gv)
        gv.extend([tuple(p + tangent*(-grain*.7)-up*(grain*.35)+normal*.00002),
                   tuple(p + tangent*(grain*.8)-up*(grain*.4)+normal*.00002),
                   tuple(p + up*(grain*.85)+normal*.00002),
                   tuple(p + normal*grain*.75)])
        gf.extend([(o,o+1,o+3), (o+1,o+2,o+3), (o+2,o,o+3)])
        gi.extend([rng.choices(range(4), [4,5,3,2])[0]]*3)
    grains = _mesh(name+' | green shoulder dust', gv, gf, collection, mats['powder'], gi, False)
    dust_z=[v[2] for v in gv]
    assert min(dust_z) > z0+body_height*.54, 'Shoulder dust is below its intended surface region'
    assert max(dust_z) > z0+body_height*.94, 'Shoulder dust is missing from the crown'
    grains['validated_z_range_m']=(min(dust_z),max(dust_z))
    return body, flakes, grains


def _cut_layer(name, center, radius, bottom, top, seed, collection, material, porous=False):
    rng = random.Random(seed)
    N, M = 288, (42 if porous else 14)
    verts, faces = [], []
    pores = [(rng.random()*TAU, rng.uniform(bottom+.0006, top-.0006), rng.uniform(.00006, .00020), rng.uniform(.000015, .00005)) for _ in range(110)] if porous else []
    for j in range(M+1):
        t = j/M
        z = bottom+(top-bottom)*t
        edge = .00022*(math.exp(-((t-.0)/.085)**2)+math.exp(-((t-1)/.085)**2))
        for i in range(N):
            a = TAU*i/N
            wav = .00026*math.sin(a*3+seed) + .00020*math.cos(a*7-seed)
            rr = radius + wav - edge
            p = (center[0]+rr*math.cos(a), center[1]+rr*math.sin(a), z)
            rr += _noise((p[0]+seed*.019,p[1],p[2]), 1050)*(.000025 if porous else .00012)
            if porous:
                for pa, pz, pr, depth in pores:
                    da = abs((a-pa+math.pi)%TAU-math.pi)*radius
                    if da < pr*2.5 and abs(z-pz) < pr*2.5:
                        rr -= depth * math.exp(-(da*da+(z-pz)**2)/(pr*pr))
            zz = z + .00016*math.sin(a*3+.8+seed) + .000085*math.sin(a*11+t*1.2)
            verts.append((center[0]+rr*math.cos(a)+t*.00015, center[1]+rr*math.sin(a), zz))
    for j in range(M):
        for i in range(N):
            faces.append((j*N+i, j*N+(i+1)%N, (j+1)*N+(i+1)%N, (j+1)*N+i))
    vbottom, vtop = len(verts), len(verts)+1
    verts += [(center[0],center[1],bottom), (center[0],center[1],top)]
    for i in range(N):
        faces.append((vbottom, (i+1)%N, i))
        faces.append((vtop, M*N+i, M*N+(i+1)%N))
    return _mesh(name, verts, faces, collection, [material])


def _leaf_wrapper(name, center, radius, height, seed, collection, material):
    rng = random.Random(seed)
    N, M = 256, 18
    verts, faces = [], []
    phase = seed*.719
    peaks = [(1.9+phase%1, .0032, .15), (4.1+phase%1, .0045, .17), (.35, .0028, .14)]
    # Main dark sheet, subtly undulating, rises into an irregular hand-cut rim.
    for j in range(M+1):
        r = radius*j/M
        for i in range(N):
            a = TAU*i/N
            edge_mask = (j/M)**13
            edge = .00048 + .00032*math.sin(a*7+phase)+.0002*math.sin(a*19)
            for pa, ph, pw in peaks:
                da = abs((a-pa+math.pi)%TAU-math.pi)
                edge += ph*math.exp(-(da/pw)**2)
            rr = r*(1+.018*math.sin(5*a+phase)+.011*math.cos(11*a))
            z = height + .00012*math.sin(6*a+1.1)*j/M + edge*edge_mask
            verts.append((center[0]+rr*math.cos(a), center[1]+rr*math.sin(a), z))
    for j in range(M):
        for i in range(N):
            faces.append(((j+1)*N+i, (j+1)*N+(i+1)%N, j*N+(i+1)%N, j*N+i))
    # A very thin physical lower side catches no hard CG silhouette.
    off = len(verts)
    for i in range(N):
        x,y,z=verts[M*N+i]
        verts.append((x,y,height-.00065+.00012*math.sin(i*TAU/N*6)))
    for i in range(N):
        faces.append((M*N+i, off+i, off+(i+1)%N, M*N+(i+1)%N))
    return _mesh(name, verts, faces, collection, [material])


def _append_roe(verts, faces, indices, center, r, rng, matidx, detail=1.0):
    U, V = int(32*detail), int(20*detail)
    off = len(verts)
    phase = rng.random()*TAU
    ax, ay, az = rng.uniform(.955,1.065), rng.uniform(.955,1.06), rng.uniform(.86,1.025)
    dimple_a, dimple_t = rng.random()*TAU, rng.uniform(.28,.8)
    for j in range(1,V):
        theta = math.pi*j/V
        st, ct=math.sin(theta),math.cos(theta)
        for i in range(U):
            a=TAU*i/U
            irregular=1+.010*math.sin(3*a+phase)*st**2+.007*math.cos(theta*4+phase)*st
            da=abs((a-dimple_a+math.pi)%TAU-math.pi)
            dimple=.018*math.exp(-((theta-dimple_t)/.19)**2-(da/.3)**2)
            rr=r*(irregular-dimple)
            verts.append((center[0]+rr*st*math.cos(a)*ax, center[1]+rr*st*math.sin(a)*ay, center[2]+rr*ct*az))
    for j in range(V-2):
        for i in range(U):
            faces.append((off+(j+1)*U+i, off+(j+1)*U+(i+1)%U, off+j*U+(i+1)%U, off+j*U+i))
            indices.append(matidx)
    # Shared poles avoid the faceted specular pinching of coincident UV poles.
    north,south=len(verts),len(verts)+1
    verts.extend([(center[0],center[1],center[2]+r*az),
                  (center[0],center[1],center[2]-r*az)])
    for i in range(U):
        faces.append((north,off+i,off+(i+1)%U));indices.append(matidx)
        faces.append((south,off+(V-2)*U+(i+1)%U,off+(V-2)*U+i));indices.append(matidx)


def _roe_cluster(name, center, radius, base, seed, collection, mats):
    rng = random.Random(seed)
    eggs=[]
    # Variable-size hard-core first layer follows the irregular leaf, preserving
    # real gaps and darker occlusion between beads instead of an intersected pile.
    for attempt in range(12500):
        r=rng.uniform(.00120,.00179)
        a=rng.uniform(0,TAU)
        rad=(radius-r*.66)*math.sqrt(rng.random())
        x,y=center[0]+rad*math.cos(a),center[1]+rad*math.sin(a)
        if all((x-ex)**2+(y-ey)**2 > (r+er-.000045)**2 for ex,ey,ez,er in eggs):
            z=base+r*.92+.00010*math.sin(x*760+y*580)
            eggs.append((x,y,z,r))
        if len(eggs)>=148:
            break
    base_count=len(eggs)
    # Additional roe rests over interstices; every new egg is vertically settled
    # against its neighbors. No visibly overlapping spheres or perfect grid.
    upper=[]
    for attempt in range(7000):
        if len(upper)>=110:
            break
        r=rng.uniform(.00114,.00175)
        a=rng.uniform(0,TAU)
        rad=(radius-r*1.00)*math.sqrt(rng.random())
        x,y=center[0]+rad*math.cos(a),center[1]+rad*math.sin(a)
        # A second-layer center may not be directly above another top bead.
        if any((x-ex)**2+(y-ey)**2 < (r+er-.000055)**2 for ex,ey,ez,er in upper):
            continue
        z=base+r
        for ex,ey,ez,er in eggs[:base_count]:
            d2=(x-ex)**2+(y-ey)**2
            rr=r+er-.000045
            if d2<rr*rr:
                z=max(z,ez+math.sqrt(rr*rr-d2)*.91)
        if z < base+.0032:
            continue
        upper.append((x,y,z,r))
    eggs += upper
    verts,faces,indices=[],[],[]
    for x,y,z,r in eggs:
        idx=rng.choices(range(6),[4,3,5,2,2,3])[0]
        _append_roe(verts, faces, indices, (x,y,z),r,rng,idx)
    ob=_mesh(name+' | individually deformed packed roe',verts,faces,collection,mats['roe'],indices)
    ob['bead_count']=len(eggs)
    ob['packing']='Two crowded irregular layers, settled on neighbors; radius 1.14–1.79 mm'
    return ob,eggs


def _tube(name, points, radius, collection, material, sides=8):
    verts, faces=[],[]
    for j, point in enumerate(points):
        p=Vector(point)
        tangent=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
        tangent.normalize()
        axis=tangent.cross(Vector((0,0,1)))
        if axis.length<.001:
            axis=tangent.cross(Vector((0,1,0)))
        axis.normalize()
        cross=tangent.cross(axis).normalized()
        rr=radius*(1-.30*j/max(1,len(points)-1))
        for i in range(sides):
            a=TAU*i/sides
            verts.append(tuple(p+axis*math.cos(a)*rr+cross*math.sin(a)*rr))
    for j in range(len(points)-1):
        for i in range(sides):
            faces.append((j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i))
    return _mesh(name,verts,faces,collection,[material])


def _flower(name, position, radius, seed, collection, mats, tilt=(.12,-.33,.0)):
    rng=random.Random(seed)
    origin=Vector(position)
    normal=Vector((tilt[0],tilt[1],1)).normalized()
    east=Vector((1,0,-tilt[0])).normalized()
    north=normal.cross(east).normalized()
    verts,faces=[],[]
    for petal in range(4):
        angle=TAU*petal/4+rng.uniform(-.19,.19)+seed*.17
        along=(east*math.cos(angle)+north*math.sin(angle)).normalized()
        across=normal.cross(along).normalized()
        length=radius*rng.uniform(.80,1.14)
        width=radius*rng.uniform(.37,.56)
        fold=rng.uniform(-.11,.18)
        twist=rng.uniform(-.055,.055)
        off=len(verts)
        rows,cols=18,14
        for j in range(rows+1):
            t=j/rows
            # Heart-like lobe with softly indented tip, no uniformly oval petals.
            halfwidth=width*math.sin(math.pi*(.015+t*.975))**.65
            for i in range(cols+1):
                s=-1+2*i/cols
                indent=.10*math.exp(-(s/.26)**2)*t**7
                forward=length*(t-indent)
                wav=.00006*math.sin(10*t+s*5+petal)
                cup=radius*(.095*s*s+.045*math.sin(t*math.pi)+fold*t**1.7+twist*s*t) + wav
                p=origin+along*(forward+radius*.12)+across*halfwidth*s+normal*cup
                verts.append(tuple(p))
        for j in range(rows):
            for i in range(cols):
                a=off+j*(cols+1)+i
                faces.append((a+cols+1,a+cols+2,a+1,a))
    flower=_mesh(name+' | four imperfect ivory petals',verts,faces,collection,[mats['petal']])
    sol=flower.modifiers.new('Actual petal thickness · 24 microns','SOLIDIFY')
    sol.thickness=.000024
    # Tiny central pistil and curved anthers are the only extra flower geometry.
    vv,ff,ii=[],[],[]
    _append_roe(vv,ff,ii,tuple(origin+normal*.0001),radius*.14,rng,0,.5)
    _mesh(name+' | yellow-green heart',vv,ff,collection,[mats['pollen']],ii)
    for k in range(4):
        a=TAU*k/4+.4
        v=east*math.cos(a)+north*math.sin(a)
        p0=origin+normal*.00015
        p1=origin+v*(radius*.17)+normal*.00036
        p2=origin+v*(radius*.24)+normal*.0002
        _tube(name+' | anther %02d'%k,[p0,p1,p2],.000055,collection,mats['stamen'],6)
    return flower


def _garnish(name, center, creamtop, seed, collection, mats):
    rng=random.Random(seed)
    objects=[]
    # The forward blossom nestles into the roe, with the flower looking slightly
    # toward the camera. The rear blossom is smaller and a little out of focus.
    objects.append(_flower(name+' | foreground blossom', (center[0]-.0080,center[1]-.0183,creamtop+.0081),.00355,seed+3,collection,mats,(-.04,-.65,0)))
    objects.append(_flower(name+' | rear blossom', (center[0]+.0045,center[1]+.0145,creamtop+.0083),.00265,seed+8,collection,mats,(.13,-.15,0)))
    for k,(a,length) in enumerate([(3.62,.0080),(5.83,.0058),(1.15,.0074)]):
        a+=.09*math.sin(seed+k)
        x,y=center[0]+.0215*math.cos(a),center[1]+.0215*math.sin(a)
        z=creamtop+.0004
        # Slim curved magenta stem, flower bud and pointed burgundy leaf.
        p0=Vector((x,y,z))
        p1=p0+Vector((math.cos(a)*.0010,math.sin(a)*.0010,length*.55))
        p2=p0+Vector((math.cos(a)*.0015,math.sin(a)*.0015,length))
        if k<2:
            objects.append(_tube(name+' | magenta bud stem %d'%k,[p0,p1,p2],.00015,collection,mats['stem']))
            vv,ff,ii=[],[],[]
            # A compact organic bud, elongated after explicit mesh construction.
            _append_roe(vv,ff,ii,(0,0,0),.00082,rng,0,.6)
            vv=[(x+p2.x,y+p2.y,z*1.36+p2.z) for x,y,z in vv]
            objects.append(_mesh(name+' | small magenta bud %d'%k,vv,ff,collection,[mats['magenta']],ii))
        lv,lf=[],[]
        rows,cols=20,8
        inward=Vector((-math.sin(a),math.cos(a),0))
        for j in range(rows+1):
            t=j/rows
            width=.0013*math.sin(math.pi*t)**.75
            axis=p0+Vector((math.cos(a)*.0023*t,math.sin(a)*.0023*t,length*t))
            axis+=inward*(.0010*math.sin(t*2.5))
            for i in range(cols+1):
                s=-1+2*i/cols
                point=axis+inward*(width*s)+Vector((math.cos(a),math.sin(a),0))*(.0007*s*s*math.sin(math.pi*t))
                lv.append(tuple(point))
        for j in range(rows):
            for i in range(cols):
                o=j*(cols+1)+i
                lf.append((o,o+1,o+cols+2,o+cols+1))
        objects.append(_mesh(name+' | pointed burgundy leaf %d'%k,lv,lf,collection,[mats['burgundy']]))
    return objects


def build_food(collection):
    """Create the reference-visible two bites. Parent caller owns the scene."""
    mats=_build_materials()
    result={'objects':[], 'pastries':[], 'roe_clusters':[], 'materials':mats, 'roe_count':0}
    specs=[
        dict(name='Hero front bite', center=(.003,-.026), radius=.0345, z0=.025, height=.043,
             cr=.0230, cb=.0701, ct=.0800, seed=43),
        dict(name='Rear bite', center=(-.032,.031), radius=.0295, z0=.025, height=.040,
             cr=.0205, cb=.0671, ct=.0765, seed=101),
    ]
    for spec in specs:
        name,center,seed=spec['name'],spec['center'],spec['seed']
        crust=_pastry(name,center,spec['radius'],spec['z0'],spec['height'],seed,collection,mats)
        result['objects']+=list(crust)
        result['pastries'].append(crust[0])
        amber=_cut_layer(name+' | irregular amber filling',center,spec['cr']*.98,
                         spec['z0']+spec['height']-.0009,spec['cb']+.00013,seed+3,collection,mats['amber'])
        cream=_cut_layer(name+' | porous ivory slice',center,spec['cr'],spec['cb'],spec['ct'],seed+9,collection,mats['cream'],True)
        leaf=_leaf_wrapper(name+' | dark leaf wrapper',center,spec['cr']*1.008,spec['ct']+.00055,seed+13,collection,mats['leaf'])
        roe,eggs=_roe_cluster(name,center,spec['cr']*.987,spec['ct']+.00085,seed+41,collection,mats)
        garnish=_garnish(name,center,spec['ct'],seed+63,collection,mats)
        result['objects'] += [amber,cream,leaf,roe]+garnish
        result['roe_clusters'].append(roe)
        result['roe_count']+=len(eggs)
    result['mesh_vertices']=sum(len(o.data.vertices) for o in result['objects'] if o.type=='MESH')
    result['mesh_polygons']=sum(len(o.data.polygons) for o in result['objects'] if o.type=='MESH')
    result['hero_focus']=(.003,-.031,.075)
    result['notes']='Original explicit organic geometry; scale in meters; no stock primitives or external food textures.'
    return result
