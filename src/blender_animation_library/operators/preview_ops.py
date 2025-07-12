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
            
            animation_id = self.animation_name
            folder_path = self.folder_path
            
            # Build file paths
            preview_dir = Path(library_path) / "previews" / folder_path
            preview_dir.mkdir(parents=True, exist_ok=True)
            
            final_filename = f"{animation_id}.mp4"
            temp_filename = f"{animation_id}.tmp.mp4"
            
            final_path = preview_dir / final_filename
            temp_path = preview_dir / temp_filename
            
            print(f"🎬 STEP 1: Animation ID: {animation_id}")
            print(f"🎬 STEP 2: Final filename: {final_filename}")
            print(f"🎬 STEP 3: Temp filename: {temp_filename}")
            print(f"🎬 STEP 4: Full paths - Final: {final_path}")
            print(f"🎬 STEP 5: Full paths - Temp: {temp_path}")
            
            # STEP 1: Generate to temporary file (no conflicts)
            print(f"🎬 STEP 6: Creating temporary preview...")
            preview_success = self.capture_video_preview(str(temp_path), context)
            
            if not preview_success or not temp_path.exists():
                print(f"❌ Failed to create temporary preview")
                self.report({'ERROR'}, "Failed to create temporary preview")
                return {'CANCELLED'}
            
            print(f"✅ Temporary preview created: {temp_path.name} ({temp_path.stat().st_size} bytes)")
            
            # STEP 2: Request GUI to release the final file
            print(f"🔓 STEP 7: Requesting file release from GUI...")
            self.request_gui_file_release(animation_id)
            
            # STEP 3: Brief wait for GUI to release
            import time
            time.sleep(0.5)
            
            # STEP 4: Atomic replacement
            try:
                if final_path.exists():
                    final_path.unlink()
                    print(f"🗑️ Deleted old file: {final_filename}")
                
                temp_path.rename(final_path)
                print(f"✅ Renamed temp file to: {final_filename}")
                
            except Exception as e:
                print(f"❌ File replacement failed: {e}")
                # Cleanup temp file
                if temp_path.exists():
                    temp_path.unlink()
                self.report({'ERROR'}, f"File replacement failed: {str(e)}")
                return {'CANCELLED'}
            
            # STEP 5: Verify final file
            if final_path.exists() and final_path.stat().st_size > 0:
                # Calculate relative path for notification
                relative_path = f"previews/{folder_path}/{final_filename}"
                
                print(f"✅ Preview update successful: {final_filename} ({final_path.stat().st_size} bytes)")
                print(f"   📂 Relative path: {relative_path}")
                
                # Send notification to GUI
                from .. import server
                if server.animation_server and server.animation_server.is_running:
                    server.animation_server.send_message({
                        'type': 'preview_updated',
                        'animation_name': animation_id,
                        'preview': relative_path,
                        'status': 'success',
                        'strategy': 'temporary_file'
                    })
                    print(f"📤 Sent notification to GUI")
                
                self.report({'INFO'}, f"Preview updated: {final_filename}")
                return {'FINISHED'}
            else:
                print(f"❌ Final file verification failed")
                self.report({'ERROR'}, "Final file verification failed")
                return {'CANCELLED'}
                
        except Exception as e:
            print(f"❌ Preview update error: {e}")
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"Preview update failed: {str(e)}")
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
            
            # Store original settings to restore later
            original_settings = {
                'filepath': scene.render.filepath,
                'engine': scene.render.engine,
                'resolution_x': scene.render.resolution_x,
                'resolution_y': scene.render.resolution_y,
                'fps': scene.render.fps,
                'fps_base': scene.render.fps_base,
                'image_settings_format': scene.render.image_settings.file_format,
            }
            
            # Also store FFmpeg settings if available
            if hasattr(scene.render, 'ffmpeg'):
                original_settings['ffmpeg_format'] = getattr(scene.render.ffmpeg, 'format', None)
                original_settings['ffmpeg_codec'] = getattr(scene.render.ffmpeg, 'codec', None)
            
            # Configure render settings for video preview (512x512, MP4, H264)
            scene.render.resolution_x = 512
            scene.render.resolution_y = 512
            scene.render.fps = 24
            scene.render.fps_base = 1.0
            scene.render.filepath = Path(output_path).with_suffix("").as_posix()
            scene.render.image_settings.file_format = 'FFMPEG'
            
            # Configure FFmpeg settings for MP4/H264 output
            if hasattr(scene.render, 'ffmpeg'):
                scene.render.ffmpeg.format = 'MPEG4'
                scene.render.ffmpeg.codec = 'H264'
            
            # Use appropriate render engine (try Eevee first, fallback to Workbench)
            try:
                available_engines = [item.identifier for item in bpy.types.Scene.bl_rna.properties['render'].bl_rna.properties['engine'].enum_items]
                if 'BLENDER_EEVEE_NEXT' in available_engines:
                    scene.render.engine = 'BLENDER_EEVEE_NEXT'
                elif 'BLENDER_EEVEE' in available_engines:
                    scene.render.engine = 'BLENDER_EEVEE'
                else:
                    scene.render.engine = 'BLENDER_WORKBENCH'
            except:
                # Simple fallback if engine detection fails
                scene.render.engine = 'BLENDER_WORKBENCH'
            
            print(f"🎬 Capturing OpenGL playblast to: {output_path}")
            print(f"   📐 Resolution: {scene.render.resolution_x}x{scene.render.resolution_y}")
            print(f"   🎥 Format: {scene.render.image_settings.file_format}")
            print(f"   🎨 Engine: {scene.render.engine}")
            
            # Capture the animation using OpenGL playblast
            bpy.ops.render.opengl(animation=True, view_context=True)
            
            # Restore original render settings
            scene.render.filepath = original_settings['filepath']
            scene.render.engine = original_settings['engine']
            scene.render.resolution_x = original_settings['resolution_x']
            scene.render.resolution_y = original_settings['resolution_y']
            scene.render.fps = original_settings['fps']
            scene.render.fps_base = original_settings['fps_base']
            scene.render.image_settings.file_format = original_settings['image_settings_format']
            
            # Restore FFmpeg settings if they were stored
            if hasattr(scene.render, 'ffmpeg'):
                if original_settings.get('ffmpeg_format') is not None:
                    scene.render.ffmpeg.format = original_settings['ffmpeg_format']
                if original_settings.get('ffmpeg_codec') is not None:
                    scene.render.ffmpeg.codec = original_settings['ffmpeg_codec']
            
            # Verify the output file was created successfully
            output_file = Path(output_path)
            if output_file.exists() and output_file.stat().st_size > 0:
                print(f"✅ Video preview created successfully: {output_file.name} ({output_file.stat().st_size} bytes)")
                return True
            else:
                print(f"❌ Video preview file was not created or is empty")
                return False
                
        except Exception as e:
            print(f"❌ Error capturing video preview: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def request_gui_file_release(self, animation_id: str):
        """Request GUI to release video file so it can be replaced"""
        try:
            import time
            from .. import server
            if server.animation_server and server.animation_server.is_running:
                message = {
                    "type": "release_file_request", 
                    "animation_id": animation_id,
                    "timestamp": time.time()
                }
                server.animation_server.send_message(message)
                print(f"📤 Requested file release for: {animation_id}")
            else:
                print(f"⚠️ No server connection - cannot request file release")
        except Exception as e:
            print(f"⚠️ Could not request file release: {e}")


def register():
    """Register preview operators"""
    bpy.utils.register_class(ANIMATIONLIBRARY_OT_update_preview)


def unregister():
    """Unregister preview operators"""
    bpy.utils.unregister_class(ANIMATIONLIBRARY_OT_update_preview)
