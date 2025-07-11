# Copilot Project Instructions

## Project Purpose
A professional modular animation library for Blender, inspired by Maya Studio Library, designed to:
- Extract, store, and apply full animation sequences with **real-time thumbnail system**
- Provide a modular Studio Library-like GUI with **3-panel layout**
- Optimize performance using native `.blend` file storage for **instant application** (0.5s vs 60s)
- Support **real-time thumbnail updates** with viewport capture and aggressive cache clearing

## Current Project Status
✅ **PRODUCTION-READY**: Professional .blend file storage with instant animation application  
✅ **MODULAR ARCHITECTURE**: Component-based development with Studio Library interface  
✅ **REAL-TIME THUMBNAILS**: Complete thumbnail system with viewport capture and instant updates  
✅ **PROFESSIONAL ADD-ON**: Modular Blender add-on with development workflow  
🚧 **ENHANCING**: AI-powered features and cross-platform export

## Folder Structure Overview
```
src/
├── blender_animation_library/     # ✅ COMPLETE: Professional Blender add-on
│   ├── __init__.py               # Package entry with bl_info
│   ├── operators.py              # ✅ Thumbnail capture with multiple fallback methods
│   ├── ui.py                     # Professional multi-panel UI
│   ├── server.py                 # ✅ Real-time communication with thumbnail updates
│   ├── storage.py                # Professional .blend file storage
│   └── preferences.py            # Professional preferences
├── gui/                          # ✅ COMPLETE: Modular Qt GUI (Studio Library style)
│   ├── main.py                   # ✅ Clean main window with thumbnail coordination
│   ├── layouts/                  # ✅ Layout management system
│   │   └── studio_layout.py      # 3-panel Studio Library layout
│   ├── widgets/                  # ✅ Reusable UI components
│   │   ├── animation_card.py     # ✅ Real-time thumbnail refresh system
│   │   ├── bone_mapping.py       # Advanced bone mapping with auto-detection
│   │   ├── folder_tree.py        # Hierarchical folder navigation
│   │   ├── metadata_panel.py     # ✅ Large preview with "Update Thumbnail" button
│   │   └── toolbar.py           # Professional search & filter controls
│   └── utils/
│       ├── blender_connection.py # ✅ Enhanced with thumbnail update communication
│       └── library_manager.py
├── core/                         # ✅ Enhanced .blend file ecosystem
│   ├── animation_data.py         # ✅ Enhanced with thumbnail metadata support
│   ├── bone_mapping.py           # Intelligent bone mapping algorithms
│   ├── library_storage.py        # ✅ Thumbnail-aware storage management
│   └── communication.py          # ✅ Enhanced protocol with thumbnail commands
└── utils/                        # Utility functions
    ├── file_utils.py
    ├── json_utils.py
    └── validation.py

animation_library/                # ✅ Production storage structure
├── actions/                      # .blend files (instant application)
├── metadata/                     # JSON metadata (fast search)
└── thumbnails/                   # ✅ REAL-TIME: Live preview images
```

## Coding Conventions
- Python 3.8+ and PEP8 style
- PascalCase for classes, snake_case for functions/variables
- Type hints on all functions and class attributes
- Follow Qt and Blender Python API best practices
- **Modular component isolation** - each widget is independently testable

## Key UI Architecture Principles

### **3-Panel Studio Library Layout**
1. **Left Panel**: Folder Tree (`folder_tree.py`) - hierarchical navigation
2. **Center Panel**: Animation Grid with Cards (`animation_card.py`) - main content area  
3. **Right Panel**: Metadata Panel (`metadata_panel.py`) - details and controls

### **Critical UI Requirements**
- The **"🎬 All Animations"** root category:
  - Must appear **above all folders** in tree
  - **Cannot be deleted, renamed, or moved**
  - Is a **static category**, not a real folder
  - Always shows all animations regardless of folder

### **Real-Time Thumbnail System**
- **Automatic capture** during animation extraction (512x512 resolution)
- **Manual updates** via "Update Thumbnail" button in metadata panel
- **Aggressive cache clearing** for immediate visual updates across all components
- **Multiple fallback methods**: OpenGL render → Screen capture → Camera render
- **Cross-component refresh**: Cards, metadata panel, and future video previews

