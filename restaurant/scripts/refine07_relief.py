"""Image-guided, dimensional bronze bas-relief for the entrance.

No work happens at import time. The source is a scalar height interpretation of
the photograph, not an albedo or a depth measurement. Each image half becomes a
dense front surface with closed side walls and a triangulated solid back.
"""
from pathlib import Path
import math


PREFIX = 'REF07_Door_'


def build_relief(height_path, materials, scene, *, height_strength=.085,
                 height_cap=1800, width_cap=1200, plateau_compression=0.0):
    """Build two watertight hinged bronze leaves and return JSON-ready metadata.

    Required material: ``bronze``. Optional ``recess`` is used for rear faces;
    optional ``edge`` is used for side walls. Source image is mapped edge-to-edge:
    left leaf U=0..0.5, right leaf U=0.5..1, both V=0..1. Blender image pixels
    start at the bottom, matching these UV coordinates without vertical flipping.

    ``height_strength`` is meters from lowest to highest source value. Optional
    ``plateau_compression`` in [0,1] mixes the scalar heights toward a normalized
    exponential response; zero leaves their relationships unchanged. No spatial
    smoothing, synthetic grain or arbitrary noise is added to the reference.
    """
    import bpy
    import numpy as np
    if 'bronze' not in materials:
        raise KeyError('build_relief requires materials["bronze"]')
    height_path=Path(height_path).expanduser().resolve()
    if not height_path.is_file():
        raise FileNotFoundError(height_path)
    if not 0 < float(height_strength) <= .5:
        raise ValueError('height_strength must be >0 and <=0.5 meters')
    if not 0 <= float(plateau_compression) <= 1:
        raise ValueError('plateau_compression must be between 0 and 1')
    if int(height_cap)<8 or int(width_cap)<16:
        raise ValueError('Sampling caps must allow at least 8 rows and 8 columns per leaf')
    if scene is None:
        raise ValueError('Pass the target Blender scene explicitly')

    # Read original file pixels only: this does not edit/rewrite an image file.
    source=bpy.data.images.load(str(height_path),check_existing=False)
    source.name=PREFIX+'SourceHeight'
    source.colorspace_settings.name='Non-Color'
    sw,sh=map(int,source.size)
    if sw<16 or sh<8:
        bpy.data.images.remove(source)
        raise ValueError('Height image is too small for a two-leaf relief')
    raw=np.empty(sw*sh*4,dtype=np.float32)
    source.pixels.foreach_get(raw)
    raw=raw.reshape(sh,sw,4)
    luminance=np.clip(raw[:,:,0]*.2126+raw[:,:,1]*.7152+raw[:,:,2]*.0722,0,1)
    del raw
    source.pack()
    source['interpretation']='Scalar depth guide; inferred from reference, not measured photogrammetry'

    # Source-dependent caps avoid claiming extra source resolution. The seam
    # samples exactly U=.5 on both leaves, rather than omitting a strip of image.
    rows=min(int(height_cap),sh)
    columns=min(int(width_cap)//2,max(8,sw//2))
    vz=np.linspace(0,1,rows,dtype=np.float32)
    zs=.045+vz*4.150
    ypix=vz*(sh-1)
    yi=np.floor(ypix).astype(np.int32)
    yj=np.minimum(yi+1,sh-1)
    fy=ypix-yi

    collection=bpy.data.collections.get('Architecture')
    if collection is None:
        collection=bpy.data.collections.new('Architecture')
        scene.collection.children.link(collection)
    parent=bpy.data.objects.get('Architecture')
    if parent is None:
        parent=bpy.data.objects.new('Architecture',None)
        collection.objects.link(parent)
    if parent.type!='EMPTY':
        raise RuntimeError('Architecture parent must be an EMPTY')

    # Replace only this module's previous output. Retain every prior experiment
    # as hidden geometry so the original scene and reference trials remain intact.
    for obj in list(bpy.data.objects):
        if obj.name.startswith(PREFIX):
            mesh=obj.data if obj.type=='MESH' else None
            bpy.data.objects.remove(obj,do_unlink=True)
            if mesh is not None and mesh.users==0:
                bpy.data.meshes.remove(mesh)
    hidden=[]
    legacy=('REF06_Door_','Entrance_Bronze_Leaf','Entrance_Leaf_Crossrail',
            'Entrance_Leaf_Stile','Entry_Bronze_Root_Relief')
    for obj in scene.objects:
        if obj.name.startswith(legacy):
            obj.hide_render=True;obj.hide_viewport=True
            hidden.append(obj.name)

    created=[];leaf_reports=[]
    leaf_width=1.300
    palette=[materials['bronze'],materials.get('edge',materials['bronze']),
             materials.get('recess',materials['bronze'])]

    for side,hinge_x,u0,u1 in (('Left',-1.312,0.0,.5),('Right',1.312,.5,1.0)):
        us=np.linspace(u0,u1,columns,dtype=np.float32)
        xpix=us*(sw-1)
        xi=np.floor(xpix).astype(np.int32);xj=np.minimum(xi+1,sw-1)
        fx=xpix-xi
        # Bilinear resampling in source space, never nearest-neighbor stairs.
        lo=luminance[yi[:,None],xi[None,:]]*(1-fx[None,:])+luminance[yi[:,None],xj[None,:]]*fx[None,:]
        hi=luminance[yj[:,None],xi[None,:]]*(1-fx[None,:])+luminance[yj[:,None],xj[None,:]]*fx[None,:]
        height=(lo*(1-fy[:,None])+hi*fy[:,None]).astype(np.float32)
        del lo,hi
        if plateau_compression:
            curved=(1-np.exp(-height*2))/(1-math.exp(-2))
            height=height*(1-plateau_compression)+curved*plateau_compression
        local_x=np.linspace(0,leaf_width,columns,dtype=np.float32)
        if side=='Right':local_x-=leaf_width
        grid=np.arange(rows*columns,dtype=np.int32).reshape(rows,columns)
        # Ordered front boundary points: viewed from outside they run CCW in XZ.
        # Every boundary edge is explicitly shared with a side quad; there are no
        # disconnected strips, cracks at corners or unsupported one-sided cards.
        perimeter=np.concatenate((grid[0,:],grid[1:,-1],grid[-1,-2::-1],grid[-2:0:-1,0]))
        front_count=rows*columns;perimeter_count=len(perimeter)
        vertex_count=front_count+perimeter_count+1
        verts=np.empty((vertex_count,3),dtype=np.float32)
        verts[:front_count,0]=np.tile(local_x,rows)
        verts[:front_count,1]=(-.040-height*height_strength).ravel()
        verts[:front_count,2]=np.repeat(zs,columns)
        rear_ids=front_count+np.arange(perimeter_count,dtype=np.int32)
        verts[rear_ids]=verts[perimeter]
        verts[rear_ids,1]=.100
        center_id=vertex_count-1
        verts[center_id]=(leaf_width*.5 if side=='Left' else -leaf_width*.5,.100,2.120)

        a=grid[:-1,:-1].ravel()
        front_quads=np.column_stack((a,a+1,a+columns+1,a+columns))
        next_boundary=np.roll(perimeter,-1);next_rear=np.roll(rear_ids,-1)
        # Correct outward normals: front -Y, back +Y, sides outward.
        side_quads=np.column_stack((perimeter,rear_ids,next_rear,next_boundary))
        back_triangles=np.column_stack((np.full(perimeter_count,center_id,dtype=np.int32),
                                        next_rear,rear_ids))
        front_faces=len(front_quads)
        polygon_count=front_faces+2*perimeter_count
        loop_indices=np.concatenate((front_quads.ravel(),side_quads.ravel(),back_triangles.ravel()))
        loop_totals=np.concatenate((np.full(front_faces+perimeter_count,4,dtype=np.int32),
                                    np.full(perimeter_count,3,dtype=np.int32)))
        loop_starts=np.empty(polygon_count,dtype=np.int32)
        loop_starts[0]=0;np.cumsum(loop_totals[:-1],out=loop_starts[1:])

        mesh=bpy.data.meshes.new(PREFIX+side+'_SolidPhotoRelief')
        mesh.vertices.add(vertex_count);mesh.vertices.foreach_set('co',verts.ravel())
        mesh.loops.add(len(loop_indices));mesh.loops.foreach_set('vertex_index',loop_indices)
        mesh.polygons.add(polygon_count)
        mesh.polygons.foreach_set('loop_start',loop_starts)
        mesh.polygons.foreach_set('loop_total',loop_totals)
        smooth=np.zeros(polygon_count,dtype=np.bool_);smooth[:front_faces]=True
        mesh.polygons.foreach_set('use_smooth',smooth)
        slots=np.zeros(polygon_count,dtype=np.int32)
        slots[front_faces:front_faces+perimeter_count]=1
        slots[front_faces+perimeter_count:]=2
        mesh.polygons.foreach_set('material_index',slots)
        for material in palette:mesh.materials.append(material)
        mesh.update(calc_edges=True)

        # Exact photograph coordinates are retained on the real relief for later
        # use with a matching albedo. Sides/rear inherit the front boundary UVs.
        uv_vertex=np.empty((vertex_count,2),dtype=np.float32)
        uv_vertex[:front_count,0]=np.tile(us,rows)
        uv_vertex[:front_count,1]=np.repeat(vz,columns)
        uv_vertex[rear_ids]=uv_vertex[perimeter]
        uv_vertex[center_id]=((u0+u1)*.5,.5)
        uv=mesh.uv_layers.new(name='ReferenceUV')
        uv.data.foreach_set('uv',uv_vertex[loop_indices].ravel())

        # Conservative geometric masks derived from scalar height and local
        # concavity. Nothing uses sine waves, artificial trunk coordinates or
        # synthetic noise. These masks are shading aids, not baked illumination.
        padded=np.pad(height,1,mode='edge')
        neighbor=(padded[:-2,1:-1]+padded[2:,1:-1]+padded[1:-1,:-2]+padded[1:-1,2:])*.25
        cavity=np.clip((neighbor-height)*35,0,1)
        convex=np.clip((height-neighbor)*35,0,1)
        p05,p95=np.percentile(height,(5,95))
        elevation=np.clip((height-p05)/max(.001,float(p95-p05)),0,1)
        wear=np.clip(elevation*.20+convex*.65,0,1)
        cavity=np.clip((1-elevation)*.28+cavity*.65,0,1)
        for name,values in (('bronze_wear',wear),('bronze_cavity',cavity)):
            data=np.zeros(vertex_count,dtype=np.float32)
            data[:front_count]=values.ravel();data[rear_ids]=.05
            attr=mesh.attributes.new(name,'FLOAT','POINT');attr.data.foreach_set('value',data)

        hinge=bpy.data.objects.new(PREFIX+side+'_Hinge',None)
        collection.objects.link(hinge);hinge.parent=parent
        hinge.location=(hinge_x,-19.02,0);hinge.empty_display_size=.10
        obj=bpy.data.objects.new(PREFIX+side+'_SolidPhotoRelief',mesh)
        collection.objects.link(obj);obj.parent=hinge
        obj['source_height_image']=str(height_path)
        obj['depth_status']='Inferred bas-relief from a single image; not recovered true depth or a scan'
        obj['source_uv_half']=[u0,u1]
        obj['front_grid_dimensions']=[columns,rows]
        obj['height_strength_m']=float(height_strength)
        obj['watertight_construction']='Shared front perimeter, side quads, rear perimeter and back triangle fan'
        for frame,angle in ((1,0),(40,0),(85,90 if side=='Left' else -90)):
            hinge.rotation_euler.z=math.radians(angle)
            hinge.keyframe_insert(data_path='rotation_euler',index=2,frame=frame,group='Entrance opening')
        hinge['closed_frame']=1;hinge['hold_closed_until_frame']=40;hinge['fully_open_frame']=85
        created.extend((hinge,obj))
        leaf_reports.append({'side':side,'mesh':obj.name,'hinge':hinge.name,
            'vertices':vertex_count,'front_quads':front_faces,'side_quads':perimeter_count,
            'back_triangles':perimeter_count,'triangles':front_faces*2+perimeter_count*3,
            'uv_u_interval':[u0,u1],'source_height_min':float(height.min()),
            'source_height_max':float(height.max()),
            'local_depth_bounds_m':[float(verts[:,1].min()),.100]})

    scene.frame_set(1)
    bpy.context.view_layer.update()
    return {'objects':[o.name for o in created],'leaves':leaf_reports,
        'vertices':sum(r['vertices'] for r in leaf_reports),
        'triangles':sum(r['triangles'] for r in leaf_reports),
        'hidden_legacy_objects':hidden,'source_image':str(height_path),
        'packed_height_image':source.name,'source_dimensions_px':[sw,sh],
        'grid_per_leaf':[columns,rows],'combined_leaf_width_m':2.6,
        'outside_hinges_width_m':2.624,'center_seam_m':.024,
        'height_m':4.15,'height_strength_m':float(height_strength),
        'plateau_compression':float(plateau_compression),
        'attributes':['bronze_wear','bronze_cavity'],'uv_map':'ReferenceUV',
        'animation':{'closed':[1,40],'open':85,'left_degrees':90,'right_degrees':-90},
        'physical_limit':'Single-valued image height creates real parallax and shadows but cannot recover undercuts, hidden rear anatomy or measured depth from one photograph.'}
