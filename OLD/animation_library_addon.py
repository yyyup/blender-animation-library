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
            print(f"🚀 Animation Library server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
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
                        print(f"📱 Client connected: {addr}")
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
                            print("📱 Client disconnected")
                            self.connection.close()
                            self.connection = None
                            self.message_buffer = ""
                except socket.error as e:
                    print(f"Connection error: {e}")
                    self.connection.close()
                    self.connection = None
                    self.message_buffer = ""
            
            self.check_selection_changes()
                
        except Exception as e:
            print(f"Server error: {e}")
                
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
                    print(f"❌ JSON decode error: {e}")
                    print(f"❌ Message was: {complete_message[:100]}...")
        
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
            print(f"🎯 Selection: {list(current_selection)}")
        
    def process_message_data(self, data):
        try:
            command = data.get('command')
            
            print(f"📨 Received command: {command}")
            
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
                    'message': 'Hello from Blender! 🎬'
                })
                
        except Exception as e:
            print(f"❌ Error processing command: {e}")
            self.send_message({
                'type': 'error',
                'message': f'Command processing error: {str(e)}'
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
        
        for fcurve in action.fcurves:
            if 'pose.bones[' in fcurve.data_path:
                bone_name = fcurve.data_path.split('"')[1]
                
                if bone_name not in bone_data:
                    bone_data[bone_name] = {
                        'channels': set(),
                        'keyframe_count': 0
                    }
                
                channel = fcurve.data_path.split('.')[-1]
                bone_data[bone_name]['channels'].add(f"{channel}[{fcurve.array_index}]")
                bone_data[bone_name]['keyframe_count'] += len(fcurve.keyframe_points)
                
                for keyframe in fcurve.keyframe_points:
                    frame = keyframe.co[0]
                    frame_range[0] = min(frame_range[0], frame)
                    frame_range[1] = max(frame_range[1], frame)
        
        for bone in bone_data:
            bone_data[bone]['channels'] = list(bone_data[bone]['channels'])
        
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
        print(f"📤 Extracted animation: {action.name}")
        
    def apply_animation_from_library(self, data):
        if not (bpy.context.active_object and 
                bpy.context.active_object.type == 'ARMATURE'):
            self.send_message({
                'type': 'error',
                'message': 'No active armature found. Please select an armature to apply animation to.'
            })
            return
            
        animation_data = data.get('animation_data')
        bone_mapping = data.get('bone_mapping', {})
        frame_offset = data.get('frame_offset', 1)
        
        if not animation_data or not animation_data.get('bone_data'):
            self.send_message({
                'type': 'error',
                'message': 'No animation data provided'
            })
            return
            
        target_armature = bpy.context.active_object
        
        source_armature_name = animation_data.get('armature_source')
        source_action_name = animation_data.get('name')
        
        source_action = None
        for action in bpy.data.actions:
            if source_action_name in action.name:
                source_action = action
                break
        
        if not source_action:
            print(f"⚠️ Source action '{source_action_name}' not found, creating test animation")
            self.create_test_animation(animation_data, target_armature, bone_mapping, frame_offset)
            return
        
        action_name = f"Applied_{source_action_name}_{int(bpy.context.scene.frame_current)}"
        action_name = action_name.replace("|", "_").replace(" ", "_")
        
        if not target_armature.animation_data:
            target_armature.animation_data_create()
            
        new_action = bpy.data.actions.new(action_name)
        target_armature.animation_data.action = new_action
        
        print(f"🎬 Copying REAL animation: {source_action_name}")
        print(f"   From: {source_armature_name}")
        print(f"   To: {target_armature.name}")
        
        bones_applied = 0
        keyframes_applied = 0
        bones_processed = set()
        
        for fcurve in source_action.fcurves:
            if 'pose.bones[' in fcurve.data_path:
                source_bone = fcurve.data_path.split('"')[1]
                
                target_bone = bone_mapping.get(source_bone, source_bone)
                
                if target_bone in target_armature.pose.bones:
                    new_data_path = fcurve.data_path.replace(f'"{source_bone}"', f'"{target_bone}"')
                    
                    new_fcurve = new_action.fcurves.new(new_data_path, index=fcurve.array_index)
                    
                    for keyframe in fcurve.keyframe_points:
                        new_frame = keyframe.co[0] + frame_offset - 1
                        new_value = keyframe.co[1]
                        
                        new_keyframe = new_fcurve.keyframe_points.insert(new_frame, new_value)
                        
                        new_keyframe.interpolation = keyframe.interpolation
                        new_keyframe.handle_left_type = keyframe.handle_left_type
                        new_keyframe.handle_right_type = keyframe.handle_right_type
                        
                        keyframes_applied += 1
                    
                    if source_bone not in bones_processed:
                        bones_applied += 1
                        bones_processed.add(source_bone)
                        print(f"   ✓ {source_bone} → {target_bone} ({len(fcurve.keyframe_points)} keys)")
        
        bpy.context.view_layer.update()
        
        for area in bpy.context.screen.areas:
            if area.type == 'TIMELINE':
                area.tag_redraw()
            elif area.type == 'VIEW_3D':
                area.tag_redraw()
            elif area.type == 'DOPESHEET_EDITOR':
                area.tag_redraw()
        
        bpy.context.scene.frame_set(bpy.context.scene.frame_current)
        
        target_armature.animation_data.action = new_action
        
        result_data = {
            'type': 'animation_applied',
            'action_name': action_name,
            'bones_applied': bones_applied,
            'keyframes_applied': keyframes_applied,
            'frame_range': animation_data.get('frame_range'),
            'target_armature': target_armature.name,
            'source_action': source_action_name
        }
        
        self.send_message(result_data)
        print(f"✨ Applied REAL animation: {bones_applied} bones, {keyframes_applied} keyframes")
        
    def create_test_animation(self, animation_data, target_armature, bone_mapping, frame_offset):
        action_name = f"Test_{animation_data['name']}_{int(bpy.context.scene.frame_current)}"
        action_name = action_name.replace("|", "_").replace(" ", "_")
        
        if not target_armature.animation_data:
            target_armature.animation_data_create()
            
        new_action = bpy.data.actions.new(action_name)
        target_armature.animation_data.action = new_action
        
        bone_data = animation_data.get('bone_data', {})
        frame_range = animation_data.get('frame_range', [1, 40])
        
        bones_applied = 0
        keyframes_applied = 0
        
        for source_bone, bone_info in bone_data.items():
            target_bone = bone_mapping.get(source_bone, source_bone)
            
            if target_bone in target_armature.pose.bones:
                pose_bone = target_armature.pose.bones[target_bone]
                
                channels = bone_info.get('channels', [])
                
                if any('location' in ch for ch in channels):
                    start_frame = int(frame_range[0])
                    end_frame = int(frame_range[1])
                    
                    pose_bone.location = (0, 0, 0)
                    pose_bone.keyframe_insert(data_path="location", frame=start_frame)
                    
                    pose_bone.location = (0, 2, 0)
                    pose_bone.keyframe_insert(data_path="location", frame=end_frame)
                    
                    keyframes_applied += 6
                    
                bones_applied += 1
                
        bpy.context.view_layer.update()
        for area in bpy.context.screen.areas:
            if area.type in ['TIMELINE', 'VIEW_3D', 'DOPESHEET_EDITOR']:
                area.tag_redraw()
        bpy.context.scene.frame_set(bpy.context.scene.frame_current)
                
        result_data = {
            'type': 'animation_applied',
            'action_name': action_name,
            'bones_applied': bones_applied,
            'keyframes_applied': keyframes_applied,
            'frame_range': frame_range,
            'target_armature': target_armature.name,
            'source_action': 'test_fallback'
        }
        
        self.send_message(result_data)
        print(f"✨ Applied test animation: {bones_applied} bones, {keyframes_applied} keyframes")
        
    def send_message(self, data):
        if self.connection:
            try:
                message = json.dumps(data, indent=2)
                framed_message = message + "\n###END_MESSAGE###\n"
                self.connection.send(framed_message.encode('utf-8'))
                print(f"📤 Sent message: {data.get('type', 'unknown')} ({len(message)} chars)")
            except Exception as e:
                print(f"❌ Failed to send message: {e}")
                
    def stop_server(self):
        self.is_running = False
        if self.connection:
            self.connection.close()
        if self.socket:
            self.socket.close()
        print("🛑 Animation Library server stopped")

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
            self.report({'INFO'}, f"Server started on {prefs.host}:{prefs.port}")
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
                'message': 'Test message from Blender add-on! 🎭',
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
            box.label(text="🟢 Running", icon='CHECKMARK')
            box.label(text=f"Port: {prefs.port}")
            
            if animation_server.connection:
                box.label(text="📱 Client Connected", icon='LINKED')
            else:
                box.label(text="⏳ Waiting for client...", icon='TIME')
            
            box.operator("animlib.stop_server", icon='PAUSE')
            box.operator("animlib.test_connection", icon='NETWORK_DRIVE')
        else:
            box.label(text="🔴 Stopped", icon='X')
            box.operator("animlib.start_server", icon='PLAY')
        
        if (bpy.context.active_object and 
            bpy.context.active_object.type == 'ARMATURE' and
            bpy.context.selected_pose_bones):
            
            selection_box = layout.box()
            selection_box.label(text="Current Selection:", icon='BONE_DATA')
            
            armature = bpy.context.active_object
            selection_box.label(text=f"Armature: {armature.name}")
            
            bones = [bone.name for bone in bpy.context.selected_pose_bones]
            if len(bones) <= 3:
                for bone in bones:
                    selection_box.label(text=f"  • {bone}")
            else:
                selection_box.label(text=f"  • {len(bones)} bones selected")

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