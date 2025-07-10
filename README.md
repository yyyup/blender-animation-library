# 🎬 Blender Animation Library

> Professional animation library system that brings Maya's Studio Library functionality to Blender

A desktop application enabling animation teams to extract, store, search, and apply full animation sequences with intelligent bone mapping and real-time collaboration.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Blender](https://img.shields.io/badge/blender-3.0+-orange.svg)](https://www.blender.org/)

## 📁 Project Structure

```
blender-animation-library/
├── README.md                      # This file
├── LICENSE                        # MIT License
├── requirements.txt               # Python dependencies
├── setup.py                       # Package setup
├── .gitignore                     # Git ignore rules
│
├── src/                           # Source code
│   ├── __init__.py
│   ├── blender_addon/             # Blender add-on
│   │   ├── __init__.py
│   │   ├── animation_library_addon.py
│   │   └── operators/
│   │       ├── __init__.py
│   │       ├── extract.py
│   │       ├── apply.py
│   │       └── server.py
│   │
│   ├── gui/                       # Qt GUI application
│   │   ├── __init__.py
│   │   ├── main.py                # Main entry point
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── animation_card.py
│   │   │   ├── bone_mapping.py
│   │   │   └── connection_panel.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── blender_connection.py
│   │   │   └── library_manager.py
│   │   └── resources/
│   │       ├── icons/
│   │       ├── styles/
│   │       └── ui/
│   │
│   ├── core/                      # Shared core functionality
│   │   ├── __init__.py
│   │   ├── animation_data.py      # Animation data structures
│   │   ├── bone_mapping.py        # Bone mapping algorithms
│   │   ├── library_storage.py     # Library storage management
│   │   └── communication.py       # Socket communication protocol
│   │
│   └── utils/                     # Utility functions
│       ├── __init__.py
│       ├── file_utils.py
│       ├── json_utils.py
│       └── validation.py
│
├── tests/                         # Test files
│   ├── __init__.py
│   ├── test_blender_addon.py
│   ├── test_gui.py
│   ├── test_core.py
│   └── fixtures/
│       ├── test_animations.json
│       └── test_rigs.blend
│
├── docs/                          # Documentation
│   ├── installation.md
│   ├── user_guide.md
│   ├── api_reference.md
│   ├── development.md
│   └── screenshots/
│
├── examples/                      # Example files
│   ├── sample_animations/
│   ├── rig_templates/
│   └── scripts/
│
└── tools/                         # Development tools
    ├── build_addon.py             # Build Blender add-on
    ├── generate_thumbnails.py
    └── migrate_library.py
```

## 🚀 Quick Start

### Prerequisites
```bash
# Required software
Blender 3.0+
Python 3.8+

# Python dependencies
pip install -r requirements.txt
```

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/blender-animation-library.git
   cd blender-animation-library
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Blender Add-on**:
   ```bash
   # Copy add-on to Blender
   python tools/build_addon.py
   
   # Or manually:
   # Copy src/blender_addon/ to your Blender add-ons folder
   # Enable "Animation Library Socket Server" in Blender preferences
   ```

4. **Run the GUI**:
   ```bash
   python src/gui/main.py
   ```

### Usage

1. **Start Blender** with the add-on enabled
2. **Launch the GUI application**
3. **Connect to Blender** (status indicator turns green)
4. **Extract animations** from your rigged characters
5. **Apply animations** to different rigs with bone mapping

## ✨ Current Features (MVP)

### 🎨 **Professional Interface**
- [x] Dark themed Qt desktop application
- [x] Real-time connection status with Blender
- [x] Animation cards with metadata display
- [x] Advanced search and filtering

### 🎭 **Animation Management**
- [x] Extract full animation sequences (F-curves)
- [x] Store animations with rich metadata
- [x] Apply animations with exact reproduction
- [x] Smart auto-tagging system

### 🔄 **Real-time Collaboration**
- [x] Live bone selection synchronization
- [x] Socket-based communication protocol
- [x] Professional error handling

### ⚙️ **Apply Options**
- [x] Visual bone mapping interface
- [x] Selected bones only application
- [x] Frame offset control
- [x] Channel selection (Location/Rotation/Scale)

## 🎯 Development Status

### ✅ **Completed (MVP)**
- Core socket communication architecture
- Basic animation extraction and application
- Professional Qt GUI with dark theme
- JSON-based library storage
- Smart animation tagging system

### 🔄 **In Progress (Refactoring Phase)**
- [ ] Clean debug output removal
- [ ] Implement selected bones only logic
- [ ] Channel selection functionality
- [ ] Bone mapping integration
- [ ] Professional error handling

### 📋 **Next Phase (Advanced Features)**
- [ ] Animation thumbnail generation
- [ ] Drag & drop bone mapping
- [ ] Batch operations
- [ ] Export/import library
- [ ] Animation preview system

## 🛠️ Development

### Setting up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/blender-animation-library.git
cd blender-animation-library

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_core.py

# Run with coverage
python -m pytest --cov=src tests/
```

### Building Add-on

```bash
# Build Blender add-on
python tools/build_addon.py

# Install to Blender
python tools/build_addon.py --install
```

## 📊 Architecture

### System Overview
```
┌─────────────────────┐    HTTP Socket    ┌─────────────────────┐
│   Qt Desktop GUI   │ ◄─────────────► │  Blender Add-on     │
│                     │  JSON Protocol   │                     │
│ - Animation Browser │                  │ - Socket Server     │
│ - Bone Mapping      │                  │ - F-curve Extraction│
│ - Real-time Sync    │                  │ - Selection Monitor │
└─────────────────────┘                  └─────────────────────┘
          │                                        │
          ▼                                        ▼
┌─────────────────────┐                  ┌─────────────────────┐
│   Library Storage   │                  │    Blender Scene    │
│                     │                  │                     │
│ - JSON Metadata     │                  │ - Armatures & Rigs  │
│ - Animation Data    │                  │ - Animation Actions │
│ - Bone Mappings     │                  │ - Real-time Data    │
│ - Search Index      │                  │ - Selection State   │
└─────────────────────┘                  └─────────────────────┘
```

### Communication Protocol
```json
{
  "command": "extract_animation",
  "data": {
    "selected_bones_only": true,
    "channels": ["location", "rotation"],
    "frame_range": [1, 30]
  }
}
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/development.md) for details.

### Key Areas for Contribution:
1. **Core Features**: Selected bones logic, channel selection
2. **UI/UX**: Better visual design and user experience
3. **Performance**: Large library handling optimization
4. **Documentation**: Tutorials, examples, API docs
5. **Testing**: Unit tests, integration tests

### Development Workflow:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python -m pytest`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by Maya's Studio Library
- Built for the Blender animation community
- Designed for professional animation workflows

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/blender-animation-library/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/blender-animation-library/discussions)
- **Wiki**: [Project Wiki](https://github.com/yourusername/blender-animation-library/wiki)

---

**Current Status**: 🔄 MVP Complete - Refactoring Phase  
**Next Milestone**: 🎯 Production-Ready Core Features  
**Goal**: 🚀 Professional Animation Library for Blender Teams

### Recent Updates
- ✅ Socket communication working reliably
- ✅ Animation extraction and application functional
- ✅ Professional Qt GUI with dark theme
- 🔄 Refactoring apply options and bone mapping
- 📋 Next: Clean architecture and advanced features