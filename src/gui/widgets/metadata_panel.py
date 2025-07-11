"""
Metadata Panel Widget
Professional metadata display for animation details
"""

import sys
from pathlib import Path

# Add core modules to path
gui_dir = Path(__file__).parent.parent.parent
if str(gui_dir) not in sys.path:
    sys.path.insert(0, str(gui_dir))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QScrollArea, QTextEdit, QGridLayout, QPushButton
)
from PySide6.QtCore import Qt, Signal, QUrl, QTimer
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QBrush
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from core.animation_data import AnimationMetadata


class MetadataPanel(QWidget):
    """Professional metadata panel matching Studio Library style with video preview support"""
    
    # Signals for requesting thumbnail updates
    thumbnail_update_requested = Signal(str)  # animation_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_animation = None
        self.media_player = None
        self.video_widget = None
        self.audio_output = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the metadata panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header
        header_label = QLabel("Animation Details")
        header_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_label.setStyleSheet("color: #ffffff; padding: 8px; background-color: #4a4a4a; border-radius: 4px;")
        layout.addWidget(header_label)
        
        # Scroll area for metadata content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(12)
        
        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)
        
        # Initialize with no selection message
        self.show_no_selection()
        
        # Styling
        self.setStyleSheet("""
            QScrollArea {
                background-color: #393939;
                border: none;
            }
            
            QLabel {
                color: #ffffff;
                font-size: 11px;
            }
            
            QTextEdit {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
            }
        """)
    
    def clear_content(self):
        """Clear all content from the metadata panel"""
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
    
    def show_no_selection(self):
        """Show message when no animation is selected"""
        self.clear_content()
        
        no_selection_label = QLabel("Select an animation to view details")
        no_selection_label.setAlignment(Qt.AlignCenter)
        no_selection_label.setStyleSheet("""
            color: #888;
            font-size: 12px;
            font-style: italic;
            padding: 40px;
        """)
        
        self.content_layout.addWidget(no_selection_label)
        self.content_layout.addStretch()
    
    def show_animation_details(self, animation: AnimationMetadata):
        """Show detailed metadata for selected animation with video/image preview"""
        self.current_animation = animation
        self.clear_content()
        
        # Large preview section at the top (video or image)
        preview_group = self.create_info_group("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Check if animation has preview video
        has_video_preview = self.check_for_video_preview(animation)
        
        if has_video_preview:
            # Create video player
            self.create_video_player(preview_layout, animation)
        else:
            # Create static image preview
            self.create_image_preview(preview_layout, animation)
        
        # Buttons section
        buttons_layout = QHBoxLayout()
        
        # Update thumbnail button
        update_thumbnail_btn = QPushButton("Update Thumbnail")
        update_thumbnail_btn.setObjectName("updateThumbnailButton")
        update_thumbnail_btn.setFixedHeight(28)
        update_thumbnail_btn.clicked.connect(self.on_update_thumbnail_clicked)
        
        # Style button
        button_style = """
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
                margin: 2px;
            }
            
            QPushButton:hover {
                background-color: #357abd;
            }
            
            QPushButton:pressed {
                background-color: #2968a3;
            }
        """
        
        update_thumbnail_btn.setStyleSheet(button_style)
        
        buttons_layout.addWidget(update_thumbnail_btn)
        preview_layout.addLayout(buttons_layout)
        
        self.content_layout.addWidget(preview_group)
        
        # Animation name and description
        name_group = self.create_info_group("Basic Information")
        name_layout = QVBoxLayout(name_group)
        
        name_label = QLabel(f"Name: {animation.name}")
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        name_layout.addWidget(name_label)
        
        if animation.description:
            desc_edit = QTextEdit()
            desc_edit.setPlainText(animation.description)
            desc_edit.setMaximumHeight(80)
            desc_edit.setReadOnly(True)
            name_layout.addWidget(desc_edit)
        
        self.content_layout.addWidget(name_group)
        
        # Technical details
        tech_group = self.create_info_group("Technical Details")
        tech_layout = QVBoxLayout(tech_group)
        
        tech_info = [
            f"Duration: {int(animation.duration_frames)} frames",
            f"Frame Range: {animation.frame_range[0]:.0f} - {animation.frame_range[1]:.0f}",
            f"Animated Bones: {animation.total_bones_animated}",
            f"Total Keyframes: {animation.total_keyframes}",
            f"Source Armature: {animation.armature_source}"
        ]
        
        for info in tech_info:
            label = QLabel(info)
            tech_layout.addWidget(label)
        
        self.content_layout.addWidget(tech_group)
        
        # Performance information
        perf_group = self.create_info_group("Performance")
        perf_layout = QVBoxLayout(perf_group)
        
        perf_info = animation.get_performance_info()
        
        # Storage method with visual indicator
        storage_text = f"{perf_info['status_emoji']} {animation.storage_method.replace('_', ' ').title()}"
        storage_label = QLabel(f"Storage: {storage_text}")
        color = '#51cf66' if animation.is_blend_file_storage() else '#ffd43b'
        storage_label.setStyleSheet(f"font-weight: bold; color: {color};")
        perf_layout.addWidget(storage_label)
        
        perf_details = [
            f"Extraction Time: {perf_info['extraction_time']}",
            f"Application Time: {perf_info['application_time']}",
            f"Storage Size: {perf_info['storage_efficiency']}"
        ]
        
        for detail in perf_details:
            label = QLabel(detail)
            perf_layout.addWidget(label)
        
        self.content_layout.addWidget(perf_group)
        
        # Rig information
        rig_group = self.create_info_group("Rig Information")
        rig_layout = QVBoxLayout(rig_group)
        
        from core.animation_data import RigTypeDetector
        rig_emoji = RigTypeDetector.get_rig_emoji(animation.rig_type)
        rig_color = RigTypeDetector.get_rig_color(animation.rig_type)
        
        rig_label = QLabel(f"Rig Type: {rig_emoji} {animation.rig_type}")
        rig_label.setStyleSheet(f"font-weight: bold; color: {rig_color};")
        rig_layout.addWidget(rig_label)
        
        self.content_layout.addWidget(rig_group)
        
        # Tags
        if animation.tags:
            tags_group = self.create_info_group("Tags")
            tags_layout = QVBoxLayout(tags_group)
            
            # Create tag display
            tags_widget = QWidget()
            tags_widget_layout = QGridLayout(tags_widget)
            tags_widget_layout.setSpacing(4)
            
            for i, tag in enumerate(animation.tags[:12]):  # Show first 12 tags
                tag_label = QLabel(tag)
                tag_label.setStyleSheet("""
                    background-color: #4a90e2;
                    color: white;
                    padding: 3px 8px;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: bold;
                """)
                tag_label.setAlignment(Qt.AlignCenter)
                
                row = i // 3
                col = i % 3
                tags_widget_layout.addWidget(tag_label, row, col)
            
            if len(animation.tags) > 12:
                more_label = QLabel(f"+{len(animation.tags) - 12} more")
                more_label.setStyleSheet("color: #888; font-style: italic; font-size: 10px;")
                row = 4
                tags_widget_layout.addWidget(more_label, row, 0, 1, 3)
            
            tags_layout.addWidget(tags_widget)
            self.content_layout.addWidget(tags_group)
        
        # Bone data preview
        if animation.bone_data:
            bones_group = self.create_info_group(f"Animated Bones ({len(animation.bone_data)})")
            bones_layout = QVBoxLayout(bones_group)
            
            # Show first 10 bones
            bone_names = list(animation.bone_data.keys())[:10]
            for bone_name in bone_names:
                bone_data = animation.bone_data[bone_name]
                bone_info = f"• {bone_name} ({bone_data.total_keyframes} keyframes)"
                label = QLabel(bone_info)
                label.setStyleSheet("font-family: monospace; font-size: 10px;")
                bones_layout.addWidget(label)
            
            if len(animation.bone_data) > 10:
                more_bones_label = QLabel(f"... and {len(animation.bone_data) - 10} more bones")
                more_bones_label.setStyleSheet("color: #888; font-style: italic; font-size: 10px;")
                bones_layout.addWidget(more_bones_label)
            
            self.content_layout.addWidget(bones_group)
        
        # Creation info
        creation_group = self.create_info_group("Creation Info")
        creation_layout = QVBoxLayout(creation_group)
        
        creation_info = [
            f"Created: {animation.created_date[:16].replace('T', ' ')}",
            f"Author: {animation.author or 'Unknown'}",
            f"Category: {animation.category.title()}",
            f"Usage Count: {animation.usage_count}"
        ]
        
        for info in creation_info:
            label = QLabel(info)
            creation_layout.addWidget(label)
        
        self.content_layout.addWidget(creation_group)
        self.content_layout.addStretch()
    
    def load_large_preview(self, preview_label: QLabel, animation: AnimationMetadata):
        """Load large preview image for the animation (300x300)"""
        thumbnail_loaded = False
        
        # Check if animation has thumbnail path in metadata
        if hasattr(animation, 'thumbnail') and animation.thumbnail:
            thumbnail_path = Path("animation_library") / animation.thumbnail
            if thumbnail_path.exists():
                # Load the actual thumbnail image
                pixmap = QPixmap(str(thumbnail_path))
                if not pixmap.isNull():
                    # Scale to fit 300x300 while maintaining aspect ratio
                    scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    # Create a centered pixmap with dark background
                    final_pixmap = QPixmap(300, 300)
                    final_pixmap.fill(QColor(46, 46, 46))  # #2e2e2e background
                    
                    painter = QPainter(final_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    
                    # Center the scaled image
                    x = (300 - scaled_pixmap.width()) // 2
                    y = (300 - scaled_pixmap.height()) // 2
                    painter.drawPixmap(x, y, scaled_pixmap)
                    
                    painter.end()
                    preview_label.setPixmap(final_pixmap)
                    thumbnail_loaded = True
        
        # Fallback to animation name-based thumbnail path
        if not thumbnail_loaded:
            # Try to construct thumbnail path from animation name
            animation_id = getattr(animation, 'id', animation.name)
            thumbnail_filename = f"{animation_id}.png"
            thumbnail_path = Path("animation_library") / "thumbnails" / thumbnail_filename
            
            if thumbnail_path.exists():
                pixmap = QPixmap(str(thumbnail_path))
                if not pixmap.isNull():
                    # Scale to fit 300x300 while maintaining aspect ratio
                    scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    # Create a centered pixmap with dark background
                    final_pixmap = QPixmap(300, 300)
                    final_pixmap.fill(QColor(46, 46, 46))  # #2e2e2e background
                    
                    painter = QPainter(final_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    
                    # Center the scaled image
                    x = (300 - scaled_pixmap.width()) // 2
                    y = (300 - scaled_pixmap.height()) // 2
                    painter.drawPixmap(x, y, scaled_pixmap)
                    
                    painter.end()
                    preview_label.setPixmap(final_pixmap)
                    thumbnail_loaded = True
        
        # Fallback to placeholder icon if no image found
        if not thumbnail_loaded:
            self.show_large_placeholder_icon(preview_label)
    
    def show_large_placeholder_icon(self, preview_label: QLabel):
        """Show a large placeholder icon for missing thumbnails (300x300)"""
        pixmap = QPixmap(300, 300)
        pixmap.fill(QColor(46, 46, 46))  # #2e2e2e background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw large animation icon
        painter.setPen(QPen(QColor("#666666"), 3))
        painter.setBrush(QBrush(QColor("#666666")))
        
        # Simple figure representation (scaled up for 300x300)
        center_x, center_y = 150, 150
        
        # Head
        painter.drawEllipse(center_x-20, center_y-60, 40, 40)
        
        # Body
        painter.drawLine(center_x, center_y-20, center_x, center_y+40)
        
        # Arms
        painter.drawLine(center_x-30, center_y-10, center_x+30, center_y-10)
        
        # Legs
        painter.drawLine(center_x, center_y+40, center_x-20, center_y+80)
        painter.drawLine(center_x, center_y+40, center_x+20, center_y+80)
        
        # Add text
        painter.setPen(QColor("#888888"))
        painter.setFont(QFont("Arial", 14))
        painter.drawText(center_x-50, center_y+120, "No Preview")
        
        painter.end()
        preview_label.setPixmap(pixmap)
    
    def on_update_thumbnail_clicked(self):
        
        """Handle update thumbnail button click"""
        if self.current_animation:
            self.request_thumbnail_update(self.current_animation)
            print(f"🖱️ DEBUG: Update thumbnail button clicked")
            if self.current_animation:
                print(f"🎬 DEBUG: Current animation: {self.current_animation.name}")
                print(f"🎬 DEBUG: Animation ID: {getattr(self.current_animation, 'id', 'NO_ID')}")
                self.request_thumbnail_update(self.current_animation)
            else:
                print("❌ DEBUG: No current animation selected")
    
    def request_thumbnail_update(self, animation: AnimationMetadata):
        """Request thumbnail update for the current animation"""
        # Use animation name as specified in the requirements
        animation_name = animation.name
        print(f"📤 DEBUG: Emitting thumbnail_update_requested for: '{animation_name}'")

        self.thumbnail_update_requested.emit(animation_name)
    
    def refresh_thumbnail(self, animation_name: str):
        """Refresh the large preview image for the specified animation with cache clearing"""
        if (self.current_animation and 
            animation_name == self.current_animation.name):
            
            print(f"🔄 METADATA: Refreshing large preview for: {animation_name}")
            
            # Clear Qt's pixmap cache
            from PySide6.QtGui import QPixmapCache
            QPixmapCache.clear()
            
            # Find the preview label in the current layout
            preview_label = self.findChild(QLabel, "large_preview")
            if preview_label:
                # Force reload the large preview image
                self.load_large_preview_force_refresh(preview_label, self.current_animation)
                print(f"🖼️ METADATA: Refreshed large preview for: {animation_name}")
            else:
                print(f"⚠️ METADATA: Preview label not found for: {animation_name}")

    def load_large_preview_force_refresh(self, preview_label: QLabel, animation: AnimationMetadata):
        """Load large preview image with forced refresh (no cache)"""
        thumbnail_loaded = False
        
        # Check if animation has thumbnail path in metadata
        if hasattr(animation, 'thumbnail') and animation.thumbnail:
            thumbnail_path = Path("animation_library") / animation.thumbnail
            if thumbnail_path.exists():
                try:
                    print(f"🔍 METADATA: Loading large preview from: {thumbnail_path}")
                    
                    # Load with cache busting
                    pixmap = QPixmap(str(thumbnail_path))
                    if not pixmap.isNull():
                        # Force detach from cache
                        pixmap = pixmap.copy()
                        
                        # Scale to fit 300x300 while maintaining aspect ratio
                        scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        
                        # Create centered pixmap with dark background
                        final_pixmap = QPixmap(300, 300)
                        final_pixmap.fill(QColor(46, 46, 46))
                        
                        painter = QPainter(final_pixmap)
                        painter.setRenderHint(QPainter.Antialiasing)
                        
                        # Center the scaled image
                        x = (300 - scaled_pixmap.width()) // 2
                        y = (300 - scaled_pixmap.height()) // 2
                        painter.drawPixmap(x, y, scaled_pixmap)
                        painter.end()
                        
                        preview_label.setPixmap(final_pixmap)
                        thumbnail_loaded = True
                        print(f"✅ METADATA: Large preview loaded successfully")
                    else:
                        print(f"❌ METADATA: Pixmap is null")
                except Exception as e:
                    print(f"❌ METADATA: Error loading large preview: {e}")
        
        # Fallback to animation name-based thumbnail path
        if not thumbnail_loaded:
            animation_id = getattr(animation, 'id', animation.name)
            thumbnail_filename = f"{animation_id}.png"
            thumbnail_path = Path("animation_library") / "thumbnails" / thumbnail_filename
            
            if thumbnail_path.exists():
                try:
                    pixmap = QPixmap(str(thumbnail_path))
                    if not pixmap.isNull():
                        pixmap = pixmap.copy()  # Force detach from cache
                        scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        
                        final_pixmap = QPixmap(300, 300)
                        final_pixmap.fill(QColor(46, 46, 46))
                        
                        painter = QPainter(final_pixmap)
                        painter.setRenderHint(QPainter.Antialiasing)
                        
                        x = (300 - scaled_pixmap.width()) // 2
                        y = (300 - scaled_pixmap.height()) // 2
                        painter.drawPixmap(x, y, scaled_pixmap)
                        painter.end()
                        
                        preview_label.setPixmap(final_pixmap)
                        thumbnail_loaded = True
                        print(f"✅ METADATA: Fallback large preview loaded")
                except Exception as e:
                    print(f"❌ METADATA: Error loading fallback large preview: {e}")
        
        # Show placeholder if still not loaded
        if not thumbnail_loaded:
            self.show_large_placeholder_icon(preview_label)
            print(f"⚠️ METADATA: Using large placeholder icon")
    
    def check_for_video_preview(self, animation):
        """Check if animation has a video preview available"""
        try:
            # Check if animation has preview field in metadata
            if hasattr(animation, 'preview') and animation.preview:
                preview_path = Path("animation_library") / animation.preview
                
                # Check for MP4 video
                if preview_path.suffix.lower() == '.mp4' and preview_path.exists():
                    return True
                
                # Check for frame sequence directory
                if preview_path.is_dir() and any(preview_path.glob("*.png")):
                    return True
            
            # Fallback: check previews directory for files matching animation name
            animation_id = getattr(animation, 'id', animation.name)
            previews_dir = Path("animation_library") / "previews"
            
            if previews_dir.exists():
                # Check for MP4 file
                mp4_files = list(previews_dir.glob(f"{animation_id}*.mp4"))
                if mp4_files:
                    return True
                
                # Check for frame sequence directories
                for item in previews_dir.iterdir():
                    if item.is_dir() and animation_id in item.name:
                        if any(item.glob("*.png")):
                            return True
            
            return False
            
        except Exception as e:
            print(f"Error checking for video preview: {e}")
            return False
    
    def create_video_player(self, layout, animation):
        """Create video player widget for animation preview"""
        try:
            # Create video widget
            self.video_widget = QVideoWidget()
            self.video_widget.setFixedSize(300, 300)
            self.video_widget.setStyleSheet("""
                QVideoWidget {
                    border: none;
                    border-radius: 8px;
                    background-color: #2e2e2e;
                }
            """)
            
            # Create media player
            self.media_player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.media_player.setAudioOutput(self.audio_output)
            self.media_player.setVideoOutput(self.video_widget)
            
            # Find and load preview video
            preview_path = self.get_preview_video_path(animation)
            if preview_path and preview_path.exists():
                if preview_path.suffix.lower() == '.mp4':
                    # Load MP4 video
                    media_url = QUrl.fromLocalFile(str(preview_path.absolute()))
                    self.media_player.setSource(media_url)
                    self.media_player.setLoops(QMediaPlayer.Infinite)  # Loop playback
                    
                    # Auto-play when loaded
                    self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
                    
                    print(f"📹 Loaded video preview: {preview_path.name}")
                else:
                    # For frame sequences, show first frame as static image
                    self.create_image_preview(layout, animation)
                    return
            else:
                # Fallback to image preview
                self.create_image_preview(layout, animation)
                return
            
            layout.addWidget(self.video_widget, 0, Qt.AlignHCenter)
            
        except Exception as e:
            print(f"Error creating video player: {e}")
            # Fallback to image preview
            self.create_image_preview(layout, animation)
    
    def create_image_preview(self, layout, animation):
        """Create static image preview widget"""
        preview_label = QLabel()
        preview_label.setObjectName("large_preview")
        preview_label.setFixedSize(300, 300)
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setStyleSheet("""
            QLabel {
                border: none;
                border-radius: 8px;
                background-color: #2e2e2e;
            }
        """)
        
        # Load large preview image
        self.load_large_preview(preview_label, animation)
        
        layout.addWidget(preview_label, 0, Qt.AlignHCenter)
    
    def get_preview_video_path(self, animation):
        """Get the path to the preview video for an animation"""
        try:
            # Check metadata for preview path
            if hasattr(animation, 'preview') and animation.preview:
                preview_path = Path("animation_library") / animation.preview
                if preview_path.exists():
                    return preview_path
            
            # Fallback: search previews directory
            animation_id = getattr(animation, 'id', animation.name)
            previews_dir = Path("animation_library") / "previews"
            
            if previews_dir.exists():
                # Look for MP4 file
                mp4_files = list(previews_dir.glob(f"{animation_id}*.mp4"))
                if mp4_files:
                    return mp4_files[0]  # Return most recent
                
                # Look for frame sequence directory
                for item in previews_dir.iterdir():
                    if item.is_dir() and animation_id in item.name:
                        if any(item.glob("*.png")):
                            return item
            
            return None
            
        except Exception as e:
            print(f"Error getting preview video path: {e}")
            return None
    
    def on_media_status_changed(self, status):
        """Handle media player status changes"""
        try:
            if status == QMediaPlayer.LoadedMedia:
                # Start playback when media is loaded
                self.media_player.play()
                print("🎬 Started video preview playback")
        except Exception as e:
            print(f"Error handling media status change: {e}")
    
    def cleanup_media_player(self):
        """Clean up media player resources"""
        try:
            if self.media_player:
                self.media_player.stop()
                self.media_player.setSource(QUrl())
                self.media_player = None
            
            if self.audio_output:
                self.audio_output = None
            
            if self.video_widget:
                self.video_widget.setParent(None)
                self.video_widget = None
                
        except Exception as e:
            print(f"Error cleaning up media player: {e}")

    def create_info_group(self, title: str) -> QGroupBox:
        """Create a styled info group"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                color: #ffffff;
                background-color: #4a4a4a;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #ffffff;
                background-color: #4a4a4a;
            }
        """)
        return group