"""Source-positioned Copenhagen skyline accents for an aerial city model.

This module keeps the OSM building footprint masses.  It supplies their eave
overrides and adds only identifying roof and tower silhouettes above them.
No windows, pavement, street props or invented building footprints are added.
"""
from pathlib import Path
import json
import math
import re
from collections import defaultdict

import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
ORIGIN_LON=12.5683
ORIGIN_LAT=55.6761
GROUND=2.0
COLLECTION="04_Landmark_Accents"

# OSM identifiers are from the downloaded source, not search-result place pins.
SPECS={
    "marble_church":{"id":25524833,"type":"way","name":"Frederiks Kirke / Marmorkirken","eave":22.,"height":79.,"suppress_roof":True},
    "our_saviour":{"id":25607908,"type":"way","name":"Vor Frelsers Kirke","eave":22.,"height":90.,"suppress_roof":False},
    "christiansborg":{"id":25992657,"type":"way","name":"Christiansborg Slot","eave":27.,"height":106.,"suppress_roof":False},
    "city_hall":{"id":52142,"type":"relation","name":"Københavns Rådhus","eave":24.,"height":105.6,"suppress_roof":False},
    "rosenborg":{"id":25524592,"type":"way","name":"Rosenborg Slot","eave":13.8,"height":50.6,"suppress_roof":True},
    "opera":{"id":1088494374,"type":"way","name":"Operaen på Holmen","eave":29.,"height":38.,"suppress_roof":True},
    "amalienborg_nw":{"id":25524645,"type":"way","name":"Christian den VIII's Palæ","eave":16.,"height":24.,"suppress_roof":False},
    "amalienborg_sw":{"id":106105298,"type":"way","name":"Christian den VII's Palæ","eave":16.,"height":24.,"suppress_roof":False},
    "amalienborg_se":{"id":106105466,"type":"way","name":"Christian den IX's Palæ","eave":16.,"height":24.,"suppress_roof":False},
    "amalienborg_ne":{"id":106228713,"type":"way","name":"Frederik den VIII's Palæ","eave":16.,"height":24.,"suppress_roof":False},
}
_BY_ID={spec["id"]:spec for spec in SPECS.values()}


def landmark_building_override(building_id,tags=None,centroid=None):
    """Mass-builder hook: eave below the skyline accent, preserving footprint.

    Heights are above the shared 2 m ground datum.  Generic gable/hip roofs are
    suppressed only where this module supplies a replacement roof silhouette.
    """
    match=re.search(r"(\d+)$",str(building_id))
    spec=_BY_ID.get(int(match.group(1))) if match else None
    if spec is None:
        return None
    return {"eave_height":spec["eave"],"suppress_roof":spec["suppress_roof"],
            "landmark_name":spec["name"],"height_source":"source-guided aerial eave estimate"}


def project(lon,lat):
    return ((lon-ORIGIN_LON)*111320.*math.cos(math.radians(ORIGIN_LAT)),
            (lat-ORIGIN_LAT)*111320.)


def _collection():
    collection=bpy.data.collections.get(COLLECTION)
    if collection is None:
        collection=bpy.data.collections.new(COLLECTION)
        bpy.context.scene.collection.children.link(collection)
    return collection


def _mat(name,color,roughness=.65,metallic=0):
    mat=bpy.data.materials.get("LM_"+name)
    if mat:return mat
    mat=bpy.data.materials.new("LM_"+name)
    mat.use_nodes=True
    mat.diffuse_color=(*color,1)
    nodes=mat.node_tree.nodes
    links=mat.node_tree.links
    shader=nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value=(*color,1)
    shader.inputs["Roughness"].default_value=roughness
    shader.inputs["Metallic"].default_value=metallic
    noise=nodes.new("ShaderNodeTexNoise")
    coord=nodes.new("ShaderNodeTexCoord")
    noise.inputs["Scale"].default_value=.38
    noise.inputs["Detail"].default_value=2
    links.new(coord.outputs["Object"],noise.inputs["Vector"])
    ramp=nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color=(*[v*.83 for v in color],1)
    ramp.color_ramp.elements[1].color=(*[min(v*1.08,.95) for v in color],1)
    links.new(noise.outputs["Fac"],ramp.inputs[0])
    links.new(ramp.outputs["Color"],shader.inputs["Base Color"])
    return mat


