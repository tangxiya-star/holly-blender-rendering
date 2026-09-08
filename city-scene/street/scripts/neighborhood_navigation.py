"""A closed route through all four streets, with inspectable per-street cameras."""
import bpy, math, json
from common import *

def build_neighborhood_navigation():
    s=bpy.context.scene
    overview=camera('08 | FOUR STREETS - overview',(32,6,140),(32,6,0),35)
    overview.data.type='ORTHO';overview.data.ortho_scale=184
    overview.rotation_euler=(0,0,0)
    overview['purpose']='Four connected streets and complete perimeter loop, north up.'
    camera('09 | North street - eastbound',(20,50.25,1.7),(61,51.8,2.5),32)
    camera('10 | East street - southbound',(65.45,36,1.7),(64,-3,2.7),32)
    camera('11 | South street - westbound',(48,-38.3,1.7),(3,-40,2.7),32)
    turn=camera('12 | TURN HERE - north intersection',(.2,49,1.7),(21,52,2.5),32)
    # Follow the inside footways of the four-street perimeter, including
    # rounded corners outside the occupied building envelope.
    points=[(6.7,-36.1),(6.7,42),(6.8,46),(7.4,47.5),(9,48.1),
            (54,48.1),(57.2,48.1),(59,46.5),(59,43),
            (59,-30),(59,-33),(58,-35),(55,-36.1),
            (11,-36.1),(8,-36.1),(6.7,-36.1)]
    cam=camera('13 | FULL LOOP - all four streets',(*points[0],1.88),(*points[1],2.1),32)
    cam.rotation_mode='QUATERNION'
    sampled=[]
    for a,b in zip(points,points[1:]):
        av=Vector((*a,1.88));bv=Vector((*b,1.88));steps=max(1,math.ceil((bv-av).length/.4))
        for j in range(steps):sampled.append(av.lerp(bv,j/steps))
    sampled.append(Vector((*points[-1],1.88)))
    fps=24;speed=1.4;distance=0;frame=1
    for i,p in enumerate(sampled):
        if i:distance+=(p-sampled[i-1]).length
        frame=1+round(distance/speed*fps)
        ahead=sampled[min(i+10,len(sampled)-1)]
        if (ahead-p).length<.001:ahead=p+Vector((0,3,0))
        cam.location=p;cam.rotation_quaternion=(ahead+Vector((0,0,.2))-p).to_track_quat('-Z','Y')
        cam.keyframe_insert('location',frame=frame);cam.keyframe_insert('rotation_quaternion',frame=frame)
    s.frame_end=frame;s.frame_set(1)
    route=curve('LOOP | Four connected streets',[tuple(p) for p in sampled],.08,'Neighborhood_Navigation',mat('Loop display',(.06,.42,.52),.6))
    route.hide_render=True;route.display_type='WIRE';route['length_m']=distance
    s['streets']=4;s['closed_loop_length_m']=distance
    # No timeline camera binding: users can independently select a viewpoint.
    for name,f in [('MAIN STREET',1),('TURN EAST',round(85/speed*fps)),('TURN SOUTH',round(149/speed*fps)),('TURN WEST',round(235/speed*fps))]:
        s.timeline_markers.new(name,frame=f)
    report={'street_count':4,'intersection_centres':[[0,-40],[0,52],[64,52],[64,-40]],
            'streets':[{'name':'Main street','axis':'Y','centre_x':0},
                       {'name':'North cross street','axis':'X','centre_y':52},
                       {'name':'East neighborhood street','axis':'Y','centre_x':64},
                       {'name':'South cross street','axis':'X','centre_y':-40}],
            'closed_loop':True,'route_points':points,'eye_z':1.88,'surface_z':.18,'length_m':distance,'fps':fps,'frames':frame,
            'camera':cam.name,'overview_camera':overview.name,'per_street_cameras':['01 | Human eye street','09 | North street - eastbound','10 | East street - southbound','11 | South street - westbound']}
    (ROOT/'reports'/'neighborhood_navigation.json').write_text(json.dumps(report,indent=2))
    return report
