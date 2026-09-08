"""Prepare genuine OSM geometry, in local metres, for Blender without GIS deps.

Requires Shapely >= 2.1. Coast polygons use actual directed OSM shorelines and
only the rectangular extract boundary to close the map. No fictional land is
added. Polygon holes and constrained triangulations are exported explicitly.
"""
import json
import math
from pathlib import Path
from collections import Counter
from shapely import make_valid, constrained_delaunay_triangles, STRtree
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union, polygonize
from shapely.geometry.polygon import orient

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
ORIGIN=(12.5683,55.6761)
BBOX=(12.48,55.625,12.67,55.735)
SCALE_X=111320*math.cos(math.radians(ORIGIN[1]))


def xy(lon,lat):
    return ((lon-ORIGIN[0])*SCALE_X,(lat-ORIGIN[1])*111320)

MINX,MINY=xy(BBOX[0],BBOX[1])
MAXX,MAXY=xy(BBOX[2],BBOX[3])
CLIP=box(MINX,MINY,MAXX,MAXY)


def polygons(shape):
    if shape.is_empty:
        return []
    if shape.geom_type=='Polygon':
        return [shape]
    if shape.geom_type in ('MultiPolygon','GeometryCollection'):
        return [p for g in shape.geoms for p in polygons(g)]
    return []


def lines(shape):
    if shape.is_empty:
        return []
    if shape.geom_type=='LineString':
        return [shape]
    if hasattr(shape,'geoms'):
        return [p for g in shape.geoms for p in lines(g)]
    return []


def coordinates(geometry):
    return [xy(v['lon'],v['lat']) for v in geometry if v and 'lon' in v]


def element_polygon(element):
    if element['type']=='way':
        coords=coordinates(element.get('geometry',[]))
        if len(coords)>=4 and coords[0]==coords[-1]:
            return make_valid(Polygon(coords))
        return None
    if element['type']=='relation':
        outer,inner=[],[]
        for member in element.get('members',[]):
            if member.get('type')!='way' or member.get('role') in ('part','label','admin_centre'):
                continue
            coords=coordinates(member.get('geometry',[]))
            if len(coords)<2:
                continue
            (inner if member.get('role')=='inner' else outer).append(LineString(coords))
        if not outer:
            return None
        outside=list(polygonize(unary_union(outer)))
        if not outside:
            return None
        geometry=unary_union(outside)
        if inner:
            inside=list(polygonize(unary_union(inner)))
            if inside:
                geometry=geometry.difference(unary_union(inside))
        return make_valid(geometry)
    return None


def round_ring(ring):
    return [[round(x,3),round(y,3)] for x,y in list(ring.coords)[:-1]]


def packed(poly, tags=None, identifier=None, triangles=True):
    poly=orient(poly,sign=1.0)
    result={'outer':round_ring(poly.exterior), 'holes':[round_ring(r) for r in poly.interiors]}
    if tags is not None:
        result['tags']=tags
    if identifier is not None:
        result['id']=identifier
    if triangles:
        result['triangles']=[round_ring(t.exterior) for t in constrained_delaunay_triangles(poly).geoms]
    return result


def make_land(elements):
    coast=[]
    oriented_segments=[]
    for element in elements:
        if element.get('tags',{}).get('natural')!='coastline':
            continue
        points=coordinates(element.get('geometry',[]))
        if len(points)<2:
            continue
        line=LineString(points).intersection(CLIP)
        coast.extend(lines(line))
        for a,b in zip(points,points[1:]):
            if a!=b:
                segment=LineString([a,b])
                if segment.intersects(CLIP):
                    oriented_segments.append(segment)
    if not coast:
        raise RuntimeError('No real coastline was returned; refusing fictional landmass')
    pieces=list(polygonize(unary_union(coast+[CLIP.boundary])))
    tree=STRtree(oriented_segments)
    land,sea=[],[]
    decisions=[]
    for poly in pieces:
        if poly.area<1:
            continue
        p=poly.representative_point()
        segment=oriented_segments[int(tree.nearest(p))]
        a,b=list(segment.coords)
        cross=(b[0]-a[0])*(p.y-a[1])-(b[1]-a[1])*(p.x-a[0])
        # OSM coastline direction defines land on the left, sea on the right.
        (land if cross>0 else sea).append(poly)
        decisions.append({'area_m2':round(poly.area),'land':cross>0,'sample':[round(p.x,2),round(p.y,2)]})
    return unary_union(land),unary_union(sea),len(coast),decisions