def _palette():
    return {"stone":_mat("warm_limestone",(.57,.555,.49),.8),
            "pale":_mat("marble",(.69,.705,.665),.76),
            "brick":_mat("red_brick",(.33,.115,.063),.85),
            "copper":_mat("patinated_copper",(.14,.27,.225),.65,.40),
            "darkcopper":_mat("dark_patinated_copper",(.068,.11,.105),.60,.45),
            "roof":_mat("palace_slate",(.11,.13,.14),.75),
            "gold":_mat("weathered_gilt",(.62,.41,.105),.42,.68),
            "metal":_mat("opera_roof_zinc",(.33,.37,.37),.63,.38),
            "dark":_mat("belfry_void",(.018,.025,.026),.85)}


class MeshBatch:
    def __init__(self):self.parts=defaultdict(lambda:[[],[]])
    def mesh(self,mat,vertices,faces):
        vv,ff=self.parts[mat]; start=len(vv)
        vv.extend(vertices); ff.extend([tuple(start+i for i in face) for face in faces])
    def box(self,mat,center,size,angle=0):
        x,y,z=center; w,d,h=[v/2 for v in size]
        c,s=math.cos(angle),math.sin(angle)
        verts=[(x+u*c-v*s,y+u*s+v*c,z+zz) for zz in [-h,h]
               for u,v in [(-w,-d),(w,-d),(w,d),(-w,d)]]
        self.mesh(mat,verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    def lathe(self,mat,xy,profile,segments=32,angle=0):
        x,y=xy
        verts=[(x+r*math.cos(i*math.tau/segments+angle),y+r*math.sin(i*math.tau/segments+angle),GROUND+z)
               for z,r in profile for i in range(segments)]
        faces=[]
        for row in range(len(profile)-1):
            for i in range(segments):
                j=(i+1)%segments
                faces.append((row*segments+i,row*segments+j,(row+1)*segments+j,(row+1)*segments+i))
        faces += [tuple(reversed(range(segments))),tuple(range((len(profile)-1)*segments,len(profile)*segments))]
        self.mesh(mat,verts,faces)
    def rod(self,mat,points,radius,sides=6):
        vertices=[]
        for i,pp in enumerate(points):
            center=Vector(pp)
            tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
            if tangent.length<1e-6:tangent=Vector((0,0,1))
            tangent.normalize()
            helper=Vector((0,0,1)) if abs(tangent.z)<.85 else Vector((1,0,0))
            u=tangent.cross(helper).normalized()*radius
            v=tangent.cross(u).normalized()*radius
            for j in range(sides):
                a=j*math.tau/sides;vertices.append(tuple(center+u*math.cos(a)+v*math.sin(a)))
        faces=[]
        for row in range(len(points)-1):
            for j in range(sides):faces.append((row*sides+j,row*sides+(j+1)%sides,(row+1)*sides+(j+1)%sides,(row+1)*sides+j))
        self.mesh(mat,vertices,faces)
    def finish(self,name):
        objects=[]
        for material,(verts,faces) in self.parts.items():
            mesh=bpy.data.meshes.new(name+"_"+material.name)
            mesh.from_pydata(verts,[],faces);mesh.update()
            obj=bpy.data.objects.new(name+"_"+material.name,mesh)
            _collection().objects.link(obj);obj.data.materials.append(material)
            objects.append(obj)
        return objects


def _raw_features():
    path=ROOT/"data"/"osm_raw.json"
    if not path.exists():raise FileNotFoundError("Landmarks require downloaded source OSM: "+str(path))
    elements=json.loads(path.read_text()).get("elements",[])
    # Focused tower building-parts, when supplied by the geography fetcher.
    for name in ["landmark_parts_raw.json","landmark_parts.json","osm_landmark_parts.json","landmark_building_parts.json"]:
        extra=ROOT/"data"/name
        if extra.exists():elements+=json.loads(extra.read_text()).get("elements",[])
    return elements


def _geometry(feature):
    if feature.get("geometry"):return feature["geometry"]
    return [point for member in feature.get("members",[]) if member.get("role")!="inner"
            for point in member.get("geometry",[])]


def _centroid(points):
    # A geographic centroid is sufficient at this small local projection scale.
    ring=[(p["lon"],p["lat"]) for p in points]
    if ring[0]==ring[-1]:ring=ring[:-1]
    # Shift coordinates first to keep shoelace arithmetic numerically stable.
    ox,oy=ring[0];r=[(x-ox,y-oy) for x,y in ring]
    area=sx=sy=0
    for i,(x,y) in enumerate(r):
        xx,yy=r[(i+1)%len(r)];cross=x*yy-xx*y
        area+=cross;sx+=(x+xx)*cross;sy+=(y+yy)*cross
    if abs(area)<1e-16:return (sum(x for x,y in ring)/len(ring),sum(y for x,y in ring)/len(ring))
    return ox+sx/(3*area),oy+sy/(3*area)


def _oriented_box(points):
    pts=[project(p["lon"],p["lat"]) for p in points]
    best=None
    for i,(x,y) in enumerate(pts):
        xx,yy=pts[(i+1)%len(pts)]
        if math.hypot(xx-x,yy-y)<.5:continue
        angle=math.atan2(yy-y,xx-x);c,s=math.cos(angle),math.sin(angle)
        rotated=[(px*c+py*s,-px*s+py*c) for px,py in pts]
        minx=min(p[0] for p in rotated);maxx=max(p[0] for p in rotated)
        miny=min(p[1] for p in rotated);maxy=max(p[1] for p in rotated)
        area=(maxx-minx)*(maxy-miny)
        if best is None or area<best[0]:best=(area,angle,minx,maxx,miny,maxy)
    _,angle,minx,maxx,miny,maxy=best
    c,s=math.cos(angle),math.sin(angle);u=(minx+maxx)/2;v=(miny+maxy)/2
    width,depth=maxx-minx,maxy-miny
    if depth>width:angle+=math.pi/2;width,depth=depth,width
    return (u*c-v*s,u*s+v*c),angle,width,depth


def _part_candidates(features,center,radius=90):
    cx,cy=project(*center);result=[]
    for element in features:
        tags=element.get("tags",{})
        if not (tags.get("building:part") or tags.get("man_made")=="tower"):continue
        points=_geometry(element)
        if not points:continue
        lon,lat=_centroid(points);x,y=project(lon,lat)
        if math.hypot(x-cx,y-cy)<radius:result.append((element,(lon,lat)))
    return result


def _number(value,default=0):
    try:return float(re.search(r"[\d.]+",str(value)).group())
    except:return default


def _tower_point(features,feature,kind):
    center=_centroid(_geometry(feature))
    exact_ids={"marble_church":382667658,"our_saviour":1012313938,
               "christiansborg":381955936,"city_hall":1011067074}
    source=next((f for f in features if f["type"]=="way" and f["id"]==exact_ids.get(kind)),None)
    if source is not None:
        return _centroid(_geometry(source)),"OSM way/"+str(source["id"]),source
    candidates=_part_candidates(features,center,200 if kind=="christiansborg" else 125)
    ranked=[]
    for element,point in candidates:
        tags=element.get("tags",{})
        height=_number(tags.get("height"))
        label=" ".join(str(tags.get(k,"")) for k in ["name","building:part","tower:type","roof:shape"])
        score=height + (60 if any(x in label.lower() for x in ["tower","tårn","spire"]) else 0)
        if kind=="our_saviour" and height>60:score+=100
        if kind=="city_hall" and height>95:score+=100
        if kind=="christiansborg" and height>95:score+=100
        if score>45:ranked.append((score,element,point))
    if ranked:
        _,element,point=max(ranked,key=lambda value:value[0])
        return point,"OSM "+element["type"]+"/"+str(element["id"]),element
    # The current source may map a tower as part of the outline rather than a
    # separate part. In that case use the directly measured OSM outline center,
    # and record that reduced positional specificity in the build statistics.
    return center,"OSM footprint centroid (no separate tower part)",None


def _marble(batch,p,xy):
    batch.lathe(p["pale"],xy,[(22,19.6),(24,19.6),(24,18.4),(35.6,18.4),(36.6,19.3)],64)
    profile=[(36.6+17.3*math.sin(i*math.pi/2/20),17.95*math.cos(i*math.pi/2/20)) for i in range(20)]
    profile.append((53.9,2.5));batch.lathe(p["copper"],xy,profile,64)
    x,y=xy
    for i in range(16):
        a=i*math.tau/16
        batch.rod(p["copper"],[(x+18.1*math.cos(a)*math.cos(t),y+18.1*math.sin(a)*math.cos(t),GROUND+36.6+17.5*math.sin(t))
                              for t in [j*math.pi/2/20 for j in range(19)]],.15,6)
        batch.lathe(p["pale"],(x+18.6*math.cos(a),y+18.6*math.sin(a)),[(24,.45),(35,.45)],8)
    batch.lathe(p["pale"],xy,[(54,3.4),(55.1,3.4),(55.1,2.4),(61.5,2.4)],24)
    batch.lathe(p["copper"],xy,[(61.5,3.4),(63,3.1),(65.3,1.25),(68.6,.82),(75.5,.28),(77,.16)],24)
    batch.rod(p["gold"],[(x,y,GROUND+76),(x,y,GROUND+79)],.13,8)
    batch.rod(p["gold"],[(x-.7,y,GROUND+78),(x+.7,y,GROUND+78)],.11,8)


def _saviour(batch,p,xy,angle):
    x,y=xy
    batch.box(p["brick"],(x,y,GROUND+34),(10.5,10.5,24),angle)
    for z in [31,36.3,46]:batch.box(p["stone"],(x,y,GROUND+z),(11.3,11.3,.7),angle)
    batch.lathe(p["darkcopper"],xy,[(46,7.3),(50,6.5),(56,5.4),(59,5.2),(80,.58)],8,angle+math.pi/8)
    batch.lathe(p["gold"],xy,[(55.5,5.7),(56,5.7)],32)
    spiral=[]
    for i in range(193):
        t=i/192;angle_sp=t*math.tau*4;radius=5.7*(1-t)+.60*t
        spiral.append((x+radius*math.cos(angle_sp),y+radius*math.sin(angle_sp),GROUND+56+t*24))
    batch.rod(p["gold"],spiral,.19,6)
    batch.lathe(p["darkcopper"],xy,[(80,.65),(81.5,1.05),(82.5,.65)],24)
    batch.lathe(p["gold"],xy,[(82.5,.05),(82.8,.85),(83.7,1.2),(84.5,.85),(85,.10)],24)
    batch.rod(p["gold"],[(x,y,GROUND+85),(x,y,GROUND+90)],.24,8)
    batch.rod(p["gold"],[(x-.8,y,GROUND+89),(x+.8,y,GROUND+89)],.16,8)


def _christiansborg(batch,p,xy,angle):
    x,y=xy
    batch.box(p["stone"],(x,y,GROUND+44),(17,17,34),angle)
    for z,w in [(29,18),(51,18.2),(61,19)]:batch.box(p["stone"],(x,y,GROUND+z),(w,w,.85),angle)
    batch.lathe(p["copper"],xy,[(61,12.4),(65,10.4),(70,8.4),(73,7.0),(78,6.4),(80,7.4),
                              (82,6.0),(91,3.1),(94,2.3),(98,1.2),(101,.45)],8,angle+math.pi/8)
    for z,r in [(82,5.1),(92,2.8),(99,1.4)]:
        batch.lathe(p["gold"],xy,[(z,r),(z+.65,r+.15)],24)
        for i in range(8):
            a=i*math.tau/8
            batch.rod(p["gold"],[(x+r*math.cos(a),y+r*math.sin(a),GROUND+z+.4),
                                  (x+r*.94*math.cos(a),y+r*.94*math.sin(a),GROUND+z+1.8)],.14,6)
    batch.rod(p["gold"],[(x,y,GROUND+101),(x,y,GROUND+106)],.15,8)


def _cityhall(batch,p,xy,angle):
    x,y=xy
    batch.box(p["brick"],(x,y,GROUND+47.5),(12.2,12.2,47),angle)
    for z,width in [(58,12.8),(70,14.4),(81,14.5)]:batch.box(p["stone"],(x,y,GROUND+z),(width,width,.7),angle)
    # Open belfry silhouette with four red masonry piers, not black decals.
    for sx in [-1,1]:
        for sy in [-1,1]:
            xx=sx*4.65;yy=sy*4.65;c,s=math.cos(angle),math.sin(angle)
            batch.box(p["brick"],(x+xx*c-yy*s,y+xx*s+yy*c,GROUND+75.6),(2.7,2.7,10),angle)
    batch.lathe(p["copper"],xy,[(81,10.5),(86,7.3),(96,3.4),(100,.75),(104,.1)],4,angle+math.pi/4)
    batch.rod(p["gold"],[(x,y,GROUND+102),(x,y,GROUND+105.6)],.16,8)


def _hip_roof(batch,mat,xy,width,depth,base,rise,angle):
    x,y=xy;c,s=math.cos(angle),math.sin(angle)
    hip=min(depth*.48,width*.20)
    coords=[(-width/2,-depth/2,base),(width/2,-depth/2,base),(width/2,depth/2,base),
            (-width/2,depth/2,base),(-width/2+hip,0,base+rise),(width/2-hip,0,base+rise)]
    verts=[(x+u*c-v*s,y+u*s+v*c,GROUND+z) for u,v,z in coords]
    batch.mesh(mat,verts,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)])


