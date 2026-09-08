"""Batched, footprint-faithful Copenhagen city massing for aerial flight.

build_city_massing(geo, materials, target_xy=(1470, 460), flight_points=None)
accepts local XY metres and OSM building tags. ``materials`` may provide shared
``facades`` and ``roofs`` lists, plus optional ``roof_edge`` and ``chimney``
materials. Missing entries receive the restrained palette below. No per-building
materials or objects are created. Courtyard triangles supplied by the GIS stage
are retained, including when the roof is pitched.
"""
import hashlib
import importlib
import json
import math
import re
from collections import defaultdict

import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

COLLECTION = "Copenhagen_City_Massing"
TILE_SIZE = 400.0
GROUND_Z = 2.0


def _material(name, color, roughness=.83):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (*color, 1)
        mat.use_nodes = True
        shader = mat.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = (*color, 1)
        shader.inputs["Roughness"].default_value = roughness
    return mat


def _palette(materials):
    materials = materials or {}
    facades = materials.get("facades") or materials.get("facade")
    roofs = materials.get("roofs") or materials.get("roof")
    if not facades:
        facades = [_material("CPH_City_Facade_"+str(i), color) for i, color in enumerate([
            (.52, .445, .31), (.66, .635, .54), (.58, .385, .18),
            (.43, .445, .41), (.31, .185, .115), (.38, .17, .095),
            (.57, .55, .47), (.47, .37, .25)])]
    elif not isinstance(facades, (list, tuple)):
        facades = [facades]
    if not roofs:
        roofs = [_material("CPH_City_Roof_"+str(i), color) for i, color in enumerate([
            (.25, .095, .045), (.36, .14, .065), (.105, .13, .145),
            (.22, .25, .245), (.145, .155, .145), (.20, .31, .265)])]
    elif not isinstance(roofs, (list, tuple)):
        roofs = [roofs]
    edge = materials.get("roof_edge") or _material("CPH_City_Roof_Edge", (.20, .215, .20))
    chimney = materials.get("chimney") or _material("CPH_City_Chimney", (.28, .115, .058))
    return list(facades), list(roofs), edge, chimney


def _signed_area(ring):
    return sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(ring, ring[1:]+ring[:1]))*.5


def _ring(values, ccw=True):
    result = []
    for value in values or []:
        point = (float(value[0]), float(value[1]))
        if not all(math.isfinite(v) for v in point):
            continue
        if not result or math.dist(point, result[-1]) > .025:
            result.append(point)
    if len(result)>1 and math.dist(result[0], result[-1]) < .025:
        result.pop()
    if len(result) >= 3 and (_signed_area(result)>0) != ccw:
        result.reverse()
    return result


def _inside(point, ring):
    x, y = point
    inside = False
    for a, b in zip(ring, ring[1:]+ring[:1]):
        if (a[1]>y) != (b[1]>y):
            intersection = (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]
            if x < intersection:
                inside = not inside
    return inside


def _triangles(building, outer, holes):
    provided = building.get("triangles")
    if provided:
        result = [[(float(v[0]), float(v[1])) for v in tri] for tri in provided if len(tri)==3]
    else:
        rings = [[Vector((x, y, 0)) for x, y in ring] for ring in [outer]+holes]
        flattened = [point for ring in [outer]+holes for point in ring]
        # Blender 5.2 returns indices into the flattened input polylines;
        # earlier mathutils versions return Vector values directly.
        result = [[(v.x, v.y) if hasattr(v,"x") else flattened[int(v)]
                   for v in tri] for tri in tessellate_polygon(rings)]
    valid = []
    for tri in result:
        area = _signed_area(tri)
        if abs(area) < .0001:
            continue
        center = (sum(v[0] for v in tri)/3, sum(v[1] for v in tri)/3)
        if not _inside(center, outer) or any(_inside(center, hole) for hole in holes):
            continue
        valid.append(tri if area>0 else list(reversed(tri)))
    return valid


def _number(value):
    if value is None:
        return None
    match = re.search(r"[-+]?\d+(?:[.,]\d+)?", str(value))
    if not match:
        return None
    number = float(match.group().replace(",", "."))
    if "ft" in str(value).lower() or "'" in str(value):
        number *= .3048
    return number


def _color(value):
    value = str(value or "").strip().lower()
    named = {"white":(.78,.77,.72),"black":(.07,.075,.07),
             "grey":(.40,.42,.40),"gray":(.40,.42,.40),
             "red":(.40,.14,.07),"yellow":(.62,.44,.18),
             "brown":(.31,.18,.10),"orange":(.52,.24,.085),
             "beige":(.57,.49,.35),"green":(.20,.31,.26),
             "slategray":(.15,.18,.20),"slategrey":(.15,.18,.20)}
    if value in named:
        return named[value]
    if re.fullmatch(r"#[0-9a-f]{6}",value):
        channels = [int(value[i:i+2],16)/255 for i in (1,3,5)]
        return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in channels)
    return None


