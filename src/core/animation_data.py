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
                if '[' in channel_str and ']' in channel_str:
                    channel_name = channel_str.split('[')[0]
                    array_index = int(channel_str.split('[')[1].split(']')[0])
                    keyframe_count = bone_info.get('keyframe_count', 0)
                    frame_range = blender_data.get('frame_range', (1, 1))
                    
                    bone_anim.add_channel(channel_name, array_index, keyframe_count, frame_range)
            
            bone_data[bone_name] = bone_anim
        
        return cls(
            id=animation_id,
            name=blender_data['action_name'],
            description=f"Extracted from {blender_data['armature_name']}",
            armature_source=blender_data['armature_name'],
            frame_range=tuple(blender_data['frame_range']),
            total_bones_animated=blender_data['total_bones_animated'],
            total_keyframes=blender_data['total_keyframes'],
            bone_data=bone_data,
            rig_type="rigify" if "rigify" in blender_data['armature_name'].lower() else "unknown",
            tags=AnimationTagger.generate_tags(blender_data, bone_data),
            category="extracted"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
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
                    channel_name = channel_str.split('[')[0]
                    array_index = int(channel_str.split('[')[1].split(']')[0])
                    bone_anim.channels[channel_str] = ChannelData(
                        channel_name=channel_name,
                        array_index=array_index,
                        keyframe_count=bone_info.get('keyframe_count', 0),
                        frame_range=tuple(data['frame_range'])
                    )
            
            bone_data[bone_name] = bone_anim
        
        return cls(
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