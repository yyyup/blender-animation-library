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
    """Custom thumbnail widget with performance indicators and overlays"""
    
    def __init__(self, animation_metadata: AnimationMetadata, parent=None):
        super().__init__(parent)
        self.animation_metadata = animation_metadata
        self.is_selected = False
        
        self.setFixedSize(180, 120)
        self.setAlignment(Qt.AlignCenter)
        
        # Generate thumbnail
        self.generate_thumbnail()
        
        # Setup styling
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #555;
                border-radius: 6px;
                background-color: #393939;
            }
        """)
    
    def generate_thumbnail(self):
        """Generate a procedural thumbnail for the animation"""
        # Create a pixmap for the thumbnail
        pixmap = QPixmap(180, 120)
        pixmap.fill(QColor(57, 57, 57))  # Dark background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background gradient
        gradient = QLinearGradient(0, 0, 180, 120)
        gradient.setColorAt(0, QColor(70, 70, 70))
        gradient.setColorAt(1, QColor(45, 45, 45))
        painter.fillRect(0, 0, 180, 120, QBrush(gradient))
        
        # Rig type indicator
        from core.animation_data import RigTypeDetector
        rig_color = RigTypeDetector.get_rig_color(self.animation_metadata.rig_type)
        rig_emoji = RigTypeDetector.get_rig_emoji(self.animation_metadata.rig_type)
        
        # Top-left rig indicator
        painter.setPen(QPen(QColor(rig_color), 2))
        painter.setBrush(QBrush(QColor(rig_color).darker(150)))
        painter.drawRoundedRect(8, 8, 24, 16, 3, 3)
        
        # Rig emoji/text
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.drawText(10, 20, rig_emoji)
        
        # Storage method indicator (top-right)
        perf_info = self.animation_metadata.get_performance_info()
        status_color = "#51cf66" if self.animation_metadata.is_blend_file_storage() else "#ffd43b"
        
        painter.setPen(QPen(QColor(status_color), 2))
        painter.setBrush(QBrush(QColor(status_color).darker(150)))
        painter.drawRoundedRect(148, 8, 24, 16, 3, 3)
        
        # Performance emoji
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.drawText(152, 20, perf_info['status_emoji'])
        
        # Central animation icon/visualization
        painter.setPen(QPen(QColor("#4a90e2"), 3))
        
        # Draw simple bone visualization
        bone_count = min(self.animation_metadata.total_bones_animated, 8)
        center_x, center_y = 90, 60
        
        for i in range(bone_count):
            angle = (i / bone_count) * 360
            import math
            x = center_x + 20 * math.cos(math.radians(angle))
            y = center_y + 20 * math.sin(math.radians(angle))
            
            # Draw bone as small circle
            painter.setBrush(QBrush(QColor("#4a90e2")))
            painter.drawEllipse(int(x-3), int(y-3), 6, 6)
            
            # Draw connection to center
            painter.drawLine(center_x, center_y, int(x), int(y))
        
        # Central hub
        painter.setBrush(QBrush(QColor("#4a90e2").lighter(120)))
        painter.drawEllipse(center_x-5, center_y-5, 10, 10)
        
        # Duration indicator (bottom-right)
        duration_text = f"{int(self.animation_metadata.duration_frames)}f"
        painter.setPen(QPen(QColor("black"), 1))
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        painter.drawRoundedRect(130, 95, 40, 16, 8, 8)
        
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(135, 106, duration_text)
        
        # Keyframe density visualization (bottom)
        keyframe_density = self.animation_metadata.total_keyframes / max(self.animation_metadata.duration_frames, 1)
        density_width = int((keyframe_density / 20) * 160)  # Max 160px width
        density_width = min(max(density_width, 10), 160)  # Clamp between 10-160
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#ffd43b").darker(130)))
        painter.drawRoundedRect(10, 108, density_width, 4, 2, 2)
        
        painter.end()
        self.setPixmap(pixmap)
    
    def set_selected(self, selected: bool):
        """Set selection state"""
        self.is_selected = selected
        if selected:
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid #4a90e2;
                    border-radius: 6px;
                    background-color: #454545;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    border: 1px solid #555;
                    border-radius: 6px;
                    background-color: #393939;
                }
            """)


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
        """Setup the card UI layout"""
        self.setFixedSize(200, 280)
        self.setFrameStyle(QFrame.NoFrame)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Thumbnail
        self.thumbnail = AnimationThumbnail(self.animation_metadata)
        layout.addWidget(self.thumbnail)
        
        # Info section
        info_widget = self.create_info_section()
        layout.addWidget(info_widget)
        
        # Actions section (hidden by default, shown on hover)
        self.actions_widget = self.create_actions_section()
        self.actions_widget.setVisible(False)
        layout.addWidget(self.actions_widget)
    
    def create_info_section(self) -> QWidget:
        """Create the information section"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # Title
        self.title_label = QLabel(self.animation_metadata.name)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(32)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(self.title_label)
        
        # Metadata row 1: Duration and bones
        meta1_widget = QWidget()
        meta1_layout = QHBoxLayout(meta1_widget)
        meta1_layout.setContentsMargins(0, 0, 0, 0)
        meta1_layout.setSpacing(8)
        
        duration_label = QLabel(f"{int(self.animation_metadata.duration_frames)}f")
        duration_label.setObjectName("metaLabel")
        meta1_layout.addWidget(duration_label)
        
        bones_label = QLabel(f"{self.animation_metadata.total_bones_animated} bones")
        bones_label.setObjectName("metaLabel")
        meta1_layout.addWidget(bones_label)
        
        meta1_layout.addStretch()
        layout.addWidget(meta1_widget)
        
        # Metadata row 2: Performance and rig
        meta2_widget = QWidget()
        meta2_layout = QHBoxLayout(meta2_widget)
        meta2_layout.setContentsMargins(0, 0, 0, 0)
        meta2_layout.setSpacing(8)
        
        # Performance indicator
        perf_info = self.animation_metadata.get_performance_info()
        perf_label = QLabel(f"{perf_info['status_emoji']} {perf_info['application_time']}")
        perf_label.setObjectName("perfLabel")
        
        if self.animation_metadata.is_blend_file_storage():
            perf_label.setStyleSheet("color: #51cf66; font-weight: bold; font-size: 9px;")
        else:
            perf_label.setStyleSheet("color: #ffd43b; font-weight: bold; font-size: 9px;")
        
        meta2_layout.addWidget(perf_label)
        
        # Rig type
        from core.animation_data import RigTypeDetector
        rig_emoji = RigTypeDetector.get_rig_emoji(self.animation_metadata.rig_type)
        rig_color = RigTypeDetector.get_rig_color(self.animation_metadata.rig_type)
        
        rig_label = QLabel(f"{rig_emoji} {self.animation_metadata.rig_type}")
        rig_label.setObjectName("rigLabel")
        rig_label.setStyleSheet(f"color: {rig_color}; font-weight: bold; font-size: 9px;")
        meta2_layout.addWidget(rig_label)
        
        meta2_layout.addStretch()
        layout.addWidget(meta2_widget)
        
        # Tags (first 2)
        if self.animation_metadata.tags:
            tags_widget = QWidget()
            tags_layout = QHBoxLayout(tags_widget)
            tags_layout.setContentsMargins(0, 0, 0, 0)
            tags_layout.setSpacing(4)
            
            for tag in self.animation_metadata.tags[:2]:
                tag_label = QLabel(tag)
                tag_label.setObjectName("tagLabel")
                tags_layout.addWidget(tag_label)
            
            if len(self.animation_metadata.tags) > 2:
                more_label = QLabel(f"+{len(self.animation_metadata.tags) - 2}")
                more_label.setObjectName("moreTagsLabel")
                tags_layout.addWidget(more_label)
            
            tags_layout.addStretch()
            layout.addWidget(tags_widget)
        
        return widget
    
    def create_actions_section(self) -> QWidget:
        """Create the actions section"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)
        
        # Apply button
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setObjectName("applyButton")
        self.apply_btn.setFixedHeight(24)
        self.apply_btn.clicked.connect(lambda: self.apply_requested.emit(self.animation_data))
        layout.addWidget(self.apply_btn)
        
        # Options menu button
        self.options_btn = QToolButton()
        self.options_btn.setObjectName("optionsButton")
        self.options_btn.setText("⋯")
        self.options_btn.setFixedSize(24, 24)
        self.options_btn.setToolTip("More options")
        
        # Create options menu
        options_menu = QMenu(self)
        
        preview_action = QAction("Preview", self)
        preview_action.triggered.connect(lambda: self.preview_requested.emit(self.animation_data))
        options_menu.addAction(preview_action)
        
        edit_action = QAction("Edit Metadata", self)
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.animation_data))
        options_menu.addAction(edit_action)
        
        options_menu.addSeparator()
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.animation_data))
        options_menu.addAction(delete_action)
        
        self.options_btn.setMenu(options_menu)
        self.options_btn.setPopupMode(QToolButton.InstantPopup)
        
        layout.addWidget(self.options_btn)
        
        return widget
    
    def setup_animations(self):
        """Setup hover animations"""
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Add subtle drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)
    
    def setup_style(self):
        """Setup card styling"""
        self.setStyleSheet("""
            AnimationCard {
                border: 1px solid #555;
                border-radius: 8px;
                background-color: #4a4a4a;
            }
            
            AnimationCard:hover {
                border-color: #4a90e2;
                background-color: #525252;
            }
            
            AnimationCard[selected="true"] {
                border-color: #4a90e2;
                border-width: 2px;
                background-color: #525252;
            }
            
            #titleLabel {
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
                padding: 0px;
            }
            
            #metaLabel {
                color: #cccccc;
                font-size: 9px;
                padding: 0px;
            }
            
            #tagLabel {
                background-color: #4a90e2;
                color: white;
                padding: 1px 6px;
                border-radius: 8px;
                font-size: 8px;
                font-weight: bold;
            }
            
            #moreTagsLabel {
                color: #888888;
                font-size: 8px;
                font-style: italic;
            }
            
            #applyButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }
            
            #applyButton:hover {
                background-color: #357abd;
            }
            
            #applyButton:pressed {
                background-color: #2968a3;
            }
            
            #optionsButton {
                background-color: #666;
                color: #cccccc;
                border: 1px solid #777;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            
            #optionsButton:hover {
                background-color: #777;
                border-color: #4a90e2;
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
        """Remove animation card from grid"""
        if animation_card in self.cards:
            self.cards.remove(animation_card)
            animation_card.setParent(None)
            self.refresh_layout()
    
    def clear_cards(self):
        """Clear all animation cards"""
        for card in self.cards:
            card.setParent(None)
        self.cards.clear()
        self.selected_card = None
    
    def refresh_layout(self):
        """Refresh the grid layout"""
        # Clear layout
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item:
                self.grid_layout.removeItem(item)
        
        # Calculate columns based on widget width
        widget_width = self.scroll_area.viewport().width() - 24  # Account for margins
        card_width = 220 + 12  # Card width + spacing
        columns = max(1, widget_width // card_width)
        
        # Add cards to grid
        for i, card in enumerate(self.cards):
            row = i // columns
            col = i % columns
            self.grid_layout.addWidget(card, row, col)
        
        # Add stretch to last row
        if self.cards:
            last_row = (len(self.cards) - 1) // columns + 1
            self.grid_layout.setRowStretch(last_row, 1)
    
    def resizeEvent(self, event):
        """Handle resize event to adjust grid"""
        super().resizeEvent(event)
        self.refresh_layout()