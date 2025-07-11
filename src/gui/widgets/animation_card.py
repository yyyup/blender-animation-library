"""
Animation Card Widget - COMPLETE FILE WITH FIXED THUMBNAIL REFRESH
Replace your entire src/gui/widgets/animation_card.py with this file
"""

import time
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QWidget, QMenu, QToolButton, QGraphicsDropShadowEffect, QGridLayout,
    QApplication, QInputDialog, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QRect, QTimer, QMimeData
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QAction, QBrush, QPen, QLinearGradient, QDrag, QPixmapCache
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add core modules to path
gui_dir = Path(__file__).parent.parent.parent
if str(gui_dir) not in sys.path:
    sys.path.insert(0, str(gui_dir))

from core.animation_data import AnimationMetadata


class AnimationThumbnail(QLabel):
    """Clean thumbnail widget with 140x140 size for optimal card utilization"""
    
    def __init__(self, animation_metadata: AnimationMetadata, parent=None):
        super().__init__(parent)
        self.animation_metadata = animation_metadata
        self.is_selected = False
        self.last_loaded_path = None  # Track last loaded file path
        
        self.setFixedSize(140, 140)  # Larger thumbnail for better card utilization
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
                pixmap = self._load_pixmap_no_cache(thumbnail_path)
                if not pixmap.isNull():
                    self._set_centered_pixmap(pixmap)
                    self.last_loaded_path = str(thumbnail_path)
                    thumbnail_loaded = True
                    print(f"🖼️ Loaded thumbnail from metadata: {thumbnail_path}")
        
        # Fallback to animation name-based thumbnail path
        if not thumbnail_loaded:
            # Try to construct thumbnail path from animation name
            animation_id = getattr(self.animation_metadata, 'id', self.animation_metadata.name)
            thumbnail_filename = f"{animation_id}.png"
            thumbnail_path = Path("animation_library") / "thumbnails" / thumbnail_filename
            
            if thumbnail_path.exists():
                pixmap = self._load_pixmap_no_cache(thumbnail_path)
                if not pixmap.isNull():
                    self._set_centered_pixmap(pixmap)
                    self.last_loaded_path = str(thumbnail_path)
                    thumbnail_loaded = True
                    print(f"🖼️ Loaded thumbnail from ID: {thumbnail_path}")
        
        # NEW: Search for any thumbnail file containing the animation name
        if not thumbnail_loaded:
            thumbnail_path = self._find_thumbnail_by_name()
            if thumbnail_path:
                pixmap = self._load_pixmap_no_cache(thumbnail_path)
                if not pixmap.isNull():
                    self._set_centered_pixmap(pixmap)
                    self.last_loaded_path = str(thumbnail_path)
                    thumbnail_loaded = True
                    print(f"🖼️ Found thumbnail by name search: {thumbnail_path}")
        
        # Fallback to placeholder icon if no image found
        if not thumbnail_loaded:
            self.show_placeholder_icon()
            self.last_loaded_path = None
            print(f"⚠️ No thumbnail found, using placeholder")
    
    def _find_thumbnail_by_name(self) -> Optional[Path]:
        """Find thumbnail file by searching for files containing the animation name"""
        try:
            thumbnails_dir = Path("animation_library") / "thumbnails"
            if not thumbnails_dir.exists():
                return None
            
            animation_name = self.animation_metadata.name
            
            # Search for PNG files containing the animation name
            all_thumbnails = list(thumbnails_dir.glob("*.png"))
            matching_files = []
            
            for thumbnail_file in all_thumbnails:
                if animation_name in thumbnail_file.name:
                    matching_files.append(thumbnail_file)
            
            if matching_files:
                # Use the most recent file if multiple matches
                most_recent = max(matching_files, key=lambda f: f.stat().st_mtime)
                print(f"🔍 Found matching thumbnail: {most_recent.name}")
                return most_recent
            
            return None
            
        except Exception as e:
            print(f"❌ Error searching for thumbnail: {e}")
            return None
    
    def _load_pixmap_no_cache(self, image_path: Path) -> QPixmap:
        """Load pixmap without using Qt's cache system"""
        try:
            # Force fresh load by checking file modification time
            file_stat = image_path.stat()
            
            # Clear any existing cache for this file
            QPixmapCache.remove(str(image_path))
            
            # Load with explicit no-cache
            pixmap = QPixmap(str(image_path))
            
            if not pixmap.isNull():
                # Force detach from any internal caching
                pixmap = pixmap.copy()
                return pixmap
            else:
                print(f"❌ THUMBNAIL: Pixmap is null for: {image_path}")
                return QPixmap()
                
        except Exception as e:
            print(f"❌ THUMBNAIL: Error loading {image_path}: {e}")
            return QPixmap()
    
    def _set_centered_pixmap(self, pixmap: QPixmap):
        """Set pixmap centered in the label with dark background - optimized for 140x140"""
        if pixmap.isNull():
            return
        
        # Scale to fit 140x140 while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Create a centered pixmap with dark background
        final_pixmap = QPixmap(140, 140)
        final_pixmap.fill(QColor(46, 46, 46))  # #2e2e2e background
        
        painter = QPainter(final_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Center the scaled image
        x = (140 - scaled_pixmap.width()) // 2
        y = (140 - scaled_pixmap.height()) // 2
        painter.drawPixmap(x, y, scaled_pixmap)
        
        painter.end()
        self.setPixmap(final_pixmap)
    
    def show_placeholder_icon(self):
        """Show a clean placeholder icon for missing thumbnails - optimized for 140x140"""
        pixmap = QPixmap(140, 140)
        pixmap.fill(QColor(46, 46, 46))  # #2e2e2e background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw simple animation icon
        painter.setPen(QPen(QColor("#666666"), 2))
        painter.setBrush(QBrush(QColor("#666666")))
        
        # Simple figure representation - scaled for 140x140
        center_x, center_y = 70, 70  # Updated center for 140x140
        
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
        """Refresh thumbnail for the specified animation with MAXIMUM force refresh"""
        # Check if this thumbnail is for the updated animation
        animation_id = getattr(self.animation_metadata, 'id', self.animation_metadata.name)
        
        # Match by name or ID
        if (animation_name == self.animation_metadata.name or 
            animation_name == animation_id):
            
            print(f"🔄 THUMBNAIL: Starting MAXIMUM force refresh for: {animation_name}")
            
            # STEP 1: Clear ALL Qt pixmap caches AGGRESSIVELY
            QPixmapCache.clear()
            print(f"🧹 THUMBNAIL: Cleared Qt pixmap cache")
            
            # STEP 2: Clear this widget's current pixmap
            self.clear()
            print(f"🧹 THUMBNAIL: Cleared widget pixmap")
            
            # STEP 3: Force Qt to process all pending events
            QApplication.processEvents()
            
            # STEP 4: Wait for file system to sync
            time.sleep(0.2)  # Increased wait time
            
            # STEP 5: Force reload with maximum aggression
            self.load_thumbnail_image_force_refresh()
            
            # STEP 6: Force widget update
            self.update()
            self.repaint()
            QApplication.processEvents()
            
            print(f"✅ THUMBNAIL: MAXIMUM force refresh completed for: {animation_name}")
    
    def load_thumbnail_image_force_refresh(self):
        """Load thumbnail image with MAXIMUM force refresh - searches all possible locations"""
        thumbnail_loaded = False
        
        print(f"🔍 THUMBNAIL: Starting comprehensive thumbnail search...")
        
        # METHOD 1: Check metadata path with force refresh
        if hasattr(self.animation_metadata, 'thumbnail') and self.animation_metadata.thumbnail:
            thumbnail_path = Path("animation_library") / self.animation_metadata.thumbnail
            print(f"🔍 METHOD 1: Checking metadata path: {thumbnail_path}")
            
            if thumbnail_path.exists():
                try:
                    file_stat = thumbnail_path.stat()
                    print(f"🔍 METHOD 1: File exists - size: {file_stat.st_size}, modified: {file_stat.st_mtime}")
                    
                    pixmap = self._load_pixmap_force_refresh(thumbnail_path)
                    if not pixmap.isNull():
                        self._set_centered_pixmap(pixmap)
                        thumbnail_loaded = True
                        print(f"✅ METHOD 1: Successfully loaded from metadata path")
                    else:
                        print(f"❌ METHOD 1: Pixmap is null from metadata path")
                        
                except Exception as e:
                    print(f"❌ METHOD 1: Error loading from metadata path: {e}")
        
        # METHOD 2: Try animation ID-based path
        if not thumbnail_loaded:
            animation_id = getattr(self.animation_metadata, 'id', self.animation_metadata.name)
            thumbnail_filename = f"{animation_id}.png"
            thumbnail_path = Path("animation_library") / "thumbnails" / thumbnail_filename
            
            print(f"🔍 METHOD 2: Checking ID-based path: {thumbnail_path}")
            
            if thumbnail_path.exists():
                try:
                    file_stat = thumbnail_path.stat()
                    print(f"🔍 METHOD 2: File exists - size: {file_stat.st_size}, modified: {file_stat.st_mtime}")
                    
                    pixmap = self._load_pixmap_force_refresh(thumbnail_path)
                    if not pixmap.isNull():
                        self._set_centered_pixmap(pixmap)
                        thumbnail_loaded = True
                        print(f"✅ METHOD 2: Successfully loaded from ID-based path")
                    else:
                        print(f"❌ METHOD 2: Pixmap is null from ID-based path")
                        
                except Exception as e:
                    print(f"❌ METHOD 2: Error loading from ID-based path: {e}")
        
        # METHOD 3: Search all thumbnails directory for matching files
        if not thumbnail_loaded:
            print(f"🔍 METHOD 3: Searching thumbnails directory...")
            
            try:
                thumbnails_dir = Path("animation_library") / "thumbnails"
                if thumbnails_dir.exists():
                    animation_name = self.animation_metadata.name
                    all_thumbnails = list(thumbnails_dir.glob("*.png"))
                    print(f"🔍 METHOD 3: Found {len(all_thumbnails)} total PNG files")
                    
                    # Find files containing the animation name
                    matching_files = []
                    for thumbnail_file in all_thumbnails:
                        if animation_name in thumbnail_file.name:
                            matching_files.append(thumbnail_file)
                            print(f"🔍 METHOD 3: MATCH found: {thumbnail_file.name}")
                    
                    if matching_files:
                        # Use the most recent file
                        most_recent = max(matching_files, key=lambda f: f.stat().st_mtime)
                        print(f"🔍 METHOD 3: Using most recent: {most_recent.name}")
                        
                        pixmap = self._load_pixmap_force_refresh(most_recent)
                        if not pixmap.isNull():
                            self._set_centered_pixmap(pixmap)
                            thumbnail_loaded = True
                            print(f"✅ METHOD 3: Successfully loaded from search")
                        else:
                            print(f"❌ METHOD 3: Pixmap is null from search")
                    else:
                        print(f"🔍 METHOD 3: No matching files found for '{animation_name}'")
                        
                        # Debug: List all files
                        print(f"🔍 METHOD 3: All available files:")
                        for f in all_thumbnails[:10]:  # Show first 10
                            print(f"   - {f.name}")
                        if len(all_thumbnails) > 10:
                            print(f"   ... and {len(all_thumbnails) - 10} more")
                            
            except Exception as e:
                print(f"❌ METHOD 3: Error in directory search: {e}")
        
        # Show placeholder if nothing worked
        if not thumbnail_loaded:
            self.show_placeholder_icon()
            print(f"⚠️ THUMBNAIL: All methods failed, using placeholder icon")
    
    def _load_pixmap_force_refresh(self, image_path: Path) -> QPixmap:
        """Load pixmap with MAXIMUM force - bypassing ALL caching mechanisms"""
        try:
            # Method 1: Clear Qt's pixmap cache for this specific file
            QPixmapCache.remove(str(image_path))
            
            # Method 2: Read file directly into memory to bypass OS file caching
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            print(f"🔍 FORCE: Read {len(image_data)} bytes from {image_path.name}")
            
            # Method 3: Create pixmap from raw data
            pixmap = QPixmap()
            success = pixmap.loadFromData(image_data)
            
            if success and not pixmap.isNull():
                # Method 4: Force detach to ensure no internal caching
                pixmap = pixmap.copy()
                print(f"✅ FORCE: Successfully created pixmap from raw data")
                return pixmap
            else:
                print(f"❌ FORCE: Failed to create pixmap from raw data")
                return QPixmap()
                
        except Exception as e:
            print(f"❌ FORCE: Error in maximum force refresh: {e}")
            return QPixmap()


class AnimationCard(QFrame):
    """Professional animation card with FIXED thumbnail refresh support"""
    
    # Signals
    apply_requested = Signal(dict)
    edit_requested = Signal(dict)
    delete_requested = Signal(dict)
    preview_requested = Signal(dict)
    move_to_folder_requested = Signal(dict, str)
    
    def __init__(self, animation_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.animation_data = animation_data
        self.animation_metadata = AnimationMetadata.from_dict(animation_data)
        self.is_hovered = False
        self.is_selected = False
        self.drag_start_position = None
        
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
        
        # Thumbnail at top - 140x140px (increased from 120x120px)
        self.thumbnail = AnimationThumbnail(self.animation_metadata)
        layout.addWidget(self.thumbnail, 0, Qt.AlignHCenter)
        
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
            self.set_selected(True)
            self.drag_start_position = event.pos()
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
        """Start drag operation for this animation card"""
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
        
        # Execute drag
        _ = drag.exec_(Qt.MoveAction)  # Result not used
    
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
        self.thumbnail.set_selected(selected)
        
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)
    
    def refresh_thumbnail(self, animation_name: str):
        """Refresh thumbnail for the specified animation - AGGRESSIVE VERSION"""
        # Check if this card is for the updated animation
        if (animation_name == self.animation_metadata.name or 
            animation_name == getattr(self.animation_metadata, 'id', self.animation_metadata.name)):
            
            print(f"🎬 CARD: Starting AGGRESSIVE thumbnail refresh for: {animation_name}")
            
            # Use the enhanced refresh method from the thumbnail widget
            self.thumbnail.refresh_thumbnail(animation_name)
            
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
            
            print(f"✅ CARD: AGGRESSIVE thumbnail refresh completed for: {animation_name}")


class AnimationCardGrid(QWidget):
    """Grid container for animation cards with responsive layout and FIXED refresh"""
    
    animation_selected = Signal(dict)  # Emits selected animation data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards = []
        self.selected_card = None
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
        """Add animation card to grid"""
        # Connect selection signal properly with closure
        def create_mouse_handler(original_handler, card_reference):
            def new_mouse_press(event):
                original_handler(event)
                if event.button() == Qt.LeftButton:
                    self.select_card(card_reference)
            return new_mouse_press
        
        animation_card.mousePressEvent = create_mouse_handler(animation_card.mousePressEvent, animation_card)
        
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
    
    def refresh_thumbnail(self, animation_name: str):
        """Refresh thumbnail for the specified animation across ALL cards - AGGRESSIVE VERSION"""
        refreshed_count = 0
        
        print(f"🔄 GRID: Starting AGGRESSIVE thumbnail refresh for all cards matching: {animation_name}")
        
        for card in self.cards:
            if hasattr(card, 'refresh_thumbnail'):
                # Check if this card is for the updated animation
                if (animation_name == card.animation_metadata.name or 
                    animation_name == getattr(card.animation_metadata, 'id', card.animation_metadata.name)):
                    
                    print(f"🎬 GRID: Refreshing card for: {card.animation_metadata.name}")
                    card.refresh_thumbnail(animation_name)
                    refreshed_count += 1
        
        if refreshed_count > 0:
            print(f"✅ GRID: Refreshed {refreshed_count} card(s) for animation: {animation_name}")
            
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
            print(f"⚠️ GRID: No cards found for animation: {animation_name}")