import bpy, math, json
from common import *

def build_navigation():
    s=bpy.context.scene
    stops=[((-6.6,-25,1.88),(-3,5,3)),((-6.6,-8,1.88),(-4,16,3)),((-6.6,17,1.88),(-9,21.52,2)),((-6.6,24,1.88),(-1,49,3)),((-6.6,41,1.88),(0,58,3)),((-6.6,48.2,1.88),(-22,51,2.7)),((-24,48.2,1.88),(-32,57.5,2.6)),((-41,48.2,1.88),(-60,51.3,2.8))]
    cam=camera('06 | Walkthrough',stops[0][0],stops[0][1],32);cam.rotation_mode='QUATERNION'
    fps=24;frame=1;points=[];records=[]
    for i in range(len(stops)-1):
        p0,t0=map(Vector,stops[i]);p1,t1=map(Vector,stops[i+1]);q0=(t0-p0).to_track_quat('-Z','Y');q1=(t1-p1).to_track_quat('-Z','Y')
        duration=round((p1-p0).length/1.35*fps)
        records.append({'frame':frame,'position':tuple(p0),'lookAt':tuple(t0)})
        for j in range(0,duration+1,4):
            u=j/duration;e=u*u*(3-2*u);cam.location=p0.lerp(p1,u);cam.rotation_quaternion=q0.slerp(q1,e)
            cam.keyframe_insert('location',frame=frame+j);cam.keyframe_insert('rotation_quaternion',frame=frame+j)
            points.append(tuple(cam.location))
        frame+=duration
    s.frame_end=frame;s.frame_set(1)
    c=curve('Walking route | 1.35m per second',points,.012,'Navigation',None);c.hide_render=True;c.display_type='WIRE'
    for i,r in enumerate(records):s.timeline_markers.new(['Start','Shop street','Bakery approach','Continue','Intersection','Turn left','Gallery'][i],frame=r['frame'])
    records.append({'frame':frame,'position':stops[-1][0],'lookAt':stops[-1][1]})
    for o in bpy.data.collections['POI_Targets'].objects:o.hide_render=True
    drive=camera('07 | Driving perspective',(1.35,-57,1.25),(1.35,-12,1.8),35)
    for f,y in [(1,-57),(697,117)]:
        drive.location=(1.35,y,1.25);aim(drive,(1.35,y+45,1.8))
        drive.keyframe_insert('location',frame=f);drive.keyframe_insert('rotation_euler',frame=f)
    drive['route']='Right traffic lane, 174m in29s; cinematic preview, no vehicle physics controller.'
    (ROOT/'reports'/'navigation.json').write_text(json.dumps({'fps':fps,'frame_end':frame,'approx_duration_seconds':frame/fps,'walking_speed_m_s':1.35,'eye_height_m':1.7,'route':records,'drive_preview':{'camera':drive.name,'frame_start':1,'frame_end':697,'distance_m':174},'navigation_instructions':'For interactive walking use F3 > Walk Navigation in Blender 3D View; WASD, mouse look, Q/E vertical, wheel speed. For animated preview choose camera 06 | Walkthrough and play timeline.'},indent=2))
