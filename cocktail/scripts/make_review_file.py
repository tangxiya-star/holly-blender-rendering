import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
initial=bpy.context.scene
with bpy.data.libraries.load(str(ROOT/'cocktail_07.blend'),link=False) as (src,dst):
    dst.scenes=[n for n in src.scenes if n.startswith('Cocktail |')]
s=dst.scenes[0]
bpy.context.window.scene=s
bpy.data.scenes.remove(initial)
image=bpy.data.images.load(str(ROOT/'renders'/'cocktail_07.png'));image.name='Cocktail | Current Cycles render';image.pack()
for workspace in bpy.data.workspaces:
    for screen in workspace.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA'
                area.spaces.active.region_3d.view_camera_zoom=10
                area.spaces.active.overlay.show_overlays=False
                area.spaces.active.shading.type='RENDERED'
layout=bpy.data.workspaces.get('Layout')
if layout:
    layout.name='Hero Render';bpy.context.window.workspace=layout
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.type='IMAGE_EDITOR';area.spaces.active.image=image
            region=next((r for r in area.regions if r.type=='WINDOW'),None)
            if region:
                with bpy.context.temp_override(area=area,region=region):
                    bpy.ops.image.view_all(fit_view=True)
if bpy.data.workspaces.get('Modeling'):bpy.data.workspaces['Modeling'].name='3D Model'
s.cycles.preview_samples=32;s.cycles.use_preview_denoising=True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'cocktail_current_review.blend'))
print('REVIEW_READY',str(ROOT/'cocktail_current_review.blend'),flush=True)
