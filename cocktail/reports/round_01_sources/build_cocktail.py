"""Procedural full-detail cocktail build, executed inside the connected Blender via MCP."""
import bpy, math, random
from mathutils import Vector
import optics


def get_subject_collection(scene):
    for c in scene.collection.children:
        if c.name=='01 | Cocktail vessel and liquid':return c
    return optics.collection(scene,'01 | Cocktail vessel and liquid')


def set_hero_camera(scene,height,distance=.68,elevation_degrees=13):
    target=Vector((0,0,height*.50))
    angle=math.radians(elevation_degrees)
    cam=scene.camera
    cam.location=target+Vector((0,-distance*math.cos(angle),distance*math.sin(angle)))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    focus=cam.data.dof.focus_object
    focus.location=(0,-.005,height*.73)
    cam.data.dof.aperture_fstop=9
    cam.data.lens=95
    cam.data.shift_y=.035


def finish_subject(scene,glass,liquid):
    glass['wall_thickness_mm']='0.8–1.2, vessel dependent; separately modeled interior and exterior'
    glass['manufacturing']='Continuous closed lathed solid with rolled lip, very small circumferential variation'
    liquid['optics']='IOR 1.333; volumetric absorption; meniscus; separate closed geometry'
    liquid['intent']='Liquid boundary follows interior profile with microscopic clearance'
    scene['purpose']='Photorealistic cocktail test; native Cycles materials; no web conversion or baking'
    scene['reference_url']='https://share.google/ggyyabeBT3pQDENw3'
    scene['units_note']='All geometry in metres; camera full frame portrait 95 mm'
    bpy.context.view_layer.update()
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.overlay.show_overlays=False
            area.spaces.active.shading.type='MATERIAL'
    return {'glass':glass.name,'liquid':liquid.name,'glass_dimensions_m':list(glass.dimensions)}


