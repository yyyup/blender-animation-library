"""
Animation Card Widget - Studio Library Style
Professional animation card display with metadata, actions, and drag & drop support
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QWidget, QMenu, QToolButton, QGraphicsDropShadowEffect, QGridLayout,
    QApplication, QInputDialog
)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QRect, QTimer, QMimeData
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QAction, QBrush, QPen, QLinearGradient, QDrag
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add core modules to path
gui_dir = Path(__file__).parent.parent.parent
if str(gui_dir) not in sys.path:
    sys.path.insert(0, str(gui_dir))

from core.animation_data import AnimationMetadata


class AnimationThumbnail(QLabel):
    """Clean thumbnail widget with 120x120 size and no overlays"""
    
    def __init__(self, animation_metadata: AnimationMetadata, parent=None):
        super().__init__(parent)
        self.animation_metadata = animation_metadata
        self.is_selected = False
        
        self.setFixedSize(120, 120)
        self.setAlignment(Qt.AlignCenter)
        
        # Load thumbnail image with clean styling
        self.load_thumbnail_image()
        
        # Clean styling with rounded corners
        self.setStyleSheet("""
            QLabel {
                border: none;
                border-radius: 8px;
                background-color: #2e2e2e;
            }
        """)
    
    def load_thumbnail_image(self):
        """Load thumbnail image from file or show placeholder"""
        thumbnail_loaded = False
        
        # Check if animation has thumbnail path in metadata
        if hasattr(self.animation_metadata, 'thumbnail') and self.animation_metadata.thumbnail:
            thumbnail_path = Path("animation_library") / self.animation_metadata.thumbnail
            if thumbnail_path.exists():
                # Load the actual thumbnail image
                pixmap = QPixmap(str(thumbnail_path))
                if not pixmap.isNull():
                    # Scale to fit 120x120 while maintaining aspect ratio
                    scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    # Create a centered pixmap with dark background
                    final_pixmap = QPixmap(120, 120)
                    final_pixmap.fill(QColor(46, 46, 46))  # #2e2e2e background
                    
                    painter = QPainter(final_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    
                    # Center the scaled image
                    x = (120 - scaled_pixmap.width()) // 2
                    y = (120 - scaled_pixmap.height()) // 2
                    painter.drawPixmap(x, y, scaled_pixmap)
                    
                    painter.end()
                    self.setPixmap(final_pixmap)
                    thumbnail_loaded = True
        
        # Fallback to animation name-based thumbnail path
        if not thumbnail_loaded:
            # Try to construct thumbnail path from animation name
            animation_id = getattr(self.animation_metadata, 'id', self.animation_metadata.name)
            thumbnail_filename = f"{animation_id}.png"
            thumbnail_path = Path("animation_library") / "thumbnails" / thumbnail_filename
            
            if thumbnail_path.exists():
                pixmap = QPixmap(str(thumbnail_path))
                if not pixmap.isNull():
                    # Scale to fit 120x120 while maintaining aspect ratio
                    scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    # Create a centered pixmap with dark background
                    final_pixmap = QPixmap(120, 120)
                    final_pixmap.fill(QColor(46, 46, 46))  # #2e2e2e background
                    
                    painter = QPainter(final_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    
                    # Center the scaled image
                    x = (120 - scaled_pixmap.width()) // 2
                    y = (120 - scaled_pixmap.height()) // 2
                    painter.drawPixmap(x, y, scaled_pixmap)
                    
                    painter.end()
                    self.setPixmap(final_pixmap)
                    thumbnail_loaded = True
        
        # Fallback to placeholder icon if no image found
        if not thumbnail_loaded:
            self.show_placeholder_icon()
    
    def show_placeholder_icon(self):
        """Show a clean placeholder icon for missing thumbnails"""
        pixmap = QPixmap(120, 120)
        pixmap.fill(QColor(46, 46, 46))  # #2e2e2e background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw simple animation icon
        painter.setPen(QPen(QColor("#666666"), 2))
        painter.setBrush(QBrush(QColor("#666666")))
        
        # Simple figure representation
        center_x, center_y = 60, 60
        
        # Head
        painter.drawEllipse(center_x-8, center_y-25, 16, 16)
        
        # Body
        painter.drawLine(center_x, center_y-9, center_x, center_y+15)
        
        # Arms
        painter.drawLine(center_x-12, center_y-5, center_x+12, center_y-5)
        
        # Legs
        painter.drawLine(center_x, center_y+15, center_x-8, center_y+30)
        painter.drawLine(center_x, center_y+15, center_x+8, center_y+30)
        
        painter.end()
        self.setPixmap(pixmap)
    
    def set_selected(self, selected: bool):
        """Set selection state"""
        self.is_selected = selected
        # Selection will be handled by the parent card
    
    def refresh_thumbnail(self, animation_name: str):
        """Refresh thumbnail for the specified animation"""
        # Check if animation has thumbnail path in metadata
        thumbnail_loaded = False
        
        # Check if animation has thumbnail path in metadata
        if hasattr(self.animation_metadata, 'thumbnail') and self.animation_metadata.thumbnail:
            thumbnail_path = Path("animation_library") / self.animation_metadata.thumbnail
            if thumbnail_path.exists():
                # Load the actual thumbnail image
                pixmap = QPixmap(str(thumbnail_path))
                if not pixmap.isNull():
                    # Scale to fit 120x120 while maintaining aspect ratio
                    scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    # Create a centered pixmap with dark background
                    final_pixmap = QPixmap(120, 120)
                    final_pixmap.fill(QColor(46, 46, 46))  # #2e2e2e background
                    
                    painter = QPainter(final_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    
                    # Center the scaled image
                    x = (120 - scaled_pixmap.width()) // 2
                    y = (120 - scaled_pixmap.height()) // 2
                    painter.drawPixmap(x, y, scaled_pixmap)
                    
                    painter.end()
                    self.setPixmap(final_pixmap)
                    thumbnail_loaded = True
        
        # Fallback to animation name-based thumbnail path
        if not thumbnail_loaded:
            # Try to construct thumbnail path from animation name
            animation_id = getattr(self.animation_metadata, 'id', self.animation_metadata.name)
            thumbnail_filename = f"{animation_id}.png"
            thumbnail_path = Path("animation_library") / "thumbnails" / thumbnail_filename
            
            if thumbnail_path.exists():
                pixmap = QPixmap(str(thumbnail_path))
                if not pixmap.isNull():
                    # Scale to fit 120x120 while maintaining aspect ratio
                    scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    # Create a centered pixmap with dark background
                    final_pixmap = QPixmap(120, 120)
                    final_pixmap.fill(QColor(46, 46, 46))  # #2e2e2e background
                    
                    painter = QPainter(final_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    
                    # Center the scaled image
                    x = (120 - scaled_pixmap.width()) // 2
                    y = (120 - scaled_pixmap.height()) // 2
                    painter.drawPixmap(x, y, scaled_pixmap)
                    
                    painter.end()
                    self.setPixmap(final_pixmap)
                    thumbnail_loaded = True
        
        # Fallback to placeholder icon if no image found
        if not thumbnail_loaded:
            self.show_placeholder_icon()
    
    def show_placeholder_icon(self):
        """Show a clean placeholder icon for missing thumbnails"""
        pixmap = QPixmap(120, 120)
        pixmap.fill(QColor(46, 46, 46))  # #2e2e2e background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw simple animation icon
        painter.setPen(QPen(QColor("#666666"), 2))
        painter.setBrush(QBrush(QColor("#666666")))
        
        # Simple figure representation
        center_x, center_y = 60, 60
        
        # Head
        painter.drawEllipse(center_x-8, center_y-25, 16, 16)
        
        # Body
        painter.drawLine(center_x, center_y-9, center_x, center_y+15)
        
        # Arms
        painter.drawLine(center_x-12, center_y-5, center_x+12, center_y-5)
        
        # Legs
        painter.drawLine(center_x, center_y+15, center_x-8, center_y+30)
        painter.drawLine(center_x, center_y+15, center_x+8, center_y+30)
        
        painter.end()
        self.setPixmap(pixmap)
    
        painter.end()
        self.setPixmap(pixmap)
    
    def set_selected(self, selected: bool):
        """Set selection state"""
        self.is_selected = selected
        # Selection will be handled by the parent card
    
    def refresh_thumbnail(self, animation_name: str):
        """Refresh thumbnail for the specified animation"""
        # Check if this thumbnail is for the updated animation
        animation_id = getattr(self.animation_metadata, 'id', self.animation_metadata.name)
        
        # Match by name or ID
        if (animation_name == self.animation_metadata.name or 
            animation_name == animation_id):
            # Reload the thumbnail image
            self.load_thumbnail_image()
            print(f"🖼️ Refreshed thumbnail for: {animation_name}")
    
class AnimationCard(QFrame):
    """Professional animation card with Studio Library styling and drag & drop support"""
    
    # Signals
    apply_requested = Signal(dict)
    edit_requested = Signal(dict)
    delete_requested = Signal(dict)
    preview_requested = Signal(dict)
    move_to_folder_requested = Signal(dict, str)  # NEW: For folder movement
    
    def __init__(self, animation_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.animation_data = animation_data
        self.animation_metadata = AnimationMetadata.from_dict(animation_data)
        self.is_hovered = False
        self.is_selected = False
        self.drag_start_position = None
        
        self.setup_ui()
        self.setup_animations()
        self.setup_style()
        
        # Enable drag and drop
        self.setAcceptDrops(False)  # Cards don't accept drops, only initiate drags
    
    def setup_ui(self):
        """Setup the card UI layout - Studio Library style"""
        self.setFixedSize(160, 220)  # Compact size for Studio Library style
        self.setFrameStyle(QFrame.NoFrame)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Thumbnail at top - 120x120px
        self.thumbnail = AnimationThumbnail(self.animation_metadata)
        layout.addWidget(self.thumbnail, 0, Qt.AlignHCenter)
        
        # Animation name (bold)
        self.title_label = QLabel(self.animation_metadata.name)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(32)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Optional metadata (frame count, rig type)
        metadata_widget = QWidget()
        metadata_layout = QVBoxLayout(metadata_widget)
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.setSpacing(2)
        
        # Frame count
        frame_label = QLabel(f"{int(self.animation_metadata.duration_frames)} frames")
        frame_label.setObjectName("metaLabel")
        frame_label.setAlignment(Qt.AlignCenter)
        metadata_layout.addWidget(frame_label)
        
        # Rig type
        rig_label = QLabel(self.animation_metadata.rig_type)
        rig_label.setObjectName("rigLabel")
        rig_label.setAlignment(Qt.AlignCenter)
        metadata_layout.addWidget(rig_label)
        
        layout.addWidget(metadata_widget)
        
        # Action buttons at bottom
        self.actions_widget = self.create_actions_section()
        layout.addWidget(self.actions_widget)
        
        # Add stretch to push everything to top
        layout.addStretch()
    
    def create_actions_section(self) -> QWidget:
        """Create the clean action buttons section"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        
        # Apply button
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setObjectName("applyButton")
        self.apply_btn.setFixedHeight(24)
        self.apply_btn.clicked.connect(lambda: self.apply_requested.emit(self.animation_data))
        layout.addWidget(self.apply_btn)
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("deleteButton")
        delete_btn.setFixedHeight(24)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.animation_data))
        layout.addWidget(delete_btn)
        
        # Rename button
        rename_btn = QPushButton("Rename")
        rename_btn.setObjectName("renameButton")
        rename_btn.setFixedHeight(24)
        rename_btn.clicked.connect(lambda: self.edit_requested.emit(self.animation_data))
        layout.addWidget(rename_btn)
        
        return widget
    
    def setup_animations(self):
        """Setup hover animations without shadows"""
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def setup_style(self):
        """Setup Studio Library style card styling"""
        self.setStyleSheet("""
            AnimationCard {
                border: none;
                border-radius: 8px;
                background-color: #2e2e2e;
            }
            
            AnimationCard:hover {
                background-color: #262626;
            }
            
            AnimationCard[selected="true"] {
                border: 1px solid #4a90e2;
                background-color: #2e2e2e;
            }
            
            #titleLabel {
                color: #eeeeee;
                font-size: 11px;
                font-weight: bold;
                padding: 2px;
            }
            
            #metaLabel {
                color: #cccccc;
                font-size: 9px;
                padding: 1px;
            }
            
            #rigLabel {
                color: #cccccc;
                font-size: 9px;
                padding: 1px;
            }
            
            #applyButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9px;
            }
            
            #applyButton:hover {
                background-color: #357abd;
            }
            
            #applyButton:pressed {
                background-color: #2968a3;
            }
            
            #deleteButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9px;
            }
            
            #deleteButton:hover {
                background-color: #c0392b;
            }
            
            #renameButton {
                background-color: #666;
                color: #cccccc;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9px;
            }
            
            #renameButton:hover {
                background-color: #777;
            }
        """)
    
    def enterEvent(self, event):
        """Handle mouse enter event"""
        self.is_hovered = True
        self.actions_widget.setVisible(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event"""
        self.is_hovered = False
        self.actions_widget.setVisible(False)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press for selection and drag start"""
        print(f"🖱️ Mouse press on card: {self.animation_metadata.name}")
        if event.button() == Qt.LeftButton:
            self.set_selected(True)
            self.drag_start_position = event.pos()
            print(f"🖱️ Drag start position set: {self.drag_start_position}")
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for drag initiation"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if not self.drag_start_position:
            return
        
        # Check if we've moved far enough to start a drag
        distance = (event.pos() - self.drag_start_position).manhattanLength()
        min_distance = QApplication.startDragDistance()
        
        print(f"🖱️ Mouse move - distance: {distance}, min: {min_distance}")
        
        if distance < min_distance:
            return
        
        print(f"🎬 Starting drag for: {self.animation_metadata.name}")
        # Start drag operation
        self.start_drag()
    
    def start_drag(self):
        """Start drag operation for this animation card"""
        print(f"🚀 Drag started for animation: {self.animation_metadata.name}")
        
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Set animation ID as drag data
        animation_id = self.animation_data.get('id', '')
        mime_data.setText(f"animation_id:{animation_id}")
        
        print(f"🎬 Drag data: animation_id:{animation_id}")
        
        drag.setMimeData(mime_data)
        
        # Create drag pixmap (thumbnail of the card)
        pixmap = self.grab()
        scaled_pixmap = pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Make it semi-transparent
        painter = QPainter(scaled_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        painter.fillRect(scaled_pixmap.rect(), QColor(0, 0, 0, 180))
        painter.end()
        
        drag.setPixmap(scaled_pixmap)
        drag.setHotSpot(scaled_pixmap.rect().center())
        
        # Execute drag
        print(f"🎬 Executing drag...")
        drop_action = drag.exec_(Qt.MoveAction)
        
        print(f"🎬 Drag completed for animation: {self.animation_metadata.name}, action: {drop_action}")
    
    def contextMenuEvent(self, event):
        """Show context menu with folder move options"""
        menu = QMenu(self)
        
        # Move to folder submenu
        move_menu = QMenu("Move to Folder", self)
        
        # Add some common folder options (these would come from the library manager)
        root_action = QAction("📁 Root", self)
        root_action.triggered.connect(lambda: self.move_to_folder_requested.emit(self.animation_data, "Root"))
        move_menu.addAction(root_action)
        
        # Separator for custom folders
        move_menu.addSeparator()
        
        # TODO: Add dynamic folder list from library manager
        # For now, just add a placeholder
        new_folder_action = QAction("+ Create New Folder...", self)
        new_folder_action.triggered.connect(self.show_folder_creation_dialog)
        move_menu.addAction(new_folder_action)
        
        menu.addMenu(move_menu)
        menu.addSeparator()
        
        # Other options
        preview_action = QAction("Preview", self)
        preview_action.triggered.connect(lambda: self.preview_requested.emit(self.animation_data))
        menu.addAction(preview_action)
        
        edit_action = QAction("Edit Metadata", self)
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.animation_data))
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.animation_data))
        menu.addAction(delete_action)
        
        menu.exec_(event.globalPos())
    
    def show_folder_creation_dialog(self):
        """Show dialog to create new folder and move animation there"""
        folder_name, ok = QInputDialog.getText(
            self, "Create Folder", 
            f"Create folder and move '{self.animation_metadata.name}' there:",
            text=""
        )
        
        if ok and folder_name.strip():
            folder_name = folder_name.strip()
            self.move_to_folder_requested.emit(self.animation_data, folder_name)
    
    def set_selected(self, selected: bool):
        """Set selection state"""
        self.is_selected = selected
        self.thumbnail.set_selected(selected)
        
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)
    
    def update_animation_data(self, animation_data: Dict[str, Any]):
        """Update the animation data and refresh display"""
        self.animation_data = animation_data
        self.animation_metadata = AnimationMetadata.from_dict(animation_data)
        
        # Update UI elements
        self.title_label.setText(self.animation_metadata.name)
        
        # Regenerate thumbnail
        self.thumbnail.animation_metadata = self.animation_metadata
        self.thumbnail.generate_thumbnail()
    
    def set_loading_state(self, loading: bool):
        """Set card loading state"""
        self.apply_btn.setEnabled(not loading)
        self.options_btn.setEnabled(not loading)
        
        if loading:
            self.apply_btn.setText("Applying...")
        else:
            self.apply_btn.setText("Apply")
    
    def refresh_thumbnail(self, animation_name: str):
        """Refresh thumbnail for the specified animation"""
        # Check if this card is for the updated animation
        if (animation_name == self.animation_metadata.name or 
            animation_name == getattr(self.animation_metadata, 'id', self.animation_metadata.name)):
            # Refresh the thumbnail
            self.thumbnail.refresh_thumbnail(animation_name)
            print(f"🎬 Refreshed card thumbnail for: {animation_name}")
    
