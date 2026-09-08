import bpy, math, os, json
from mathutils import Vector
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def group(name, parent=None):
    c=bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
    return c

def put(o, category):
    c=group(category)
    for old in list(o.users_collection): old.objects.unlink(o)
    c.objects.link(o)
    return o

def mat(name, color, rough=.5, metal=0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    m.use_fake_user=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metal
    m.diffuse_color=(*color,1)
    return m

def finish(o,name,category,material=None,bevel=0):
    o.name=name; put(o,category)
    if material: o.data.materials.append(material)
    if bevel:
        m=o.modifiers.new('Crafted edge radius','BEVEL');m.width=bevel;m.segments=3
        m=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');m.keep_sharp=True
    return o

def box(name,loc,size,category='Architecture',material=None,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,category,material,bevel)

def cyl(name,loc,r,depth,category,material=None,vertices=64,bevel=0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc)
    o=finish(bpy.context.object,name,category,material,bevel)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return o

def mesh(name,verts,faces,category,material=None,bevel=0,smooth=False):
    d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update()
    o=bpy.data.objects.new(name,d);group(category).objects.link(o)
    if material:d.materials.append(material)
    for p in d.polygons:p.use_smooth=smooth
    if bevel:
        m=o.modifiers.new('Soft edges','BEVEL');m.width=bevel;m.segments=3
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o

def arc(name,center,r,width,z,depth,start,end,category,material=None,n=96,bevel=0):
    v=[]
    for i in range(n+1):
        a=math.radians(start+(end-start)*i/n)
        for zz,rr in [(z-depth/2,r-width/2),(z-depth/2,r+width/2),(z+depth/2,r-width/2),(z+depth/2,r+width/2)]:
            v.append((center[0]+rr*math.cos(a),center[1]+rr*math.sin(a),zz))
    f=[]
    for i in range(n):
        k=i*4;j=k+4
        f.extend([(k,j,j+1,k+1),(k+2,k+3,j+3,j+2),(k,k+2,j+2,j),(k+1,j+1,j+3,k+3)])
    f.extend([(0,1,3,2),(n*4,n*4+2,n*4+3,n*4+1)])
    return mesh(name,v,f,category,material,bevel)

def ribbon(name,points,width,z,depth,category,material=None,bevel=0):
    v=[]
    for i,p in enumerate(points):
        t=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        t.normalize();normal=Vector((-t.y,t.x))
        for zz,side in [(z-depth/2,-1),(z-depth/2,1),(z+depth/2,-1),(z+depth/2,1)]:
            q=Vector(p)+normal*width*.5*side;v.append((q.x,q.y,zz))
    f=[]
    for i in range(len(points)-1):
        k=4*i;j=k+4;f.extend([(k,j,j+1,k+1),(k+2,k+3,j+3,j+2),(k,k+2,j+2,j),(k+1,j+1,j+3,k+3)])
    k=(len(points)-1)*4;f.extend([(0,1,3,2),(k,k+2,k+3,k+1)])
    return mesh(name,v,f,category,material,bevel)

def counter_path(side,row):
    pts=[(2.15,-3.25)]
    pts.append((5.75,-3.25))
    for i in range(1,17):
        a=-math.pi/2+math.pi/2*i/16;pts.append((5.75+.65*math.cos(a),-2.6+.65*math.sin(a)))
    pts.append((6.4,-.65))
    for i in range(1,17):
        a=math.pi/2*i/16;pts.append((5.75+.65*math.cos(a),-.65+.65*math.sin(a)))
    pts.append((2.15,0))
    return [(side*x,y+row) for x,y in pts]

def chair_positions():
    out=[]
    for side in [-1,1]:
        for row in [0,5]:
            for x in [2.8,4,5.2]:
                out.extend([(side*x,-2.35+row,0),(side*x,-.90+row,math.pi)])
            out.append((side*5.48,-1.63+row,side*math.pi/2))
    return out

def aim(o,at):o.rotation_euler=(Vector(at)-o.location).to_track_quat('-Z','Y').to_euler()

def camera(name,loc,at,lens=25):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);group('Cameras').objects.link(o)
    o.location=loc;d.lens=lens;d.clip_start=.07;d.clip_end=150;aim(o,at);return o

