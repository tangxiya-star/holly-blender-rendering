"""Show the actual final Cycles PNG in Blender beside its editable scene data."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
image_path=ROOT/'renders'/'food_final.png'
if image_path.exists():
    render=bpy.data.images.load(str(image_path),check_existing=True)
    reference=bpy.data.images.load(str(ROOT/'references'/'reference_dish.jpg'),check_existing=True)
    for window in bpy.context.window_manager.windows:
        areas=[a for a in window.screen.areas if a.type in {'VIEW_3D','IMAGE_EDITOR'}]
        if areas:
            area=max(areas,key=lambda a:a.width*a.height);area.type='IMAGE_EDITOR'
            area.spaces.active.image=render
            region=next((r for r in area.regions if r.type=='WINDOW'),None)
            try:
                with bpy.context.temp_override(window=window,area=area,region=region):
                    bpy.ops.image.view_all(fit_view=True)
            except Exception:pass
    (ROOT/'reports'/'gui_opened.json').write_text(json.dumps({'blend':bpy.data.filepath,'shown_image':str(image_path),'reference_loaded':reference.name,'view':'Image Editor — actual Cycles render'},indent=2))
