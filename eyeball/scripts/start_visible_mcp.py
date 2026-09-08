"""Start the installed interactive bridge in this task's visible Blender window.

Launch with --online-mode. No preferences are changed or saved.
"""
import bpy, os
from bl_ext.user_default.mcp import mcp_to_blender_server as bridge, execute_interactive

assert not bpy.app.background
assert bpy.app.online_access, 'Blender must be launched with --online-mode'
if not bridge.is_running():bridge.start('127.0.0.1',9876)
if not bpy.app.timers.is_registered(execute_interactive.run):
    bpy.app.timers.register(execute_interactive.run,first_interval=bridge.TIMER_INTERVAL_ACTIVE,persistent=True)
print('MCP_READY',os.getpid(),bpy.data.filepath,'127.0.0.1:9876',flush=True)
