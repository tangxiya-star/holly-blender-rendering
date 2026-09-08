"""Metric Copenhagen street surfaces. Call build_surfaces() after scale review.

The slabs, kerbs, setts, and markings are combined by material so a long
walkable street does not require thousands of individual Blender objects.
"""
import bpy
import math
import random
from collections import defaultdict


class _Batch:
    def __init__(self):
        self.data = defaultdict(lambda: [[], []])

    def mesh(self, material, vertices, faces):
        dst_v, dst_f = self.data[material]
        first = len(dst_v)
        dst_v.extend(vertices)
        dst_f.extend(tuple(first + i for i in face) for face in faces)

    def box(self, mat, x0, x1, y0, y1, bottom, top):
        self.mesh(mat, [(x0,y0,bottom),(x1,y0,bottom),(x1,y1,bottom),(x0,y1,bottom),
                        (x0,y0,top),(x1,y0,top),(x1,y1,top),(x0,y1,top)],
                  [(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])

    def tile(self, mat, x0, x1, y0, y1, z, chamfer=.004):
        # A real edge catches soft skylight; the joint bed hides the open base.
        c = min(chamfer, (x1-x0)/5, (y1-y0)/5)
        self.mesh(mat, [(x0,y0,z-c),(x1,y0,z-c),(x1,y1,z-c),(x0,y1,z-c),
                        (x0+c,y0+c,z),(x1-c,y0+c,z),(x1-c,y1-c,z),(x0+c,y1-c,z)],
                  [(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])

    def quad(self, mat, x0, x1, y0, y1, z):
        self.mesh(mat, [(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)], [(0,1,2,3)])

    def line(self, mat, points, width, z):
        for a, b in zip(points, points[1:]):
            dx, dy = b[0]-a[0], b[1]-a[1]
            d = math.hypot(dx,dy)
            if d < .00001:
                continue
            nx, ny = -dy/d*width/2, dx/d*width/2
            self.mesh(mat, [(a[0]+nx,a[1]+ny,z),(a[0]-nx,a[1]-ny,z),
                            (b[0]-nx,b[1]-ny,z),(b[0]+nx,b[1]+ny,z)], [(0,1,2,3)])

    def ring(self, mat, x, y, radius, width, z, n=40):
        vertices = []
        for i in range(n):
            t = i*math.tau/n
            for r in (radius-width/2, radius+width/2):
                vertices.append((x+r*math.cos(t),y+r*math.sin(t),z))
        self.mesh(mat, vertices, [(2*i,2*i+1,2*((i+1)%n)+1,2*((i+1)%n)) for i in range(n)])

    def finish(self, collection, materials):
        count = 0
        for key, (verts, faces) in self.data.items():
            mesh = bpy.data.meshes.new('CPH_SurfaceMesh_' + key)
            mesh.from_pydata(verts, [], faces)
            mesh.update()
            obj = bpy.data.objects.new('CPH_' + key, mesh)
            collection.objects.link(obj)
            obj.data.materials.append(materials[key])
            obj['metric_surface'] = True
            count += len(faces)
        return count


def _material(name, color, roughness=.8, fine_scale=90, relief=.0015,
              variation=.12, metallic=0, aggregate=.10):
    mat = bpy.data.materials.get('CPH_Surface_' + name)
    if mat is None:
        mat = bpy.data.materials.new('CPH_Surface_' + name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (900, 0)
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    shader.location = (630, 0)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    links.new(shader.outputs['BSDF'], out.inputs['Surface'])
    geometry = nodes.new('ShaderNodeNewGeometry')
    geometry.location = (-1100, 80)
    grain = nodes.new('ShaderNodeTexNoise')
    grain.location = (-850, 20)
    grain.inputs['Scale'].default_value = fine_scale
    grain.inputs['Detail'].default_value = 2
    grain.inputs['Roughness'].default_value = .72
    links.new(geometry.outputs['Position'], grain.inputs['Vector'])
    mottling = nodes.new('ShaderNodeTexNoise')
    mottling.location = (-850, 400)
    mottling.inputs['Scale'].default_value = .36
    mottling.inputs['Detail'].default_value = 2
    links.new(geometry.outputs['Position'], mottling.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (-480, 400)
    ramp.color_ramp.elements[0].position = .16
    ramp.color_ramp.elements[0].color = (*(max(.003,c*(1-variation)) for c in color),1)
    ramp.color_ramp.elements[1].position = .84
    ramp.color_ramp.elements[1].color = (*(min(.95,c*(1+variation)) for c in color),1)
    links.new(mottling.outputs['Fac'],ramp.inputs['Fac'])
    # Fine color structure is essential: bump alone is lost to denoising at
    # eye-level distances. Distances are world metres, never object Generated.
    cells = nodes.new('ShaderNodeTexVoronoi')
    cells.location = (-850,-230)
    cells.feature = 'F1'
    cells.distance = 'EUCLIDEAN'
    cells.inputs['Scale'].default_value = fine_scale*1.4
    links.new(geometry.outputs['Position'],cells.inputs['Vector'])
    fine_mix = nodes.new('ShaderNodeMixRGB')
    fine_mix.location = (-510,20)
    fine_mix.blend_type = 'MIX'
    fine_mix.inputs[0].default_value = .32
    links.new(grain.outputs['Fac'],fine_mix.inputs[1])
    links.new(cells.outputs['Distance'],fine_mix.inputs[2])
    micro_ramp = nodes.new('ShaderNodeValToRGB')
    micro_ramp.location = (-270,90)
    micro_ramp.color_ramp.elements[0].position = .25
    micro_ramp.color_ramp.elements[0].color = (1-aggregate,1-aggregate,1-aggregate,1)
    micro_ramp.color_ramp.elements[1].position = .72
    micro_ramp.color_ramp.elements[1].color = (1+aggregate,1+aggregate,1+aggregate,1)
    links.new(fine_mix.outputs['Color'],micro_ramp.inputs['Fac'])
    base_mix = nodes.new('ShaderNodeMixRGB')
    base_mix.location = (160,300)
    base_mix.blend_type = 'MULTIPLY'
    base_mix.inputs[0].default_value = 1
    links.new(ramp.outputs['Color'],base_mix.inputs[1])
    links.new(micro_ramp.outputs['Color'],base_mix.inputs[2])
    links.new(base_mix.outputs['Color'],shader.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump')
    bump.location = (160,-80)
    bump.inputs['Strength'].default_value = .62
    bump.inputs['Distance'].default_value = relief
    links.new(fine_mix.outputs['Color'],bump.inputs['Height'])
    # Secondary sand-scale relief gives the broad aggregate a matte mineral
    # surface, rather than polished or rubbery lumps.
    sand = nodes.new('ShaderNodeTexNoise')
    sand.location = (-510,-450)
    sand.inputs['Scale'].default_value = fine_scale*2.75
    sand.inputs['Detail'].default_value = 1.5
    links.new(geometry.outputs['Position'],sand.inputs['Vector'])
    micro_bump = nodes.new('ShaderNodeBump')
    micro_bump.location = (410,-130)
    micro_bump.inputs['Strength'].default_value = .31
    micro_bump.inputs['Distance'].default_value = relief*.30
    links.new(sand.outputs['Fac'],micro_bump.inputs['Height'])
    links.new(bump.outputs['Normal'],micro_bump.inputs['Normal'])
    links.new(micro_bump.outputs['Normal'],shader.inputs['Normal'])
    remap = nodes.new('ShaderNodeMapRange')
    remap.location = (-120,-210)
    remap.inputs['From Min'].default_value = 0
    remap.inputs['From Max'].default_value = 1
    remap.inputs['To Min'].default_value = max(.04,roughness-.08)
    remap.inputs['To Max'].default_value = min(1,roughness+.07)
    links.new(grain.outputs['Fac'],remap.inputs['Value'])
    links.new(remap.outputs['Result'],shader.inputs['Roughness'])
    return mat


def _intervals(a, b, excluded):
    cursor = a
    for lo, hi in sorted(excluded):
        if lo > cursor:
            yield cursor, min(lo,b)
        cursor = max(cursor,hi)
    if cursor < b:
        yield cursor,b


def _paving(batch, rng, x0, x1, y0, y1, axis='y'):
    """Copenhagen concrete flag bands separated by narrow granite sett rows."""
    batch.box('Joint_bed',x0,x1,y0,y1,.12,.174)
    # Tile coordinates are expressed in walking direction, across pavement.
    start,end = (y0,y1) if axis == 'y' else (x0,x1)
    side0,side1 = (x0,x1) if axis == 'y' else (y0,y1)
    width = side1-side0
    nflags = max(1, round((width-.22)/.75))
    band = (width-.22)/nflags

    def tile(material, u0,u1,v0,v1,z,chamfer):
        if axis == 'y':
            batch.tile(material,v0,v1,u0,u1,z,chamfer)
        else:
            batch.tile(material,u0,u1,v0,v1,z,chamfer)

    # A narrow, darker double course at the road edge and a fine course between
    # concrete walking bands; joints remain millimetres, not cartoon black gaps.
    def setts(v0,v1):
        p = start
        while p < end-.015:
            q = min(end,p+rng.uniform(.145,.185))
            tile('Sett_'+str(rng.randrange(4)),p+.002,q-.002,v0+.002,v1-.002,
                 .181+rng.uniform(-.001,.001),.003)
            p = q

    setts(side0,side0+.11)
    setts(side1-.11,side1)
    for j in range(nflags):
        left = side0+.11+j*band
        right = left+band
        inner_strip = .09 if j < nflags-1 and band > .72 else 0
        if inner_strip:
            setts(right-inner_strip,right)
        p = start
        # Half-slab offset every other band, with cut flags at block ends.
        if j%2:
            q = min(end,p+.375)
            tile('Slab_'+str(rng.randrange(6)),p+.002,q-.002,left+.003,right-inner_strip-.003,
                 .18+rng.uniform(-.0008,.0008),.003)
            p = q
        while p < end-.015:
            q = min(end,p+.75)
            if q-p > .025:
                tile('Slab_'+str(rng.randrange(6)),p+.002,q-.002,left+.003,right-inner_strip-.003,
                     .18+rng.uniform(-.0008,.0008),.003)
            p = q


def _kerb_run(batch, rng, x0,x1,y0,y1,top,axis='y'):
    length0,length1 = (y0,y1) if axis=='y' else (x0,x1)
    p = length0
    while p < length1-.006:
        q = min(length1,p+rng.uniform(.80,1.18))
        key = 'Kerb_'+str(rng.randrange(3))
        stone_top=top+rng.uniform(-.0015,.0015)
        if axis=='y':
            batch.box(key,x0,x1,p+.004,q-.004,-.06,stone_top-.005)
            batch.tile(key,x0,x1,p+.004,q-.004,stone_top,.005)
        else:
            batch.box(key,p+.004,q-.004,y0,y1,-.06,stone_top-.005)
            batch.tile(key,p+.004,q-.004,y0,y1,stone_top,.005)
        p = q


def _bicycle_mark(batch, x,y,direction):
    z = .073
    # Deliberately small white outline stencil: two wheels, diamond frame,
    # seat, handlebar; an arrow makes the one-way track unambiguous.
    def pt(u,v):
        return x+direction*u,y+direction*v
    for u in (-.31,.31):
        xx,yy = pt(u,0)
        batch.ring('Road_paint',xx,yy,.205,.024,z,28)
    for points in [ [(-.31,0),(-.12,.30),(.10,0),(-.31,0)],
                    [(.10,0),(.20,.39),(.31,0)],
                    [(-.12,.30),(.20,.30)],
                    [(-.12,.30),(-.16,.40)],
                    [(-.25,.40),(-.07,.40)],
                    [(.20,.39),(.16,.47),(.31,.47)] ]:
        batch.line('Road_paint',[pt(*p) for p in points],.024,z)
    batch.line('Road_paint',[pt(0,.95),pt(0,1.75)],.055,z)
    batch.line('Road_paint',[pt(-.22,1.47),pt(0,1.75),pt(.22,1.47)],.055,z)


def _drain(batch,x,y):
    batch.box('Drain_dark',x-.205,x+.205,y-.34,y+.34,-.025,.002)
    for xa,xb,ya,yb in [(x-.205,x-.176,y-.34,y+.34),
                        (x+.176,x+.205,y-.34,y+.34),
                        (x-.176,x+.176,y-.34,y-.307),
                        (x-.176,x+.176,y+.307,y+.34)]:
        batch.box('Iron',xa,xb,ya,yb,.002,.011)
    for i in range(10):
        yy = y-.285+i*.063
        batch.box('Iron',x-.176,x+.176,yy-.015,yy+.015,.003,.010)
    batch.box('Iron',x-.012,x+.012,y-.307,y+.307,.003,.011)


def _manhole(batch,x,y,z=.008,r=.33):
    n=48
    vertices=[(x,y,z)]+[(x+r*math.cos(i*math.tau/n),y+r*math.sin(i*math.tau/n),z) for i in range(n)]
    batch.mesh('Iron',vertices,[(0,i+1,(i+1)%n+1) for i in range(n)])
    batch.ring('Drain_dark',x,y,r+.011,.019,z+.001,48)
    batch.ring('Iron_highlight',x,y,r-.018,.017,z+.003,48)
    batch.ring('Drain_dark',x,y,r-.065,.008,z+.003,40)
    # Low raised cast-iron grid, restrained enough to read as an actual cover.
    for k in range(-4,5):
        offset=k*.051
        half=math.sqrt(max(0,(r-.08)**2-offset**2))
        batch.line('Iron_highlight',[(x-half,y+offset),(x+half,y+offset)],.009,z+.004)
        batch.line('Iron_highlight',[(x+offset,y-half),(x+offset,y+half)],.009,z+.004)
    for dx in (-.15,.15):
        batch.quad('Drain_dark',x+dx-.025,x+dx+.025,y-.014,y+.014,z+.005)


def build_surfaces():
    """Replace blockout roads with finished metric surfaces; return summary."""
    for name in ('Blockout_Roads','CPH_Street_Surfaces'):
        old=bpy.data.collections.get(name)
        if old:
            for obj in list(old.all_objects):
                bpy.data.objects.remove(obj,do_unlink=True)
            bpy.data.collections.remove(old)
    collection=bpy.data.collections.new('CPH_Street_Surfaces')
    bpy.context.scene.collection.children.link(collection)
    collection['description']='Raised Copenhagen cycle tracks; concrete flags and granite setts; metric materials'
    rng=random.Random(61721)
    batch=_Batch()
    mats={
        'Asphalt':_material('Asphalt',(.062,.063,.061),.88,112,.003,.025,aggregate=.37),
        'Cycle_asphalt':_material('Cycle_asphalt',(.057,.061,.062),.86,130,.0025,.022,aggregate=.32),
        'Asphalt_patch':_material('Asphalt_patch',(.053,.055,.054),.88,125,.0028,.025,aggregate=.34),
        'Asphalt_patch_old':_material('Asphalt_patch_old',(.067,.067,.064),.90,112,.003,.025,aggregate=.32),
        'Asphalt_crack':_material('Asphalt_crack',(.026,.027,.025),.95,90,.001,.08),
        'Joint_bed':_material('Joint_bed',(.13,.132,.122),.96,100,.001,.12),
        'Blue_crossing':_material('Blue_crossing',(.055,.195,.29),.82,110,.0024,.09),
        'Road_paint':_material('Road_paint',(.66,.665,.627),.73,120,.0011,.06),
        'Iron':_material('Iron',(.052,.058,.057),.77,85,.0017,.13,.55),
        'Iron_highlight':_material('Iron_highlight',(.085,.09,.085),.68,100,.001,.12,.6),
        'Drain_dark':_material('Drain_dark',(.011,.014,.013),.9,90,.0008,.07),
    }
    for i,value in enumerate((.287,.291,.295,.299,.303,.307)):
        mats['Slab_'+str(i)]=_material('Slab_'+str(i),(value*1.025,value*1.014,value*.971),
                                      .84+(i%3)*.023,135,.0017,.018,aggregate=.105)
    for i,value in enumerate((.225,.24,.255,.27)):
        mats['Sett_'+str(i)]=_material('Sett_'+str(i),(value*1.035,value*1.012,value*.98),
                                     .87,95,.0024,.035,aggregate=.20)
    for i,value in enumerate((.185,.202,.22)):
        mats['Kerb_'+str(i)]=_material('Kerb_'+str(i),(value*1.04,value*1.012,value*.965),
                                     .87,105,.002,.035,aggregate=.22)

    junctions=(-40,52)
    gaps=[(y-5.5,y+5.5) for y in junctions]
    segments=list(_intervals(-65,125,gaps))
    batch.box('Asphalt',-2.8,2.8,-65,125,-.18,0)
    for cy in junctions:
        # Split the junction arms to avoid coincident main-road faces.
        for x0,x1 in [(-80,-2.8),(2.8,80)]:
            batch.box('Asphalt',x0,x1,cy-3.2,cy+3.2,-.18,0)
        for x0,x1 in [(-80,-5.6),(5.6,80)]:
            for side in (-1,1):
                lo,hi=sorted((cy+side*3.37,cy+side*5.5))
                _paving(batch,rng,x0,x1,lo,hi,'x')
                klo,khi=sorted((cy+side*3.2,cy+side*3.37))
                _kerb_run(batch,rng,x0,x1,klo,khi,.185,'x')
        for side in (-1,1):
            x0,x1=sorted((side*2.95,side*5.45))
            batch.quad('Blue_crossing',x0,x1,cy-3.2,cy+3.2,.005)
            # Shallow track ramps lower cyclists to carriageway level.
            for d in (-1,1):
                a,b=cy+d*3.2,cy+d*5.5
                batch.mesh('Cycle_asphalt',[(x0,a,.002),(x1,a,.002),
                                            (x1,b,.07),(x0,b,.07)],
                           [(0,1,2,3)] if d==1 else [(3,2,1,0)])
                # The kerbs taper into the junction as well; there are no
                # exposed ground slots where the raised tracks meet the road.
                for near,far,height in ((2.8,2.95,.075),(5.45,5.6,.185)):
                    k0,k1=sorted((side*near,side*far))
                    batch.mesh('Kerb_1',[(k0,a,.003),(k1,a,.003),
                                         (k1,b,height),(k0,b,height)],
                               [(0,1,2,3)] if d==1 else [(3,2,1,0)])
            # Crossing edge guide dashes: white is confined to the junction.
            for yy in [cy-2.7+j*.95 for j in range(6)]:
                for xx in (x0+.04,x1-.10):
                    batch.quad('Road_paint',xx,xx+.055,yy,yy+.36,.008)
        # Two simple zebra crossings, connecting the actual corner sidewalks.
        for d in (-1,1):
            y0,y1=sorted((cy+d*3.5,cy+d*5.1))
            for j in range(6):
                x0=-2.55+j*.88
                batch.quad('Road_paint',x0,x0+.46,y0,y1,.0055)
            for side in (-1,1):
                for j in range(3):
                    x0=side*(3.03+j*.79)
                    if side<0:
                        x0-=.40
                    # Paint follows track ramp exactly instead of floating.
                    z0=.002+.068*abs(y0-(cy+d*3.2))/2.3+.003
                    z1=.002+.068*abs(y1-(cy+d*3.2))/2.3+.003
                    batch.mesh('Road_paint',[(x0,y0,z0),(x0+.40,y0,z0),
                                             (x0+.40,y1,z1),(x0,y1,z1)],[(0,1,2,3)])

    for y0,y1 in segments:
        for side in (-1,1):
            cx0,cx1=sorted((side*2.95,side*5.45))
            batch.box('Cycle_asphalt',cx0,cx1,y0,y1,-.10,.07)
            k0,k1=sorted((side*2.8,side*2.95))
            _kerb_run(batch,rng,k0,k1,y0,y1,.075)
            k0,k1=sorted((side*5.45,side*5.6))
            _kerb_run(batch,rng,k0,k1,y0,y1,.185)
            sx0,sx1=sorted((side*5.6,side*9))
            _paving(batch,rng,sx0,sx1,y0,y1)

    # Sparse bicycle stencils, pointing with right-hand traffic.
    for y in (-57,-23,5,32,71,101):
        _bicycle_mark(batch,4.17,y,1)
        _bicycle_mark(batch,-4.17,y+4,-1)

    # Asphalt repairs have subtle value changes and credible cut edges.
    for i in range(19):
        x=rng.uniform(-2.05,2.05)
        y=rng.uniform(-61,119)
        width=rng.uniform(.45,1.03)
        length=rng.uniform(.8,2.1)
        z=.0025
        corners=[(x-width/2,y-length/2,z),(x+width/2-.05,y-length/2-.035,z),
                 (x+width/2,y+length/2-.06,z),(x-width/2+.03,y+length/2,z)]
        batch.mesh('Asphalt_patch' if i%3 else 'Asphalt_patch_old',corners,[(0,1,2,3)])
        if i%3==0:
            batch.line('Asphalt_crack',[(p[0],p[1]) for p in corners+[corners[0]]],.006,.004)
    for i in range(48):
        x=rng.uniform(-2.63,2.63)
        y=rng.uniform(-63,122)
        points=[(x,y)]
        for j in range(rng.randint(3,6)):
            x+=rng.uniform(-.11,.11)
            y+=rng.uniform(.10,.31)
            points.append((x,y))
        batch.line('Asphalt_crack',points,rng.uniform(.004,.009),.003)
        if i%5==0:
            a=points[1]
            batch.line('Asphalt_crack',[a,(a[0]+.18,a[1]+.12),(a[0]+.23,a[1]+.27)],.004,.003)

    for y in range(-59,124,15):
        if min(abs(y-cy) for cy in junctions)>6:
            for side in (-1,1):
                _drain(batch,side*2.49,y+(1.4 if side<0 else 0))
    for cy in junctions:
        for x in (-17,18):
            _drain(batch,x,cy+2.79)
            _drain(batch,x+1.6,cy-2.79)
    for x,y in ((.85,-17),(-.65,12),(1.15,77),(-1.0,110)):
        _manhole(batch,x,y)
    for x,y in ((6.1,-7),(-6.25,28),(6.15,85)):
        _manhole(batch,x,y,.185,.25)

    faces=batch.finish(collection,mats)
    collection['face_count']=faces
    collection['paving_spec']='0.75m concrete flags, granite sett courses, 4–6mm joints'
    collection['curb_levels']='Road 0.00m / cycletrack 0.07m / footway 0.18m'
    return {'collection':collection.name,'objects':len(collection.objects),'faces':faces,
            'road_width_m':5.6,'cycletrack_width_m':2.5,'footway_width_m':3.4}
