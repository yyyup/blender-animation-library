# Fixed folder_tree.py - Clean implementation without emoji pollution

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class FolderTreeWidget(QWidget):
    """Clean folder tree widget without emoji pollution"""
    
    # Signals - Complete set expected by main window
    folder_selected = Signal(str)  # filter_string
    folder_created = Signal(str)   # folder_path 
    folder_deleted = Signal(str)   # folder_name
    folder_moved = Signal(str, str)  # source_folder, target_folder
    multi_folder_selected = Signal(list)  # list of selected folder names
    folder_auto_expanded = Signal(str)  # folder that was auto-expanded
    batch_move_started = Signal(list, str)  # batch operation signals
    folder_organization_changed = Signal(dict)  # organization rules
    animation_moved = Signal(str, str)  # animation_id, target_folder
    animation_count_changed = Signal(str, str, int)  # source, target, count change
    drag_entered = Signal(object)  # QDropEvent
    dragged_over = Signal(object)  # QDropEvent  
    dropped_on_item = Signal(object)  # QDropEvent
    drop_invalid = Signal(object)  # QDropEvent
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder_structure = {}
        self.current_selection = "all"
        
        # Set up UI
        self.setup_ui()
        self.setup_default_structure()
        
    def setup_ui(self):
        """Set up the folder tree UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tree widget first
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setDragDropMode(QAbstractItemView.DragDrop)
        self.tree_widget.setDefaultDropAction(Qt.MoveAction)
        self.tree_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        # Enable drag and drop for receiving animations
        self.tree_widget.setAcceptDrops(True)
        self.tree_widget.setDropIndicatorShown(True)
        
        # Connect signals
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        # Custom drop handling
        self.tree_widget.dropEvent = self.tree_dropEvent
        self.tree_widget.dragEnterEvent = self.tree_dragEnterEvent
        self.tree_widget.dragMoveEvent = self.tree_dragMoveEvent
        
        # Add toolbar (now tree_widget exists)
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # Add tree widget
        layout.addWidget(self.tree_widget)
        
        # Apply styling
        self.apply_styling()
        
    def apply_styling(self):
        """Apply dark theme styling"""
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                background-color: #2e2e2e;
                color: #eeeeee;
                border: none;
                outline: none;
                selection-background-color: #4a90e2;
            }
            QTreeWidget::item {
                height: 24px;
                padding: 4px 8px;
                border: none;
            }
            QTreeWidget::item:hover {
                background-color: #3a3a3a;
            }
            QTreeWidget::item:selected {
                background-color: #4a90e2;
                color: white;
            }
            QTreeWidget::branch:has-children:closed {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiI+PHBhdGggZD0iTTYgNGw0IDQtNCA0eiIgZmlsbD0iI2VlZWVlZSIvPjwvc3ZnPg==);
            }
            QTreeWidget::branch:has-children:open {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiI+PHBhdGggZD0iTTQgNmw0IDQgNC00eiIgZmlsbD0iI2VlZWVlZSIvPjwvc3ZnPg==);
            }
        """)
        
    def create_toolbar(self) -> QWidget:
        """Create toolbar for folder operations"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Add folder button
        self.add_folder_btn = QPushButton("+ Folder")
        self.add_folder_btn.setToolTip("Create new folder")
        self.add_folder_btn.clicked.connect(self.create_new_folder)
        layout.addWidget(self.add_folder_btn)
        
        layout.addStretch()
        
        # Collapse/expand buttons
        collapse_btn = QPushButton("−")
        collapse_btn.setToolTip("Collapse all folders")
        collapse_btn.setMaximumWidth(24)
        collapse_btn.clicked.connect(self.tree_widget.collapseAll)
        layout.addWidget(collapse_btn)
        
        expand_btn = QPushButton("+")
        expand_btn.setToolTip("Expand all folders")
        expand_btn.setMaximumWidth(24)
        expand_btn.clicked.connect(self.tree_widget.expandAll)
        layout.addWidget(expand_btn)
        
        return toolbar
        
    def setup_default_structure(self):
        """Setup default folder structure"""
        self.folder_structure = {
            "🎬 All Animations": {"type": "root", "filter": "all", "count": 0}
        }
        self.refresh_tree()
        
    def create_tree_item(self, name: str, data: Dict[str, Any]) -> QTreeWidgetItem:
        """Create a tree widget item with proper icon"""
        item = QTreeWidgetItem([name])
        item.setData(0, Qt.UserRole, data)
        
        # Set appropriate icon
        if data.get("type") == "root":
            # Use film/animation icon for root
            item.setIcon(0, self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            # Use folder icon for folders
            item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
            
        return item
        
    def refresh_tree(self):
        """Refresh the tree widget display"""
        print(f"🔄 TREE: Refreshing tree with {len(self.folder_structure)} folders")
        self.tree_widget.clear()
        
        # Add root item
        root_data = {"type": "root", "filter": "all", "count": 0}
        root_item = self.create_tree_item("🎬 All Animations", root_data)
        root_item.setExpanded(True)
        self.tree_widget.addTopLevelItem(root_item)
        
        # Build and add folder hierarchy
        if hasattr(self, 'folder_structure'):
            print(f"🌳 TREE: Building hierarchy from {len(self.folder_structure)} folders")
            hierarchy = self._build_folder_hierarchy()
            print(f"🌳 TREE: Built hierarchy with {len(hierarchy)} top-level items")
            if hierarchy:
                self._add_folders_to_tree(hierarchy)
            else:
                print("⚠️ TREE: No hierarchy built - check folder structure")
            
        # Select root by default
        if self.tree_widget.topLevelItemCount() > 0:
            first_item = self.tree_widget.topLevelItem(0)
            first_item.setSelected(True)
            self.current_selection = "all"
            
    def _build_folder_hierarchy(self) -> Dict[str, Any]:
        """Build hierarchical folder structure from flat folder list"""
        hierarchy = {}
        
        # First, get all the clean folder paths
        folder_paths = []
        for folder_key, folder_data in self.folder_structure.items():
            if folder_key == "🎬 All Animations":
                continue
                
            clean_path = self._extract_clean_path(folder_key)
            if clean_path:
                folder_paths.append((clean_path, folder_data))
                print(f"🔍 HIERARCHY: Processing folder: '{clean_path}'")
        
        print(f"🔍 HIERARCHY: Total paths to process: {len(folder_paths)}")
        
        # Sort by path depth (parents before children)
        folder_paths.sort(key=lambda x: x[0].count("/"))
        print(f"🔍 HIERARCHY: Sorted paths: {[path for path, _ in folder_paths]}")
        
        # Build hierarchy
        for clean_path, folder_data in folder_paths:
            print(f"🔨 HIERARCHY: Building path: '{clean_path}'")
            
            # Split path into parts
            path_parts = clean_path.split("/")
            print(f"🔨 HIERARCHY: Path parts: {path_parts}")
            
            # Navigate to the correct position in hierarchy
            current_level = hierarchy
            for i, part in enumerate(path_parts[:-1]):  # All except last part
                print(f"  🔨 Creating/finding parent: '{part}'")
                if part not in current_level:
                    # Create intermediate folder node
                    current_level[part] = {
                        "data": {"type": "folder", "count": 0, "filter": f"folder:{'/'.join(path_parts[:i+1])}"},
                        "children": {},
                        "full_path": "/".join(path_parts[:i+1])
                    }
                    print(f"  ✅ Created parent folder: '{part}'")
                current_level = current_level[part]["children"]
            
            # Add the final folder
            final_part = path_parts[-1]
            print(f"  🔨 Adding final part: '{final_part}'")
            current_level[final_part] = {
                "data": folder_data.copy(),
                "children": {},
                "full_path": clean_path
            }
            print(f"  ✅ Added final folder: '{final_part}'")
        
        print(f"🏗️ HIERARCHY: Final hierarchy: {list(hierarchy.keys())}")
        for key, value in hierarchy.items():
            print(f"  📁 {key} has {len(value['children'])} children: {list(value['children'].keys())}")
                
        return hierarchy
        
    def _extract_clean_path(self, folder_key: str) -> str:
        """Extract clean folder path from stored key"""
        # Remove all possible emoji prefixes and clean the path
        clean = folder_key
        
        # Remove common emoji prefixes
        prefixes_to_remove = ["📁 ", "🧪 ", "🗂️ ", "📂 "]
        for prefix in prefixes_to_remove:
            clean = clean.replace(prefix, "")
            
        # Remove any remaining Unicode artifacts
        clean = ''.join(char for char in clean if ord(char) < 65536)
        
        return clean.strip()
        
    def _add_folders_to_tree(self, folder_hierarchy: Dict[str, Any], parent_item: Optional[QTreeWidgetItem] = None):
        """Add folders to tree with proper nesting"""
        print(f"🌲 ADD_TO_TREE: Adding {len(folder_hierarchy)} folders to tree")
        
        for folder_name, folder_info in folder_hierarchy.items():
            print(f"🌲 ADD_TO_TREE: Processing folder '{folder_name}' with {len(folder_info['children'])} children")
            
            folder_data = folder_info["data"].copy()
            folder_data["type"] = "folder"
            
            # Create display name with count
            display_name = folder_name
            if folder_data.get("count", 0) > 0:
                display_name += f" ({folder_data['count']})"
                
            # Set filter for navigation
            folder_data["filter"] = f"folder:{folder_info['full_path']}"
            
            # Create tree item
            folder_item = self.create_tree_item(display_name, folder_data)
            print(f"🌲 ADD_TO_TREE: Created tree item for '{display_name}'")
            
            # Add to parent or root level
            if parent_item:
                parent_item.addChild(folder_item)
                print(f"🌲 ADD_TO_TREE: Added '{display_name}' as child of parent")
            else:
                self.tree_widget.addTopLevelItem(folder_item)
                print(f"🌲 ADD_TO_TREE: Added '{display_name}' as top-level item")
                
            # Recursively add children
            if folder_info["children"]:
                print(f"🌲 ADD_TO_TREE: '{folder_name}' has children, recursing...")
                self._add_folders_to_tree(folder_info["children"], folder_item)
                folder_item.setExpanded(False)  # Start collapsed
                print(f"🌲 ADD_TO_TREE: Set '{folder_name}' as expandable")
            else:
                print(f"🌲 ADD_TO_TREE: '{folder_name}' has no children")
                
    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click"""
        if not item:
            return
            
        item_data = item.data(0, Qt.UserRole)
        if item_data:
            filter_str = item_data.get("filter", "all")
            self.current_selection = filter_str
            self.folder_selected.emit(filter_str)
            print(f"📁 Selected folder with filter: {filter_str}")
            
    def show_context_menu(self, position: QPoint):
        """Show context menu for folder operations"""
        item = self.tree_widget.itemAt(position)
        menu = QMenu(self)
        
        if item:
            item_data = item.data(0, Qt.UserRole)
            if item_data and item_data.get("type") == "folder":
                # Folder context menu
                create_sub = menu.addAction("Create Subfolder")
                create_sub.triggered.connect(lambda: self.create_subfolder(item))
                menu.addSeparator()
                delete = menu.addAction("Delete Folder")
                delete.triggered.connect(lambda: self.delete_folder(item))
        else:
            # Root level context menu
            add = menu.addAction("Create Folder")
            add.triggered.connect(self.create_new_folder)
            
        menu.exec(self.tree_widget.mapToGlobal(position))
        
    def create_new_folder(self):
        """Create a new folder at root level"""
        folder_name, ok = QInputDialog.getText(
            self, "Create Folder", "Enter folder name:", text="New Folder"
        )
        if ok and folder_name.strip():
            clean_name = folder_name.strip()
            print(f"📁 Creating folder: {clean_name}")
            self.folder_created.emit(clean_name)
            
    def create_subfolder(self, parent_item: QTreeWidgetItem):
        """Create a subfolder under the given parent"""
        if not parent_item:
            return
            
        parent_data = parent_item.data(0, Qt.UserRole)
        if not parent_data:
            return
            
        # Extract parent folder path
        parent_filter = parent_data.get("filter", "")
        if parent_filter.startswith("folder:"):
            parent_path = parent_filter[7:]  # Remove "folder:" prefix
        else:
            return
            
        subfolder_name, ok = QInputDialog.getText(
            self, "Create Subfolder", f"Enter subfolder name:", text="New Subfolder"
        )
        if ok and subfolder_name.strip():
            clean_name = subfolder_name.strip()
            full_path = f"{parent_path}/{clean_name}"
            print(f"📁 Creating subfolder: {full_path}")
            self.folder_created.emit(full_path)
            
    def delete_folder(self, item: QTreeWidgetItem):
        """Delete the selected folder"""
        if not item:
            return
            
        item_data = item.data(0, Qt.UserRole)
        if not item_data or item_data.get("type") != "folder":
            return
            
        # Extract folder path
        filter_str = item_data.get("filter", "")
        if filter_str.startswith("folder:"):
            folder_path = filter_str[7:]  # Remove "folder:" prefix
        else:
            return
            
        reply = QMessageBox.question(
            self, "Delete Folder",
            f"Are you sure you want to delete the folder '{folder_path}'?\n\n"
            "All animations in this folder will be moved to the Root folder.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            print(f"🗑️ Deleting folder: {folder_path}")
            self.folder_deleted.emit(folder_path)
            
    def update_folder_structure(self, folder_structure: Dict[str, Any]):
        """Update folder structure from library manager"""
        print(f"📁 TREE: Updating with structure keys: {list(folder_structure.keys())}")
        
        # Get custom folders
        custom_folders = folder_structure.get("Custom Folders", {}).get("children", {})
        print(f"📁 TREE: Found {len(custom_folders)} custom folders: {list(custom_folders.keys())}")
        
        # Check if structure actually changed
        new_structure = {
            "🎬 All Animations": {"type": "root", "filter": "all", "count": 0}
        }
        
        # Add custom folders directly (they're already clean)
        for folder_key, folder_data in custom_folders.items():
            if isinstance(folder_data, dict):
                folder_data["type"] = "folder"
                new_structure[folder_key] = folder_data
                
        # Only refresh if structure actually changed
        if self._structure_changed(new_structure):
            print(f"📁 TREE: Structure changed, refreshing tree")
            self.folder_structure = new_structure
            self.refresh_tree()
        else:
            print(f"📁 TREE: Structure unchanged, skipping refresh")
            
    def _structure_changed(self, new_structure: Dict[str, Any]) -> bool:
        """Check if folder structure has actually changed"""
        if len(new_structure) != len(self.folder_structure):
            return True
            
        for key, data in new_structure.items():
            if key not in self.folder_structure:
                return True
            old_data = self.folder_structure[key]
            # Check if filter or type changed
            if (data.get("filter") != old_data.get("filter") or 
                data.get("type") != old_data.get("type")):
                return True
                
        return False
        
    def update_folder_counts_only(self, folder_stats: Dict[str, Dict[str, int]]):
        """Update folder counts WITHOUT rebuilding the tree"""
        print(f"📊 TREE: Updating counts only, no refresh")
        
        # Update root count
        total_animations = sum(stats.get("total", 0) for stats in folder_stats.values())
        self.folder_structure["🎬 All Animations"]["count"] = total_animations
        
        # Update folder counts in structure
        for folder_key, folder_data in self.folder_structure.items():
            if folder_key != "🎬 All Animations" and folder_data.get("type") == "folder":
                clean_path = self._extract_clean_path(folder_key)
                if clean_path in folder_stats:
                    folder_data["count"] = folder_stats[clean_path]["total"]
                    
        # Update display text without rebuilding tree
        self._update_display_counts_only()
        
    def _update_display_counts_only(self):
        """Update display text of existing items without rebuilding"""
        def update_item_counts(item):
            item_data = item.data(0, Qt.UserRole)
            if item_data:
                if item_data.get("type") == "root":
                    count = self.folder_structure["🎬 All Animations"].get("count", 0)
                    item.setText(0, f"🎬 All Animations ({count})" if count > 0 else "🎬 All Animations")
                elif item_data.get("type") == "folder":
                    filter_str = item_data.get("filter", "")
                    if filter_str.startswith("folder:"):
                        folder_path = filter_str[7:]
                        # Find matching folder data
                        for folder_key, folder_data in self.folder_structure.items():
                            clean_path = self._extract_clean_path(folder_key)
                            if clean_path == folder_path:
                                count = folder_data.get("count", 0)
                                base_name = clean_path.split("/")[-1]  # Get last part of path
                                has_children = item.childCount() > 0
                                display_name = base_name
                                if count > 0:
                                    display_name += f" ({count})"
                                if has_children:
                                    display_name += " [+]"
                                item.setText(0, display_name)
                                break
            
            # Update children recursively
            for i in range(item.childCount()):
                update_item_counts(item.child(i))
        
        # Update all top-level items
        for i in range(self.tree_widget.topLevelItemCount()):
            update_item_counts(self.tree_widget.topLevelItem(i))
        
    def update_folder_counts(self, folder_stats: Dict[str, Dict[str, int]]):
        """Update folder counts"""
        # Update root count
        total_animations = sum(stats.get("total", 0) for stats in folder_stats.values())
        self.folder_structure["🎬 All Animations"]["count"] = total_animations
        
        # Update folder counts
        for folder_key, folder_data in self.folder_structure.items():
            if folder_key != "🎬 All Animations" and folder_data.get("type") == "folder":
                clean_path = self._extract_clean_path(folder_key)
                if clean_path in folder_stats:
                    folder_data["count"] = folder_stats[clean_path]["total"]
                    
        self.refresh_tree()
        
    def select_folder(self, filter_str: str):
        """Programmatically select a folder"""
        self.current_selection = filter_str
        
        # Find and select the item
        def find_item_by_filter(item, target_filter):
            item_data = item.data(0, Qt.UserRole)
            if item_data and item_data.get("filter") == target_filter:
                return item
                
            for i in range(item.childCount()):
                found = find_item_by_filter(item.child(i), target_filter)
                if found:
                    return found
            return None
            
        # Search all items
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            found_item = find_item_by_filter(item, filter_str)
            if found_item:
                self.tree_widget.setCurrentItem(found_item)
                found_item.setSelected(True)
                break
                
    def update_single_folder_count(self, folder_name: str, count: int):
        """Update count for a single folder"""
        # Basic implementation - update the folder structure and refresh
        for folder_key, folder_data in self.folder_structure.items():
            clean_path = self._extract_clean_path(folder_key)
            if clean_path == folder_name or folder_key == folder_name:
                folder_data["count"] = count
                break
        self.refresh_tree()
        
    def increment_folder_count(self, folder_name: str, increment: int = 1):
        """Increment or decrement folder count"""
        for folder_key, folder_data in self.folder_structure.items():
            clean_path = self._extract_clean_path(folder_key)
            if clean_path == folder_name or folder_key == folder_name:
                current_count = folder_data.get("count", 0)
                folder_data["count"] = max(0, current_count + increment)
                break
        self.refresh_tree()
        
    def force_refresh_from_library(self, folder_structure: Dict[str, Any]):
        """Force refresh tree from library structure"""
        self.update_folder_structure(folder_structure)
        
    # Stub methods for compatibility with main window expectations
    def on_batch_move_started(self, *args):
        """Handle batch move operations - stub for compatibility"""
        pass
        
    def on_folder_auto_expanded(self, folder_name: str):
        """Handle auto-expansion - stub for compatibility"""
        self.folder_auto_expanded.emit(folder_name)
        
    def on_folder_organization_changed(self, rules: dict):
        """Handle organization changes - stub for compatibility"""
        self.folder_organization_changed.emit(rules)
        
    def tree_dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasText():
            data = event.mimeData().text()
            if data.startswith("animation_id:") or data.startswith("folder:"):
                event.acceptProposedAction()
                return
        event.ignore()
    
    def tree_dragMoveEvent(self, event: QDragMoveEvent):
        """Handle drag move event"""
        if event.mimeData().hasText():
            data = event.mimeData().text()
            if data.startswith("animation_id:") or data.startswith("folder:"):
                # Check if the item at current position can accept the drop
                item = self.tree_widget.itemAt(event.pos())
                if item:
                    item_data = item.data(0, Qt.UserRole)
                    if item_data and item_data.get("type") in ["folder", "root"]:
                        event.acceptProposedAction()
                        return
        event.ignore()
            
    def tree_dropEvent(self, event):
        """Handle drop event for animations onto folders"""
        print(f"📥 Drop event on tree widget")
        
        if event.mimeData().hasText():
            data = event.mimeData().text()
            print(f"📄 Drop data: {data}")
            
            # Get the item at drop position
            position = event.pos()
            item = self.tree_widget.itemAt(position)
            
            if not item:
                print("🚫 Drop failed - no target item")
                event.ignore()
                return
            
            item_data = item.data(0, Qt.UserRole)
            if not item_data:
                print("🚫 Drop failed - no item data")
                event.ignore()
                return
            
            target_type = item_data.get("type", "")
            
            if data.startswith("animation_id:"):
                # Animation being dropped into folder
                animation_id = data.replace("animation_id:", "")
                
                # Get target folder
                target_folder = self._get_folder_path_from_item(item)
                if target_folder:
                    print(f"🎬 Drop successful! Animation {animation_id} → {target_folder}")
                    
                    # Emit the animation moved signal
                    self.animation_moved.emit(animation_id, target_folder)
                    event.acceptProposedAction()
                    return
                
                print("🎬 Drop failed - invalid animation target")
                event.ignore()
                
            elif data.startswith("folder:"):
                # Folder being dropped into another folder or root
                source_folder = data.replace("folder:", "")
                
                # Prevent dropping folder onto itself
                target_folder = self._get_folder_path_from_item(item)
                if target_folder == source_folder:
                    print(f"🚫 Cannot drop folder '{source_folder}' onto itself")
                    event.ignore()
                    return
                
                # Prevent dropping onto non-folder/non-root items
                if target_type not in ["folder", "root"]:
                    print(f"🚫 Cannot drop folder onto item of type: {target_type}")
                    event.ignore()
                    return
                
                # Prevent dropping root category
                if source_folder == "All Animations":
                    print("🚫 Cannot move the root 'All Animations' category")
                    event.ignore()
                    return
                
                if target_folder:
                    print(f"📁 Folder reorganization: {source_folder} → {target_folder}")
                    # Emit proper signal for folder reorganization
                    self.folder_moved.emit(source_folder, target_folder)
                    event.acceptProposedAction()
                    return
                
                print("📁 Folder drop failed - invalid target")
                event.ignore()
        else:
            event.ignore()
    
    def _get_folder_path_from_item(self, item) -> Optional[str]:
        """Get folder path from tree item"""
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return None
        
        item_type = item_data.get("type", "")
        
        if item_type == "folder":
            # This is a custom folder - extract the clean folder name
            folder_display_name = item.text(0).split(" (")[0]  # Remove count
            folder_name = folder_display_name.replace("📁 ", "")  # Remove emoji
            print(f"🔍 Extracted folder name: '{folder_name}' from display: '{folder_display_name}'")
            return folder_name
        elif item_type == "root":
            # Dropped on root - use "Root" as default folder
            return "Root"
        
        return None
        
    def startDrag(self, supportedActions: Qt.DropActions = Qt.CopyAction | Qt.MoveAction):
        """Override to provide custom drag support for animations"""
        print(f"🖱️ Drag started")
        # Custom drag logic here (if needed)
        super().startDrag(supportedActions)