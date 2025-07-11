"""
Animation data structures and utilities for the Animation Library system.
FIXED VERSION: src/core/animation_data.py

Enhanced with .blend file storage support for instant animation application.
All duplicate methods removed, type hints improved, and validation added.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from datetime import datetime
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChannelData:
    """Represents animation data for a specific channel         auto_rig_patterns = ["c_spine", "c_root", "_fk_", "_ik_"]
        auto_rig_indicators = sum(
            1 for bone in bone_names 
            if any(pattern in str(bone).lower() for pattern in auto_rig_patterns)
        ).g., location[0])"""
    channel_name: str
    array_index: int
    keyframe_count: int
    frame_range: Tuple[float, float]
    
    def __post_init__(self):
        """Validate channel data after initialization"""
        if self.keyframe_count < 0:
            raise ValueError(f"Keyframe count cannot be negative: {self.keyframe_count}")
        if self.frame_range[0] > self.frame_range[1]:
            raise ValueError(f"Invalid frame range: {self.frame_range}")
    
    def __str__(self) -> str:
        return f"{self.channel_name}[{self.array_index}]"


@dataclass
class BoneAnimationData:
    """Represents animation data for a single bone"""
    bone_name: str
    channels: Dict[str, ChannelData] = field(default_factory=dict)
    total_keyframes: int = 0
    
    def __post_init__(self):
        """Validate bone data after initialization"""
        if not self.bone_name.strip():
            raise ValueError("Bone name cannot be empty")
        if self.total_keyframes < 0:
            raise ValueError(f"Total keyframes cannot be negative: {self.total_keyframes}")
    
    def add_channel(
        self, channel_name: str, array_index: int, 
        keyframe_count: int, frame_range: Tuple[float, float]
    ) -> None:
        """Add channel data to this bone with validation"""
        if not channel_name.strip():
            raise ValueError("Channel name cannot be empty")
        if keyframe_count < 0:
            raise ValueError(f"Keyframe count cannot be negative: {keyframe_count}")
        
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
        if not channel_type:
            return False
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
class BlendFileReference:
    """Reference to .blend file containing animation data"""
    blend_file: str  # Filename of .blend file
    blend_action_name: str  # Original action name in .blend file
    file_size_mb: float = 0.0
    creation_date: str = field(default_factory=lambda: datetime.now().isoformat())
    file_path: Optional[Path] = None  # Full path to .blend file
    
    def __post_init__(self):
        """Validate blend file reference after initialization"""
        if not self.blend_file.strip():
            raise ValueError("Blend file name cannot be empty")
        if not self.blend_action_name.strip():
            raise ValueError("Blend action name cannot be empty")
        if self.file_size_mb < 0:
            raise ValueError(f"File size cannot be negative: {self.file_size_mb}")
    
    def exists(self) -> bool:
        """Check if .blend file exists"""
        return bool(self.file_path and self.file_path.exists())
    
    def get_size_mb(self) -> float:
        """Get current file size in MB"""
        if self.file_path and self.file_path.exists():
            try:
                return self.file_path.stat().st_size / (1024 * 1024)
            except OSError as e:
                logger.warning(f"Failed to get file size for {self.file_path}: {e}")
                return self.file_size_mb
        return self.file_size_mb


@dataclass
class AnimationMetadata:
    """Complete animation metadata with .blend file storage support and folder organization"""
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
    
    # Folder organization
    folder_path: str = "Root"  # Folder path in library structure
    
    # Thumbnail support
    thumbnail: str = ""  # Relative path to thumbnail image
    
    # Storage method and .blend file support
    storage_method: str = "blend_file"  # "blend_file" or "json_keyframes"
    blend_reference: Optional[BlendFileReference] = None
    extraction_time_seconds: float = 1.5  # Time to extract
    application_time_seconds: float = 0.5  # Time to apply
    
    def __post_init__(self):
        """Validate and calculate derived values after initialization"""
        # Validation
        if not self.id.strip():
            raise ValueError("Animation ID cannot be empty")
        if not self.name.strip():
            raise ValueError("Animation name cannot be empty")
        if not self.armature_source.strip():
            raise ValueError("Armature source cannot be empty")
        if self.frame_range[0] > self.frame_range[1]:
            raise ValueError(f"Invalid frame range: {self.frame_range}")
        if self.total_bones_animated < 0:
            raise ValueError(f"Total bones animated cannot be negative: {self.total_bones_animated}")
        if self.total_keyframes < 0:
            raise ValueError(f"Total keyframes cannot be negative: {self.total_keyframes}")
        if self.quality_rating < 0 or self.quality_rating > 5:
            raise ValueError(f"Quality rating must be between 0 and 5: {self.quality_rating}")
        if self.usage_count < 0:
            raise ValueError(f"Usage count cannot be negative: {self.usage_count}")
        if self.extraction_time_seconds < 0:
            raise ValueError(f"Extraction time cannot be negative: {self.extraction_time_seconds}")
        if self.application_time_seconds < 0:
            raise ValueError(f"Application time cannot be negative: {self.application_time_seconds}")
        
        # Calculate derived values
        if self.duration_frames == 0.0:
            self.duration_frames = self.frame_range[1] - self.frame_range[0] + 1
        
        # Validate storage method consistency
        if self.storage_method == "blend_file" and not self.blend_reference:
            logger.warning(f"Animation {self.id} uses blend_file storage but has no blend_reference")
    
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
            "tags": self.tags.copy(),  # Create copy to prevent modification
            "category": self.category,
            "duration_frames": self.duration_frames,
            "author": self.author,
            "quality_rating": self.quality_rating,
            "usage_count": self.usage_count,
            "folder_path": self.folder_path,
            "thumbnail": self.thumbnail,
            "storage_method": self.storage_method,
            "extraction_time_seconds": self.extraction_time_seconds,
            "application_time_seconds": self.application_time_seconds
        }
        
        # Add .blend file reference if using new storage
        if self.blend_reference:
            result.update({
                "blend_file": self.blend_reference.blend_file,
                "blend_action_name": self.blend_reference.blend_action_name,
                "file_size_mb": self.blend_reference.file_size_mb
            })
        
        # Preserve original blender data for legacy animations
        if hasattr(self, '_original_blender_data'):
            result['_original_blender_data'] = self._original_blender_data
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnimationMetadata':
        """Create from dictionary (JSON deserialization) with validation"""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        
        # Validate required fields
        required_fields = ['id', 'name', 'armature_source', 'frame_range', 'total_bones_animated', 'total_keyframes']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Reconstruct bone data with validation
        bone_data = {}
        for bone_name, bone_info in data.get('bone_data', {}).items():
            if not isinstance(bone_info, dict):
                logger.warning(f"Invalid bone data for {bone_name}, skipping")
                continue
                
            bone_anim = BoneAnimationData(bone_name=bone_name)
            bone_anim.total_keyframes = bone_info.get('keyframe_count', 0)
            
            for channel_str in bone_info.get('channels', []):
                try:
                    if '[' in channel_str and ']' in channel_str:
                        last_bracket = channel_str.rfind('[')
                        if last_bracket != -1:
                            channel_name = channel_str[:last_bracket]
                            array_index_str = channel_str[last_bracket+1:].rstrip(']')
                            
                            try:
                                array_index = int(array_index_str)
                                bone_anim.channels[channel_str] = ChannelData(
                                    channel_name=channel_name,
                                    array_index=array_index,
                                    keyframe_count=bone_info.get('keyframe_count', 0),
                                    frame_range=tuple(data['frame_range'])
                                )
                            except ValueError:
                                bone_anim.channels[channel_str] = ChannelData(
                                    channel_name=channel_str,
                                    array_index=0,
                                    keyframe_count=bone_info.get('keyframe_count', 0),
                                    frame_range=tuple(data['frame_range'])
                                )
                    else:
                        bone_anim.channels[channel_str] = ChannelData(
                            channel_name=channel_str,
                            array_index=0,
                            keyframe_count=bone_info.get('keyframe_count', 0),
                            frame_range=tuple(data['frame_range'])
                        )
                except Exception as e:
                    logger.warning(f"Failed to create channel {channel_str} for bone {bone_name}: {e}")
                    continue
            
            bone_data[bone_name] = bone_anim
        
        # Create .blend file reference if present
        blend_reference = None
        if data.get('storage_method') == 'blend_file' and 'blend_file' in data:
            try:
                blend_reference = BlendFileReference(
                    blend_file=data['blend_file'],
                    blend_action_name=data['blend_action_name'],
                    file_size_mb=data.get('file_size_mb', 0.0),
                    creation_date=data.get('created_date', datetime.now().isoformat())
                )
            except Exception as e:
                logger.warning(f"Failed to create blend reference: {e}")
                blend_reference = None
        
        # Create metadata instance with defaults for missing fields
        try:
            metadata = cls(
                id=data['id'],
                name=data['name'],
                description=data.get('description', ''),
                armature_source=data['armature_source'],
                frame_range=tuple(data['frame_range']),
                total_bones_animated=data['total_bones_animated'],
                total_keyframes=data['total_keyframes'],
                bone_data=bone_data,
                created_date=data.get('created_date', datetime.now().isoformat()),
                rig_type=data.get('rig_type', 'unknown'),
                tags=data.get('tags', []).copy() if data.get('tags') else [],
                category=data.get('category', 'extracted'),
                duration_frames=data.get('duration_frames', 0.0),
                author=data.get('author', ''),
                quality_rating=max(0, min(5, data.get('quality_rating', 0.0))),  # Clamp to valid range
                usage_count=max(0, data.get('usage_count', 0)),  # Ensure non-negative
                folder_path=data.get('folder_path', 'Root'),
                thumbnail=data.get('thumbnail', ''),
                storage_method=data.get('storage_method', 'json_keyframes'),
                blend_reference=blend_reference,
                extraction_time_seconds=max(0, data.get('extraction_time_seconds', 30.0)),
                application_time_seconds=max(0, data.get('application_time_seconds', 30.0))
            )
        except Exception as e:
            logger.error(f"Failed to create AnimationMetadata from data: {e}")
            raise ValueError(f"Invalid animation data: {e}")
        
        # Restore original blender data if available (legacy support)
        if '_original_blender_data' in data:
            metadata._original_blender_data = data['_original_blender_data']
        
        return metadata
    
    @classmethod
    def from_blender_data(cls, animation_data: Dict[str, Any], thumbnail_path: str = "") -> 'AnimationMetadata':
        """
        Create AnimationMetadata instance from Blender animation data.
        
        Args:
            animation_data: Dictionary containing animation data from Blender extraction
            thumbnail_path: Relative path to thumbnail image
            
        Returns:
            AnimationMetadata: New instance with mapped fields from animation_data
            
        Raises:
            ValueError: If animation_data is invalid or missing required fields
        """
        if not isinstance(animation_data, dict):
            raise ValueError("Animation data must be a dictionary")
        
        # Extract and validate basic information
        animation_id = animation_data.get('animation_id', animation_data.get('id', ''))
        if not animation_id:
            # Generate ID if missing
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            animation_id = f"animation_{timestamp}"
        
        name = animation_data.get('action_name', animation_data.get('name', 'Unknown Animation'))
        armature_name = animation_data.get('armature_name', 'Unknown Armature')
        
        # Frame range and duration with validation
        frame_range_data = animation_data.get('frame_range', [1, 1])
        if not isinstance(frame_range_data, (list, tuple)) or len(frame_range_data) != 2:
            logger.warning(f"Invalid frame range {frame_range_data}, using default [1, 1]")
            frame_range_data = [1, 1]
        
        frame_range = tuple(frame_range_data)
        duration_frames = float(animation_data.get('duration_frames', frame_range[1] - frame_range[0] + 1))
        
        # Bone and keyframe data with validation
        total_bones_animated = max(0, animation_data.get('total_bones_animated', 0))
        total_keyframes = max(0, animation_data.get('total_keyframes', 0))
        animated_bones = animation_data.get('animated_bones', [])
        
        # Create bone data structure
        bone_data = {}
        if 'bone_data' in animation_data and isinstance(animation_data['bone_data'], dict):
            # If detailed bone data is provided
            for bone_name, bone_info in animation_data['bone_data'].items():
                try:
                    bone_anim = BoneAnimationData(bone_name=bone_name)
                    bone_anim.total_keyframes = bone_info.get('keyframe_count', 0)
                    
                    # Map channels if available
                    for channel_str in bone_info.get('channels', []):
                        try:
                            if '[' in channel_str and ']' in channel_str:
                                last_bracket = channel_str.rfind('[')
                                if last_bracket != -1:
                                    channel_name = channel_str[:last_bracket]
                                    array_index_str = channel_str[last_bracket+1:].rstrip(']')
                                    
                                    try:
                                        array_index = int(array_index_str)
                                        bone_anim.channels[channel_str] = ChannelData(
                                            channel_name=channel_name,
                                            array_index=array_index,
                                            keyframe_count=bone_info.get('keyframe_count', 0),
                                            frame_range=frame_range
                                        )
                                    except ValueError:
                                        bone_anim.channels[channel_str] = ChannelData(
                                            channel_name=channel_str,
                                            array_index=0,
                                            keyframe_count=bone_info.get('keyframe_count', 0),
                                            frame_range=frame_range
                                        )
                            else:
                                bone_anim.channels[channel_str] = ChannelData(
                                    channel_name=channel_str,
                                    array_index=0,
                                    keyframe_count=bone_info.get('keyframe_count', 0),
                                    frame_range=frame_range
                                )
                        except Exception as e:
                            logger.warning(f"Failed to create channel {channel_str} for bone {bone_name}: {e}")
                            continue
                    
                    bone_data[bone_name] = bone_anim
                except Exception as e:
                    logger.warning(f"Failed to create bone data for {bone_name}: {e}")
                    continue
        else:
            # Create simplified bone data from animated_bones list
            if animated_bones and isinstance(animated_bones, list):
                keyframes_per_bone = max(1, total_keyframes // max(1, len(animated_bones)))
                for bone_name in animated_bones:
                    if not isinstance(bone_name, str) or not bone_name.strip():
                        continue
                        
                    try:
                        bone_anim = BoneAnimationData(bone_name=bone_name)
                        bone_anim.total_keyframes = keyframes_per_bone
                        # Add basic transform channels
                        for transform_type in ['location', 'rotation_euler', 'scale']:
                            for i in range(3):
                                channel_key = f"{transform_type}[{i}]"
                                bone_anim.channels[channel_key] = ChannelData(
                                    channel_name=transform_type,
                                    array_index=i,
                                    keyframe_count=keyframes_per_bone // 3,
                                    frame_range=frame_range
                                )
                        bone_data[bone_name] = bone_anim
                    except Exception as e:
                        logger.warning(f"Failed to create simplified bone data for {bone_name}: {e}")
                        continue
        
        # Detect rig type
        rig_type = RigTypeDetector.detect_rig_type(armature_name, animated_bones)
        
        # Create .blend file reference if blend file data is present
        blend_reference = None
        if animation_data.get('storage_method') == 'blend_file' and 'blend_file' in animation_data:
            try:
                blend_reference = BlendFileReference(
                    blend_file=animation_data['blend_file'],
                    blend_action_name=animation_data.get('blend_action_name', name),
                    file_size_mb=max(0, animation_data.get('file_size_mb', 0.0)),
                    creation_date=animation_data.get('created_date', datetime.now().isoformat())
                )
            except Exception as e:
                logger.warning(f"Failed to create blend reference: {e}")
                blend_reference = None
        
        # Generate automatic tags
        tags = AnimationTagger.generate_tags(animation_data, bone_data)
        
        # Create the metadata instance
        try:
            metadata = cls(
                id=animation_id,
                name=name,
                description=animation_data.get('description', f"Animation extracted from {armature_name}"),
                armature_source=armature_name,
                frame_range=frame_range,
                total_bones_animated=total_bones_animated,
                total_keyframes=total_keyframes,
                bone_data=bone_data,
                created_date=animation_data.get('created_date', datetime.now().isoformat()),
                rig_type=rig_type,
                tags=tags,
                category=animation_data.get('category', 'extracted'),
                duration_frames=duration_frames,
                author=animation_data.get('author', ''),
                quality_rating=max(0, min(5, animation_data.get('quality_rating', 0.0))),
                usage_count=max(0, animation_data.get('usage_count', 0)),
                folder_path=animation_data.get('folder_path', 'Root'),
                thumbnail=thumbnail_path,
                storage_method=animation_data.get('storage_method', 'blend_file'),
                blend_reference=blend_reference,
                extraction_time_seconds=max(0, animation_data.get('extraction_time_seconds', 1.5)),
                application_time_seconds=max(0, animation_data.get('application_time_seconds', 0.5))
            )
        except Exception as e:
            logger.error(f"Failed to create AnimationMetadata from Blender data: {e}")
            raise ValueError(f"Invalid Blender animation data: {e}")
        
        # Store original blender data for reference if needed
        metadata._original_blender_data = animation_data
        
        return metadata
    
    def is_blend_file_storage(self) -> bool:
        """Check if animation uses .blend file storage"""
        return self.storage_method == 'blend_file' and self.blend_reference is not None
    
    def is_legacy_storage(self) -> bool:
        """Check if animation uses legacy JSON storage"""
        return self.storage_method == 'json_keyframes' or hasattr(self, '_original_blender_data')
    
    def get_performance_info(self) -> Dict[str, str]:
        """Get performance information for UI display"""
        if self.is_blend_file_storage():
            file_size = (f"{self.blend_reference.file_size_mb:.1f}MB" 
                        if self.blend_reference else "Unknown")
            return {
                'extraction_time': f"~{self.extraction_time_seconds:.1f}s",
                'application_time': f"~{self.application_time_seconds:.1f}s",
                'performance_level': 'instant',
                'storage_efficiency': file_size,
                'status_emoji': '⚡',
                'status_text': 'Instant'
            }
        else:
            return {
                'extraction_time': f"~{self.extraction_time_seconds:.0f}s",
                'application_time': f"~{self.application_time_seconds:.0f}s",
                'performance_level': 'slow',
                'storage_efficiency': 'Legacy JSON',
                'status_emoji': '⏳',
                'status_text': 'Legacy (Slow)'
            }
    
    def update_blend_file_path(self, library_path: Path) -> None:
        """Update the full path to .blend file"""
        if self.blend_reference:
            self.blend_reference.file_path = library_path / 'actions' / self.blend_reference.blend_file
    
    def increment_usage(self) -> None:
        """Increment usage count safely"""
        self.usage_count = max(0, self.usage_count + 1)
    
    def set_quality_rating(self, rating: float) -> None:
        """Set quality rating with validation"""
        if not isinstance(rating, (int, float)):
            raise ValueError("Quality rating must be a number")
        self.quality_rating = max(0.0, min(5.0, float(rating)))
    
    def add_tag(self, tag: str) -> None:
        """Add a tag if it doesn't already exist"""
        if isinstance(tag, str) and tag.strip() and tag not in self.tags:
            self.tags.append(tag.strip())
    
    def remove_tag(self, tag: str) -> bool:
        """Remove a tag if it exists, returns True if removed"""
        try:
            self.tags.remove(tag)
            return True
        except ValueError:
            return False


