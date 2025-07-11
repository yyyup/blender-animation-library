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
    QMenu, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QAction, QIcon, QColor, QDragEnterEvent, QDropEvent
from typing import Dict, Any, Optional


class FolderTreeWidget(QWidget):
    """Professional folder tree widget for animation library organization"""
    
    # Signals
    folder_selected = Signal(str)  # Emits filter string for selected folder
    animation_moved = Signal(str, str)  # Emits (animation_id, target_folder)
    folder_created = Signal(str)  # Emits new folder name
    folder_deleted = Signal(str)  # Emits deleted folder name
    
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
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setExpandsOnDoubleClick(True)
        
        # Enable drag and drop
        self.tree_widget.setDragDropMode(QTreeWidget.DropOnly)
        self.tree_widget.setAcceptDrops(True)
        self.tree_widget.setDropIndicatorShown(True)
        
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
        
        # Now create toolbar (after tree_widget exists)
        toolbar_widget = self.create_toolbar()
        layout.addWidget(toolbar_widget)
        
        # Add tree widget to layout
        layout.addWidget(self.tree_widget)
        
        # Apply styling to entire widget
        self.apply_styling()
        
    def apply_styling(self):
        """Apply styling to the folder tree widget"""
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #393939;
                color: #ffffff;
                border: none;
                font-size: 11px;
                outline: none;
            }
            
            QTreeWidget::item {
                padding: 4px 8px;
                border: none;
                height: 24px;
            }
            
            QTreeWidget::item:selected {
                background-color: #4a90e2;
                color: white;
            }
            
            QTreeWidget::item:hover {
                background-color: #525252;
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
                image: url(none);
                border-image: none;
                border: none;
            }
            
            QTreeWidget::branch:open:has-children:has-siblings {
                image: url(none);
                border-image: none;
                border: none;
            }
            
            QTreeWidget::branch:closed:has-children:!has-siblings {
                image: url(none);
                border-image: none;
                border: none;
            }
            
            QTreeWidget::branch:open:has-children:!has-siblings {
                image: url(none);
                border-image: none;
                border: none;
            }
            
            QPushButton {
                background-color: #666;
                color: white;
                border: 1px solid #777;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #777;
                border-color: #4a90e2;
            }
            
            QPushButton:pressed {
                background-color: #555;
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
        """Setup minimal default folder structure"""
        self.folder_structure = {
            "All Animations": {"type": "filter", "filter": "all", "count": 0},
            "Custom Folders": {
                "type": "category",
                "children": {
                    "📁 Root": {"type": "folder", "filter": "folder:Root", "count": 0}
                }
            }
        }
        
        self.refresh_tree()
    
    def update_folder_structure(self, folder_structure: Dict[str, Any]):
        """Update folder structure from library manager"""
        # Merge with default structure, keeping custom folders
        custom_folders = folder_structure.get("Custom Folders", {}).get("children", {})
        
        # Update custom folders section
        if custom_folders:
            self.folder_structure["Custom Folders"]["children"].update(custom_folders)
        
        self.refresh_tree()
    
    def refresh_tree(self):
        """Refresh the tree widget display"""
        self.tree_widget.clear()
        
        # Create tree items
        for folder_name, folder_data in self.folder_structure.items():
            folder_item = self.create_tree_item(folder_name, folder_data)
            self.tree_widget.addTopLevelItem(folder_item)
        
        # Expand custom folders by default
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            if item.text(0) == "Custom Folders":
                item.setExpanded(True)
                break
        
        # Select "All Animations" by default
        if self.tree_widget.topLevelItemCount() > 0:
            first_item = self.tree_widget.topLevelItem(0)
            first_item.setSelected(True)
            self.current_selection = "all"
    
    def create_tree_item(self, name: str, data: Dict[str, Any], parent: Optional[QTreeWidgetItem] = None) -> QTreeWidgetItem:
        """Create a tree widget item"""
        if parent:
            item = QTreeWidgetItem(parent)
        else:
            item = QTreeWidgetItem()
        
        # Set item text and data
        display_name = name
        if data.get("count") is not None:
            display_name = f"{name} ({data['count']})"
        
        item.setText(0, display_name)
        item.setData(0, Qt.UserRole, data)
        
        # Set icon/styling based on type
        item_type = data.get("type", "folder")
        if item_type == "category":
            # Category folders are bold
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
        elif item_type == "filter":
            # Filter items are slightly indented visually
            pass
        
        # Add children if present
        children = data.get("children", {})
        for child_name, child_data in children.items():
            self.create_tree_item(child_name, child_data, item)
        
        return item
    
    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click"""
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
        
        if item_type == "category" and item.text(0) == "Custom Folders":
            # Add folder to custom folders
            add_action = QAction("Add Folder", self)
            add_action.triggered.connect(self.create_new_folder)
            menu.addAction(add_action)
        elif item_type == "folder" and item.parent() and item.parent().text(0) == "Custom Folders":
            # Custom folder operations
            folder_display_name = item.text(0).split(" (")[0]
            folder_name = folder_display_name.replace("📁 ", "")
            
            # Don't allow deleting Root folder
            if folder_name == "Root":
                info_action = QAction("📁 Root folder (cannot be deleted)", self)
                info_action.setEnabled(False)
                menu.addAction(info_action)
            else:
                rename_action = QAction("Rename", self)
                rename_action.triggered.connect(lambda: self.rename_folder(item))
                menu.addAction(rename_action)
                
                delete_action = QAction("Delete", self)
                delete_action.triggered.connect(lambda: self.delete_folder(item))
                menu.addAction(delete_action)
        
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
    
    def rename_folder(self, item: QTreeWidgetItem):
        """Rename a custom folder"""
        old_name = item.text(0).split(" (")[0].replace("📁 ", "")
        
        new_name, ok = QInputDialog.getText(
            self, "Rename Folder", "Enter new folder name:",
            text=old_name
        )
        
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            
            # Update structure
            custom_folders = self.folder_structure["Custom Folders"]["children"]
            old_key = f"📁 {old_name}"
            new_key = f"📁 {new_name}"
            
            if new_key in custom_folders:
                QMessageBox.warning(self, "Folder Exists", f"A folder named '{new_name}' already exists.")
                return
            
            # Move folder data
            if old_key in custom_folders:
                folder_data = custom_folders[old_key]
                folder_data["filter"] = f"folder:{new_name}"
                custom_folders[new_key] = folder_data
                del custom_folders[old_key]
                
                # Refresh tree
                self.refresh_tree()
                
                print(f"📁 Renamed folder: {old_name} → {new_name}")
                
                # TODO: Update animations in this folder
                # This would require connection to library manager
    
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
        # Update custom folder counts
        custom_folders = self.folder_structure["Custom Folders"]["children"]
        for folder_key, folder_data in custom_folders.items():
            folder_name = folder_key.replace("📁 ", "")
            if folder_name in folder_stats:
                folder_data["count"] = folder_stats[folder_name]["total"]
        
        # Update other dynamic counts would go here
        # For now, we'll refresh the display
        self.refresh_tree()
    
    def select_folder(self, filter_str: str):
        """Programmatically select a folder by filter string"""
        self.current_selection = filter_str
        
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
        print(f"🔄 TREE: Force refreshing tree from library structure")
        self.folder_structure = folder_structure
        self.refresh_tree()
        print(f"🔄 TREE: Tree refreshed with {len(folder_structure)} top-level items")
    
    def get_current_selection(self) -> str:
        """Get the current folder selection filter"""
        return self.current_selection
    
    def tree_dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event for tree widget"""
        if event.mimeData().hasText():
            data = event.mimeData().text()
            if data.startswith("animation_id:"):
                event.acceptProposedAction()
                print(f"🎬 Drag enter accepted: {data}")
            else:
                event.ignore()
        else:
            event.ignore()
    
    def tree_dragMoveEvent(self, event):
        """Handle drag move event for tree widget"""
        if event.mimeData().hasText():
            data = event.mimeData().text()
            if data.startswith("animation_id:"):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def tree_dropEvent(self, event: QDropEvent):
        """Handle drop event for tree widget"""
        if event.mimeData().hasText():
            data = event.mimeData().text()
            if data.startswith("animation_id:"):
                animation_id = data.replace("animation_id:", "")
                
                # Get the item at drop position
                position = event.pos()
                item = self.tree_widget.itemAt(position)
                
                if item:
                    # Get target folder
                    target_folder = self._get_folder_path_from_item(item)
                    if target_folder:
                        print(f"🎬 Drop successful! Animation {animation_id} → {target_folder}")
                        self.animation_moved.emit(animation_id, target_folder)
                        event.acceptProposedAction()
                        return
                
                print("🎬 Drop failed - invalid target")
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
        elif item_type == "category" and item.text(0) == "Custom Folders":
            # Dropped on Custom Folders category - use Root
            return "Root"
        
        return None