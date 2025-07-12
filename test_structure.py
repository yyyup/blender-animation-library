#!/usr/bin/env python3
"""
Test Blender addon import structure without requiring Blender
This tests the module structure and import chains
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock Blender modules before importing our code
print("🧪 Setting up Blender module mocks...")
sys.modules['bpy'] = MagicMock()
sys.modules['bpy.types'] = MagicMock()
sys.modules['bpy.props'] = MagicMock()
sys.modules['bpy.utils'] = MagicMock()
print("✅ Blender modules mocked")

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_import_structure():
    """Test that our import structure is correct"""
    print("\n🧪 Testing import structure...")
    
    try:
        # Test that we can import the preview operators
        print("   📦 Testing preview_ops from operators...")
        from blender_animation_library.operators.preview_ops import ANIMATIONLIBRARY_OT_update_preview
        print("   ✅ ANIMATIONLIBRARY_OT_update_preview imported from operators")
        
        print("   📦 Testing preview_ops from ops...")
        from blender_animation_library.ops.preview_ops import ANIMATIONLIBRARY_OT_update_preview as OpsPreview
        print("   ✅ ANIMATIONLIBRARY_OT_update_preview imported from ops")
        
        # Test that __init__ files can import correctly
        print("   📦 Testing operators __init__...")
        from blender_animation_library.operators import ANIMATIONLIBRARY_OT_update_preview as InitPreview
        print("   ✅ Preview operator available through operators __init__")
        
        print("   📦 Testing ops __init__...")
        from blender_animation_library.ops import ANIMATIONLIBRARY_OT_update_preview as OpsInitPreview
        print("   ✅ Preview operator available through ops __init__")
        
        # Verify no thumbnail_ops imports remain
        print("   🔍 Verifying no thumbnail_ops references...")
        
        # This should NOT work (thumbnail_ops should be gone)
        try:
            from blender_animation_library.operators import thumbnail_ops
            print("   ❌ ERROR: thumbnail_ops still exists in operators!")
            return False
        except ImportError:
            print("   ✅ thumbnail_ops correctly removed from operators")
        
        try:
            from blender_animation_library.ops import thumbnail_ops
            print("   ❌ ERROR: thumbnail_ops still exists in ops!")
            return False
        except ImportError:
            print("   ✅ thumbnail_ops correctly removed from ops")
        
        print("\n🎉 ALL STRUCTURE TESTS PASSED!")
        print("✅ Thumbnail to video preview migration is complete!")
        print("✅ Import structure is correct!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = test_import_structure()
    exit_code = 0 if success else 1
    print(f"\n🏁 Test {'PASSED' if success else 'FAILED'}")
    sys.exit(exit_code)
