#!/usr/bin/env python3
"""
Quick test to verify Blender addon can import successfully
Tests if we've successfully removed all thumbnail_ops references
"""

import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_blender_addon_imports():
    """Test that Blender addon components can be imported"""
    print("🧪 Testing Blender Animation Library imports...")
    
    try:
        # Test main addon package
        print("   📦 Testing main addon package...")
        import blender_animation_library
        print("   ✅ Main package imported successfully")
        
        # Test operators package
        print("   📦 Testing operators package...")
        from blender_animation_library import operators
        print("   ✅ Operators package imported successfully")
        
        # Test ops package  
        print("   📦 Testing ops package...")
        from blender_animation_library import ops
        print("   ✅ Ops package imported successfully")
        
        # Test preview_ops specifically
        print("   📦 Testing preview_ops...")
        from blender_animation_library.operators import preview_ops
        print("   ✅ Preview ops imported successfully")
        
        from blender_animation_library.ops import preview_ops as ops_preview
        print("   ✅ Ops preview imported successfully")
        
        print("\n🎉 ALL IMPORTS SUCCESSFUL!")
        print("✅ Thumbnail migration complete - no import errors!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("💡 This indicates missing thumbnail_ops references may still exist")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = test_blender_addon_imports()
    exit_code = 0 if success else 1
    sys.exit(exit_code)
