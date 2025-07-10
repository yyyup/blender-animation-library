# 🚀 Animation Library - Setup Instructions

## Quick Start Guide

### Step 1: Install Dependencies

```bash
pip install PySide6
```

### Step 2: Create Project Structure

Create this folder structure:

```
animation-library/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── animation_data.py
│   │   ├── communication.py
│   │   └── library_storage.py
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── blender_connection.py
│   │   └── widgets/
│   │       ├── __init__.py
│   │       ├── animation_card.py
│   │       └── bone_mapping.py
│   └── blender_addon/
│       ├── __init__.py
│       └── animation_library_addon.py
├── requirements.txt
└── run_gui.py
```

### Step 3: Create Empty __init__.py Files

Create empty `__init__.py` files in each folder:

```bash
# Windows
type nul > src\__init__.py
type nul > src\core\__init__.py
type nul > src\gui\__init__.py
type nul > src\gui\utils\__init__.py
type nul > src\gui\widgets\__init__.py
type nul > src\blender_addon\__init__.py

# Mac/Linux
touch src/__init__.py
touch src/core/__init__.py
touch src/gui/__init__.py
touch src/gui/utils/__init__.py
touch src/gui/widgets/__init__.py
touch src/blender_addon/__init__.py
```

### Step 4: Copy the Code Files

Copy each code file I provided into the correct location:

1. **Core files:**
   - `animation_data.py` → `src/core/animation_data.py`
   - `communication.py` → `src/core/communication.py` 
   - `library_storage.py` → `src/core/library_storage.py`

2. **GUI files:**
   - `main.py` → `src/gui/main.py`
   - `blender_connection.py` → `src/gui/utils/blender_connection.py`
   - `animation_card.py` → `src/gui/widgets/animation_card.py`
   - `bone_mapping.py` → `src/gui/widgets/bone_mapping.py`

3. **Blender add-on:**
   - `animation_library_addon.py` → `src/blender_addon/animation_library_addon.py`

### Step 5: Create Launch Script

Create `run_gui.py` in the root folder:

```python
#!/usr/bin/env python3
"""
Launch script for Animation Library GUI
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Launch the GUI
from gui.main import main

if __name__ == "__main__":
    main()
```

### Step 6: Install Blender Add-on

1. **Copy** `src/blender_addon/animation_library_addon.py` to your Blender add-ons folder
2. **In Blender**: Edit → Preferences → Add-ons → Enable "Animation Library Socket Server"

### Step 7: Run the System

1. **Start Blender** with the add-on enabled
2. **In Blender**: Open sidebar (N key) → Animation Library tab → "Start Animation Library Server"
3. **Run the GUI**:
   ```bash
   python run_gui.py
   ```
4. **Click "Connect to Blender"** in the GUI

## ✅ Success Indicators

You should see:
- ✅ GUI opens with professional dark theme
- ✅ "Connect to Blender" button turns to "Disconnect" 
- ✅ Status shows "Connected" in green
- ✅ Current selection updates when you select bones in Blender
- ✅ "Extract Animation" works and creates animation cards
- ✅ "Apply" on cards transfers animations properly

## 🔧 Troubleshooting

**Import Errors?**
- Make sure all `__init__.py` files exist
- Check that `src` folder is in the right place
- Verify Python path in `run_gui.py`

**Connection Issues?**
- Ensure Blender server is started
- Check port 8080 isn't blocked
- Look at Blender console for error messages

**Missing Dependencies?**
```bash
pip install --upgrade PySide6
```

## 🎯 Quick Test

1. **In Blender**: Select an armature, go to Pose Mode, select some bones
2. **In GUI**: Should show current selection in real-time
3. **Create animation** in Blender, click "Extract Animation"
4. **Apply animation** by clicking "Apply" on the card

You now have a fully professional animation library system! 🚀