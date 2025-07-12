"""
Animation Library Storage Management
COMPLETE FILE: src/core/library_storage.py

Enhanced with .blend file management, migration capabilities, and folder organization.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from .animation_data import AnimationMetadata, BlendFileReference, AnimationStorageDetector

logger = logging.getLogger(__name__)


class AnimationLibraryManager:
    """Enhanced animation library manager with .blend file support and folder organization"""
    
    def __init__(self, library_path: Optional[Path] = None):
        self.library_path = library_path or Path('./animation_library')
        self.metadata_file = self.library_path / 'library_metadata.json'
        self.clips_folder = self.library_path / 'clips'  # Legacy JSON clips
        self.actions_folder = self.library_path / 'actions'  # NEW: .blend files
        self.thumbnails_folder = self.library_path / 'thumbnails'
        self.folders_file = self.library_path / 'folders.json'  # NEW: Folder structure
        
        # In-memory storage
        self.animations: Dict[str, AnimationMetadata] = {}
        self.folder_structure = self._load_folder_structure()
        
        self.library_metadata = {
            "version": "2.1",  # Updated for .blend file support
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "total_animations": 0,
            "blend_file_animations": 0,  # NEW: Track .blend file count
            "json_animations": 0,        # NEW: Track legacy JSON count
            "tags": set(),
            "rig_types": set(),
            "storage_methods": ["blend_file", "json_keyframes"],  # NEW: Supported methods
            "folder_structure": {}  # NEW: Track folder organization
        }
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        self.library_path.mkdir(exist_ok=True)
        self.clips_folder.mkdir(exist_ok=True)
        self.actions_folder.mkdir(exist_ok=True)  # NEW: For .blend files
        self.thumbnails_folder.mkdir(exist_ok=True)
        
        logger.info(f"📁 Library directories initialized: {self.library_path}")
    
    def _load_folder_structure(self) -> Dict[str, Any]:
        """Load folder structure from disk"""
        if self.folders_file and self.folders_file.exists():
            try:
                with open(self.folders_file, 'r') as f:
                    structure = json.load(f)
                    # Ensure Root folder exists in loaded structure
                    if "Custom Folders" in structure and "children" in structure["Custom Folders"]:
                        if "📁 Root" not in structure["Custom Folders"]["children"]:
                            structure["Custom Folders"]["children"]["📁 Root"] = {
                                "type": "folder", 
                                "filter": "folder:Root", 
                                "count": 0
                            }
                    return structure
            except Exception as e:
                logger.warning(f"Failed to load folder structure: {e}")
        
        # Minimal default folder structure with Root folder visible
        return {
            "Custom Folders": {
                "type": "category", 
                "children": {
                    "📁 Root": {"type": "folder", "filter": "folder:Root", "count": 0}
                }
            }
        }
    
    def _save_folder_structure(self):
        """Save folder structure to disk"""
        try:
            with open(self.folders_file, 'w') as f:
                json.dump(self.folder_structure, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save folder structure: {e}")
    
    def create_folder(self, folder_name: str, parent_path: str = "Root") -> bool:
        """Create a new folder in the structure"""
        try:
            # Navigate to parent folder
            current = self.folder_structure
            if parent_path != "Root":
                path_parts = parent_path.split("/")
                for part in path_parts:
                    if part in current and "children" in current[part]:
                        current = current[part]["children"]
                    else:
                        logger.error(f"Parent path not found: {parent_path}")
                        return False
            
            # For custom folders, add to Custom Folders section
            if "Custom Folders" not in current:
                current["Custom Folders"] = {"type": "category", "children": {}}
            
            custom_folders = current["Custom Folders"]["children"]
            folder_key = f"📁 {folder_name}"
            
            # Create new folder
            if folder_key not in custom_folders:
                custom_folders[folder_key] = {
                    "type": "folder", 
                    "filter": f"folder:{folder_name}",
                    "count": 0
                }
                self._save_folder_structure()
                logger.info(f"📁 Created folder: {folder_name}")
                return True
            else:
                logger.warning(f"Folder already exists: {folder_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            return False
    
    def delete_folder(self, folder_path: str) -> bool:
        """Delete a folder (moves animations to Root)"""
        try:
            print(f"📁 LIBRARY: Deleting folder '{folder_path}'")
            
            # Don't allow deleting system folders
            if folder_path in ["Root", "All Animations", "Custom Folders"]:
                logger.warning(f"Cannot delete system folder: {folder_path}")
                return False
            
            # Move animations to Root
            animations_in_folder = []
            animations_moved = 0
            
            for anim_id, animation in self.animations.items():
                current_folder = getattr(animation, 'folder_path', 'Root')
                if current_folder == folder_path:
                    animations_in_folder.append((anim_id, animation))
            
            print(f"📁 LIBRARY: Found {len(animations_in_folder)} animations in folder '{folder_path}'")
            
            # Move all animations to Root
            for anim_id, animation in animations_in_folder:
                old_folder = getattr(animation, 'folder_path', 'Root')
                animation.folder_path = "Root"
                animations_moved += 1
                print(f"📁 LIBRARY: Moved animation {animation.name}: '{old_folder}' → 'Root'")
            
            # Remove folder from structure - try different possible folder keys
            folder_removed = False
            if "Custom Folders" in self.folder_structure and "children" in self.folder_structure["Custom Folders"]:
                custom_folders = self.folder_structure["Custom Folders"]["children"]
                
                # Try different possible keys
                possible_keys = [
                    f"📁 {folder_path}",
                    folder_path,
                    f"{folder_path}"
                ]
                
                print(f"📁 LIBRARY: Looking for folder in structure...")
                print(f"📁 LIBRARY: Available folder keys: {list(custom_folders.keys())}")
                
                for key in possible_keys:
                    if key in custom_folders:
                        del custom_folders[key]
                        folder_removed = True
                        print(f"📁 LIBRARY: Successfully removed folder key '{key}' from structure")
                        break
                
                if not folder_removed:
                    print(f"❌ LIBRARY: Could not find folder '{folder_path}' in structure with any key")
            
            # Save changes
            self._save_folder_structure()
            self.save_library()
            
            if folder_removed:
                logger.info(f"🗑️ Deleted folder: {folder_path}, moved {animations_moved} animations to Root")
                return True
            else:
                logger.warning(f"⚠️ Moved animations but could not remove folder from structure: {folder_path}")
                return False
                
        except Exception as e:
            print(f"❌ LIBRARY: Failed to delete folder {folder_path}: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Failed to delete folder: {e}")
            return False
    
    def get_folder_structure(self) -> Dict[str, Any]:
        """Get the complete folder structure"""
        # Update dynamic folders with current counts
        structure = self.folder_structure.copy()
        
        # Update counts for filter folders
        self._update_folder_counts(structure)
        
        return structure
    
    def _update_folder_counts(self, structure: Dict[str, Any]):
        """Update animation counts for filter folders"""
        all_animations = self.get_all_animations()
        
        for folder_name, folder_data in structure.items():
            if folder_data.get("type") == "filter":
                # Count animations matching this filter
                filter_str = folder_data.get("filter", "")
                count = self._count_animations_for_filter(all_animations, filter_str)
                folder_data["count"] = count
            elif "children" in folder_data:
                self._update_folder_counts(folder_data["children"])
    
    def _count_animations_for_filter(self, animations: List[AnimationMetadata], filter_str: str) -> int:
        """Count animations matching a filter string"""
        if not filter_str:
            return len(animations)
        
        count = 0
        for anim in animations:
            if filter_str.startswith("rig_type:"):
                rig_type = filter_str.split(":", 1)[1]
                if anim.rig_type == rig_type:
                    count += 1
            elif filter_str.startswith("storage:"):
                storage_method = filter_str.split(":", 1)[1]
                if anim.storage_method == storage_method:
                    count += 1
            elif filter_str.startswith("tag:"):
                tag = filter_str.split(":", 1)[1]
                if tag in anim.tags:
                    count += 1
        
        return count
    
    def add_animation(self, animation: AnimationMetadata, folder_path: str = "Root") -> bool:
        """Add animation to library with folder organization"""
        try:
            # Update .blend file path if using blend storage
            if animation.is_blend_file_storage():
                animation.update_blend_file_path(self.library_path)
            
            # Set folder for animation
            animation.folder_path = folder_path
            
            # Store in memory
            self.animations[animation.id] = animation
            
            # Update library metadata
            self._update_library_metadata()
            
            # Save to disk
            self.save_library()
            
            storage_info = "(.blend file)" if animation.is_blend_file_storage() else "(JSON)"
            logger.info(
                f"✅ Added animation: {animation.name} ({animation.id}) "
                f"to folder '{folder_path}' {storage_info}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to add animation {animation.id}: {e}")
            return False
    
    def remove_animation(self, animation_id: str) -> bool:
        """Remove animation from library and clean up files"""
        try:
            if animation_id not in self.animations:
                logger.warning(f"Animation {animation_id} not found in library")
                return False
            
            animation = self.animations[animation_id]
            
            # Remove from memory
            del self.animations[animation_id]
            
            # Remove associated files
            self._remove_animation_files(animation)
            
            # Update library metadata
            self._update_library_metadata()
            
            # Save to disk
            self.save_library()
            
            logger.info(f"🗑️ Removed animation: {animation.name} ({animation_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove animation {animation_id}: {e}")
            return False
    
    def get_animation(self, animation_id: str) -> Optional[AnimationMetadata]:
        """Get animation by ID with .blend file validation"""
        animation = self.animations.get(animation_id)
        
        if animation and animation.is_blend_file_storage():
            # Validate .blend file still exists
            animation.update_blend_file_path(self.library_path)
            if not animation.blend_reference.exists():
                logger.warning(f"⚠️ .blend file missing for animation: {animation.name}")
                # Could trigger auto-repair or migration here
        
        return animation
    
    def get_all_animations(self) -> List[AnimationMetadata]:
        """Get all animations with .blend file validation"""
        valid_animations = []
        
        for animation in self.animations.values():
            if animation.is_blend_file_storage():
                animation.update_blend_file_path(self.library_path)
                if animation.blend_reference.exists():
                    valid_animations.append(animation)
                else:
                    logger.warning(f"⚠️ Skipping animation with missing .blend file: {animation.name}")
            else:
                # Legacy JSON animations
                valid_animations.append(animation)
        
        return valid_animations
    
    def get_animations_in_folder(self, folder_path: str) -> List[AnimationMetadata]:
        """Get all animations in a specific folder"""
        folder_animations = []
        
        for animation in self.animations.values():
            animation_folder = getattr(animation, 'folder_path', 'Root')
            
            if folder_path == "Root":
                # Show animations in root or without folder specified
                if animation_folder in ["Root", None, ""]:
                    folder_animations.append(animation)
            else:
                # Show animations in specific folder
                if animation_folder == folder_path:
                    folder_animations.append(animation)
        
        return folder_animations
    
    def move_animation_to_folder(self, animation_id: str, new_folder_path: str) -> bool:
        """Move animation to a different folder"""
        try:
            if animation_id in self.animations:
                old_folder = getattr(self.animations[animation_id], 'folder_path', 'Root')
                print(f"📁 LIBRARY: Moving animation {animation_id}")
                print(f"📁 LIBRARY: '{old_folder}' → '{new_folder_path}'")
                
                # Update the folder path
                self.animations[animation_id].folder_path = new_folder_path
                
                # Verify the change
                updated_folder = getattr(self.animations[animation_id], 'folder_path', 'Root')
                print(f"📁 LIBRARY: Folder path updated to: '{updated_folder}'")
                
                # Save changes
                self.save_library()
                
                logger.info(f"📁 Moved animation {animation_id} from '{old_folder}' to '{new_folder_path}'")
                return True
            else:
                print(f"❌ LIBRARY: Animation {animation_id} not found")
                logger.warning(f"Animation {animation_id} not found")
                return False
                
        except Exception as e:
            print(f"❌ LIBRARY: Failed to move animation {animation_id}: {e}")
            logger.error(f"Failed to move animation {animation_id}: {e}")
            return False
    
    def get_folder_statistics(self) -> Dict[str, Dict[str, int]]:
        """Get statistics for each folder"""
        folder_stats = {}
        
        for animation in self.animations.values():
            folder_path = getattr(animation, 'folder_path', 'Root')
            
            if folder_path not in folder_stats:
                folder_stats[folder_path] = {
                    'total': 0,
                    'blend_files': 0,
                    'json_files': 0
                }
            
            folder_stats[folder_path]['total'] += 1
            
            if animation.is_blend_file_storage():
                folder_stats[folder_path]['blend_files'] += 1
            else:
                folder_stats[folder_path]['json_files'] += 1
        
        return folder_stats
    
    def search_animations(self, query: str) -> List[AnimationMetadata]:
        """Search animations by name, description, or tags"""
        query = query.lower()
        results = []
        
        for animation in self.get_all_animations():
            if (query in animation.name.lower() or
                query in animation.description.lower() or
                any(query in tag.lower() for tag in animation.tags)):
                results.append(animation)
        
        return results
    
    def filter_by_tags(self, tags: List[str]) -> List[AnimationMetadata]:
        """Filter animations by tags"""
        results = []
        tags_lower = [tag.lower() for tag in tags]
        
        for animation in self.get_all_animations():
            animation_tags_lower = [tag.lower() for tag in animation.tags]
            if any(tag in animation_tags_lower for tag in tags_lower):
                results.append(animation)
        
        return results
    
    def filter_by_rig_type(self, rig_type: str) -> List[AnimationMetadata]:
        """Filter animations by rig type"""
        return [anim for anim in self.get_all_animations() 
                if anim.rig_type.lower() == rig_type.lower()]
    
    def filter_by_storage_method(self, storage_method: str) -> List[AnimationMetadata]:
        """Filter animations by storage method"""
        return [anim for anim in self.get_all_animations() 
                if anim.storage_method == storage_method]
    
    def get_blend_file_animations(self) -> List[AnimationMetadata]:
        """Get only .blend file animations (fast ones)"""
        return self.filter_by_storage_method("blend_file")
    
    def get_legacy_animations(self) -> List[AnimationMetadata]:
        """Get only legacy JSON animations (slow ones)"""
        return self.filter_by_storage_method("json_keyframes")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get library statistics with storage method breakdown"""
        all_animations = self.get_all_animations()
        blend_animations = self.get_blend_file_animations()
        legacy_animations = self.get_legacy_animations()
        
        if not all_animations:
            return {
                "total_animations": 0,
                "blend_file_animations": 0,
                "json_animations": 0,
                "total_keyframes": 0,
                "average_duration": 0,
                "tags": [],
                "rig_types": [],
                "storage_methods": {},
                "performance_stats": {},
                "folder_stats": {}
            }
        
        total_keyframes = sum(anim.total_keyframes for anim in all_animations)
        average_duration = sum(anim.duration_frames for anim in all_animations) / len(all_animations)
        
        # Collect unique values
        all_tags = set()
        all_rig_types = set()
        creation_dates = []
        
        for anim in all_animations:
            all_tags.update(anim.tags)
            all_rig_types.add(anim.rig_type)
            creation_dates.append(anim.created_date)
        
        # Performance statistics
        if blend_animations:
            blend_extraction_times = [anim.extraction_time_seconds for anim in blend_animations]
            blend_avg_extraction = sum(blend_extraction_times) / len(blend_animations)
            
            blend_application_times = [anim.application_time_seconds for anim in blend_animations]
            blend_avg_application = sum(blend_application_times) / len(blend_animations)
        else:
            blend_avg_extraction = 0
            blend_avg_application = 0
        
        if legacy_animations:
            legacy_extraction_times = [anim.extraction_time_seconds for anim in legacy_animations]
            legacy_avg_extraction = sum(legacy_extraction_times) / len(legacy_animations)
            
            legacy_application_times = [anim.application_time_seconds for anim in legacy_animations]
            legacy_avg_application = sum(legacy_application_times) / len(legacy_animations)
        else:
            legacy_avg_extraction = 0
            legacy_avg_application = 0
        
        # Calculate total storage size
        total_blend_size = sum(anim.blend_reference.get_size_mb() for anim in blend_animations if anim.blend_reference)
        
        return {
            "total_animations": len(all_animations),
            "blend_file_animations": len(blend_animations),
            "json_animations": len(legacy_animations),
            "total_keyframes": total_keyframes,
            "average_duration": average_duration,
            "tags": sorted(list(all_tags)),
            "rig_types": sorted(list(all_rig_types)),
            "creation_dates": sorted(creation_dates, reverse=True),
            "storage_methods": {
                "blend_file": len(blend_animations),
                "json_keyframes": len(legacy_animations)
            },
            "performance_stats": {
                "blend_avg_extraction_time": blend_avg_extraction,
                "blend_avg_application_time": blend_avg_application,
                "legacy_avg_extraction_time": legacy_avg_extraction,
                "legacy_avg_application_time": legacy_avg_application,
                "performance_improvement": {
                    "extraction": legacy_avg_extraction / blend_avg_extraction if blend_avg_extraction > 0 else 1,
                    "application": legacy_avg_application / blend_avg_application if blend_avg_application > 0 else 1
                }
            },
            "storage_stats": {
                "total_blend_size_mb": total_blend_size,
                "average_blend_size_mb": total_blend_size / len(blend_animations) if blend_animations else 0
            },
            "folder_stats": self.get_folder_statistics()
        }
    
    def save_library(self) -> bool:
        """Save library to disk with .blend file references"""
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
            
            # Save folder structure
            self._save_folder_structure()
            
            blend_count = len(self.get_blend_file_animations())
            legacy_count = len(self.get_legacy_animations())
            logger.info(f"💾 Saved library: {blend_count} .blend + {legacy_count} JSON animations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save library: {e}")
            return False
    
    def load_library(self) -> bool:
        """Load library from disk with .blend file path resolution"""
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
            
            blend_count = 0
            legacy_count = 0
            
            for anim_id, anim_data in animations_data.items():
                try:
                    animation = AnimationMetadata.from_dict(anim_data)
                    
                    # Update .blend file paths
                    if animation.is_blend_file_storage():
                        animation.update_blend_file_path(self.library_path)
                        blend_count += 1
                    else:
                        legacy_count += 1
                    
                    self.animations[anim_id] = animation
                    
                except Exception as e:
                    logger.warning(f"Failed to load animation {anim_id}: {e}")
            
            # Load folder structure
            self.folder_structure = self._load_folder_structure()
            
            logger.info(f"📚 Loaded library: {blend_count} .blend + {legacy_count} JSON animations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load library: {e}")
            return False
    
    def cleanup_missing_blend_files(self) -> int:
        """Remove animations with missing .blend files"""
        animations_to_remove = []
        
        for anim_id, animation in self.animations.items():
            if animation.is_blend_file_storage():
                animation.update_blend_file_path(self.library_path)
                if not animation.blend_reference.exists():
                    animations_to_remove.append(anim_id)
                    logger.warning(f"🗑️ Removing animation with missing .blend file: {animation.name}")
        
        for anim_id in animations_to_remove:
            del self.animations[anim_id]
        
        if animations_to_remove:
            self._update_library_metadata()
            self.save_library()
        
        return len(animations_to_remove)
    
    def optimize_library(self) -> Dict[str, Any]:
        """Optimize library by cleaning up and organizing files"""
        results = {
            "orphaned_files_removed": 0,
            "missing_animations_removed": 0,
            "space_saved_mb": 0,
            "operations": []
        }
        
        # Remove animations with missing .blend files
        missing_count = self.cleanup_missing_blend_files()
        results["missing_animations_removed"] = missing_count
        results["operations"].append(f"Removed {missing_count} animations with missing .blend files")
        
        # Remove orphaned .blend files
        validation = self.validate_blend_files()
        space_saved = 0
        
        for orphaned_file in validation["orphaned"]:
            orphaned_path = self.actions_folder / orphaned_file
            if orphaned_path.exists():
                file_size = orphaned_path.stat().st_size
                orphaned_path.unlink()
                space_saved += file_size
                results["orphaned_files_removed"] += 1
        
        results["space_saved_mb"] = space_saved / (1024 * 1024)
        results["operations"].append(f"Removed {results['orphaned_files_removed']} orphaned .blend files")
        
        # Save optimized library
        self.save_library()
        
        logger.info(f"🔧 Library optimized: {results}")
        return results
    
    def validate_blend_files(self) -> Dict[str, List[str]]:
        """Validate all .blend file references"""
        validation_results = {
            "valid": [],
            "missing": [],
            "corrupted": [],
            "orphaned": []
        }
        
        # Check animations with .blend references
        for animation in self.get_blend_file_animations():
            animation.update_blend_file_path(self.library_path)
            
            if animation.blend_reference.exists():
                validation_results["valid"].append(animation.name)
            else:
                validation_results["missing"].append(animation.name)
        
        # Check for orphaned .blend files
        blend_animations = self.get_blend_file_animations()
        referenced_files = {
            anim.blend_reference.blend_file for anim in blend_animations 
            if anim.blend_reference
        }
        actual_files = {f.name for f in self.actions_folder.glob("*.blend")}
        orphaned_files = actual_files - referenced_files
        validation_results["orphaned"] = list(orphaned_files)
        
        return validation_results
    
    def _update_library_metadata(self):
        """Update library metadata with storage method counts"""
        self.library_metadata["last_modified"] = datetime.now().isoformat()
        self.library_metadata["total_animations"] = len(self.animations)
        
        # Count by storage method
        blend_count = len(self.get_blend_file_animations())
        legacy_count = len(self.get_legacy_animations())
        
        self.library_metadata["blend_file_animations"] = blend_count
        self.library_metadata["json_animations"] = legacy_count
        
        # Update tags and rig types
        all_tags = set()
        all_rig_types = set()
        
        for animation in self.animations.values():
            all_tags.update(animation.tags)
            all_rig_types.add(animation.rig_type)
        
        self.library_metadata["tags"] = sorted(list(all_tags))
        self.library_metadata["rig_types"] = sorted(list(all_rig_types))
        
        # Update folder structure
        self.library_metadata["folder_structure"] = self.get_folder_statistics()
    
    def _remove_animation_files(self, animation: AnimationMetadata):
        """Remove files associated with an animation"""
        if animation.is_blend_file_storage() and animation.blend_reference:
            # Remove .blend file
            blend_path = self.actions_folder / animation.blend_reference.blend_file
            if blend_path.exists():
                blend_path.unlink()
                logger.info(f"🗑️ Removed .blend file: {blend_path.name}")
        
        # Remove legacy clip file if it exists
        clip_file = self.clips_folder / f"{animation.id}.blend"
        if clip_file.exists():
            clip_file.unlink()
        
        # Remove thumbnail file
        thumbnail_file = self.thumbnails_folder / f"{animation.id}.png"
        if thumbnail_file.exists():
            thumbnail_file.unlink()


class BlendFileValidator:
    """Utility class for validating .blend files"""
    
    @staticmethod
    def validate_blend_file(file_path: Path) -> Dict[str, Any]:
        """Validate a .blend file"""
        if not file_path.exists():
            return {"valid": False, "error": "File does not exist"}
        
        if file_path.suffix != '.blend':
            return {"valid": False, "error": "Not a .blend file"}
        
        try:
            file_size = file_path.stat().st_size
            if file_size == 0:
                return {"valid": False, "error": "Empty file"}
            
            # Basic file header check (Blender files start with "BLENDER")
            with open(file_path, 'rb') as f:
                header = f.read(7)
                if header != b'BLENDER':
                    return {"valid": False, "error": "Invalid .blend file header"}
            
            return {
                "valid": True,
                "size_mb": file_size / (1024 * 1024),
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}