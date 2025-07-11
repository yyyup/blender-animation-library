#!/usr/bin/env python3
"""
Animation Library Qt GUI - Main Application
Clean, modular Studio Library interface
"""

import sys
import logging
from pathlib import Path

# Add core modules to path
gui_dir = Path(__file__).parent.parent
if str(gui_dir) not in sys.path:
    sys.path.insert(0, str(gui_dir))

from PySide6.QtWidgets import QApplication, QMainWindow, QStatusBar, QProgressBar, QLabel, QMessageBox
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont

from gui.utils.blender_connection import BlenderConnectionHandler
from gui.layouts.studio_layout import StudioLayoutManager
from core.animation_data import AnimationMetadata, ApplyOptions
from core.library_storage import AnimationLibraryManager
from gui.widgets.animation_card import AnimationCard

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnimationLibraryMainWindow(QMainWindow):
    """Main window with modular Studio Library layout"""
    
    def __init__(self):
        super().__init__()
        
        # Core components
        self.blender_connection = BlenderConnectionHandler()
        self.library_manager = AnimationLibraryManager()
        
        # Layout manager
        self.layout_manager = StudioLayoutManager(self)
        
        # Current state
        self.current_selection = []
        self.current_armature = None
        self.available_armatures = []
        self.current_filter = "all"
        self.current_animation = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_library()
        
        print("🎨 Modular Studio Library interface initialized!")
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_selection_info)
        self.refresh_timer.start(2000)
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("Animation Library - Professional Studio Layout")
        self.setGeometry(100, 100, 1800, 1000)
        
        # Apply professional dark theme
        self.setStyleSheet(self.get_application_style())
        
        # Setup layout using layout manager
        central_widget = self.layout_manager.setup_layout()
        self.setCentralWidget(central_widget)
        
        # Status bar
        self.setup_status_bar()
        
        print("✅ Modular Studio Library layout created!")
    
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
        self.status_bar.showMessage("Animation Library ready - Modular Studio Layout", 3000)
        
        # Status bar styling
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #4a4a4a;
                border-top: 1px solid #555;
                color: #ccc;
                font-size: 11px;
            }
        """)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Get widgets from layout manager
        toolbar = self.layout_manager.get_widget('toolbar')
        folder_tree = self.layout_manager.get_widget('folder_tree')
        animation_grid = self.layout_manager.get_widget('animation_grid')
        
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
        
        # UI signals
        toolbar.connect_requested.connect(self.toggle_blender_connection)
        toolbar.extract_requested.connect(self.extract_animation)
        toolbar.search_changed.connect(self.on_search_changed)
        toolbar.tag_filter_changed.connect(self.on_tag_filter_changed)
        toolbar.rig_filter_changed.connect(self.on_rig_filter_changed)
        
        folder_tree.folder_selected.connect(self.on_folder_selected)
        animation_grid.animation_selected.connect(self.on_animation_selected)
    
    def get_application_style(self) -> str:
        """Get the application stylesheet"""
        return """
            QMainWindow {
                background-color: #2e2e2e;
                color: #ffffff;
            }
            
            QWidget {
                background-color: #2e2e2e;
                color: #ffffff;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 11px;
            }
            
            QGroupBox {
                border: 2px solid #555;
                border-radius: 6px;
                margin-top: 12px;
                font-weight: bold;
                padding-top: 8px;
                background-color: #393939;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #ffffff;
                background-color: #393939;
            }
            
            #primaryButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            
            #primaryButton:hover {
                background-color: #357abd;
            }
            
            #secondaryButton {
                background-color: #666;
                color: white;
                border: 1px solid #777;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            
            #secondaryButton:hover {
                background-color: #777;
                border-color: #4a90e2;
            }
            
            #secondaryButton:disabled {
                background-color: #444;
                color: #666;
                border-color: #555;
            }
            
            QCheckBox {
                color: #ffffff;
                spacing: 8px;
                font-size: 11px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #555;
                border-radius: 3px;
                background-color: #4a4a4a;
            }
            
            QCheckBox::indicator:checked {
                background-color: #4a90e2;
                border-color: #4a90e2;
            }
            
            QSpinBox {
                background-color: #4a4a4a;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 8px;
                color: #ffffff;
            }
        """
    
    # Connection handling methods
    def toggle_blender_connection(self):
        """Toggle Blender connection"""
        toolbar = self.layout_manager.get_widget('toolbar')
        
        if self.blender_connection.is_connected():
            self.blender_connection.disconnect_from_blender()
        else:
            toolbar.set_connecting(True)
            success = self.blender_connection.connect_to_blender()
            
            if not success:
                toolbar.set_connecting(False)
    
    def on_blender_connected(self):
        """Handle successful Blender connection"""
        toolbar = self.layout_manager.get_widget('toolbar')
        
        self.connection_status.setText("Connected")
        self.connection_status.setStyleSheet("color: #51cf66; font-weight: bold; padding: 4px;")
        
        toolbar.set_connected(True)
        toolbar.set_connecting(False)
        
        self.status_bar.showMessage("Connected to Blender successfully", 3000)
    
    def on_blender_disconnected(self):
        """Handle Blender disconnection"""
        toolbar = self.layout_manager.get_widget('toolbar')
        
        self.connection_status.setText("Disconnected")
        self.connection_status.setStyleSheet("color: #ff6b6b; font-weight: bold; padding: 4px;")
        
        toolbar.set_connected(False)
        
        self.status_bar.showMessage("Disconnected from Blender", 3000)
    
    def on_connection_error(self, error_msg: str):
        """Handle connection errors"""
        QMessageBox.warning(self, "Connection Error", f"Failed to connect to Blender:\n{error_msg}")
        self.on_blender_disconnected()
    
    # Data handling methods
    def on_scene_info_received(self, scene_data: dict):
        """Handle scene information from Blender"""
        self.available_armatures = scene_data.get('armatures', [])
        
        if self.current_armature:
            current_rig_type = self.detect_current_rig_type()
            from core.animation_data import RigTypeDetector
            rig_emoji = RigTypeDetector.get_rig_emoji(current_rig_type)
            rig_color = RigTypeDetector.get_rig_color(current_rig_type)
            
            current_rig_label = self.layout_manager.get_widget('current_rig_label')
            current_rig_label.setText(f"Current Rig: {rig_emoji} {current_rig_type}")
            current_rig_label.setStyleSheet(f"color: {rig_color}; font-weight: bold;")
    
    def on_selection_updated(self, selection_data: dict):
        """Handle selection update from Blender"""
        armature = selection_data.get('armature_name')
        bones = selection_data.get('selected_bones', [])
        frame = selection_data.get('current_frame', 0)
        
        self.current_armature = armature
        self.current_selection = bones
        
        # Get UI widgets
        armature_label = self.layout_manager.get_widget('armature_label')
        bones_label = self.layout_manager.get_widget('bones_label')
        frame_label = self.layout_manager.get_widget('frame_label')
        selected_bones_info = self.layout_manager.get_widget('selected_bones_info')
        current_rig_label = self.layout_manager.get_widget('current_rig_label')
        
        # Update UI
        if armature:
            armature_label.setText(f"Armature: {armature}")
            
            current_rig_type = self.detect_current_rig_type()
            from core.animation_data import RigTypeDetector
            rig_emoji = RigTypeDetector.get_rig_emoji(current_rig_type)
            rig_color = RigTypeDetector.get_rig_color(current_rig_type)
            current_rig_label.setText(f"Current Rig: {rig_emoji} {current_rig_type}")
            current_rig_label.setStyleSheet(f"color: {rig_color}; font-weight: bold;")
        else:
            armature_label.setText("No armature selected")
            current_rig_label.setText("Current Rig: Not detected")
            current_rig_label.setStyleSheet("color: #888;")
        
        # Update bone selection display
        if bones:
            if len(bones) <= 5:
                bone_text = ", ".join(bones)
            else:
                bone_text = f"{', '.join(bones[:3])} +{len(bones)-3} more"
            bones_label.setText(f"Bones: {bone_text}")
            
            selected_bones_info.setText(f"Selected: {len(bones)} bones ({', '.join(bones[:2])}{'...' if len(bones) > 2 else ''})")
            selected_bones_info.setStyleSheet("font-size: 9px; color: #51cf66; padding: 2px 8px;")
        else:
            bones_label.setText("No bones selected")
            selected_bones_info.setText("No bones selected")
            selected_bones_info.setStyleSheet("font-size: 9px; color: #888; padding: 2px 8px;")
        
        frame_label.setText(f"Frame: {frame}")
    
    def on_animation_extracted(self, animation_data: dict):
        """Handle animation extraction from Blender"""
        try:
            metadata = AnimationMetadata.from_blender_data(animation_data)
            self.library_manager.add_animation(metadata)
            
            self.refresh_library_display()
            self.update_tag_filter()
            
            self.status_bar.showMessage(f"Animation '{animation_data['action_name']}' extracted successfully", 3000)
            
        except Exception as e:
            logger.error(f"Error processing extracted animation: {e}")
            QMessageBox.warning(self, "Extraction Error", f"Failed to process extracted animation:\n{str(e)}")
    
    def on_animation_applied(self, result_data: dict):
        """Handle animation application result"""
        action_name = result_data.get('action_name', 'Unknown')
        self.status_bar.showMessage(f"Applied '{action_name}' successfully", 3000)
        self.progress_bar.setVisible(False)
    
    def on_blender_error(self, error_msg: str):
        """Handle errors from Blender"""
        QMessageBox.warning(self, "Blender Error", error_msg)
        self.progress_bar.setVisible(False)
    
    # UI event handlers
    def on_folder_selected(self, filter_str: str):
        """Handle folder selection"""
        self.current_filter = filter_str
        self.refresh_library_display()
        print(f"📁 Folder selected: {filter_str}")
    
    def on_animation_selected(self, animation_data: dict):
        """Handle animation selection"""
        try:
            animation_id = animation_data.get('id')
            metadata_panel = self.layout_manager.get_widget('metadata_panel')
            
            if animation_id:
                animation = self.library_manager.get_animation(animation_id)
                if animation:
                    self.current_animation = animation
                    metadata_panel.show_animation_details(animation)
                    print(f"🎬 Animation selected: {animation.name}")
                else:
                    metadata_panel.show_no_selection()
            else:
                metadata_panel.show_no_selection()
        except Exception as e:
            logger.error(f"Error showing animation details: {e}")
    
    def on_search_changed(self, search_text: str):
        """Handle search text change"""
        self.refresh_library_display()
    
    def on_tag_filter_changed(self, tag: str):
        """Handle tag filter change"""
        self.refresh_library_display()
    
    def on_rig_filter_changed(self, rig_type: str):
        """Handle rig filter change"""
        self.refresh_library_display()
    
    # Animation operations
    def extract_animation(self):
        """Extract animation from Blender"""
        if not self.blender_connection.is_connected():
            QMessageBox.warning(self, "Not Connected", "Please connect to Blender first")
            return
        
        if not self.current_armature:
            QMessageBox.warning(self, "No Armature", "Please select an armature in Blender")
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
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
        
        # Get apply options from UI
        selected_bones_only_cb = self.layout_manager.get_widget('selected_bones_only_cb')
        frame_offset_spin = self.layout_manager.get_widget('frame_offset_spin')
        location_cb = self.layout_manager.get_widget('location_cb')
        rotation_cb = self.layout_manager.get_widget('rotation_cb')
        scale_cb = self.layout_manager.get_widget('scale_cb')
        
        apply_options = ApplyOptions(
            selected_bones_only=selected_bones_only_cb.isChecked(),
            frame_offset=frame_offset_spin.value(),
            channels={
                'location': location_cb.isChecked(),
                'rotation': rotation_cb.isChecked(),
                'scale': scale_cb.isChecked()
            },
            bone_mapping={}
        )
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        success = self.blender_connection.apply_animation(animation_data, apply_options)
        if not success:
            self.progress_bar.setVisible(False)
            QMessageBox.warning(self, "Apply Failed", "Failed to send apply request to Blender")
        else:
            print(f"⚡ Applying animation: {animation_data['name']}")
    
    def preview_animation(self, animation_data: dict):
        """Preview animation (placeholder)"""
        QMessageBox.information(self, "Preview", f"Preview for '{animation_data['name']}' would be shown here")
    
    def edit_animation(self, animation_data: dict):
        """Edit animation metadata (placeholder)"""
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
            
            metadata_panel = self.layout_manager.get_widget('metadata_panel')
            metadata_panel.show_no_selection()
            
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
            print(f"📚 Loaded {count} animations from library")
            
        except Exception as e:
            logger.error(f"Failed to load library: {e}")
            QMessageBox.warning(self, "Load Error", f"Failed to load animation library:\n{str(e)}")
    
    def refresh_library_display(self):
        """Refresh the animation library display"""
        animations = self.get_filtered_animations()
        animation_grid = self.layout_manager.get_widget('animation_grid')
        
        animation_grid.clear_cards()
        
        for animation_data in animations:
            card = AnimationCard(animation_data.to_dict())
            
            # Connect signals
            card.apply_requested.connect(self.apply_animation)
            card.preview_requested.connect(self.preview_animation)
            card.edit_requested.connect(self.edit_animation)
            card.delete_requested.connect(self.delete_animation)
            
            animation_grid.add_card(card)
        
        self.update_statistics()
        print(f"🔄 Refreshed display: {len(animations)} animations shown")
    
    def get_filtered_animations(self) -> list:
        """Get animations filtered by current criteria"""
        all_animations = self.library_manager.get_all_animations()
        toolbar = self.layout_manager.get_widget('toolbar')
        
        # Apply folder filter
        if self.current_filter != "all":
            if self.current_filter.startswith("rig_type:"):
                rig_type = self.current_filter.split(":", 1)[1]
                all_animations = [anim for anim in all_animations if anim.rig_type == rig_type]
            elif self.current_filter.startswith("storage:"):
                storage_method = self.current_filter.split(":", 1)[1]
                all_animations = [anim for anim in all_animations if anim.storage_method == storage_method]
            elif self.current_filter.startswith("tag:"):
                tag = self.current_filter.split(":", 1)[1]
                all_animations = [anim for anim in all_animations if tag in anim.tags]
            elif self.current_filter.startswith("category:"):
                category = self.current_filter.split(":", 1)[1].lower()
                all_animations = [anim for anim in all_animations 
                                if any(category in tag.lower() for tag in anim.tags)]
        
        # Apply search filter
        search_text = toolbar.search_box.text().lower()
        if search_text:
            all_animations = [
                anim for anim in all_animations
                if (search_text in anim.name.lower() or
                    search_text in anim.description.lower() or
                    any(search_text in tag.lower() for tag in anim.tags))
            ]
        
        # Apply tag filter
        selected_tag = toolbar.tag_filter.currentText()
        if selected_tag != "All Tags":
            all_animations = [
                anim for anim in all_animations
                if selected_tag.lower() in [tag.lower() for tag in anim.tags]
            ]
        
        # Apply rig filter
        selected_rig = toolbar.rig_filter.currentText()
        if selected_rig != "All Rigs":
            all_animations = [
                anim for anim in all_animations
                if anim.rig_type.lower() == selected_rig.lower()
            ]
        
        return all_animations
    
    def update_tag_filter(self):
        """Update the tag filter dropdown"""
        # Collect all unique tags
        all_tags = set()
        for animation in self.library_manager.get_all_animations():
            all_tags.update(animation.tags)
        
        toolbar = self.layout_manager.get_widget('toolbar')
        toolbar.update_tag_filter(list(all_tags))
    
    def update_statistics(self):
        """Update library statistics display"""
        all_animations = self.library_manager.get_all_animations()
        filtered_animations = self.get_filtered_animations()
        
        total_count = len(all_animations)
        filtered_count = len(filtered_animations)
        
        # Count by storage method
        blend_count = len([a for a in filtered_animations if a.is_blend_file_storage()])
        legacy_count = len([a for a in filtered_animations if a.is_legacy_storage()])
        
        if total_count == filtered_count:
            stats_text = f"{total_count} animations"
        else:
            stats_text = f"{filtered_count} of {total_count} animations"
        
        if blend_count > 0 or legacy_count > 0:
            stats_text += f" (⚡{blend_count} instant, ⏳{legacy_count} legacy)"
        
        toolbar = self.layout_manager.get_widget('toolbar')
        toolbar.update_stats(stats_text)
    
    def detect_current_rig_type(self) -> str:
        """Detect the rig type of the currently selected armature"""
        if not self.current_armature:
            return "Unknown"
        
        current_bones = []
        for armature_data in self.available_armatures:
            if armature_data['name'] == self.current_armature:
                current_bones = armature_data['bones']
                break
        
        from core.animation_data import RigTypeDetector
        return RigTypeDetector.detect_rig_type(self.current_armature, current_bones)
    
    def refresh_selection_info(self):
        """Refresh selection info periodically"""
        if self.blender_connection.is_connected():
            # Could request updated selection info here
            pass
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.blender_connection.is_connected():
            self.blender_connection.disconnect_from_blender()
        
        try:
            self.library_manager.save_library()
        except Exception as e:
            logger.error(f"Failed to save library on exit: {e}")
        
        event.accept()


def main():
    """Main application entry point"""
    print("🎬 Starting Animation Library - Modular Studio Layout...")
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Animation Library Professional")
    app.setApplicationVersion("2.1")
    app.setOrganizationName("Animation Studio")
    
    # Create and show main window
    window = AnimationLibraryMainWindow()
    window.show()
    
    # Center window on screen
    screen = app.primaryScreen().geometry()
    window_geo = window.geometry()
    x = (screen.width() - window_geo.width()) // 2
    y = (screen.height() - window_geo.height()) // 2
    window.move(x, y)
    
    print("✅ Modular Animation Library started successfully!")
    
    # Run application
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        app.quit()


if __name__ == "__main__":
    main()