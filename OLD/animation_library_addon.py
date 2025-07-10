import bpy
import socket
import json
import select
from bpy.types import Operator, Panel, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

bl_info = {
    "name": "Animation Library Socket Server",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "3D Viewport > Sidebar > Animation Library",
    "description": "Socket server for external animation library GUI",
    "category": "Animation",
}

# Global server instance
animation_server = None

class AnimationLibraryServer:
    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.socket = None
        self.connection = None
        self.is_running = False
        self.last_selection = set()
        self.message_buffer = ""
        
    def start_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setblocking(False)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.is_running = True
            
            bpy.app.timers.register(self.handle_server, first_interval=0.1)
            print("Animation Library server started on " + str(self.host) + ":" + str(self.port))
            return True
            
        except Exception as e:
            print("Failed to start server: " + str(e))
            return False
            
    def handle_server(self):
        if not self.is_running:
            return None
            
        try:
            if self.connection is None:
                try:
                    ready, _, _ = select.select([self.socket], [], [], 0)
                    if ready:
                        self.connection, addr = self.socket.accept()
                        self.connection.setblocking(False)
                        print("Client connected: " + str(addr))
                        self.send_message({'type': 'connected', 'status': 'success'})
                except socket.error:
                    pass
            
            if self.connection:
                try:
                    ready, _, _ = select.select([self.connection], [], [], 0)
                    if ready:
                        data = self.connection.recv(4096)
                        if data:
                            self.message_buffer += data.decode('utf-8')
                            self.process_buffered_messages()
                        else:
                            print("Client disconnected")
                            self.connection.close()
                            self.connection = None
                            self.message_buffer = ""
                except socket.error as e:
                    print("Connection error: " + str(e))
                    self.connection.close()
                    self.connection = None
                    self.message_buffer = ""
            
            self.check_selection_changes()
                
        except Exception as e:
            print("Server error: " + str(e))
                
        return 0.1
        
    def process_buffered_messages(self):
        while "###END_MESSAGE###" in self.message_buffer:
            message_end = self.message_buffer.find("###END_MESSAGE###")
            complete_message = self.message_buffer[:message_end].strip()
            
            self.message_buffer = self.message_buffer[message_end + len("###END_MESSAGE###"):].strip()
            
            if complete_message:
                try:
                    data = json.loads(complete_message)
                    self.process_message_data(data)
                except json.JSONDecodeError as e:
                    print("JSON decode error: " + str(e))
        
    def check_selection_changes(self):
        current_selection = set()
        armature_name = None
        
        if (bpy.context.active_object and 
            bpy.context.active_object.type == 'ARMATURE' and
            bpy.context.selected_pose_bones):
            
            armature_name = bpy.context.active_object.name
            current_selection = {bone.name for bone in bpy.context.selected_pose_bones}
        
        if current_selection != self.last_selection:
            self.last_selection = current_selection.copy()
            
            selection_data = {
                'type': 'selection_update',
                'armature_name': armature_name,
                'selected_bones': list(current_selection),
                'current_frame': bpy.context.scene.frame_current,
                'frame_range': [bpy.context.scene.frame_start, bpy.context.scene.frame_end]
            }
            
            self.send_message(selection_data)
        
    def process_message_data(self, data):
        try:
            command = data.get('command')
            
            print("Received command: " + str(command))
            
            if command == 'ping':
                self.send_message({'type': 'pong', 'timestamp': data.get('timestamp')})
                
            elif command == 'get_scene_info':
                self.send_scene_info()
                
            elif command == 'extract_animation':
                self.extract_current_animation()
                
            elif command == 'apply_animation':
                self.apply_animation_from_library(data)
                
            elif command == 'test_message':
                self.send_message({
                    'type': 'test_response', 
                    'message': 'Hello from Blender!'
                })
                
        except Exception as e:
            print("Error processing command: " + str(e))
            self.send_message({
                'type': 'error',
                'message': 'Command processing error: ' + str(e)
            })
            
    def send_scene_info(self):
        scene_info = {
            'type': 'scene_info',
            'scene_name': bpy.context.scene.name,
            'current_frame': bpy.context.scene.frame_current,
            'frame_range': [bpy.context.scene.frame_start, bpy.context.scene.frame_end],
            'armatures': []
        }
        
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE':
                armature_data = {
                    'name': obj.name,
                    'bones': [bone.name for bone in obj.pose.bones],
                    'has_animation': obj.animation_data is not None,
                    'active_action': obj.animation_data.action.name if (obj.animation_data and obj.animation_data.action) else None
                }
                scene_info['armatures'].append(armature_data)
        
        self.send_message(scene_info)
        
    def extract_current_animation(self):
        if not (bpy.context.active_object and 
                bpy.context.active_object.type == 'ARMATURE' and
                bpy.context.active_object.animation_data and
                bpy.context.active_object.animation_data.action):
            self.send_message({
                'type': 'error',
                'message': 'No active armature with animation found'
            })
            return
            
        armature = bpy.context.active_object
        action = armature.animation_data.action
        
        bone_data = {}
        frame_range = [float('inf'), float('-inf')]
        
        print("Extracting animation: " + action.name)
        print("Total F-curves: " + str(len(action.fcurves)))
        
        for fcurve in action.fcurves:
            if 'pose.bones[' in fcurve.data_path:
                bone_name = fcurve.data_path.split('"')[1]
                
                if bone_name not in bone_data:
                    bone_data[bone_name] = {
                        'channels': set(),
                        'keyframe_count': 0,
                        'fcurves': {}
                    }
                
                channel = fcurve.data_path.split('.')[-1]
                channel_key = channel + "[" + str(fcurve.array_index) + "]"
                bone_data[bone_name]['channels'].add(channel_key)
                bone_data[bone_name]['keyframe_count'] += len(fcurve.keyframe_points)
                
                # Store F-curve data for reconstruction
                keyframes = []
                for keyframe in fcurve.keyframe_points:
                    frame = keyframe.co[0]
                    value = keyframe.co[1]
                    keyframes.append({
                        'frame': frame,
                        'value': value,
                        'interpolation': keyframe.interpolation,
                        'handle_left_type': keyframe.handle_left_type,
                        'handle_right_type': keyframe.handle_right_type,
                        'handle_left': [keyframe.handle_left[0], keyframe.handle_left[1]],
                        'handle_right': [keyframe.handle_right[0], keyframe.handle_right[1]]
                    })
                    
                    frame_range[0] = min(frame_range[0], frame)
                    frame_range[1] = max(frame_range[1], frame)
                
                bone_data[bone_name]['fcurves'][channel_key] = {
                    'data_path': fcurve.data_path,
                    'array_index': fcurve.array_index,
                    'keyframes': keyframes
                }
                
                print("Bone " + bone_name + "." + channel_key + ": " + str(len(keyframes)) + " keyframes")
        
        # Convert sets to lists for JSON serialization
        for bone_name, bone_info in bone_data.items():
            bone_info['channels'] = list(bone_info['channels'])
            print("Bone " + bone_name + ": " + str(len(bone_info['fcurves'])) + " F-curves, " + str(bone_info['keyframe_count']) + " total keyframes")
        
        extraction_data = {
            'type': 'animation_extracted',
            'action_name': action.name,
            'armature_name': armature.name,
            'bone_data': bone_data,
            'frame_range': frame_range if frame_range[0] != float('inf') else [1, 1],
            'total_bones_animated': len(bone_data),
            'total_keyframes': sum(len(fc.keyframe_points) for fc in action.fcurves)
        }
        
        self.send_message(extraction_data)
        print("Extracted animation with F-curve data: " + action.name)
        print("Total: " + str(len(bone_data)) + " bones, F-curve data stored for reconstruction")
        
    def apply_animation_from_library(self, data):
        try:
            print("Apply animation command received")
            
            if not (bpy.context.active_object and 
                    bpy.context.active_object.type == 'ARMATURE'):
                error_msg = 'No active armature found. Please select an armature to apply animation to.'
                print("Error: " + error_msg)
                self.send_message({'type': 'error', 'message': error_msg})
                return
                
            animation_data = data.get('animation_data')
            if not animation_data:
                error_msg = 'No animation data provided'
                print("Error: " + error_msg)
                self.send_message({'type': 'error', 'message': error_msg})
                return
            
            print("Animation: " + str(animation_data.get('name', 'Unknown')))
            
            # Get apply options
            selected_bones_only = data.get('selected_bones_only', False)
            frame_offset = data.get('frame_offset', 1)
            channels = data.get('channels', {'location': True, 'rotation': True, 'scale': True})
            
            print("Options: selected_only=" + str(selected_bones_only) + ", offset=" + str(frame_offset))
            
            target_armature = bpy.context.active_object
            
            # Determine target bones FIRST to filter the data early
            if selected_bones_only and bpy.context.selected_pose_bones:
                target_bone_names = {bone.name for bone in bpy.context.selected_pose_bones}
                print("Applying to " + str(len(target_bone_names)) + " selected bones: " + str(list(target_bone_names)[:5]))
            else:
                target_bone_names = {bone.name for bone in target_armature.pose.bones}
                print("Applying to all " + str(len(target_bone_names)) + " bones")
            
            # FILTER the bone data early - only get bones we're actually applying to
            bone_data = animation_data.get('bone_data', {})
            filtered_bone_data = {}
            
            for bone_name, bone_info in bone_data.items():
                if bone_name in target_bone_names and bone_name in target_armature.pose.bones:
                    filtered_bone_data[bone_name] = bone_info
            
            print("Filtered to " + str(len(filtered_bone_data)) + " bones to process (from " + str(len(bone_data)) + " total)")
            
            if len(filtered_bone_data) == 0:
                error_msg = "No matching bones found to apply animation to"
                print("Error: " + error_msg)
                self.send_message({'type': 'error', 'message': error_msg})
                return
            
            # Create new action
            action_name = "Applied_" + str(animation_data.get('name', 'Animation')) + "_" + str(int(bpy.context.scene.frame_current))
            action_name = action_name.replace("|", "_").replace(" ", "_")
            
            if not target_armature.animation_data:
                target_armature.animation_data_create()
                
            new_action = bpy.data.actions.new(action_name)
            target_armature.animation_data.action = new_action
            
            print("Created action: " + action_name)
            
            bones_applied = 0
            keyframes_applied = 0
            bones_with_fcurves = 0
            
            # Now only process the filtered bone data
            total_bones = len(filtered_bone_data)
            processed_count = 0
            
            for source_bone_name, bone_info in filtered_bone_data.items():
                try:
                    processed_count += 1
                    
                    # Show progress for every bone when processing small numbers
                    if total_bones <= 20 or processed_count % 10 == 0:
                        print("Progress: " + str(processed_count) + "/" + str(total_bones) + " - " + source_bone_name)
                    
                    # Get F-curve data if available
                    fcurves_data = bone_info.get('fcurves', {})
                    
                    if fcurves_data:
                        # Use stored F-curve data (preferred method)
                        bones_with_fcurves += 1
                        
                        for channel_key, fcurve_info in fcurves_data.items():
                            try:
                                # Check channel filter
                                channel_name = channel_key.split('[')[0]
                                if not self.should_apply_channel(channel_name, channels):
                                    continue
                                
                                data_path = fcurve_info['data_path']
                                array_index = fcurve_info['array_index']
                                
                                # Create F-curve
                                new_fcurve = new_action.fcurves.new(data_path, index=array_index)
                                
                                # Batch insert keyframes
                                keyframe_data = fcurve_info['keyframes']
                                if keyframe_data:
                                    # Pre-allocate keyframes
                                    new_fcurve.keyframe_points.add(len(keyframe_data))
                                    
                                    # Set keyframe data in batch
                                    for i, kf_data in enumerate(keyframe_data):
                                        new_frame = kf_data['frame'] + frame_offset - 1
                                        new_value = kf_data['value']
                                        
                                        kf_point = new_fcurve.keyframe_points[i]
                                        kf_point.co = (new_frame, new_value)
                                        kf_point.interpolation = kf_data.get('interpolation', 'BEZIER')
                                        kf_point.handle_left_type = kf_data.get('handle_left_type', 'AUTO')
                                        kf_point.handle_right_type = kf_data.get('handle_right_type', 'AUTO')
                                        
                                        keyframes_applied += 1
                                    
                                    # Update F-curve once
                                    new_fcurve.update()
                                    
                            except Exception as e:
                                print("Warning: Error applying F-curve " + channel_key + " for " + source_bone_name)
                        
                        bones_applied += 1
                        
                    else:
                        # Quick fallback for bones without F-curve data
                        channels_list = bone_info.get('channels', [])
                        
                        try:
                            if any('location' in ch for ch in channels_list) and channels.get('location', True):
                                pose_bone = target_armature.pose.bones[source_bone_name]
                                start_frame = int(animation_data.get('frame_range', [1, 40])[0]) + frame_offset - 1
                                pose_bone.keyframe_insert(data_path="location", frame=start_frame)
                                keyframes_applied += 3
                            
                            bones_applied += 1
                        except Exception as e:
                            print("Warning: Error creating fallback for " + source_bone_name)
                            
                except Exception as e:
                    print("Error processing bone " + source_bone_name + ": " + str(e))
                    continue
            
            print("COMPLETED: Applied " + str(bones_applied) + " bones, " + str(keyframes_applied) + " keyframes")
            print("F-curve data available for: " + str(bones_with_fcurves) + " bones")
            
            # Minimal viewport update
            bpy.context.view_layer.update()
            
            result_data = {
                'type': 'animation_applied',
                'action_name': action_name,
                'bones_applied': bones_applied,
                'keyframes_applied': keyframes_applied,
                'frame_range': animation_data.get('frame_range'),
                'target_armature': target_armature.name,
                'source_action': animation_data.get('name', 'stored_data')
            }
            
            self.send_message(result_data)
            print("Animation application completed successfully")
            
        except Exception as e:
            error_msg = "Animation application failed: " + str(e)
            print("Error: " + error_msg)
            import traceback
            traceback.print_exc()
            self.send_message({'type': 'error', 'message': error_msg})
    
    def should_apply_channel(self, channel_name, channels_filter):
        """Check if a channel should be applied based on user selection"""
        if 'location' in channel_name:
            return channels_filter.get('location', True)
        elif 'rotation' in channel_name:
            return channels_filter.get('rotation', True)
        elif 'scale' in channel_name:
            return channels_filter.get('scale', True)
        return True
    
    def create_basic_keyframes(self, armature, bone_name, channel_type, frame_range, frame_offset):
        """Create basic keyframes as fallback when F-curve data is not available"""
        pose_bone = armature.pose.bones[bone_name]
        start_frame = int(frame_range[0]) + frame_offset - 1
        end_frame = int(frame_range[1]) + frame_offset - 1
        
        if channel_type == 'location':
            pose_bone.location = (0, 0, 0)
            pose_bone.keyframe_insert(data_path="location", frame=start_frame)
            pose_bone.location = (0, 0.1, 0)  # Small movement
            pose_bone.keyframe_insert(data_path="location", frame=end_frame)
        elif channel_type == 'rotation_quaternion':
            pose_bone.rotation_quaternion = (1, 0, 0, 0)
            pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=start_frame)
            pose_bone.rotation_quaternion = (0.99, 0.1, 0, 0)  # Small rotation
            pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=end_frame)
        
    def send_message(self, data):
        if self.connection:
            try:
                message = json.dumps(data, indent=2)
                framed_message = message + "\n###END_MESSAGE###\n"
                self.connection.send(framed_message.encode('utf-8'))
            except Exception as e:
                print("Failed to send message: " + str(e))
                
    def stop_server(self):
        self.is_running = False
        if self.connection:
            self.connection.close()
        if self.socket:
            self.socket.close()
        print("Animation Library server stopped")

