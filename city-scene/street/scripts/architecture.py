"""Copenhagen perimeter-block architecture, batched by building and material.

The registry describes facade-centre transforms.  A building's street is local
negative Y, its width is local X, and its occupied volume is positive Y.
Upper windows and shop windows are genuine gaps in the masonry shell.
Run build_architecture() after the street-scale blockout has been inspected.
"""
from pathlib import Path
import json
import math
import random
from collections import defaultdict

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = "Architecture_Copenhagen"


def _collection():
    collection = bpy.data.collections.get(COLLECTION)
    if collection is None:
        collection = bpy.data.collections.new(COLLECTION)
        bpy.context.scene.collection.children.link(collection)
    return collection


def _material(name, color, rough=.65, metal=0, texture=None):
    name = "CPH_Arch_" + name
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color[:3], 1)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color[:3], 1)
    shader.inputs["Roughness"].default_value = rough
    shader.inputs["Metallic"].default_value = metal
    if texture:
        coord = nodes.new("ShaderNodeTexCoord")
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 2.8 if texture == "plaster" else 5.4
        noise.inputs["Detail"].default_value = 3.0
        noise.inputs["Roughness"].default_value = .68
        links.new(coord.outputs["Object"], noise.inputs["Vector"])
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = .15
        ramp.color_ramp.elements[0].color = (*[v*.84 for v in color[:3]], 1)
        ramp.color_ramp.elements[1].position = .86
        ramp.color_ramp.elements[1].color = (*[min(v*1.09, .94) for v in color[:3]], 1)
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
        roughmap = nodes.new("ShaderNodeMapRange")
        roughmap.inputs["From Min"].default_value = 0
        roughmap.inputs["From Max"].default_value = 1
        roughmap.inputs["To Min"].default_value = max(rough-.12, .12)
        roughmap.inputs["To Max"].default_value = min(rough+.12, .96)
        links.new(noise.outputs["Fac"], roughmap.inputs["Value"])
        links.new(roughmap.outputs["Result"], shader.inputs["Roughness"])
        fine = nodes.new("ShaderNodeTexNoise")
        fine.inputs["Scale"].default_value = 85 if texture == "plaster" else 36
        fine.inputs["Detail"].default_value = 2
        links.new(coord.outputs["Object"], fine.inputs["Vector"])
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .22
        bump.inputs["Distance"].default_value = .009 if texture == "plaster" else .004
        links.new(fine.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], shader.inputs["Normal"])
        if texture == "brick":
            split = nodes.new("ShaderNodeSeparateXYZ")
            combine = nodes.new("ShaderNodeCombineXYZ")
            links.new(coord.outputs["Object"], split.inputs["Vector"])
            links.new(split.outputs["X"], combine.inputs["X"])
            links.new(split.outputs["Z"], combine.inputs["Y"])
            links.new(split.outputs["Y"], combine.inputs["Z"])
            brick = nodes.new("ShaderNodeTexBrick")
            brick.offset = .5
            brick.offset_frequency = 2
            brick.inputs["Scale"].default_value = 1
            brick.inputs["Mortar Size"].default_value = .0055
            brick.inputs["Mortar Smooth"].default_value = .003
            brick.inputs["Brick Width"].default_value = .228
            brick.inputs["Row Height"].default_value = .068
            brick.inputs["Color1"].default_value = (*[v*.82 for v in color[:3]], 1)
            brick.inputs["Color2"].default_value = (*[min(v*1.12, .94) for v in color[:3]], 1)
            brick.inputs["Mortar"].default_value = (.30, .285, .25, 1)
            links.new(combine.outputs["Vector"], brick.inputs["Vector"])
            links.new(brick.outputs["Color"], shader.inputs["Base Color"])
            mortar_bump = nodes.new("ShaderNodeBump")
            mortar_bump.invert = True
            mortar_bump.inputs["Strength"].default_value = .42
            mortar_bump.inputs["Distance"].default_value = .013
            links.new(brick.outputs["Fac"], mortar_bump.inputs["Height"])
            links.new(bump.outputs["Normal"], mortar_bump.inputs["Normal"])
            links.new(mortar_bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def _glass(name, tint, rough):
    material = _material(name, tint, rough)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    # Physical thin-sheet glazing: full grazing-angle reflections, transparent
    # face-on views.  A constant mix had made the windows read as empty holes.
    glossy = nodes.new("ShaderNodeBsdfPrincipled")
    glossy.inputs["Base Color"].default_value = (*tint[:3],1)
    glossy.inputs["Metallic"].default_value = 1
    glossy.inputs["Roughness"].default_value = rough
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    transparent.inputs[0].default_value = (.935, .956, .958, 1)
    fresnel = nodes.new("ShaderNodeFresnel")
    fresnel.inputs["IOR"].default_value = 1.46
    mix = nodes.new("ShaderNodeMixShader")
    links.new(fresnel.outputs["Fac"],mix.inputs[0])
    links.new(transparent.outputs["BSDF"],mix.inputs[1])
    links.new(glossy.outputs["BSDF"],mix.inputs[2])
    links.new(mix.outputs[0],output.inputs["Surface"])
    return material


def _emission(name,color,strength):
    material=_material(name,color,.65)
    shader=material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Emission Color"].default_value=(*color,1)
    shader.inputs["Emission Strength"].default_value=strength
    return material


class Batch:
    """Disconnected solid parts share one mesh per material per building."""
    def __init__(self):
        self.parts = defaultdict(lambda: [[], []])

    def mesh(self, material, verts, faces):
        vv, ff = self.parts[material]
        offset = len(vv)
        vv.extend(verts)
        ff.extend(tuple(offset+i for i in face) for face in faces)

    def box(self, material, center, size):
        x, y, z = center
        a, b, c = [v*.5 for v in size]
        if min(a, b, c) <= 0:
            return
        self.mesh(material, [(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
                             (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)],
                  [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])

    def pane(self, material, x, y, z, width, height):
        self.mesh(material, [(x-width/2,y,z-height/2),(x+width/2,y,z-height/2),
                             (x+width/2,y,z+height/2),(x-width/2,y,z+height/2)], [(0,1,2,3)])

    def rod(self, material, start, end, radius, sides=10):
        start, end = Vector(start), Vector(end)
        axis = (end-start).normalized()
        helper = Vector((0,0,1)) if abs(axis.z)<.9 else Vector((1,0,0))
        u = axis.cross(helper).normalized()*radius
        v = axis.cross(u).normalized()*radius
        vertices = []
        for center in [start,end]:
            for j in range(sides):
                angle = j*math.tau/sides
                vertices.append(tuple(center+u*math.cos(angle)+v*math.sin(angle)))
        faces = [tuple(reversed(range(sides))), tuple(range(sides,2*sides))]
        faces += [(j,(j+1)%sides,(j+1)%sides+sides,j+sides) for j in range(sides)]
        self.mesh(material, vertices, faces)

    def finish(self, name, root):
        objects = []
        for material, (verts, faces) in self.parts.items():
            if not faces:
                continue
            mesh = bpy.data.meshes.new(name+"_"+material.name)
            mesh.from_pydata(verts, [], faces)
            mesh.update()
            obj = bpy.data.objects.new(name+"_"+material.name, mesh)
            _collection().objects.link(obj)
            obj.parent = root
            obj.data.materials.append(material)
            objects.append(obj)
        return objects


def _palette():
    return {
        "trim": _material("Limestone_aged", (.64,.60,.51), .79, texture="plaster"),
        "ivory": _material("Paint_ivory", (.71,.715,.66), .47, texture="paint"),
        "frame_gray": _material("Paint_graygreen", (.22,.27,.24), .5, texture="paint"),
        "frame_cream": _material("Paint_warmwhite", (.78,.76,.66), .48, texture="paint"),
        "frame_brown": _material("Paint_brownblack", (.105,.079,.06), .48, texture="paint"),
        "stone": _material("Granite_plinth", (.24,.25,.235), .85, texture="stone"),
        "wood": _material("Aged_oak", (.205,.115,.051), .6, texture="wood"),
        "zinc": _material("Weathered_zinc", (.28,.30,.30), .48, .60, "metal"),
        "darkmetal": _material("Iron_charcoal", (.07,.085,.08), .5, .58),
        "slate": _material("Slate_bluegray", (.13,.155,.165), .77, texture="stone"),
        "room": _material("Interior_unlit", (.155,.142,.124), .95),
        "room_light": _material("Interior_plaster", (.46,.405,.33), .90),
        "room_warm": _emission("Interior_softwarm", (.46,.34,.22), .055),
        "ceiling_light": _emission("Shop_daylight_lamp", (.89,.78,.59), 2.5),
        "curtain_white": _material("Linen_natural", (.74,.715,.635), .96, texture="linen"),
        "curtain_gray": _material("Linen_gray", (.36,.39,.36), .96, texture="linen"),
        "curtain_warm": _material("Linen_fadedochre", (.42,.335,.235), .96, texture="linen"),
        "sign": _material("Shop_lettering_cream", (.83,.80,.68), .7),
        "paper": _material("Book_paper", (.63,.57,.44), .85),
        "book_red": _material("Book_oxblood", (.22,.055,.038), .86),
        "book_green": _material("Book_fadedgreen", (.10,.16,.12), .84),
        "bread": _material("Bread_crust", (.49,.265,.095), .87, texture="bread"),
        "glass": _glass("Window_clear", (.85,.895,.91), .065),
        "glass_old": _glass("Window_old", (.83,.87,.87), .11),
        "shopglass": _glass("Shop_glass", (.92,.955,.96), .045),
        "roof0": _material("Clay_roof0", (.30,.098,.047), .83, texture="clay"),
        "roof1": _material("Clay_roof1", (.36,.128,.064), .83, texture="clay"),
        "roof2": _material("Clay_roof2", (.25,.080,.040), .84, texture="clay"),
        "roof3": _material("Clay_roof3", (.325,.108,.054), .83, texture="clay"),
        "chimney": _material("Chimney_oldbrick", (.32,.15,.075), .85, texture="brick"),
    }


def _curtain(batch, material, x, y, bottom, width, height, phase):
    columns = max(6, int(width/.045))
    vertices = []
    for row in [0,1]:
        for i in range(columns+1):
            xx = x-width/2+width*i/columns
            yy = y+.018*math.sin(i*1.8+phase)
            zz = bottom+height*row + (.009*math.sin(i*.8+phase) if row == 0 else 0)
            vertices.append((xx,yy,zz))
    batch.mesh(material, vertices, [(i,i+1,i+columns+2,i+columns+1) for i in range(columns)])


def _window(batch, p, rng, x, bottom, width, height, frame, fancy=False):
    center = bottom+height/2
    # Cavity lining: bright plaster reveal, then a dark, closed cell.
    reveal = p["trim"]
    batch.box(reveal, (x-width/2-.022,.155,center), (.044,.30,height+.07))
    batch.box(reveal, (x+width/2+.022,.155,center), (.044,.30,height+.07))
    batch.box(reveal, (x,.155,bottom+height+.022), (width+.088,.30,.044))
    batch.box(p["room"], (x,1.32,center), (width+.17,.08,height+.16))
    batch.box(p["room"], (x-width/2-.04,.79,center), (.08,1.0,height+.14))
    batch.box(p["room"], (x+width/2+.04,.79,center), (.08,1.0,height+.14))
    batch.box(p["room"], (x,.79,bottom+height+.035), (width+.15,1.0,.07))
    batch.box(p["room_light"], (x,.79,bottom-.02), (width+.14,1.0,.04))
    state = rng.random()
    if state < .56:
        curtain = rng.choice([p["curtain_white"],p["curtain_white"],p["curtain_gray"],p["curtain_warm"]])
        if state < .13:
            _curtain(batch,curtain,x,.57,bottom+.045,width*.97,height*.97,rng.random()*6)
        else:
            frac = rng.uniform(.19,.36)
            for side in [-1,1]:
                _curtain(batch,curtain,x+side*width*(.5-frac/2),.59,bottom+.04,
                         width*frac,height*.98,rng.random()*6)
            batch.rod(p["wood"],(x-width/2,.6,bottom+height-.04),
                      (x+width/2,.6,bottom+height-.04),.012,6)
    elif state > .92:
        batch.box(p["room_warm"], (x,1.23,center), (width*.96,.03,height*.96))
        batch.box(p["wood"], (x+.22,.94,bottom+.30), (.32,.30,.55))
    elif state > .72:
        # A partly lowered fabric blind, with a dark visible lower interior.
        blind_height = height*rng.uniform(.22,.55)
        batch.box(p["curtain_gray"], (x,.49,bottom+height-blind_height/2),
                  (width*.96,.026,blind_height))
    glass = p["glass_old"] if rng.random()<.28 else p["glass"]
    # Glazing sits within the timber rebate, 14 cm behind the masonry face.
    batch.pane(glass,x,.140,center,width,height)
    # Deep timber casements; six lights with characteristic high transom.
    for xx in [x-width/2+.025,x+width/2-.025]:
        batch.box(frame,(xx,.133,center),(.050,.084,height))
    for zz in [bottom+.025,bottom+height-.025]:
        batch.box(frame,(x,.133,zz),(width,.084,.050))
    batch.box(frame,(x,.115,center),(.043,.105,height-.05))
    batch.box(frame,(x,.112,bottom+height*.69),(width,.10,.052))
    batch.box(frame,(x,.139,bottom+height*.345),(width,.065,.026))
    # Sill overhang and lintel shade create real facade relief.
    batch.box(reveal,(x,.018,bottom-.039),(width+.15,.25,.060))
    batch.box(reveal,(x,.045,bottom+height+.052),(width+.12,.23,.055))
    if fancy:
        batch.box(reveal,(x,.016,bottom+height+.112),(width+.22,.25,.036))
        for side in [-1,1]:
            batch.box(reveal,(x+side*(width/2+.053),.075,center),(.041,.20,height+.055))
    # Small dark handle only; enough detail near the camera without clutter.
    batch.box(p["darkmetal"],(x+.055,.048,bottom+height*.46),(.018,.021,.09))


def _sign(name, body, loc, size, material, root, width=None):
    font = bpy.data.curves.new(name,"FONT")
    font.body = body
    font.align_x = "CENTER"
    font.align_y = "CENTER"
    font.size = size
    font.space_character = 1.16
    font.extrude = .0015
    obj = bpy.data.objects.new(name,font)
    _collection().objects.link(obj)
    obj.parent = root
    obj.location = loc
    obj.rotation_euler = (math.pi/2,0,0)
    font.materials.append(material)
    return obj


def _shop(batch,p,rng,width,height,shop,root,building_id):
    colors = [(.075,.14,.115),(.14,.19,.175),(.235,.22,.175),(.19,.11,.075),(.145,.18,.195)]
    color_index = rng.randrange(len(colors))
    shopmat = _material("Shop_paint_"+str(color_index), colors[color_index],.54,texture="paint")
    n = max(3,round(width/2.65))
    bay = width/n
    door_bay = n-1 if rng.random()<.65 else 0
    doorway_x=-width/2+(door_bay+.5)*bay
    root["doorway_local_x"]=doorway_x
    root["doorway_world_xyz"]=[root.location.x+math.cos(root.rotation_euler.z)*doorway_x,
                               root.location.y+math.sin(root.rotation_euler.z)*doorway_x,
                               root.location.z+.15]
    entrance=bpy.data.objects.new("Entrance_"+building_id,None)
    _collection().objects.link(entrance)
    entrance.parent=root
    entrance.location=(doorway_x,-.10,.15)
    entrance.empty_display_type="PLAIN_AXES"
    entrance.empty_display_size=.25
    detail_rng=random.Random(sum(ord(c)*(i+1) for i,c in enumerate(building_id)))
    is_bakery=any(word in shop.upper() for word in ["BAGER","BRØD"])
    is_books=any(word in shop.upper() for word in ["BOG","BØG","ATELIER"])
    is_cafe=any(word in shop.upper() for word in ["KAFFE","CAF"])
    # Pilasters, sign fascia, and granite kickplates leave glazing cavities.
    for i in range(n+1):
        xx = -width/2+i*bay
        batch.box(shopmat,(xx,.13,1.70),(.17,.32,3.36))
        batch.box(p["stone"],(xx,.015,.23),(.23,.35,.46))
        batch.box(shopmat,(xx,.015,2.83),(.25,.32,.075))
    batch.box(shopmat,(0,.09,3.18),(width,.48,.56))
    batch.box(p["trim"],(0,.015,3.59),(width+.06,.51,.12))
    batch.box(shopmat,(0,-.08,2.84),(width,.30,.085))
    for i in range(n):
        x = -width/2+(i+.5)*bay
        ww = bay-.25
        doorway = i == door_bay
        bottom = .16 if doorway else .49
        wh = 2.70-bottom
        center = bottom+wh/2
        back_material=p["room_light"] if (is_bakery or is_cafe or is_books) else p["room"]
        batch.box(back_material,(x,1.80,1.50),(ww+.12,.12,2.86))
        batch.box(p["room_light"],(x,.98,2.79),(ww+.12,2.42,.10))
        batch.box(p["wood"],(x,1.05,.16),(ww+.12,2.25,.08))
        for side in [-1,1]:
            # Interior returns must begin behind the glazed shopfront. Earlier
            # returns began at Y=.05 and masked the recessed panes at street
            # grazing angles, making the windows appear to be unglazed holes.
            batch.box(p["room"],(x+side*(ww/2+.035),1.19,1.50),(.07,2.00,2.80))
        batch.box(shopmat,(x,.115,bottom-.095),(ww,.28,.19))
        batch.box(shopmat,(x,.095,2.73),(ww,.24,.08))
        for side in [-1,1]:
            batch.box(shopmat,(x+side*(ww/2-.025),.10,center),(.065,.23,wh))
        if doorway:
            # A slightly recessed painted entrance with a timber lower panel.
            doorw=min(1.22,ww-.12)
            shoulder=(ww-doorw)/2
            for side in [-1,1]:
                batch.box(shopmat,(x+side*(doorw/2+shoulder/2),.19,1.39),
                          (shoulder,.20,2.64))
                batch.box(shopmat,(x+side*(doorw/2-.03),.19,1.44),(.065,.14,2.56))
            batch.box(shopmat,(x,.20,.49),(doorw-.10,.09,.61))
            batch.pane(p["shopglass"],x,.150,1.74,doorw-.12,1.77)
            batch.box(shopmat,(x,.20,2.40),(doorw-.10,.11,.06))
            batch.box(shopmat,(x,.20,1.13),(doorw-.10,.11,.06))
            batch.box(shopmat,(x,.20,1.75),(.055,.11,1.2))
            batch.rod(p["zinc"],(x+doorw*.31,.13,1.04),(x+doorw*.31,.13,1.36),.014,8)
            batch.box(p["stone"],(x,-.08,.072),(doorw+.11,.63,.144))
            _sign(building_id+"_door_no",str(3+(abs(sum(ord(c) for c in building_id))%87)),
                  (x,.035,2.57),.115,p["sign"],root)
        else:
            # Shop glazing is nearly flush: 4 cm behind the outer frame face,
            # with transoms in front of it and cavity walls wholly behind it.
            batch.pane(p["shopglass"],x,.025,center,ww-.06,wh-.035)
            batch.box(shopmat,(x,.040,2.23),(ww-.02,.11,.055))
            if ww>2.15:
                batch.box(shopmat,(x,.040,center),(.045,.11,wh))
            # Restrained real depth: a shelf/counter and a few readable objects.
            batch.box(p["wood"],(x,.77,.86),(ww*.83,.44,.055))
            batch.box(shopmat,(x,.81,.52),(ww*.80,.39,.62))
            count = rng.randint(4,7)
            for j in range(count):
                xx = x-ww*.29+j*(ww*.58/max(count-1,1))
                h = rng.uniform(.14,.31)
                batch.box(rng.choice([p["paper"],p["book_red"],p["book_green"]]),
                          (xx,.69,.89+h/2),(rng.uniform(.065,.12),.13,h))
            if is_books:
                for zz in [1.30,1.74]:
                    batch.box(p["wood"],(x,1.30,zz),(ww*.82,.24,.045))
                    for j in range(12):
                        xx=x-ww*.36+j*ww*.72/11
                        hh=detail_rng.uniform(.16,.28)
                        batch.box(detail_rng.choice([p["paper"],p["book_green"],p["book_red"]]),
                                  (xx,1.22,zz+.025+hh/2),(.065,.16,hh))
                for side in [-1,1]:
                    batch.box(p["paper"],(x+side*ww*.2,.53,1.13),(.19,.035,.28))
            if is_cafe or is_bakery:
                # Cups, pastry trays and a shelf lamp give the windows a lived-in
                # daylight interior, not a night-time emissive rectangle.
                batch.box(p["wood"],(x,1.38,1.44),(ww*.73,.24,.04))
                for j in range(4):
                    cx=x-ww*.26+j*ww*.52/3
                    batch.rod(p["ivory"],(cx,.57,.90),(cx,.57,.98),.04,12)
                    batch.rod(p["room"],(cx,.57,.979),(cx,.57,.982),.033,12)
                if is_bakery:
                    for row in range(2):
                        batch.box(p["wood"],(x,.94+row*.22,1.09+row*.19),(ww*.68,.21,.035))
                        for j in range(5):
                            cx=x-ww*.28+j*ww*.14
                            batch.rod(p["bread"],(cx-.07,.94+row*.22,1.15+row*.19),
                                      (cx+.07,.94+row*.22,1.15+row*.19),.055,10)
                batch.box(p["ceiling_light"],(x,1.10,2.67),(.37,.27,.025))
            if building_id=="Hero_1_1_05" and i==1:
                _curtain(batch,p["curtain_gray"],x,.38,bottom+.02,ww*.98,wh*.98,.6)
            if rng.random()<.18:
                # Linen cafe blind rather than identical bare display glass.
                _curtain(batch,p["curtain_white"],x,.41,2.08,ww*.97,.58,rng.random()*6)
    clean_shop = shop.strip() if shop else rng.choice(["BAGERI","KAFFE & BRØD","BOGHANDEL","ATELIER","CYKLER","BLOMSTER"])
    clean_shop = clean_shop.upper()
    size = min(.305,(width-.85)/max(len(clean_shop)*.66,1))
    _sign(building_id+"_shop_sign",clean_shop,(0,-.165,3.19),size,p["sign"],root)
    return shopmat


def _tile_roof(batch,p,rng,width,depth,height,rise,kind):
    eave_y=-.28
    rear_y=depth+.22
    ridge_y=depth*.50
    z=height+.16
    roofmat=p["slate"] if kind=="zinc" else p["roof0"]
    # Closed slopes, eave lip, and ridge. Shallow ceramic profiles produce
    # believable highlights while keeping each complete roof in four meshes.
    batch.mesh(roofmat,[(-width/2-.20,eave_y,z),(width/2+.20,eave_y,z),
                        (width/2+.20,ridge_y,z+rise),(-width/2-.20,ridge_y,z+rise),
                        (-width/2-.20,rear_y,z),(width/2+.20,rear_y,z)],
               [(0,1,2,3),(3,2,5,4)])
    if kind=="zinc":
        spacing=.56
        for i in range(int(width/spacing)+1):
            x=-width/2+i*spacing
            batch.rod(p["zinc"],(x,eave_y,z+.015),(x,ridge_y,z+rise+.015),.012,6)
            batch.rod(p["zinc"],(x,ridge_y,z+rise+.015),(x,rear_y,z+.015),.012,6)
    else:
        cols=max(24,round((width+.40)/.265))
        tilew=(width+.40)/cols
        for start_y,end_y,start_z,end_z in [(eave_y,ridge_y,z,z+rise),(rear_y,ridge_y,z,z+rise)]:
            length=math.sqrt((end_y-start_y)**2+(end_z-start_z)**2)
            rows=max(12,round(length/.34))
            for row in range(rows):
                # Small random tonal differences, with no exaggerated grunge.
                t0=row/rows
                t1=min((row+1.07)/rows,1.006)
                y0=start_y+(end_y-start_y)*t0
                y1=start_y+(end_y-start_y)*t1
                z0=start_z+(end_z-start_z)*t0+.018
                z1=start_z+(end_z-start_z)*t1+.012
                for col in range(cols):
                    x0=-width/2-.20+col*tilew
                    material=p["roof"+str(rng.choices([0,1,2,3],[.52,.15,.12,.21])[0])]
                    verts=[]
                    for yy,zz in [(y0,z0),(y1,z1)]:
                        for a in range(4):
                            u=a/3
                            verts.append((x0+tilew*u,yy,zz+.018*math.sin(u*math.pi)))
                    batch.mesh(material,verts,[(0,1,5,4),(1,2,6,5),(2,3,7,6)])
                    # The shadow under the tile's exposed lower lip matters
                    # more at street level than hidden back-facing detail.
                    batch.mesh(material,[(x0,y0,z0-.024),(x0+tilew,y0,z0-.024),
                                         (x0+tilew,y0,z0),(x0,y0,z0)],[(0,1,2,3)])
    batch.rod(p["zinc"] if kind=="zinc" else p["roof1"],
              (-width/2-.23,ridge_y,z+rise+.06),(width/2+.23,ridge_y,z+rise+.06),.092,12)
    return z


def _dormer(batch,p,rng,x,height,rise,depth,frame):
    y=.85
    base=height+.49
    width=1.22
    top=base+1.73
    # Zinc-cheeked Copenhagen roof dormer; its pane is recessed into an opening.
    batch.box(p["zinc"],(x-width/2+.045,y+.49,base+.81),(.09,1.25,1.80))
    batch.box(p["zinc"],(x+width/2-.045,y+.49,base+.81),(.09,1.25,1.80))
    batch.box(p["zinc"],(x,y+.44,base+.10),(width,1.40,.20))
    batch.box(p["room"],(x,y+.95,base+.87),(width-.15,.04,1.40))
    batch.pane(p["glass_old"],x,y+.08,base+.87,width-.19,1.33)
    for side in [-1,1]:
        batch.box(frame,(x+side*(width/2-.12),y+.025,base+.88),(.07,.10,1.41))
    for zz in [base+.18,base+1.57]:
        batch.box(frame,(x,y+.025,zz),(width-.18,.10,.07))
    batch.box(frame,(x,y+.015,base+.89),(.05,.12,1.39))
    batch.box(frame,(x,y+.015,base+1.13),(width-.18,.12,.055))
    batch.box(p["zinc"],(x,y-.025,top-.06),(width+.12,1.55,.13))
    batch.mesh(p["zinc"],[(x-width/2-.09,y-.35,top),(x+width/2+.09,y-.35,top),
                          (x,y-.35,top+.37),(x-width/2-.09,y+1.12,top),
                          (x+width/2+.09,y+1.12,top),(x,y+1.12,top+.37)],
               [(0,1,2),(0,2,5,3),(2,1,4,5)])


def _build_one(spec,p):
    rng=random.Random(int(spec.get("seed",0)))
    width=float(spec["width"])
    depth=float(spec.get("depth",12))
    height=float(spec["height"])
    floors=int(spec.get("floors",5))
    ident=str(spec["id"])
    root=bpy.data.objects.new("Building_"+ident,None)
    _collection().objects.link(root)
    root.location=spec.get("origin",[0,0,.18])
    root.rotation_euler[2]=spec.get("rotation",0)
    root["building_id"]=ident
    root["facade_width_m"]=width
    root["storeys"]=floors
    root["shop"]=spec.get("shop","")
    root["window_openings"]=True
    root["construction"]="Piers and spandrels; glazed cavities; batched material meshes"
    batch=Batch()
    color=tuple(spec.get("color",[.62,.50,.32]))
    # Convert palette colors directly as scene-linear, matching the street system.
    wall=_material("Facade_"+ident,color,.82,texture=spec.get("style","plaster"))
    frame=rng.choice([p["frame_cream"],p["frame_cream"],p["ivory"],p["frame_gray"],p["frame_brown"]])
    trim=p["trim"]
    # Only side and rear shells are continuous: never put a solid front box
    # behind the upper windows or shopfronts.
    batch.box(wall,(-width/2+.12,depth/2,height/2),(.24,depth,height))
    batch.box(wall,(width/2-.12,depth/2,height/2),(.24,depth,height))
    batch.box(wall,(0,depth-.12,height/2),(width,.24,height))
    batch.box(p["stone"],(0,.18,.17),(width,.40,.34))
    shopmat=_shop(batch,p,rng,width,height,spec.get("shop",""),root,ident)
    ground=3.65
    upper_height=(height-ground)/max(floors-1,1)
    bays=max(3,min(6,round(width/rng.uniform(2.15,2.45))))
    margin=rng.uniform(1.02,1.25)
    pitch=(width-2*margin)/(bays-1)
    win_width=min(rng.uniform(1.09,1.24),pitch-.68)
    fancy=spec.get("style","plaster")!="brick" and rng.random()<.46
    for level in range(floors-1):
        base=ground+level*upper_height
        wh= min(1.91 + (.055 if level==0 else 0),upper_height-.98)
        bottom=base+.50
        top=bottom+wh
        centers=[-width/2+margin+i*pitch for i in range(bays)]
        # Solid below-sill and above-lintel spandrels.
        batch.box(wall,(0,.17,(base+bottom)/2),(width,.34,bottom-base))
        batch.box(wall,(0,.17,(top+base+upper_height)/2),(width,.34,base+upper_height-top))
        edge=-width/2
        for x in centers:
            left=x-win_width/2
            if left>edge:
                batch.box(wall,((left+edge)/2,.17,(bottom+top)/2),(left-edge,.34,wh))
            _window(batch,p,rng,x,bottom,win_width,wh,frame,fancy and level<2)
            edge=x+win_width/2
        if edge<width/2:
            batch.box(wall,((edge+width/2)/2,.17,(bottom+top)/2),(width/2-edge,.34,wh))
        # Interior floor slabs disappear into the room cells behind glazing.
        batch.box(p["room"],(0,depth/2,base-.08),(width-.1,depth-.1,.16))
        if level==0 or (fancy and level==1):
            batch.box(trim,(0,.055,base+.055),(width+.025,.25,.055))
        if level==0 and fancy and rng.random()<.5:
            for x in centers:
                batch.box(trim,(x,.055,base+.25),(win_width+.035,.24,.055))
    # Narrow corner pilasters: these give party-wall rhythm without monumental
    # columns or generic luxury-building decoration.
    if fancy:
        for side in [-1,1]:
            xx=side*(width/2-.13)
            batch.box(trim,(xx,.085,(ground+height)/2),(.10,.24,height-ground))
    for zz,dd,hh in [(height-.19,.30,.10),(height-.09,.39,.075),(height+.035,.49,.12)]:
        batch.box(trim,(0,.025,zz),(width+.13,dd,hh))
    # Gable walls close roofs at the party-wall ends.
    rise=rng.uniform(2.35,3.32)
    kind="zinc" if rng.random()<.25 else "tile"
    for side in [-1,1]:
        xx=side*(width/2-.03)
        batch.mesh(wall,[(xx,0,height),(xx,depth,height),(xx,depth*.5,height+rise+.16)],[(0,1,2)])
    _tile_roof(batch,p,rng,width,depth,height,rise,kind)
    dormer_count = 1 if width<9 else (2 if width<12.7 else 3)
    if rng.random()<.81:
        for i in range(dormer_count):
            xx=(i-(dormer_count-1)/2)*min(3.35,width/(dormer_count+.3))
            _dormer(batch,p,rng,xx,height,rise,depth,frame)
    # Galvanised gutters and downpipes run naturally down party-wall edges.
    batch.rod(p["zinc"],(-width/2-.13,-.27,height+.035),(width/2+.13,-.27,height+.035),.077,12)
    pipe_x=width/2-.20 if rng.random()<.5 else -width/2+.20
    batch.rod(p["zinc"],(pipe_x,-.29,.30),(pipe_x,-.29,height-.30),.049,10)
    batch.rod(p["zinc"],(pipe_x,-.29,height-.30),(pipe_x,-.35,height+.015),.049,10)
    for z in [1.05,4.0,7.0,10.0,13.0]:
        if z<height-.5:
            batch.box(p["darkmetal"],(pipe_x,-.255,z),(.125,.12,.027))
    # One or two chimney stacks, with caps and terracotta pots.
    for i in range(1 if width<12 else 2):
        cx=(-.28 if i==0 else .30)*width
        cy=depth*.62
        roof_z=height+.16+rise*(1-abs(cy-depth*.5)/(depth*.5))
        stack_h=rng.uniform(1.12,1.50)
        batch.box(p["chimney"],(cx,cy,roof_z+stack_h/2-.10),(.67,.68,stack_h))
        batch.box(p["trim"],(cx,cy,roof_z+stack_h-.09),(.79,.78,.11))
        for dx in [-.18,.18]:
            batch.rod(p["roof2"],(cx+dx,cy,roof_z+stack_h-.04),(cx+dx,cy,roof_z+stack_h+.33),.095,10)
            batch.rod(p["roof2"],(cx+dx,cy,roof_z+stack_h+.26),(cx+dx,cy,roof_z+stack_h+.35),.122,10)
    objects=batch.finish("Building_"+ident,root)
    root["mesh_count"]=len(objects)
    return {"id":ident,"width":width,"height":height,"floors":floors,
            "bays":bays,"roof":kind,"mesh_objects":len(objects),
            "vertices":sum(len(obj.data.vertices) for obj in objects)}


def build_architecture():
    """Build all detailed facades from reports/building_registry.json."""
    registry=json.loads((ROOT/"reports"/"building_registry.json").read_text())
    if isinstance(registry,dict):
        registry=registry.get("buildings",registry.get("registry",[]))
    poi_shops={"Hero_-1_1_04":"BAGERI","Hero_-1_1_03":"KAFFE & BRØD", "Cross_52_1_-80_04":"GALLERI"}
    for spec in registry:
        if str(spec["id"]) in poi_shops:
            spec["shop"]=poi_shops[str(spec["id"])]
    # This module owns only its collection, so regenerating facades preserves
    # the independently built roads, furniture, lighting and route cameras.
    old=bpy.data.collections.get(COLLECTION)
    if old:
        for obj in list(old.objects):
            bpy.data.objects.remove(obj,do_unlink=True)
    _collection()
    palette=_palette()
    result=[]
    for i,spec in enumerate(registry):
        result.append(_build_one(spec,palette))
        if i%8==0:
            print("CPH architecture",i+1,"/",len(registry),flush=True)
    summary={"buildings":len(result),"mesh_objects":sum(s["mesh_objects"] for s in result),
             "vertices":sum(s["vertices"] for s in result),"details":result}
    (ROOT/"reports"/"architecture_report.json").write_text(json.dumps(summary,indent=2))
    bpy.context.view_layer.update()
    print("CPH architecture complete:",summary["buildings"],"buildings,",summary["mesh_objects"],"mesh objects",flush=True)
    return summary


if __name__=="__main__":
    build_architecture()