def _rosenborg(batch,p,xy,angle,width,depth,parts):
    width=min(width,69);depth=min(depth,24)
    _hip_roof(batch,p["copper"],xy,width,depth,13.8,6.6,angle)
    # If separately mapped turrets are supplied, their source centroids win.
    turrets=[]
    turret_ids={383465284:50.6,383510582:36.2,383510580:36.2}
    for element,point in parts:
        tags=element.get("tags",{})
        if element.get("id") in turret_ids:
            turrets.append((project(*point),turret_ids[element["id"]]))
    if not turrets:
        # Source-outline-derived positions: three attached roof silhouettes on
        # the castle's measured long axis, explicitly recorded as approximations.
        c,s=math.cos(angle),math.sin(angle);x,y=xy
        for u,v in [(-width*.32,depth*.20),(width*.32,depth*.20),(0,-depth*.35)]:
            turrets.append(((x+u*c-v*s,y+u*s+v*c),50.6 if u==0 else 36.2))
    for center,height in turrets[:3]:
        is_main=height>40;scale=1.12 if is_main else .78
        body_top=27.2 if is_main else 26
        batch.lathe(p["brick"],center,[(13.8,3.2*scale),(body_top,3.2*scale)],8)
        crown=height-body_top
        profile=[(body_top+crown*t,r*scale) for t,r in [(0,3.8),(.14,4),(.36,2.1),(.48,2.3),(.70,1.2),(.97,.10)]]
        batch.lathe(p["copper"],center,profile,16)
        batch.rod(p["gold"],[(center[0],center[1],GROUND+height-1.8),(center[0],center[1],GROUND+height)],.10,6)