class ANIMLIB_OT_start_server(Operator):
    bl_idname = "animlib.start_server"
    bl_label = "Start Animation Library Server"
    bl_description = "Start the socket server for external animation library"
    
    def execute(self, context):
        global animation_server
        
        if animation_server and animation_server.is_running:
            self.report({'WARNING'}, "Server is already running")
            return {'CANCELLED'}
        
        prefs = context.preferences.addons[__name__].preferences
        animation_server = AnimationLibraryServer(prefs.host, prefs.port)
        
        if animation_server.start_server():
            self.report({'INFO'}, "Server started on " + prefs.host + ":" + str(prefs.port))
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Failed to start server")
            return {'CANCELLED'}

class ANIMLIB_OT_stop_server(Operator):
    bl_idname = "animlib.stop_server"
    bl_label = "Stop Animation Library Server"
    bl_description = "Stop the animation library server"
    
    def execute(self, context):
        global animation_server
        
        if animation_server and animation_server.is_running:
            animation_server.stop_server()
            animation_server = None
            self.report({'INFO'}, "Server stopped")
        else:
            self.report({'WARNING'}, "Server is not running")
        
        return {'FINISHED'}

class ANIMLIB_OT_test_connection(Operator):
    bl_idname = "animlib.test_connection"
    bl_label = "Test Connection"
    bl_description = "Send a test message to connected client"
    
    def execute(self, context):
        global animation_server
        
        if animation_server and animation_server.is_running and animation_server.connection:
            animation_server.send_message({
                'type': 'test_from_blender',
                'message': 'Test message from Blender add-on!',
                'current_selection': list(animation_server.last_selection)
            })
            self.report({'INFO'}, "Test message sent")
        else:
            self.report({'WARNING'}, "No client connected")
        
        return {'FINISHED'}