class RigTypeDetector:
    """Utility class for detecting rig types"""
    
    @classmethod
    def detect_rig_type(cls, armature_name: str, bone_names: List[str]) -> str:
        """
        Detect rig type from armature name and bone patterns
        
        Args:
            armature_name: Name of the armature
            bone_names: List of bone names in the armature
            
        Returns:
            str: Detected rig type
        """
        if not isinstance(armature_name, str) or not isinstance(bone_names, list):
            logger.warning("Invalid input types for rig detection")
            return "Unknown"
        
        armature_lower = armature_name.lower()
        bone_str = " ".join(str(bone) for bone in bone_names).lower()
        
        # Check armature name first (most reliable)
        if "rigify" in armature_lower:
            return "Rigify"
        elif any(keyword in armature_lower for keyword in ["autorig", "auto_rig", "auto-rig"]):
            return "Auto-Rig Pro"
        elif "mixamo" in armature_lower:
            return "Mixamo"
        
        # Check bone patterns as backup
        rigify_patterns = ["_fk.", "_ik.", "mch-", "def-", "org-"]
        rigify_indicators = sum(
            1 for bone in bone_names 
            if any(pattern in str(bone).lower() for pattern in rigify_patterns)
        )
        
        mixamo_indicators = sum(1 for bone in bone_names if "mixamorig:" in str(bone).lower())
        
        autorig_indicators = sum(1 for bone in bone_names 
                                if any(pattern in str(bone).lower() for pattern in ["c_spine", "c_root", "_fk_", "_ik_"]))
        
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
        if not isinstance(rig_type1, str) or not isinstance(rig_type2, str):
            return False
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
        """
        Generate automatic tags based on animation data
        
        Args:
            blender_data: Raw data from Blender
            bone_data: Processed bone animation data
            
        Returns:
            List[str]: Generated tags
        """
        if not isinstance(blender_data, dict) or not isinstance(bone_data, dict):
            logger.warning("Invalid input types for tag generation")
            return ["uncategorized"]
        
        tags = []
        animated_bones = set(bone_data.keys())
        
        # Add storage method tag
        storage_method = blender_data.get('storage_method', 'json_keyframes')
        if storage_method == 'blend_file':
            tags.append('instant')
        else:
            tags.append('legacy')
        
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
        frame_range = blender_data.get('frame_range', [1, 1])
        if isinstance(frame_range, (list, tuple)) and len(frame_range) >= 2:
            try:
                duration = frame_range[1] - frame_range[0] + 1
                if duration < 10:
                    tags.append("short")
                elif duration > 100:
                    tags.append("long")
                else:
                    tags.append("medium")
            except (TypeError, ValueError):
                tags.append("unknown_duration")
        
        # Complexity-based tags
        total_keyframes = blender_data.get('total_keyframes', 0)
        if isinstance(total_keyframes, (int, float)) and total_keyframes > 0:
            try:
                duration = max(1, frame_range[1] - frame_range[0] + 1) if isinstance(frame_range, (list, tuple)) else 1
                keyframe_density = total_keyframes / duration
                if keyframe_density > 20:
                    tags.append("dense")
                elif keyframe_density < 5:
                    tags.append("sparse")
                else:
                    tags.append("moderate")
            except (TypeError, ValueError, ZeroDivisionError):
                tags.append("unknown_complexity")
        
        # Performance tags
        if storage_method == 'blend_file':
            tags.append("fast")
            tags.append("production")
        
        return tags if tags else ["uncategorized"]