def _opera(batch,p,xy,angle):
    x,y=xy
    # The 158 x 90 m canopy is documented by the roof engineering supplier.
    batch.box(p["metal"],(x,y,GROUND+32.5),(158,90,2.2),angle)
    c,s=math.cos(angle),math.sin(angle)
    batch.box(p["stone"],(x+19*c,y+19*s,GROUND+35.0),(35,48,6),angle)
    batch.box(p["darkcopper"],(x+19*c,y+19*s,GROUND+38.3),(37,50,.7),angle)


def build_landmarks(materials=None):
    """Add geographically registered silhouette accents; return audit metadata."""
    collection=_collection()
    for obj in list(collection.objects):bpy.data.objects.remove(obj,do_unlink=True)
    features=_raw_features()
    lookup={(f["type"],f["id"]):f for f in features}
    p=_palette();results=[]
    for key,spec in SPECS.items():
        feature=lookup.get((spec["type"],spec["id"]))
        if feature is None:
            raise RuntimeError("Missing verified landmark source "+str(spec["id"]))
        geom=_geometry(feature);center=_centroid(geom)
        xy,angle,width,depth=_oriented_box(geom)
        actual_center=project(*center)
        tower_source="OSM footprint centroid"
        tower_part=None
        if key in ["marble_church","our_saviour","christiansborg","city_hall"]:
            center,tower_source,tower_part=_tower_point(features,feature,key)
            actual_center=project(*center)
            orientation_ids={"our_saviour":290040529,"christiansborg":381945170,"city_hall":1011067074}
            orientation_source=lookup.get(("way",orientation_ids.get(key)))
            if orientation_source:_,angle,_,_=_oriented_box(_geometry(orientation_source))
        batch=MeshBatch()
        if key=="marble_church":_marble(batch,p,actual_center)
        elif key=="our_saviour":_saviour(batch,p,actual_center,angle)
        elif key=="christiansborg":_christiansborg(batch,p,actual_center,angle)
        elif key=="city_hall":_cityhall(batch,p,actual_center,angle)
        elif key=="rosenborg":
            roof_source=lookup.get(("way",383465248))
            if roof_source:xy,angle,width,depth=_oriented_box(_geometry(roof_source))
            _rosenborg(batch,p,xy,angle,width,depth,_part_candidates(features,center,50))
        elif key=="opera":_opera(batch,p,xy,angle)
        # Amalienborg's four existing real footprints and restrained hipped
        # roof masses already supply the silhouette; do not overlay extra blocks.
        objects=batch.finish("LM_"+key)
        for obj in objects:
            obj["landmark_name"]=spec["name"]
            obj["source_osm"]=spec["type"]+"/"+str(spec["id"])
            obj["source_lon"]=center[0];obj["source_lat"]=center[1]
            obj["detail_level"]="aerial roof/tower silhouette"
        results.append({"key":key,"name":spec["name"],"osm_id":spec["type"]+"/"+str(spec["id"]),
                        "lon":center[0],"lat":center[1],"xy_m":list(actual_center),
                        "tower_position_source":tower_source,"height_m":spec["height"],
                        "height_quality":"documented total" if key in ["marble_church","our_saviour","christiansborg","city_hall"] else "aerial silhouette estimate",
                        "eave_override_m":spec["eave"],"mesh_objects":len(objects),
                        "exclude_full_footprint":False,"suppress_generic_roof":spec["suppress_roof"]})
    bpy.context.view_layer.update()
    report={"origin_lonlat":[ORIGIN_LON,ORIGIN_LAT],"ground_z":GROUND,"landmarks":results,
            "mesh_objects":sum(s["mesh_objects"] for s in results),
            "building_overrides":{str(spec["id"]):landmark_building_override(spec["id"]) for spec in SPECS.values()}}
    (ROOT/"reports").mkdir(parents=True,exist_ok=True)
    (ROOT/"reports"/"landmark_build_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print("Landmark skyline accents:",report["mesh_objects"],"mesh objects",flush=True)
    return report


if __name__=="__main__":build_landmarks()