def _closest_material(color, materials):
    return min(range(len(materials)),key=lambda i:
               sum((materials[i].diffuse_color[j]-color[j])**2 for j in range(3)))


def _distance_to_route(point, route):
    best = float("inf")
    for a, b in zip(route, route[1:]):
        dx, dy = b[0]-a[0], b[1]-a[1]
        denominator = dx*dx+dy*dy
        t = max(0, min(1, ((point[0]-a[0])*dx+(point[1]-a[1])*dy)/denominator)) if denominator else 0
        best = min(best, math.hypot(point[0]-a[0]-t*dx, point[1]-a[1]-t*dy))
    if len(route)==1:
        best = math.dist(point, route[0])
    return best


def _roof_axes(outer):
    # The longest footprint edge gives a stable ridge direction for attached
    # historic houses; avoid an axis-aligned generic city-grid appearance.
    a, b = max(zip(outer, outer[1:]+outer[:1]), key=lambda pair: math.dist(*pair))
    length = max(math.dist(a, b), .001)
    ux, uy = (b[0]-a[0])/length, (b[1]-a[1])/length
    vx, vy = -uy, ux
    along = [x*ux+y*uy for x, y in outer]
    across = [x*vx+y*vy for x, y in outer]
    if max(across)-min(across) > max(along)-min(along):
        ux, uy, vx, vy = vx, vy, -ux, -uy
        across = [x*vx+y*vy for x, y in outer]
    center = (min(across)+max(across))/2
    half = max((max(across)-min(across))/2, .001)
    return vx, vy, center, half


def _clip_half(points, axes, side):
    vx, vy, center, _ = axes
    result = []
    for a, b in zip(points, points[1:]+points[:1]):
        da, db = (a[0]*vx+a[1]*vy-center)*side, (b[0]*vx+b[1]*vy-center)*side
        ina, inb = da >= -1e-7, db >= -1e-7
        if ina:
            result.append(a)
        if ina != inb:
            t = da/(da-db)
            result.append((a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1])))
    return result


