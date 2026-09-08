"""Millimetre-aware geometric and optical helpers for the Cycles cocktail study."""
import bpy, bmesh, math


def bezier_profile(segments, steps=16):
    """Sample joined cubic radial/height curves for a continuously curved vessel."""
    output=[]
    for points in segments:
        for k in range(steps):
            t=k/steps;u=1-t
            output.append(tuple(u*u*u*points[0][i]+3*u*u*t*points[1][i]+3*u*t*t*points[2][i]+t*t*t*points[3][i] for i in range(2)))
    output.append(tuple(segments[-1][-1]))
    return output


def mesh_object(name, vertices, faces, collection, material=None):
    mesh = bpy.data.meshes.new(name + ' mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh); collection.objects.link(obj)
    for poly in mesh.polygons: poly.use_smooth = True
    if material: mesh.materials.append(material)
    return obj


def lathe(name, profile, collection, material, segments=256, wobble=0):
    """Revolve a continuous exterior→rim→interior profile; end rings close at axis."""
    vertices=[]; faces=[]
    for r,z in profile:
        for k in range(segments):
            a=2*math.pi*k/segments
            # Below 25 microns of slow blown-glass variation, never coarse facets.
            dr=wobble*(math.sin(a*3+.4)+.35*math.sin(a*7+z*35))*min(r/.01,1)
            vertices.append(((r+dr)*math.cos(a),(r+dr)*math.sin(a),z))
    for j in range(len(profile)-1):
        for k in range(segments):
            n=(k+1)%segments
            faces.append((j*segments+k,j*segments+n,(j+1)*segments+n,(j+1)*segments+k))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple((len(profile)-1)*segments+k for k in range(segments)))
    return mesh_object(name,vertices,faces,collection,material)


def dielectric(name,ior=1.45,roughness=.022,tint=(1,1,1),absorption=None,density=0,micro=False):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*tint,1)
    p.inputs['Transmission Weight'].default_value=1
    p.inputs['IOR'].default_value=ior
    p.inputs['Roughness'].default_value=roughness
    if absorption:
        v=n.new('ShaderNodeVolumeAbsorption');v.name='Physical depth absorption'
        v.inputs['Color'].default_value=(*absorption,1);v.inputs['Density'].default_value=density
        l.new(v.outputs['Volume'],n.get('Material Output').inputs['Volume'])
    if micro:
        tex=n.new('ShaderNodeTexNoise');tex.name='Very subtle polishing variation'
        tex.inputs['Scale'].default_value=180;tex.inputs['Detail'].default_value=2
        ramp=n.new('ShaderNodeMapRange');ramp.name='Near optical polish'
        ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1
        ramp.inputs['To Min'].default_value=roughness*.6;ramp.inputs['To Max'].default_value=roughness*1.3
        l.new(tex.outputs['Fac'],ramp.inputs['Value']);l.new(ramp.outputs['Result'],p.inputs['Roughness'])
    return m


def collection(scene,name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c


def uv_drop(name,collection,center,radius,material,stretch=(1,1,1),segments=12,rings=8):
    vertices=[];faces=[]
    for j in range(rings+1):
        t=math.pi*j/rings
        for k in range(segments):
            a=2*math.pi*k/segments
            vertices.append((center[0]+radius*stretch[0]*math.sin(t)*math.cos(a),
                             center[1]+radius*stretch[1]*math.sin(t)*math.sin(a),
                             center[2]+radius*stretch[2]*math.cos(t)))
    for j in range(rings):
        for k in range(segments):
            n=(k+1)%segments;faces.append((j*segments+k,j*segments+n,(j+1)*segments+n,(j+1)*segments+k))
    return mesh_object(name,vertices,faces,collection,material)
