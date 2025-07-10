"""
Animation data structures and utilities for the Animation Library system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
import json
from pathlib import Path


@dataclass
class ChannelData:
    """Represents animation data for a specific channel (e.g., location[0])"""
    channel_name: str
    array_index: int
    keyframe_count: int
    frame_range: Tuple[float, float]
    
    def __str__(self):
        return f"{self.channel_name}[{self.array_index}]"


@dataclass
class BoneAnimationData:
    """Represents animation data for a single bone"""
    bone_name: str
    channels: Dict[str, ChannelData] = field(default_factory=dict)
    total_keyframes: int = 0
    
    def add_channel(self, channel_name: str, array_index: int, keyframe_count: int, frame_range: Tuple[float, float]):
        """Add channel data to this bone"""
        channel_key = f"{channel_name}[{array_index}]"
        self.channels[channel_key] = ChannelData(
            channel_name=channel_name,
            array_index=array_index,
            keyframe_count=keyframe_count,
            frame_range=frame_range
        )
        self.total_keyframes += keyframe_count
    
    def has_channel_type(self, channel_type: str) -> bool:
        """Check if bone has specific channel type (location, rotation, scale)"""
        return any(channel_type in channel_name for channel_name in self.channels.keys())
    
    def get_channel_types(self) -> Set[str]:
        """Get all channel types for this bone"""
        types = set()
        for channel_key in self.channels.keys():
            if 'location' in channel_key:
                types.add('location')
            elif 'rotation' in channel_key:
                types.add('rotation')
            elif 'scale' in channel_key:
                types.add('scale')
        return types


@dataclass
class AnimationMetadata:
    """Complete animation metadata with all necessary information"""
    id: str
    name: str
    description: str
    armature_source: str
    frame_range: Tuple[float, float]
    total_bones_animated: int
    total_keyframes: int
    bone_data: Dict[str, BoneAnimationData] = field(default_factory=dict)
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    rig_type: str = "unknown"
    tags: List[str] = field(default_factory=list)
    category: str = "extracted"
    duration_frames: float = 0.0
    author: str = ""
    quality_rating: float = 0.0
    usage_count: int = 0
    
    def __post_init__(self):
        """Calculate derived values after initialization"""
        if self.duration_frames == 0.0:
            self.duration_frames = self.frame_range[1] - self.frame_range[0] + 1
    
    @classmethod
    def from_blender_data(cls, blender_data: Dict[str, Any]) -> 'AnimationMetadata':
        """Create AnimationMetadata from Blender extraction data"""
        animation_id = f"{blender_data['armature_name']}_{blender_data['action_name']}_{int(datetime.now().timestamp())}"
        animation_id = animation_id.replace("|", "_").replace(" ", "_")
        
        # Process bone data
        bone_data = {}
        for bone_name, bone_info in blender_data.get('bone_data', {}).items():
            bone_anim = BoneAnimationData(bone_name=bone_name)
            
            # Process channels
            for channel_str in bone_info.get('channels', []):
                # Parse channel string like "location[0]" or "rotation_quaternion[1]"
                # But be careful of bone names that might contain brackets
                if '[' in channel_str and ']' in channel_str:
                    # Find the LAST occurrence of '[' to get the array index
                    last_bracket = channel_str.rfind('[')
                    if last_bracket != -1:
                        channel_name = channel_str[:last_bracket]
                        array_index_str = channel_str[last_bracket+1:].rstrip(']')
                        
                        # Verify the array index is actually numeric
                        try:
                            array_index = int(array_index_str)
                            keyframe_count = bone_info.get('keyframe_count', 0)
                            frame_range = blender_data.get('frame_range', (1, 1))
                            
                            bone_anim.add_channel(channel_name, array_index, keyframe_count, frame_range)
                        except ValueError:
                            # If it's not numeric, treat the whole thing as the channel name
                            print(f"Warning: Non-numeric array index in channel '{channel_str}', treating as channel name")
                            bone_anim.add_channel(channel_str, 0, bone_info.get('keyframe_count', 0), blender_data.get('frame_range', (1, 1)))
                else:
                    # No brackets, treat as simple channel name
                    bone_anim.add_channel(channel_str, 0, bone_info.get('keyframe_count', 0), blender_data.get('frame_range', (1, 1)))
            
            bone_data[bone_name] = bone_anim
        
        # Create metadata and preserve the original blender_data for F-curve info
        metadata = cls(
            id=animation_id,
            name=blender_data['action_name'],
            description=f"Extracted from {blender_data['armature_name']}",
            armature_source=blender_data['armature_name'],
            frame_range=tuple(blender_data['frame_range']),
            total_bones_animated=blender_data['total_bones_animated'],
            total_keyframes=blender_data['total_keyframes'],
            bone_data=bone_data,
            rig_type=RigTypeDetector.detect_rig_type(
                blender_data['armature_name'], 
                list(blender_data.get('bone_data', {}).keys())
            ),
            tags=AnimationTagger.generate_tags(blender_data, bone_data),
            category="extracted"
        )
        
        # Store the original blender data for F-curve reconstruction
        metadata._original_blender_data = blender_data
        
        return metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "armature_source": self.armature_source,
            "frame_range": list(self.frame_range),
            "total_bones_animated": self.total_bones_animated,
            "total_keyframes": self.total_keyframes,
            "bone_data": {
                bone_name: {
                    "channels": list(bone_data.channels.keys()),
                    "keyframe_count": bone_data.total_keyframes
                }
                for bone_name, bone_data in self.bone_data.items()
            },
            "created_date": self.created_date,
            "rig_type": self.rig_type,
            "tags": self.tags,
            "category": self.category,
            "duration_frames": self.duration_frames,
            "author": self.author,
            "quality_rating": self.quality_rating,
            "usage_count": self.usage_count
        }
        
        # Preserve original blender data with F-curve info if available
        if hasattr(self, '_original_blender_data'):
            result['_original_blender_data'] = self._original_blender_data
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnimationMetadata':
        """Create from dictionary (JSON deserialization)"""
        # Reconstruct bone data
        bone_data = {}
        for bone_name, bone_info in data.get('bone_data', {}).items():
            bone_anim = BoneAnimationData(bone_name=bone_name)
            bone_anim.total_keyframes = bone_info.get('keyframe_count', 0)
            
            # Reconstruct channels
            for channel_str in bone_info.get('channels', []):
                if '[' in channel_str and ']' in channel_str:
                    # Find the LAST occurrence of '[' to get the array index
                    last_bracket = channel_str.rfind('[')
                    if last_bracket != -1:
                        channel_name = channel_str[:last_bracket]
                        array_index_str = channel_str[last_bracket+1:].rstrip(']')
                        
                        # Verify the array index is actually numeric
                        try:
                            array_index = int(array_index_str)
                            bone_anim.channels[channel_str] = ChannelData(
                                channel_name=channel_name,
                                array_index=array_index,
                                keyframe_count=bone_info.get('keyframe_count', 0),
                                frame_range=tuple(data['frame_range'])
                            )
                        except ValueError:
                            # If it's not numeric, treat the whole thing as the channel name
                            bone_anim.channels[channel_str] = ChannelData(
                                channel_name=channel_str,
                                array_index=0,
                                keyframe_count=bone_info.get('keyframe_count', 0),
                                frame_range=tuple(data['frame_range'])
                            )
                else:
                    # No brackets, treat as simple channel name
                    bone_anim.channels[channel_str] = ChannelData(
                        channel_name=channel_str,
                        array_index=0,
                        keyframe_count=bone_info.get('keyframe_count', 0),
                        frame_range=tuple(data['frame_range'])
                    )
            
            bone_data[bone_name] = bone_anim
        
        metadata = cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            armature_source=data['armature_source'],
            frame_range=tuple(data['frame_range']),
            total_bones_animated=data['total_bones_animated'],
            total_keyframes=data['total_keyframes'],
            bone_data=bone_data,
            created_date=data.get('created_date', datetime.now().isoformat()),
            rig_type=data.get('rig_type', 'unknown'),
            tags=data.get('tags', []),
            category=data.get('category', 'extracted'),
            duration_frames=data.get('duration_frames', 0.0),
            author=data.get('author', ''),
            quality_rating=data.get('quality_rating', 0.0),
            usage_count=data.get('usage_count', 0)
        )
        
        # Restore original blender data if available
        if '_original_blender_data' in data:
            metadata._original_blender_data = data['_original_blender_data']
        
        return metadata


class RigTypeDetector:
    """Utility class for detecting rig types"""
    
    @classmethod
    def detect_rig_type(cls, armature_name: str, bone_names: List[str]) -> str:
        """Detect rig type from armature name and bone patterns"""
        armature_lower = armature_name.lower()
        bone_str = " ".join(bone_names).lower()
        
        # Check armature name first (most reliable)
        if "rigify" in armature_lower:
            return "Rigify"
        elif "autorig" in armature_lower or "auto_rig" in armature_lower or "auto-rig" in armature_lower:
            return "Auto-Rig Pro"
        elif "mixamo" in armature_lower:
            return "Mixamo"
        
        # Check bone patterns as backup
        rigify_indicators = sum(1 for bone in bone_names 
                               if any(pattern in bone.lower() for pattern in ["_fk.", "_ik.", "mch-", "def-", "org-"]))
        
        mixamo_indicators = sum(1 for bone in bone_names if "mixamorig:" in bone.lower())
        
        autorig_indicators = sum(1 for bone in bone_names 
                                if any(pattern in bone.lower() for pattern in ["c_spine", "c_root", "_fk_", "_ik_"]))
        
        # Determine rig type based on indicators
        if mixamo_indicators > 0:
            return "Mixamo"
        elif rigify_indicators >= 3:  # Need several Rigify bones to be confident
            return "Rigify"
        elif autorig_indicators >= 2:  # Need some Auto-Rig Pro patterns
            return "Auto-Rig Pro"
        
        return "Unknown"
    
    @classmethod
    def are_rigs_compatible(cls, rig_type1: str, rig_type2: str) -> bool:
        """Check if two rig types are compatible"""
        if rig_type1 == "Unknown" or rig_type2 == "Unknown":
            return True  # Allow unknown rigs to be applied (user decides)
        return rig_type1 == rig_type2
    
    @classmethod
    def get_rig_color(cls, rig_type: str) -> str:
        """Get color indicator for rig type"""
        colors = {
            "Rigify": "#51cf66",      # Green
            "Auto-Rig Pro": "#339af0", # Blue
            "Mixamo": "#ffd43b",      # Yellow
            "Unknown": "#868e96"      # Gray
        }
        return colors.get(rig_type, "#868e96")
    
    @classmethod
    def get_rig_emoji(cls, rig_type: str) -> str:
        """Get emoji indicator for rig type"""
        emojis = {
            "Rigify": "🟢",
            "Auto-Rig Pro": "🔵", 
            "Mixamo": "🟡",
            "Unknown": "⚪"
        }
        return emojis.get(rig_type, "⚪")


class AnimationTagger:
    """Utility class for automatically generating animation tags"""
    
    # Bone name patterns for different animation types
    LOCOMOTION_BONES = {
        'thigh_fk.L', 'thigh_fk.R', 'shin_fk.L', 'shin_fk.R', 
        'foot_fk.L', 'foot_fk.R', 'thigh_ik.L', 'thigh_ik.R',
        'foot_ik.L', 'foot_ik.R', 'toe_fk.L', 'toe_fk.R'
    }
    
    UPPER_BODY_BONES = {
        'upper_arm_fk.L', 'upper_arm_fk.R', 'forearm_fk.L', 'forearm_fk.R',
        'hand_fk.L', 'hand_fk.R', 'upper_arm_ik.L', 'upper_arm_ik.R',
        'shoulder.L', 'shoulder.R'
    }
    
    FACIAL_KEYWORDS = {'jaw', 'eyes', 'brow', 'lip', 'cheek', 'nose', 'ear', 'tongue', 'teeth'}
    FINGER_KEYWORDS = {'thumb', 'f_index', 'f_middle', 'f_ring', 'f_pinky'}
    SPINE_KEYWORDS = {'spine', 'torso', 'chest', 'neck', 'head'}
    
    @classmethod
    def generate_tags(cls, blender_data: Dict[str, Any], bone_data: Dict[str, BoneAnimationData]) -> List[str]:
        """Generate automatic tags based on animation data"""
        tags = []
        animated_bones = set(bone_data.keys())
        
        # Animation type detection
        if animated_bones & cls.LOCOMOTION_BONES:
            tags.append("locomotion")
        
        if animated_bones & cls.UPPER_BODY_BONES:
            tags.append("upper_body")
        
        # Keyword-based detection
        bone_str = ' '.join(animated_bones).lower()
        
        if any(keyword in bone_str for keyword in cls.FACIAL_KEYWORDS):
            tags.append("facial")
        
        if any(keyword in bone_str for keyword in cls.FINGER_KEYWORDS):
            tags.append("hands")
        
        if any(keyword in bone_str for keyword in cls.SPINE_KEYWORDS):
            tags.append("spine")
        
        # Duration-based tags
        duration = blender_data.get('frame_range', [1, 1])[1] - blender_data.get('frame_range', [1, 1])[0] + 1
        if duration < 10:
            tags.append("short")
        elif duration > 100:
            tags.append("long")
        else:
            tags.append("medium")
        
        # Complexity-based tags
        keyframe_density = blender_data.get('total_keyframes', 0) / max(duration, 1)
        if keyframe_density > 20:
            tags.append("dense")
        elif keyframe_density < 5:
            tags.append("sparse")
        else:
            tags.append("moderate")
        
        # Animation type inference
        if any(bone_data[bone].has_channel_type('location') for bone in animated_bones):
            tags.append("translation")
        
        if any(bone_data[bone].has_channel_type('rotation') for bone in animated_bones):
            tags.append("rotation")
        
        if any(bone_data[bone].has_channel_type('scale') for bone in animated_bones):
            tags.append("scale")
        
        return tags if tags else ["uncategorized"]


@dataclass
class ApplyOptions:
    """Options for applying animations"""
    selected_bones_only: bool = True
    frame_offset: int = 1
    channels: Dict[str, bool] = field(default_factory=lambda: {
        'location': True,
        'rotation': True,
        'scale': True
    })
    bone_mapping: Dict[str, str] = field(default_factory=dict)
    overwrite_existing: bool = True
    
    def should_apply_channel(self, channel_name: str) -> bool:
        """Check if a specific channel should be applied"""
        for channel_type, enabled in self.channels.items():
            if channel_type in channel_name.lower() and enabled:
                return True
        return False