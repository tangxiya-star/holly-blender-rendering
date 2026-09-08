"""Preserve and verify the visible session, then show the requested eye model."""
import bpy, json, datetime
from pathlib import Path

assert not bpy.app.background, 'This script is only for the visible Blender window'
root=Path(__file__).resolve().parents[1]
target=root/'eye_07.blend'
assert target.is_file()
old_file=bpy.data.filepath
old_mode=bpy.context.mode
if bpy.context.object and bpy.context.object.mode!='OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
old_scenes={s.name:[o.name for o in s.objects] for s in bpy.data.scenes}
backup_dir=root/'backups';backup_dir.mkdir(exist_ok=True)
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
backup=backup_dir/('before_eye07_'+stamp+'.blend')
assert bpy.ops.wm.save_as_mainfile(filepath=str(backup),copy=True)=={'FINISHED'}
assert backup.is_file() and backup.stat().st_size>1000
# Read the written backup through Blender's library reader without loading or
# replacing the current scene. Abort the switch if any used object is missing.
with bpy.data.libraries.load(str(backup),link=False) as (available,unused):
    assert all(name in available.scenes for name in old_scenes), 'Backup lacks a scene'
    assert all(name in available.objects for names in old_scenes.values() for name in names), 'Backup lacks a scene object'
    verified_objects=len(available.objects)
proof={'previous_filepath':old_file,'verified_backup':str(backup),
       'previous_mode':old_mode,
       'backup_bytes':backup.stat().st_size,'verified_objects':verified_objects,
       'preserved_scenes':{name:len(objects) for name,objects in old_scenes.items()},
       'opened':str(target),'background':bpy.app.background}
(root/'reports'/'visible_eye07_handoff.json').write_text(json.dumps(proof,indent=2))
bpy.ops.wm.open_mainfile(filepath=str(target))
scene=bpy.context.scene
scene.cycles.preview_samples=32;scene.cycles.use_preview_denoising=True
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        space=area.spaces.active
        space.shading.type='RENDERED';space.overlay.show_overlays=False
        space.lens=50;space.clip_start=.001;space.clip_end=100
        region=space.region_3d
        region.view_rotation=scene.camera.rotation_euler.to_quaternion()
        region.view_location=(0,0,.085)
        region.view_distance=.46
        region.view_perspective='PERSP'
print('VISIBLE_EYE07_OPENED',bpy.data.filepath,'PREVIOUS_SESSION_BACKUP',str(backup))