def build_antini(scene):
    c=get_subject_collection(scene)
    glassmat=bpy.data.materials.get('Cocktail | hand-blown lead-free glass IOR 1.45') or optics.dielectric('Cocktail | hand-blown lead-free glass IOR 1.45',1.45,.018,micro=True)
    # One continuous solid: recessed underside, rounded foot, slender drawn stem,
    # rounded V-shaped coupe, fire-polished lip, and complete interior bowl.
    mm=.001
    curves=[
      [(0.001,.0011),(.014,.0011),(.025,.0001),(.030,.0001)],
      [(.030,.0001),(.032,.0001),(.033,.0004),(.033,.0014)],
      [(.033,.0014),(.033,.0025),(.032,.0031),(.030,.0033)],
      [(.030,.0033),(.020,.0038),(.006,.0030),(.0035,.008)],
      [(.0035,.008),(.0025,.012),(.00205,.020),(.00205,.034)],
      [(.00205,.034),(.00203,.058),(.002,.083),(.0023,.101)],
      [(.0023,.101),(.0024,.107),(.003,.110),(.0055,.112)],
      [(.0055,.112),(.014,.116),(.027,.121),(.0355,.132)],
      [(.0355,.132),(.043,.141),(.0455,.150),(.0455,.158)],
      [(.0455,.158),(.0455,.161),(.0455,.164),(.0455,.1656)],
    ]
    profile=optics.bezier_profile(curves,20)
    # Semicircular fire-polished lip, radius 0.425 mm. Thickness 0.85 mm.
    for i in range(1,17):
        a=math.pi*i/16
        profile.append((.045075+.000425*math.cos(a),.1656+.000425*math.sin(a)))
    inner_start=len(profile)-1
    # Explicit point at contact height permits the wet/dry optical interface split.
    dry=[[(.04465,.1656),(.04465,.162),(.04465,.159),(.04461,.156)],
         [(.04461,.156),(.04460,.1552),(.04456,.1544),(.04448,.15355)]]
    profile+=optics.bezier_profile(dry,12)[1:]
    wet_start=len(profile)-1
    wet_curves=[
      [(.04448,.15355),(.0441,.146),(.0405,.1393),(.03475,.1328)],
      [(.03475,.1328),(.0262,.122),(.0135,.1176),(.0052,.114)],
      [(.0052,.114),(.003,.1135),(.0015,.11345),(.000001,.11345)],
    ]
    wet_profile=optics.bezier_profile(wet_curves,28)
    profile+=wet_profile[1:]
    glass=optics.lathe('Glass | Antini hand-drawn coupe',profile,c,glassmat,segments=256,wobble=.000006)
    wet=optics.dielectric('Cocktail | glass-to-drink interface IOR 1.0878',1.45/1.333,.013)
    glass.data.materials.append(wet)
    for face in glass.data.polygons:
        ring=face.index//256
        if wet_start<=ring<len(profile)-1:face.material_index=1
    # Reverse interior profile, shrink by 20 μm: liquid remains strictly inside glass.
    liquid_profile=[(max(.000001,r-.000020),z+.000008) for r,z in reversed(wet_profile)]
    # A 0.45 mm capillary rise eases from contact into a genuinely flat free surface.
    radius=liquid_profile[-1][0];contact_z=liquid_profile[-1][1]
    liquid_profile += [
      (radius-.00014,contact_z-.00018),(radius-.0004,contact_z-.00032),
      (radius-.0008,contact_z-.00040),(radius-.0014,contact_z-.00044),
      (radius-.0024,contact_z-.00045),
      (.036,contact_z-.00045),(.026,contact_z-.00045),(.012,contact_z-.00045),(.000001,contact_z-.00045)]
    liquidmat=optics.dielectric('Cocktail | pale currant-stem Antini',1.333,.011,absorption=(.72,.82,.30),density=3.2)
    liquid=optics.lathe('Liquid | Antini with curved meniscus',liquid_profile,c,liquidmat,segments=256)
    # Side/bottom are a null surface bounding the absorbing medium: the relative
    # IOR is already handled once on the wetted glass face, with no fake air layer.
    medium=liquidmat.copy();medium.name='Cocktail | absorption medium boundary'
    ns=medium.node_tree.nodes;ls=medium.node_tree.links
    t=ns.new('ShaderNodeBsdfTransparent');t.inputs['Color'].default_value=(1,1,1,1)
    ls.new(t.outputs[0],ns.get('Material Output').inputs['Surface'])
    liquid.data.materials.append(medium)
    side_end=len(wet_profile)-1
    for face in liquid.data.polygons:
        if face.index<side_end*256 or face.index==(len(liquid_profile)-1)*256:
            face.material_index=1
    glass['rim_thickness_mm']=.85
    glass['optical_interfaces']='Exterior/dry IOR1.45; wet inner IOR1.45/1.333; closed liquid null side boundary'
    glass['profile_outer_points']=inner_start
    glass['profile_wet_start']=wet_start
    glass['lathe_segments']=256
    liquid['volume_tint']='Subtle straw green, absorption only; no painted surface color'
    liquid['fill_height_m']=contact_z-.00045
    liquid['glass_clearance_m']=.000020
    # Uncoated glass; a few almost invisible chilled moisture beads, no frosting.
    drops=optics.collection(scene,'02 | Restrained moisture')
    water=bpy.data.materials.get('Cocktail | water moisture IOR 1.333')
    rng=random.Random(813)
    for i in range(19):
        z=rng.uniform(.146,.161)
        r=.0449 if z>.150 else .0439
        a=rng.uniform(-math.pi*.96,-math.pi*.04)
        rad=rng.uniform(.000055,.00014)
        o=optics.uv_drop('Moisture | %02d'%i,drops,((r+rad*.4)*math.cos(a),(r+rad*.4)*math.sin(a),z),rad,water,stretch=(1,.5,1.1))
    set_hero_camera(scene,.166,distance=.58,elevation_degrees=13)
    return finish_subject(scene,glass,liquid)
