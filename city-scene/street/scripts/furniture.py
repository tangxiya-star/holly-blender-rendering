"""Reusable Copenhagen bicycle and street-furniture assets.

Run build_furniture() inside Blender. One Blender unit is one metre. The
unlinked prototype collections are rendered only through placed instances.
Self-contained; safe to call again to replace only this module's objects.
"""
import bpy
import math
import random
from mathutils import Vector, Matrix


_P = "CPH_Furniture_"


def _material(name, color, roughness=0.5, metallic=0.0):
    material = bpy.data.materials.get(_P + name)
    if material is None:
        material = bpy.data.materials.new(_P + name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return material


class _Mesh:
    """Accumulate small parts into one mesh per material, preserving flat faces."""
    def __init__(self):
        self.parts = {}

    def add(self, material, vertices, faces, smooth=False):
        key = material.name
        if key not in self.parts:
            self.parts[key] = [material, [], [], []]
        data = self.parts[key]
        n = len(data[1])
        data[1].extend(vertices)
        data[2].extend([tuple(n + i for i in f) for f in faces])
        data[3].extend([smooth] * len(faces))

    def tube(self, points, radius, material, sides=8, cap=True):
        points = [Vector(p) for p in points]
        if len(points) < 2:
            return
        verts = []
        for i, point in enumerate(points):
            tangent = (points[min(i + 1, len(points) - 1)] -
                       points[max(i - 1, 0)]).normalized()
            cross = tangent.cross(Vector((1, 0, 0)))
            if cross.length < 0.01:
                cross = tangent.cross(Vector((0, 1, 0)))
            u = cross.normalized()
            v = tangent.cross(u).normalized()
            for j in range(sides):
                angle = 2 * math.pi * j / sides
                verts.append(tuple(point + radius * (math.cos(angle) * u + math.sin(angle) * v)))
        faces = []
        for i in range(len(points) - 1):
            for j in range(sides):
                faces.append((i*sides+j, i*sides+(j+1)%sides,
                              (i+1)*sides+(j+1)%sides, (i+1)*sides+j))
        if cap:
            faces += [tuple(reversed(range(sides))),
                      tuple((len(points)-1)*sides+j for j in range(sides))]
        self.add(material, verts, faces, True)

    def bar(self, a, b, radius, material, sides=8):
        self.tube([a, b], radius, material, sides)

    def box(self, center, size, material):
        x, y, z = center
        a, b, c = [v/2 for v in size]
        verts = [(x-a,y-b,z-c), (x+a,y-b,z-c), (x+a,y+b,z-c), (x-a,y+b,z-c),
                 (x-a,y-b,z+c), (x+a,y-b,z+c), (x+a,y+b,z+c), (x-a,y+b,z+c)]
        self.add(material, verts, [(0,3,2,1),(4,5,6,7),(0,1,5,4),
                                  (1,2,6,5),(2,3,7,6),(3,0,4,7)])

    def ellipsoid(self, center, radii, material, segments=24, rings=10):
        verts, faces = [], []
        for i in range(rings+1):
            phi = math.pi*i/rings
            for j in range(segments):
                theta = math.tau*j/segments
                verts.append((center[0]+radii[0]*math.sin(phi)*math.cos(theta),
                              center[1]+radii[1]*math.sin(phi)*math.sin(theta),
                              center[2]+radii[2]*math.cos(phi)))
        for i in range(rings):
            for j in range(segments):
                faces.append((i*segments+j,i*segments+(j+1)%segments,
                              (i+1)*segments+(j+1)%segments,(i+1)*segments+j))
        self.add(material, verts, faces, True)

    def wheelring(self, center, radius, tube_radius, material, segments=56, profile=8):
        # Wheel axis X, bicycle travels along local Y.
        verts, faces = [], []
        for i in range(segments):
            t = math.tau*i/segments
            for j in range(profile):
                a = math.tau*j/profile
                rr = radius+tube_radius*math.cos(a)
                verts.append((center[0]+tube_radius*math.sin(a),
                              center[1]+rr*math.cos(t),center[2]+rr*math.sin(t)))
        for i in range(segments):
            for j in range(profile):
                faces.append((i*profile+j,((i+1)%segments)*profile+j,
                              ((i+1)%segments)*profile+(j+1)%profile,i*profile+(j+1)%profile))
        self.add(material, verts, faces, True)

    def finish(self, name, collection):
        objects = []
        for key, (material, verts, faces, smooth) in self.parts.items():
            mesh = bpy.data.meshes.new(_P+name+"_"+key)
            mesh.from_pydata(verts, [], faces)
            mesh.materials.append(material)
            mesh.update()
            obj = bpy.data.objects.new(_P+name+"_"+key, mesh)
            collection.objects.link(obj)
            for polygon, is_smooth in zip(mesh.polygons, smooth):
                polygon.use_smooth = is_smooth
            objects.append(obj)
        return objects


def _bike(name, frame_material, materials, step_through=False, basket=False):
    collection = bpy.data.collections.new(_P+"Asset_"+name)
    collection["asset_kind"] = "Reusable upright city bicycle"
    b = _Mesh()
    rubber, chrome, black, leather, reflector = [materials[k] for k in
                                               ("rubber","chrome","black","leather","reflector")]
    centers = [(0,-.56,.351), (0,.53,.351)]
    for wheel in centers:
        b.wheelring(wheel,.326,.025,rubber)
        b.wheelring(wheel,.306,.008,chrome)
        b.wheelring(wheel,.294,.0035,black)
        b.bar((-.042,wheel[1],wheel[2]),(.042,wheel[1],wheel[2]),.025,chrome,12)
        for spoke in range(28):
            theta = math.tau*spoke/28
            angle = theta + (0.16 if spoke%2 else -0.16)
            b.bar((.024 if spoke%2 else -.024,wheel[1]+.018*math.cos(theta),wheel[2]+.018*math.sin(theta)),
                  (0,wheel[1]+.301*math.cos(angle),wheel[2]+.301*math.sin(angle)),.00165,chrome,5)
        # Thin mudguard hugs the upper half of each wheel, with metal stays.
        pts = [(0,wheel[1]+.365*math.cos(t),wheel[2]+.365*math.sin(t))
               for t in [math.radians(-12+204*i/32) for i in range(33)]]
        # Three close tubes read as a curved narrow fender rather than a thick torus.
        for xx in [-.016,0,.016]:
            b.tube([(xx,p[1],p[2]) for p in pts],.009,frame_material,8)
        for end_t in [math.radians(20), math.radians(156)]:
            for xx in [-.036,.036]:
                b.bar((xx,wheel[1],wheel[2]),(xx,wheel[1]+.36*math.cos(end_t),wheel[2]+.36*math.sin(end_t)),.0035,chrome,6)
    rear = (0,-.56,.351)
    crank = (0,-.06,.335)
    seat = (0,-.22,.866)
    head_low, head_high = (0,.354,.734),(0,.277,.974)
    b.bar(crank,seat,.017,frame_material,12)
    b.bar(head_low,head_high,.02,frame_material,12)
    b.bar(crank,head_low,.019,frame_material,12)
    if step_through:
        b.tube([seat,(0,-.18,.61),(0,-.05,.49),(0,.12,.50),head_high],.015,frame_material,12)
    else:
        b.bar((0,-.218,.845),(0,.286,.945),.016,frame_material,12)
    for xx in [-.036,.036]:
        b.bar((xx,-.56,.351),(xx,-.22,.80),.012,frame_material,10)
        b.bar((xx,-.56,.351),(xx,-.06,.335),.012,frame_material,10)
        b.tube([(xx,.348,.754),(xx,.43,.49),(xx,.53,.351)],.012,frame_material,10)
    b.bar((0,-.22,.846),(0,-.244,.982),.012,chrome,12)
    # Broad rear and narrower nose of a practical leather saddle.
    b.ellipsoid((0,-.25,.984),(.105,.123,.034),leather)
    b.ellipsoid((0,-.16,.982),(.045,.107,.025),leather)
    b.bar((0,.282,.95),(0,.239,1.113),.013,chrome,12)
    b.tube([(-.32,.10,1.085),(-.25,.075,1.09),(-.17,.18,1.11),
            (0,.24,1.113),(.17,.18,1.11),(.25,.075,1.09),(.32,.10,1.085)],.012,chrome,10)
    for xx in [-1,1]:
        b.bar((xx*.255,.078,1.089),(xx*.331,.104,1.083),.017,rubber,10)
        b.tube([(xx*.218,.099,1.067),(xx*.188,.155,1.02),(xx*.045,.33,.87),
                (xx*.027,.45,.61)],.0024,black,5)
    # Chainring axis X and opposite crank arms / rubber pedals.
    b.wheelring((.049,-.06,.335),.081,.007,chrome,32,6)
    b.wheelring((.052,-.56,.351),.039,.006,chrome,24,6)
    b.tube([(.052,-.56,.394),(.052,-.06,.416),(.052,.018,.35),
            (.052,-.06,.254),(.052,-.56,.312),(.052,-.598,.35),(.052,-.56,.394)],.0035,black,5)
    for s in [-1,1]:
        yy=-.06+s*.12
        zz=.335+s*.075
        b.bar((s*.064,-.06,.335),(s*.064,yy,zz),.009,chrome,8)
        b.bar((s*.065,yy,zz),(s*.126,yy,zz),.007,chrome,8)
        b.box((s*.128,yy,zz),(.079,.061,.023),rubber)
        b.box((s*.128,yy+.032,zz),(.043,.004,.009),materials["amber"])
    # Rear luggage rack, fork-mounted lamp, stand, small rear reflector.
    for xx in [-.085,.085]:
        b.tube([(xx,-.765,.767),(xx,-.79,.793),(xx,-.39,.793),(xx,-.36,.767)],.006,chrome,7)
        b.bar((xx,-.70,.785),(xx,-.56,.37),.005,chrome,6)
    for yy in [-.74,-.65,-.55,-.43]:
        b.bar((-.085,yy,.79),(.085,yy,.79),.0045,chrome,6)
    b.ellipsoid((0,.485,.739),(.029,.035,.029),chrome,16,8)
    b.ellipsoid((0,.514,.741),(.023,.006,.023),materials["lampglass"],16,8)
    b.box((0,-.81,.778),(.045,.011,.022),reflector)
    b.bar((-.025,-.08,.35),(-.18,-.15,.015),.007,black,8)
    if basket:
        # Open wire basket with narrow rails; no solid block in front of the rider.
        for zz in [.81, .91, 1.025]:
            b.tube([(-.20,.35,zz),(.20,.35,zz),(.20,.67,zz),(-.20,.67,zz),(-.20,.35,zz)],.005,black,6)
        for xx in [-.20,-.12,-.04,.04,.12,.20]:
            b.bar((xx,.35,.81),(xx,.35,1.025),.0025,black,5)
            b.bar((xx,.67,.81),(xx,.67,1.025),.0025,black,5)
            b.bar((xx,.35,.81),(xx,.67,.81),.0025,black,5)
        for yy in [.39,.47,.55,.63]:
            for xx in [-.20,.20]:
                b.bar((xx,yy,.81),(xx,yy,1.025),.0025,black,5)
        b.bar((0,.39,.77),(0,.48,.81),.008,chrome,8)
    b.finish(name,collection)
    return collection


def _instance(name, asset, collection, location, yaw=0):
    obj=bpy.data.objects.new(_P+name,None)
    obj.instance_type="COLLECTION"
    obj.instance_collection=asset
    obj.location=location
    obj.rotation_euler.z=yaw
    collection.objects.link(obj)
    return obj


def _bench(materials):
    collection=bpy.data.collections.new(_P+"Asset_Bench")
    b=_Mesh()
    for yy in [-.61,.61]:
        b.tube([(-.20,yy,.025),(-.18,yy,.45),(.22,yy,.45),(.24,yy,.90)],.026,materials["black"],10)
        b.bar((.19,yy,.44),(.22,yy,.025),.023,materials["black"],10)
    for xx in [-.18,-.09,0,.09,.18]:
        b.box((xx,0,.464),(.075,1.55,.045),materials["wood"])
    for zz in [.63,.75,.87]:
        b.box((.233,0,zz),(.035,1.55,.09),materials["wood"])
    for yy in [-.70,.70]:
        b.tube([(-.18,yy,.48),(-.18,yy,.665),(.22,yy,.665)],.018,materials["black"],8)
    b.finish("Bench",collection)
    return collection


def _bin(materials):
    collection=bpy.data.collections.new(_P+"Asset_Bin")
    b=_Mesh()
    # Open cavity between bin body and hovering rain hood.
    b.bar((0,0,.06),(0,0,.60),.205,materials["black"],40)
    b.bar((0,0,.60),(0,0,.619),.186,materials["rubber"],40)
    b.bar((0,0,.75),(0,0,.779),.228,materials["black"],40)
    for a in [0,math.pi]:
        b.bar((.19*math.cos(a),.19*math.sin(a),.59),(.19*math.cos(a),.19*math.sin(a),.752),.014,materials["black"],8)
    b.bar((0,0,.025),(0,0,.08),.17,materials["black"],40)
    b.finish("Bin",collection)
    return collection


def _street_plaque(collection, side, y, label, materials):
    x=side*8.968
    b=_Mesh()
    b.box((x,y,3.18),(.035,1.35,.245),materials["blue"])
    b.finish("Plaque_"+label,collection)
    curve=bpy.data.curves.new(_P+"PlaqueText",type="FONT")
    curve.body=label
    curve.size=.092
    curve.space_character=1.1
    curve.align_x="CENTER"
    curve.align_y="CENTER"
    curve.extrude=.0004
    curve.materials.append(materials["letter"])
    text=bpy.data.objects.new(_P+"Street_"+label,curve)
    collection.objects.link(text)
    # Local text X runs along the wall; local +Z faces the street.
    local_x=Vector((0,-side,0))
    local_y=Vector((0,0,1))
    normal=local_x.cross(local_y)
    text.rotation_euler=Matrix((local_x,local_y,normal)).transposed().to_euler()
    text.location=(x-side*.02,y,3.18)


def _tapered_branch(mesh, points, radii, material, sides=9):
    points=[Vector(p) for p in points]
    vertices,faces=[],[]
    for i,point in enumerate(points):
        direction=(points[min(i+1,len(points)-1)]-points[max(i-1,0)]).normalized()
        u=direction.cross(Vector((1,0,0)))
        if u.length<.01:
            u=direction.cross(Vector((0,1,0)))
        u.normalize()
        v=direction.cross(u).normalized()
        for j in range(sides):
            angle=math.tau*j/sides
            # Fine longitudinal irregularity avoids a perfectly turned trunk.
            radius=radii[i]*(1+.075*math.sin(j*4.1+i*.37))
            vertices.append(tuple(point+radius*(math.cos(angle)*u+math.sin(angle)*v)))
    for i in range(len(points)-1):
        for j in range(sides):
            faces.append((i*sides+j,i*sides+(j+1)%sides,
                          (i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    faces.append(tuple((len(points)-1)*sides+j for j in range(sides)))
    mesh.add(material,vertices,faces,True)


def _linden_tree(materials):
    """A compact street-tree asset with attached branches and individual leaves.

    Crown construction is botanical branch hierarchy, not disconnected sphere
    scatter. About 50k polygons in one unlinked prototype, instanced twice.
    """
    collection=bpy.data.collections.new(_P+"Asset_LindenTree")
    mesh=_Mesh()
    rng=random.Random(60952)
    bark=_material("LindenBark",(.115,.104,.083),.91)
    nodes=bark.node_tree.nodes
    links=bark.node_tree.links
    shader=nodes.get("Principled BSDF")
    if not nodes.get("BarkFineNoise"):
        noise=nodes.new("ShaderNodeTexNoise")
        noise.name="BarkFineNoise"
        noise.inputs["Scale"].default_value=65
        noise.inputs["Detail"].default_value=3
        bump=nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value=.3
        bump.inputs["Distance"].default_value=.009
        links.new(noise.outputs["Fac"],bump.inputs["Height"])
        links.new(bump.outputs["Normal"],shader.inputs["Normal"])
    leaf_materials=[]
    for i,color in enumerate([(.065,.113,.027),(.080,.132,.034),(.094,.145,.044),(.045,.086,.019)]):
        leaf_material=_material("LindenLeaf_%d"%i,color,.62)
        leaf_shader=leaf_material.node_tree.nodes.get("Principled BSDF")
        if "Subsurface Weight" in leaf_shader.inputs:
            leaf_shader.inputs["Subsurface Weight"].default_value=.035
        leaf_materials.append(leaf_material)

    def crown_point(point):
        # Keep foliage on the street side of the facades at x +/-9 m.
        point=Vector(point)
        point.x=max(-1.23,min(1.23,point.x))
        point.y=max(-1.53,min(1.53,point.y))
        point.z=max(3.1,min(6.66,point.z))
        return point

    trunk=[(0,0,0),(.012,-.013,.75),(-.018,.01,1.65),(.025,.024,2.65),
           (.018,.011,3.65),(.080,-.027,4.65),(.041,-.013,5.55),(.12,.03,6.60)]
    _tapered_branch(mesh,trunk,[.135,.119,.104,.088,.070,.048,.025,.007],bark,14)

    leaf_count=0
    # Branch levels and a golden-angle arrangement leave gaps between foliage.
    for i in range(14):
        azimuth=i*2.399963+rng.uniform(-.24,.24)
        level=2.93+(i/13)*2.75
        radial=1.02 if level<5.1 else .62
        radial*=rng.uniform(.82,1.11)
        base=Vector((.03,.012,level))
        direction=Vector((math.cos(azimuth)*.88,math.sin(azimuth),0))
        elbow=base+direction*radial*.44+Vector((0,0,.40))
        tip=crown_point(base+direction*radial+Vector((0,0,.66)))
        primary=[base,elbow,tip]
        thickness=.038 if level<4.5 else .025
        _tapered_branch(mesh,primary,[thickness,thickness*.64,.011],bark,9)
        for j in range(5):
            fraction=.29+j*.145
            junction=base.lerp(tip,fraction)+Vector((0,0,.10))
            fan=azimuth+(j-2)*.51+rng.uniform(-.19,.19)
            second_dir=Vector((math.cos(fan)*.86,math.sin(fan),0))
            end=crown_point(junction+second_dir*rng.uniform(.34,.63)+Vector((0,0,rng.uniform(.18,.43))))
            middle=junction.lerp(end,.50)+Vector((0,0,.075))
            _tapered_branch(mesh,[junction,middle,end],[.012,.007,.0038],bark,7)
            for k in range(4):
                attach=junction.lerp(end,.34+k*.185)
                angle=fan+(k-1.5)*.68+rng.uniform(-.16,.16)
                twig_dir=Vector((math.cos(angle),math.sin(angle),0))
                twig_end=crown_point(attach+twig_dir*rng.uniform(.19,.34)+Vector((0,0,rng.uniform(.08,.25))))
                twig_mid=attach.lerp(twig_end,.53)+Vector((0,0,.035))
                _tapered_branch(mesh,[attach,twig_mid,twig_end],[.0045,.0027,.0012],bark,5)
                for leaf_index in range(10):
                    t=.10+leaf_index*.089
                    if t<.53:
                        stem_start=attach.lerp(twig_mid,t/.53)
                    else:
                        stem_start=twig_mid.lerp(twig_end,(t-.53)/.47)
                    side=-1 if leaf_index%2 else 1
                    outward=Vector((math.cos(angle+side*1.06),math.sin(angle+side*1.06),rng.uniform(-.12,.24)))
                    outward.normalize()
                    origin=stem_start+outward*.021
                    mesh.bar(stem_start,origin,.0008,bark,5)
                    long_axis=(outward+Vector((0,0,rng.uniform(-.45,.48)))).normalized()
                    normal=Vector((rng.uniform(-.45,.45),rng.uniform(-.45,.45),1)).normalized()
                    cross=long_axis.cross(normal)
                    if cross.length<.01:
                        cross=long_axis.cross(Vector((1,0,0)))
                    cross.normalize()
                    normal=cross.cross(long_axis).normalized()
                    length=rng.uniform(.079,.123)
                    width=length*rng.uniform(.69,.89)
                    # Heart-shaped linden leaf: notched base, broad lobes, pointed tip.
                    outline=[(0,0),(-.43,-.025),(-.55,.29),(-.34,.70),
                             (0,1),(.32,.72),(.53,.31),(.44,-.035)]
                    vertices=[tuple(origin+long_axis*length*.40+normal*.009)]
                    for xx,yy in outline:
                        bend=.004*math.sin(yy*math.pi)
                        vertices.append(tuple(origin+cross*width*xx+long_axis*length*yy+normal*bend))
                    faces=[(0,1+n,1+(n+1)%8) for n in range(8)]
                    mesh.add(leaf_materials[(leaf_index+i+j)%4],vertices,faces,True)
                    leaf_count+=1
    mesh.finish("LindenTree",collection)
    collection["leaf_count"]=leaf_count
    collection["height_m"]=6.8
    collection["construction"]="Tapered trunk, attached branches and twigs, bent heart-shaped leaf meshes"
    return collection


def build_furniture():
    """Create 26 instanced bicycles, four suspended lamps and restrained furniture."""
    for obj in list(bpy.data.objects):
        if obj.name.startswith(_P):
            bpy.data.objects.remove(obj,do_unlink=True)
    for collection in list(bpy.data.collections):
        if collection.name.startswith(_P):
            bpy.data.collections.remove(collection)
    street=bpy.data.collections.new(_P+"Street")
    bpy.context.scene.collection.children.link(street)
    street["reference"]="Representative inner Copenhagen; see references/reference_analysis.md"
    materials={
        "rubber":_material("TireRubber",(.012,.014,.016),.88),
        "chrome":_material("BrushedSteel",(.42,.47,.48),.26,.82),
        "black":_material("GraphiteEnamel",(.032,.043,.041),.48,.58),
        "leather":_material("SaddleLeather",(.105,.068,.039),.62),
        "reflector":_material("RearReflector",(.34,.018,.014),.22,.1),
        "amber":_material("PedalReflector",(.62,.30,.035),.29),
        "lampglass":_material("LampGlass",(.64,.67,.65),.18),
        "wood":_material("DarkOiledWood",(.125,.095,.062),.72),
        "blue":_material("StreetSignBlue",(.015,.055,.11),.43,.32),
        "letter":_material("SignLetters",(.83,.84,.80),.48),
        "shade":_material("StreetLampShade",(.13,.16,.17),.58,.62),
        "planter":_material("PlanterClay",(.225,.19,.16),.82),
        "soil":_material("PottingSoil",(.048,.038,.023),.98),
        "leaf":_material("PlanterLeaves",(.073,.118,.038),.79),
    }
    colors=[(.024,.052,.041),(.034,.041,.055),(.22,.055,.034),(.21,.23,.21)]
    assets=[_bike("Bicycle_%02d"%i,_material("BikeFrame_%d"%i,c,.33,.58),materials,
                  step_through=i in [0,2],basket=i in [0,3]) for i,c in enumerate(colors)]
    rng=random.Random(7301)
    # The hero group has deliberate breathing room and a noticeably turned bike.
    # Even its 0.65-radian bicycle remains outside the clear x[-7.1,-5.6] walkpath.
    placements=[(-7.80,-16,.18,-.25),(-7.93,-12,.18,.65),(-7.66,-9,.18,.08)]
    # Each group fits between junction exclusion zones and leaves clear walking space.
    groups=[(1,8,4),(-1,22,4),(1,34,4),(-1,73,5),(1,93,6)]
    for side,center,count in groups:
        for j in range(count):
            yy=center+(j-(count-1)/2)*1.91+rng.uniform(-.14,.14)
            xx=side*(7.63+rng.uniform(-.15,.15))
            angle=rng.uniform(-.16,.16)+(math.pi if j%3==0 else 0)
            placements.append((xx,yy,.18,angle))
    for i,(x,y,z,yaw) in enumerate(placements):
        obj=_instance("ParkedBicycle_%02d"%i,assets[(i+i//3)%len(assets)],street,(x,y,z),yaw)
        obj["asset_type"]="upright_city_bicycle"
    benches=_bench(materials)
    bins=_bin(materials)
    for i,(side,yy) in enumerate([(-1,6),(1,79)]):
        _instance("Bench_%02d"%i,benches,street,(side*8.40,yy,.18),0 if side>0 else math.pi)
    for i,(side,yy) in enumerate([(-1,9),(1,82),(-1,27)]):
        _instance("Litterbin_%02d"%i,bins,street,(side*8.34,yy,.18))
    b=_Mesh()
    # A small number of cycle parking hoops parallel to the frontage.
    for side,yy in [(-1,-12),(-1,22),(1,8),(1,93)]:
        xx=side*7.88
        b.tube([(xx,yy-.40,.18),(xx,yy-.40,.88),(xx,yy-.34,.96),
                (xx,yy+.34,.96),(xx,yy+.40,.88),(xx,yy+.40,.18)],.022,materials["chrome"],10)
        for end in [-.4,.4]:
            b.box((xx,yy+end,.19),(.12,.12,.022),materials["chrome"])
    for yy in [-22,15,78,110]:
        points=[]
        for j in range(65):
            xx=-9+18*j/64
            zz=7.70+.80*(xx/9)**2
            points.append((xx,yy,zz))
        b.tube(points,.009,materials["black"],6)
        b.bar((0,yy,7.70),(0,yy,7.49),.011,materials["black"],8)
        # Revolved hemispherical shell, with a wide diffuse underside.
        verts,faces=[],[]
        profile=[(.025,7.65),(.12,7.63),(.23,7.57),(.31,7.48),(.355,7.37),(.36,7.335)]
        segments=40
        for radius,height in profile:
            for j in range(segments):
                a=math.tau*j/segments
                verts.append((radius*math.cos(a),yy+radius*math.sin(a),height))
        for i in range(len(profile)-1):
            for j in range(segments):
                faces.append((i*segments+j,i*segments+(j+1)%segments,
                              (i+1)*segments+(j+1)%segments,(i+1)*segments+j))
        b.add(materials["shade"],verts,faces,True)
        b.bar((0,yy,7.324),(0,yy,7.34),.337,materials["lampglass"],40)
        for side in [-1,1]:
            b.box((side*8.985,yy,8.50),(.035,.12,.17),materials["black"])
    # Two modest planted containers close to destination fronts.
    for side,yy in [(-1,2.4),(1,76.5)]:
        xx=side*8.42
        for dx in [-.245,.245]:
            b.box((xx+dx,yy,.47),(.06,.64,.56),materials["planter"])
        for dy in [-.29,.29]:
            b.box((xx,yy+dy,.47),(.49,.06,.56),materials["planter"])
        b.box((xx,yy,.705),(.45,.52,.045),materials["soil"])
        # Thin arching grasslike leaves; surfaces, not low-poly shrub spheres.
        for j in range(36):
            theta=rng.uniform(0,math.tau)
            rr=rng.uniform(0,.17)
            height=rng.uniform(.18,.47)
            start=Vector((xx+rr*math.cos(theta),yy+rr*math.sin(theta),.73))
            direction=Vector((math.cos(theta),math.sin(theta),0))
            sideways=Vector((-math.sin(theta),math.cos(theta),0))*.009
            mid=start+direction*.11+Vector((0,0,height*.74))
            tip=start+direction*.22+Vector((0,0,height*.84))
            b.add(materials["leaf"],[tuple(start-sideways),tuple(start+sideways),
                  tuple(mid+sideways*.62),tuple(mid-sideways*.62),tuple(tip)],[(0,1,2,3),(3,2,4)])
    b.finish("StreetFixtures",street)
    tree=_linden_tree(materials)
    for i,(side,yy,yaw) in enumerate([(-1,61.5,.035),(1,62.1,-.055)]):
        instance=_instance("LindenTree_%02d"%i,tree,street,(side*7.60,yy,.18),yaw)
        instance["asset_type"]="linden_style_street_tree"
    # Small permeable planting squares distinguish the trunk footing from paving.
    tree_bases=_Mesh()
    for side,yy in [(-1,61.5),(1,62.1)]:
        xx=side*7.60
        tree_bases.box((xx,yy,.183),(.95,1.16,.008),materials["soil"])
        for dx in [-.48,.48]:
            tree_bases.box((xx+dx,yy,.187),(.018,1.19,.02),materials["black"])
        for dy in [-.585,.585]:
            tree_bases.box((xx,yy+dy,.187),(.97,.018,.02),materials["black"])
    tree_bases.finish("TreeFootings",street)
    _street_plaque(street,-1,-29,"LILLE NØRREGADE",materials)
    _street_plaque(street,1,42.5,"TEGLSTRÆDE",materials)
    return {"collection":street.name,"bicycle_instances":len(placements),
            "bicycle_prototypes":len(assets),"suspended_lamps":4,"benches":2,"bins":3,
            "trees":2,"tree_leaves_per_prototype":tree["leaf_count"]}
