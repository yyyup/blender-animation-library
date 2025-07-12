"""
Animation Card Widget - VIDEO PREVIEW SYSTEM
Complete migration from static thumbnails to dynamic video previews
"""

import time
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QWidget, QMenu, QToolButton, QGraphicsDropShadowEffect, QGridLayout,
    QApplication, QInputDialog, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QRect, QTimer, QMimeData, QUrl
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QAction, QBrush, QPen, QLinearGradient, QDrag
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add core modules to path
gui_dir = Path(__file__).parent.parent.parent
if str(gui_dir) not in sys.path:
    sys.path.insert(0, str(gui_dir))

from core.animation_data import AnimationMetadata


class AnimationPreview(QVideoWidget):
    """Video preview widget with hover-to-play functionality (140x140 size)"""
    
    def __init__(self, animation_metadata: AnimationMetadata, parent=None):
        super().__init__(parent)
        self.animation_metadata = animation_metadata
        self.is_selected = False
        
        # Set fixed size for card integration
        self.setFixedSize(140, 140)
        
        # Setup media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.0)  # Silent preview
        
        # Connect media player to video widget
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self)
        
        # Load video preview
        self.load_preview_video()
        
        # Clean styling with rounded corners
        self.setStyleSheet("""
            QVideoWidget {
                border: none;
                border-radius: 8px;
                background-color: #2e2e2e;
            }
        """)
    
    def load_preview_video(self):
        """Load MP4 preview video from file"""
        preview_loaded = False
        
        # Check if animation has preview path in metadata
        if hasattr(self.animation_metadata, 'preview') and self.animation_metadata.preview:
            preview_path = Path("animation_library") / self.animation_metadata.preview
            if preview_path.exists():
                self.media_player.setSource(QUrl.fromLocalFile(str(preview_path.absolute())))
                preview_loaded = True
                print(f"🎬 Loaded preview from metadata: {preview_path}")
        
        # Fallback to animation ID-based preview path using folder structure
        if not preview_loaded:
            animation_id = getattr(self.animation_metadata, 'id', self.animation_metadata.name)
            folder_path = getattr(self.animation_metadata, 'folder_path', 'Root')
            preview_filename = f"{animation_id}.mp4"
            preview_path = Path("animation_library") / "previews" / folder_path / preview_filename
            
            if preview_path.exists():
                self.media_player.setSource(QUrl.fromLocalFile(str(preview_path.absolute())))
                preview_loaded = True
                print(f"🎬 Loaded preview from ID: {preview_path}")
        
        # Search for any preview file containing the animation name
        if not preview_loaded:
            preview_path = self._find_preview_by_name()
            if preview_path:
                self.media_player.setSource(QUrl.fromLocalFile(str(preview_path.absolute())))
                preview_loaded = True
                print(f"🎬 Found preview by name search: {preview_path}")
        
        # No preview found - show placeholder
        if not preview_loaded:
            self.show_placeholder()
            print(f"⚠️ No preview found for animation: {self.animation_metadata.name}")
    
    def _find_preview_by_name(self) -> Optional[Path]:
        """Find preview file by searching for files containing the animation name"""
        try:
            animation_name = self.animation_metadata.name.replace(" ", "_")
            folder_path = getattr(self.animation_metadata, 'folder_path', 'Root')
            previews_dir = Path("animation_library") / "previews" / folder_path
            
            if previews_dir.exists():
                # Search for MP4 files containing the animation name
                for preview_file in previews_dir.glob("*.mp4"):
                    if animation_name in preview_file.name:
                        return preview_file
            return None
        except Exception as e:
            print(f"⚠️ Error searching for preview: {e}")
            return None
    
    def show_placeholder(self):
        """Show placeholder when no preview is available"""
        # For now, just set background color - could be enhanced with a placeholder image
        self.setStyleSheet("""
            QVideoWidget {
                border: 2px solid #555;
                border-radius: 8px;
                background-color: #1e1e1e;
                color: #888;
            }
        """)
    
    def enterEvent(self, event):
        """Play video on hover"""
        if self.media_player.source().isValid():
            self.media_player.play()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Pause video on leave"""
        if self.media_player.source().isValid():
            self.media_player.pause()
            self.media_player.setPosition(0)  # Reset to beginning
        super().leaveEvent(event)
    
    def refresh_preview(self):
        """Refresh preview - reload the video file for temporary file strategy"""
        print(f"🔄 Card refreshing preview: {self.animation_metadata.name}")
        
        # Brief release then reload for temporary file strategy
        self.release_video_file()
        QTimer.singleShot(100, self.load_preview_video)
        print(f"✅ Card preview refresh scheduled for: {self.animation_metadata.name}")
    
    def release_video_file(self):
        """Release video file so Blender can delete/recreate it"""
        if self.media_player:
            self.media_player.stop()
            self.media_player.setSource(QUrl())
            print(f"🔓 Card released video: {self.animation_metadata.name}")
    
    def reload_video_file(self):
        """Reload video after Blender creates new file"""
        print(f"🔄 Card reloading video: {self.animation_metadata.name}")
        self.load_preview_video()
    
    def set_selected(self, selected: bool):
        """Update selection state"""
        self.is_selected = selected
        # Could add visual selection feedback here if needed



class AnimationCard(QFrame):
    """Professional animation card with FIXED thumbnail refresh support"""
    
    # Signals
    apply_requested = Signal(dict)
    edit_requested = Signal(dict)
    delete_requested = Signal(dict)
    preview_requested = Signal(dict)
    move_to_folder_requested = Signal(dict, str)
    drag_started = Signal()  # NEW: Signal when drag begins
    drag_finished = Signal(bool)  # NEW: Signal when drag ends (success/failure)
    
    def __init__(self, animation_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.animation_data = animation_data
        self.animation_metadata = AnimationMetadata.from_dict(animation_data)
        self.is_hovered = False
        self.is_selected = False
        self.drag_start_position = None
        self.is_dragging = False  # NEW: Track drag state
        
        # Initialize button attributes
        self.apply_btn = None
        self.actions_widget = None
        
        self.setup_ui()
        self.setup_animations()
        self.setup_style()
        
        # Enable drag and drop
        self.setAcceptDrops(False)
    
    def setup_ui(self):
        """Setup the card UI layout - Studio Library style with optimized space utilization"""
        self.setFixedSize(160, 220)
        self.setFrameStyle(QFrame.NoFrame)
        
        # Main layout with minimal padding for maximum thumbnail prominence
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)  # Reduced from 8px to 4px
        layout.setSpacing(4)  # Reduced from 8px to 4px for tighter layout
        
        # Video preview at top - 140x140px (replacing thumbnail)
        self.preview = AnimationPreview(self.animation_metadata)
        layout.addWidget(self.preview, 0, Qt.AlignHCenter)
        
        # Animation name (bold) with reduced height
        self.title_label = QLabel(self.animation_metadata.name)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(28)  # Reduced from 32px to 28px
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Optional metadata (frame count, rig type) with tighter spacing
        metadata_widget = QWidget()
        metadata_layout = QVBoxLayout(metadata_widget)
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.setSpacing(1)  # Reduced from 2px to 1px
        
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
        
        # Minimal stretch to maintain layout without wasting space
        layout.addStretch()
    
    def create_actions_section(self) -> QWidget:
        """Create professional icon-based action buttons with even spacing"""
        widget = QWidget()
        widget.setObjectName("actionsContainer")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # No spacing, we'll use stretches for even distribution
        
        # Even spacing pattern: [stretch] [button] [stretch] [button] [stretch] [button] [stretch]
        layout.addStretch()  # Left spacing
        
        # Apply button - Play/Right arrow icon
        self.apply_btn = QPushButton("▶")
        self.apply_btn.setObjectName("applyIconButton")
        self.apply_btn.setFixedSize(26, 26)
        self.apply_btn.setToolTip("Apply Animation")
        self.apply_btn.clicked.connect(lambda: self.apply_requested.emit(self.animation_data))
        layout.addWidget(self.apply_btn)
        
        layout.addStretch()  # Between first and second button
        
        # Delete button - Trash icon
        delete_btn = QPushButton("🗑")
        delete_btn.setObjectName("deleteIconButton")
        delete_btn.setFixedSize(26, 26)
        delete_btn.setToolTip("Delete Animation")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.animation_data))
        layout.addWidget(delete_btn)
        
        layout.addStretch()  # Between second and third button
        
        # Rename button - Edit/Pencil icon
        rename_btn = QPushButton("✎")
        rename_btn.setObjectName("renameIconButton")
        rename_btn.setFixedSize(26, 26)
        rename_btn.setToolTip("Rename Animation")
        rename_btn.clicked.connect(lambda: self.edit_requested.emit(self.animation_data))
        layout.addWidget(rename_btn)
        
        layout.addStretch()  # Right spacing
        
        # Initially hidden, shown on hover
        widget.setVisible(False)
        
        return widget
    
    def setup_animations(self):
        """Setup hover animations without shadows"""
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def setup_style(self):
        """Setup Studio Library style card styling with exact specifications"""
        self.setStyleSheet("""
            /* Main card styling - Studio Library specifications */
            AnimationCard {
                border: 2px solid transparent;
                border-radius: 8px;
                background-color: #2e2e2e;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            /* Hover effect - subtle brightness increase */
            AnimationCard:hover {
                background-color: #323232;
                border: 2px solid transparent;
            }
            
            /* Selected state - Elegant Studio Library blue border with subtle highlight */
            AnimationCard[selected="true"] {
                border: 3px solid #4a90e2;
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2e2e2e, stop:1 #2a2a2a);
            }
            
            /* Selected hover state - Enhanced elegance */
            AnimationCard[selected="true"]:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #323232, stop:1 #2e2e2e);
                border: 3px solid #5ba0f2;
            }
            
            /* Title label - 11px bold as specified */
            #titleLabel {
                color: #eeeeee;
                font-size: 11px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 2px 4px;
                background: transparent;
                border: none;
            }
            
            /* Metadata labels - proper Studio Library typography */
            #metaLabel {
                color: #cccccc;
                font-size: 9px;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 1px 4px;
                background: transparent;
                border: none;
            }
            
            #rigLabel {
                color: #aaaaaa;
                font-size: 9px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-style: italic;
                padding: 1px 4px;
                background: transparent;
                border: none;
            }
            
            /* Apply icon button - Studio Library primary action */
            #applyIconButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 11px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: bold;
                text-align: center;
                padding: 0px;
            }
            
            #applyIconButton:hover {
                background-color: #357abd;
                border: 1px solid #4a90e2;
            }
            
            #applyIconButton:pressed {
                background-color: #2968a3;
            }
            
            /* Delete icon button - Studio Library danger action */
            #deleteIconButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 11px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: bold;
                text-align: center;
                padding: 0px;
            }
            
            #deleteIconButton:hover {
                background-color: #c0392b;
                border: 1px solid #e74c3c;
            }
            
            #deleteIconButton:pressed {
                background-color: #a93226;
            }
            
            /* Rename icon button - Studio Library secondary action */
            #renameIconButton {
                background-color: #666666;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 11px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: bold;
                text-align: center;
                padding: 0px;
            }
            
            #renameIconButton:hover {
                background-color: #777777;
                border: 1px solid #999999;
            }
            
            #renameIconButton:pressed {
                background-color: #555555;
            }
            
            /* Actions container - evenly spaced icon layout */
            #actionsContainer {
                background: transparent;
                border: none;
                margin: 0px;
                padding: 0px;
            }
            
            #renameButton:hover {
                background-color: #777777;
            }
            
            #renameButton:pressed {
                background-color: #555555;
            }
        """)
    
    def enterEvent(self, event):
        """Handle mouse enter event with smooth action button transition"""
        self.is_hovered = True
        # Show action buttons with smooth transition
        if hasattr(self, 'actions_widget'):
            self.actions_widget.setVisible(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event with smooth action button transition"""
        self.is_hovered = False
        # Hide action buttons with smooth transition
        if hasattr(self, 'actions_widget'):
            self.actions_widget.setVisible(False)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press for selection and drag start"""
        if event.button() == Qt.LeftButton:
            print(f"🖱️ DEBUG: Animation card clicked: {self.animation_metadata.name}")
            print(f"🖱️ DEBUG: Animation ID: {getattr(self.animation_metadata, 'id', 'NO_ID')}")
            print(f"🖱️ DEBUG: Animation data: {self.animation_data}")
            
            self.set_selected(True)
            self.drag_start_position = event.pos()
            print("🖱️ DEBUG: Card selection set, drag position recorded")
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
        
        if distance < min_distance:
            return
        
        # Start drag operation
        self.start_drag()
    
    def start_drag(self):
        """Start drag operation for this animation card with proper state management"""
        if self.is_dragging:
            return  # Prevent multiple simultaneous drags
            
        self.is_dragging = True
        self.drag_started.emit()  # Notify that drag is starting
        
        print(f"🎬 DRAG: Starting drag for animation: {self.animation_metadata.name}")
        
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Set animation ID as drag data
        animation_id = self.animation_data.get('id', '')
        mime_data.setText(f"animation_id:{animation_id}")
        
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
        
        # Execute drag and handle result
        drop_action = drag.exec_(Qt.MoveAction)
        
        # Handle drag completion
        success = (drop_action == Qt.MoveAction)
        print(f"🎬 DRAG: Drag completed - Success: {success}, Action: {drop_action}")
        
        self.is_dragging = False
        self.drag_finished.emit(success)
        
        if not success:
            print(f"⚠️ DRAG: Failed to drop animation {self.animation_metadata.name}")
            # Optionally show user feedback for failed drops
    
    def contextMenuEvent(self, event):
        """Show context menu with folder move options"""
        menu = QMenu(self)
        
        # Move to folder submenu
        move_menu = QMenu("Move to Folder", self)
        
        # Add some common folder options
        root_action = QAction("📁 Root", self)
        root_action.triggered.connect(lambda: self.move_to_folder_requested.emit(self.animation_data, "Root"))
        move_menu.addAction(root_action)
        
        # Separator for custom folders
        move_menu.addSeparator()
        
        # Create new folder option
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
        self.preview.set_selected(selected)
        
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)
    
    def refresh_thumbnail(self, animation_identifier: str):
        """Refresh thumbnail for the specified animation - AGGRESSIVE VERSION"""
        # Check if this card is for the updated animation
        if (animation_identifier == self.animation_metadata.name or 
            animation_identifier == getattr(self.animation_metadata, 'id', self.animation_metadata.name)):
            
            print(f"🎬 CARD: Starting AGGRESSIVE thumbnail refresh for: {animation_identifier}")
            
            # Use the enhanced refresh method from the thumbnail widget
            self.preview.refresh_preview()
            
            # Force update the entire card multiple times
            self.update()
            self.repaint()
            QApplication.processEvents()
            
            # Wait a bit and force another update
            QTimer.singleShot(100, lambda: [
                self.update(),
                self.repaint(),
                QApplication.processEvents()
            ])
            
            print(f"✅ CARD: AGGRESSIVE thumbnail refresh completed for: {animation_identifier}")


class AnimationCardGrid(QWidget):
    """Grid container for animation cards with responsive layout and FIXED refresh"""
    
    animation_selected = Signal(dict)  # Emits selected animation data
    drag_in_progress = Signal(bool)    # NEW: Signal for drag state changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards = []
        self.selected_card = None
        self.active_drags = 0  # NEW: Track number of active drags
        self.setup_ui()
    
    def setup_ui(self):
        """Setup grid layout"""
        # Use scroll area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Grid widget
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(1)  # Ultra-tight Studio Library spacing - almost touching
        self.grid_layout.setContentsMargins(4, 4, 4, 4)  # Minimal container margins
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
        """Add animation card to grid and connect drag signals"""
        # Connect selection signal properly with closure
        def create_mouse_handler(original_handler, card_reference):
            def new_mouse_press(event):
                original_handler(event)
                if event.button() == Qt.LeftButton:
                    self.select_card(card_reference)
            return new_mouse_press
        
        animation_card.mousePressEvent = create_mouse_handler(animation_card.mousePressEvent, animation_card)
        
        # NEW: Connect drag state signals
        animation_card.drag_started.connect(self.on_drag_started)
        animation_card.drag_finished.connect(self.on_drag_finished)
        
        self.cards.append(animation_card)
        self.refresh_layout()
    
    def on_drag_started(self):
        """Handle when a card starts being dragged"""
        self.active_drags += 1
        if self.active_drags == 1:  # First drag started
            self.drag_in_progress.emit(True)
            print(f"🎯 Drag started - active drags: {self.active_drags}")
    
    def on_drag_finished(self):
        """Handle when a card finishes being dragged"""
        self.active_drags = max(0, self.active_drags - 1)  # Prevent negative
        if self.active_drags == 0:  # All drags finished
            self.drag_in_progress.emit(False)
            print(f"✅ All drags finished - active drags: {self.active_drags}")
    
    def select_card(self, card):
        """Select an animation card"""
        print(f"🔄 DEBUG: select_card called for: {card.animation_metadata.name}")
        print(f"🔄 DEBUG: Card animation data: {card.animation_data}")
        
        # Deselect previous card
        if self.selected_card:
            print(f"🔄 DEBUG: Deselecting previous card: {self.selected_card.animation_metadata.name}")
            self.selected_card.set_selected(False)
        
        # Select new card
        self.selected_card = card
        card.set_selected(True)
        print(f"🔄 DEBUG: Selected new card: {card.animation_metadata.name}")
        
        # Emit selection signal
        print("🔄 DEBUG: About to emit animation_selected signal")
        self.animation_selected.emit(card.animation_data)
        print("🔄 DEBUG: animation_selected signal emitted")
    
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
    
    def bulk_add_cards(self, cards_list):
        """Add multiple cards efficiently without refreshing layout each time"""
        print(f"📦 Bulk adding {len(cards_list)} animation cards...")
        
        # Add all cards to internal list first
        for card in cards_list:
            # Connect selection signal properly with proper closure
            def create_mouse_handler(original_handler, card_reference):
                def new_mouse_press(event):
                    original_handler(event)
                    if event.button() == Qt.LeftButton:
                        self.select_card(card_reference)
                return new_mouse_press
            
            card.mousePressEvent = create_mouse_handler(card.mousePressEvent, card)
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
        
        # Step 2: Calculate grid dimensions based on ultra-tight Studio Library spacing
        widget_width = self.scroll_area.viewport().width() - 8  # Account for minimal margins (4px each side)
        card_width = 160 + 1  # Studio Library card width (160px) + ultra-tight spacing (1px)
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
    
    def refresh_thumbnail(self, animation_identifier: str):
        """Refresh preview for specified animation across ALL cards"""
        refreshed_count = 0
        
        print(f"🔄 GRID: Starting preview refresh for all cards matching: {animation_identifier}")
        
        for card in self.cards:
            # Check if this card matches the animation
            if (animation_identifier == card.animation_metadata.name or 
                animation_identifier == getattr(card.animation_metadata, 'id', card.animation_metadata.name)):
                
                print(f"🎬 GRID: Refreshing card preview for: {card.animation_metadata.name}")
                
                # Call the correct refresh method on the video preview widget
                if hasattr(card, 'preview') and hasattr(card.preview, 'refresh_preview'):
                    card.preview.refresh_preview()  # ✅ Call video refresh method
                    refreshed_count += 1
                elif hasattr(card, 'refresh_thumbnail'):
                    # Fallback to card's own refresh method
                    card.refresh_thumbnail(animation_identifier)
                    refreshed_count += 1
        
        if refreshed_count > 0:
            print(f"✅ GRID: Refreshed {refreshed_count} card(s)")
            
            # Force grid-wide update
            self.update()
            self.repaint()
            QApplication.processEvents()
            
            # Delayed additional refresh
            QTimer.singleShot(200, lambda: [
                self.update(),
                self.repaint(),
                QApplication.processEvents()
            ])
        else:
            print(f"⚠️ GRID: No matching cards found for: {animation_identifier}")
    
    def release_all_video_files(self):
        """Release video files from all animation cards"""
        print(f"🔓 GRID: Releasing video files from {len(self.cards)} animation cards")
        
        for card in self.cards:
            if hasattr(card, 'preview') and hasattr(card.preview, 'release_video_file'):
                card.preview.release_video_file()
        
        print(f"✅ GRID: All video files released")