@dataclass
class ApplyOptions:
    """Options for applying animations with .blend file support"""
    selected_bones_only: bool = False
    frame_offset: int = 1
    channels: Dict[str, bool] = field(default_factory=lambda: {
        'location': True,
        'rotation': True,
        'scale': True
    })
    bone_mapping: Dict[str, str] = field(default_factory=dict)
    overwrite_existing: bool = True
    
    # Performance preferences
    prefer_blend_files: bool = True  # Prefer .blend over JSON when available
    force_migration: bool = False    # Force migrate JSON to .blend during apply
    
    def __post_init__(self):
        """Validate apply options after initialization"""
        if self.frame_offset < 1:
            raise ValueError(f"Frame offset must be >= 1: {self.frame_offset}")
        
        # Validate channels dictionary
        if not isinstance(self.channels, dict):
            self.channels = {'location': True, 'rotation': True, 'scale': True}
        
        # Ensure all channel values are boolean
        for key, value in self.channels.items():
            if not isinstance(value, bool):
                self.channels[key] = bool(value)
        
        # Validate bone mapping
        if not isinstance(self.bone_mapping, dict):
            self.bone_mapping = {}
        
        # Clean bone mapping - ensure all keys and values are strings
        cleaned_mapping = {}
        for source, target in self.bone_mapping.items():
            if isinstance(source, str) and isinstance(target, str):
                cleaned_mapping[source] = target
        self.bone_mapping = cleaned_mapping
    
    def should_apply_channel(self, channel_name: str) -> bool:
        """Check if a specific channel should be applied"""
        if not isinstance(channel_name, str):
            return False
            
        for channel_type, enabled in self.channels.items():
            if channel_type in channel_name.lower() and enabled:
                return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for communication"""
        return {
            'selected_bones_only': self.selected_bones_only,
            'frame_offset': self.frame_offset,
            'channels': self.channels.copy(),
            'bone_mapping': self.bone_mapping.copy(),
            'overwrite_existing': self.overwrite_existing,
            'prefer_blend_files': self.prefer_blend_files,
            'force_migration': self.force_migration
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplyOptions':
        """Create from dictionary with validation"""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        
        # Use defaults for missing values
        return cls(
            selected_bones_only=bool(data.get('selected_bones_only', False)),
            frame_offset=max(1, int(data.get('frame_offset', 1))),
            channels=data.get('channels', {'location': True, 'rotation': True, 'scale': True}),
            bone_mapping=data.get('bone_mapping', {}),
            overwrite_existing=bool(data.get('overwrite_existing', True)),
            prefer_blend_files=bool(data.get('prefer_blend_files', True)),
            force_migration=bool(data.get('force_migration', False))
        )


class AnimationStorageDetector:
    """Utility for detecting and managing storage methods"""
    
    @staticmethod
    def detect_storage_method(animation_data: Dict[str, Any]) -> str:
        """
        Detect storage method from animation data
        
        Args:
            animation_data: Animation data dictionary
            
        Returns:
            str: Detected storage method
        """
        if not isinstance(animation_data, dict):
            return 'unknown'
        
        if 'storage_method' in animation_data:
            method = animation_data['storage_method']
            if method in ['blend_file', 'json_keyframes']:
                return method
        
        if 'blend_file' in animation_data:
            return 'blend_file'
        elif '_original_blender_data' in animation_data:
            return 'json_keyframes'
        else:
            return 'unknown'
    
    @staticmethod
    def needs_migration(animation_metadata: AnimationMetadata) -> bool:
        """Check if animation needs migration to .blend file"""
        if not isinstance(animation_metadata, AnimationMetadata):
            return False
        
        return (animation_metadata.storage_method == 'json_keyframes' or 
                hasattr(animation_metadata, '_original_blender_data'))
    
    @staticmethod
    def get_performance_estimate(animation_metadata: AnimationMetadata) -> Dict[str, float]:
        """
        Get performance estimates based on storage method
        
        Args:
            animation_metadata: Animation metadata to analyze
            
        Returns:
            Dict containing performance estimates
        """
        if not isinstance(animation_metadata, AnimationMetadata):
            return {
                'extraction_time': 30.0,
                'application_time': 30.0,
                'performance_multiplier': 0.01
            }
        
        if animation_metadata.is_blend_file_storage():
            return {
                'extraction_time': 1.5,
                'application_time': 0.5,
                'performance_multiplier': 1.0
            }
        else:
            duration = max(1, animation_metadata.duration_frames)
            return {
                'extraction_time': min(60, max(10, duration * 0.2)),
                'application_time': min(120, max(15, duration * 0.3)),
                'performance_multiplier': 0.01  # 1% of .blend file performance
            }


# Validation utilities
def validate_animation_id(animation_id: str) -> bool:
    """Validate animation ID format"""
    if not isinstance(animation_id, str) or not animation_id.strip():
        return False
    
    # Check for invalid characters
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    return not any(char in animation_id for char in invalid_chars)


def validate_frame_range(frame_range: Tuple[float, float]) -> bool:
    """Validate frame range"""
    if not isinstance(frame_range, (tuple, list)) or len(frame_range) != 2:
        return False
    
    try:
        start, end = float(frame_range[0]), float(frame_range[1])
        return start <= end and start >= 0
    except (ValueError, TypeError):
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for cross-platform compatibility"""
    if not isinstance(filename, str):
        return "unknown"
    
    # Replace invalid characters
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure non-empty
    if not sanitized:
        sanitized = "unknown"
    
    return sanitized


# Export all public classes and functions
__all__ = [
    'ChannelData',
    'BoneAnimationData', 
    'BlendFileReference',
    'AnimationMetadata',
    'ApplyOptions',
    'RigTypeDetector',
    'AnimationTagger',
    'AnimationStorageDetector',
    'validate_animation_id',
    'validate_frame_range',
    'sanitize_filename'
]