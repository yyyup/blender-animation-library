"""
Utility functions for Animation Library operators
Shared helper functions used across all operator modules
"""

import bpy
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def capture_viewport_thumbnail_robust(output_path: str) -> bool:
    """
    Robust viewport thumbnail capture with multiple fallback methods.
    """
    try:
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"🎬 Starting robust viewport capture to: {output_path}")
        
        # Method 1: Try render.opengl with proper context
        success = _try_opengl_render(output_path_obj)
        if success:
            return True
        
        # Method 2: Try screen.screenshot as fallback
        success = _try_screen_screenshot(output_path_obj)
        if success:
            return True
        
        # Method 3: Try simple render as last resort
        success = _try_simple_render(output_path_obj)
        if success:
            return True
        
        print(f"❌ All thumbnail capture methods failed for: {output_path}")
        return False
        
    except Exception as e:
        print(f"❌ Critical error in thumbnail capture: {e}")
        import traceback
        traceback.print_exc()
        return False


def _try_opengl_render(output_path_obj: Path) -> bool:
    """Try OpenGL render method"""
    try:
        print("🎬 Method 1: Trying OpenGL render...")
        
        # Find the 3D viewport
        viewport_area = None
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                viewport_area = area
                break
        
        if not viewport_area:
            print("⚠️ No 3D viewport found")
            return False
        
        # Store original render settings
        scene = bpy.context.scene
        original_filepath = scene.render.filepath
        original_engine = scene.render.engine
        original_resolution_x = scene.render.resolution_x
        original_resolution_y = scene.render.resolution_y
        original_resolution_percentage = scene.render.resolution_percentage
        
        # Store viewport settings
        viewport_space = None
        for space in viewport_area.spaces:
            if space.type == 'VIEW_3D':
                viewport_space = space
                break
        
        if not viewport_space:
            print("⚠️ No 3D viewport space found")
            return False
        
        original_shading = viewport_space.shading.type
        original_overlays = viewport_space.overlay.show_overlays
        
        try:
            # Configure render settings for thumbnail
            # Check available render engines for Blender 4.0+ compatibility
            available_engines = [item.identifier for item in bpy.types.Scene.bl_rna.properties['render'].bl_rna.properties['engine'].enum_items]
            
            if 'BLENDER_EEVEE_NEXT' in available_engines:
                scene.render.engine = 'BLENDER_EEVEE_NEXT'
            elif 'BLENDER_EEVEE' in available_engines:
                scene.render.engine = 'BLENDER_EEVEE'
            else:
                scene.render.engine = 'BLENDER_WORKBENCH'  # Fallback
            
            scene.render.resolution_x = 512
            scene.render.resolution_y = 512
            scene.render.resolution_percentage = 100
            scene.render.filepath = str(output_path_obj.with_suffix(''))
            
            # Optimize viewport for capture
            if viewport_space.shading.type == 'WIREFRAME':
                viewport_space.shading.type = 'SOLID'
            
            viewport_space.overlay.show_overlays = True
            
            # Force update
            bpy.context.view_layer.update()
            
            # Execute OpenGL render with proper context override
            with bpy.context.temp_override(area=viewport_area, space=viewport_space):
                result = bpy.ops.render.opengl(write_still=True, view_context=True)
                print(f"🎬 OpenGL render result: {result}")
            
        finally:
            # Always restore settings
            scene.render.filepath = original_filepath
            scene.render.engine = original_engine
            scene.render.resolution_x = original_resolution_x
            scene.render.resolution_y = original_resolution_y
            scene.render.resolution_percentage = original_resolution_percentage
            
            viewport_space.shading.type = original_shading
            viewport_space.overlay.show_overlays = original_overlays
        
        # Check if file was created
        if _verify_thumbnail_file(output_path_obj):
            print(f"✅ OpenGL render successful: {output_path_obj}")
            return True
        
        print("⚠️ OpenGL render completed but no file created")
        return False
        
    except Exception as e:
        print(f"⚠️ OpenGL render failed: {e}")
        return False


