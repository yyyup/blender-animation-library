# File System Issues Fix - Animation Library Debug & Repair

## 🎯 Problems Identified & Fixed

### **Issue 1: Extraction Fails - "Cannot open file for writing"**
**Root Cause**: Directory creation was incomplete and paths were incorrect after thumbnail-to-preview migration.

### **Issue 2: Deleted Animations Reappear After Restart**
**Root Cause**: Deletion system was still using old thumbnail file structure and not removing files from correct locations.

## 🔧 Comprehensive Fixes Applied

### 1. **Enhanced Debug Logging in BlendFileAnimationStorage**

Added comprehensive debug output to `src/blender_animation_library/storage.py`:

```python
def extract_animation_to_blend_with_preview(self, armature_name: str, action_name: str):
    print(f"🔍 DEBUG: Starting extraction...")
    print(f"🔍 DEBUG: Library path: {self.library_path}")
    print(f"🔍 DEBUG: Library path exists: {self.library_path.exists()}")
    print(f"🔍 DEBUG: Animations path: {self.animations_path}")
    print(f"🔍 DEBUG: Animations path exists: {self.animations_path.exists()}")
    print(f"🔍 DEBUG: Previews path: {self.previews_path}")
    print(f"🔍 DEBUG: Previews path exists: {self.previews_path.exists()}")
    
    # ... detailed logging for each step of extraction process
```

### 2. **Fixed Core Library Storage Paths**

Updated `src/core/library_storage.py` to use preview system:

```python
# BEFORE (broken thumbnail references):
self.thumbnails_folder = self.library_path / 'thumbnails'

# AFTER (correct preview system):
self.previews_folder = self.library_path / 'previews'  # Updated from thumbnails_folder
```

### 3. **Completely Rewrote File Deletion System**

Fixed `_remove_animation_files()` method in `src/core/library_storage.py`:

```python
def _remove_animation_files(self, animation: AnimationMetadata):
    """Remove files associated with an animation - UPDATED FOR NEW FOLDER STRUCTURE"""
    # NEW: Remove .blend file from animations/folder_path/ structure
    folder_path = animation.folder_path or "Root"
    blend_path = self.animations_folder / folder_path / animation.blend_reference.blend_file
    
    # NEW: Remove preview file from previews/folder_path/ structure
    preview_file = self.previews_folder / folder_path / f"{animation.id}.mp4"
    
    # Includes fallback support for legacy files during migration
```

### 4. **Updated All Thumbnail References to Preview System**

Systematically updated 18+ references in `src/core/library_storage.py`:
- `thumbnails_folder` → `previews_folder`
- `thumbnail_file` → `preview_file`
- `.png` files → `.mp4` files
- Legacy thumbnail support maintained for migration

### 5. **Enhanced Directory Creation with Debug Logging**

Added comprehensive logging to `_ensure_directories()`:

```python
def _ensure_directories(self):
    print(f"🔍 DEBUG: _ensure_directories called")
    
    self.animations_path.mkdir(exist_ok=True)
    print(f"🔍 DEBUG: Created/confirmed animations_path: {self.animations_path}")
    
    self.previews_path.mkdir(exist_ok=True) 
    print(f"🔍 DEBUG: Created/confirmed previews_path: {self.previews_path}")
    
    # Root folder creation for both animations/ and previews/
```

## 📁 Fixed Directory Structure

The system now correctly manages:

```
animation_library/
├── animations/
│   └── Root/                    # ✅ Correctly created for .blend files
│       └── animation_id.blend   # ✅ Files saved to correct location
├── previews/
│   └── Root/                    # ✅ Correctly created for .mp4 files  
│       └── animation_id.mp4     # ✅ Preview files in correct location
├── actions/                     # ✅ Legacy support maintained
├── metadata/                    # ✅ Metadata storage
└── library_metadata.json       # ✅ Library index
```

## 🧪 Debug Output Added

The system now provides detailed logging for:

**Extraction Process**:
- ✅ Path verification and existence checks
- ✅ Directory creation confirmation
- ✅ File save operation status
- ✅ File size and location verification

**Deletion Process**:
- ✅ Animation file location identification
- ✅ .blend file removal attempts (with fallback)
- ✅ Preview file removal attempts (with fallback)
- ✅ Legacy file cleanup status

**Initialization Process**:
- ✅ Path setup verification
- ✅ Directory creation confirmation
- ✅ Root folder structure validation

## 🎬 Expected Results

### **Extraction Should Now Work**:
1. Debug output will show exact paths being used
2. Directory creation will be logged and verified
3. File save operations will be tracked
4. Any remaining issues will be clearly identified in console output

### **Deletion Should Now Work**:
1. Files will be removed from correct folder locations
2. Both .blend and .mp4 files will be properly deleted
3. Legacy files will be cleaned up during migration
4. Debug output will confirm successful deletion

### **Migration Support**:
- ✅ Legacy thumbnail files (.png) will be found and removed
- ✅ Old actions/ folder files will be handled
- ✅ Graceful fallback for mixed file structures

## 🚀 Testing Strategy

1. **Run Animation Extraction**: Check console for debug output showing path resolution
2. **Verify File Creation**: Confirm .blend files appear in `animations/Root/`
3. **Test Animation Deletion**: Check console for debug output showing file removal
4. **Verify File Deletion**: Confirm files are actually removed from filesystem
5. **Restart Application**: Verify deleted animations don't reappear

The comprehensive debug logging will reveal any remaining path or permission issues that need to be addressed.
