"""Meter-scaled material and motivated lighting refinements; no file I/O."""
import bpy,math
from common import box,light,aim,mat

def fresh(name,color,rough=.5,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    m.diffuse_color=(*color,1)
    return m,n,l,p

def noise(n,l,coords,scale,detail=3,rough=.7):
    q=n.new('ShaderNodeTexNoise');q.inputs['Scale'].default_value=scale;q.inputs['Detail'].default_value=detail;q.inputs['Roughness'].default_value=rough
    l.new(coords,q.inputs['Vector']);return q.outputs['Fac']

def ramp(n,l,value,stops,name):
    r=n.new('ShaderNodeValToRGB');r.name=name
    for e in list(r.color_ramp.elements)[2:]:r.color_ramp.elements.remove(e)
    for i,(pos,col) in enumerate(stops):
        e=r.color_ramp.elements[i] if i<2 else r.color_ramp.elements.new(pos)
        e.position=pos;e.color=(*col,1)
    l.new(value,r.inputs[0]);return r.outputs['Color']

def mathnode(n,l,op,a,b):
    q=n.new('ShaderNodeMath');q.operation=op
    for i,v in enumerate((a,b)):
        if isinstance(v,(int,float)):q.inputs[i].default_value=v
        else:l.new(v,q.inputs[i])
    return q.outputs[0]

def mix(n,l,fac,a,b,name):
    q=n.new('ShaderNodeMixRGB');q.name=name
    if isinstance(fac,(float,int)):q.inputs[0].default_value=fac
    else:l.new(fac,q.inputs[0])
    for i,v in enumerate((a,b),1):
        if isinstance(v,tuple):q.inputs[i].default_value=(*v,1)
        else:l.new(v,q.inputs[i])
    return q.outputs[0]

def bronze_materials():
    out={}
    for key,name,base_rough,wear_mult in [('bronze','REF06 | cast bronze with ridge wear',.49,1),('recess','REF06 | oxidized bronze panel',.57,.28),('edge','REF06 | handled bronze moldings',.40,.8)]:
        m,n,l,p=fresh(name,(.13,.095,.06),base_rough,.78)
        coord=n.new('ShaderNodeTexCoord').outputs['Object']
        patina=noise(n,l,coord,5.2,5)
        cast=noise(n,l,coord,53,3)
        pores=noise(n,l,coord,970,2)
        color=ramp(n,l,patina,[(.19,(.025,.029,.029)),(.44,(.060,.063,.060)),(.64,(.115,.112,.095)),(.83,(.083,.103,.096))],'Bronze and grey-brown oxidation')
        grain=ramp(n,l,cast,[(.18,(.045,.047,.044)),(.8,(.145,.144,.128))],'Foundry mottling')
        color=mix(n,l,.16,color,grain,'Subtle cast variation')
        wa=n.new('ShaderNodeAttribute');wa.attribute_name='bronze_wear';wa.name='True geometric ridge wear'
        ca=n.new('ShaderNodeAttribute');ca.attribute_name='bronze_cavity';ca.name='Sculpted recess patina'
        wear=mathnode(n,l,'MULTIPLY',wa.outputs['Fac'],.63*wear_mult)
        color=mix(n,l,wear,color,(.245,.226,.188),'Restrained polished bronze ridges')
        color=mix(n,l,mathnode(n,l,'MULTIPLY',ca.outputs['Fac'],.49),color,(.021,.025,.023),'Dark cool oxide in bark grooves')
        l.new(color,p.inputs['Base Color'])
        rough=mathnode(n,l,'SUBTRACT',mathnode(n,l,'ADD',mathnode(n,l,'MULTIPLY',cast,.18),base_rough-.06),mathnode(n,l,'MULTIPLY',wear,.16))
        l.new(rough,p.inputs['Roughness'])
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.27;bump.inputs['Distance'].default_value=.00075;l.new(cast,bump.inputs['Height'])
        tiny=n.new('ShaderNodeBump');tiny.inputs['Strength'].default_value=.24;tiny.inputs['Distance'].default_value=.00018;l.new(pores,tiny.inputs['Height']);l.new(bump.outputs['Normal'],tiny.inputs['Normal']);l.new(tiny.outputs['Normal'],p.inputs['Normal'])
        p.inputs['Coat Weight'].default_value=.04;p.inputs['Coat Roughness'].default_value=.43
        m['provenance']='Procedural physically scaled bronze; geometric attributes locate abrasion and oxide. No photographic baked lighting.'
        out[key]=m
    return out

def interior_materials(scene):
    m,n,l,p=fresh('REF06 | polished mineral counter stone',(.12,.14,.15),.28)
    coord=n.new('ShaderNodeTexCoord').outputs['Object']
    broad=noise(n,l,coord,1.6,5);mineral=noise(n,l,coord,24,4);fine=noise(n,l,coord,620,2)
    c=ramp(n,l,broad,[(.18,(.050,.065,.074)),(.48,(.13,.148,.159)),(.78,(.23,.248,.255))],'Natural broad mineral patches')
    g=ramp(n,l,mineral,[(.25,(.08,.089,.097)),(.75,(.24,.249,.25))],'Feldspar mineral inclusions')
    l.new(mix(n,l,.20,c,g,'Minerals within stone'),p.inputs['Base Color'])
    l.new(ramp(n,l,mineral,[(.2,(.19,.19,.19)),(.8,(.32,.32,.32))],'Polish variation'),p.inputs['Roughness'])
    b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.15;b.inputs['Distance'].default_value=.00013;l.new(fine,b.inputs['Height']);l.new(b.outputs['Normal'],p.inputs['Normal'])
    p.inputs['Coat Weight'].default_value=.12;p.inputs['Coat Roughness'].default_value=.19
    count=0
    for o in scene.objects:
        if o.type=='MESH' and o.name.startswith(('Counter_','Island_Stone_Slab','Arrival_Bar_Stone')) and any(x and x.name=='PBR | honed blue-grey mineral stone' for x in o.data.materials):
            for i,old in enumerate(o.data.materials):
                if old and old.name=='PBR | honed blue-grey mineral stone':o.data.materials[i]=m
            count+=1
    floor=bpy.data.materials['PBR | dark polished dining floor'];n=floor.node_tree.nodes;l=floor.node_tree.links;p=n.get('Principled BSDF')
    tc=n.new('ShaderNodeTexCoord').outputs['Object'];vari=noise(n,l,tc,8,3)
    l.new(ramp(n,l,vari,[(.2,(.23,.23,.23)),(.8,(.34,.34,.34))],'Subtle floor sheen variation'),p.inputs['Roughness'])
    p.inputs['Base Color'].default_value=(.032,.036,.043,1)
    # Clear, mildly smoked glazing needs a visible interior, not black metallic glass.
    p=bpy.data.materials['PBR | smoked service glazing'].node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(.64,.69,.71,1);p.inputs['Metallic'].default_value=0;p.inputs['Transmission Weight'].default_value=1;p.inputs['Roughness'].default_value=.075
    return {'stone_objects':count,'floor_roughness_range':[.23,.34]}

def lighting_refine(scene):
    p=bpy.data.materials['PROJECTION | replace this image'].node_tree.nodes.get('Principled BSDF')
    p.inputs['Emission Strength'].default_value=4.0
    changed=[]
    for o in scene.objects:
        if o.type!='LIGHT':continue
        if o.name.startswith('TableExperience_'):
            o.data.energy=21;o.data.color=(1,.68,.37);o.data.spot_size=math.radians(112);o.data.spot_blend=.83;o.data.shadow_soft_size=.018
        elif o.name.startswith('Dome_Bounce'):o.data.energy=72;o.data.color=(.25,.36,.85)
        elif o.name.startswith('Counter_Indirect'):o.data.energy=6;o.data.color=(1,.64,.30)
        elif o.name.startswith('Island_Warm_Pool'):o.data.energy=10;o.data.shape='RECTANGLE';o.data.size=.52;o.data.size_y=.16
        elif o.name.startswith('Service_Warm_Glow'):o.data.energy=95;o.visible_glossy=True;o.visible_transmission=True
        elif o.name.startswith('Service_Oblique'):o.data.energy=42;o.visible_glossy=True;o.visible_transmission=True
        else:continue
        changed.append(o.name)
    metal=bpy.data.materials['PBR | satin blackened steel']
    stainless=mat('REF06 | satin service steel',(.25,.26,.25),.27,.88)
    for name in ['Service_Worktop','Service_Shelf','Service_Stainless_Rail','Service_Stainless_Rail.001']:
        o=bpy.data.objects.get(name)
        if o:
            o.data.materials.clear();o.data.materials.append(stainless)
    emitter=mat('REF06 | warm recessed service lens',(.65,.32,.095),.35)
    p=emitter.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.55,.23,1);p.inputs['Emission Strength'].default_value=5
    for x in [-2.85,-.95,.95,2.85]:
        box('REF06_Service_ShelfLip',(x,10.0,1.68),(1.65,.045,.055),'Architecture',stainless,.007)
        box('REF06_Service_RecessedLens',(x,9.95,1.645),(1.45,.03,.018),'Lighting',emitter,.003)
        lamp=light('REF06_Service_ShelfBounce',(x,9.91,1.62),(x,9.38,.93),24,(1,.63,.32),1.1)
        lamp.data.shape='RECTANGLE';lamp.data.size_y=.025
        # Concealed cabinet joins give scale and specular structure behind glass.
        box('REF06_Service_CabinetReveal',(x,9.06,.58),(1.24,.025,.009),'Architecture',metal,.003)
    for o in scene.objects:
        if o.name.startswith('REF06_Service') and o.parent is None:o.parent=bpy.data.objects['Lighting' if o.type=='LIGHT' or 'Lens' in o.name else 'Architecture']
    return {'adjusted_lights':len(changed),'service_sources':'Real narrow shelf strips, directional practical lighting, clear glazing'}

