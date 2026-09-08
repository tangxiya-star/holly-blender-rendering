"""Download GeoDanmark open orthophotos for this local evaluation scene.

Data: GeoDanmark / Klimadatastyrelsen, CC BY 4.0.
Delivery: Septima MapProxy, private/evaluation service; no production hotlinking.
WMS 1.1.1 EPSG:4326 gives exact west/south/east/north geographic bounds,
matching the scene's affine lon/lat-to-local-metres transform without UV warp.
"""
import concurrent.futures
import io
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
SERVICE='https://osmtools.septima.dk/mapproxy/service'
LAYER='DAF_ortoforaar'
BBOX=(12.48,55.625,12.67,55.735)
ORIGIN=(12.5683,55.6761)


def fetch_imagery(size=8192):
    tiles_per_axis=size//2048
    west,south,east,north=BBOX
    jobs=[(col,row) for row in range(tiles_per_axis) for col in range(tiles_per_axis)]
    requests=[]
    def tile(job):
        col,row=job
        x0=west+(east-west)*col/tiles_per_axis
        x1=west+(east-west)*(col+1)/tiles_per_axis
        y1=north-(north-south)*row/tiles_per_axis
        y0=north-(north-south)*(row+1)/tiles_per_axis
        params={'SERVICE':'WMS','VERSION':'1.1.1','REQUEST':'GetMap','LAYERS':LAYER,
                'STYLES':'','FORMAT':'image/jpeg','SRS':'EPSG:4326',
                'BBOX':','.join(str(v) for v in (x0,y0,x1,y1)),
                'WIDTH':2048,'HEIGHT':2048,'TRANSPARENT':'FALSE'}
        url=SERVICE+'?'+urllib.parse.urlencode(params)
        tile_name=('aerial_imagery_tile_%d_%d.jpg' if size==8192 else 'aerial_imagery_tile4096_%d_%d.jpg')
        destination=DATA/(tile_name%(col,row))
        if destination.exists():
            raw=destination.read_bytes()
        else:
            request=urllib.request.Request(url,headers={'User-Agent':'Copenhagen-Blender-Hackathon-Local-Evaluation/1.0'})
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(request,timeout=100) as response:
                        raw=response.read()
                    image=Image.open(io.BytesIO(raw));image.load()
                    if image.size!=(2048,2048):
                        raise RuntimeError('Unexpected WMS image dimensions: '+str(image.size))
                    destination.write_bytes(raw)
                    break
                except Exception:
                    if attempt==2:
                        raise
                    time.sleep(2+attempt)
        image=Image.open(io.BytesIO(raw)).convert('RGB')
        print('Tile',col,row,'ready',len(raw),'bytes',flush=True)
        return col,row,image,{'tile':[col,row],'bbox':[x0,y0,x1,y1],'url':url}
    atlas=Image.new('RGB',(size,size))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for col,row,image,request in pool.map(tile,jobs):
            atlas.paste(image,(col*2048,row*2048))
            requests.append(request)
    atlas.save(DATA/'aerial_imagery.jpg',quality=95,subsampling=0)
    if size==8192:
        atlas.resize((4096,4096),Image.Resampling.LANCZOS).save(DATA/'aerial_imagery_4096.jpg',quality=94,subsampling=0)
    sx=111320*math.cos(math.radians(ORIGIN[1]))
    local={'min_x':(west-ORIGIN[0])*sx,'min_y':(south-ORIGIN[1])*111320,
           'max_x':(east-ORIGIN[0])*sx,'max_y':(north-ORIGIN[1])*111320}
    metadata={'image':'aerial_imagery.jpg','width':size,'height':size,'north_up':True,
        'origin':{'lon':ORIGIN[0],'lat':ORIGIN[1]},'bbox_lonlat':list(BBOX),'bounds_local_m':local,
        'uv_mapping':{'u':'(world_x - min_x) / (max_x - min_x)','v':'(world_y - min_y) / (max_y - min_y)','image_top':'north','blender_image_uv_origin':'bottom left'},
        'provider':'GeoDanmark / Klimadatastyrelsen','delivery_provider':'Septima MapProxy',
        'layer':LAYER,'source_crs':'EPSG:4326','wms_version':'1.1.1',
        'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
        'attribution':'Orthophoto © GeoDanmark / Klimadatastyrelsen, CC BY 4.0; delivered via Septima OSMtools; cropped and resampled for a Blender visualization.',
        'service_access_constraints':'Septima WMS states private and evaluation use only. This acquisition is for the local evaluation scene, not a public production service or ongoing hotlink.',
        'capture_date':'The live WMS layer did not declare a per-tile capture date; not asserted.',
        'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'source_pages':['https://osmtools.septima.dk/','https://www.klimadatastyrelsen.dk/om-klimadatastyrelsen/vilkaar-og-priser'],
        'requests':requests}
    (DATA/'aerial_imagery.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    print('Saved exact north-up atlas:',size,'×',size,flush=True)

def fetch_nyhavn():
    # Service advertises MaxWidth/MaxHeight4000, so use the requested2048 option.
    size=2048
    local={'min_x':1100.0,'min_y':100.0,'max_x':1850.0,'max_y':850.0}
    sx=111320*math.cos(math.radians(ORIGIN[1]))
    bbox=(ORIGIN[0]+local['min_x']/sx,ORIGIN[1]+local['min_y']/111320,
          ORIGIN[0]+local['max_x']/sx,ORIGIN[1]+local['max_y']/111320)
    params={'SERVICE':'WMS','VERSION':'1.1.1','REQUEST':'GetMap','LAYERS':LAYER,
            'STYLES':'','FORMAT':'image/jpeg','SRS':'EPSG:4326',
            'BBOX':','.join(str(v) for v in bbox),'WIDTH':size,'HEIGHT':size,'TRANSPARENT':'FALSE'}
    url=SERVICE+'?'+urllib.parse.urlencode(params)
    destination=DATA/'nyhavn_imagery.jpg'
    if not destination.exists():
        request=urllib.request.Request(url,headers={'User-Agent':'Copenhagen-Blender-Hackathon-Local-Evaluation/1.0'})
        with urllib.request.urlopen(request,timeout=100) as response:
            raw=response.read()
        image=Image.open(io.BytesIO(raw));image.load()
        if image.size!=(size,size):
            raise RuntimeError('Unexpected Nyhavn export dimensions: '+str(image.size))
        destination.write_bytes(raw)
    metadata={'image':destination.name,'width':size,'height':size,'north_up':True,
        'bounds_local_m':local,'bbox_lonlat':bbox,'metres_per_texel':750/size,
        'origin':{'lon':ORIGIN[0],'lat':ORIGIN[1]},
        'uv_mapping':{'u':'(world_x - 1100) / 750','v':'(world_y - 100) / 750','image_top':'north'},
        'provider':'GeoDanmark / Klimadatastyrelsen','delivery_provider':'Septima MapProxy',
        'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
        'attribution':'Orthophoto © GeoDanmark / Klimadatastyrelsen, CC BY 4.0; delivered via Septima OSMtools; cropped for Blender visualization.',
        'service_access_constraints':'Private/evaluation service; single local prototype export; not public production hotlinking.',
        'capture_date':'Not declared by live WMS layer','source_crs':'EPSG:4326','wms_version':'1.1.1',
        'request_url':url,'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    (DATA/'nyhavn_imagery.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    print('Nyhavn local atlas ready:',destination,size,'px;',750/size,'m per texel',flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--size',type=int,choices=[4096,8192],default=8192)
    parser.add_argument('--nyhavn',action='store_true')
    options=parser.parse_args()
    if options.nyhavn:
        fetch_nyhavn()
    else:
        fetch_imagery(options.size)
