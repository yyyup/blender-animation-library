"""
Preview-related operators for Animation Library
Handles video preview capture and updates (replaces thumbnail system)
"""

import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from pathlib import Path
from .utils import capture_viewport_thumbnail_robust


class ANIMATIONLIBRARY_OT_update_preview(Operator):
    """Update video preview for animation - NEW VIDEO PREVIEW SYSTEM"""
    bl_idname = "animationlibrary.update_preview"
    bl_label = "Update Animation Preview"
    bl_description = "Capture a new viewport video preview for the specified animation"
    bl_options = {'REGISTER', 'UNDO'}
    
    animation_name: StringProperty(
        name="Animation Name",
        description="Name of the animation to update preview for",
        default=""
    )
    
    folder_path: StringProperty(
        name="Folder Path",
        description="Folder path where the preview is located (e.g., 'Root', 'New Folder')",
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
            print(f"🎬 STEP 1: Updating video preview for animation: {target_name}")
            
            # Find existing preview file by searching the previews directory
            preview_path = self.find_existing_preview_file(library_path, target_name, self.folder_path)
            
            if not preview_path:
                print(f"❌ No existing preview found for: {target_name}")
                self.report({'ERROR'}, f"No existing preview found for: {target_name}")
                return {'CANCELLED'}
            
            print(f"🎬 STEP 2: Found existing preview: {preview_path}")
            
            # Remove the existing file
            if preview_path.exists():
                preview_path.unlink()
                print(f"🗑️ Removed existing preview: {preview_path.name}")
            
            # Capture new video preview to the SAME path
            print(f"🎬 STEP 3: Capturing new video preview...")
            preview_success = self.capture_video_preview(str(preview_path), context)
            
            if preview_success and preview_path.exists() and preview_path.stat().st_size > 0:
                # Calculate relative path from library root
                relative_path = str(preview_path.relative_to(Path(library_path)))
                
                print(f"✅ Successfully updated existing preview")
                print(f"   📁 File: {preview_path.name}")
                print(f"   📂 Relative path: {relative_path}")
                
                # Send notification to GUI
                from .. import server
                if server.animation_server and server.animation_server.is_running:
                    server.animation_server.send_message({
                        'type': 'preview_updated',
                        'animation_name': target_name,
                        'preview': relative_path,
                        'status': 'success'
                    })
                    print(f"📤 Sent notification to GUI")
                
                self.report({'INFO'}, f"✅ Updated existing preview: {preview_path.name}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"Failed to capture new video preview")
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Preview update failed: {str(e)}")
            print(f"❌ Preview update error: {e}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
    
    def find_existing_preview_file(self, library_path: str, animation_name: str, folder_path: str):
        """Find existing preview file by searching the specific folder in previews directory"""
        try:
            # Look in the specific folder under previews/
            previews_dir = Path(library_path) / 'previews' / folder_path
            
            if not previews_dir.exists():
                print(f"⚠️ Previews directory doesn't exist: {previews_dir}")
                return None
            
            print(f"🔍 Searching for previews containing '{animation_name}' in folder: {previews_dir}")
            
            # Get all MP4 files in the specific folder
            all_previews = list(previews_dir.glob("*.mp4"))
            print(f"🔍 Found {len(all_previews)} total MP4 files in folder")
            
            # Find files that contain the animation name
            matching_files = []
            for preview_file in all_previews:
                if animation_name in preview_file.name:
                    matching_files.append(preview_file)
                    print(f"🔍 MATCH: {preview_file.name}")
            
            if matching_files:
                # If multiple files found, use the most recent one
                most_recent = max(matching_files, key=lambda f: f.stat().st_mtime)
                print(f"🔍 Using most recent: {most_recent.name}")
                return most_recent
            else:
                print(f"🔍 No preview files found containing '{animation_name}' in folder {folder_path}")
                
                # Debug: show all files for troubleshooting
                print(f"🔍 All preview files in folder:")
                for preview_file in all_previews:
                    print(f"   - {preview_file.name}")
                
                return None
                
        except Exception as e:
            print(f"❌ Error searching preview files: {e}")
            return None
    
    def capture_video_preview(self, output_path: str, context) -> bool:
        """Capture video preview using OpenGL playblast"""
        try:
            scene = context.scene
            
            # Store original settings
            original_settings = {
                'filepath': scene.render.filepath,
                'engine': scene.render.engine,
                'resolution_x': scene.render.resolution_x,
                'resolution_y': scene.render.resolution_y,
                'fps': scene.render.fps,
                'fps_base': scene.render.fps_base,
                'image_settings': scene.render.image_settings.file_format,
                'ffmpeg_format': getattr(scene.render.ffmpeg, 'format', None) if hasattr(scene.render, 'ffmpeg') else None,
                'ffmpeg_codec': getattr(scene.render.ffmpeg, 'codec', None) if hasattr(scene.render, 'ffmpeg') else None,
            }
            
            # Set preview settings
            scene.render.resolution_x = 512
            scene.render.resolution_y = 512
            scene.render.fps = 24
            scene.render.fps_base = 1.0
            scene.render.filepath = Path(output_path).with_suffix("").as_posix()
            scene.render.image_settings.file_format = 'FFMPEG'
            
            if hasattr(scene.render, 'ffmpeg'):
                scene.render.ffmpeg.format = 'MPEG4'
                scene.render.ffmpeg.codec = 'H264'
            
            # Use appropriate render engine
            available_engines = [item.identifier for item in bpy.types.Scene.bl_rna.properties['render'].bl_rna.properties['engine'].enum_items]
            if 'BLENDER_EEVEE_NEXT' in available_engines:
                scene.render.engine = 'BLENDER_EEVEE_NEXT'
            elif 'BLENDER_EEVEE' in available_engines:
                scene.render.engine = 'BLENDER_EEVEE'
            else:
                scene.render.engine = 'BLENDER_WORKBENCH'
            
            # Capture playblast
            print(f"🎬 Capturing playblast preview: {output_path}")
            bpy.ops.render.opengl(animation=True, view_context=True)
            
            # Restore original settings
            for key, value in original_settings.items():
                if value is not None:
                    if '.' in key:
                        obj, attr = key.rsplit('.', 1)
                        setattr(getattr(scene.render, obj), attr, value)
                    else:
                        setattr(scene.render, key, value)
            
            print(f"✅ Preview capture completed: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error capturing video preview: {e}")
            return False


def register():
    """Register preview operators"""
    bpy.utils.register_class(ANIMATIONLIBRARY_OT_update_preview)


def unregister():
    """Unregister preview operators"""
    bpy.utils.unregister_class(ANIMATIONLIBRARY_OT_update_preview)