### **Component Communication**
- Use **signal-based communication** between widgets
- **Layout manager** handles widget placement and signal routing
- **Main window** coordinates thumbnail updates across all components
- Each widget is **independently refreshable** without affecting others

## Performance & Storage Architecture

### **Professional .blend File Storage** (Current Implementation)
- **99% performance improvement**: 0.5s application vs 60s JSON recreation
- **Perfect fidelity**: Native Blender action preservation
- **90% smaller files**: Optimized binary storage vs text JSON
- **Cross-project compatibility**: Share animations between projects

### **Thumbnail System Performance**
- **Viewport capture**: ~0.3s with multiple fallback methods
- **Real-time updates**: Aggressive cache clearing ensures immediate refresh
- **Memory efficient**: Smart pixmap management with forced cache clearing
- **Error recovery**: Placeholder generation and retry mechanisms

## Current Technical Implementation Status

### **✅ COMPLETED SYSTEMS**
1. **Thumbnail System**: Complete real-time thumbnail capture and update system
2. **Modular Architecture**: All widgets properly isolated and communicating via signals
3. **Professional Add-on**: Complete Blender add-on with robust thumbnail capture
4. **Studio Library Interface**: 3-panel layout matching Maya Studio Library
5. **Real-time Communication**: Blender ↔ GUI with thumbnail update commands

### **🚧 CURRENT FOCUS AREAS**
1. **Performance Optimization**: Further speed improvements for large libraries (10,000+ animations)
2. **Advanced Features**: Video preview loops, AI-powered tagging
3. **Cross-platform**: Maya/Unity export for broader workflow integration

## Development Workflow Guidelines

### **Component-Based Development**
```bash
# Each developer works on isolated components
src/gui/widgets/
├── animation_card.py     # Team Member A: Card thumbnail refresh system
├── metadata_panel.py     # Team Member B: Large preview with update button
├── folder_tree.py        # Team Member C: Navigation features  
├── toolbar.py           # Team Member D: Search & filters
└── bone_mapping.py      # Team Member E: Auto-mapping algorithms

# Blender add-on components
src/blender_animation_library/
├── operators.py         # Team Member F: Thumbnail capture methods
├── server.py           # Team Member G: Real-time communication
├── storage.py          # Team Member H: .blend file optimization
└── ui.py               # Team Member I: Panel improvements

# Main coordination
src/gui/main.py         # Team Lead: Core logic + thumbnail coordination
```

### **Testing Strategy**
```bash
# Component testing (individual widgets)
python -m pytest tests/test_animation_card.py      # Card refresh functionality
python -m pytest tests/test_metadata_panel.py      # Large preview + update button
python -m pytest tests/test_folder_tree.py         # Navigation and drag/drop
python -m pytest tests/test_thumbnail_system.py    # End-to-end thumbnail workflow

# Integration testing
python -m pytest tests/test_thumbnail_integration.py  # Cross-component updates
python -m pytest tests/test_blender_communication.py  # Blender ↔ GUI thumbnail commands
python -m pytest tests/test_studio_layout.py         # 3-panel layout management

# Performance testing
python -m pytest tests/test_performance.py           # Large library handling
```

## Critical Implementation Notes

### **Thumbnail System Requirements**
- **NEVER use localStorage/sessionStorage** in Qt widgets
- **Always clear Qt pixmap cache** when refreshing thumbnails
- **Use aggressive refresh strategies** for immediate visual updates
- **Implement multiple fallback methods** for robust thumbnail capture
- **Handle Blender version compatibility** (3.0+ to 4.0+)

### **Modular Architecture Rules**
- **Each widget must be independently testable**
- **Use signals for all inter-component communication**
- **Never directly import other widgets** - use layout manager for access
- **Main window coordinates** but doesn't contain widget logic
- **Components should work in isolation** during development

