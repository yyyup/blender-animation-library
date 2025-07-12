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
        self.actions_folder = self.library_path / 'actions'  # Legacy .blend files (migration support)
        self.animations_folder = self.library_path / 'animations'  # NEW: File system-based folders
        self.previews_folder = self.library_path / 'previews'  # Updated from thumbnails_folder
        
        # Remove JSON-based folder structure - now using file system
        # self.folders_file = self.library_path / 'folders.json'  # REMOVED: No longer needed
        
        # In-memory storage
        self.animations: Dict[str, AnimationMetadata] = {}
        # self.folder_structure = self._load_folder_structure()  # REMOVED: Use file system scanning
        
        self.library_metadata = {
            "version": "3.0",  # Updated for file system-based folders
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "total_animations": 0,
            "blend_file_animations": 0,  # NEW: Track .blend file count
            "json_animations": 0,        # NEW: Track legacy JSON count
            "tags": set(),
            "rig_types": set(),
            "storage_methods": ["blend_file", "json_keyframes"],  # NEW: Supported methods
            "folder_structure": "filesystem"  # NEW: Indicates file system-based folders
        }
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist with proper structure"""
        # Create main library directories
        self.library_path.mkdir(exist_ok=True)
        self.clips_folder.mkdir(exist_ok=True)
        
        # Create animations/ as the main folder container
        self.animations_folder.mkdir(exist_ok=True)
        self.previews_folder.mkdir(exist_ok=True)  # Updated from thumbnails_folder
        
        # Create animations/Root/ as the default location for new animations
        root_animations_folder = self.animations_folder / "Root"
        root_animations_folder.mkdir(exist_ok=True)
        
        # Create previews/Root/ to mirror the structure (updated from thumbnails)
        root_previews_folder = self.previews_folder / "Root"
        root_previews_folder.mkdir(exist_ok=True)
        
        # Legacy support: Keep actions/ for migration
        self.actions_folder.mkdir(exist_ok=True)
        
        logger.info("📁 Library directories initialized: %s", self.library_path)
        logger.info("📁 Default Root folder created: %s", root_animations_folder)
    
    def scan_filesystem_folders(self) -> Dict[str, Any]:
        """Scan file system to build folder structure"""
        folder_structure = {
            "🎬 All Animations": {
                "type": "all",
                "count": len(self.animations)
            },
            "Custom Folders": {
                "type": "category", 
                "children": {}
            }
        }
        
        # Scan animations folder for actual directories
        if self.animations_folder.exists():
            try:
                for folder_path in self.animations_folder.iterdir():
                    if folder_path.is_dir():
                        folder_name = folder_path.name
                        
                        # Count animations in this folder
                        animation_count = self._count_animations_in_folder(folder_name)
                        
                        # Add to structure with emoji prefix for display
                        folder_structure["Custom Folders"]["children"][f"📁 {folder_name}"] = {
                            "type": "folder",
                            "filter": f"folder:{folder_name}",
                            "count": animation_count
                        }
                        
                logger.info("📁 Scanned file system: found %d folders", 
                           len(folder_structure["Custom Folders"]["children"]))
            except Exception as e:
                logger.error("Failed to scan filesystem folders: %s", e)
        
        return folder_structure
        
    def _count_animations_in_folder(self, folder_name: str) -> int:
        """Count animations in a specific folder"""
        count = 0
        for animation in self.animations.values():
            if getattr(animation, 'folder_path', 'Root') == folder_name:
                count += 1
        return count
    
    def create_folder(self, folder_name: str) -> bool:
        """Create a new folder in the file system"""
        try:
            # Validate folder name
            if not folder_name.strip():
                logger.warning("Empty folder name provided")
                return False
                
            # Prevent nested folder names
            if "/" in folder_name or "\\" in folder_name:
                logger.warning("Folder names cannot contain path separators")
                return False
                
            # Create folder in animations directory
            new_folder = self.animations_folder / folder_name.strip()
            if new_folder.exists():
                logger.warning("Folder already exists: %s", folder_name)
                return False
                
            new_folder.mkdir(parents=True, exist_ok=False)
            
            # Create corresponding previews folder (updated from thumbnails)
            previews_folder = self.previews_folder / folder_name.strip()
            previews_folder.mkdir(parents=True, exist_ok=True)
            
            logger.info("📁 Created folder: %s", folder_name)
            return True
            
        except Exception as e:
            logger.error("Failed to create folder: %s", e)
            return False
    
    def delete_folder(self, folder_path: str) -> bool:
        """Delete a folder from the file system and move animations to Root"""
        try:
            print(f"📁 LIBRARY: Deleting folder '{folder_path}'")
            
            # Prevent deletion of system folders
            if folder_path in ["Root", "All Animations", "Custom Folders"]:
                logger.warning("Cannot delete system folder: %s", folder_path)
                return False
            
            # Get folder path in file system
            folder_to_delete = self.animations_folder / folder_path
            if not folder_to_delete.exists():
                logger.warning("Folder does not exist: %s", folder_path)
                return False
            
            # Find animations in this folder and move them to Root
            animations_in_folder = []
            for animation_id, animation in self.animations.items():
                current_folder = getattr(animation, 'folder_path', 'Root')
                if current_folder == folder_path:
                    animations_in_folder.append(animation_id)
                    
            print(f"📁 LIBRARY: Found {len(animations_in_folder)} animations in folder '{folder_path}'")
            
            # Move animations to Root folder
            animations_moved = 0
            for animation_id in animations_in_folder:
                animation = self.animations[animation_id]
                old_folder = getattr(animation, 'folder_path', 'Root')
                animation.folder_path = "Root"
                
                # Move actual .blend file if it exists
                if animation.is_blend_file_storage() and animation.blend_reference.exists():
                    old_path = animation.blend_reference.file_path
                    new_path = self.animations_folder / "Root" / old_path.name
                    
                    try:
                        shutil.move(str(old_path), str(new_path))
                        # Update the animation's file path
                        animation.blend_reference.file_path = new_path
                        animations_moved += 1
                    except Exception as e:
                        logger.error("Failed to move animation file %s: %s", old_path, e)
                else:
                    animations_moved += 1
            
            # Remove the actual folder from file system
            try:
                if folder_to_delete.is_dir():
                    # Move any remaining files to Root before deleting
                    root_folder = self.animations_folder / "Root"
                    for item in folder_to_delete.iterdir():
                        if item.is_file():
                            shutil.move(str(item), str(root_folder / item.name))
                    
                    # Remove the empty folder
                    folder_to_delete.rmdir()
                    
                # Also remove previews folder if it exists (updated from thumbnails)
                previews_folder = self.previews_folder / folder_path
                if previews_folder.exists():
                    previews_root = self.previews_folder / "Root"
                    for item in previews_folder.iterdir():
                        if item.is_file():
                            shutil.move(str(item), str(previews_root / item.name))
                    previews_folder.rmdir()
                    
            except Exception as e:
                logger.error("Failed to remove folder from filesystem: %s", e)
                return False
            
            # Save the library with updated animation paths
            self.save_library()
            
            if animations_moved > 0:
                logger.info("🗑️ Deleted folder: %s, moved %d animations to Root", folder_path, animations_moved)
            else:
                logger.info("🗑️ Deleted empty folder: %s", folder_path)
            
            return True
            
        except Exception as e:
            print(f"❌ LIBRARY: Failed to delete folder {folder_path}: {e}")
            logger.error("Failed to delete folder %s: %s", folder_path, e)
            return False
    
    def get_folder_structure(self) -> Dict[str, Any]:
        """Get the complete folder structure by scanning file system"""
        return self.scan_filesystem_folders()
    
    def _update_folder_counts(self, structure: Dict[str, Any]):
        """Update animation counts for folders (not used in file system mode)"""
        # This method is kept for compatibility but not used
        # File system folders get counts dynamically from scan_filesystem_folders
        pass
    
    def _count_animations_for_filter(self, animations: List[AnimationMetadata], filter_str: str) -> int:
        """Count animations matching a filter string (not used in file system mode)"""
        # This method is kept for compatibility but not used
        # File system folders get counts dynamically
        return 0
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
        """Add animation to library with file system folder organization"""
        try:
            # Ensure target folder exists in file system
            target_folder = self.animations_folder / folder_path
            target_folder.mkdir(parents=True, exist_ok=True)
            
            # Also ensure previews folder exists (updated from thumbnails)
            target_previews = self.previews_folder / folder_path
            target_previews.mkdir(parents=True, exist_ok=True)
            
            # Update .blend file path if using blend storage
            if animation.is_blend_file_storage():
                # Move .blend file to correct folder if needed
                current_path = animation.blend_reference.file_path
                if current_path.parent != target_folder:
                    new_path = target_folder / current_path.name
                    try:
                        shutil.move(str(current_path), str(new_path))
                        animation.blend_reference.file_path = new_path
                        print(f"📁 Moved .blend file to folder: {new_path}")
                    except Exception as e:
                        logger.warning("Failed to move .blend file to folder: %s", e)
                
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
                "✅ Added animation: %s (%s) to folder '%s' %s",
                animation.name, animation.id, folder_path, storage_info
            )
            return True
            
        except Exception as e:
            logger.error("Failed to add animation %s: %s", animation.id, e)
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
        """Move animation to a different folder in the file system"""
        try:
            if animation_id in self.animations:
                animation = self.animations[animation_id]
                old_folder = getattr(animation, 'folder_path', 'Root')
                print(f"📁 LIBRARY: Moving animation {animation_id}")
                print(f"📁 LIBRARY: '{old_folder}' → '{new_folder_path}'")
                
                # Ensure target folder exists in file system
                target_folder = self.animations_folder / new_folder_path
                target_folder.mkdir(parents=True, exist_ok=True)
                
                # Also ensure previews folder exists (updated from thumbnails)
                target_previews = self.previews_folder / new_folder_path  
                target_previews.mkdir(parents=True, exist_ok=True)
                
                # Move .blend file if it exists
                if animation.is_blend_file_storage() and animation.blend_reference.exists():
                    old_path = animation.blend_reference.file_path
                    new_path = target_folder / old_path.name
                    
                    try:
                        shutil.move(str(old_path), str(new_path))
                        # Update the animation's file path
                        animation.blend_reference.file_path = new_path
                        print(f"📁 LIBRARY: Moved .blend file: {old_path} → {new_path}")
                    except Exception as e:
                        logger.error("Failed to move .blend file %s: %s", old_path, e)
                        return False
                
                # Move preview if it exists (updated from thumbnail)
                preview_name = f"{animation_id}.mp4"  # Updated from .png to .mp4
                old_preview = self.previews_folder / old_folder / preview_name
                new_preview = target_previews / preview_name
                
                if old_preview.exists():
                    try:
                        shutil.move(str(old_preview), str(new_preview))
                        print(f"📁 LIBRARY: Moved preview: {old_preview} → {new_preview}")
                    except Exception as e:
                        logger.warning("Failed to move preview %s: %s", old_preview, e)
                
                # Update the folder path in metadata
                animation.folder_path = new_folder_path
                
                # Verify the change
                updated_folder = getattr(animation, 'folder_path', 'Root')
                print(f"📁 LIBRARY: Folder path updated to: '{updated_folder}'")
                
                # Save changes
                self.save_library()
                
                logger.info("📁 Moved animation %s from '%s' to '%s'", animation_id, old_folder, new_folder_path)
                return True
            else:
                print(f"❌ LIBRARY: Animation {animation_id} not found")
                logger.warning("Animation %s not found", animation_id)
                return False
                
        except Exception as e:
            print(f"❌ LIBRARY: Failed to move animation {animation_id}: {e}")
            logger.error("Failed to move animation %s: %s", animation_id, e)
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
            # Prepare metadata for serialization (convert sets to lists)
            serializable_metadata = self.library_metadata.copy()
            if 'tags' in serializable_metadata and isinstance(serializable_metadata['tags'], set):
                serializable_metadata['tags'] = list(serializable_metadata['tags'])
            if 'rig_types' in serializable_metadata and isinstance(serializable_metadata['rig_types'], set):
                serializable_metadata['rig_types'] = list(serializable_metadata['rig_types'])
            
            # Prepare data for serialization
            library_data = {
                "metadata": serializable_metadata,
                "animations": {
                    anim_id: anim.to_dict() 
                    for anim_id, anim in self.animations.items()
                }
            }
            
            # Write to temporary file first
            temp_file = self.metadata_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(library_data, f, indent=2)
            
            # Atomic replace
            temp_file.replace(self.metadata_file)
            
            # No longer saving folder structure - using file system
            
            blend_count = len(self.get_blend_file_animations())
            legacy_count = len(self.get_legacy_animations())
            logger.info("💾 Saved library: %d .blend + %d JSON animations", blend_count, legacy_count)
            return True
            
        except Exception as e:
            logger.error("Failed to save library: %s", e)
            return False
    
    def load_library(self) -> bool:
        """Load library from disk with .blend file path resolution"""
        try:
            if not self.metadata_file.exists():
                logger.info("No existing library found, starting with empty library")
                
                # IMPORTANT: Even for new library, check for existing .blend files
                imported_count = self.detect_and_import_existing_blend_files()
                if imported_count > 0:
                    logger.info("📁 Auto-imported %d existing .blend files", imported_count)
                
                return True
            
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
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
                    logger.warning("Failed to load animation %s: %s", anim_id, e)
            
            # No longer loading folder structure - using file system scanning
            
            logger.info("📚 Loaded library: %d .blend + %d JSON animations", blend_count, legacy_count)
            
            # IMPORTANT: Detect and import any existing .blend files that aren't in metadata
            imported_count = self.detect_and_import_existing_blend_files()
            if imported_count > 0:
                logger.info("📁 Auto-imported %d existing .blend files", imported_count)
            
            return True
            
        except Exception as e:
            logger.error("Failed to load library: %s", e)
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
        """Remove files associated with an animation - UPDATED FOR NEW FOLDER STRUCTURE"""
        print(f"🔍 DEBUG: Removing files for animation: {animation.id}")
        print(f"🔍 DEBUG: Animation folder_path: {animation.folder_path}")
        
        if animation.is_blend_file_storage() and animation.blend_reference:
            # NEW: Remove .blend file from animations/folder_path/ structure
            folder_path = animation.folder_path or "Root"
            blend_path = self.animations_folder / folder_path / animation.blend_reference.blend_file
            print(f"🔍 DEBUG: Attempting to remove .blend file: {blend_path}")
            print(f"🔍 DEBUG: .blend file exists: {blend_path.exists()}")
            
            if blend_path.exists():
                try:
                    blend_path.unlink()
                    print(f"✅ DEBUG: Removed .blend file: {blend_path.name}")
                    logger.info(f"🗑️ Removed .blend file: {blend_path.name}")
                except Exception as e:
                    print(f"❌ DEBUG: Failed to remove .blend file: {e}")
                    logger.error(f"Failed to remove .blend file {blend_path}: {e}")
            else:
                # Fallback: Try legacy actions folder for migration support
                legacy_blend_path = self.actions_folder / animation.blend_reference.blend_file
                print(f"🔍 DEBUG: Fallback - trying legacy path: {legacy_blend_path}")
                if legacy_blend_path.exists():
                    try:
                        legacy_blend_path.unlink()
                        print(f"✅ DEBUG: Removed legacy .blend file: {legacy_blend_path.name}")
                        logger.info(f"🗑️ Removed legacy .blend file: {legacy_blend_path.name}")
                    except Exception as e:
                        print(f"❌ DEBUG: Failed to remove legacy .blend file: {e}")
        
        # Remove legacy clip file if it exists
        clip_file = self.clips_folder / f"{animation.id}.blend"
        print(f"🔍 DEBUG: Checking legacy clip file: {clip_file}")
        if clip_file.exists():
            try:
                clip_file.unlink()
                print(f"✅ DEBUG: Removed legacy clip file: {clip_file.name}")
            except Exception as e:
                print(f"❌ DEBUG: Failed to remove legacy clip file: {e}")
        
        # NEW: Remove preview file from previews/folder_path/ structure (updated from thumbnails)
        folder_path = animation.folder_path or "Root"
        preview_file = self.previews_folder / folder_path / f"{animation.id}.mp4"
        print(f"🔍 DEBUG: Attempting to remove preview file: {preview_file}")
        print(f"🔍 DEBUG: Preview file exists: {preview_file.exists()}")
        
        if preview_file.exists():
            try:
                preview_file.unlink()
                print(f"✅ DEBUG: Removed preview file: {preview_file.name}")
                logger.info(f"🗑️ Removed preview file: {preview_file.name}")
            except Exception as e:
                print(f"❌ DEBUG: Failed to remove preview file: {e}")
                logger.error(f"Failed to remove preview file {preview_file}: {e}")
        else:
            # Fallback: Try legacy thumbnail file for migration support
            legacy_thumbnail_file = self.previews_folder / f"{animation.id}.png"
            print(f"🔍 DEBUG: Fallback - trying legacy thumbnail: {legacy_thumbnail_file}")
            if legacy_thumbnail_file.exists():
                try:
                    legacy_thumbnail_file.unlink()
                    print(f"✅ DEBUG: Removed legacy thumbnail file: {legacy_thumbnail_file.name}")
                    logger.info(f"🗑️ Removed legacy thumbnail file: {legacy_thumbnail_file.name}")
                except Exception as e:
                    print(f"❌ DEBUG: Failed to remove legacy thumbnail file: {e}")
        
        print(f"🔍 DEBUG: File removal complete for animation: {animation.id}")
    
    def detect_and_import_existing_blend_files(self) -> int:
        """Detect existing .blend files in animations folder and add them to library"""
        imported_count = 0
        
        try:
            # Scan all folders in animations directory
            if not self.animations_folder.exists():
                return 0
                
            for folder_path in self.animations_folder.iterdir():
                if not folder_path.is_dir():
                    continue
                    
                folder_name = folder_path.name
                
                # Look for .blend files in this folder
                for blend_file in folder_path.glob("*.blend"):
                    blend_filename = blend_file.name
                    animation_id = blend_filename.replace(".blend", "")
                    
                    # Check if this animation is already in the library
                    if animation_id in self.animations:
                        continue
                        
                    # Create animation metadata from .blend file
                    try:
                        # Create basic metadata for existing .blend file
                        animation = AnimationMetadata(
                            id=animation_id,
                            name=animation_id.replace("_", " "),
                            description="Imported from existing .blend file",
                            armature_source="Unknown",
                            frame_range=(1, 100),  # Default frame range
                            total_bones_animated=1,
                            total_keyframes=1,
                            bone_data={},
                            rig_type="unknown",
                            folder_path=folder_name,
                            blend_reference=BlendFileReference(
                                blend_file=blend_filename,
                                blend_action_name="Unknown",
                                file_path=blend_file
                            )
                        )
                        
                        # Add to library
                        self.animations[animation_id] = animation
                        imported_count += 1
                        
                        logger.info("📁 Imported existing .blend file: %s from folder %s", 
                                  blend_filename, folder_name)
                        
                    except Exception as e:
                        logger.warning("Failed to import .blend file %s: %s", blend_filename, e)
            
            if imported_count > 0:
                self._update_library_metadata()
                self.save_library()
                logger.info("📚 Imported %d existing .blend files", imported_count)
                
        except Exception as e:
            logger.error("Failed to detect existing .blend files: %s", e)
            
        return imported_count

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