class ANIMLIB_PT_main_panel(Panel):
    bl_label = "Animation Library"
    bl_idname = "ANIMLIB_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Animation Library"
    
    def draw(self, context):
        layout = self.layout
        global animation_server
        
        prefs = context.preferences.addons[__name__].preferences
        
        box = layout.box()
        box.label(text="Server Status:", icon='NETWORK_DRIVE')
        
        if animation_server and animation_server.is_running:
            box.label(text="Running", icon='CHECKMARK')
            box.label(text="Port: " + str(prefs.port))
            
            if animation_server.connection:
                box.label(text="Client Connected", icon='LINKED')
            else:
                box.label(text="Waiting for client...", icon='TIME')
            
            box.operator("animlib.stop_server", icon='PAUSE')
            box.operator("animlib.test_connection", icon='NETWORK_DRIVE')
        else:
            box.label(text="Stopped", icon='X')
            box.operator("animlib.start_server", icon='PLAY')
        
        if (bpy.context.active_object and 
            bpy.context.active_object.type == 'ARMATURE' and
            bpy.context.selected_pose_bones):
            
            selection_box = layout.box()
            selection_box.label(text="Current Selection:", icon='BONE_DATA')
            
            armature = bpy.context.active_object
            selection_box.label(text="Armature: " + armature.name)
            
            bones = [bone.name for bone in bpy.context.selected_pose_bones]
            if len(bones) <= 3:
                for bone in bones:
                    selection_box.label(text="  • " + bone)
            else:
                selection_box.label(text="  • " + str(len(bones)) + " bones selected")

class ANIMLIB_preferences(AddonPreferences):
    bl_idname = __name__
    
    host: StringProperty(
        name="Host",
        description="Server host address",
        default="127.0.0.1"
    )
    
    port: IntProperty(
        name="Port",
        description="Server port number",
        default=8080,
        min=1024,
        max=65535
    )
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "host")
        layout.prop(self, "port")

classes = [
    ANIMLIB_OT_start_server,
    ANIMLIB_OT_stop_server,
    ANIMLIB_OT_test_connection,
    ANIMLIB_PT_main_panel,
    ANIMLIB_preferences,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    global animation_server
    if animation_server:
        animation_server.stop_server()
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)