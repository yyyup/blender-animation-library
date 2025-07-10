#!/usr/bin/env python3
"""
Animation Library Manager - Enhanced client with storage capabilities
Stores and manages animation clips with metadata
"""

import socket
import json
import threading
import time
import os
from datetime import datetime
from pathlib import Path

class AnimationLibraryManager:
    def __init__(self, host='127.0.0.1', port=8080, library_path='./animation_library'):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        
        # Animation library storage
        self.library_path = Path(library_path)
        self.library_path.mkdir(exist_ok=True)
        
        self.metadata_file = self.library_path / 'library_metadata.json'
        self.clips_folder = self.library_path / 'clips'
        self.clips_folder.mkdir(exist_ok=True)
        
        # Load existing library
        self.animation_library = self.load_library()
        
        print(f"📚 Animation Library: {len(self.animation_library)} clips loaded")
        
    def load_library(self):
        """Load animation library metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading library: {e}")
        
        return {"animations": [], "version": "1.0", "created": datetime.now().isoformat()}
    
    def save_library(self):
        """Save animation library metadata"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.animation_library, f, indent=2)
            print("💾 Library saved")
        except Exception as e:
            print(f"❌ Error saving library: {e}")
    
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.running = True
            print(f"✅ Connected to Blender at {self.host}:{self.port}")
            
            # Start listening thread
            listen_thread = threading.Thread(target=self.listen_to_blender, daemon=True)
            listen_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    def listen_to_blender(self):
        """Listen for messages from Blender with proper JSON handling"""
        buffer = ""
        while self.running:
            try:
                data = self.socket.recv(4096)
                if data:
                    buffer += data.decode('utf-8')
                    
                    # Try to parse complete JSON messages
                    while buffer:
                        try:
                            # Find complete JSON object
                            decoder = json.JSONDecoder()
                            message, idx = decoder.raw_decode(buffer)
                            self.handle_blender_message(message)
                            buffer = buffer[idx:].lstrip()
                        except json.JSONDecodeError:
                            # Incomplete JSON, wait for more data
                            break
                else:
                    print("🔌 Connection closed by Blender")
                    break
            except Exception as e:
                if self.running:
                    print(f"Listen error: {e}")
                break
    
    def handle_blender_message(self, message):
        """Process messages from Blender"""
        msg_type = message.get('type')
        
        if msg_type == 'connected':
            print("🎉 Blender confirmed connection!")
            
        elif msg_type == 'selection_update':
            armature = message.get('armature_name')
            bones = message.get('selected_bones', [])
            
            if bones and len(bones) <= 5:  # Only show small selections
                print(f"🎯 Selected: {', '.join(bones)}")
                
        elif msg_type == 'animation_extracted':
            # Automatically store extracted animation
            self.store_animation(message)
            
        elif msg_type == 'animation_applied':
            print(f"\n✨ Animation Applied Successfully!")
            print(f"   Action: {message.get('action_name')}")
            print(f"   Target: {message.get('target_armature')}")
            print(f"   Bones: {message.get('bones_applied')}")
            print(f"   Keyframes: {message.get('keyframes_applied')}")
            print(f"   Frame Range: {message.get('frame_range')}")
            
        elif msg_type == 'scene_info':
            self.display_scene_info(message)
            
        elif msg_type == 'error':
            print(f"❌ Blender Error: {message.get('message')}")
    
    def store_animation(self, animation_data):
        """Store extracted animation in library"""
        action_name = animation_data.get('action_name')
        armature_name = animation_data.get('armature_name')
        
        # Generate unique ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        animation_id = f"{armature_name}_{action_name}_{timestamp}".replace("|", "_").replace(" ", "_")
        
        # Create animation metadata
        animation_metadata = {
            "id": animation_id,
            "name": action_name,
            "description": f"Extracted from {armature_name}",
            "armature_source": armature_name,
            "frame_range": animation_data.get('frame_range'),
            "total_bones_animated": animation_data.get('total_bones_animated'),
            "total_keyframes": animation_data.get('total_keyframes'),
            "bone_data": animation_data.get('bone_data'),
            "created_date": datetime.now().isoformat(),
            "rig_type": "rigify" if "rigify" in armature_name.lower() else "unknown",
            "tags": self.generate_tags(animation_data),
            "category": "extracted",
            "duration_frames": animation_data.get('frame_range', [1, 1])[1] - animation_data.get('frame_range', [1, 1])[0] + 1
        }
        
        # Add to library
        self.animation_library["animations"].append(animation_metadata)
        self.save_library()
        
        print(f"\n📦 Animation Stored!")
        print(f"   ID: {animation_id}")
        print(f"   Name: {action_name}")
        print(f"   Duration: {animation_metadata['duration_frames']} frames")
        print(f"   Bones: {animation_metadata['total_bones_animated']}")
        print(f"   Keyframes: {animation_metadata['total_keyframes']}")
        print(f"   Tags: {', '.join(animation_metadata['tags'])}")
    
    def generate_tags(self, animation_data):
        """Generate automatic tags based on animation data"""
        tags = []
        bone_data = animation_data.get('bone_data', {})
        animated_bones = set(bone_data.keys())
        
        # Locomotion detection
        leg_bones = {'thigh_fk.L', 'thigh_fk.R', 'thigh_ik.L', 'thigh_ik.R', 
                    'shin_fk.L', 'shin_fk.R', 'foot_fk.L', 'foot_fk.R'}
        if animated_bones & leg_bones:
            tags.append("locomotion")
        
        # Upper body detection
        arm_bones = {'upper_arm_fk.L', 'upper_arm_fk.R', 'forearm_fk.L', 'forearm_fk.R'}
        if animated_bones & arm_bones:
            tags.append("upper_body")
        
        # Facial animation detection
        face_bones = {'jaw', 'eyes', 'brow', 'lip', 'cheek'}
        if any(face_bone in str(animated_bones) for face_bone in face_bones):
            tags.append("facial")
        
        # Finger animation detection
        finger_bones = {'thumb', 'f_index', 'f_middle', 'f_ring', 'f_pinky'}
        if any(finger_bone in str(animated_bones) for finger_bone in finger_bones):
            tags.append("hands")
        
        # Spine animation
        if any('spine' in bone for bone in animated_bones):
            tags.append("spine")
        
        # Duration-based tags
        duration = animation_data.get('frame_range', [1, 1])[1] - animation_data.get('frame_range', [1, 1])[0] + 1
        if duration < 10:
            tags.append("short")
        elif duration > 100:
            tags.append("long")
        else:
            tags.append("medium")
        
        # Keyframe density
        keyframe_density = animation_data.get('total_keyframes', 0) / max(duration, 1)
        if keyframe_density > 20:
            tags.append("dense")
        elif keyframe_density < 5:
            tags.append("sparse")
        
        return tags if tags else ["uncategorized"]
    
    def display_scene_info(self, scene_info):
        print("\n📊 Scene Information:")
        print(f"   Scene: {scene_info.get('scene_name')}")
        print(f"   Frame: {scene_info.get('current_frame')}")
        print(f"   Range: {scene_info.get('frame_range')}")
        
        armatures = scene_info.get('armatures', [])
        if armatures:
            print(f"   Armatures ({len(armatures)}):")
            for arm in armatures:
                action_info = f" → {arm['active_action']}" if arm.get('active_action') else ""
                print(f"     • {arm['name']} ({len(arm['bones'])} bones){action_info}")
    
    def list_animations(self, filter_tags=None):
        """List stored animations with optional tag filtering"""
        animations = self.animation_library.get("animations", [])
        
        if filter_tags:
            animations = [anim for anim in animations 
                         if any(tag in anim.get('tags', []) for tag in filter_tags)]
        
        if not animations:
            print("📭 No animations found" + (f" with tags: {filter_tags}" if filter_tags else ""))
            return
        
        print(f"\n📚 Animation Library ({len(animations)} clips):")
        print("-" * 80)
        
        for i, anim in enumerate(animations, 1):
            print(f"{i:2d}. {anim['name']}")
            print(f"    ID: {anim['id']}")
            print(f"    Duration: {anim['duration_frames']} frames | Bones: {anim['total_bones_animated']} | Keys: {anim['total_keyframes']}")
            print(f"    Tags: {', '.join(anim['tags'])}")
            print(f"    Created: {anim['created_date'][:16]}")
            print()
    
    def search_animations(self, query):
        """Search animations by name, tags, or description"""
        query = query.lower()
        animations = self.animation_library.get("animations", [])
        
        results = []
        for anim in animations:
            if (query in anim['name'].lower() or 
                query in anim.get('description', '').lower() or
                any(query in tag for tag in anim.get('tags', []))):
                results.append(anim)
        
        if results:
            print(f"\n🔍 Search Results for '{query}' ({len(results)} found):")
            print("-" * 50)
            for anim in results:
                print(f"• {anim['name']} - {', '.join(anim['tags'])}")
        else:
            print(f"🔍 No animations found matching '{query}'")
            
    def get_animation_by_index(self, index):
        """Get animation by list index (1-based)"""
        animations = self.animation_library.get("animations", [])
        if 1 <= index <= len(animations):
            return animations[index - 1]
        return None
        
    def apply_animation_by_id(self, animation_id, bone_mapping=None, frame_offset=1):
        """Apply animation from library by ID"""
        animations = self.animation_library.get("animations", [])
        animation = next((anim for anim in animations if anim['id'] == animation_id), None)
        
        if not animation:
            print(f"❌ Animation not found: {animation_id}")
            return False
            
        # Use automatic bone mapping if none provided
        if bone_mapping is None:
            bone_mapping = {}
            
        command = {
            'command': 'apply_animation',
            'animation_data': animation,
            'bone_mapping': bone_mapping,
            'frame_offset': frame_offset
        }
        
        self.send_command(command)
        print(f"📤 Applying animation: {animation['name']}")
        return True
    
    def send_command(self, command_data):
        """Send command to Blender with proper message framing"""
        try:
            message = json.dumps(command_data)
            # Add message delimiter
            framed_message = message + "\n###END_MESSAGE###\n"
            self.socket.send(framed_message.encode('utf-8'))
        except Exception as e:
            print(f"❌ Send error: {e}")
    
    def disconnect(self):
        self.running = False
        if self.socket:
            self.socket.close()
            print("🔌 Disconnected from Blender")