class _Batch:
    def __init__(self):
        self.vertices, self.faces, self.indices = [], [], []
        self.buildings = 0

    def face(self, points, material):
        if len(points)<3:
            return
        start = len(self.vertices)
        self.vertices.extend(points)
        self.faces.append(tuple(range(start, start+len(points))))
        self.indices.append(material)

    def box(self, center, size, material):
        x, y, z = center
        a, b, c = [v/2 for v in size]
        vertices = [(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
                    (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)]
        for face in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
            self.face([vertices[i] for i in face], material)

    def beam(self, a, b, width, material):
        # Four-sided rainwater/roof-edge strip; shares the tile mesh.
        start, end = Vector(a), Vector(b)
        axis = end-start
        if axis.length < .05:
            return
        axis.normalize()
        cross = axis.cross(Vector((0,0,1)))
        if cross.length < .001:
            cross = axis.cross(Vector((0,1,0)))
        cross.normalize()
        cross *= width/2
        up = axis.cross(cross).normalized()*width/2
        vv = [tuple(p+cross*s+up*t) for p in (start,end) for s,t in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        for face in [(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(0,3,2,1),(4,5,6,7)]:
            self.face([vv[i] for i in face], material)


def _geometry(batch, outer, holes, triangles, bottom, eave, rise, axes,
              facade_index, roof_index, edge_index, chimney_index, lod, seed):
    vx, vy, center, half = axes

    def roof_z(point):
        return eave + rise*max(0, 1-abs(point[0]*vx+point[1]*vy-center)/half)

    for ring in [outer]+holes:
        for a, b in zip(ring, ring[1:]+ring[:1]):
            batch.face([(a[0],a[1],bottom),(b[0],b[1],bottom),
                        (b[0],b[1],eave),(a[0],a[1],eave)], facade_index)
            if rise:
                da, db = a[0]*vx+a[1]*vy-center, b[0]*vx+b[1]*vy-center
                segments = [(a,b)]
                if da*db < -1e-7:
                    t = da/(da-db)
                    middle = (a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1]))
                    segments = [(a,middle),(middle,b)]
                for aa, bb in segments:
                    za, zb = roof_z(aa), roof_z(bb)
                    if max(za,zb)>eave+.002:
                        batch.face([(aa[0],aa[1],eave),(bb[0],bb[1],eave),
                                    (bb[0],bb[1],zb),(aa[0],aa[1],za)], facade_index)
            if lod==3 and math.dist(a,b)>.8:
                batch.beam((a[0],a[1],eave+.06),(b[0],b[1],eave+.06),.12,edge_index)
    for tri in triangles:
        pieces = [_clip_half(tri, axes, side) for side in (-1,1)] if rise else [tri]
        for piece in pieces:
            if len(piece)<3:
                continue
            vertices = [(x,y,roof_z((x,y))) for x,y in piece]
            for i in range(1,len(vertices)-1):
                batch.face([vertices[0],vertices[i],vertices[i+1]], roof_index)
    if lod==3 and triangles and eave>6:
        # Interior roof points are selected from real footprint triangles so
        # chimney stacks cannot float in courtyard holes.
        ranked = sorted(triangles, key=lambda tri: abs(_signed_area(tri)), reverse=True)
        count = 1 if len(outer)<12 else 2
        for i, tri in enumerate(ranked[:count]):
            x, y = sum(v[0] for v in tri)/3, sum(v[1] for v in tri)/3
            z = roof_z((x,y))
            height = .9+(seed%5)*.12
            batch.box((x,y,z+height/2-.08),(.65,.62,height),chimney_index)
            batch.box((x,y,z+height-.04),(.77,.74,.12),edge_index)


def build_city_massing(geo, materials, target_xy=(1470,460), flight_points=None):
    """Build tile/LOD meshes from OSM polygons and return a JSON-safe report."""
    old = bpy.data.collections.get(COLLECTION)
    if old:
        for obj in list(old.objects):
            mesh = obj.data if obj.type=="MESH" else None
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh and mesh.users==0:
                bpy.data.meshes.remove(mesh)
    else:
        old = bpy.data.collections.new(COLLECTION)
        bpy.context.scene.collection.children.link(old)
    facades, roofs, edge, chimney = _palette(materials)
    palette = facades+roofs+[edge,chimney]
    roof_offset, edge_index, chimney_index = len(facades), len(facades)+len(roofs), len(palette)-1
    route = []
    for point in flight_points or []:
        if isinstance(point,dict):
            point = point.get("position", point.get("location", [point.get("x",0),point.get("y",0)]))
        route.append((float(point[0]),float(point[1])))
    landmark_override = None
    try:
        landmark_override = getattr(importlib.import_module("landmarks"), "landmark_building_override", None)
    except ImportError:
        pass
    overrides = geo.get("building_overrides", {})
    excluded = set(str(value) for value in geo.get("exclude_building_ids", []))
    batches = defaultdict(_Batch)
    stats = {"source_buildings":len(geo.get("buildings",[])), "buildings":0,
             "courtyard_buildings":0, "pitched_roofs":0, "flat_roofs":0,
             "lod_counts":{"1":0,"2":0,"3":0}, "skipped":[],
             "source":"OpenStreetMap building footprints; local metre coordinates",
             "lod3_radius_m":200, "tile_size_m":TILE_SIZE}
    for number, building in enumerate(geo.get("buildings", [])):
        ident = str(building.get("id",number))
        if ident in excluded or building.get("skip_massing"):
            continue
        outer = _ring(building.get("outer", []))
        holes = [ring for ring in (_ring(r,False) for r in building.get("holes",[])) if len(ring)>=3]
        if len(outer)<3:
            stats["skipped"].append({"id":ident,"reason":"invalid outer polygon"})
            continue
        area = abs(_signed_area(outer))-sum(abs(_signed_area(h)) for h in holes)
        if area<2:
            continue
        triangles = _triangles(building,outer,holes)
        if not triangles:
            stats["skipped"].append({"id":ident,"reason":"roof triangulation empty"})
            continue
        centroid = (sum(p[0] for p in outer)/len(outer),sum(p[1] for p in outer)/len(outer))
        target_distance = math.dist(centroid,target_xy)
        route_distance = _distance_to_route(centroid,route)
        lod = 3 if target_distance<=200 else (2 if target_distance<=850 or route_distance<=220 else 1)
        tags = building.get("tags",{}) or {}
        seed = int.from_bytes(hashlib.blake2b(ident.encode(),digest_size=4).digest(),"little")
        axes = _roof_axes(outer)
        shape = str(tags.get("roof:shape","")).lower()
        kind = str(tags.get("building","")).lower()
        small = area<45 or kind in {"garage","garages","shed","hut","outbuilding","service",
                                    "allotment_house","carport","roof","cabin","static_caravan"}
        house = kind in {"house","detached","semidetached_house","terrace","bungalow"}
        industrial = kind in {"industrial","warehouse","hangar","retail","supermarket"}
        levels = _number(tags.get("building:levels"))
        total_height = _number(tags.get("height"))
        bottom = max(0, _number(tags.get("min_height")) or 0)
        # Untagged historic perimeter buildings are usually three to five
        # storeys; small courtyard service volumes remain proportionate.
        default_eave = (3.0+(seed%4)*.50 if small else
                        (5.6+(seed%4)*.75 if house else
                         (7.0+(seed%4)*1.1 if industrial else
                          (6.5+(seed%3)*1.25 if math.hypot(*centroid)>3000 and area<220
                           else 12.2+(seed%6)*1.45))))
        eave = levels*3.05+1.0 if levels else default_eave
        pitched = shape in {"gabled","hipped","half-hipped","gambrel","mansard","saltbox"}
        if not shape:
            pitched = not industrial and not small and area<2200 and axes[3]<24 and seed%100 < (66 if lod==1 else 82)
        if shape in {"flat","dome","onion","pyramidal","skillion"}:
            pitched = False
        rise = (_number(tags.get("roof:height")) or min(3.9,max(1.35,axes[3]*.36))) if pitched else 0
        if total_height and total_height>0:
            eave = max(bottom+2,total_height-rise)
        override = overrides.get(ident)
        if not override and landmark_override:
            override = landmark_override(ident,tags,centroid)
        if override:
            eave = float(override.get("eave_height",override.get("height",eave)))
            if override.get("suppress_roof"):
                rise=0
            elif "roof_height" in override:
                rise=float(override["roof_height"])
        elif kind in {"church","cathedral","civic","townhall"} and eave>35 and area>500:
            # Tall landmark tags frequently describe their spire, not the
            # entire occupied footprint. Landmark accents supply the towers.
            eave=20 if kind in {"church","cathedral"} else 24
            rise=min(rise,5)
        eave = max(bottom+1.8,min(eave,180))
        facade_index = seed%len(facades)
        facade_color = _color(tags.get("building:colour",tags.get("building:color")))
        if facade_color:
            facade_index = _closest_material(facade_color,facades)
        roof_choice = (seed//7)%min(len(roofs),4)
        if not rise:
            roof_choice = min(4,len(roofs)-1)
        if any(word in str(tags.get("roof:material","")).lower() for word in ("copper","verdigris")):
            roof_choice=min(5,len(roofs)-1)
        elif "slate" in str(tags.get("roof:material","")).lower():
            roof_choice=min(2,len(roofs)-1)
        roof_color = _color(tags.get("roof:colour",tags.get("roof:color")))
        if roof_color:
            roof_choice = _closest_material(roof_color,roofs)
        key = (math.floor(centroid[0]/TILE_SIZE),math.floor(centroid[1]/TILE_SIZE),lod)
        batch = batches[key]
        _geometry(batch,outer,holes,triangles,bottom+GROUND_Z,eave+GROUND_Z,rise,axes,facade_index,
                  roof_offset+roof_choice,edge_index,chimney_index,lod,seed)
        batch.buildings += 1
        stats["buildings"] += 1
        stats["courtyard_buildings"] += bool(holes)
        stats["pitched_roofs" if rise else "flat_roofs"] += 1
        stats["lod_counts"][str(lod)] += 1
        if number and number%2500==0:
            print("City footprints processed:",number,"/",stats["source_buildings"],flush=True)
    stats.update(mesh_objects=0,vertices=0,faces=0)
    for (tile_x,tile_y,lod),batch in sorted(batches.items()):
        name="CPH_City_Tile_%s_%s_LOD%s" % (tile_x,tile_y,lod)
        mesh=bpy.data.meshes.new(name)
        mesh.from_pydata(batch.vertices,[],batch.faces)
        mesh.update()
        for material in palette:
            mesh.materials.append(material)
        mesh.polygons.foreach_set("material_index",batch.indices)
        obj=bpy.data.objects.new(name,mesh)
        old.objects.link(obj)
        obj["building_count"]=batch.buildings
        obj["lod"]=lod
        obj["source"]="OpenStreetMap / ODbL"
        obj["footprint_based"]=True
        obj["ground_datum_m"]=GROUND_Z
        stats["mesh_objects"]+=1
        stats["vertices"]+=len(batch.vertices)
        stats["faces"]+=len(batch.faces)
        # Release Python geometry as each Blender mesh takes ownership. This
        # matters for an 80k-footprint city and does not change scene detail.
        batch.vertices.clear()
        batch.faces.clear()
        batch.indices.clear()
    bpy.context.scene["city_massing_stats"]=json.dumps(stats)
    bpy.context.view_layer.update()
    print("Copenhagen aerial massing:",stats["buildings"],"buildings,",stats["mesh_objects"],
          "tile meshes,",stats["faces"],"faces",flush=True)
    return stats
