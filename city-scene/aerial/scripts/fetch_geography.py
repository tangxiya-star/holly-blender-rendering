"""Cache a real OSM extract for the Copenhagen aerial scene (ODbL attribution)."""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data'
BBOX = (55.625,12.48,55.735,12.67)
ENDPOINTS = ['https://overpass.private.coffee/api/interpreter', 'https://overpass-api.de/api/interpreter']
QUERY = '''[out:json][timeout:180][maxsize:536870912];
(
  way[building](55.625,12.48,55.735,12.67);
  relation[building](55.625,12.48,55.735,12.67);
  way[highway](55.625,12.48,55.735,12.67);
  way[railway=rail](55.625,12.48,55.735,12.67);
  way[natural=coastline](55.615,12.47,55.745,12.68);
  nwr[natural=water](55.625,12.48,55.735,12.67);
  nwr[waterway=riverbank](55.625,12.48,55.735,12.67);
  way[waterway~"canal|river"](55.625,12.48,55.735,12.67);
  nwr[leisure~"park|garden|nature_reserve|golf_course"](55.625,12.48,55.735,12.67);
  nwr[landuse~"grass|forest|recreation_ground|cemetery|allotments"](55.625,12.48,55.735,12.67);
  nwr[natural~"wood|scrub|wetland|beach"](55.625,12.48,55.735,12.67);
);
out body geom;'''


def fetch():
    DATA.mkdir(parents=True,exist_ok=True)
    destination = DATA/'osm_raw.json'
    if destination.exists():
        payload = json.loads(destination.read_text())
        if payload.get('elements') and not payload.get('remark'):
            print('Cached OSM elements:',len(payload['elements']),flush=True)
            return destination
    (DATA/'overpass_query.txt').write_text(QUERY)
    for endpoint in ENDPOINTS:
        print('Downloading',endpoint,flush=True)
        try:
            req=urllib.request.Request(endpoint,data=urllib.parse.urlencode({'data':QUERY}).encode(),
                headers={'User-Agent':'Copenhagen-Blender-GIS-Hackathon/1.0 (one-time geographic visualization)','Accept-Encoding':'gzip'})
            with urllib.request.urlopen(req,timeout=220) as response:
                raw=response.read()
                if response.headers.get('Content-Encoding')=='gzip':
                    import gzip
                    raw=gzip.decompress(raw)
            payload=json.loads(raw)
            if payload.get('remark'):
                raise RuntimeError(payload['remark'])
            destination.write_bytes(raw)
            (DATA/'fetch_metadata.json').write_text(json.dumps({'endpoint':endpoint,'bbox':BBOX,
                'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                'osm_metadata':payload.get('osm3s',{}),'elements':len(payload['elements']),
                'license':'Open Database License (ODbL) 1.0','attribution':'© OpenStreetMap contributors'},indent=2))
            print('Saved',len(payload['elements']),'elements;',len(raw),'bytes',flush=True)
            return destination
        except Exception as error:
            print(type(error).__name__,str(error),flush=True)
    raise RuntimeError('All public OSM endpoints failed')



def fetch_parts():
    """Optional small city-centre extract for mapped towers and dome parts."""
    query='[out:json][timeout:60];(way["building:part"](55.665,12.565,55.695,12.61);nwr[man_made=tower](55.665,12.565,55.695,12.61););out body geom;'
    destination=DATA/'landmark_parts_raw.json'
    if destination.exists():
        print('Cached landmark parts',flush=True)
        return
    request=urllib.request.Request(ENDPOINTS[1],data=urllib.parse.urlencode({'data':query}).encode(),headers={'User-Agent':'Copenhagen-Blender-GIS-Hackathon/1.0'})
    with urllib.request.urlopen(request,timeout=80) as response:
        raw=response.read()
    destination.write_bytes(raw)
    payload=json.loads(raw)
    print('Saved landmark parts:',len(payload.get('elements',[])),flush=True)


def fetch_context():
    """Broad real coastline, without city objects, to complete the horizon."""
    query='[out:json][timeout:90];way[natural=coastline](55.48,12.23,55.94,12.92);out body geom;'
    destination=DATA/'context_coastline_raw.json'
    if destination.exists():
        print('Cached context coastline',flush=True)
        return
    request=urllib.request.Request(ENDPOINTS[1],data=urllib.parse.urlencode({'data':query}).encode(),headers={'User-Agent':'Copenhagen-Blender-GIS-Hackathon/1.0'})
    with urllib.request.urlopen(request,timeout=110) as response:
        raw=response.read()
    payload=json.loads(raw)
    if payload.get('remark'):
        raise RuntimeError(payload['remark'])
    destination.write_bytes(raw)
    print('Saved context coastline:',len(payload.get('elements',[])),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--parts',action='store_true')
    parser.add_argument('--context',action='store_true')
    options=parser.parse_args()
    if options.parts:
        fetch_parts()
    elif options.context:
        fetch_context()
    else:
        fetch()
