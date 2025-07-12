# Fixed library_storage.py - Clean folder creation without emoji pollution

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AnimationLibraryManager:
    """Fixed library manager with clean folder creation"""
    
    def __init__(self, library_path: Optional[Path] = None):
        self.library_path = library_path or Path('./animation_library')
        self.folders_file = self.library_path / 'folders.json'
        self.folder_structure = self._load_folder_structure()
        
        # Ensure directories exist
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        self.library_path.mkdir(exist_ok=True)
        
    def _load_folder_structure(self) -> Dict[str, Any]:
        """Load folder structure from disk"""
        if self.folders_file.exists():
            try:
                with open(self.folders_file, 'r', encoding='utf-8') as f:
                    structure = json.load(f)
                    return structure
            except Exception as e:
                logger.warning(f"Failed to load folder structure: {e}")
                
        # Default structure
        return {
            "Custom Folders": {
                "type": "category",
                "children": {}
            }
        }
        
    def _save_folder_structure(self):
        """Save folder structure to disk"""
        try:
            with open(self.folders_file, 'w', encoding='utf-8') as f:
                json.dump(self.folder_structure, f, indent=2, ensure_ascii=False)
            logger.info(f"📁 Saved folder structure to {self.folders_file}")
        except Exception as e:
            logger.error(f"Failed to save folder structure: {e}")
            
    def create_folder(self, folder_path: str) -> bool:
        """Create a new folder with clean naming (no emoji pollution)"""
        try:
            # Clean the folder path (remove any emoji artifacts)
            clean_path = self._clean_folder_path(folder_path)
            
            if not clean_path:
                logger.error("Empty folder path after cleaning")
                return False
                
            # Check if folder already exists
            if self._folder_exists(clean_path):
                logger.warning(f"Folder already exists: {clean_path}")
                return False
                
            # Get custom folders section
            custom_folders = self.folder_structure["Custom Folders"]["children"]
            
            # Create folder entry with CLEAN naming
            folder_key = clean_path  # Store as plain text, no emoji prefixes!
            custom_folders[folder_key] = {
                "type": "folder",
                "filter": f"folder:{clean_path}",
                "count": 0
            }
            
            # Save to disk
            self._save_folder_structure()
            
            logger.info(f"📁 Created folder: {clean_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create folder {folder_path}: {e}")
            return False
            
    def _clean_folder_path(self, folder_path: str) -> str:
        """Clean folder path of any emoji or Unicode artifacts"""
        if not folder_path:
            return ""
            
        # Remove common emoji prefixes that might be added
        clean = folder_path.strip()
        
        # Remove emoji prefixes
        prefixes_to_remove = ["📁 ", "🧪 ", "🗂️ ", "📂 "]
        for prefix in prefixes_to_remove:
            clean = clean.replace(prefix, "")
            
        # Remove any problematic Unicode characters (keep only basic Latin + common chars)
        # Allow: letters, numbers, spaces, /, -, _, ()
        allowed_chars = []
        for char in clean:
            if (char.isalnum() or 
                char in " /-_()." or 
                (ord(char) < 256 and char.isprintable())):
                allowed_chars.append(char)
                
        clean = ''.join(allowed_chars).strip()
        
        # Replace multiple spaces/slashes with single ones
        import re
        clean = re.sub(r'\s+', ' ', clean)
        clean = re.sub(r'/+', '/', clean)
        
        # Remove leading/trailing slashes
        clean = clean.strip('/')
        
        return clean
        
    def _folder_exists(self, folder_path: str) -> bool:
        """Check if a folder already exists"""
        custom_folders = self.folder_structure["Custom Folders"]["children"]
        
        # Check exact match
        if folder_path in custom_folders:
            return True
            
        # Check for existing folders with similar paths (case insensitive)
        folder_path_lower = folder_path.lower()
        for existing_key in custom_folders.keys():
            if existing_key.lower() == folder_path_lower:
                return True
                
        return False
        
    def delete_folder(self, folder_path: str) -> bool:
        """Delete a folder and move its animations to Root"""
        try:
            clean_path = self._clean_folder_path(folder_path)
            
            # Find the folder in structure
            custom_folders = self.folder_structure["Custom Folders"]["children"]
            
            folder_key = None
            for key in custom_folders.keys():
                if self._clean_folder_path(key) == clean_path:
                    folder_key = key
                    break
                    
            if not folder_key:
                logger.warning(f"Folder not found for deletion: {clean_path}")
                return False
                
            # Remove from structure
            del custom_folders[folder_key]
            
            # Save changes
            self._save_folder_structure()
            
            logger.info(f"🗑️ Deleted folder: {clean_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete folder {folder_path}: {e}")
            return False
            
    def get_folder_structure(self) -> Dict[str, Any]:
        """Get the current folder structure"""
        return self.folder_structure.copy()
        
    def load_library(self) -> bool:
        """Load animation library from disk"""
        try:
            # Create metadata file if it doesn't exist
            if not self.library_path.exists():
                self.library_path.mkdir(parents=True, exist_ok=True)
                
            if not self.folders_file.exists():
                # Create empty folder structure
                self._save_folder_structure()
                logger.info("📚 No existing library found, starting with empty library")
                return True
            
            # Load existing folder structure
            self.folder_structure = self._load_folder_structure()
            
            logger.info("📚 Loaded library successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load library: {e}")
            return False
            
    def save_library(self) -> bool:
        """Save library to disk"""
        try:
            self._save_folder_structure()
            logger.info("💾 Saved library successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save library: {e}")
            return False
            
    def get_all_animations(self) -> list:
        """Get all animations - placeholder for compatibility"""
        # This would normally return actual animation objects
        # For now, return empty list to prevent crashes
        return []
        
    def get_animation(self, animation_id: str):
        """Get a specific animation - placeholder for compatibility"""
        # This would normally return an animation object
        return None
        
    def get_folder_statistics(self) -> Dict[str, Dict[str, int]]:
        """Get statistics for each folder"""
        # This would be implemented based on your animation storage
        # For now, return empty stats
        stats = {}
        
        custom_folders = self.folder_structure["Custom Folders"]["children"]
        for folder_key in custom_folders.keys():
            clean_path = self._clean_folder_path(folder_key)
            stats[clean_path] = {
                "total": 0,
                "blend_files": 0,
                "json_files": 0
            }
            
        return stats
        
    def move_animation_to_folder(self, animation_id: str, target_folder: str) -> bool:
        """Move an animation to a different folder"""
        # This would be implemented based on your animation storage system
        logger.info(f"📦 Moving animation {animation_id} to folder {target_folder}")
        return True
        
    def clean_existing_folder_structure(self):
        """Clean up existing folder structure from emoji pollution"""
        try:
            custom_folders = self.folder_structure["Custom Folders"]["children"]
            cleaned_folders = {}
            
            for folder_key, folder_data in custom_folders.items():
                # Clean the folder key
                clean_key = self._clean_folder_path(folder_key)
                
                if clean_key and clean_key not in cleaned_folders:
                    # Update filter to clean format
                    folder_data["filter"] = f"folder:{clean_key}"
                    cleaned_folders[clean_key] = folder_data
                    
            # Replace with cleaned structure
            self.folder_structure["Custom Folders"]["children"] = cleaned_folders
            
            # Save cleaned structure
            self._save_folder_structure()
            
            logger.info(f"🧹 Cleaned folder structure: {len(cleaned_folders)} folders")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clean folder structure: {e}")
            return False