"""
Folder Tree Widget
Professional hierarchical folder navigation for animation library
Maya Studio Library enhanced drag-and-drop functionality
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
    QMenu, QStyledItemDelegate, QApplication
)
from PySide6.QtCore import Qt, Signal, QMimeData, QTimer, QRect, QPoint
from PySide6.QtGui import (
    QDragEnterEvent, QDropEvent, QDrag, QPainter, QFont, QAction,
    QPen, QBrush, QColor, QPixmap, QPainterPath, QLinearGradient
)
from typing import Dict, Any, Optional, List


class FolderTreeItemDelegate(QStyledItemDelegate):
    """Enhanced custom delegate for Maya Studio Library style folder tree items"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drop_indicator_rect = QRect()
        self.is_drop_target = False
        self.show_insertion_line = False
        self.insertion_position = 0
    
    def paint(self, painter: QPainter, option, index):
        """Enhanced paint method with Maya-style drag indicators"""
        # Let the default painter handle basic styling through CSS
        super().paint(painter, option, index)
        
        # Draw Maya-style drop indicators
        if self.is_drop_target and option.rect.intersects(self.drop_indicator_rect):
            self._paint_drop_indicator(painter, option.rect)
        
        if self.show_insertion_line:
            self._paint_insertion_line(painter, option.rect)
    
    def _paint_drop_indicator(self, painter: QPainter, rect: QRect):
        """Paint Maya-style blue drop indicator"""
        painter.save()
        
        # Blue highlight for valid drop targets
        highlight_color = QColor(74, 144, 226, 80)  # Maya blue with transparency
        border_color = QColor(74, 144, 226, 200)
        
        painter.fillRect(rect, QBrush(highlight_color))
        
        # Blue border
        pen = QPen(border_color, 2)
        painter.setPen(pen)
        painter.drawRect(rect.adjusted(1, 1, -1, -1))
        
        painter.restore()
    
    def _paint_insertion_line(self, painter: QPainter, rect: QRect):
        """Paint insertion line for folder ordering"""
        painter.save()
        
        # Blue insertion line
        pen = QPen(QColor(74, 144, 226), 2)
        painter.setPen(pen)
        
        y = rect.top() if self.insertion_position == 0 else rect.bottom()
        painter.drawLine(rect.left() + 10, y, rect.right() - 10, y)
        
        painter.restore()
    
    def set_drop_indicator(self, rect: QRect, is_target: bool = True):
        """Set drop indicator rectangle"""
        self.drop_indicator_rect = rect
        self.is_drop_target = is_target
    
    def set_insertion_line(self, show: bool, position: int = 0):
        """Set insertion line visibility and position"""
        self.show_insertion_line = show
        self.insertion_position = position


