"""
Animation Card Widget
Professional animation card display with metadata and actions
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QWidget, QMenu, QToolButton
)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QAction
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add core modules to path
gui_dir = Path(__file__).parent.parent.parent
if str(gui_dir) not in sys.path:
    sys.path.insert(0, str(gui_dir))

from core.animation_data import AnimationMetadata


class AnimationCard(QFrame):
    """Professional animation card widget with hover effects and actions"""
    
    # Signals
    apply_requested = Signal(dict)
    edit_requested = Signal(dict)
    delete_requested = Signal(dict)
    preview_requested = Signal(dict)
    
    def __init__(self, animation_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.animation_data = animation_data
        self.animation_metadata = AnimationMetadata.from_dict(animation_data)
        self.is_hovered = False
        
        self.setup_ui()
        self.setup_animations()
        self.setup_style()
    
    def setup_ui(self):
        """Setup the card UI layout"""
        self.setFixedSize(220, 320)  # Increased height for rig type
        self.setFrameStyle(QFrame.NoFrame)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Thumbnail section
        self.thumbnail_widget = self.create_thumbnail_widget()
        layout.addWidget(self.thumbnail_widget)
        
        # Title section
        self.title_label = self.create_title_label()
        layout.addWidget(self.title_label)
        
        # Metadata section
        self.metadata_widget = self.create_metadata_widget()
        layout.addWidget(self.metadata_widget)
        
        # Tags section
        self.tags_widget = self.create_tags_widget()
        layout.addWidget(self.tags_widget)
        
        # Actions section
        self.actions_widget = self.create_actions_widget()
        layout.addWidget(self.actions_widget)
        
        layout.addStretch()
    
    def create_thumbnail_widget(self) -> QWidget:
        """Create thumbnail display widget"""
        widget = QFrame()
        widget.setFixedSize(196, 120)
        widget.setObjectName("thumbnail")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Placeholder thumbnail
        thumbnail_label = QLabel()
        thumbnail_label.setAlignment(Qt.AlignCenter)
        thumbnail_label.setText("🎬\nAnimation\nPreview")
        thumbnail_label.setObjectName("thumbnailLabel")
        
        layout.addWidget(thumbnail_label)
        
        # Overlay with duration
        duration = self.animation_metadata.duration_frames
        duration_label = QLabel(f"{int(duration)}f")
        duration_label.setObjectName("durationLabel")
        duration_label.setAlignment(Qt.AlignCenter)
        
        # Position duration label at bottom right
        duration_label.setParent(widget)
        duration_label.setGeometry(160, 95, 30, 20)
        
        return widget
    
    def create_title_label(self) -> QLabel:
        """Create animation title label"""
        label = QLabel(self.animation_metadata.name)
        label.setObjectName("titleLabel")
        label.setWordWrap(True)
        label.setMaximumHeight(50)
        label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        return label
    
    def create_metadata_widget(self) -> QWidget:
        """Create metadata display widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Duration and bones info
        duration = int(self.animation_metadata.duration_frames)
        bones = self.animation_metadata.total_bones_animated
        keyframes = self.animation_metadata.total_keyframes
        
        info_text = f"{duration} frames • {bones} bones"
        info_label = QLabel(info_text)
        info_label.setObjectName("infoLabel")
        layout.addWidget(info_label)
        
        # Keyframes info
        keyframe_text = f"{keyframes} keyframes"
        keyframe_label = QLabel(keyframe_text)
        keyframe_label.setObjectName("keyframeLabel")
        layout.addWidget(keyframe_label)
        
        # Rig type info with emoji and color
        rig_type = self.animation_metadata.rig_type
        # Import here to avoid circular imports
        import sys
        from pathlib import Path
        gui_dir = Path(__file__).parent.parent.parent
        if str(gui_dir) not in sys.path:
            sys.path.insert(0, str(gui_dir))
        from core.animation_data import RigTypeDetector
        
        rig_emoji = RigTypeDetector.get_rig_emoji(rig_type)
        rig_color = RigTypeDetector.get_rig_color(rig_type)
        
        rig_label = QLabel(f"{rig_emoji} {rig_type} Rig")
        rig_label.setObjectName("rigLabel")
        rig_label.setStyleSheet(f"color: {rig_color}; font-weight: bold; font-size: 9px;")
        layout.addWidget(rig_label)
        
        # Creation date
        created_date = self.animation_metadata.created_date[:16].replace('T', ' ')
        date_label = QLabel(f"Created: {created_date}")
        date_label.setObjectName("dateLabel")
        layout.addWidget(date_label)
        
        return widget
    
    def create_tags_widget(self) -> QWidget:
        """Create tags display widget"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        tags = self.animation_metadata.tags[:3]  # Show first 3 tags
        
        for tag in tags:
            tag_label = QLabel(tag)
            tag_label.setObjectName("tagLabel")
            tag_label.setMaximumWidth(60)
            layout.addWidget(tag_label)
        
        if len(self.animation_metadata.tags) > 3:
            more_label = QLabel(f"+{len(self.animation_metadata.tags) - 3}")
            more_label.setObjectName("moreTagsLabel")
            layout.addWidget(more_label)
        
        layout.addStretch()
        return widget
    
    def create_actions_widget(self) -> QWidget:
        """Create action buttons widget"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # Apply button (primary action)
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setObjectName("applyButton")
        self.apply_btn.clicked.connect(lambda: self.apply_requested.emit(self.animation_data))
        layout.addWidget(self.apply_btn)
        
        # Options button (secondary actions)
        self.options_btn = QToolButton()
        self.options_btn.setObjectName("optionsButton")
        self.options_btn.setText("⋯")
        self.options_btn.setToolTip("More options")
        
        # Create options menu
        options_menu = QMenu(self)
        
        preview_action = QAction("Preview", self)
        preview_action.triggered.connect(lambda: self.preview_requested.emit(self.animation_data))
        options_menu.addAction(preview_action)
        
        edit_action = QAction("Edit Metadata", self)
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.animation_data))
        options_menu.addAction(edit_action)
        
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
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def setup_style(self):
        """Setup card styling"""
        self.setStyleSheet("""
            AnimationCard {
                border: 2px solid #404040;
                border-radius: 12px;
                background-color: #2b2b2b;
            }
            
            AnimationCard:hover {
                border-color: #0078d4;
                background-color: #353535;
            }
            
            #thumbnail {
                border: 1px solid #555;
                border-radius: 8px;
                background-color: #1e1e1e;
            }
            
            #thumbnailLabel {
                color: #888;
                font-size: 12px;
                font-weight: bold;
            }
            
            #durationLabel {
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                border-radius: 10px;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 6px;
            }
            
            #titleLabel {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
            }
            
            #infoLabel {
                color: #cccccc;
                font-size: 10px;
            }
            
            #keyframeLabel {
                color: #aaaaaa;
                font-size: 9px;
            }
            
            #rigLabel {
                font-size: 9px;
                font-weight: bold;
                padding: 1px 0px;
            }
            
            #dateLabel {
                color: #888888;
                font-size: 8px;
            }
            
            #tagLabel {
                background-color: #0078d4;
                color: white;
                padding: 2px 6px;
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
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            
            #applyButton:hover {
                background-color: #106ebe;
            }
            
            #applyButton:pressed {
                background-color: #005a9e;
            }
            
            #optionsButton {
                background-color: #404040;
                color: #cccccc;
                border: 1px solid #555;
                padding: 6px 8px;
                border-radius: 6px;
                font-weight: bold;
            }
            
            #optionsButton:hover {
                background-color: #4a4a4a;
                border-color: #0078d4;
            }
        """)
    
    def enterEvent(self, event):
        """Handle mouse enter event"""
        self.is_hovered = True
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event"""
        self.is_hovered = False
        super().leaveEvent(event)
    
    def update_animation_data(self, animation_data: Dict[str, Any]):
        """Update the animation data and refresh display"""
        self.animation_data = animation_data
        self.animation_metadata = AnimationMetadata.from_dict(animation_data)
        
        # Update UI elements
        self.title_label.setText(self.animation_metadata.name)
        
        # Update metadata
        duration = int(self.animation_metadata.duration_frames)
        bones = self.animation_metadata.total_bones_animated
        keyframes = self.animation_metadata.total_keyframes
        
        # Find and update info labels
        info_widget = self.metadata_widget
        info_label = info_widget.findChild(QLabel, "infoLabel")
        if info_label:
            info_label.setText(f"{duration} frames • {bones} bones")
        
        keyframe_label = info_widget.findChild(QLabel, "keyframeLabel")
        if keyframe_label:
            keyframe_label.setText(f"{keyframes} keyframes")
    
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup grid layout"""
        from PySide6.QtWidgets import QGridLayout
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(16, 16, 16, 16)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    
    def add_card(self, animation_card: AnimationCard):
        """Add animation card to grid"""
        self.cards.append(animation_card)
        self.refresh_layout()
    
    def remove_card(self, animation_card: AnimationCard):
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
    
    def refresh_layout(self):
        """Refresh the grid layout"""
        # Clear layout
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item:
                self.grid_layout.removeItem(item)
        
        # Calculate columns based on widget width
        widget_width = self.width()
        card_width = 220 + 16  # Card width + spacing
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