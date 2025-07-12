"""
Animation Library Operators - Modular Structure
Main registration point for all operator modules
"""

import bpy

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

# Import utility functions to make them available
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
    print("🔧 Registering Animation Library operators...")
    
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"  ✅ {cls.bl_idname}")
        except Exception as e:
            print(f"  ❌ Failed to register {cls.__name__}: {e}")
            raise e
    
    print(f"✅ Registered {len(classes)} operator classes")


def unregister():
    """Unregister all operator classes"""
    print("🔧 Unregistering Animation Library operators...")
    
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"  ⚠️ Failed to unregister {cls.__name__}: {e}")
    
    print("✅ All operators unregistered")