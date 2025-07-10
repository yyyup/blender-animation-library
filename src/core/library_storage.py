"""
Animation Library Storage Management
Handles persistent storage and retrieval of animation library data
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .animation_data import AnimationMetadata

logger = logging.getLogger(__name__)


class AnimationLibraryManager:
    """Manages animation library storage and operations"""
    
    def __init__(self, library_path: Optional[Path] = None):
        self.library_path = library_path or Path('./animation_library')
        self.metadata_file = self.library_path / 'library_metadata.json'
        self.clips_folder = self.library_path / 'clips'
        self.thumbnails_folder = self.library_path / 'thumbnails'
        
        # In-memory storage
        self.animations: Dict[str, AnimationMetadata] = {}
        self.library_metadata = {
            "version": "2.0",
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "total_animations": 0,
            "tags": set(),
            "rig_types": set()
        }
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        self.library_path.mkdir(exist_ok=True)
        self.clips_folder.mkdir(exist_ok=True)
        self.thumbnails_folder.mkdir(exist_ok=True)
    
    def add_animation(self, animation: AnimationMetadata) -> bool:
        """Add animation to library"""
        try:
            # Store in memory
            self.animations[animation.id] = animation
            
            # Update library metadata
            self._update_library_metadata()
            
            # Save to disk
            self.save_library()
            
            logger.info(f"Added animation: {animation.name} ({animation.id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add animation {animation.id}: {e}")
            return False
    
    def remove_animation(self, animation_id: str) -> bool:
        """Remove animation from library"""
        try:
            if animation_id not in self.animations:
                logger.warning(f"Animation {animation_id} not found in library")
                return False
            
            animation = self.animations[animation_id]
            
            # Remove from memory
            del self.animations[animation_id]
            
            # Remove associated files
            self._remove_animation_files(animation_id)
            
            # Update library metadata
            self._update_library_metadata()
            
            # Save to disk
            self.save_library()
            
            logger.info(f"Removed animation: {animation.name} ({animation_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove animation {animation_id}: {e}")
            return False
    
    def get_animation(self, animation_id: str) -> Optional[AnimationMetadata]:
        """Get animation by ID"""
        return self.animations.get(animation_id)
    
    def get_all_animations(self) -> List[AnimationMetadata]:
        """Get all animations"""
        return list(self.animations.values())
    
    def search_animations(self, query: str) -> List[AnimationMetadata]:
        """Search animations by name, description, or tags"""
        query = query.lower()
        results = []
        
        for animation in self.animations.values():
            if (query in animation.name.lower() or
                query in animation.description.lower() or
                any(query in tag.lower() for tag in animation.tags)):
                results.append(animation)
        
        return results
    
    def filter_by_tags(self, tags: List[str]) -> List[AnimationMetadata]:
        """Filter animations by tags"""
        results = []
        tags_lower = [tag.lower() for tag in tags]
        
        for animation in self.animations.values():
            animation_tags_lower = [tag.lower() for tag in animation.tags]
            if any(tag in animation_tags_lower for tag in tags_lower):
                results.append(animation)
        
        return results
    
    def filter_by_rig_type(self, rig_type: str) -> List[AnimationMetadata]:
        """Filter animations by rig type"""
        return [anim for anim in self.animations.values() 
                if anim.rig_type.lower() == rig_type.lower()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get library statistics"""
        animations = list(self.animations.values())
        
        if not animations:
            return {
                "total_animations": 0,
                "total_keyframes": 0,
                "average_duration": 0,
                "tags": [],
                "rig_types": [],
                "creation_dates": []
            }
        
        total_keyframes = sum(anim.total_keyframes for anim in animations)
        average_duration = sum(anim.duration_frames for anim in animations) / len(animations)
        
        # Collect unique values
        all_tags = set()
        all_rig_types = set()
        creation_dates = []
        
        for anim in animations:
            all_tags.update(anim.tags)
            all_rig_types.add(anim.rig_type)
            creation_dates.append(anim.created_date)
        
        return {
            "total_animations": len(animations),
            "total_keyframes": total_keyframes,
            "average_duration": average_duration,
            "tags": sorted(list(all_tags)),
            "rig_types": sorted(list(all_rig_types)),
            "creation_dates": sorted(creation_dates, reverse=True)
        }
    
    def save_library(self) -> bool:
        """Save library to disk"""
        try:
            # Prepare data for serialization
            library_data = {
                "metadata": self.library_metadata,
                "animations": {
                    anim_id: anim.to_dict() 
                    for anim_id, anim in self.animations.items()
                }
            }
            
            # Write to temporary file first
            temp_file = self.metadata_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(library_data, f, indent=2)
            
            # Atomic replace
            temp_file.replace(self.metadata_file)
            
            logger.info(f"Saved library with {len(self.animations)} animations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save library: {e}")
            return False
    
    def load_library(self) -> bool:
        """Load library from disk"""
        try:
            if not self.metadata_file.exists():
                logger.info("No existing library found, starting with empty library")
                return True
            
            with open(self.metadata_file, 'r') as f:
                library_data = json.load(f)
            
            # Load metadata
            self.library_metadata = library_data.get("metadata", self.library_metadata)
            
            # Load animations
            animations_data = library_data.get("animations", {})
            self.animations = {}
            
            for anim_id, anim_data in animations_data.items():
                try:
                    animation = AnimationMetadata.from_dict(anim_data)
                    self.animations[anim_id] = animation
                except Exception as e:
                    logger.warning(f"Failed to load animation {anim_id}: {e}")
            
            logger.info(f"Loaded library with {len(self.animations)} animations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load library: {e}")
            return False
    
    def backup_library(self, backup_path: Optional[Path] = None) -> bool:
        """Create a backup of the library"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.library_path.parent / f"animation_library_backup_{timestamp}"
            
            # Copy entire library directory
            if self.library_path.exists():
                shutil.copytree(self.library_path, backup_path)
                logger.info(f"Created library backup at: {backup_path}")
                return True
            else:
                logger.warning("No library to backup")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def restore_library(self, backup_path: Path) -> bool:
        """Restore library from backup"""
        try:
            if not backup_path.exists():
                logger.error(f"Backup path does not exist: {backup_path}")
                return False
            
            # Create backup of current library
            current_backup = self.library_path.with_suffix('.backup')
            if self.library_path.exists():
                shutil.move(str(self.library_path), str(current_backup))
            
            # Restore from backup
            shutil.copytree(backup_path, self.library_path)
            
            # Reload library
            self.load_library()
            
            logger.info(f"Restored library from backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            # Try to restore current backup if it exists
            current_backup = self.library_path.with_suffix('.backup')
            if current_backup.exists():
                shutil.move(str(current_backup), str(self.library_path))
            return False
    
    def export_library(self, export_path: Path, include_files: bool = True) -> bool:
        """Export library to a different location"""
        try:
            # Ensure export directory exists
            export_path.mkdir(parents=True, exist_ok=True)
            
            # Export metadata
            export_metadata_file = export_path / 'library_metadata.json'
            library_data = {
                "metadata": self.library_metadata,
                "animations": {
                    anim_id: anim.to_dict() 
                    for anim_id, anim in self.animations.items()
                }
            }
            
            with open(export_metadata_file, 'w') as f:
                json.dump(library_data, f, indent=2)
            
            # Copy files if requested
            if include_files:
                if self.clips_folder.exists():
                    export_clips = export_path / 'clips'
                    shutil.copytree(self.clips_folder, export_clips, dirs_exist_ok=True)
                
                if self.thumbnails_folder.exists():
                    export_thumbnails = export_path / 'thumbnails'
                    shutil.copytree(self.thumbnails_folder, export_thumbnails, dirs_exist_ok=True)
            
            logger.info(f"Exported library to: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export library: {e}")
            return False
    
    def import_library(self, import_path: Path, merge: bool = True) -> bool:
        """Import library from a different location"""
        try:
            import_metadata_file = import_path / 'library_metadata.json'
            
            if not import_metadata_file.exists():
                logger.error(f"No library metadata found at: {import_path}")
                return False
            
            with open(import_metadata_file, 'r') as f:
                import_data = json.load(f)
            
            animations_data = import_data.get("animations", {})
            imported_count = 0
            
            for anim_id, anim_data in animations_data.items():
                try:
                    animation = AnimationMetadata.from_dict(anim_data)
                    
                    # Handle conflicts
                    if anim_id in self.animations:
                        if merge:
                            # Generate new ID for imported animation
                            original_id = anim_id
                            counter = 1
                            while anim_id in self.animations:
                                anim_id = f"{original_id}_{counter}"
                                counter += 1
                            animation.id = anim_id
                        else:
                            logger.warning(f"Skipping duplicate animation: {anim_id}")
                            continue
                    
                    self.animations[anim_id] = animation
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to import animation {anim_id}: {e}")
            
            # Update metadata and save
            self._update_library_metadata()
            self.save_library()
            
            logger.info(f"Imported {imported_count} animations from: {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import library: {e}")
            return False
    
    def _update_library_metadata(self):
        """Update library metadata"""
        self.library_metadata["last_modified"] = datetime.now().isoformat()
        self.library_metadata["total_animations"] = len(self.animations)
        
        # Update tags and rig types
        all_tags = set()
        all_rig_types = set()
        
        for animation in self.animations.values():
            all_tags.update(animation.tags)
            all_rig_types.add(animation.rig_type)
        
        self.library_metadata["tags"] = sorted(list(all_tags))
        self.library_metadata["rig_types"] = sorted(list(all_rig_types))
    
    def _remove_animation_files(self, animation_id: str):
        """Remove files associated with an animation"""
        # Remove animation clip file
        clip_file = self.clips_folder / f"{animation_id}.blend"
        if clip_file.exists():
            clip_file.unlink()
        
        # Remove thumbnail file
        thumbnail_file = self.thumbnails_folder / f"{animation_id}.png"
        if thumbnail_file.exists():
            thumbnail_file.unlink()
    
    def get_library_size(self) -> Dict[str, int]:
        """Get library size information"""
        total_size = 0
        file_count = 0
        
        for file_path in self.library_path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        return {
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "file_count": file_count,
            "animation_count": len(self.animations)
        }