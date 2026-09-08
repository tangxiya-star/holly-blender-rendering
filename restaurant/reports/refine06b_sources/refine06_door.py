"""Photo-guided, fully dimensional entrance relief; no work at import time.

Call build_door({'bronze': material, 'recess': material, 'edge': material}).
Only REF06_Door_ objects are replaced. Legacy door geometry is retained hidden.
The photographed sculpture is interpreted from its visible front, not scanned.
"""
import math
import random


PREFIX = 'REF06_Door_'
WIDTH = 1.588


def _sample(points, spacing=.006):
    """Centrally clamped cubic path with explicit local width multipliers."""
    out = []
    for i in range(len(points)-1):
        p0, p1 = points[max(0, i-1)], points[i]
        p2, p3 = points[i+1], points[min(len(points)-1, i+2)]
        steps = max(4, math.ceil(math.hypot(p2[0]-p1[0], p2[1]-p1[1])/spacing))
        for j in range(steps):
            t = j/steps
            coords = tuple(.5*(2*p1[k]+(-p0[k]+p2[k])*t+
                (2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*t*t+
                (-p0[k]+3*p1[k]-3*p2[k]+p3[k])*t*t*t) for k in range(2))
            out.append((*coords, p1[2]*(1-t)+p2[2]*t))
    out.append(points[-1])
    return out


class _Geometry:
    def __init__(self):
        self.vertices = []
        self.faces = []
        self.wear = []
        self.cavity = []
        self.slots = []
        self.flat = []

    def vert(self, co, wear=.1, cavity=0):
        self.vertices.append(co)
        self.wear.append(min(1, max(0, wear)))
        self.cavity.append(min(1, max(0, cavity)))
        return len(self.vertices)-1

    def face(self, ids, slot=0, flat=False):
        self.faces.append(tuple(ids))
        self.slots.append(slot)
        self.flat.append(flat)

    def sweep(self, points, width, seed, detail=40, center=-.049, flat=.50,
              bark=True, taper=True):
        """Irregular cast branch with deeply fluted section and embedded back.

        Unlike a bevelled curve, the asymmetric section changes continuously,
        with open-looking folds, taper, swell and fine scalloped bark edges.
        The branch itself is nevertheless closed and has full back geometry.
        """
        from mathutils import Vector
        from mathutils.noise import noise_vector
        points = _sample(points, .005 if width>.07 else .007)
        offset = len(self.vertices)
        rand = random.Random(seed)
        phase = rand.random()*math.tau
        lobes = rand.choice((11, 13, 15, 17))
        for i, (x, z, scale) in enumerate(points):
            prev, nxt = points[max(0, i-1)], points[min(len(points)-1, i+1)]
            dx, dz = nxt[0]-prev[0], nxt[1]-prev[1]
            length = max(math.hypot(dx, dz), 1e-9)
            nx, nz = -dz/length, dx/length
            t = i/(len(points)-1)
            end = max(.035,min(1,t*15,(1-t)*18)**.65) if taper else 1
            rad = width*max(.1, scale)*end
            swell = 1+.10*math.sin(t*31+phase)+.045*math.sin(t*93+phase*.7)
            for j in range(detail):
                a = j*math.tau/detail
                # These furrows travel along, bend and divide around the trunk.
                drift = phase+t*5.1+.70*math.sin(t*13+phase)+.20*math.sin(t*53+phase)
                ridge = math.sin(a*lobes+drift)
                fine = math.sin(a*(lobes*2+1)-t*14+phase)
                furrow = math.copysign(abs(ridge)**.58, ridge)
                # Broad cactus-like corrugation is deliberately suppressed. The
                # short broken raised bark plates below now carry the detail.
                corr = 1 + (.065*furrow+.033*fine if bark else .02*ridge)
                nv = noise_vector(Vector((x*40+j*.07, z*40, seed*.37)))
                lateral = rad*math.cos(a)*swell*corr
                front = math.sin(a)
                depth = rad*flat*(1+.20*math.sin(t*11+phase))
                buried_center=-.028+(center+.028)*end if taper else center
                y = buried_center-depth*front*corr
                if bark:
                    y += .0024*nv.z*max(.3, abs(front))
                    lateral += .0017*nv.x
                self.vert((x+nx*lateral, y, z+nz*lateral),
                          .10+.65*max(0, front)*max(0, furrow),
                          .08+.70*max(0, -furrow)*max(0, front))
        for i in range(len(points)-1):
            for j in range(detail):
                a=offset+i*detail+j
                b=offset+i*detail+(j+1)%detail
                # Cross product faces toward the exposed -Y side.
                self.face((a, b, b+detail, a+detail))
        self.face(tuple(offset+j for j in reversed(range(detail))))
        end = offset+(len(points)-1)*detail
        self.face(tuple(end+j for j in range(detail)))
        if bark and width>.009:
            self.broken_bark(offset,len(points),detail,points,width,seed)
        return points

    def broken_bark(self, offset, stations, rings, points, width, seed):
        """Solid torn bark plates sampled directly from the parent cast skin.

        Surface attachment uses the exact generated vertex grid: varying parent
        depth, taper, fluting and local swell are all retained. Thousands of
        interrupted directional plates replace long buried decorative tubes.
        """
        rand=random.Random(seed+73251)
        distance=sum(math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(points,points[1:]))
        area=distance*width*2.0
        plate_count=max(8,int(area/.00057))
        self.bark_plate_count=getattr(self,'bark_plate_count',0)+plate_count
        # Front-half angular coordinates remain inside the parent's closed mesh.
        def skin(t,a):
            si=max(0,min(stations-1.001,t*(stations-1)))
            ri=(a%math.tau)*rings/math.tau
            s=int(si);r=int(ri)%rings;sf=si-s;rf=ri-int(ri)
            ids=(offset+s*rings+r,offset+s*rings+(r+1)%rings,
                 offset+(s+1)*rings+r,offset+(s+1)*rings+(r+1)%rings)
            v=[self.vertices[i] for i in ids]
            return tuple((v[0][k]*(1-rf)+v[1][k]*rf)*(1-sf)+
                         (v[2][k]*(1-rf)+v[3][k]*rf)*sf for k in range(3))
        for n in range(plate_count):
            t0=rand.uniform(.025,.95)
            physical_length=rand.uniform(.023,.080)*(1 if width>.06 else .72)
            dt=min(.25,physical_length/max(.02,distance))
            t0=min(t0,.985-dt)
            ac=rand.uniform(.12,math.pi-.12)
            # Narrow splinters and broad flakes overlap without a tiled lattice.
            physical_width=rand.uniform(.005,.020)*(.72 if n%7==0 else 1)
            da=min(.54,physical_width/max(.012,width))
            slant=rand.uniform(-.85,.85)
            height=rand.uniform(.0020,.0065)*(1.15 if width>.085 else .78)
            row_count=7;cols=5;begin=len(self.vertices)
            jagged=[rand.uniform(.68,1.21) for _ in range(row_count)]
            phase=rand.random()*math.tau
            for i in range(row_count):
                t=i/(row_count-1)
                # Splintered spear ends; one ragged shoulder is intentionally
                # broader, so these read as broken lamellae rather than scales.
                breadth=max(.055,math.sin(math.pi*t)**.44)*jagged[i]
                for j in range(cols):
                    cross=j/(cols-1)*2-1
                    angle=ac+slant*(t-.5)+cross*da*.5*breadth
                    st=t0+dt*t+cross*dt*.08*math.sin(t*7+phase)
                    x,y,z=skin(max(.001,min(.999,st)),angle)
                    lift=height*math.sin(math.pi*t)**.5*(.32+.68*(1-abs(cross))**.55)
                    # Torn transverse edge and one raised lip expose a deep
                    # narrow shadow gap beneath each fragment's local rim.
                    lip=height*.35*max(0,cross)*math.sin(math.pi*t)
                    wobble=.00055*math.sin(i*2.71+j*3.9+phase)
                    self.vert((x,y-.0009-lift-lip+wobble,z),
                              .14+.42*(1-abs(cross))*(.35+.65*t),
                              .1+.40*abs(cross))
            for i in range(row_count-1):
                for j in range(cols-1):
                    a=begin+i*cols+j
                    self.face((a,a+1,a+cols+1,a+cols),0,flat=(j==3 and n%3==0))
            boundary=[begin+j for j in range(cols)]
            boundary += [begin+i*cols+cols-1 for i in range(1,row_count)]
            boundary += [begin+(row_count-1)*cols+j for j in range(cols-2,-1,-1)]
            boundary += [begin+i*cols for i in range(row_count-2,0,-1)]
            bottom=[]
            for vi in boundary:
                x,y,z=self.vertices[vi]
                bottom.append(self.vert((x,y+.0018,z),.03,.75))
            for i,vi in enumerate(boundary):
                nxt=(i+1)%len(boundary)
                self.face((vi,bottom[i],bottom[nxt],boundary[nxt]),0,flat=True)
            self.face(tuple(reversed(bottom)),0,flat=True)

    def bark_sliver(self, points, width, seed, base_width):
        """A split lamella raised along the front of a trunk, closed underneath."""
        rand=random.Random(seed)
        start=rand.uniform(.06,.66)
        length=rand.uniform(.16,.36)
        count=len(points)
        i0=int(start*(count-1));i1=min(count-1,int((start+length)*(count-1)))
        if i1-i0<4:return
        lateral=rand.uniform(-.68,.68)
        a=math.asin(lateral)
        front=math.sqrt(1-lateral*lateral)
        lifted=[]
        for i in range(i0,i1+1,2):
            x,z,scale=points[i]
            prev,nxt=points[max(0,i-1)],points[min(count-1,i+1)]
            dx,dz=nxt[0]-prev[0],nxt[1]-prev[1]
            n=max(1e-8,math.hypot(dx,dz))
            spread=base_width*scale*lateral
            lifted.append((x-dz/n*spread,z+dx/n*spread,1))
        if len(lifted)<2:return
        self.sweep(lifted,width,seed,detail=10,
                   center=-.050-base_width*.51*front,
                   flat=.38,bark=False,taper=True)


def _network(side):
    """Normalized X/photo-Z control drawings. Left and right are distinct.

    Third coordinate is a local swelling multiplier. Branch roots overlap,
    with selected sections moving forward into sculptural crossing knots.
    """
    # Main long trunks are contiguous across some mouldings, as in the casting.
    left = [
        (.100,[(.24,.10,1.4),(.28,.42,1.1),(.24,.75,1.3),(.32,1.05,1),(.31,1.35,.8)]),
        (.125,[(.42,.12,1.0),(.39,.38,1.4),(.43,.67,1.1),(.42,.93,1),(.50,1.22,.7),(.57,1.38,.25)]),
        (.068,[(.94,.18,.3),(.71,.15,1),(.53,.24,1.0),(.43,.51,1),(.46,.72,.5)]),
        (.053,[(.46,.72,1),(.56,.88,.9),(.79,.95,.5),(.96,.98,.1)]),
        (.070,[(.31,1.33,.8),(.46,1.36,1),(.67,1.29,.8),(.78,1.25,.1)]),
        (.118,[(.39,1.43,1),(.40,1.71,1.1),(.32,1.92,1.3),(.35,2.20,1),(.33,2.49,.6)]),
        (.089,[(.53,1.41,.8),(.57,1.64,1.1),(.52,1.88,1.2),(.64,2.12,1),(.76,2.23,.4),(.98,2.34,.2)]),
        (.078,[(.24,1.97,.5),(.37,2.00,1),(.49,2.13,1),(.54,2.31,.65),(.53,2.49,.4)]),
        (.069,[(.16,1.46,.6),(.22,1.67,1),(.21,1.91,.8),(.27,2.23,1),(.24,2.48,.4)]),
        (.044,[(.57,1.44,.5),(.65,1.50,1),(.78,1.47,.7),(.97,1.48,.2)]),
        (.142,[(.49,2.59,.6),(.42,2.79,1.1),(.42,3.02,1.1),(.30,3.28,1.3),(.37,3.54,.5)]),
        (.085,[(.21,2.59,.45),(.29,2.79,1),(.32,3.01,1),(.27,3.27,.8),(.16,3.41,.5)]),
        (.085,[(.43,3.15,.8),(.58,3.22,1.1),(.79,3.29,.9),(.92,3.40,.6),(.91,3.51,.2)]),
        (.068,[(.41,3.45,.8),(.62,3.52,1),(.76,3.48,.85),(.82,3.40,.6),(.71,3.34,.3)]),
        (.098,[(.56,2.57,.6),(.67,2.72,1.1),(.72,2.89,1.2),(.85,2.93,.7),(.94,3.10,.4)]),
        (.064,[(.68,2.72,.6),(.55,2.79,1),(.51,2.99,.7),(.52,3.17,.4)]),
        (.057,[(.90,2.59,.4),(.87,2.76,1),(.92,2.91,.8),(.95,3.19,.5),(.93,3.43,.2)]),
        (.057,[(.08,3.06,.5),(.13,3.25,1),(.08,3.54,.7),(.07,3.85,.9),(.10,4.13,.2)]),
        (.058,[(.20,3.63,.6),(.15,3.78,1),(.16,3.94,.9),(.20,4.14,.3)]),
        (.044,[(.18,3.69,1),(.28,3.64,.8),(.43,3.63,.2)]),
        (.047,[(.92,3.62,.9),(.94,3.84,.65),(.96,4.12,.3)]),
        (.036,[(.91,3.68,1),(.80,3.65,.6),(.68,3.63,.2)]),
    ]
    right = [
        (.135,[(.29,.11,1.2),(.42,.29,1.3),(.53,.53,1.2),(.60,.84,1.1),(.60,1.12,.9),(.63,1.36,.4)]),
        (.102,[(.78,.12,1.2),(.69,.39,1.1),(.66,.71,1.0),(.67,.98,.7),(.71,1.37,.45)]),
        (.073,[(.12,.21,.3),(.30,.34,.8),(.45,.52,1),(.58,.71,.9),(.63,.94,.3)]),
        (.055,[(.11,.77,.2),(.26,.80,.8),(.40,.92,1),(.53,1.11,.5)]),
        (.070,[(.08,.15,.8),(.18,.43,1),(.21,.63,.8),(.15,.97,.4),(.13,1.33,.2)]),
        (.093,[(.39,1.43,.7),(.42,1.65,1.1),(.49,1.93,1.1),(.41,2.18,1),(.38,2.46,.6)]),
        (.097,[(.63,1.43,.7),(.67,1.68,1.1),(.61,1.88,1.2),(.61,2.12,1.1),(.55,2.31,.8),(.54,2.47,.3)]),
        (.065,[(.12,1.44,.5),(.23,1.70,1),(.22,1.94,.6),(.27,2.26,.8),(.20,2.47,.3)]),
        (.072,[(.14,2.42,.3),(.32,2.41,.9),(.52,2.38,1),(.73,2.30,.5),(.78,2.06,.3)]),
        (.047,[(.75,1.42,.3),(.77,1.66,.8),(.80,1.89,1),(.94,1.94,.3)]),
        (.130,[(.40,2.59,.7),(.29,2.76,1),(.23,3.03,1.2),(.26,3.22,1),(.14,3.49,.6)]),
        (.092,[(.41,2.61,.9),(.53,2.82,1.1),(.48,3.03,1),(.48,3.21,.7),(.58,3.42,.4)]),
        (.078,[(.10,2.69,.4),(.18,2.85,.9),(.38,2.86,1),(.62,2.74,.9),(.82,2.78,.6),(.91,2.92,.2)]),
        (.080,[(.43,3.13,.8),(.61,3.04,1),(.78,3.02,1),(.92,3.16,.3)]),
        (.070,[(.24,3.18,.8),(.39,3.26,1.2),(.60,3.15,1),(.78,3.15,.5),(.91,3.28,.2)]),
        (.047,[(.16,3.43,.5),(.35,3.51,1),(.59,3.48,.8),(.83,3.49,.5),(.90,3.67,.2)]),
        (.057,[(.16,3.36,.7),(.14,3.18,1),(.11,2.99,.6),(.10,2.67,.4)]),
        (.066,[(.86,2.59,.6),(.86,2.86,1),(.89,3.13,1),(.92,3.36,.7),(.93,3.65,.4)]),
        (.052,[(.84,3.63,.8),(.81,3.88,1),(.87,4.13,.4)]),
        (.042,[(.80,3.71,.4),(.69,3.78,.7),(.67,3.92,.3)]),
        (.047,[(.80,3.73,.8),(.68,3.64,.6),(.55,3.62,.2)]),
        (.038,[(.07,3.63,.7),(.05,3.88,.6),(.06,4.11,.3)]),
        (.036,[(.29,3.65,.7),(.31,3.79,1),(.29,3.96,.15)]),
        (.033,[(.14,3.64,.2),(.29,3.67,.8),(.45,3.63,.2)]),
    ]
    return left if side=='Left' else right


def build_door(materials):
    """Return JSON-ready dimensions, geometry counts and animation metadata."""
    import bpy
    from mathutils import Vector
    from mathutils.noise import noise
    for key in ('bronze','recess','edge'):
        if key not in materials:raise KeyError('Door requires '+key)
    collection=bpy.data.collections.get('Architecture')
    parent=bpy.data.objects.get('Architecture')
    if not collection or not parent:raise RuntimeError('Architecture collection/empty required')
    for obj in list(bpy.data.objects):
        if obj.name.startswith(PREFIX):
            mesh=obj.data if obj.type=='MESH' else None
            bpy.data.objects.remove(obj,do_unlink=True)
            if mesh and mesh.users==0:bpy.data.meshes.remove(mesh)
    hidden=[]
    for obj in bpy.data.objects:
        if obj.name.startswith(('Entrance_Bronze_Leaf','Entrance_Leaf_Crossrail',
            'Entrance_Leaf_Stile','Entry_Bronze_Root_Relief')):
            obj.hide_render=True;obj.hide_viewport=True;hidden.append(obj.name)
    created=[];hinges=[];counts={}

    def make(label,g,hinge,smooth=True):
        mesh=bpy.data.meshes.new(PREFIX+label)
        mesh.from_pydata(g.vertices,[],g.faces);mesh.update()
        for m in ('bronze','recess','edge'):mesh.materials.append(materials[m])
        for poly,slot,flat in zip(mesh.polygons,g.slots,g.flat):
            poly.material_index=slot;poly.use_smooth=smooth and len(poly.vertices)==4 and not flat
        for name,values in (('bronze_wear',g.wear),('bronze_cavity',g.cavity)):
            attr=mesh.attributes.new(name,'FLOAT','POINT')
            attr.data.foreach_set('value',values)
        obj=bpy.data.objects.new(PREFIX+label,mesh);collection.objects.link(obj)
        obj.parent=hinge;created.append(obj)
        return obj

    def box(g,x0,x1,y0,y1,z0,z1,slot=0):
        i=len(g.vertices)
        for x,y,z in ((x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
                      (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)):
            g.vert((x,y,z),.28 if slot==2 else .06,.1 if slot==1 else 0)
        for f in ((0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)):
            g.face(tuple(i+j for j in f),slot)

    def moulding(g,x0,x1,z0,z1):
        # One watertight mitred rectangular casting: raised bead, valley, bolection.
        profile=[(0,-.034),(.006,-.050),(.015,-.065),(.024,-.069),
                 (.032,-.060),(.037,-.050),(.042,-.047),(.047,-.057),
                 (.057,-.068),(.068,-.072),(.077,-.061),(.085,-.052),
                 (.091,-.047),(.096,-.040)]
        start=len(g.vertices)
        for inset,y in profile:
            for x,z in ((x0+inset,z0+inset),(x1-inset,z0+inset),
                        (x1-inset,z1-inset),(x0+inset,z1-inset)):
                g.vert((x,y,z),.55 if y<-.062 else .12,.6 if -.055<y<-.046 else .1)
        for ring in range(len(profile)-1):
            for j in range(4):
                a=start+ring*4+j;b=start+ring*4+(j+1)%4
                g.face((a,b,b+4,a+4),2)
        # Back cap/annulus connects inner and outer profile boundaries.
        end=start+(len(profile)-1)*4
        for j in range(4):g.face((start+j,end+j,end+(j+1)%4,start+(j+1)%4),0)

    for side,hinge_x in (('Left',-1.6),('Right',1.6)):
        hinge=bpy.data.objects.new(PREFIX+side+'_Hinge',None)
        collection.objects.link(hinge);hinge.parent=parent
        hinge.location=(hinge_x,-19.02,0);hinge.empty_display_size=.12
        hinges.append(hinge)
        shift=0 if side=='Left' else -WIDTH
        def lx(u):return shift+u*WIDTH
        base=_Geometry()
        box(base,lx(0),lx(1),-.039,.100,.045,4.195,1)
        body=make(side+'_SolidCastLeaf',base,hinge,False)
        mod=body.modifiers.new('Cast edge radius 3 mm','BEVEL');mod.width=.003;mod.segments=3
        body.modifiers.new('Stable corner normals','WEIGHTED_NORMAL')
        frame=_Geometry();moulding(frame,lx(.014),lx(.986),.071,4.173)
        # Recessed inset fields are separate subtly undulating solid cast panels.
        for n,(bottom,top) in enumerate(((.17,1.38),(1.40,2.52),(2.54,3.59),(3.61,4.06))):
            field=_Geometry();nx=74;nz=max(24,int((top-bottom)/.014))
            x0,x1=lx(.080),lx(.920)
            for k in range(nz+1):
                z=bottom+(top-bottom)*k/nz
                for j in range(nx+1):
                    x=x0+(x1-x0)*j/nx
                    v=noise(Vector((x*5.1,z*6.4,4.32)))
                    wave=.0013*v+.0004*noise(Vector((x*40,z*40,18)))
                    field.vert((x,-.040-wave,z),.035,.15+.08*v)
            for k in range(nz):
                for j in range(nx):
                    a=k*(nx+1)+j;field.face((a,a+1,a+nx+2,a+nx+1),1)
            # Underlying continuous thick leaf backs the complete field.
            make(side+'_RecessedCastPanel_'+str(n+1),field,hinge)
        for z in (1.386,2.526,3.596):
            box(frame,lx(.061),lx(.939),-.062,-.031,z-.011,z+.011,2)
        frame_obj=make(side+'_MitredSteppedMouldings',frame,hinge,False)
        bevel=frame_obj.modifiers.new('Worn bronze arris 1 mm','BEVEL');bevel.width=.001;bevel.segments=2
        frame_obj.modifiers.new('Moulding corner normals','WEIGHTED_NORMAL')
        relief=_Geometry();branch_count=0;slivers=0;twigs=0
        network=_network(side)
        for idx,(width,raw) in enumerate(network):
            seed=1000+idx*37+(10000 if side=='Right' else 0)
            pts=[(lx(u),z,r) for u,z,r in raw]
            center=-.056 if idx%4==0 else -.050
            samples=relief.sweep(pts,width,seed,detail=48 if width>.08 else 36,
                                 center=center,flat=.51)
            branch_count+=1
            rand=random.Random(seed)
            # Broken bark is now authored inside sweep(), directly on its exact
            # skin. The former long guessed-depth ridges were mostly buried.
            # Fine forked splinters emerge from selected sides of larger branches.
            for j in range(3 if width>.07 else 1):
                at=rand.randint(max(2,len(samples)//6),max(3,len(samples)*4//5))
                p=samples[at];q=samples[min(len(samples)-1,at+6)]
                dx,dz=q[0]-p[0],q[1]-p[1];mag=max(.00001,math.hypot(dx,dz))
                sign=rand.choice((-1,1));span=rand.uniform(.10,.24)
                endx=p[0]+(-dz/mag*sign*.62+dx/mag*.6)*span
                endz=p[1]+(dx/mag*sign*.62+dz/mag*.6)*span
                endx=max(lx(.055),min(lx(.945),endx));endz=max(.12,min(4.12,endz))
                twig=[(p[0],p[1],1),(p[0]*.6+endx*.4,p[1]*.6+endz*.4,1.25),(endx,endz,.12)]
                relief.sweep(twig,width*.23,seed+j+300,detail=20,flat=.52)
                twigs+=1
        # The photo's organic cross rails are uneven root stems, not neat metal bars.
        for n,z in enumerate((.17,1.39,2.54,3.61)):
            pts=[]
            for j in range(8):
                u=.065+.87*j/7
                pts.append((lx(u),z+.013*math.sin(j*1.5+n+hinge_x),.75+.2*math.sin(j*1.7)))
            relief.sweep(pts,.024 if n<3 else .030,556+n+(0 if side=='Left' else 8),detail=28,flat=.7)
            branch_count+=1
        # The casting terminates inside its bottom/top moulding. Soft compression
        # prevents broad diagonal root flares from passing through the threshold,
        # while avoiding the hard planar slices caused by coordinate clamping.
        def soft_max(value, boundary, softness):
            d=value-boundary
            return boundary+.5*(d+math.sqrt(d*d+softness*softness))
        bounded=[]
        for x,y,z in relief.vertices:
            z=soft_max(z,.065,.003)
            z=-soft_max(-z,-4.155,.003)
            y=soft_max(y,-.170,.002)
            bounded.append((x,y,z))
        relief.vertices=bounded
        obj=make(side+'_TwistedTrunksAndCarvedBark',relief,hinge)
        obj['source']='references/entrance.jpg; independently traced left/right front-visible trunk networks'
        obj['sculpture_status']='dimensional interpretation, not a scan or exact copy'
        obj['primary_cast_branches']=branch_count;obj['bark_lamellae']=slivers;obj['forked_splinters']=twigs
        obj['broken_bark_plates']=getattr(relief,'bark_plate_count',0)
        counts[side]={'primary_branches':branch_count,'bark_lamellae':slivers,'forked_splinters':twigs,
                      'broken_bark_plates':getattr(relief,'bark_plate_count',0),
                      'relief_vertices':len(relief.vertices)}
        # Three sculptural knob/accretion details correspond to the visible casting.
        knob_locations=[(.74,2.72),(.21,1.52)] if side=='Left' else [(.43,.99)]
        knobs=_Geometry()
        for n,(u,z) in enumerate(knob_locations):
            knobs.sweep([(lx(u),z-.049,.4),(lx(u)-.007,z-.021,1.0),
                         (lx(u)+.004,z+.018,1.0),(lx(u),z+.045,.3)],
                        .043,910+n,detail=36,center=-.092,flat=.82,bark=False)
        make(side+'_WornReliefBosses',knobs,hinge)
        hardware=_Geometry()
        # Hinges, pintle brackets and rear reinforcing straps stay on each leaf.
        hinge_local=0 if side=='Left' else 0
        for n,z in enumerate((.29,1.56,2.79,3.99)):
            hardware.sweep([(hinge_local,z-.091,1),(hinge_local,z+.091,1)],
                           .025,880+n,detail=24,center=.038,flat=1,bark=False,taper=False)
            if side=='Left':box(hardware,.007,.10,.015,.070,z-.061,z+.061,2)
            else:box(hardware,-.10,-.007,.015,.070,z-.061,z+.061,2)
        for z in (.35,1.6,2.9,4.04):box(hardware,lx(.08),lx(.93),.099,.116,z-.018,z+.018,0)
        box(hardware,lx(.935),lx(.95),.098,.119,.18,4.05,0)
        make(side+'_HingePintlesAndBackStraps',hardware,hinge)
        for frame_num,angle in ((1,0),(40,0),(85,90 if side=='Left' else -90)):
            hinge.rotation_euler.z=math.radians(angle)
            hinge.keyframe_insert(data_path='rotation_euler',index=2,frame=frame_num,group='Entrance opening')
        hinge['closed_frame']=1;hinge['hold_closed_until_frame']=40;hinge['fully_open_frame']=85
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    verts=sum(len(o.data.vertices) for o in created)
    tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in created)
    return {'objects':[o.name for o in created],'hinges':[h.name for h in hinges],
            'hidden_legacy_objects':hidden,'vertices':verts,'triangles':tris,
            'leaf_counts':counts,'leaf_width_m':WIDTH,'center_seam_m':.024,
            'leaf_height_m':4.15,'solid_leaf_thickness_m':.139,
            'attributes':['bronze_wear','bronze_cavity'],
            'animation':{'closed':[1,40],'open':85,'left_degrees':90,'right_degrees':-90},
            'source':'references/entrance.jpg','geometry_is_scan':False}
