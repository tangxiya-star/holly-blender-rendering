"""Second critique pass: narrower portal, weathered brick, darker patinated bronze."""
import bpy,math,random
from common import box,aim,mat
from refine06_surfaces import fresh,noise,ramp,mix,mathnode

def apply_entry_finish(scene):
    # Match the observed tall door proportions, still explicitly inferred from photos.
    factor=.82
    for hinge in [o for o in scene.objects if o.name.startswith('REF06_Door_') and o.name.endswith('_Hinge') and o.type=='EMPTY']:
        hinge.location.x*=factor
        for o in hinge.children:
            o.location.x*=factor
            if o.type=='MESH':
                for v in o.data.vertices:v.co.x*=factor
    for o in scene.objects:
        if o.name.startswith(('Portal_Bronze','REF06_Entry_RainCanopy')):
            o.location.x*=factor
            if o.type=='MESH':
                for v in o.data.vertices:v.co.x*=factor
    # Lower the broad metallic reflection that made the first casting read silver.
    for m in bpy.data.materials:
        if not m.name.startswith(('REF06 | cast bronze','REF06 | oxidized bronze','REF06 | handled bronze')):continue
        p=m.node_tree.nodes.get('Principled BSDF');n=m.node_tree.nodes;l=m.node_tree.links
        old=p.inputs['Base Color'].links[0].from_socket
        dark=n.new('ShaderNodeMixRGB');dark.blend_type='MULTIPLY';dark.inputs[0].default_value=1;dark.inputs[2].default_value=(.40,.43,.42,1);l.new(old,dark.inputs[1]);l.new(dark.outputs[0],p.inputs['Base Color'])
        p.inputs['Metallic'].default_value=.52
        # Fine ragged casting grain, subordinate to the actual sculpted bark plates.
        tc=n.new('ShaderNodeTexCoord').outputs['Object']
        b=n.new('ShaderNodeBump');b.inputs['Distance'].default_value=.00055;b.inputs['Strength'].default_value=.40
        old=p.inputs['Normal'].links[0].from_socket;l.new(old,b.inputs['Normal']);l.new(noise(n,l,tc,390,3),b.inputs['Height']);l.new(b.outputs[0],p.inputs['Normal'])
    for o in scene.objects:
        if o.type=='LIGHT' and o.name.startswith(('Street_Overcast','REF06_Entry_SkyOpening','REF06_Entry_CoolBounce')):o.data.energy*=.30
    sky=bpy.data.objects.get('REF06_Entry_SkyOpening')
    if sky:sky.data.size=2.3;sky.data.color=(1,.95,.84)
    if bpy.data.objects.get('Entry_Brick_Veneer'):
        bpy.data.objects['Entry_Brick_Veneer'].hide_render=True;bpy.data.objects['Entry_Brick_Veneer'].hide_viewport=True
    rng=random.Random(608)
    pal=[]
    for i,c in enumerate([(.30,.29,.258),(.43,.414,.365),(.27,.145,.067),(.195,.20,.185),(.38,.376,.338),(.205,.177,.134)]):
        m,n,l,p=fresh('REF06 | aged brick '+str(i),c,.89)
        tc=n.new('ShaderNodeTexCoord').outputs['Object'];n1=noise(n,l,tc,21,5)
        l.new(ramp(n,l,n1,[(.2,tuple(x*.62 for x in c)),(.75,tuple(min(.65,x*1.30) for x in c))],'Pale salts and fired mineral variation'),p.inputs['Base Color'])
        b=n.new('ShaderNodeBump');b.inputs['Distance'].default_value=.0014;b.inputs['Strength'].default_value=.45;l.new(noise(n,l,tc,190,4),b.inputs['Height']);l.new(b.outputs[0],p.inputs['Normal']);pal.append(m)
    verts=[];faces=[];slots=[];bricks=0
    def brick(x0,x1,z0,z1):
        nonlocal bricks
        if x1-x0<.02 or z1-z0<.016:return
        offset=len(verts);b=.0035;y=-19.205+rng.uniform(-.003,.003)
        corners=[(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
        inner=[(x0+b+rng.uniform(-.001,.001),z0+b),(x1-b,z0+b+rng.uniform(-.001,.001)),(x1-b+rng.uniform(-.001,.001),z1-b),(x0+b,z1-b+rng.uniform(-.001,.001))]
        verts.extend((x,-19.125,z) for x,z in corners);verts.extend((x,y+.004,z) for x,z in corners);verts.extend((x,y+rng.uniform(-.0008,.0008),z) for x,z in inner)
        fs=[(3,2,1,0),(8,9,10,11)]
        for i in range(4):j=(i+1)%4;fs.extend([(i,j,j+4,i+4),(i+4,j+4,j+8,i+8)])
        faces.extend(tuple(offset+j for j in f) for f in fs)
        slot=rng.choices(range(6),[30,24,9,13,18,6])[0];slots.extend([slot]*len(fs));bricks+=1
    for row in range(73):
        z0=row*.083+.002;z1=min(z0+.074+rng.uniform(-.002,.001),6)
        for col in range(-1,39):
            x0=max(-4.55,-4.55+col*.248-(.124 if row%2 else 0));x1=min(4.55,x0+.239)
            if z0>=4.25:brick(x0,x1,z0,z1)
            else:
                brick(x0,min(x1,-1.435),z0,z1);brick(max(x0,1.435),x1,z0,z1)
                if z1>4.25:brick(max(x0,-1.435),min(x1,1.435),4.25,z1)
    d=bpy.data.meshes.new('REF06_Entry_WeatheredBrickwork');d.from_pydata(verts,[],faces);d.update()
    for m in pal:d.materials.append(m)
    for p,idx in zip(d.polygons,slots):p.material_index=idx
    o=bpy.data.objects.new('REF06_Entry_WeatheredBrickwork',d);bpy.data.collections['Architecture'].objects.link(o);o.parent=bpy.data.objects['Architecture']
    mortar=mat('REF06 | warm grey old mortar',(.25,.24,.21),.94)
    for side in (-1,1):box('REF06_Entry_MortarInfill',(side*1.60,-19.13,2.12),(.34,.095,4.24),'Architecture',mortar,.002).parent=bpy.data.objects['Architecture']
    beam=mat('REF06 | exposed concrete lintel',(.235,.247,.235),.90)
    o=box('REF06_Entry_ConcreteBand',(0,-19.15,4.95),(9.08,.15,.27),'Architecture',beam,.012);o.parent=bpy.data.objects['Architecture']
    n=beam.node_tree.nodes;l=beam.node_tree.links;p=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord').outputs['Object']
    q=noise(n,l,tc,26,4);l.new(ramp(n,l,q,[(.18,(.105,.12,.112)),(.75,(.37,.38,.34))],'Concrete weathering'),p.inputs['Base Color'])
    b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.3;b.inputs['Distance'].default_value=.0015;l.new(noise(n,l,tc,125,3),b.inputs['Height']);l.new(b.outputs[0],p.inputs['Normal'])
    cam=bpy.data.objects['CAM_Entry_Hero'];cam.location=(0,-27.35,2.38);cam.data.lens=58;aim(cam,(0,-19.03,2.23))
    cam=bpy.data.objects['CAM_Entry_Detail'];cam.location=(.82,-21.05,2.81);aim(cam,(-.34,-19.15,2.69))
    scene['door_dimensions']='4.15m leaf height;2.624m opening width inferred from photographs; preserves complete walkthrough.'
    return {'new_bricks':bricks,'door_width_factor':factor,'door_opening_m':2.624,'lighting_multiplier':.30,'materials':'Dark charcoal bronze with gentle crest wear; new fired masonry'}
