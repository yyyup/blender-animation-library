"""
Thumbnail-related operators for Animation Library
Handles thumbnail capture and updates
"""

import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from pathlib import Path
from .utils import capture_viewport_thumbnail_robust


class ANIMATIONLIBRARY_OT_update_thumbnail(Operator):
    """Update thumbnail for animation by name - FIXED VERSION"""
    bl_idname = "animationlibrary.update_thumbnail"
    bl_label = "Update Animation Thumbnail"
    bl_description = "Capture a new viewport thumbnail for the specified animation"
    bl_options = {'REGISTER', 'UNDO'}
    
    animation_name: StringProperty(
        name="Animation Name",
        description="Name of the animation to update thumbnail for",
        default=""
    )
    
    folder_path: StringProperty(
        name="Folder Path",
        description="Folder path where the thumbnail is located (e.g., 'Root', 'New Folder')",
        default="Root"
    )
    
    def execute(self, context):
        # Get library path from addon preferences
        addon_prefs = context.preferences.addons[__package__.split('.')[0]].preferences
        library_path = addon_prefs.library_path if hasattr(addon_prefs, 'library_path') else "./animation_library"
        
        try:
            if not self.animation_name:
                self.report({'ERROR'}, "No animation name provided")
                return {'CANCELLED'}
            
            target_name = self.animation_name
            print(f"🎬 STEP 1: Updating thumbnail for animation: {target_name}")
            
            # Find existing thumbnail file by searching the thumbnails directory
            thumbnail_path = self.find_existing_thumbnail_file(library_path, target_name, self.folder_path)
            
            if not thumbnail_path:
                print(f"❌ No existing thumbnail found for: {target_name}")
                self.report({'ERROR'}, f"No existing thumbnail found for: {target_name}")
                return {'CANCELLED'}
            
            print(f"🎬 STEP 2: Found existing thumbnail: {thumbnail_path}")
            
            # Remove the existing file
            if thumbnail_path.exists():
                thumbnail_path.unlink()
                print(f"🗑️ Removed existing thumbnail: {thumbnail_path.name}")
            
            # Capture new thumbnail to the SAME path
            print(f"🎬 STEP 3: Capturing new thumbnail...")
            thumbnail_success = capture_viewport_thumbnail_robust(str(thumbnail_path))
            
            if thumbnail_success and thumbnail_path.exists() and thumbnail_path.stat().st_size > 0:
                # Calculate relative path from library root
                relative_path = str(thumbnail_path.relative_to(Path(library_path)))
                
                print(f"✅ Successfully updated existing thumbnail")
                print(f"   📁 File: {thumbnail_path.name}")
                print(f"   📂 Relative path: {relative_path}")
                
                # Send notification to GUI
                from .. import server
                if server.animation_server and server.animation_server.is_running:
                    server.animation_server.send_message({
                        'type': 'thumbnail_updated',
                        'animation_name': target_name,
                        'thumbnail': relative_path,
                        'status': 'success'
                    })
                    print(f"📤 Sent notification to GUI")
                
                self.report({'INFO'}, f"✅ Updated existing thumbnail: {thumbnail_path.name}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"Failed to capture new thumbnail")
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Thumbnail update failed: {str(e)}")
            print(f"❌ Thumbnail update error: {e}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
    
    def find_existing_thumbnail_file(self, library_path: str, animation_name: str, folder_path: str):
        """Find existing thumbnail file by searching the specific folder in thumbnails directory"""
        try:
            # Look in the specific folder under thumbnails/
            thumbnails_dir = Path(library_path) / 'thumbnails' / folder_path
            
            if not thumbnails_dir.exists():
                print(f"⚠️ Thumbnails directory doesn't exist: {thumbnails_dir}")
                return None
            
            print(f"🔍 Searching for thumbnails containing '{animation_name}' in folder: {thumbnails_dir}")
            
            # Get all PNG files in the specific folder
            all_thumbnails = list(thumbnails_dir.glob("*.png"))
            print(f"🔍 Found {len(all_thumbnails)} total PNG files in folder")
            
            # Find files that contain the animation name
            matching_files = []
            for thumbnail_file in all_thumbnails:
                if animation_name in thumbnail_file.name:
                    matching_files.append(thumbnail_file)
                    print(f"🔍 MATCH: {thumbnail_file.name}")
            
            if matching_files:
                # If multiple files found, use the most recent one
                most_recent = max(matching_files, key=lambda f: f.stat().st_mtime)
                print(f"🔍 Using most recent: {most_recent.name}")
                return most_recent
            else:
                print(f"🔍 No thumbnail files found containing '{animation_name}' in folder {folder_path}")
                
                # Debug: show all files for troubleshooting
                print(f"🔍 All thumbnail files in folder:")
                for thumbnail_file in all_thumbnails:
                    print(f"   - {thumbnail_file.name}")
                
                return None
                
        except Exception as e:
            print(f"❌ Error searching thumbnail files: {e}")
            return None