def prepare():
    raw=json.loads((DATA/'osm_raw.json').read_text())
    elements=raw['elements']
    metadata=json.loads((DATA/'fetch_metadata.json').read_text())
    print('Preparing',len(elements),'OSM elements',flush=True)
    land,sea,coast_count,decisions=make_land(elements)
    print('Coastline assembled:',coast_count,'ways;',len(polygons(land)),'land polygons;',len(polygons(sea)),'sea polygons',flush=True)
    building_members=set()
    area_members=set()
    for element in elements:
        if element['type']!='relation':
            continue
        tags=element.get('tags',{})
        if 'building' in tags:
            building_members.update(m['ref'] for m in element.get('members',[]) if m.get('type')=='way' and m.get('role') in ('outer','inner','outline',''))
        if tags.get('natural') in ('water','wood','scrub','wetland','beach') or tags.get('leisure') in ('park','garden','nature_reserve','golf_course') or tags.get('landuse') in ('grass','forest','recreation_ground','cemetery','allotments'):
            area_members.update(m['ref'] for m in element.get('members',[]) if m.get('type')=='way')
    buildings,parks,roads,inland=[],[],[],[]
    landmarks=[]
    water_shapes=[]
    for count,element in enumerate(elements):
        tags=element.get('tags',{})
        if element['type']=='node':
            continue
        identifier=element['type']+'/'+str(element['id'])
        if 'building' in tags and tags.get('building') not in ('no','construction','ruins'):
            if element['type']=='way' and element['id'] in building_members:
                continue
            shape=element_polygon(element)
            if shape is None:
                continue
            for part_index,poly in enumerate(polygons(make_valid(shape.intersection(CLIP)))):
                if poly.area<8:
                    continue
                poly=poly.simplify(.13,preserve_topology=True)
                entry=packed(poly,tags,identifier,triangles=bool(poly.interiors))
                entry['area_m2']=round(poly.area,2)
                buildings.append(entry)
                name=' '.join(str(tags.get(k,'')) for k in ('name','name:en','wikidata','building'))
                if any(term.casefold() in name.casefold() for term in ('Frederik','Frelsers','Christiansborg','Rådhus','Rosenborg','Opera','Marmorkirken','Børsen')):
                    c=poly.centroid
                    landmarks.append({'id':identifier,'tags':tags,'centroid':[round(c.x,3),round(c.y,3)],'area_m2':round(poly.area),'bounds':list(poly.bounds)})
            continue
        if element['type']=='way' and ('highway' in tags or tags.get('railway')=='rail'):
            coords=coordinates(element.get('geometry',[]))
            if len(coords)>=2:
                for line in lines(LineString(coords).intersection(CLIP)):
                    if line.length>=2:
                        roads.append({'id':identifier,'points':[[round(x,3),round(y,3)] for x,y in line.simplify(.45,preserve_topology=False).coords],'tags':tags})
            continue
        if element['type']=='way' and element['id'] in area_members:
            continue
        is_water=tags.get('natural')=='water' or tags.get('waterway')=='riverbank'
        is_park=tags.get('leisure') in ('park','garden','nature_reserve','golf_course') or tags.get('landuse') in ('grass','forest','recreation_ground','cemetery','allotments') or tags.get('natural') in ('wood','scrub','wetland','beach')
        if not (is_water or is_park):
            continue
        shape=element_polygon(element)
        if shape is None:
            continue
        for poly in polygons(make_valid(shape.intersection(CLIP))):
            if poly.area<15:
                continue
            poly=poly.simplify(.45 if is_water else .75,preserve_topology=True)
            if is_water:
                water_shapes.append(poly)
                inland.append(packed(poly,tags,identifier))
            else:
                parks.append(packed(poly,tags,identifier))
    all_water=unary_union([sea]+water_shapes)
    land=make_valid(land.difference(unary_union(water_shapes)))
    land_records=[packed(p.simplify(.55,preserve_topology=True)) for p in polygons(land) if p.area>10]
    water_records=[packed(p.simplify(.55,preserve_topology=True)) for p in polygons(all_water) if p.area>10]
    output={'origin':{'lon':ORIGIN[0],'lat':ORIGIN[1],'projection':'local equirectangular; metres east/north; Z up'},
            'bounds':{'west':BBOX[0],'south':BBOX[1],'east':BBOX[2],'north':BBOX[3], 'min_x':MINX,'min_y':MINY,'max_x':MAXX,'max_y':MAXY},
            'buildings':buildings,'land':land_records,'water':water_records,'parks':parks,'roads':roads,
            'sources':[{'name':'OpenStreetMap contributors','url':'https://www.openstreetmap.org/copyright','license':'ODbL 1.0','attribution':'© OpenStreetMap contributors'},
                       {'name':'Overpass API extract','url':metadata['endpoint'],'osm_timestamp':raw.get('osm3s',{}).get('timestamp_osm_base'),'retrieved_utc':metadata['retrieved_utc']},
                       {'name':'Coastline direction convention','url':'https://wiki.openstreetmap.org/wiki/Tag:natural%3Dcoastline'}],
            'processing':{'coastline':'Real directed OSM coastlines polygonized against rectangular extract boundary; left side is land','simplification_m':{'land_water':.55,'parks':.75,'building':.13,'roads':.45},'building_heights':'Tags preserved; no heights fabricated in source data','courtyards':'Inner rings preserved; constrained Delaunay roof triangles provided for courtyard buildings'}}
    (DATA/'copenhagen_geo.json').write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')))
    (DATA/'landmarks_osm.json').write_text(json.dumps(landmarks,ensure_ascii=False,indent=2))
    summary={'counts':{key:len(output[key]) for key in ('buildings','land','water','parks','roads')},'land_area_km2':land.area/1e6,'water_area_km2':all_water.area/1e6,'bbox_area_km2':CLIP.area/1e6,'coastline_ways':coast_count,'coast_polygons':decisions,'courtyard_buildings':sum(bool(b['holes']) for b in buildings),'named_landmarks':len(landmarks)}
    (DATA/'geography_report.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2),flush=True)
    return output



def preview_and_validate():
    """Create small map previews and verify harbor coordinates against GIS."""
    from PIL import Image, ImageDraw
    output=json.loads((DATA/'copenhagen_geo.json').read_text())
    shapes={key:unary_union([make_valid(Polygon(p['outer'],p['holes'])) for p in output[key]]) for key in ('land','water')}
    checks=[]
    # Geographically fixed sample points; classifications are computed from
    # actual extracted OSM boundaries, never used to generate the coast.
    samples=[('Nyhavn canal centre',12.59075,55.67978,'water'),
             ('Nyhavn north quay',12.59075,55.68015,'land'),
             ('Christianshavns Kanal centre',12.5908283,55.6724288,'water'),
             ('Christianshavn east bank',12.59150,55.6724288,'land'),
             ('Inner harbour',12.594,55.6777,'water'),
             ('Kongens Nytorv',12.58515,55.68051,'land')]
    for name,lon,lat,expected in samples:
        point=Point(xy(lon,lat))
        actual='land' if shapes['land'].contains(point) else 'water' if shapes['water'].contains(point) else 'outside'
        checks.append({'name':name,'lon':lon,'lat':lat,'xy':[round(point.x,3),round(point.y,3)],'expected':expected,'actual':actual,'pass':expected==actual})
    for filename,bounds,size in [('geography_preview.png',(MINX,MINY,MAXX,MAXY),1800),
                                  ('harbour_preview.png',(-200,-1200,3100,1900),1600)]:
        x0,y0,x1,y1=bounds
        width=size
        height=round(size*(y1-y0)/(x1-x0))
        image=Image.new('RGB',(width,height),(89,130,143))
        draw=ImageDraw.Draw(image)
        def pt(p):
            return ((p[0]-x0)/(x1-x0)*width,height-(p[1]-y0)/(y1-y0)*height)
        for key,color in [('land',(210,205,187)),('parks',(143,160,122))]:
            for record in output[key]:
                if max(p[0] for p in record['outer'])<x0 or min(p[0] for p in record['outer'])>x1:
                    continue
                for triangle in record['triangles']:
                    draw.polygon([pt(p) for p in triangle],fill=color)
        for road in output['roads']:
            if road['tags'].get('highway') in ('motorway','trunk','primary','secondary','tertiary','residential','unclassified','living_street'):
                draw.line([pt(p) for p in road['points']],fill=(239,232,211),width=2 if filename.startswith('harbour') else 1)
        for building in output['buildings']:
            if max(p[0] for p in building['outer'])<x0 or min(p[0] for p in building['outer'])>x1:
                continue
            draw.polygon([pt(p) for p in building['outer']],fill=(134,112,95))
            for hole in building['holes']:
                draw.polygon([pt(p) for p in hole],fill=(210,205,187))
        if filename.startswith('harbour'):
            for check in checks:
                x,y=pt(check['xy'])
                draw.ellipse((x-4,y-4,x+4,y+4),fill=(255,241,83))
                draw.text((x+7,y-8),check['name'],fill=(35,33,30))
        image.save(DATA/filename)
    (DATA/'harbour_control_points.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps(checks,indent=2))
    print('Preview PNG files written')
    return checks


def prepare_context():
    """Prepare surrounding real Zealand/Amager/Øresund coast at same origin."""
    global CLIP
    west,south,east,north=12.25,55.50,12.90,55.92
    x0,y0=xy(west,south)
    x1,y1=xy(east,north)
    old_clip=CLIP
    CLIP=box(x0,y0,x1,y1)
    raw=json.loads((DATA/'context_coastline_raw.json').read_text())
    try:
        land,water,coast_count,decisions=make_land(raw['elements'])
    finally:
        CLIP=old_clip
    # Leave the entire detailed core aperture open; the context layer must not
    # fill inland lakes or canals beneath the detailed ground's holes.
    land=make_valid(land.difference(old_clip))
    output={'origin':{'lon':ORIGIN[0],'lat':ORIGIN[1],'projection':'local equirectangular; metres east/north; Z up'},
            'bounds':{'west':west,'south':south,'east':east,'north':north,'min_x':x0,'min_y':y0,'max_x':x1,'max_y':y1},
            'land':[packed(p.simplify(2.5,preserve_topology=True)) for p in polygons(land) if p.area>20],
            'water':[packed(p.simplify(2.5,preserve_topology=True)) for p in polygons(water) if p.area>20],
            'sources':[{'name':'OpenStreetMap contributors','url':'https://www.openstreetmap.org/copyright','license':'ODbL 1.0','attribution':'© OpenStreetMap contributors'},
                       {'name':'Overpass coastline extract','url':'https://overpass-api.de/api/interpreter','osm_timestamp':raw.get('osm3s',{}).get('timestamp_osm_base')}],
            'processing':{'coastline_ways':coast_count,'simplification_m':2.5,'geometry':'Real directed OSM shoreline polygonized against 40.8 km by 46.8 km map boundary; land-left convention; complete core rectangle removed from context land'}}
    (DATA/'context_geography.json').write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')))
    print('Context geography ready:',len(output['land']),'land polygons;',len(output['water']),'water polygons;',coast_count,'coastline ways')
    return output


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--preview',action='store_true')
    parser.add_argument('--context',action='store_true')
    options=parser.parse_args()
    if options.preview:
        preview_and_validate()
    elif options.context:
        prepare_context()
    else:
        prepare()