class FolderTreeWidget(QWidget):
    """Professional folder tree widget with Maya Studio Library enhanced drag-and-drop"""
    
    # Original signals
    folder_selected = Signal(str)  # Emits filter string for selected folder
    animation_moved = Signal(str, str)  # Emits (animation_id, target_folder)
    folder_created = Signal(str)  # Emits new folder name
    folder_deleted = Signal(str)  # Emits deleted folder name
    folder_moved = Signal(str, str)  # Emits (source_folder, target_folder) for reorganization
    animation_count_changed = Signal(str, str, int)  # Emits (source_folder, target_folder, animation_count_change)
    drag_entered = Signal(QDropEvent)  # Signal emitted when a drag enters the widget
    dragged_over = Signal(QDropEvent)  # Signal emitted when an item is dragged over the widget
    dropped_on_item = Signal(QDropEvent)  # Signal emitted when an item is dropped on a valid target
    drop_invalid = Signal(QDropEvent)  # Signal emitted when a drop is invalid
    
    # New Maya-style enhancement signals
    multi_folder_selected = Signal(list)  # For multi-folder operations
    folder_auto_expanded = Signal(str)    # For auto-expansion tracking
    batch_move_started = Signal(list, str)  # For batch operations
    folder_organization_changed = Signal(dict)  # For structure updates
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.folder_structure = {}
        self.current_selection = "all"
        
        # Maya-style enhancement properties
        self.selected_folders = []  # Multi-selection support
        self.auto_expand_timer = QTimer()
        self.auto_expand_timer.timeout.connect(self._auto_expand_folder)
        self.auto_expand_timer.setSingleShot(True)
        self.hover_item = None
        self.drag_scroll_timer = QTimer()
        self.drag_scroll_timer.timeout.connect(self._handle_drag_scroll)
        self.scroll_direction = 0
        self.last_auto_expanded_items = []  # Track auto-expanded items
        
        # Drag operation state
        self.is_dragging = False
        self.drag_start_position = QPoint()
        self.current_drag_items = []
        self.drag_feedback_pixmap = None
        
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
        
        # Maya-style enhancements
        self.tree_widget.setSelectionMode(QTreeWidget.ExtendedSelection)  # Enable multi-selection
        self.tree_widget.setMouseTracking(True)  # Enable hover tracking
        
        # Set enhanced custom delegate for Maya-style styling
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
        
        # Maya-style enhanced event connections
        self.tree_widget.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Override tree widget's drag and drop events with Maya-style versions
        self.tree_widget.dragEnterEvent = self.tree_dragEnterEvent
        self.tree_widget.dragMoveEvent = self.tree_dragMoveEvent  
        self.tree_widget.dragLeaveEvent = self.tree_dragLeaveEvent
        self.tree_widget.dropEvent = self.tree_dropEvent
        self.tree_widget.startDrag = self.tree_startDrag
        
        # Override mouse events for Maya-style multi-selection
        self.tree_widget.mousePressEvent = self._enhanced_mouse_press_event
        
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
        """Apply professional Studio Library styling to the folder tree widget"""
        self.setStyleSheet("""
            /* Main folder tree widget styling */
            QTreeWidget {
                background-color: #2e2e2e;
                color: #eeeeee;
                border: none;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
                outline: none;
                selection-background-color: #3d5afe;
                alternate-background-color: #2e2e2e;
                show-decoration-selected: 1;
            }
            
            /* Tree item styling - exact Studio Library specifications */
            QTreeWidget::item {
                height: 36px;
                padding: 10px 12px;
                margin: 0px;
                border: none;
                border-radius: 6px;
                background-color: #2e2e2e;
                color: #eeeeee;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            /* Selected item - Studio Library blue highlight */
            QTreeWidget::item:selected {
                background-color: #3d5afe !important;
                color: white !important;
                font-weight: normal;
                border: none;
            }
            
            /* Hover state for non-selected items */
            QTreeWidget::item:hover:!selected {
                background-color: #3a3a3a !important;
                color: #ffffff;
            }
            
            /* Selected item hover (keep selected styling) */
            QTreeWidget::item:selected:hover {
                background-color: #3d5afe !important;
                color: white !important;
            }
            
            /* Remove all green styling and ensure consistent backgrounds */
            QTreeWidget::item:alternate {
                background-color: #2e2e2e !important;
            }
            
            QTreeWidget::item:!selected {
                background-color: #2e2e2e !important;
            }
            
            /* Clean branch styling - no tree lines */
            QTreeWidget::branch {
                background: transparent;
                width: 16px;
                border: none;
            }
            
            QTreeWidget::branch:has-siblings:!adjoins-item,
            QTreeWidget::branch:has-siblings:adjoins-item,
            QTreeWidget::branch:!has-children:!has-siblings:adjoins-item,
            QTreeWidget::branch:closed:has-children:has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings,
            QTreeWidget::branch:closed:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:!has-siblings {
                background: transparent;
                border: none;
                image: none;
            }
            
            /* Toolbar button styling */
            QPushButton {
                background-color: #666;
                color: #eeeeee;
                border: 1px solid #777;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QPushButton:hover {
                background-color: #777;
                border-color: #4a90e2;
                color: #ffffff;
            }
            
            QPushButton:pressed {
                background-color: #555;
                border-color: #4a90e2;
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
        print(f"📁 TREE: Updating folder structure with: {list(folder_structure.keys())}")
        
        # Get custom folders from the structure
        custom_folders = folder_structure.get("Custom Folders", {}).get("children", {})
        
        # Store the folder structure
        self.folder_structure = {
            "🎬 All Animations": {"type": "root", "filter": "all", "count": 0}
        }
        
        # Add custom folders to structure
        for folder_name, folder_data in custom_folders.items():
            # Ensure folder has proper data structure
            if isinstance(folder_data, dict):
                folder_data["type"] = "folder"
                self.folder_structure[folder_name] = folder_data
            else:
                # Create proper folder data if missing
                self.folder_structure[folder_name] = {
                    "type": "folder",
                    "filter": f"folder:{folder_name.replace('📁 ', '').replace('🧪 ', '')}",
                    "count": 0
                }
        
        print(f"📁 TREE: Stored folder structure: {list(self.folder_structure.keys())}")
        self.refresh_tree()
    
    def refresh_tree(self):
        """Refresh the tree widget display with proper folder hierarchy"""
        self.tree_widget.clear()
        
        # Always add "All Animations" root first
        root_data = {"type": "root", "filter": "all", "count": 0}
        root_item = self.create_tree_item("🎬 All Animations", root_data)
        root_item.setExpanded(True)
        self.tree_widget.addTopLevelItem(root_item)
        
        # Add custom folders from folder_structure
        if hasattr(self, 'folder_structure'):
            for folder_name, folder_data in self.folder_structure.items():
                if folder_name == "🎬 All Animations":
                    continue  # Skip root, already added
                
                # Create folder item
                folder_item = self.create_tree_item(folder_name, folder_data)
                self.tree_widget.addTopLevelItem(folder_item)
        
        # Select root by default
        if self.tree_widget.topLevelItemCount() > 0:
            first_item = self.tree_widget.topLevelItem(0)
            first_item.setSelected(True)
            self.current_selection = "all"
        
        print(f"🔄 TREE: Displayed {self.tree_widget.topLevelItemCount()} items in tree")

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
    
    def _is_item_draggable(self, item: QTreeWidgetItem) -> bool:
        """Check if a tree item can be dragged"""
        if not item:
            return False
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return False
        item_type = item_data.get("type", "")
        # Root cannot be dragged
        if item_type == "root":
            return False
        # Custom folders can be dragged
        if item_type == "folder":
            return True
        return False
    
    def on_item_clicked(self, item: QTreeWidgetItem, column: int = 0):
        """Handle item click in the folder tree"""
        _ = column  # Unused parameter

        if not item:
            return

        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return

        item_type = item_data.get("type", "folder")
        filter_value = item_data.get("filter", "")

        if item_type == "root":
            # Clicked on "All Animations" - show all
            self.current_selection = "all"
            self.folder_selected.emit("all")
            print("📁 Root selected: All Animations")
            
        elif item_type == "folder":
            # Clicked on a custom folder - filter by folder name
            folder_display_name = item.text(0).split(" (")[0]
            folder_name = folder_display_name.replace("📁 ", "").replace("🧪 ", "")

            self.current_selection = f"folder:{folder_name}"
            self.folder_selected.emit(f"folder:{folder_name}")
            print(f"📁 Custom folder selected: {folder_name} (filter: folder:{folder_name})")
            
        elif item_type == "filter" and filter_value:
            # Handle other filter types
            self.current_selection = filter_value
            self.folder_selected.emit(filter_value)
            print(f"📁 Filter selected: {filter_value}")
    
    def show_context_menu(self, position):
        """Show context menu for folder operations"""
        item = self.tree_widget.itemAt(position)
        menu = QMenu(self)
        if item:
            item_data = item.data(0, Qt.UserRole)
            item_type = item_data.get("type", "") if item_data else ""
            if item_type == "folder":
                # Add folder-specific actions
                add_sub = menu.addAction("📁 Create Subfolder")
                add_sub.triggered.connect(lambda: self.create_subfolder(item))
                menu.addSeparator()
                move_up = menu.addAction("⬆️ Move Up")
                move_up.triggered.connect(lambda: print("📁 Move folder up - to be implemented"))
                delete = menu.addAction("🗑️ Delete Folder")
                delete.triggered.connect(lambda: self.delete_folder(item))
        else:
            # Root level context menu
            add = menu.addAction("📁 Create Folder")
            add.triggered.connect(self.create_new_folder)
        menu.exec(self.tree_widget.mapToGlobal(position))

    def create_new_folder(self):
        """Create a new folder at root level"""
        folder_name, ok = QInputDialog.getText(
            self,
            "Create Folder",
            "Enter folder name:",
            text="New Folder"
        )
        if ok and folder_name.strip():
            folder_name = folder_name.strip()
            print(f"📁 Requesting folder creation: {folder_name}")
            self.folder_created.emit(folder_name)

    def create_subfolder(self, parent_item: QTreeWidgetItem):
        """Create a subfolder under the given parent item"""
        if not parent_item:
            return
        parent_data = parent_item.data(0, Qt.UserRole)
        if not parent_data:
            return
        parent_display = parent_item.text(0).split(" (")[0]
        parent_folder_name = parent_display.replace("📁 ", "").replace("🧪 ", "")
        sub_name, ok = QInputDialog.getText(
            self,
            "Create Subfolder",
            f"Enter subfolder name for '{parent_folder_name}':",
            text="New Subfolder"
        )
        if ok and sub_name.strip():
            sub_name = sub_name.strip()
            full_path = f"{parent_folder_name}/{sub_name}"
            print(f"📁 Requesting subfolder creation: {full_path}")
            self.folder_created.emit(full_path)

    def delete_folder(self, item: QTreeWidgetItem):
        """Delete the selected folder"""
        if not item:
            return
        item_data = item.data(0, Qt.UserRole)
        if not item_data or item_data.get("type") != "folder":
            return
        folder_display = item.text(0).split(" (")[0]
        folder_name = folder_display.replace("📁 ", "").replace("🧪 ", "")
        reply = QMessageBox.question(
            self,
            "Delete Folder",
            f"Are you sure you want to delete the folder '{folder_name}'?\n\nAll animations in this folder will be moved to the Root folder.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            print(f"🗑️ Requesting folder deletion: {folder_name}")
            self.folder_deleted.emit(folder_name)
    
    def create_tree_item(self, name: str, data: Dict[str, Any], parent: Optional[QTreeWidgetItem] = None) -> QTreeWidgetItem:
        """Create a tree widget item with proper styling"""
        if parent:
            item = QTreeWidgetItem(parent)
        else:
            item = QTreeWidgetItem()
        
        # Set item text and data
        item_type = data.get("type", "folder")
        count = data.get("count")
        
        # Create display name with count if available
        if count is not None and count > 0:
            display_name = f"{name} ({count})"
        else:
            display_name = name
        
        item.setText(0, display_name)
        item.setData(0, Qt.UserRole, data)
        
        # Store item type for reference
        item.setData(0, Qt.UserRole + 1, item_type)
        
        # Set font properties based on item type
        font = item.font(0)
        if item_type == "root":
            font.setBold(True)
            font.setPointSize(13)
            item.setFont(0, font)
        elif item_type == "category":
            font.setBold(True)
            font.setPointSize(12)
            item.setFont(0, font)
        elif item_type == "folder":
            font.setPointSize(11)
            item.setFont(0, font)
        
        # Add children if present
        children = data.get("children", {})
        for child_name, child_data in children.items():
            self.create_tree_item(child_name, child_data, item)
        
        return item

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
        """Enhanced drag move with Maya-style visual feedback"""
        if event.mimeData().hasText():
            data = event.mimeData().text()
            
            if data.startswith("animation_id:") or data.startswith("folder:") or data.startswith("batch_folders:"):
                # Get item under cursor for highlighting
                item = self.tree_widget.itemAt(event.pos())
                
                if item:
                    item_data = item.data(0, Qt.UserRole)
                    item_type = item_data.get("type", "") if item_data else ""
                    
                    # Enhanced drop validation
                    is_valid_target = False
                    
                    if data.startswith("folder:") or data.startswith("batch_folders:"):
                        # For folder drops, validate nesting rules
                        if data.startswith("folder:"):
                            folder_name = data.replace("folder:", "")
                            folders = [folder_name]
                        else:
                            folders = data.replace("batch_folders:", "").split(",")
                        
                        target_folder = self._get_folder_path_from_item(item)
                        
                        # Check if all folders can be dropped
                        is_valid_target = all(
                            self.can_drop_folder_on_target(folder, target_folder or "Root") 
                            for folder in folders
                        )
                    else:
                        # For animation drops, allow on folders and root
                        is_valid_target = item_type in ["folder", "root"]
                    
                    if is_valid_target:
                        # Show Maya-style drop preview
                        self.show_drop_preview(item, 2)  # On item
                        self.tree_widget.setCurrentItem(item)
                        
                        # Auto-expand on hover
                        self.auto_expand_on_hover(item)
                        
                        # Smart scroll during drag
                        self.smart_scroll_during_drag(event)
                        
                        event.acceptProposedAction()
                        return
                    else:
                        # Show invalid drop indicator
                        self.hide_drop_preview()
                
                # Handle auto-scroll even without valid target
                self.smart_scroll_during_drag(event)
                event.ignore()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def tree_dragLeaveEvent(self, event):
        """Handle drag leave to clean up visual indicators"""
        self.hide_drop_preview()
        self._stop_drag_scroll()
        self.auto_expand_timer.stop()
        event.accept()
    
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
        """Enhanced start drag with Maya-style multi-selection support"""
        _ = supportedActions  # Unused parameter
        
        # Check if we have multi-selection
        selected_items = self.tree_widget.selectedItems()
        draggable_items = [item for item in selected_items if self._is_item_draggable(item)]
        
        if not draggable_items:
            print("🚫 No draggable items selected")
            return
        
        self.is_dragging = True
        
        if len(draggable_items) == 1:
            # Single folder drag
            current_item = draggable_items[0]
            folder_name = self._get_folder_name_from_item(current_item)
            
            # Create mime data
            mime_data = QMimeData()
            mime_data.setText(f"folder:{folder_name}")
            
            # Create drag operation with Maya-style pixmap
            drag = QDrag(self.tree_widget)
            drag.setMimeData(mime_data)
            drag.setPixmap(self.create_single_drag_pixmap(folder_name))
            
            print(f"📁 Starting single folder drag: {folder_name}")
            
            # Execute drag
            result = drag.exec_(Qt.MoveAction)
            if result == Qt.MoveAction:
                print(f"📁 Single folder drag completed: {folder_name}")
        else:
            # Multi-folder drag
            folder_names = [self._get_folder_name_from_item(item) for item in draggable_items]
            
            # Start batch drag operation
            self.start_batch_folder_drag(folder_names)
        
        self.is_dragging = False
    
    # ==================================================
    # MAYA STUDIO LIBRARY STYLE ENHANCEMENTS
    # ==================================================
    
    def handle_multi_folder_selection(self, event):
        """Handle Ctrl+Click and Shift+Click for multiple folders"""
        modifiers = QApplication.keyboardModifiers()
        current_item = self.tree_widget.itemAt(event.pos())
        
        if not current_item or not self._is_item_draggable(current_item):
            return
        
        folder_name = self._get_folder_name_from_item(current_item)
        
        if modifiers == Qt.ControlModifier:
            # Ctrl+Click: Toggle individual folder selection
            if folder_name in self.selected_folders:
                self.selected_folders.remove(folder_name)
                current_item.setSelected(False)
            else:
                self.selected_folders.append(folder_name)
                current_item.setSelected(True)
        elif modifiers == Qt.ShiftModifier:
            # Shift+Click: Select range of folders
            self._select_folder_range(current_item)
        else:
            # Normal click: Select single folder
            self.selected_folders = [folder_name]
            self.tree_widget.clearSelection()
            current_item.setSelected(True)
        
        # Emit multi-selection signal
        if len(self.selected_folders) > 1:
            self.multi_folder_selected.emit(self.selected_folders)
    
    def _select_folder_range(self, end_item: QTreeWidgetItem):
        """Select range of folders from last selected to current"""
        # Implementation for Shift+Click range selection
        # This would require tracking the last selected item
        pass
    
    def _get_folder_name_from_item(self, item: QTreeWidgetItem) -> str:
        """Extract clean folder name from tree item"""
        folder_display_name = item.text(0).split(" (")[0]
        return folder_display_name.replace("📁 ", "")
    
    def start_batch_folder_drag(self, selected_folders: List[str]):
        """Handle dragging multiple folders simultaneously"""
        if len(selected_folders) <= 1:
            return
        
        # Create custom drag pixmap showing folder count
        pixmap = self.create_batch_drag_pixmap(selected_folders)
        
        # Create mime data for batch operation
        mime_data = QMimeData()
        mime_data.setText(f"batch_folders:{','.join(selected_folders)}")
        
        # Create drag operation
        drag = QDrag(self.tree_widget)
        drag.setMimeData(mime_data)
        drag.setPixmap(pixmap)
        
        print(f"📁 Starting batch drag for {len(selected_folders)} folders")
        self.batch_move_started.emit(selected_folders, "")
        
        # Execute drag with move action
        result = drag.exec_(Qt.MoveAction)
        if result == Qt.MoveAction:
            print(f"📁 Batch drag completed successfully")
    
    def create_batch_drag_pixmap(self, folders: List[str]) -> QPixmap:
        """Create professional drag preview for multiple folders"""
        pixmap = QPixmap(120, 40)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Maya-style semi-transparent background
        background_color = QColor(74, 144, 226, 180)
        painter.fillRect(pixmap.rect(), background_color)
        
        # Border
        pen = QPen(QColor(74, 144, 226), 2)
        painter.setPen(pen)
        painter.drawRect(pixmap.rect().adjusted(1, 1, -1, -1))
        
        # Text
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        text = f"📁 {len(folders)} folders"
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        
        painter.end()
        return pixmap
    
    def create_drag_pixmap(self, folders: List[str]) -> QPixmap:
        """Create professional drag preview with Maya-style design"""
        if len(folders) == 1:
            return self.create_single_drag_pixmap(folders[0])
        else:
            return self.create_batch_drag_pixmap(folders)
    
    def create_single_drag_pixmap(self, folder_name: str) -> QPixmap:
        """Create drag preview for single folder"""
        pixmap = QPixmap(100, 30)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Semi-transparent background
        background_color = QColor(74, 144, 226, 150)
        painter.fillRect(pixmap.rect(), background_color)
        
        # Text
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 9))
        text = f"📁 {folder_name}"
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        
        painter.end()
        return pixmap
    
    def auto_expand_on_hover(self, item: QTreeWidgetItem, hover_time: int = 800):
        """Auto-expand folders during drag hover with Maya-style delay"""
        if not item or not self.is_dragging:
            return
        
        # Only expand if folder contains subfolders
        if item.childCount() == 0:
            return
        
        # Only expand if not already expanded
        if item.isExpanded():
            return
        
        self.hover_item = item
        self.auto_expand_timer.start(hover_time)
    
    def _auto_expand_folder(self):
        """Execute auto-expansion of hovered folder"""
        if self.hover_item and not self.hover_item.isExpanded():
            # Collapse previous auto-expanded items
            for prev_item in self.last_auto_expanded_items:
                if prev_item != self.hover_item and prev_item.isExpanded():
                    prev_item.setExpanded(False)
            
            # Expand current item
            self.hover_item.setExpanded(True)
            self.last_auto_expanded_items.append(self.hover_item)
            
            # Emit signal
            folder_name = self._get_folder_name_from_item(self.hover_item)
            self.folder_auto_expanded.emit(folder_name)
            
            print(f"📁 Auto-expanded folder: {folder_name}")
    
    def smart_scroll_during_drag(self, event):
        """Auto-scroll tree during drag operations with Maya-style smoothness"""
        if not self.is_dragging:
            return
        
        # Get viewport rect
        viewport = self.tree_widget.viewport()
        viewport_rect = viewport.rect()
        
        # Check if near edges (20px threshold)
        edge_threshold = 20
        pos = event.pos()
        
        if pos.y() < edge_threshold:
            # Near top edge - scroll up
            self.scroll_direction = -1
            self._start_drag_scroll()
        elif pos.y() > viewport_rect.height() - edge_threshold:
            # Near bottom edge - scroll down
            self.scroll_direction = 1
            self._start_drag_scroll()
        else:
            # Not near edges - stop scrolling
            self._stop_drag_scroll()
    
    def _start_drag_scroll(self):
        """Start auto-scroll timer"""
        if not self.drag_scroll_timer.isActive():
            self.drag_scroll_timer.start(50)  # 50ms intervals for smooth scrolling
    
    def _stop_drag_scroll(self):
        """Stop auto-scroll timer"""
        self.drag_scroll_timer.stop()
        self.scroll_direction = 0
    
    def _handle_drag_scroll(self):
        """Handle auto-scroll during drag"""
        if self.scroll_direction != 0:
            scroll_bar = self.tree_widget.verticalScrollBar()
            current_value = scroll_bar.value()
            
            # Variable scroll speed based on direction
            scroll_amount = 5 * self.scroll_direction
            new_value = current_value + scroll_amount
            
            # Clamp to valid range
            new_value = max(scroll_bar.minimum(), min(scroll_bar.maximum(), new_value))
            scroll_bar.setValue(new_value)
    
    def show_drop_preview(self, target_item: QTreeWidgetItem, position: int):
        """Show Maya-style drop preview"""
        if not target_item:
            return
        
        # Get item rect
        item_rect = self.tree_widget.visualItemRect(target_item)
        
        # Update delegate with drop indicator
        self.item_delegate.set_drop_indicator(item_rect, True)
        
        # Show insertion line if needed
        if position == 0:  # Above item
            self.item_delegate.set_insertion_line(True, 0)
        elif position == 1:  # Below item
            self.item_delegate.set_insertion_line(True, 1)
        else:  # On item
            self.item_delegate.set_insertion_line(False)
        
        # Force repaint
        self.tree_widget.viewport().update(item_rect)
    
    def hide_drop_preview(self):
        """Hide drop preview indicators"""
        self.item_delegate.set_drop_indicator(QRect(), False)
        self.item_delegate.set_insertion_line(False)
        self.tree_widget.viewport().update()
    
    def create_folder_from_selection(self, selected_animations: List[str]):
        """Create folder and move selected animations with smart naming"""
        if not selected_animations:
            return
        
        # Smart folder naming based on animation types or common patterns
        suggested_name = self._suggest_folder_name(selected_animations)
        
        folder_name, ok = QInputDialog.getText(
            self, "Create Folder from Selection", 
            "Enter folder name for selected animations:",
            text=suggested_name
        )
        
        if ok and folder_name.strip():
            folder_name = folder_name.strip()
            
            # Create folder
            self.folder_created.emit(folder_name)
            
            # Emit signal to move animations (handled by main window)
            for animation_id in selected_animations:
                self.animation_moved.emit(animation_id, folder_name)
            
            print(f"📁 Created folder '{folder_name}' with {len(selected_animations)} animations")
    
    def _suggest_folder_name(self, animation_ids: List[str]) -> str:
        """Suggest smart folder name based on animation characteristics"""
        # This could analyze animation names for common patterns
        # For now, return a simple suggestion
        if len(animation_ids) == 1:
            return f"Folder for {animation_ids[0]}"
        else:
            return f"Animation Group ({len(animation_ids)} items)"
    
    def auto_organize_folders(self, organization_rules: Dict[str, Any]):
        """Auto-organize folders by criteria with preview"""
        # This would implement smart folder organization
        # Based on animation metadata, character names, etc.
        print("📁 Auto-organization feature - to be implemented based on metadata")
        self.folder_organization_changed.emit(organization_rules)
    
    def can_drop_folder_on_target(self, source_folder: str, target_folder: str) -> bool:
        """Validate folder nesting rules for Maya-style behavior"""
        # Prevent circular nesting (folder into itself)
        if source_folder == target_folder:
            return False
        
        # Check if target is a child of source (would create circular reference)
        if self._is_target_child_of_source(source_folder, target_folder):
            return False
        
        # Check maximum nesting depth (e.g., 5 levels)
        if self._get_nesting_depth(target_folder) >= 5:
            return False
        
        # Check for naming conflicts
        if self._would_create_naming_conflict(source_folder, target_folder):
            return False
        
        return True
    
    def _is_target_child_of_source(self, source: str, target: str) -> bool:
        """Check if target folder is a child of source folder"""
        # Implementation would check folder hierarchy
        return target.startswith(f"{source}/")
    
    def _get_nesting_depth(self, folder_path: str) -> int:
        """Get the nesting depth of a folder path"""
        return folder_path.count("/")
    
    def _would_create_naming_conflict(self, source: str, target: str) -> bool:
        """Check if moving source into target would create naming conflicts"""
        # Implementation would check for existing folders with same name
        return False
    
    def create_enhanced_context_menu(self, item: QTreeWidgetItem, position: QPoint) -> QMenu:
        """Create enhanced context menu with Maya Studio Library features"""
        menu = QMenu(self)
        
        if not item:
            return menu
        
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return menu
        
        item_type = item_data.get("type", "")
        
        if item_type == "folder":
            # Enhanced folder operations
            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(lambda: self.rename_folder(item))
            menu.addAction(rename_action)
            
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(lambda: self.delete_folder(item))
            menu.addAction(delete_action)
            
            menu.addSeparator()
            
            # New Maya-style options
            add_sub_action = QAction("Create Subfolder", self)
            add_sub_action.triggered.connect(lambda: self.create_subfolder(item))
            menu.addAction(add_sub_action)
            
            move_up_action = QAction("Move Folder Up", self)
            move_up_action.triggered.connect(lambda: self._move_folder_up(item))
            menu.addAction(move_up_action)
            
            move_down_action = QAction("Move Folder Down", self)
            move_down_action.triggered.connect(lambda: self._move_folder_down(item))
            menu.addAction(move_down_action)
            
            menu.addSeparator()
            
            sort_action = QAction("Sort Subfolders A-Z", self)
            sort_action.triggered.connect(lambda: self._sort_subfolders(item))
            menu.addAction(sort_action)
            
            merge_action = QAction("Merge with Another Folder", self)
            merge_action.triggered.connect(lambda: self._merge_folders(item))
            menu.addAction(merge_action)
            
            menu.addSeparator()
            
            export_action = QAction("Export Folder Structure", self)
            export_action.triggered.connect(lambda: self._export_folder_structure(item))
            menu.addAction(export_action)
            
            properties_action = QAction("Folder Properties", self)
            properties_action.triggered.connect(lambda: self._show_folder_properties(item))
            menu.addAction(properties_action)
        
        return menu
    
    def _move_folder_up(self, item: QTreeWidgetItem):
        """Move folder up in the hierarchy"""
        print("📁 Move folder up - to be implemented")
    
    def _move_folder_down(self, item: QTreeWidgetItem):
        """Move folder down in the hierarchy"""
        print("📁 Move folder down - to be implemented")
    
    def _sort_subfolders(self, item: QTreeWidgetItem):
        """Sort subfolders alphabetically"""
        print("📁 Sort subfolders - to be implemented")
    
    def _merge_folders(self, item: QTreeWidgetItem):
        """Merge with another folder"""
        print("📁 Merge folders - to be implemented")
    
    def _export_folder_structure(self, item: QTreeWidgetItem):
        """Export folder structure"""
        print("📁 Export folder structure - to be implemented")
    
    def _show_folder_properties(self, item: QTreeWidgetItem):
        """Show folder properties dialog"""
        print("📁 Show folder properties - to be implemented")
    
    def _enhanced_mouse_press_event(self, event):
        """Enhanced mouse press event with Maya-style multi-selection support"""
        # Handle multi-selection with Ctrl/Shift
        if event.button() == Qt.LeftButton:
            self.handle_multi_folder_selection(event)
        
        # Call original mouse press event for other functionality
        QTreeWidget.mousePressEvent(self.tree_widget, event)
    
    def _on_selection_changed(self):
        """Handle selection changes for Maya-style behavior"""
        selected_items = self.tree_widget.selectedItems()
        draggable_items = [item for item in selected_items if self._is_item_draggable(item)]
        
        if draggable_items:
            self.selected_folders = [self._get_folder_name_from_item(item) for item in draggable_items]
            
            if len(self.selected_folders) > 1:
                self.multi_folder_selected.emit(self.selected_folders)
        else:
            self.selected_folders = []