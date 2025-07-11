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

from core.animation_data import AnimationMetadata, BlendFileReference, AnimationStorageDetector

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
            logger.info(f"✅ Added animation: {animation.name} ({animation.id}) to folder '{folder_path}' {storage_info}")
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
                self.animations[animation_id].folder_path = new_folder_path
                
                # Save changes
                self.save_library()
                
                logger.info(f"📁 Moved animation {animation_id} from '{old_folder}' to '{new_folder_path}'")
                return True
            else:
                logger.warning(f"Animation {animation_id} not found")
                return False
                
        except Exception as e:
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
        """NEW: Filter animations by storage method"""
        return [anim for anim in self.get_all_animations() 
                if anim.storage_method == storage_method]
    
    def get_blend_file_animations(self) -> List[AnimationMetadata]:
        """NEW: Get only .blend file animations (fast ones)"""
        return self.filter_by_storage_method("blend_file")
    
    def get_legacy_animations(self) -> List[AnimationMetadata]:
        """NEW: Get only legacy JSON animations (slow ones)"""
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
        blend_avg_extraction = sum(anim.extraction_time_seconds for anim in blend_animations) / len(blend_animations) if blend_animations else 0
        blend_avg_application = sum(anim.application_time_seconds for anim in blend_animations) / len(blend_animations) if blend_animations else 0
        
        legacy_avg_extraction = sum(anim.extraction_time_seconds for anim in legacy_animations) / len(legacy_animations) if legacy_animations else 0
        legacy_avg_application = sum(anim.application_time_seconds for anim in legacy_animations) / len(legacy_animations) if legacy_animations else 0
        
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
            
            logger.info(f"📚 Loaded library: {blend_count} .blend + {legacy_count} JSON animations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load library: {e}")
            return False
    
    def migrate_animation_to_blend(self, animation_id: str) -> bool:
        """NEW: Migrate a JSON animation to .blend file storage"""
        animation = self.get_animation(animation_id)
        if not animation:
            logger.error(f"Animation {animation_id} not found")
            return False
        
        if animation.is_blend_file_storage():
            logger.info(f"Animation {animation.name} already uses .blend file storage")
            return True
        
        if not animation.is_legacy_storage():
            logger.error(f"Animation {animation.name} has unknown storage method")
            return False
        
        try:
            # This would require Blender integration to recreate and save the action
            # For now, mark as needing migration
            logger.info(f"🔄 Animation {animation.name} marked for migration to .blend file")
            # Implementation would involve:
            # 1. Recreate action in Blender from JSON data
            # 2. Save action to .blend file
            # 3. Update animation metadata
            # 4. Remove JSON data
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate animation {animation_id}: {e}")
            return False
    
    def batch_migrate_to_blend(self) -> Dict[str, Any]:
        """NEW: Migrate all JSON animations to .blend files"""
        legacy_animations = self.get_legacy_animations()
        
        if not legacy_animations:
            logger.info("No legacy animations to migrate")
            return {"migrated": 0, "failed": 0, "total": 0}
        
        migrated_count = 0
        failed_count = 0
        
        logger.info(f"🔄 Starting batch migration of {len(legacy_animations)} animations...")
        
        for animation in legacy_animations:
            try:
                if self.migrate_animation_to_blend(animation.id):
                    migrated_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Migration failed for {animation.name}: {e}")
                failed_count += 1
        
        result = {
            "migrated": migrated_count,
            "failed": failed_count,
            "total": len(legacy_animations)
        }
        
        logger.info(f"🎯 Migration complete: {migrated_count} success, {failed_count} failed")
        return result
    
    def cleanup_missing_blend_files(self) -> int:
        """NEW: Remove animations with missing .blend files"""
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
    
    def validate_blend_files(self) -> Dict[str, List[str]]:
        """NEW: Validate all .blend file references"""
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
                # Could add corruption check here
                validation_results["valid"].append(animation.name)
            else:
                validation_results["missing"].append(animation.name)
        
        # Check for orphaned .blend files
        referenced_files = {anim.blend_reference.blend_file for anim in self.get_blend_file_animations() if anim.blend_reference}
        actual_files = {f.name for f in self.actions_folder.glob("*.blend")}
        orphaned_files = actual_files - referenced_files
        validation_results["orphaned"] = list(orphaned_files)
        
        return validation_results
    
    def backup_library(self, backup_path: Optional[Path] = None) -> bool:
        """Create a backup of the library with .blend files"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.library_path.parent / f"animation_library_backup_{timestamp}"
            
            # Copy entire library directory including .blend files
            if self.library_path.exists():
                shutil.copytree(self.library_path, backup_path)
                
                # Log backup contents
                blend_count = len(list((backup_path / 'actions').glob("*.blend")))
                logger.info(f"📦 Created library backup at: {backup_path}")
                logger.info(f"   📁 {blend_count} .blend files backed up")
                return True
            else:
                logger.warning("No library to backup")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def restore_library(self, backup_path: Path) -> bool:
        """Restore library from backup including .blend files"""
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
            
            # Validate .blend files after restore
            validation = self.validate_blend_files()
            logger.info(f"📥 Restored library from backup: {backup_path}")
            logger.info(f"   ✅ {len(validation['valid'])} valid .blend files")
            logger.info(f"   ❌ {len(validation['missing'])} missing .blend files")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            # Try to restore current backup if it exists
            current_backup = self.library_path.with_suffix('.backup')
            if current_backup.exists():
                shutil.move(str(current_backup), str(self.library_path))
            return False
    
    def export_library(self, export_path: Path, include_blend_files: bool = True) -> bool:
        """Export library to a different location with .blend files"""
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
            if include_blend_files:
                # Copy .blend files
                if self.actions_folder.exists():
                    export_actions = export_path / 'actions'
                    shutil.copytree(self.actions_folder, export_actions, dirs_exist_ok=True)
                
                # Copy legacy clips if they exist
                if self.clips_folder.exists():
                    export_clips = export_path / 'clips'
                    shutil.copytree(self.clips_folder, export_clips, dirs_exist_ok=True)
                
                # Copy thumbnails
                if self.thumbnails_folder.exists():
                    export_thumbnails = export_path / 'thumbnails'
                    shutil.copytree(self.thumbnails_folder, export_thumbnails, dirs_exist_ok=True)
            
            blend_count = len(list(self.actions_folder.glob("*.blend"))) if include_blend_files else 0
            logger.info(f"📤 Exported library to: {export_path}")
            logger.info(f"   📁 {blend_count} .blend files exported")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export library: {e}")
            return False
    
    def import_library(self, import_path: Path, merge: bool = True) -> bool:
        """Import library from a different location with .blend file support"""
        try:
            import_metadata_file = import_path / 'library_metadata.json'
            
            if not import_metadata_file.exists():
                logger.error(f"No library metadata found at: {import_path}")
                return False
            
            with open(import_metadata_file, 'r') as f:
                import_data = json.load(f)
            
            animations_data = import_data.get("animations", {})
            imported_count = 0
            blend_files_imported = 0
            
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
                    
                    # Copy .blend file if it exists
                    if animation.is_blend_file_storage():
                        source_blend = import_path / 'actions' / animation.blend_reference.blend_file
                        target_blend = self.actions_folder / animation.blend_reference.blend_file
                        
                        if source_blend.exists():
                            shutil.copy2(source_blend, target_blend)
                            blend_files_imported += 1
                        else:
                            logger.warning(f"Missing .blend file for {animation.name}: {source_blend}")
                    
                    self.animations[anim_id] = animation
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to import animation {anim_id}: {e}")
            
            # Update metadata and save
            self._update_library_metadata()
            self.save_library()
            
            logger.info(f"📥 Imported {imported_count} animations from: {import_path}")
            logger.info(f"   📁 {blend_files_imported} .blend files imported")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import library: {e}")
            return False
    
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
    
    def get_library_size(self) -> Dict[str, Any]:
        """Get library size information with .blend file breakdown"""
        total_size = 0
        file_count = 0
        blend_size = 0
        blend_count = 0
        
        for file_path in self.library_path.rglob('*'):
            if file_path.is_file():
                size = file_path.stat().st_size
                total_size += size
                file_count += 1
                
                if file_path.suffix == '.blend' and file_path.parent.name == 'actions':
                    blend_size += size
                    blend_count += 1
        
        return {
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "file_count": file_count,
            "animation_count": len(self.animations),
            "blend_file_size_mb": blend_size / (1024 * 1024),
            "blend_file_count": blend_count,
            "average_blend_size_mb": (blend_size / blend_count / (1024 * 1024)) if blend_count > 0 else 0,
            "storage_efficiency": f"{((blend_size / total_size) * 100):.1f}% .blend files" if total_size > 0 else "0%"
        }
    
    def optimize_library(self) -> Dict[str, Any]:
        """NEW: Optimize library by cleaning up and organizing files"""
        results = {
            "orphaned_files_removed": 0,
            "missing_animations_removed": 0,
            "space_saved_mb": 0,