def main():
    print("🎬 Animation Library Manager")
    print("=" * 50)
    
    manager = AnimationLibraryManager()
    
    if not manager.connect():
        return
    
    # Interactive command loop
    print("\nAvailable commands:")
    print("  extract       - Extract current animation from Blender")
    print("  apply <num>   - Apply animation by number (use 'list' to see numbers)")
    print("  list [tags]   - List all animations (optional tag filter)")
    print("  search <term> - Search animations")
    print("  scene         - Get Blender scene info")
    print("  tags          - Show all available tags")
    print("  clear         - Clear screen")
    print("  quit/exit     - Disconnect and exit")
    print("\n💡 Extract an animation, then use 'apply 1' to test it on another armature!")
    print("-" * 50)
    
    try:
        while manager.running:
            try:
                command_input = input("\n> ").strip()
                
                if not command_input:
                    continue
                    
                parts = command_input.split()
                command = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                
                if command in ['quit', 'exit', 'q']:
                    break
                    
                elif command == 'apply':
                    if args:
                        try:
                            index = int(args[0])
                            animation = manager.get_animation_by_index(index)
                            if animation:
                                manager.apply_animation_by_id(animation['id'])
                            else:
                                print(f"❌ Animation #{index} not found. Use 'list' to see available animations.")
                        except ValueError:
                            print("Usage: apply <number> (use 'list' to see animation numbers)")
                    else:
                        print("Usage: apply <number> (use 'list' to see animation numbers)")
                        
                elif command == 'extract':
                    manager.send_command({'command': 'extract_animation'})
                    print("📤 Requesting animation extraction...")
                    
                elif command == 'scene':
                    manager.send_command({'command': 'get_scene_info'})
                    
                elif command == 'list':
                    filter_tags = args if args else None
                    manager.list_animations(filter_tags)
                    
                elif command == 'search':
                    if args:
                        query = ' '.join(args)
                        manager.search_animations(query)
                    else:
                        print("Usage: search <term>")
                        
                elif command == 'tags':
                    all_tags = set()
                    for anim in manager.animation_library.get("animations", []):
                        all_tags.update(anim.get('tags', []))
                    
                    if all_tags:
                        print(f"\n🏷️ Available Tags ({len(all_tags)}):")
                        for tag in sorted(all_tags):
                            count = sum(1 for anim in manager.animation_library.get("animations", [])
                                      if tag in anim.get('tags', []))
                            print(f"  {tag} ({count})")
                    else:
                        print("No tags found")
                        
                elif command == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    
                elif command == 'help':
                    print("\nCommands: extract, apply <num>, list, search, scene, tags, clear, quit")
                    
                else:
                    print(f"❓ Unknown command: {command}")
                    print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\n🛑 Interrupted by user")
                break
            except EOFError:
                print("\n🛑 Input closed")
                break
                
    finally:
        manager.disconnect()
        print("👋 Animation library session ended!")

if __name__ == "__main__":
    main()