def light(name,loc,at,energy,color=(1,.8,.6),size=3,kind='AREA'):
    d=bpy.data.lights.new(name,kind);o=bpy.data.objects.new(name,d);group('Lighting').objects.link(o)
    o.location=loc;d.energy=energy;d.color=color
    if kind=='AREA': d.shape='DISK';d.size=size
    if kind=='POINT':d.shadow_soft_size=size
    aim(o,at);return o

def render(cam,path,width=1100,samples=24,height_ratio=.625):
    s=bpy.context.scene;s.camera=bpy.data.objects[cam];s.render.engine='CYCLES';s.cycles.samples=samples
    s.cycles.use_denoising=True;s.render.resolution_x=width;s.render.resolution_y=int(width*height_ratio);s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.filepath=str(ROOT/'renders'/path)
    bpy.ops.render.render(write_still=True)

def save(name):bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/name))

def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene;s.name='Alchemist | spatial journey';s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
    s.render.fps=24;s.world=bpy.data.worlds.new('Restrained environment');s.world.use_nodes=True
    s.world.node_tree.nodes['Background'].inputs[0].default_value=(.3,.34,.42,1)
    s.world.node_tree.nodes['Background'].inputs[1].default_value=.15
    s.view_settings.view_transform='AgX'
    for n in ['Architecture','Dome','Tables','Seating','Lighting','Glassware','Props','InteractionTargets','Cameras','Navigation']:group(n)

def walkthrough():
    s=bpy.context.scene
    stops=[((0,-22,1.65),(0,-18,2.1)),((0,-18,1.65),(-1,-14,1.8)),((0,-14,1.65),(0,-10,1.7)),((0,-10,1.65),(0,-5,2.4)),((1.2,-6,1.65),(0,2,3.2)),((1.2,-1,1.65),(0,2,5.3)),((1.2,1.1,1.65),(2.8,1.75,.78)),((1.2,1.1,1.65),(0,-7,1.7)),((1.2,-6,1.65),(0,-14,1.65)),((0,-14,1.65),(0,-21,1.7)),((0,-22,1.65),(0,-28,1.8))]
    cam=camera('WALKTHROUGH',stops[0][0],stops[0][1],25);cam.rotation_mode='QUATERNION'
    pts=[];duration=144
    for i in range(len(stops)-1):
        p0,t0=map(Vector,stops[i]);p1,t1=map(Vector,stops[i+1])
        q0=(t0-p0).to_track_quat('-Z','Y');q1=(t1-p1).to_track_quat('-Z','Y')
        for j in range(0,duration+1,4):
            u=j/duration;u=u*u*(3-2*u);f=1+i*duration+j
            cam.location=p0.lerp(p1,u);cam.rotation_quaternion=q0.slerp(q1,u)
            cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_quaternion',frame=f)
            pts.append(tuple(cam.location))
    curve=bpy.data.curves.new('Walkthrough centerline','CURVE');curve.dimensions='3D';sp=curve.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,co in zip(sp.points,pts):p.co=(*co,1)
    o=bpy.data.objects.new('PATH_Walkthrough',curve);group('Navigation').objects.link(o);o.hide_render=True
    s.frame_end=1+(len(stops)-1)*duration;s.frame_set(1)
    for i,n in enumerate(['Entrance','Arrival','Transition','Dining reveal','Dome','Table approach','Hero table','Turn to exit','Return transition','Arrival return','Copenhagen']):s.timeline_markers.new(n,frame=1+i*duration)
    for n,p in [('entrance',(0,-19,1.3)),('hero_table',(2.8,1.75,.78)),('dome',(0,0,5)),('exit',(0,-22,1.3))]:
        o=bpy.data.objects.new(n,None);o.location=p;o.empty_display_type='SPHERE';o.empty_display_size=.25;o['interaction']=n;group('InteractionTargets').objects.link(o)
    (ROOT/'reports'/'walkthrough.json').write_text(json.dumps({'units':'meters','axes':'Blender Z up; glTF export converts to Y up','fps':24,'frames':s.frame_end,'stops':[{'position':p,'lookAt':t,'frame':1+i*duration} for i,(p,t) in enumerate(stops)]},indent=2))