def entry_lighting(scene,bronze):
    # Natural overcast street illumination with a directional opening in the sky.
    for o in scene.objects:
        if o.type=='LIGHT' and o.name.startswith('Portal_Uplight'):o.data.energy=10
        if o.type=='LIGHT' and o.name=='Street_Overcast':o.data.energy=1450;o.location=(-2.8,-23.7,7.8);o.data.size=7;aim(o,(0,-19.1,2.25))
    light('REF06_Entry_SkyOpening',(-4.1,-21.8,5.7),(0,-19.1,2.0),680,(1,.89,.74),3.2)
    light('REF06_Entry_CoolBounce',(3.8,-22.5,3.7),(0,-19.1,2.1),240,(.70,.79,1),4)
    # Quiet aged facade: mortar and heterogeneous mineral finish remain actual mesh.
    for m in list(bpy.data.materials):
        if not m.name.startswith('Entry_') or 'limestone' not in m.name:continue
        n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');coord=n.new('ShaderNodeTexCoord').outputs['Object']
        q=noise(n,l,coord,36,4);base=tuple(p.inputs['Base Color'].default_value[:3])
        l.new(ramp(n,l,q,[(.2,tuple(c*.78 for c in base)),(.8,tuple(c*1.10 for c in base))],'Irregular old brick mineral stain'),p.inputs['Base Color'])
        b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.26;b.inputs['Distance'].default_value=.0012;l.new(noise(n,l,coord,210,3),b.inputs['Height']);l.new(b.outputs['Normal'],p.inputs['Normal'])
    for o in scene.objects:
        if o.name.startswith('Portal_Bronze'):
            o.data.materials.clear();o.data.materials.append(bronze['edge'])
    # Source photo has a simple narrow flat canopy and no huge added door title.
    title=bpy.data.objects.get('Entrance_Lettering')
    if title:title.hide_render=True;title.hide_viewport=True
    o=box('REF06_Entry_RainCanopy',(0,-19.26,4.43),(3.62,.31,.045),'Architecture',bronze['edge'],.01)
    o.parent=bpy.data.objects['Architecture']
    for o in scene.objects:
        if o.name.startswith('REF06_Entry') and o.parent is None:o.parent=bpy.data.objects['Lighting' if o.type=='LIGHT' else 'Architecture']
