import bpy, math, random
from collections import defaultdict
from aerial_common import mesh, material, group

def polygon_mesh(name,features,z,collection,mat,coast=False):
    vs=[];fs=[]
    for a in features:
        for tri in a.get('triangles',[]):
            a0,b0,c0=tri
            up=(b0[0]-a0[0])*(c0[1]-a0[1])-(b0[1]-a0[1])*(c0[0]-a0[0])>0
            k=len(vs);vs.extend([(p[0],p[1],z) for p in tri]);fs.append((k,k+1,k+2) if up else (k+2,k+1,k))
        if coast:
            for ring in [a['outer']]+a.get('holes',[]):
                for p,q in zip(ring,ring[1:]+ring[:1]):
                    k=len(vs);vs.extend([(p[0],p[1],0),(q[0],q[1],0),(q[0],q[1],z),(p[0],p[1],z)]);fs.append((k,k+1,k+2,k+3))
    if vs:return mesh(name,vs,fs,collection,[mat])

def water_material():
    m=material('Water | Baltic harbor blue green',(.024,.061,.067),.23,.08)
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['IOR'].default_value=1.333;p.inputs['Transmission Weight'].default_value=.12
    geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=.43;noise.inputs['Detail'].default_value=2;noise.inputs['Roughness'].default_value=.65
    mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(.38,1.5,1)
    l.new(geo.outputs['Position'],mapping.inputs[0]);l.new(mapping.outputs[0],noise.inputs['Vector'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.085
    l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    slow=n.new('ShaderNodeTexNoise');slow.inputs['Scale'].default_value=.003;slow.inputs['Detail'].default_value=2;l.new(geo.outputs['Position'],slow.inputs[0])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.016,.040,.046,1);ramp.color_ramp.elements[1].color=(.037,.069,.067,1)
    l.new(slow.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color']);return m

def inside(pt,ring):
    x,y=pt;v=False
    for (ax,ay),(bx,by) in zip(ring,ring[1:]+ring[:1]):
        if ((ay>y)!=(by>y)) and x<(bx-ax)*(y-ay)/(by-ay)+ax:v=not v
    return v

def in_feature(pt,p):return inside(pt,p['outer']) and not any(inside(pt,h) for h in p.get('holes',[]))

def build_surfaces(geo,mats):
    polygon_mesh('Real coastlines | Zealand Amager and harbor islands',geo['land'],2,'01_Real_Geography',mats['ground'],True)
    water=water_material()
    mesh('Baltic sea and Copenhagen harbor',[(-45000,-45000,0),(45000,-45000,0),(45000,45000,0),(-45000,45000,0)],[(0,1,2,3)],'01_Real_Geography',[water])
    # Inland lakes are holes cut from the land by GIS preparation; this mesh preserves any elevated water definitions.
    polygon_mesh('Real inland lakes and canals',geo['water'],.05,'01_Real_Geography',water)
    polygon_mesh('Real parks gardens and green areas',geo['parks'],2.035,'01_Real_Geography',mats['park'])
    buckets={k:([],[]) for k in ['roads','paths','bridges']};bridge_count=0
    widths={'motorway':13,'motorway_link':6,'trunk':12,'trunk_link':5,'primary':11,'secondary':9,'tertiary':8,'residential':5.3,'living_street':4,'service':3.5,'unclassified':5.5,'pedestrian':5,'footway':2.0,'path':1.7,'cycleway':2.4,'track':3,'steps':1.5}
    for feat in geo['roads']:
        tags=feat.get('tags',{});kind=tags.get('highway','residential');pts=feat.get('points',[])
        if len(pts)<2 or tags.get('tunnel') in ['yes','building_passage']:continue
        ispath=kind in ['footway','cycleway','path','steps','pedestrian','track']
        bridge=tags.get('bridge','no') not in ['no','false','0','']
        if kind not in widths:continue
        width=widths[kind]
        try:width=min(24,max(1.2,float(tags['width'].split(' ')[0])))
        except (KeyError,ValueError,AttributeError):pass
        key='bridges' if bridge else ('paths' if ispath else 'roads');vs,fs=buckets[key]
        lengths=[0]
        for p,q in zip(pts,pts[1:]):lengths.append(lengths[-1]+math.dist(p,q))
        if bridge:bridge_count+=1
        for i,(x,y) in enumerate(pts):
            before=pts[max(0,i-1)];after=pts[min(len(pts)-1,i+1)];dx=after[0]-before[0];dy=after[1]-before[1];length=max(.01,math.hypot(dx,dy));nx=-dy/length*width/2;ny=dx/length*width/2
            z=2.1+(min(1,lengths[i]/20,(lengths[-1]-lengths[i])/20)*4 if bridge else 0)
            vs.extend([(x+nx,y+ny,z),(x-nx,y-ny,z)])
            if i: k=len(vs)-4;fs.append((k,k+1,k+3,k+2))
    for key,(vs,fs) in buckets.items():
        mesh('OSM '+key,vs,fs,'02_Roads_and_Bridges',[mats['paths'] if key=='paths' else mats['roads']])
    return {'land_polygons':len(geo['land']),'water_polygons':len(geo['water']),'park_polygons':len(geo['parks']),'road_segments':len(geo['roads']),'bridge_segments':bridge_count}

def tree_prototype(mat,trunk,i):
    vs=[];fs=[];mi=[]
    # Low polygon canopy clusters share geometry through GN instancing.
    rings=7;segments=8
    for center,scale in [((0,0,6.2),(3.1,2.8,4.1)),((-1.7,.1,5.5),(2.1,2.1,2.9)),((1.5,.6,6.1),(2.0,2.0,3.0))]:
        base=len(vs)
        for j in range(rings+1):
            theta=math.pi*j/rings
            for k in range(segments):
                phi=math.tau*k/segments
                vs.append(tuple(center[a]+scale[a]*v for a,v in enumerate((math.sin(theta)*math.cos(phi),math.sin(theta)*math.sin(phi),math.cos(theta)))))
        for j in range(rings):
            for k in range(segments):
                a=base+j*segments+k;b=base+j*segments+(k+1)%segments;c=b+segments;d=a+segments;fs.append((a,b,c,d));mi.append(0)
    base=len(vs)
    for z in [0,5]:
        for j in range(6):vs.append((.22*math.cos(j*math.tau/6),.22*math.sin(j*math.tau/6),z))
    for j in range(6):fs.append((base+j,base+(j+1)%6,base+(j+1)%6+6,base+j+6));mi.append(1)
    o=mesh('Instanced canopy source '+str(i),vs,fs,'03_Vegetation_Prototypes',[mat,trunk],mi);o.location=(0,0,-900)
    for p in o.data.polygons:p.use_smooth=True
    return o

def build_vegetation(geo,mats):
    rng=random.Random(6231);occupied=defaultdict(list)
    for b in geo['buildings']:
        ring=b['outer'];xs=[p[0] for p in ring];ys=[p[1] for p in ring]
        for x in range(math.floor(min(xs)/80),math.floor(max(xs)/80)+1):
            for y in range(math.floor(min(ys)/80),math.floor(max(ys)/80)+1):occupied[(x,y)].append(b)
    def free(p):return not any(in_feature(p,b) for b in occupied.get((math.floor(p[0]/80),math.floor(p[1]/80)),[]))
    points=[];taken=set();scales=[]
    def add(p,scale):
        key=(round(p[0]/5),round(p[1]/5))
        if key not in taken and free(p):taken.add(key);points.append((p[0],p[1],2.03));scales.append(scale)
    # Real OSM green polygons, explicitly no blanket sprinkling over water or roofs.
    parks=geo['parks']
    for p in parks:
        ring=p['outer'];xmin=min(q[0] for q in ring);xmax=max(q[0] for q in ring);ymin=min(q[1] for q in ring);ymax=max(q[1] for q in ring)
        area=(xmax-xmin)*(ymax-ymin);tags=p.get('tags',{})
        woodland=tags.get('natural') in ['wood','scrub'] or tags.get('landuse') in ['forest']
        n=min(5500,int(area/(130 if woodland else 310)))
        for _ in range(n):
            q=(rng.uniform(xmin,xmax),rng.uniform(ymin,ymax))
            if in_feature(q,p):add(q,rng.uniform(.65,1.38))
    # A small amount of garden canopy in true enclosed footprint courtyards.
    for b in geo['buildings']:
        for h in b.get('holes',[]):
            cx=sum(p[0] for p in h)/len(h);cy=sum(p[1] for p in h)/len(h)
            if inside((cx,cy),h):add((cx,cy),rng.uniform(.65,.95))
    if len(points)>38000:
        ids=rng.sample(range(len(points)),38000);points=[points[i] for i in ids];scales=[scales[i] for i in ids]
    pointmesh=mesh('Real green areas | canopy distribution',points,[],'03_Instanced_Vegetation')
    attr=pointmesh.data.attributes.new('canopy_scale','FLOAT','POINT')
    for d,v in zip(attr.data,scales):d.value=v
    for i,mat in enumerate(mats['foliage']):tree_prototype(mat,mats['trunk'],i)
    nodes=bpy.data.node_groups.new('Canopies | reusable geometry on real park points','GeometryNodeTree')
    nodes.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');nodes.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    n=nodes.nodes;l=nodes.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');ci=n.new('GeometryNodeCollectionInfo');ci.inputs['Collection'].default_value=group('03_Vegetation_Prototypes');ci.inputs['Separate Children'].default_value=True;ci.inputs['Reset Children'].default_value=True
    inst=n.new('GeometryNodeInstanceOnPoints');inst.inputs['Pick Instance'].default_value=True;l.new(inp.outputs['Geometry'],inst.inputs['Points']);l.new(ci.outputs['Instances'],inst.inputs['Instance'])
    attrnode=n.new('GeometryNodeInputNamedAttribute');attrnode.data_type='FLOAT';attrnode.inputs['Name'].default_value='canopy_scale';l.new(attrnode.outputs['Attribute'],inst.inputs['Scale'])
    rnd=n.new('FunctionNodeRandomValue');rnd.data_type='INT';rnd.inputs['Min'].default_value=0;rnd.inputs['Max'].default_value=3;l.new(rnd.outputs['Value'],inst.inputs['Instance Index'])
    rot=n.new('FunctionNodeRandomValue');rot.data_type='FLOAT_VECTOR';rot.inputs['Min'].default_value=(0,0,0);rot.inputs['Max'].default_value=(0,0,math.tau);l.new(rot.outputs['Value'],inst.inputs['Rotation'])
    l.new(inst.outputs['Instances'],out.inputs['Geometry']);mod=pointmesh.modifiers.new('Efficient canopy instances','NODES');mod.node_group=nodes
    return {'instanced_trees':len(points),'tree_prototypes':4}
