# File: src/blender_animation_library/operators/preview_ops.py
# SIMPLE APPROACH: Just delete old file and create new one with same name

import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from pathlib import Path

class ANIMATIONLIBRARY_OT_update_preview(Operator):
    """Update video preview for animation - SIMPLE VERSION"""
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
        description="Folder path where the preview is located",
        default="Root"
    )
    
    def execute(self, context):
        addon_prefs = context.preferences.addons[__package__.split('.')[0]].preferences
        library_path = addon_prefs.library_path if hasattr(addon_prefs, 'library_path') else "./animation_library"
        
        try:
            if not self.animation_name:
                self.report({'ERROR'}, "No animation name provided")
                return {'CANCELLED'}
            
            # STEP 1: Find the existing preview file
            existing_preview = self.find_existing_preview_file(library_path, self.animation_name, self.folder_path)
            
            if not existing_preview:
                print(f"❌ No existing preview found for: {self.animation_name}")
                self.report({'ERROR'}, f"No existing preview found for: {self.animation_name}")
                return {'CANCELLED'}
            
            print(f"🎬 Found existing preview: {existing_preview}")
            
            # STEP 2: Get the EXACT filename to recreate
            target_filename = existing_preview.name
            target_path = existing_preview
            
            print(f"🎯 Target: {target_filename}")
            print(f"🎯 Path: {target_path}")
            
            # STEP 3: Request GUI to release the file
            print(f"🔓 Requesting GUI to release file...")
            self.request_gui_file_release(self.animation_name)
            
            # STEP 4: Wait for GUI to release with retry mechanism
            import time
            max_attempts = 10
            attempt = 0
            
            while attempt < max_attempts:
                time.sleep(0.5)
                try:
                    # Try to delete the file
                    if target_path.exists():
                        target_path.unlink()
                        print(f"🗑️ Deleted old file: {target_filename}")
                        break
                except PermissionError:
                    attempt += 1
                    print(f"⏳ File still locked, attempt {attempt}/{max_attempts}")
                    if attempt >= max_attempts:
                        print(f"❌ Could not unlock file after {max_attempts} attempts")
                        self.report({'ERROR'}, "File is locked by another process. Please close video preview and try again.")
                        return {'CANCELLED'}
                except Exception as e:
                    print(f"❌ Error deleting file: {e}")
                    self.report({'ERROR'}, f"Could not delete old file: {e}")
                    return {'CANCELLED'}
            
            # STEP 5: Create new file with EXACT same name
            print(f"🎬 Creating new preview with exact same name...")
            preview_success = self.capture_video_preview(str(target_path), context)
            
            if not preview_success:
                print(f"❌ Failed to create new preview")
                self.report({'ERROR'}, "Failed to create new preview")
                return {'CANCELLED'}
            
            # STEP 6: Verify the file exists with correct name
            if target_path.exists() and target_path.stat().st_size > 0:
                relative_path = f"previews/{self.folder_path}/{target_filename}"
                
                print(f"✅ Preview updated successfully: {target_filename}")
                print(f"   📂 Size: {target_path.stat().st_size} bytes")
                
                # Send notification to GUI
                from .. import server
                if server.animation_server and server.animation_server.is_running:
                    server.animation_server.send_message({
                        'type': 'preview_updated',
                        'animation_name': self.animation_name,
                        'preview': relative_path,
                        'status': 'success'
                    })
                    print(f"📤 Sent notification to GUI")
                
                self.report({'INFO'}, f"Preview updated: {target_filename}")
                return {'FINISHED'}
            else:
                print(f"❌ New file verification failed")
                self.report({'ERROR'}, "New file verification failed")
                return {'CANCELLED'}
                
        except Exception as e:
            print(f"❌ Preview update error: {e}")
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"Preview update failed: {str(e)}")
            return {'CANCELLED'}
    
    def find_existing_preview_file(self, library_path: str, animation_name: str, folder_path: str):
        """Find existing preview file"""
        try:
            previews_dir = Path(library_path) / 'previews' / folder_path
            
            if not previews_dir.exists():
                print(f"⚠️ Previews directory doesn't exist: {previews_dir}")
                return None
            
            # Get all MP4 files in the folder
            all_previews = list(previews_dir.glob("*.mp4"))
            print(f"🔍 Found {len(all_previews)} MP4 files in folder")
            
            # Find files that contain the animation name
            matching_files = []
            for preview_file in all_previews:
                if animation_name in preview_file.name:
                    matching_files.append(preview_file)
                    print(f"🔍 MATCH: {preview_file.name}")
            
            if matching_files:
                # Use the most recent one
                most_recent = max(matching_files, key=lambda f: f.stat().st_mtime)
                print(f"🔍 Using: {most_recent.name}")
                return most_recent
            else:
                print(f"🔍 No matching files for '{animation_name}'")
                return None
                
        except Exception as e:
            print(f"❌ Error searching preview files: {e}")
            return None
    
    def capture_video_preview(self, output_path: str, context) -> bool:
        """SIMPLE video capture - just create the file at the exact path"""
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
                'file_format': scene.render.image_settings.file_format,
            }
            
            if hasattr(scene.render, 'ffmpeg'):
                original_settings.update({
                    'ffmpeg_format': getattr(scene.render.ffmpeg, 'format', None),
                    'ffmpeg_codec': getattr(scene.render.ffmpeg, 'codec', None),
                })
            
            # Set render settings
            scene.render.resolution_x = 512
            scene.render.resolution_y = 512
            scene.render.fps = 24
            scene.render.fps_base = 1.0
            scene.render.image_settings.file_format = 'FFMPEG'
            
            if hasattr(scene.render, 'ffmpeg'):
                scene.render.ffmpeg.format = 'MPEG4'
                scene.render.ffmpeg.codec = 'H264'
            
            # Set render engine
            try:
                scene.render.engine = 'BLENDER_EEVEE'
                print(f"🎬 Using EEVEE engine")
            except:
                scene.render.engine = 'BLENDER_WORKBENCH'
                print(f"🎬 Using WORKBENCH engine")
            
            # SIMPLE: Set the filepath without extension, let Blender add .mp4
            output_file = Path(output_path)
            base_path = output_file.with_suffix("")
            scene.render.filepath = str(base_path)
            
            print(f"🎬 Render filepath: {scene.render.filepath}")
            print(f"🎬 Expected output: {output_path}")
            
            # Capture the video
            bpy.ops.render.opengl(animation=True, view_context=True)
            
            # Restore settings
            scene.render.filepath = original_settings['filepath']
            scene.render.engine = original_settings['engine']
            scene.render.resolution_x = original_settings['resolution_x']
            scene.render.resolution_y = original_settings['resolution_y']
            scene.render.fps = original_settings['fps']
            scene.render.fps_base = original_settings['fps_base']
            scene.render.image_settings.file_format = original_settings['file_format']
            
            if hasattr(scene.render, 'ffmpeg') and 'ffmpeg_format' in original_settings:
                if original_settings['ffmpeg_format'] is not None:
                    scene.render.ffmpeg.format = original_settings['ffmpeg_format']
                if original_settings['ffmpeg_codec'] is not None:
                    scene.render.ffmpeg.codec = original_settings['ffmpeg_codec']
            
            # Check if file was created
            target_file = Path(output_path)
            if target_file.exists() and target_file.stat().st_size > 0:
                print(f"✅ Video created: {target_file.name} ({target_file.stat().st_size} bytes)")
                return True
            else:
                # Check for files with frame numbers that Blender might have created
                parent_dir = target_file.parent
                base_name = target_file.stem
                potential_files = list(parent_dir.glob(f"{base_name}*.mp4"))
                
                if potential_files:
                    # Take the first one and rename it to our target
                    actual_file = potential_files[0]
                    print(f"🔄 Found {actual_file.name}, renaming to {target_file.name}")
                    actual_file.rename(target_file)
                    return True
                else:
                    print(f"❌ No video file created")
                    return False
                
        except Exception as e:
            print(f"❌ Error capturing video: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def request_gui_file_release(self, animation_id: str):
        """Request GUI to release video file with more aggressive approach"""
        try:
            import time
            from .. import server
            if server.animation_server and server.animation_server.is_running:
                message = {
                    "type": "release_file_request", 
                    "animation_id": animation_id,
                    "timestamp": time.time(),
                    "force_release": True  # NEW: Force release flag
                }
                server.animation_server.send_message(message)
                print(f"📤 Requested FORCE file release for: {animation_id}")
                
                # Send multiple release requests to be sure
                for i in range(3):
                    time.sleep(0.1)
                    server.animation_server.send_message(message)
                    print(f"📤 Release request {i+1}/3 sent")
                    
        except Exception as e:
            print(f"⚠️ Could not request file release: {e}")


def register():
    bpy.utils.register_class(ANIMATIONLIBRARY_OT_update_preview)


def unregister():
    bpy.utils.unregister_class(ANIMATIONLIBRARY_OT_update_preview)