class AnimationCardGrid(QWidget):
    """Grid container for animation cards with responsive layout"""
    
    animation_selected = Signal(dict)  # Emits selected animation data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards = []
        self.selected_card = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup grid layout"""
        from PySide6.QtWidgets import QScrollArea
        
        # Use scroll area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Grid widget
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.scroll_area.setWidget(self.grid_widget)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)
        
        # Styling
        self.setStyleSheet("""
            QScrollArea {
                background-color: #2e2e2e;
                border: none;
            }
            
            QScrollBar:vertical {
                background-color: #4a4a4a;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #666;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #777;
            }
        """)
    
    def add_card(self, animation_card):
        """Add animation card to grid"""
        # Connect selection signal properly
        original_mouse_press = animation_card.mousePressEvent
        
        def new_mouse_press(event):
            original_mouse_press(event)
            if event.button() == Qt.LeftButton:
                self.select_card(animation_card)
        
        animation_card.mousePressEvent = new_mouse_press
        
        self.cards.append(animation_card)
        self.refresh_layout()
    
    def select_card(self, card):
        """Select an animation card"""
        # Deselect previous card
        if self.selected_card:
            self.selected_card.set_selected(False)
        
        # Select new card
        self.selected_card = card
        card.set_selected(True)
        
        # Emit selection signal
        self.animation_selected.emit(card.animation_data)
    def remove_card(self, animation_card):
        """Remove animation card from grid with proper cleanup"""
        if animation_card in self.cards:
            print(f"🗑️ Removing animation card: {animation_card.animation_metadata.name}")
            
            # Remove from internal list first
            self.cards.remove(animation_card)
            
            # Clear selection if this card was selected
            if self.selected_card == animation_card:
                self.selected_card = None
            
            # Remove from layout
            self.grid_layout.removeWidget(animation_card)
            
            # Schedule for deletion to prevent memory leaks
            animation_card.deleteLater()
            
            # Refresh layout to fill the gap
            self.refresh_layout()
            
            print("✅ Animation card removed and layout refreshed")
    
    def rebuild_grid(self, new_cards_data):
        """Completely rebuild the grid with new animation data"""
        print(f"🔧 Rebuilding grid with {len(new_cards_data)} animations")
        
        # Step 1: Clear everything with proper cleanup
        self.clear_cards()
        
        # Step 2: Note - cards should be created externally and added via add_card()
        # This method is for coordination with the main window refresh logic
        
        print(f"✅ Grid cleared and ready for {len(new_cards_data)} new cards")
    
    def bulk_add_cards(self, cards_list):
        """Add multiple cards efficiently without refreshing layout each time"""
        print(f"📦 Bulk adding {len(cards_list)} animation cards...")
        
        # Add all cards to internal list first
        for card in cards_list:
            # Connect selection signal properly
            original_mouse_press = card.mousePressEvent
            
            def new_mouse_press(event, card_ref=card):
                original_mouse_press(event)
                if event.button() == Qt.LeftButton:
                    self.select_card(card_ref)
            
            card.mousePressEvent = new_mouse_press
            self.cards.append(card)
        
        # Refresh layout once at the end
        self.refresh_layout()
        
        print(f"✅ Bulk add completed: {len(self.cards)} total cards in grid")
    
    def update_grid_performance_mode(self, large_dataset=False):
        """Optimize grid for large datasets (200+ animations)"""
        if large_dataset:
            print("⚡ Enabling performance mode for large dataset...")
            # Disable animations and effects for better performance
            self.setUpdatesEnabled(False)
            self.grid_widget.setUpdatesEnabled(False)
        else:
            print("🎨 Enabling standard mode for normal dataset...")
            self.setUpdatesEnabled(True)
            self.grid_widget.setUpdatesEnabled(True)
            
        QApplication.processEvents()

    def clear_cards(self):
        """Clear all animation cards with proper cleanup"""
        print(f"🧹 Clearing {len(self.cards)} animation cards from grid")
        
        # First, remove all widgets from layout and properly delete them
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    # Remove from layout first
                    self.grid_layout.removeWidget(widget)
                    # Schedule for deletion to prevent memory leaks
                    widget.deleteLater()
                    
        # Clear the layout completely
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child:
                widget = child.widget()
                if widget:
                    widget.deleteLater()
        
        # Reset internal tracking
        self.cards.clear()
        self.selected_card = None
        
        # Process pending deletions
        QApplication.processEvents()
        
        print("✅ Animation cards cleared and memory cleaned up")
    
    def safe_delete_animation_card(self, animation_id: str):
        """Safely delete a specific animation card by ID"""
        card_to_remove = None
        for card in self.cards:
            if card.animation_data.get('id') == animation_id:
                card_to_remove = card
                break
        
        if card_to_remove:
            print(f"🗑️ Safely deleting animation card: {animation_id}")
            self.remove_card(card_to_remove)
            return True
        else:
            print(f"⚠️ Animation card not found for deletion: {animation_id}")
            return False
    
    def get_card_count(self) -> int:
        """Get the current number of cards in the grid"""
        return len(self.cards)
    
    def force_layout_cleanup(self):
        """Force cleanup of any orphaned layout items"""
        print("🧹 Performing force layout cleanup...")
        
        # Remove any widgets that might be in layout but not in cards list
        widgets_in_layout = []
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                widgets_in_layout.append(item.widget())
        
        cards_widgets = set(self.cards)
        orphaned_widgets = [w for w in widgets_in_layout if w not in cards_widgets]
        
        if orphaned_widgets:
            print(f"🚨 Found {len(orphaned_widgets)} orphaned widgets in layout")
            for widget in orphaned_widgets:
                self.grid_layout.removeWidget(widget)
                widget.deleteLater()
            QApplication.processEvents()
        else:
            print("✅ No orphaned widgets found")
    
    def refresh_layout(self):
        """Refresh the grid layout with complete rebuild"""
        print(f"🔄 Refreshing layout with {len(self.cards)} cards")
        
        # Step 1: Remove all widgets from layout without deleting them
        widgets_to_re_add = []
        
        # Collect all current widgets before clearing layout
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                self.grid_layout.removeWidget(widget)
                widgets_to_re_add.append(widget)
        
        # Clear any remaining layout items
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child and child.widget():
                child.widget().setParent(None)
        
        # Step 2: Calculate grid dimensions
        widget_width = self.scroll_area.viewport().width() - 24  # Account for margins
        card_width = 220 + 12  # Card width + spacing
        columns = max(1, widget_width // card_width)
        
        print(f"📐 Grid layout: {len(self.cards)} cards in {columns} columns")
        
        # Step 3: Re-add cards to grid in correct positions
        for i, card in enumerate(self.cards):
            row = i // columns
            col = i % columns
            self.grid_layout.addWidget(card, row, col)
        
        # Step 4: Add stretch to last row for proper spacing
        if self.cards:
            last_row = (len(self.cards) - 1) // columns + 1
            # Clear any existing row stretches first
            for r in range(last_row + 1):
                self.grid_layout.setRowStretch(r, 0)
            # Apply stretch to the last row
            self.grid_layout.setRowStretch(last_row, 1)
        
        # Force layout update
        self.grid_layout.update()
        self.grid_widget.update()
        
        print("✅ Layout refreshed successfully")
    
    def refresh_thumbnail(self, animation_name: str):
        """Refresh thumbnail for the specified animation across all cards"""
        refreshed_count = 0
        for card in self.cards:
            if hasattr(card, 'refresh_thumbnail'):
                # Check if this card is for the updated animation
                if (animation_name == card.animation_metadata.name or 
                    animation_name == getattr(card.animation_metadata, 'id', card.animation_metadata.name)):
                    card.refresh_thumbnail(animation_name)
                    refreshed_count += 1
        
        if refreshed_count > 0:
            print(f"🔄 Refreshed {refreshed_count} card(s) for animation: {animation_name}")
        else:
            print(f"⚠️ No cards found for animation: {animation_name}")