### **Performance Guidelines**
- **Optimize for 10,000+ animation libraries**
- **Use bulk operations** for large dataset updates
- **Implement lazy loading** where appropriate
- **Monitor memory usage** during thumbnail operations
- **Cache thumbnails efficiently** but allow forced refresh

## Security & Production Readiness

### **File System Security**
- **Validate all thumbnail file paths** to prevent directory traversal
- **Sanitize animation names** for cross-platform filename compatibility
- **Handle file system permissions** gracefully with fallbacks
- **Implement safe cleanup** of temporary thumbnail files

### **Error Handling**
- **Robust thumbnail capture** with multiple fallback methods
- **Graceful degradation** when Blender operations fail
- **User feedback** for all operations with clear error messages
- **Recovery mechanisms** for corrupted thumbnail files

## Future Architecture Considerations

### **Planned Enhancements**
1. **Video Preview System**: Hover-to-play animation loops in cards
2. **AI-Powered Features**: Motion analysis and automatic tagging
3. **Cloud Synchronization**: Team collaboration with thumbnail sync
4. **Performance Analytics**: Detailed timing and usage statistics
5. **Plugin Ecosystem**: Custom thumbnail generators and processors

### **Extension Points**
- **Custom thumbnail generators**: For procedural animation previews
- **Additional storage backends**: Database integration, cloud storage
- **Export systems**: Maya, Unity, other DCC applications
- **Advanced search**: AI-powered similarity detection
- **Workflow integrations**: Version control, asset management systems

## Visual Design Standards

All UI components must strictly follow the design system documented in `copilot/gui_style_guide.md`. 

### **Critical Design Requirements**
- **Color Palette**: #2e2e2e backgrounds, #4a90e2 primary accents, #eeeeee text
- **Thumbnail System**: 120x120px cards, 300x300px detail view, aggressive cache clearing
- **Layout**: 3-panel Studio Library design with consistent 12px spacing
- **Typography**: Segoe UI font family, 11px body text, proper hierarchy
- **Interactive States**: Subtle hover effects, clear selection indicators

### **UI Component Checklist**
- [ ] Follows established color palette from style guide
- [ ] Implements proper thumbnail sizing and refresh behavior  
- [ ] Uses consistent spacing (12px margins, 8-12px padding)
- [ ] Includes hover/selected/loading states per style guide
- [ ] Maintains dark theme compatibility
- [ ] Follows typography hierarchy and font sizing

**📋 Always reference `copilot/gui_style_guide.md` before implementing UI changes**

## Code Quality Standards

### **Required for All New Code**
- **Type hints** on all functions and class methods
- **Docstrings** for all public methods and classes
- **Error handling** with specific exception types
- **Logging** for debugging and monitoring
- **Unit tests** for all new functionality
- **Component isolation** - no cross-widget dependencies

### **Thumbnail-Specific Standards**
- **Cache management**: Always implement cache clearing strategies
- **File validation**: Verify thumbnail files exist and are valid
- **Fallback handling**: Multiple methods for thumbnail generation
- **Signal emission**: Proper notification of thumbnail updates
- **Memory cleanup**: Prevent pixmap memory leaks

## GitHub Copilot Usage Guidelines

### **For New Features**
- **Start with the widget level** - implement in isolated components first
- **Use existing patterns** from animation_card.py and metadata_panel.py
- **Follow the thumbnail refresh patterns** already established
- **Integrate via signals** rather than direct method calls
- **Test component isolation** before integration

### **For Bug Fixes**
- **Identify the specific component** responsible for the issue
- **Use existing debugging patterns** and logging statements
- **Test fixes in isolation** before full integration
- **Verify thumbnail updates** work across all affected components
- **Update related tests** to prevent regression

### **For Performance Optimization**
- **Profile before optimizing** to identify actual bottlenecks
- **Use existing bulk operation patterns** from animation_card.py
- **Maintain component isolation** during optimization
- **Test with large datasets** (1000+ animations)
- **Monitor memory usage** especially for thumbnail operations

This architecture supports professional animation studios with maintainable, scalable, and high-performance workflows while enabling team-based development with minimal conflicts.