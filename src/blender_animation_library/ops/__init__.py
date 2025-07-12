"""
Animation Library Operators Package
Modular operator structure for the Blender Animation Library addon
"""

# Import all operator modules
from .server_ops import (
    ANIMLIB_OT_start_server,
    ANIMLIB_OT_stop_server,
    ANIMLIB_OT_test_connection,
    ANIMLIB_OT_get_scene_info,
)

from .library_ops import (
    ANIMLIB_OT_extract_current,
    ANIMLIB_OT_optimize_library,
    ANIMLIB_OT_validate_library,
)

from .preview_ops import (
    ANIMATIONLIBRARY_OT_update_preview,
)

from .utils import (
    capture_viewport_thumbnail_robust,
    create_placeholder_thumbnail,
)

# Collect all operator classes for registration
classes = [
    # Server operators
    ANIMLIB_OT_start_server,
    ANIMLIB_OT_stop_server,
    ANIMLIB_OT_test_connection,
    ANIMLIB_OT_get_scene_info,
    
    # Library operators
    ANIMLIB_OT_extract_current,
    ANIMLIB_OT_optimize_library,
    ANIMLIB_OT_validate_library,
    
    # Preview operators
    ANIMATIONLIBRARY_OT_update_preview,
]

def register():
    """Register all operator classes"""
    import bpy
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    """Unregister all operator classes"""
    import bpy
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