def _try_screen_screenshot(output_path_obj: Path) -> bool:
    """Try screen.screenshot method"""
    try:
        print("🎬 Method 2: Trying screen screenshot...")
        
        # Remove existing file
        if output_path_obj.exists():
            output_path_obj.unlink()
        
        result = bpy.ops.screen.screenshot(filepath=str(output_path_obj), check_existing=False)
        print(f"📸 Screenshot result: {result}")
        
        if _verify_thumbnail_file(output_path_obj):
            print(f"✅ Screen screenshot successful: {output_path_obj}")
            return True
        
        print("⚠️ Screen screenshot completed but no file created")
        return False
        
    except Exception as e:
        print(f"⚠️ Screen screenshot failed: {e}")
        return False


def _try_simple_render(output_path_obj: Path) -> bool:
    """Try simple render method as last resort"""
    try:
        print("🎬 Method 3: Trying simple render...")
        
        scene = bpy.context.scene
        
        # Store original settings
        original_filepath = scene.render.filepath
        original_resolution_x = scene.render.resolution_x
        original_resolution_y = scene.render.resolution_y
        
        try:
            # Set up simple render
            scene.render.resolution_x = 512
            scene.render.resolution_y = 512
            scene.render.filepath = str(output_path_obj.with_suffix(''))
            
            # Use current viewport camera
            if bpy.context.scene.camera:
                result = bpy.ops.render.render(write_still=True)
                print(f"🎨 Simple render result: {result}")
            else:
                print("⚠️ No camera available for simple render")
                return False
        
        finally:
            # Restore settings
            scene.render.filepath = original_filepath
            scene.render.resolution_x = original_resolution_x
            scene.render.resolution_y = original_resolution_y
        
        if _verify_thumbnail_file(output_path_obj):
            print(f"✅ Simple render successful: {output_path_obj}")
            return True
        
        print("⚠️ Simple render completed but no file created")
        return False
        
    except Exception as e:
        print(f"⚠️ Simple render failed: {e}")
        return False


def _verify_thumbnail_file(output_path_obj: Path) -> bool:
    """Verify that thumbnail file was created and has content"""
    try:
        # Check direct file
        if output_path_obj.exists() and output_path_obj.stat().st_size > 0:
            return True
        
        # Check for files with frame numbers or different extensions
        parent_dir = output_path_obj.parent
        base_name = output_path_obj.stem
        
        # Look for files that start with our base name
        potential_files = list(parent_dir.glob(f"{base_name}*.png"))
        if not potential_files:
            potential_files = list(parent_dir.glob(f"{base_name}*"))
        
        # Find the most recent file
        valid_files = [f for f in potential_files if f.stat().st_size > 0]
        if valid_files:
            # Get the most recent file
            latest_file = max(valid_files, key=lambda f: f.stat().st_mtime)
            
            # Rename to expected filename if different
            if latest_file != output_path_obj:
                if output_path_obj.exists():
                    output_path_obj.unlink()
                latest_file.rename(output_path_obj)
            
            print(f"✅ Found and verified thumbnail: {output_path_obj}")
            return True
        
        return False
        
    except Exception as e:
        print(f"⚠️ File verification failed: {e}")
        return False


def create_placeholder_thumbnail(output_path: str) -> bool:
    """Create a placeholder thumbnail if capture fails"""
    try:
        print(f"🎨 Creating placeholder thumbnail: {output_path}")
        
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a simple text file as placeholder
        placeholder_path = output_path_obj.with_suffix('.txt')
        with open(placeholder_path, 'w') as f:
            f.write(f"Thumbnail capture failed at {datetime.now().isoformat()}")
        
        print(f"📝 Created placeholder file: {placeholder_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create placeholder: {e}")
        return False
