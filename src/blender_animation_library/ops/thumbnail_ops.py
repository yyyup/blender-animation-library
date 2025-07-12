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
        name="Animation ID",
        description="ID of the animation to update thumbnail for",
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
            
            target_id = self.animation_name  # This now contains animation ID
            target_folder = self.folder_path  # Specific folder to search in
            print(f"🎬 STEP 1: Updating thumbnail for animation ID: {target_id} in folder: {target_folder}")
            
            # Find existing thumbnail file in the specific folder
            thumbnail_path = self.find_existing_thumbnail_file(library_path, target_id, target_folder)
            
            if not thumbnail_path:
                print(f"❌ No existing thumbnail found for ID: {target_id} in folder: {target_folder}")
                self.report({'ERROR'}, f"No existing thumbnail found for ID: {target_id} in folder: {target_folder}")
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
                        'animation_name': target_id,  # Send animation ID
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
    
    def find_existing_thumbnail_file(self, library_path: str, animation_id: str, folder_path: str):
        """Find existing thumbnail file in the specific folder path"""
        try:
            thumbnails_dir = Path(library_path) / 'thumbnails'
            
            if not thumbnails_dir.exists():
                print(f"⚠️ Thumbnails directory doesn't exist: {thumbnails_dir}")
                return None
            
            # Search in the specific folder path
            target_folder = thumbnails_dir / folder_path
            
            if not target_folder.exists():
                print(f"⚠️ Target folder doesn't exist: {target_folder}")
                return None
            
            print(f"🔍 Searching for thumbnails with ID '{animation_id}' in specific folder: {target_folder}")
            
            # Search for exact ID match first, then wildcards within the specific folder
            patterns = [
                f"{animation_id}.png",           # Exact ID match
                f"*{animation_id}*.png",         # ID anywhere in filename
            ]
            
            matching_files = []
            for pattern in patterns:
                matches = list(target_folder.glob(pattern))
                for match in matches:
                    if match not in matching_files:
                        matching_files.append(match)
                        relative_path = match.relative_to(thumbnails_dir)
                        print(f"🔍 MATCH: {relative_path}")
                
                # If we found exact matches, don't look for wildcards
                if pattern.startswith(animation_id) and matches:
                    break
            
            if matching_files:
                # If multiple files found, use the most recent one
                most_recent = max(matching_files, key=lambda f: f.stat().st_mtime)
                # Show relative path from thumbnails directory
                relative_path = most_recent.relative_to(thumbnails_dir)
                print(f"🔍 Using most recent: {relative_path}")
                return most_recent
            else:
                print(f"🔍 No thumbnail files found for ID '{animation_id}' in folder '{folder_path}'")
                
                # Debug: show all files in the target folder for troubleshooting
                print(f"🔍 All thumbnail files in {folder_path}:")
                all_thumbnails = list(target_folder.glob("*.png"))
                for thumbnail_file in all_thumbnails:
                    print(f"   - {thumbnail_file.name}")
                
                return None
                
        except Exception as e:
            print(f"❌ Error searching thumbnail files: {e}")
            return None
