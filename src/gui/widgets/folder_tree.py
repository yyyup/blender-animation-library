"""
Folder Tree Widget
Professional hierarchical folder navigation for animation library
"""

import sys
from pathlib import Path

# Add core modules to path
gui_dir = Path(__file__).parent.parent.parent
if str(gui_dir) not in sys.path:
    sys.path.insert(0, str(gui_dir))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QHBoxLayout, QPushButton, QInputDialog, QMessageBox,
    QMenu, QStyledItemDelegate
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDrag, QPainter, QFont, QAction
from typing import Dict, Any, Optional


class FolderTreeItemDelegate(QStyledItemDelegate):
    """Custom delegate for styling folder tree items based on their type"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paint(self, painter: QPainter, option, index):
        """Custom paint method that doesn't override any background colors"""
        # DO NOT override any colors - let CSS handle everything
        # This ensures proper background color inheritance from stylesheet
        
        # Let the default painter handle all styling through CSS
        super().paint(painter, option, index)


class FolderTreeWidget(QWidget):
    """Professional folder tree widget for animation library organization"""
    
    # Signals
    folder_selected = Signal(str)  # Emits filter string for selected folder
    animation_moved = Signal(str, str)  # Emits (animation_id, target_folder)
    folder_created = Signal(str)  # Emits new folder name
    folder_deleted = Signal(str)  # Emits deleted folder name
    folder_moved = Signal(str, str)  # Emits (source_folder, target_folder) for reorganization
    animation_count_changed = Signal(str, str, int)  # Emits (source_folder, target_folder, animation_count_change)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.folder_structure = {}
        self.current_selection = "all"
        
        self.setup_ui()
        self.setup_default_structure()
    
    def setup_ui(self):
        """Setup the folder tree UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Create tree widget first
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setRootIsDecorated(True)
        self.tree_widget.setAlternatingRowColors(False)  # Remove alternating colors
        self.tree_widget.setExpandsOnDoubleClick(True)
        
        # Set custom delegate for proper styling
        self.item_delegate = FolderTreeItemDelegate(self.tree_widget)
        self.tree_widget.setItemDelegate(self.item_delegate)
        
        # Enable drag and drop for both animations and folders
        self.tree_widget.setDragDropMode(QTreeWidget.DragDrop)
        self.tree_widget.setAcceptDrops(True)
        self.tree_widget.setDropIndicatorShown(True)
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setDefaultDropAction(Qt.MoveAction)
        
        # Enable drops on the entire widget
        self.setAcceptDrops(True)
        
        # Connect tree signals
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        # Override tree widget's drag and drop events
        self.tree_widget.dragEnterEvent = self.tree_dragEnterEvent
        self.tree_widget.dragMoveEvent = self.tree_dragMoveEvent  
        self.tree_widget.dropEvent = self.tree_dropEvent
        self.tree_widget.startDrag = self.tree_startDrag
        
        # Now create toolbar (after tree_widget exists)
        toolbar_widget = self.create_toolbar()
        layout.addWidget(toolbar_widget)
        
        # Add tree widget to layout
        layout.addWidget(self.tree_widget)
        
        # Apply styling to entire widget
        self.apply_styling()
        
        # Set custom item delegate for folder tree
        self.tree_widget.setItemDelegate(FolderTreeItemDelegate(self.tree_widget))
        
    def apply_styling(self):
        """Apply professional dark styling to the folder tree widget"""
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #2e2e2e;
                color: #eeeeee;
                border: none;
                font-size: 12px;
                outline: none;
                font-family: 'Segoe UI', Arial, sans-serif;
                selection-background-color: #3d5afe;
                alternate-background-color: #2e2e2e;
                show-decoration-selected: 1;
            }
            
            QTreeWidget::item {
                padding: 10px 12px;
                border: none;
                height: 36px;
                margin: 2px 0px;
                border-radius: 6px;
                background-color: #2e2e2e !important;
                background: #2e2e2e !important;
                color: #eeeeee;
                spacing: 10px;
                font-size: 12px;
                line-height: 36px;
            }
            
            QTreeWidget::item:selected {
                background-color: #3d5afe !important;
                background: #3d5afe !important;
                color: white !important;
                font-weight: 500;
                border: none;
            }
            
            QTreeWidget::item:hover:!selected {
                background-color: #3a3a3a !important;
                background: #3a3a3a !important;
                color: #ffffff;
            }
            
            QTreeWidget::item:selected:hover {
                background-color: #3d5afe !important;
                background: #3d5afe !important;
                color: white !important;
            }
            
            /* Remove alternating row colors - force consistent background */
            QTreeWidget::item:alternate {
                background-color: #2e2e2e !important;
                background: #2e2e2e !important;
            }
            
            /* Ensure unselected items have the correct background */
            QTreeWidget::item:!selected {
                background-color: #2e2e2e !important;
                background: #2e2e2e !important;
            }
            
            /* Drag and drop highlighting */
            QTreeWidget::item:drop {
                background-color: #4caf50;
                border: 2px solid #66bb6a;
            }
            
            QTreeWidget::branch {
                background: transparent;
                width: 16px;
            }
            
            QTreeWidget::branch:has-siblings:!adjoins-item {
                border-image: none;
                border: none;
            }
            
            QTreeWidget::branch:has-siblings:adjoins-item {
                border-image: none;
                border: none;
            }
            
            QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {
                border-image: none;
                border: none;
            }
            
            QTreeWidget::branch:closed:has-children:has-siblings {
                background: transparent;
                image: none;
                border: none;
            }
            
            QTreeWidget::branch:open:has-children:has-siblings {
                background: transparent;
                image: none;
                border: none;
            }
            
            QTreeWidget::branch:closed:has-children:!has-siblings {
                background: transparent;
                image: none;
                border: none;
            }
            
            QTreeWidget::branch:open:has-children:!has-siblings {
                background: transparent;
                image: none;
                border: none;
            }
            
            QPushButton {
                background-color: #404040;
                color: #eeeeee;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 500;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #3d5afe;
                color: #ffffff;
            }
            
            QPushButton:pressed {
                background-color: #353535;
                border-color: #3d5afe;
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
        
        # Collapse all button
        collapse_btn = QPushButton("−")
        collapse_btn.setToolTip("Collapse all folders")
        collapse_btn.setMaximumWidth(24)
        collapse_btn.clicked.connect(self.tree_widget.collapseAll)
        layout.addWidget(collapse_btn)
        
        # Expand all button
        expand_btn = QPushButton("+")
        expand_btn.setToolTip("Expand all folders")
        expand_btn.setMaximumWidth(24)
        expand_btn.clicked.connect(self.tree_widget.expandAll)
        layout.addWidget(expand_btn)
        
        return toolbar
    
    def setup_default_structure(self):
        """Setup minimal default folder structure with root at top"""
        self.folder_structure = {
            "🎬 All Animations": {"type": "root", "filter": "all", "count": 0}
        }
        
        self.refresh_tree()
    
    def update_folder_structure(self, folder_structure: Dict[str, Any]):
        """Update folder structure from library manager"""
        # Get custom folders and add them directly to root level
        custom_folders = folder_structure.get("Custom Folders", {}).get("children", {})
        
        # Remove any "Root" folder from custom folders if it exists
        custom_folders.pop("📁 Root", None)
        
        # Add custom folders directly to the root level structure
        if custom_folders:
            self.folder_structure.update(custom_folders)
        
        self.refresh_tree()
    
    def refresh_tree(self):
        """Refresh the tree widget display"""
        self.tree_widget.clear()
        
        # Create tree items
        for folder_name, folder_data in self.folder_structure.items():
            folder_item = self.create_tree_item(folder_name, folder_data)
            self.tree_widget.addTopLevelItem(folder_item)
        
        # Expand all folders by default for better visibility
        self.tree_widget.expandAll()
        
        # Select "🎬 All Animations" (root) by default
        if self.tree_widget.topLevelItemCount() > 0:
            first_item = self.tree_widget.topLevelItem(0)
            first_item.setSelected(True)
            self.current_selection = "all"
    
    def create_tree_item(self, name: str, data: Dict[str, Any], parent: Optional[QTreeWidgetItem] = None) -> QTreeWidgetItem:
        """Create a tree widget item with CSS-based styling"""
        if parent:
            item = QTreeWidgetItem(parent)
        else:
            item = QTreeWidgetItem()
        
        # Set item text and data with styled folder names
        item_type = data.get("type", "folder")
        count = data.get("count")
        
        if item_type == "folder" and name.startswith("📁"):
            display_name = self.create_styled_folder_name(name, count)
        else:
            display_name = name
            if count is not None:
                display_name = f"{name} ({count})"
        
        item.setText(0, display_name)
        item.setData(0, Qt.UserRole, data)
        
        # Store item type for reference but let CSS handle all styling
        item.setData(0, Qt.UserRole + 1, item_type)
        
        # Only set font properties minimally, remove all color overrides
        if item_type == "root":
            font = item.font(0)
            font.setBold(True)
            font.setPointSize(13)
            item.setFont(0, font)
        elif item_type == "category":
            font = item.font(0)
            font.setBold(True)
            font.setPointSize(12)
            item.setFont(0, font)
        elif item_type == "folder":
            font = item.font(0)
            font.setPointSize(11)
            item.setFont(0, font)
        # Let CSS handle all colors and backgrounds
        
        # Add children if present
        children = data.get("children", {})
        for child_name, child_data in children.items():
            self.create_tree_item(child_name, child_data, item)
        
        return item
    
    def on_item_clicked(self, item: QTreeWidgetItem, column: int = 0):
        """Handle item click"""
        _ = column  # Unused parameter
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return
        
        item_type = item_data.get("type", "folder")
        
        if item_type == "filter":
            # This is a filter item - emit the filter
            filter_str = item_data.get("filter", "all")
            self.current_selection = filter_str
            self.folder_selected.emit(filter_str)
            
            print(f"📁 Folder filter selected: {filter_str}")
        elif item_type == "root":
            # This is the root - show all animations
            filter_str = item_data.get("filter", "all")
            self.current_selection = filter_str
            self.folder_selected.emit(filter_str)
            
            print("🎬 Root selected - showing all animations")
        elif item_type == "category":
            # This is a category - just expand/collapse
            item.setExpanded(not item.isExpanded())
        elif item_type == "folder":
            # This is a custom folder - extract clean folder name
            folder_display_name = item.text(0).split(" (")[0]  # Remove count
            folder_name = folder_display_name.replace("📁 ", "")  # Remove emoji
            filter_str = f"folder:{folder_name}"
            self.current_selection = filter_str
            self.folder_selected.emit(filter_str)
            
            print(f"📁 Custom folder selected: {folder_name} (filter: {filter_str})")
    
    def show_context_menu(self, position):
        """Show context menu for folder operations"""
        item = self.tree_widget.itemAt(position)
        if not item:
            return
        
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return
        
        menu = QMenu(self)
        
        item_type = item_data.get("type", "folder")
        
        if item_type == "root":
            # Root cannot be modified
            info_action = QAction("🎬 All Animations - Shows all animations", self)
            info_action.setEnabled(False)
            menu.addAction(info_action)
            
            menu.addSeparator()
            info2_action = QAction("💡 This category cannot be moved or deleted", self)
            info2_action.setEnabled(False)
            menu.addAction(info2_action)
            
            # Allow creating folders from root
            menu.addSeparator()
            add_action = QAction("Add New Folder", self)
            add_action.triggered.connect(self.create_new_folder)
            menu.addAction(add_action)
        elif item_type == "folder":
            # Custom folder operations - all custom folders can be renamed or deleted
            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(lambda: self.rename_folder(item))
            menu.addAction(rename_action)
            
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(lambda: self.delete_folder(item))
            menu.addAction(delete_action)
            
            menu.addSeparator()
            add_sub_action = QAction("Add Subfolder", self)
            add_sub_action.triggered.connect(lambda: self.create_subfolder(item))
            menu.addAction(add_sub_action)
        
        if menu.actions():
            menu.exec_(self.tree_widget.mapToGlobal(position))
    
    def create_new_folder(self):
        """Create a new custom folder"""
        folder_name, ok = QInputDialog.getText(
            self, "New Folder", "Enter folder name:",
            text=""
        )
        
        if ok and folder_name.strip():
            folder_name = folder_name.strip()
            
            # Emit signal to let main window handle the creation
            print(f"📁 Requesting folder creation: {folder_name}")
            self.folder_created.emit(folder_name)
    
    def create_subfolder(self, parent_item: QTreeWidgetItem):
        """Create a subfolder under an existing folder"""
        parent_name = parent_item.text(0).split(" (")[0].replace("📁 ", "")
        
        folder_name, ok = QInputDialog.getText(
            self, "New Subfolder", f"Enter subfolder name under '{parent_name}':",
            text=""
        )
        
        if ok and folder_name.strip():
            folder_name = folder_name.strip()
            # Create hierarchical folder name
            full_name = f"{parent_name}/{folder_name}"
            
            # Emit signal to let main window handle the creation
            print(f"📁 Requesting subfolder creation: {full_name}")
            self.folder_created.emit(full_name)
    
    def rename_folder(self, item: QTreeWidgetItem):
        """Rename a custom folder"""
        old_name = item.text(0).split(" (")[0].replace("📁 ", "")
        
        new_name, ok = QInputDialog.getText(
            self, "Rename Folder", "Enter new folder name:",
            text=old_name
        )
        
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            
            # Update structure (folders are now at root level)
            old_key = f"📁 {old_name}"
            new_key = f"📁 {new_name}"
            
            if new_key in self.folder_structure:
                QMessageBox.warning(self, "Folder Exists", f"A folder named '{new_name}' already exists.")
                return
            
            # Move folder data
            if old_key in self.folder_structure:
                folder_data = self.folder_structure[old_key]
                folder_data["filter"] = f"folder:{new_name}"
                self.folder_structure[new_key] = folder_data
                del self.folder_structure[old_key]
                
                # Refresh tree
                self.refresh_tree()
                
                print(f"📁 Renamed folder: {old_name} → {new_name}")
                
                # Note: Animation updates will be handled by the library manager
    
    def delete_folder(self, item: QTreeWidgetItem):
        """Delete a custom folder"""
        folder_display_name = item.text(0).split(" (")[0]
        folder_name = folder_display_name.replace("📁 ", "")
        
        reply = QMessageBox.question(
            self, "Delete Folder",
            f"Are you sure you want to delete the folder '{folder_name}'?\n\n"
            "Animations in this folder will be moved to Root.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            print(f"🗑️ Requesting folder deletion: {folder_name}")
            # Emit signal to let main window handle the deletion through library manager
            self.folder_deleted.emit(folder_name)
    
    def update_folder_counts(self, folder_stats: Dict[str, Dict[str, int]]):
        """Update folder counts from library statistics"""
        # Update root count (total animations)
        total_animations = sum(stats.get("total", 0) for stats in folder_stats.values())
        self.folder_structure["🎬 All Animations"]["count"] = total_animations
        
        # Update custom folder counts (now at root level)
        for folder_key, folder_data in self.folder_structure.items():
            if folder_key != "🎬 All Animations" and folder_data.get("type") == "folder":
                folder_name = folder_key.replace("📁 ", "")
                if folder_name in folder_stats:
                    folder_data["count"] = folder_stats[folder_name]["total"]
        
        # Refresh the display to show updated counts
        self.refresh_tree()
    
    def update_single_folder_count(self, folder_name: str, count: int):
        """Update the count for a single folder without refreshing the entire tree"""
        # Handle root folder
        if folder_name == "Root" or folder_name == "all" or folder_name == "🎬 All Animations":
            self.folder_structure["🎬 All Animations"]["count"] = count
            # Update the root item display
            for i in range(self.tree_widget.topLevelItemCount()):
                item = self.tree_widget.topLevelItem(i)
                item_data = item.data(0, Qt.UserRole)
                if item_data and item_data.get("type") == "root":
                    item.setText(0, f"🎬 All Animations ({count})")
                    break
            return
        
        # Handle custom folders
        folder_key = f"📁 {folder_name}"
        if folder_key in self.folder_structure:
            self.folder_structure[folder_key]["count"] = count
            # Find and update the item in the tree
            for i in range(self.tree_widget.topLevelItemCount()):
                item = self.tree_widget.topLevelItem(i)
                item_data = item.data(0, Qt.UserRole)
                if item_data and item_data.get("type") == "folder":
                    display_name = item.text(0).split(" (")[0]
                    if display_name == folder_key:
                        item.setText(0, f"{folder_key} ({count})")
                        break
    
    def increment_folder_count(self, folder_name: str, increment: int = 1):
        """Increment or decrement a folder's count by a specific amount"""
        # Handle root folder
        if folder_name == "Root" or folder_name == "all":
            current_count = self.folder_structure["🎬 All Animations"].get("count", 0)
            new_count = max(0, current_count + increment)
            self.update_single_folder_count("🎬 All Animations", new_count)
            return
        
        # Handle custom folders
        folder_key = f"📁 {folder_name}"
        if folder_key in self.folder_structure:
            current_count = self.folder_structure[folder_key].get("count", 0)
            new_count = max(0, current_count + increment)
            self.update_single_folder_count(folder_name, new_count)
            print(f"📊 Updated folder '{folder_name}' count: {current_count} → {new_count}")
    
    def update_folder_counts_efficient(self, folder_stats: Dict[str, Dict[str, int]]):
        """Update folder counts efficiently without full tree rebuild"""
        # Update root count
        total_animations = sum(stats.get("total", 0) for stats in folder_stats.values())
        self.update_single_folder_count("🎬 All Animations", total_animations)
        
        # Update custom folder counts
        for folder_key, folder_data in self.folder_structure.items():
            if folder_key != "🎬 All Animations" and folder_data.get("type") == "folder":
                folder_name = folder_key.replace("📁 ", "")
                if folder_name in folder_stats:
                    new_count = folder_stats[folder_name]["total"]
                    self.update_single_folder_count(folder_name, new_count)
    
    def select_folder(self, filter_str: str):
        """Programmatically select a folder by filter string"""
        self.current_selection = filter_str
        
        # Handle special case for "all" filter - select root
        if filter_str == "all":
            if self.tree_widget.topLevelItemCount() > 0:
                root_item = self.tree_widget.topLevelItem(0)
                self.tree_widget.setCurrentItem(root_item)
                root_item.setSelected(True)
                return
        
        # Find and select the corresponding item
        def find_item_by_filter(item, target_filter):
            item_data = item.data(0, Qt.UserRole)
            if item_data and item_data.get("filter") == target_filter:
                return item
            
            for i in range(item.childCount()):
                found = find_item_by_filter(item.child(i), target_filter)
                if found:
                    return found
            return None
        
        # Search all top-level items
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            found_item = find_item_by_filter(item, filter_str)
            if found_item:
                self.tree_widget.setCurrentItem(found_item)
                found_item.setSelected(True)
                break
    
    def force_refresh_from_library(self, folder_structure: Dict[str, Any]):
        """Force refresh tree from library structure (for after deletions)"""
        print("🔄 TREE: Force refreshing tree from library structure")
        
        # Preserve root structure and merge with library structure
        custom_folders = folder_structure.get("Custom Folders", {}).get("children", {})
        # Remove any "Root" folder from custom folders if it exists
        custom_folders.pop("📁 Root", None)
        
        # Reset structure with root and add custom folders at root level
        self.folder_structure = {
            "🎬 All Animations": {"type": "root", "filter": "all", "count": 0}
        }
        self.folder_structure.update(custom_folders)
        
        self.refresh_tree()
        print(f"🔄 TREE: Tree refreshed with {len(custom_folders)} custom folders")
    
    def get_current_selection(self) -> str:
        """Get the current folder selection filter"""
        return self.current_selection
    
    def tree_dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event for tree widget"""
        if event.mimeData().hasText():
            data = event.mimeData().text()
            if data.startswith("animation_id:") or data.startswith("folder:"):
                event.acceptProposedAction()
                print(f"🎬 Drag enter accepted: {data}")
            else:
                event.ignore()
        else:
            event.ignore()
    
    def tree_dragMoveEvent(self, event):
        """Handle drag move event for tree widget with target highlighting"""
        if event.mimeData().hasText():
            data = event.mimeData().text()
            if data.startswith("animation_id:") or data.startswith("folder:"):
                # Get item under cursor for highlighting
                item = self.tree_widget.itemAt(event.pos())
                if item:
                    item_data = item.data(0, Qt.UserRole)
                    item_type = item_data.get("type", "") if item_data else ""
                    
                    # Check if this is a valid drop target
                    if data.startswith("folder:"):
                        # For folder drops, only allow on other folders or root
                        folder_name = data.replace("folder:", "")
                        if item_type in ["folder", "root"] and self._get_folder_path_from_item(item) != folder_name:
                            # Valid target - highlight it
                            self.tree_widget.setCurrentItem(item)
                            event.acceptProposedAction()
                            return
                    else:
                        # For animation drops, allow on folders and root
                        if item_type in ["folder", "root"]:
                            self.tree_widget.setCurrentItem(item)
                            event.acceptProposedAction()
                            return
                
                event.ignore()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def tree_dropEvent(self, event: QDropEvent):
        """Handle drop event for tree widget with proper folder nesting"""
        if event.mimeData().hasText():
            data = event.mimeData().text()
            
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
    
    def _get_folder_path_from_item(self, item: QTreeWidgetItem) -> Optional[str]:
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
    
    def tree_startDrag(self, supportedActions):
        """Handle start of drag operation for tree items"""
        _ = supportedActions  # Unused parameter
        current_item = self.tree_widget.currentItem()
        
        if not self._is_item_draggable(current_item):
            if current_item:
                item_data = current_item.data(0, Qt.UserRole)
                item_type = item_data.get("type", "") if item_data else "unknown"
                if item_type == "root":
                    print("🚫 Cannot drag the root 'All Animations' category - it must stay at the top")
                else:
                    print(f"🚫 Cannot drag item of type: {item_type}")
            return
        
        # Get folder name for dragging
        folder_display_name = current_item.text(0).split(" (")[0]  # Remove count
        folder_name = folder_display_name.replace("📁 ", "")  # Remove emoji
        
        # Create mime data for folder
        mime_data = QMimeData()
        mime_data.setText(f"folder:{folder_name}")
        
        # Create drag operation
        drag = QDrag(self.tree_widget)
        drag.setMimeData(mime_data)
        
        print(f"📁 Starting drag for folder: {folder_name}")
        
        # Execute drag with move action
        result = drag.exec_(Qt.MoveAction)
        if result == Qt.MoveAction:
            print(f"📁 Drag completed successfully for: {folder_name}")
    
    def _is_item_draggable(self, item: QTreeWidgetItem) -> bool:
        """Check if an item can be dragged"""
        if not item:
            return False
        
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return False
        
        item_type = item_data.get("type", "")
        
        # Only folders can be dragged, not root or other types
        if item_type != "folder":
            return False
        
        # Additional check: make sure it's not the "All Animations" root
        display_name = item.text(0).split(" (")[0]
        if "🎬" in display_name or "All Animations" in display_name:
            return False
        
        return True
    
    def create_styled_folder_name(self, name: str, count: Optional[int] = None) -> str:
        """Create a styled folder name with yellow folder icon"""
        if name.startswith("📁"):
            # Replace the emoji with a better folder icon
            folder_name_clean = name[2:].strip()  # Remove 📁 and space
            count_display = f" ({count})" if count is not None else ""
            # Use a different folder symbol that can be more easily styled yellow
            return f"� {folder_name_clean}{count_display}"
        else:
            count_display = f" ({count})" if count is not None else ""
            return f"{name}{count_display}"