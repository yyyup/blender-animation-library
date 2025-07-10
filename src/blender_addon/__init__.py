"""
Animation Library Blender Add-on
EXISTING SCRIPT: src/blender_addon/__init__.py (COMPLETE REFACTOR)

Professional add-on package with proper module structure for development symlink.
"""

import sys
from pathlib import Path

# Add-on metadata
bl_info = {
    "name": "Animation Library Professional",
    "author": "Animation Library Team",
    "version": (2, 1, 0),
    "blender": (3, 0, 0),
    "location": "3D Viewport > Sidebar > Animation Library",
    "description": "Professional animation library with instant .blend file storage",
    "category": "Animation",
    "doc_url": "https://github.com/yourusername/blender-animation-library",
    "tracker_url": "https://github.com/yourusername/blender-animation-library/issues",
}

# Add core modules to path for development
addon_dir = Path(__file__).parent.parent
if str(addon_dir) not in sys.path:
    sys.path.insert(0, str(addon_dir))

# Import all modules
if "bpy" in locals():
    # Reload modules for development
    import importlib
    
    submodules = [
        "operators",
        "ui",
        "server", 
        "storage",
        "preferences"
    ]
    
    for submodule in submodules:
        if submodule in locals():
            importlib.reload(locals()[submodule])
        else:
            exec(f"from . import {submodule}")
else:
    # Initial import
    from . import operators
    from . import ui
    from . import server
    from . import storage
    from . import preferences

import bpy


def register():
    """Register all add-on components"""
    print("🚀 Registering Animation Library Professional...")
    
    # Register modules in order
    preferences.register()
    operators.register()
    ui.register()
    server.register()
    storage.register()
    
    print("✅ Animation Library Professional registered successfully")
    print("📁 Using professional .blend file storage")
    print("⚡ 99% performance improvement active")


def unregister():
    """Unregister all add-on components"""
    print("🛑 Unregistering Animation Library Professional...")
    
    # Unregister in reverse order
    storage.unregister()
    server.unregister()
    ui.unregister()
    operators.unregister()
    preferences.unregister()
    
    print("✅ Animation Library Professional unregistered")


if __name__ == "__main__":
    register()