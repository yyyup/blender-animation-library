#!/usr/bin/env python3
"""
Animation Library Qt GUI - Main Application
Refactored professional interface with clean architecture
"""

import sys
import logging
from pathlib import Path

# Add core modules to path
gui_dir = Path(__file__).parent.parent
if str(gui_dir) not in sys.path:
    sys.path.insert(0, str(gui_dir))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QGroupBox, QLabel, QPushButton, QLineEdit, QComboBox,
    QScrollArea, QStatusBar, QMessageBox, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QIcon

from gui.utils.blender_connection import BlenderConnectionHandler
from gui.widgets.animation_card import AnimationCard, AnimationCardGrid
from gui.widgets.bone_mapping import BoneMappingWidget
from core.animation_data import AnimationMetadata, ApplyOptions
from core.library_storage import AnimationLibraryManager
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnimationLibraryMainWindow(QMainWindow):
    """Main application window for Animation Library"""
    
    def __init__(self):
        super().__init__()
        
        # Core components
        self.blender_connection = BlenderConnectionHandler()
        self.library_manager = AnimationLibraryManager()
        
        # Current state
        self.current_selection = []
        self.current_armature = None
        self.available_armatures = []
        
        # UI Components
        self.animation_cards = []
        
        self.setup_ui()
        self.setup_connections()
        self.load_library()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_library_display)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("Animation Library - Professional Edition")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Apply professional dark theme
        self.setStyleSheet(self.get_application_style())
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left panel - Library browser
        left_panel = self.create_library_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Controls and mapping
        right_panel = self.create_controls_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([1000, 600])
        
        # Status bar
        self.setup_status_bar()
    
    def create_library_panel(self) -> QWidget:
        """Create the animation library panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        
        # Connection section
        connection_section = self.create_connection_section()
        layout.addWidget(connection_section)
        
        # Search and filter section
        search_section = self.create_search_section()
        layout.addWidget(search_section)
        
        # Animation library section
        library_section = self.create_animation_library_section()
        layout.addWidget(library_section)
        
        return panel
    
    def create_connection_section(self) -> QWidget:
        """Create Blender connection controls"""
        section = QGroupBox("Blender Connection")
        layout = QHBoxLayout(section)
        
        # Connection button
        self.connect_btn = QPushButton("Connect to Blender")
        self.connect_btn.setObjectName("primaryButton")
        self.connect_btn.clicked.connect(self.toggle_blender_connection)
        layout.addWidget(self.connect_btn)
        
        # Extract button
        self.extract_btn = QPushButton("Extract Animation")
        self.extract_btn.setObjectName("secondaryButton")
        self.extract_btn.setEnabled(False)
        self.extract_btn.clicked.connect(self.extract_animation)
        layout.addWidget(self.extract_btn)
        
        # Connection status indicator
        self.connection_indicator = QLabel("●")
        self.connection_indicator.setObjectName("connectionIndicator")
        self.connection_indicator.setStyleSheet("color: #ff6b6b; font-size: 16px;")
        layout.addWidget(self.connection_indicator)
        
        layout.addStretch()
        
        return section
    
    def create_search_section(self) -> QWidget:
        """Create search and filter controls"""
        section = QGroupBox("Search & Filter")
        layout = QVBoxLayout(section)
        
        # Search row
        search_row = QHBoxLayout()
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search animations by name, description, or tags...")
        self.search_box.textChanged.connect(self.filter_animations)
        search_row.addWidget(self.search_box)
        
        # Tag filter
        self.tag_filter = QComboBox()
        self.tag_filter.setMinimumWidth(120)
        self.tag_filter.addItem("All Tags")
        self.tag_filter.currentTextChanged.connect(self.filter_animations)
        search_row.addWidget(self.tag_filter)
        
        # Rig type filter
        self.rig_filter = QComboBox()
        self.rig_filter.addItem("All Rigs")
        self.rig_filter.addItem("Rigify")
        self.rig_filter.addItem("Unknown")
        self.rig_filter.currentTextChanged.connect(self.filter_animations)
        search_row.addWidget(self.rig_filter)
        
        layout.addLayout(search_row)
        
        # Statistics row
        self.stats_label = QLabel("No animations loaded")
        self.stats_label.setStyleSheet("color: #888; font-size: 10px; padding: 4px;")
        layout.addWidget(self.stats_label)
        
        return section
    
    def create_animation_library_section(self) -> QWidget:
        """Create animation library display"""
        section = QGroupBox("Animation Library")
        layout = QVBoxLayout(section)
        
        # Scroll area for animation cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Animation cards grid
        self.animation_grid = AnimationCardGrid()
        self.scroll_area.setWidget(self.animation_grid)
        
        layout.addWidget(self.scroll_area)
        
        return section
    
    def create_controls_panel(self) -> QWidget:
        """Create the controls and mapping panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        
        # Current selection section
        selection_section = self.create_selection_section()
        layout.addWidget(selection_section)
        
        # Bone mapping section
        self.bone_mapping_widget = BoneMappingWidget()
        layout.addWidget(self.bone_mapping_widget)
        
        return panel
    
    def create_selection_section(self) -> QWidget:
        """Create current selection display"""
        section = QGroupBox("Current Selection")
        layout = QVBoxLayout(section)
        
        # Armature info
        self.armature_label = QLabel("No armature selected")
        self.armature_label.setObjectName("infoLabel")
        layout.addWidget(self.armature_label)
        
        # Bones info
        self.bones_label = QLabel("No bones selected")
        self.bones_label.setObjectName("infoLabel")
        layout.addWidget(self.bones_label)
        
        # Frame info
        self.frame_label = QLabel("Frame: --")
        self.frame_label.setObjectName("infoLabel")
        layout.addWidget(self.frame_label)
        
        return section
    
    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress bar for operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Connection status
        self.connection_status = QLabel("Disconnected")
        self.connection_status.setStyleSheet("color: #ff6b6b; font-weight: bold; padding: 4px;")
        self.status_bar.addPermanentWidget(self.connection_status)
        
        # Show ready message
        self.status_bar.showMessage("Animation Library ready", 3000)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Blender connection signals
        self.blender_connection.connected.connect(self.on_blender_connected)
        self.blender_connection.disconnected.connect(self.on_blender_disconnected)
        self.blender_connection.connection_error.connect(self.on_connection_error)
        
        # Data signals
        self.blender_connection.scene_info_received.connect(self.on_scene_info_received)
        self.blender_connection.selection_updated.connect(self.on_selection_updated)
        self.blender_connection.animation_extracted.connect(self.on_animation_extracted)
        self.blender_connection.animation_applied.connect(self.on_animation_applied)
        self.blender_connection.error_received.connect(self.on_blender_error)
        
        # Bone mapping signals
        self.bone_mapping_widget.mapping_changed.connect(self.on_bone_mapping_changed)
    
    def get_application_style(self) -> str:
        """Get the application stylesheet"""
        return """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            QGroupBox {
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 12px;
                font-weight: bold;
                padding-top: 8px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #ffffff;
            }
            
            #primaryButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            
            #primaryButton:hover {
                background-color: #106ebe;
            }
            
            #primaryButton:pressed {
                background-color: #005a9e;
            }
            
            #secondaryButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            
            #secondaryButton:hover {
                background-color: #4a4a4a;
                border-color: #0078d4;
            }
            
            #secondaryButton:disabled {
                background-color: #2a2a2a;
                color: #666;
                border-color: #333;
            }
            
            QLineEdit, QComboBox {
                background-color: #404040;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
            
            QLineEdit:focus, QComboBox:focus {
                border-color: #0078d4;
            }
            
            #infoLabel {
                color: #cccccc;
                font-size: 11px;
                padding: 2px;
            }
            
            QScrollArea {
                border: 1px solid #555;
                border-radius: 4px;
            }
            
            QStatusBar {
                background-color: #353535;
                border-top: 1px solid #555;
                color: #cccccc;
            }
        """
    
    # Connection handling
    def toggle_blender_connection(self):
        """Toggle Blender connection"""
        if self.blender_connection.is_connected():
            self.blender_connection.disconnect_from_blender()
        else:
            self.connect_btn.setEnabled(False)
            self.connect_btn.setText("Connecting...")
            success = self.blender_connection.connect_to_blender()
            
            if not success:
                self.connect_btn.setEnabled(True)
                self.connect_btn.setText("Connect to Blender")
    
    def on_blender_connected(self):
        """Handle successful Blender connection"""
        self.connection_status.setText("Connected")
        self.connection_status.setStyleSheet("color: #51cf66; font-weight: bold; padding: 4px;")
        self.connection_indicator.setStyleSheet("color: #51cf66; font-size: 16px;")
        
        self.connect_btn.setText("Disconnect")
        self.connect_btn.setEnabled(True)
        self.extract_btn.setEnabled(True)
        
        self.status_bar.showMessage("Connected to Blender successfully", 3000)
    
    def on_blender_disconnected(self):
        """Handle Blender disconnection"""
        self.connection_status.setText("Disconnected")
        self.connection_status.setStyleSheet("color: #ff6b6b; font-weight: bold; padding: 4px;")
        self.connection_indicator.setStyleSheet("color: #ff6b6b; font-size: 16px;")
        
        self.connect_btn.setText("Connect to Blender")
        self.connect_btn.setEnabled(True)
        self.extract_btn.setEnabled(False)
        
        self.status_bar.showMessage("Disconnected from Blender", 3000)
    
    def on_connection_error(self, error_msg: str):
        """Handle connection errors"""
        QMessageBox.warning(self, "Connection Error", f"Failed to connect to Blender:\n{error_msg}")
        self.on_blender_disconnected()
    
    # Data handling
    def on_scene_info_received(self, scene_data: dict):
        """Handle scene information from Blender"""
        self.available_armatures = scene_data.get('armatures', [])
        
        # Update bone mapping with available bones
        if self.current_armature:
            for armature_data in self.available_armatures:
                if armature_data['name'] == self.current_armature:
                    target_bones = armature_data['bones']
                    # Update bone mapping with current animation's bones if available
                    source_bones = []
                    if hasattr(self, 'current_animation_data'):
                        source_bones = list(self.current_animation_data.get('bone_data', {}).keys())
                    
                    self.bone_mapping_widget.update_bones(source_bones, target_bones)
                    break
    
    def on_selection_updated(self, selection_data: dict):
        """Handle selection update from Blender"""
        armature = selection_data.get('armature_name')
        bones = selection_data.get('selected_bones', [])
        frame = selection_data.get('current_frame', 0)
        
        self.current_armature = armature
        self.current_selection = bones
        
        # Update UI
        if armature:
            self.armature_label.setText(f"Armature: {armature}")
        else:
            self.armature_label.setText("No armature selected")
        
        if bones:
            if len(bones) <= 5:
                bone_text = ", ".join(bones)
            else:
                bone_text = f"{', '.join(bones[:3])} +{len(bones)-3} more"
            self.bones_label.setText(f"Bones: {bone_text}")
        else:
            self.bones_label.setText("No bones selected")
        
        self.frame_label.setText(f"Frame: {frame}")
    
    def on_animation_extracted(self, animation_data: dict):
        """Handle animation extraction from Blender"""
        try:
            # Store current animation data for bone mapping
            self.current_animation_data = animation_data
            
            # Create animation metadata
            metadata = AnimationMetadata.from_blender_data(animation_data)
            
            # Add to library
            self.library_manager.add_animation(metadata)
            
            # Refresh display
            self.refresh_library_display()
            self.update_tag_filter()
            
            # Update bone mapping with extracted bones
            source_bones = list(animation_data.get('bone_data', {}).keys())
            target_bones = []
            if self.current_armature:
                for armature_data in self.available_armatures:
                    if armature_data['name'] == self.current_armature:
                        target_bones = armature_data['bones']
                        break
            
            self.bone_mapping_widget.update_bones(source_bones, target_bones)
            
            self.status_bar.showMessage(f"Animation '{animation_data['action_name']}' extracted successfully", 3000)
            
        except Exception as e:
            logger.error(f"Error processing extracted animation: {e}")
            QMessageBox.warning(self, "Extraction Error", f"Failed to process extracted animation:\n{str(e)}")
    
    def on_animation_applied(self, result_data: dict):
        """Handle animation application result"""
        action_name = result_data.get('action_name', 'Unknown')
        bones_applied = result_data.get('bones_applied', 0)
        keyframes_applied = result_data.get('keyframes_applied', 0)
        
        self.status_bar.showMessage(
            f"Applied '{action_name}': {bones_applied} bones, {keyframes_applied} keyframes",
            5000
        )
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
    
    def on_blender_error(self, error_msg: str):
        """Handle errors from Blender"""
        QMessageBox.warning(self, "Blender Error", error_msg)
        self.progress_bar.setVisible(False)
    
    # Animation library operations
    def extract_animation(self):
        """Extract animation from Blender"""
        if not self.blender_connection.is_connected():
            QMessageBox.warning(self, "Not Connected", "Please connect to Blender first")
            return
        
        if not self.current_armature:
            QMessageBox.warning(self, "No Armature", "Please select an armature in Blender")
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Request extraction
        success = self.blender_connection.extract_animation()
        if not success:
            self.progress_bar.setVisible(False)
            QMessageBox.warning(self, "Extraction Failed", "Failed to send extraction request to Blender")
    
    def apply_animation(self, animation_data: dict):
        """Apply animation to current armature"""
        if not self.blender_connection.is_connected():
            QMessageBox.warning(self, "Not Connected", "Please connect to Blender first")
            return
        
        if not self.current_armature:
            QMessageBox.warning(self, "No Armature", "Please select an armature in Blender")
            return
        
        # Get apply options from bone mapping widget
        apply_options = self.bone_mapping_widget.get_apply_options()
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # Send apply request
        success = self.blender_connection.apply_animation(animation_data, apply_options)
        if not success:
            self.progress_bar.setVisible(False)
            QMessageBox.warning(self, "Apply Failed", "Failed to send apply request to Blender")
        else:
            self.status_bar.showMessage(f"Applying animation '{animation_data['name']}'...", 2000)
    
    def preview_animation(self, animation_data: dict):
        """Preview animation (placeholder for future implementation)"""
        QMessageBox.information(self, "Preview", f"Preview for '{animation_data['name']}' would be shown here")
    
    def edit_animation(self, animation_data: dict):
        """Edit animation metadata (placeholder for future implementation)"""
        QMessageBox.information(self, "Edit", f"Edit dialog for '{animation_data['name']}' would be shown here")
    
    def delete_animation(self, animation_data: dict):
        """Delete animation from library"""
        reply = QMessageBox.question(
            self, "Delete Animation",
            f"Are you sure you want to delete '{animation_data['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            animation_id = animation_data['id']
            self.library_manager.remove_animation(animation_id)
            self.refresh_library_display()
            self.update_tag_filter()
            self.status_bar.showMessage(f"Deleted animation '{animation_data['name']}'", 3000)
    
    # Library management
    def load_library(self):
        """Load animation library from disk"""
        try:
            self.library_manager.load_library()
            self.refresh_library_display()
            self.update_tag_filter()
            
            count = len(self.library_manager.get_all_animations())
            self.status_bar.showMessage(f"Loaded {count} animations from library", 3000)
            
        except Exception as e:
            logger.error(f"Failed to load library: {e}")
            QMessageBox.warning(self, "Load Error", f"Failed to load animation library:\n{str(e)}")
    
    def refresh_library_display(self):
        """Refresh the animation library display"""
        # Get filtered animations
        animations = self.get_filtered_animations()
        
        # Clear existing cards
        self.animation_grid.clear_cards()
        self.animation_cards.clear()
        
        # Create new cards
        for animation_data in animations:
            card = AnimationCard(animation_data.to_dict())
            
            # Connect signals
            card.apply_requested.connect(self.apply_animation)
            card.preview_requested.connect(self.preview_animation)
            card.edit_requested.connect(self.edit_animation)
            card.delete_requested.connect(self.delete_animation)
            
            self.animation_grid.add_card(card)
            self.animation_cards.append(card)
        
        # Update statistics
        self.update_statistics()
    
    def get_filtered_animations(self) -> list:
        """Get animations filtered by current search criteria"""
        all_animations = self.library_manager.get_all_animations()
        
        # Filter by search text
        search_text = self.search_box.text().lower()
        if search_text:
            all_animations = [
                anim for anim in all_animations
                if (search_text in anim.name.lower() or
                    search_text in anim.description.lower() or
                    any(search_text in tag.lower() for tag in anim.tags))
            ]
        
        # Filter by tag
        selected_tag = self.tag_filter.currentText()
        if selected_tag != "All Tags":
            all_animations = [
                anim for anim in all_animations
                if selected_tag.lower() in [tag.lower() for tag in anim.tags]
            ]
        
        # Filter by rig type
        selected_rig = self.rig_filter.currentText()
        if selected_rig != "All Rigs":
            all_animations = [
                anim for anim in all_animations
                if anim.rig_type.lower() == selected_rig.lower()
            ]
        
        return all_animations
    
    def filter_animations(self):
        """Apply current filters to animation display"""
        self.refresh_library_display()
    
    def update_tag_filter(self):
        """Update the tag filter dropdown"""
        current_tag = self.tag_filter.currentText()
        self.tag_filter.clear()
        self.tag_filter.addItem("All Tags")
        
        # Collect all unique tags
        all_tags = set()
        for animation in self.library_manager.get_all_animations():
            all_tags.update(animation.tags)
        
        # Add tags to filter
        for tag in sorted(all_tags):
            self.tag_filter.addItem(tag)
        
        # Restore previous selection if it exists
        tag_index = self.tag_filter.findText(current_tag)
        if tag_index >= 0:
            self.tag_filter.setCurrentIndex(tag_index)
    
    def update_statistics(self):
        """Update library statistics display"""
        all_animations = self.library_manager.get_all_animations()
        filtered_animations = self.get_filtered_animations()
        
        total_count = len(all_animations)
        filtered_count = len(filtered_animations)
        
        if total_count == filtered_count:
            self.stats_label.setText(f"{total_count} animations")
        else:
            self.stats_label.setText(f"{filtered_count} of {total_count} animations")
    
    # Event handlers
    def on_bone_mapping_changed(self, bone_mapping: dict):
        """Handle bone mapping changes"""
        # Could store or validate bone mapping here
        pass
    
    def closeEvent(self, event):
        """Handle application close"""
        # Disconnect from Blender
        if self.blender_connection.is_connected():
            self.blender_connection.disconnect_from_blender()
        
        # Save library
        try:
            self.library_manager.save_library()
        except Exception as e:
            logger.error(f"Failed to save library on exit: {e}")
        
        event.accept()


def main():
    """Main application entry point"""
    # Create application
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Animation Library")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Animation Studio")
    
    # Set application icon (if available)
    # app.setWindowIcon(QIcon("path/to/icon.png"))
    
    # Create and show main window
    window = AnimationLibraryMainWindow()
    window.show()
    
    # Center window on screen
    screen = app.primaryScreen().geometry()
    window_geo = window.geometry()
    x = (screen.width() - window_geo.width()) // 2
    y = (screen.height() - window_geo.height()) // 2
    window.move(x, y)
    
    # Run application
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        app.quit()


if __name__ == "__main__":
    main()