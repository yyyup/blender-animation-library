# Copilot Project Instructions

## Project Purpose
A professional modular animation library for Blender, inspired by Maya Studio Library, designed to:
- Extract, store, and apply full animation sequences.
- Provide a modular Studio Library-like GUI.
- Optimize performance using native `.blend` file storage for fast application.

## Folder Structure
- `src/gui/`: Qt-based Studio Library interface.
   - `layouts/`: Manages the 3-panel Studio Library layout.
   - `widgets/`: Contains reusable GUI widgets like the animation cards, folder tree, metadata panel, and toolbar.
   - `utils/`: Contains helper functions like Blender connection and library management.
- `src/blender_addon/`: Modular Blender add-on with operators, UI panels, server, and preferences.
- `src/core/`: Core logic for animation data, bone mapping, and storage management.
- `animation_library/`: Animation assets in `.blend` and JSON format.

## Coding Conventions
- Python 3.8+ and PEP8 style.
- PascalCase for classes.
- snake_case for functions and variables.
- Use type hints on all functions and class attributes.
- Follow Qt and Blender Python API best practices.

## Key UI Architecture
- The GUI has a **3-panel layout**:
   1. Left: Folder Tree (`folder_tree.py`).
   2. Center: Animation Grid with Cards (`animation_card.py`).
   3. Right: Metadata Panel (`metadata_panel.py`).
- The Folder Tree root node should include a static **“Animation”** category, which:
   - Should appear **above all folders**.
   - **Must not be deletable**.
   - Is a **static category**, not a real folder.
- Future GUI enhancements should follow this layout system, with widgets separated and isolated for maintainability.

## Special Instructions
- All animation data should be extracted/applied using `.blend` file storage (`src/core/library_storage.py`).
- Ensure real-time communication with Blender through the `blender_connection.py`.
- All new features should be modular and isolated within the appropriate component.
- Follow the modular architecture; avoid monolithic functions or classes.
- Do not modify CI/CD files unless making explicit build/test changes.

## Security & Performance
- Optimize for instant animation application (~0.5s).
- Monitor performance with built-in metrics (avoid introducing slow operations).
- Keep Blender socket communication isolated from GUI logic.

## Future Scope & Flexibility

This project is designed to support modular growth.  
Future components may include:
- Cloud library synchronization
- AI-powered animation tagging
- Version control integration
- Cross-platform export (e.g., Maya, Unity)

Copilot should follow existing architecture when adding new features and place them in appropriately named folders (e.g., `src/cloud/`, `src/ai/`).

## UI Style Guide
Follow `copilot/gui_style_guide.md` for all UI components.


