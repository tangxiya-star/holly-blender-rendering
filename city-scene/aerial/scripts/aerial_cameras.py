import bpy, math, json
from mathutils import Vector
from aerial_common import camera, group, aim, ROOT

# All positions in local east/north metres, Z is altitude above harbor datum.
FLIGHT=[
 (1,(4400,-3900,3300),(550,900,0),48),
 (145,(4100,-3500,2250),(700,650,10),44),
 (289,(2850,-1900,1500),(1030,430,15),46),
 (409,(2140,-620,790),(1320,380,20),47),
 (505,(1900,120,370),(1450,455,18),46),
 (577,(1630,480,260),(1425,465,20),43),
 (649,(1472,484,180),(1360,455,20),40),
 (673,(1418,470,160),(1290,432,22),38),
]

def interpolate(values,i,t):
    p0=Vector(values[max(0,i-1)]);p1=Vector(values[i]);p2=Vector(values[i+1]);p3=Vector(values[min(len(values)-1,i+2)])
    f0=FLIGHT[max(0,i-1)][0];f1=FLIGHT[i][0];f2=FLIGHT[i+1][0];f3=FLIGHT[min(len(values)-1,i+2)][0]
    m1=(p2-p0)*(f2-f1)/max(1,f2-f0);m2=(p3-p1)*(f2-f1)/max(1,f3-f1)
    return (2*t**3-3*t*t+1)*p1+(t**3-2*t*t+t)*m1+(-2*t**3+3*t*t)*p2+(t**3-t*t)*m2

def build_cameras():
    s=bpy.context.scene;s.render.fps=24;s.frame_start=1;s.frame_end=673
    hero=camera('01 | HERO - Copenhagen from the southeast',FLIGHT[0][1],FLIGHT[0][2],48)
    overview=camera('02 | Harbor and historic center',(3500,-2900,2450),(800,700,0),47)
    target=camera('03 | Nyhavn - handoff approach',FLIGHT[-2][1],FLIGHT[-2][2],40)
    top=camera('04 | Geographic inspection - north up',(300,700,12000),(300,700,0),40);top.data.type='ORTHO';top.data.ortho_scale=15000;top.rotation_euler=(0,0,0)
    fly=camera('05 | CINEMATIC DIVE - World Labs handoff',FLIGHT[0][1],FLIGHT[0][2],43);fly.rotation_mode='QUATERNION'
    samples=[];locs=[k[1] for k in FLIGHT];ats=[k[2] for k in FLIGHT];prev=None
    for f in range(1,674):
        i=next((i for i in range(len(FLIGHT)-1) if FLIGHT[i][0]<=f<=FLIGHT[i+1][0]),len(FLIGHT)-2)
        t=(f-FLIGHT[i][0])/(FLIGHT[i+1][0]-FLIGHT[i][0]);pos=interpolate(locs,i,t);at=interpolate(ats,i,t)
        q=(at-pos).to_track_quat('-Z','Y')
        if prev and q.dot(prev)<0:q.negate()
        prev=q.copy();fly.location=pos;fly.rotation_quaternion=q
        fly.data.lens=FLIGHT[i][3]*(1-t)+FLIGHT[i+1][3]*t
        fly.data.dof.use_dof=True;fly.data.dof.focus_distance=(at-pos).length
        if f>649:
            pull=(f-649)/24
            fly.data.dof.focus_distance=(at-pos).length*(1-pull)+6*pull
        fly.data.dof.aperture_fstop=11 if f<620 else 11-(f-620)/53*8.2
        fly.keyframe_insert('location',frame=f);fly.keyframe_insert('rotation_quaternion',frame=f)
        fly.data.keyframe_insert('lens',frame=f);fly.data.keyframe_insert('dof.focus_distance',frame=f);fly.data.keyframe_insert('dof.aperture_fstop',frame=f)
        samples.append({'frame':f,'position':list(pos),'look_at':list(at),'lens_mm':fly.data.lens})
    for f,name in [(1,'HIGH ABOVE COPENHAGEN'),(289,'HARBOR / URBAN BLOCKS'),(505,'NYHAVN DESCENT'),(649,'WORLD LABS MATCH FRAME'),(673,'END BLENDER / WORLD LABS START')]:
        mark=s.timeline_markers.new(name,frame=f)
    e=bpy.data.objects.new('WORLD LABS | handoff anchor | 55.68045 N 12.59178 E',None);group('05_Cameras_and_Flight').objects.link(e);e.location=FLIGHT[-2][1];e.empty_display_type='ARROWS';e.empty_display_size=12
    e['handoff_frame']=649;e['altitude_m']=180;e['target_environment']='World Labs Nyhavn street world; external asset not supplied'
    report={'duration_seconds':28,'fps':24,'hero_camera':hero.name,'animation_camera':fly.name,'coordinate_origin':{'lon':12.5683,'lat':55.6761},'transition':{'match_frame':649,'end_frame':673,'altitude_m':180,'position':FLIGHT[-2][1],'look_at':FLIGHT[-2][2],'lens_mm':40,'sensor_width_mm':36,'render_aspect':'16:9','technique':'DOF pull and accelerated approach; reserve final second for World Labs dissolve/occlusion; altitude raised after54m test exposed simplified facades','external_world_connected':False},'samples':samples}
    (ROOT/'reports'/'camera_handoff.json').write_text(json.dumps(report,indent=2))
    s.camera=hero;s.frame_set(1)
    return report
