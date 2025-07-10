#!/usr/bin/env python3
"""
Launch script for Animation Library GUI
Run this file to start the Animation Library application
"""

import sys
import os
from pathlib import Path

def setup_environment():
    """Setup the Python environment for the application"""
    # Get the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    
    # Add src directory to Python path
    src_path = script_dir / 'src'
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    print(f"Animation Library - Starting...")
    print(f"Script directory: {script_dir}")
    print(f"Source path: {src_path}")
    
    # Verify src directory exists
    if not src_path.exists():
        print(f"❌ ERROR: src directory not found at {src_path}")
        print("Please ensure you have the correct project structure.")
        sys.exit(1)
    
    # Check for required modules
    required_modules = [
        src_path / 'core' / 'animation_data.py',
        src_path / 'gui' / 'main.py',
    ]
    
    for module_path in required_modules:
        if not module_path.exists():
            print(f"❌ ERROR: Required module not found: {module_path}")
            sys.exit(1)
    
    print("✅ Environment setup complete")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import PySide6
        print(f"✅ PySide6 version: {PySide6.__version__}")
    except ImportError:
        print("❌ ERROR: PySide6 not installed")
        print("Please install it with: pip install PySide6")
        sys.exit(1)

def main():
    """Main entry point"""
    print("=" * 50)
    print("🎬 Animation Library - Professional Edition")
    print("=" * 50)
    
    # Setup environment
    setup_environment()
    
    # Check dependencies  
    check_dependencies()
    
    try:
        # Import and run the GUI
        from gui.main import main as gui_main
        print("🚀 Launching Animation Library GUI...")
        gui_main()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\nPlease check:")
        print("1. All required files are in the correct locations")
        print("2. All __init__.py files exist")
        print("3. The src directory structure is correct")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()