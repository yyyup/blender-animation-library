#!/usr/bin/env python3
"""
Animation Library Qt GUI - Main Application
Clean, modular Studio Library interface with folder structure
"""

import sys
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

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
    """Main window with modular Studio Library layout and folder structure"""
    
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
        
        # NEW: Drag state tracking to prevent refreshes during drag operations
        self.drag_in_progress = False
        
        self.setup_ui()
        self.setup_connections()
        self.load_library()
        
        print("🎨 Modular Studio Library interface with folder structure initialized!")
        
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
        
        # Connection status with Studio Library colors
        self.connection_status = QLabel("Disconnected")
        self.connection_status.setStyleSheet("color: #ff6b6b; font-weight: bold; padding: 4px;")
        self.status_bar.addPermanentWidget(self.connection_status)
        
        # Show ready message
        self.status_bar.showMessage("Animation Library ready - Studio Library Layout", 3000)
        
        # Status bar styling - Studio Library specification
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #4a4a4a;
                border-top: 1px solid #555;
                color: #cccccc;
                font-size: 11px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
    
    def setup_connections(self):
        """Setup signal connections - CORRECTED VERSION"""
        # Get widgets from layout manager
        toolbar = self.layout_manager.get_widget('toolbar')
        folder_tree = self.layout_manager.get_widget('folder_tree')
        animation_grid = self.layout_manager.get_widget('animation_grid')
        metadata_panel = self.layout_manager.get_widget('metadata_panel')
        
        # Blender connection signals (ADDED: file release signal)
        self.blender_connection.connected.connect(self.on_blender_connected)
        self.blender_connection.disconnected.connect(self.on_blender_disconnected)
        self.blender_connection.connection_error.connect(self.on_connection_error)
        self.blender_connection.file_release_requested.connect(self.on_file_release_requested)  # NEW
        
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
        
        # Folder tree signals (FIXED: Only connect to signals that actually exist)
        folder_tree.folder_selected.connect(self.on_folder_selected)
        folder_tree.folder_created.connect(self.on_folder_created)
        folder_tree.folder_deleted.connect(self.on_folder_deleted)
        # REMOVED: folder_tree.folder_renamed.connect(self.on_folder_renamed)  # This signal doesn't exist!
        
        # Animation grid signals (FIXED: Only connect to signals that actually exist)
        animation_grid.animation_selected.connect(self.on_animation_selected)
        # REMOVED: animation_grid.context_menu_requested.connect(self.on_animation_context_menu)  # This signal doesn't exist!
        animation_grid.drag_in_progress.connect(self.on_drag_state_changed)
        
        # Metadata panel signals
        metadata_panel.preview_update_requested.connect(self.on_preview_update_requested)
        
        logger.info("✅ All signals connected (file release handler added)")

    # ADD this new method anywhere in your AnimationLibraryMainWindow class
    def on_file_release_requested(self, animation_id: str, force_release: bool):
        """Handle file release request from Blender - NEW HANDLER"""
        try:
            logger.info(f"🔓 MAIN: Received file release request for: {animation_id} (force: {force_release})")
            print(f"🔓 MAIN: Processing file release request for: {animation_id}")
            
            # Release video files in metadata panel
            metadata_panel = self.layout_manager.get_widget('metadata_panel')
            if metadata_panel:
                print(f"🔓 MAIN: Releasing video in metadata panel")
                metadata_panel.release_video_file()
            
            # Release video files in all animation cards
            animation_grid = self.layout_manager.get_widget('animation_grid')
            if animation_grid:
                print(f"🔓 MAIN: Releasing videos in all animation cards")
                animation_grid.release_all_video_files()
            
            # Force garbage collection to ensure file handles are released
            import gc
            gc.collect()
            
            print(f"✅ MAIN: File release completed for: {animation_id}")
            logger.info(f"✅ File release completed for: {animation_id}")
            
        except Exception as e:
            logger.error(f"❌ Error releasing files: {e}")
            print(f"❌ MAIN: Error releasing files: {e}")
    
    def get_application_style(self) -> str:
        """Get the Studio Library application stylesheet"""
        return """
            /* Main application window - Studio Library colors */
            QMainWindow {
                background-color: #2e2e2e;
                color: #eeeeee;
            }
            
            /* Base widget styling */
            QWidget {
                background-color: #2e2e2e;
                color: #eeeeee;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 11px;
            }
            
            /* Group boxes for panels */
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
                color: #eeeeee;
                background-color: #393939;
            }
            
            /* Primary buttons - Studio Library blue */
            #primaryButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            
            #primaryButton:hover {
                background-color: #357abd;
            }
            
            /* Secondary buttons */
            #secondaryButton {
                background-color: #666;
                color: white;
                border: 1px solid #777;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
                font-family: "Segoe UI", Arial, sans-serif;
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
            
            /* Checkboxes */
            QCheckBox {
                color: #eeeeee;
                spacing: 8px;
                font-size: 11px;
                font-family: "Segoe UI", Arial, sans-serif;
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
            
            /* Spin boxes */
            QSpinBox {
                background-color: #4a4a4a;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 8px;
                color: #eeeeee;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            
            /* Tab widgets */
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2e2e2e;
            }
            
            QTabBar::tab {
                background-color: #4a4a4a;
                color: #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 4px 4px 0px 0px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            
            QTabBar::tab:selected {
                background-color: #4a90e2;
                color: white;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #5a5a5a;
                color: #eeeeee;
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
            
            bone_preview = ', '.join(bones[:2])
            bone_suffix = '...' if len(bones) > 2 else ''
            selected_bones_info.setText(
                f"Selected: {len(bones)} bones ({bone_preview}{bone_suffix})"
            )
            selected_bones_info.setStyleSheet(
                "font-size: 9px; color: #51cf66; padding: 2px 8px;"
            )
        else:
            bones_label.setText("No bones selected")
            selected_bones_info.setText("No bones selected")
            selected_bones_info.setStyleSheet("font-size: 9px; color: #888; padding: 2px 8px;")
        
        frame_label.setText(f"Frame: {frame}")
    
    def on_animation_extracted(self, animation_data: dict):
        """Handle animation extraction from Blender"""
        try:
            metadata = AnimationMetadata.from_blender_data(animation_data)
            
            # Add to library (default to Root folder)
            success = self.library_manager.add_animation(metadata, "Root")
            
            if success:
                # Update folder count immediately
                folder_tree = self.layout_manager.get_widget('folder_tree')
                folder_tree.increment_folder_count("Root", 1)
                
                # Refresh displays
                self.refresh_library_display()
                self.update_tag_filter()
                
                self.status_bar.showMessage(f"Animation '{animation_data['action_name']}' extracted successfully", 3000)
                print(f"✅ Added new animation '{animation_data['action_name']}' to Root folder")
            else:
                QMessageBox.warning(
                    self, "Add Animation Failed",
                    f"Failed to add animation '{animation_data['action_name']}'"
                )
                print(f"❌ Failed to add animation '{animation_data['action_name']}'")
            
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
        """Handle folder selection from tree"""
        print(f"📁 Folder filter applied: {filter_str}")
        print(f"📁 Previous filter was: {getattr(self, 'current_filter', 'none')}")
        
        # PRESERVE current animation selection
        current_animation = getattr(self, 'current_animation', None)
        if current_animation:
            print(f"🔍 DEBUG: Preserving animation selection: {current_animation.name}")
        
        # Set the new filter
        self.current_filter = filter_str
        
        # CRITICAL FIX: Uncomment refresh to apply folder filtering
        print(f"🔄 Refreshing library display to apply folder filter: {filter_str}")
        self.refresh_library_display()
        
        # RESTORE animation selection after folder change
        if current_animation:
            self.current_animation = current_animation
            metadata_panel = self.layout_manager.get_widget('metadata_panel')
            if metadata_panel:
                metadata_panel.show_animation_details(current_animation)
                print(f"✅ DEBUG: Restored animation details for: {current_animation.name}")
        
        # Update status with detailed debug info
        if filter_str == "all":
            print(f"📁 DEBUG: Showing all animations")
            self.status_bar.showMessage("Showing all animations", 2000)
        elif filter_str.startswith("rig_type:"):
            rig_type = filter_str.split(":", 1)[1]
            print(f"📁 DEBUG: Filtering by rig type: {rig_type}")
            self.status_bar.showMessage(f"Filtered by rig type: {rig_type}", 2000)
        elif filter_str.startswith("storage:"):
            storage_type = filter_str.split(":", 1)[1]
            storage_name = "Instant .blend files" if storage_type == "blend_file" else "Legacy JSON files"
            print(f"📁 DEBUG: Filtering by storage: {storage_name}")
            self.status_bar.showMessage(f"Filtered by storage: {storage_name}", 2000)
        elif filter_str.startswith("category:"):
            category = filter_str.split(":", 1)[1]
            print(f"📁 DEBUG: Filtering by category: {category}")
            self.status_bar.showMessage(f"Filtered by category: {category.title()}", 2000)
        elif filter_str.startswith("folder:"):
            folder_name = filter_str.split(":", 1)[1]
            print(f"📁 DEBUG: Filtering by folder: '{folder_name}'")
            print(f"📁 DEBUG: Current filter now set to: {self.current_filter}")
            self.status_bar.showMessage(f"Showing folder: {folder_name}", 2000)
        else:
            print(f"📁 DEBUG: Unknown filter type: {filter_str}")
            
        print(f"📁 DEBUG: Folder selection complete, filter applied: {self.current_filter}")
    
    def on_animation_selected(self, animation_data: dict):
        """Handle animation selection from cards"""
        
        # DEBUG: Print the raw animation data
        print(f"🎬 MAIN: Animation selected with data keys: {list(animation_data.keys())}")
        
        # Check what ID fields are available
        id_fields = ['id', 'animation_id', 'name']
        for field in id_fields:
            if field in animation_data:
                print(f"🎬 MAIN: {field}: '{animation_data[field]}'")
        
        print(f"📨 DEBUG: on_animation_selected called with: {animation_data.get('name', 'Unknown')}")
        
        try:
            animation_id = animation_data.get('id')
            print(f"📨 DEBUG: Animation ID: {animation_id}")
            
            metadata_panel = self.layout_manager.get_widget('metadata_panel')
            print(f"📨 DEBUG: Metadata panel: {metadata_panel}")
            
            if animation_id:
                animation = self.library_manager.get_animation(animation_id)
                print(f"📨 DEBUG: Found animation: {animation}")
                
                if animation:
                    self.current_animation = animation
                    metadata_panel.show_animation_details(animation)
                    print(f"🎬 DEBUG: Called show_animation_details")
                    print(f"🎬 Animation selected: {animation.name}")
                else:
                    print("❌ DEBUG: Animation not found in library")
                    metadata_panel.show_no_selection()
            else:
                print("❌ DEBUG: No animation ID provided")
                metadata_panel.show_no_selection()
                
        except Exception as e:
            print(f"❌ DEBUG: Error in on_animation_selected: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Error showing animation details: {e}")
    
    def on_preview_update_requested(self, animation_identifier: str, folder_path: str):
        """Handle preview update request from metadata panel - FIXED VERSION"""
        try:
            print(f"📨 DEBUG: Received preview update request for: '{animation_identifier}' in folder: '{folder_path}'")
            print(f"🔗 DEBUG: Connection status: {self.blender_connection.is_connected()}")
            
            if not self.blender_connection.is_connected():
                print("❌ DEBUG: Not connected to Blender")
                QMessageBox.warning(
                    self, "Not Connected", 
                    "Please connect to Blender first to update previews"
                )
                return
            
            # CRITICAL FIX: Don't override the animation_identifier!
            # Use the FULL animation identifier that was sent from metadata panel
            animation_name = animation_identifier  # Keep the full ID as-is
            
            print(f"📤 DEBUG: Using animation name: '{animation_name}' (not overridden)")
            
            # Send the update request to Blender with folder path
            success = self.blender_connection.send_update_preview(animation_name, folder_path)
            print(f"📤 DEBUG: Send result: {success}")
            
            if success:
                message = f"Preview update requested for: {animation_name}"
                self.status_bar.showMessage(message, 3000)
                logger.info(message)
            else:
                error_msg = f"Failed to send preview update request for: {animation_name}"
                QMessageBox.warning(self, "Update Failed", error_msg)
                logger.error(error_msg)
                
        except Exception as e:
            error_msg = f"Error requesting preview update: {e}"
            logger.error(error_msg)
            QMessageBox.critical(self, "Error", f"Error requesting preview update: {str(e)}")
    
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
    
    def on_drag_state_changed(self, is_dragging):
        """Handle drag state changes to prevent UI refreshes during drag operations"""
        self.drag_in_progress = is_dragging
        if is_dragging:
            print("🎯 Drag started - preventing library refreshes")
        else:
            print("✅ Drag finished - refreshing library display")
            # Refresh the display now that dragging is complete
            self.refresh_library_display()

    def on_animation_moved(self, animation_id, target_folder):
        """Handle animation moved to folder via drag & drop"""
        try:
            print(f"🎬 BEFORE MOVE - Animation {animation_id} to folder '{target_folder}'")
            
            # Get animation to see current folder
            animation = self.library_manager.get_animation(animation_id)
            source_folder = "Root"  # Default
            if animation:
                source_folder = getattr(animation, 'folder_path', 'Root')
                print(f"🎬 Current folder: '{source_folder}' → Target folder: '{target_folder}'")
            
            # Update folder counts immediately (optimistic UI update)
            folder_tree = self.layout_manager.get_widget('folder_tree')
            if source_folder != target_folder:
                # Decrement source folder count
                if source_folder != "Root":
                    folder_tree.increment_folder_count(source_folder, -1)
                # Increment target folder count
                folder_tree.increment_folder_count(target_folder, 1)
                # Update root count based on whether we're moving to/from root
                if source_folder == "Root" and target_folder != "Root":
                    folder_tree.increment_folder_count("Root", -1)
                elif source_folder != "Root" and target_folder == "Root":
                    folder_tree.increment_folder_count("Root", 1)
            
            # Move animation in library
            success = self.library_manager.move_animation_to_folder(animation_id, target_folder)
            
            if success:
                # Get animation name for status message
                animation = self.library_manager.get_animation(animation_id)
                animation_name = animation.name if animation else "Animation"
                new_folder = getattr(animation, 'folder_path', 'Root') if animation else 'Unknown'
                
                print(f"🎬 AFTER MOVE - Animation {animation_name} now in folder: '{new_folder}'")
                
                # CRITICAL FIX: Replace refresh_library_display() with targeted updates to prevent cards from disappearing
                
                # 1. Update folder tree counts only (already done above with optimistic updates)
                self.update_folder_tree_counts_only()
                
                # 2. Check if the moved animation should still be visible in current filter
                current_filter = getattr(self, 'current_filter', 'all')
                should_remain_visible = True
                
                if current_filter == "all":
                    # Animation should remain visible in "all" view
                    should_remain_visible = True
                elif current_filter.startswith("folder:"):
                    # Animation should only remain visible if it's still in the filtered folder
                    filter_folder = current_filter.split(":", 1)[1]
                    should_remain_visible = (target_folder == filter_folder)
                else:
                    # For other filters (rig_type, storage, etc.), animation should still be visible
                    should_remain_visible = True
                
                # 3. Remove card from grid only if it should no longer be visible in current filter
                if not should_remain_visible:
                    animation_grid = self.layout_manager.get_widget('animation_grid')
                    if animation_grid and hasattr(animation_grid, 'safe_delete_animation_card'):
                        card_removed = animation_grid.safe_delete_animation_card(animation_id)
                        if card_removed:
                            print(f"🎬 MOVE: Removed card from current view (moved to different folder)")
                        else:
                            print(f"🎬 MOVE: Card not found in current view or already removed")
                    else:
                        print(f"🎬 MOVE: Animation grid doesn't support safe card removal")
                else:
                    print(f"🎬 MOVE: Card remains visible in current view")
                
                # 4. NO full grid refresh - keeping all other cards visible
                
                # Show success message
                self.status_bar.showMessage(f"Moved '{animation_name}' to folder '{target_folder}'", 3000)
                print(f"📁 SUCCESS: Moved {animation_name} to {target_folder}")
            else:
                print(f"❌ FAILED: Could not move animation to folder '{target_folder}'")
                # Revert the optimistic UI updates
                if source_folder != target_folder:
                    # Revert source folder count
                    if source_folder != "Root":
                        folder_tree.increment_folder_count(source_folder, 1)
                    # Revert target folder count  
                    folder_tree.increment_folder_count(target_folder, -1)
                    # Revert root count
                    if source_folder == "Root" and target_folder != "Root":
                        folder_tree.increment_folder_count("Root", 1)
                    elif source_folder != "Root" and target_folder == "Root":
                        folder_tree.increment_folder_count("Root", -1)
                QMessageBox.warning(self, "Move Failed", f"Failed to move animation to folder '{target_folder}'")
                
        except Exception as e:
            logger.error(f"Failed to move animation {animation_id}: {e}")
            QMessageBox.warning(self, "Move Error", f"Error moving animation:\n{str(e)}")
    
    def on_folder_created(self, folder_name: str):
        """Handle new folder creation from tree widget"""
        try:
            print(f"📁 Creating folder: {folder_name}")
            
            # Check if folder already exists
            folder_stats = self.library_manager.get_folder_statistics()
            if folder_name in folder_stats:
                QMessageBox.warning(self, "Folder Exists", f"A folder named '{folder_name}' already exists.")
                return
            
            # Create folder in library manager
            success = self.library_manager.create_folder(folder_name)
            
            if success:
                # Update folder tree display
                self.update_folder_tree()
                
                # Show success message
                self.status_bar.showMessage(f"Created folder '{folder_name}'", 3000)
                print(f"✅ Folder created successfully: {folder_name}")
            else:
                QMessageBox.warning(self, "Folder Creation Failed", f"Failed to create folder '{folder_name}'")
                
        except Exception as e:
            logger.error(f"Failed to create folder {folder_name}: {e}")
            QMessageBox.warning(self, "Folder Creation Error", f"Error creating folder:\n{str(e)}")
    
    def on_folder_deleted(self, folder_name: str):
        """Handle folder deletion from tree widget"""
        try:
            print(f"🗑️ Main window: Deleting folder: {folder_name}")
            
            # Delete folder through library manager (this will move animations to Root)
            success = self.library_manager.delete_folder(folder_name)
            
            if success:
                print(f"✅ Main window: Folder deletion successful")
                
                # If we're currently viewing the deleted folder, switch to "All"
                if self.current_filter == f"folder:{folder_name}":
                    print(f"🔄 Switching from deleted folder view to 'All Animations'")
                    self.current_filter = "all"
                
                # Update folder tree display (reload structure from library)
                self.update_folder_tree()
                
                # Refresh animation display 
                self.refresh_library_display()
                
                # Show success message
                self.status_bar.showMessage(f"Deleted folder '{folder_name}' and moved animations to Root", 3000)
                print(f"✅ Main window: Folder deleted successfully: {folder_name}")
            else:
                print(f"❌ Main window: Folder deletion failed")
                QMessageBox.warning(self, "Folder Deletion Failed", f"Failed to delete folder '{folder_name}'")
                
        except Exception as e:
            print(f"❌ Main window: Exception during folder deletion: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Failed to delete folder {folder_name}: {e}")
            QMessageBox.warning(self, "Folder Deletion Error", f"Error deleting folder:\n{str(e)}")
    
    def move_animation_to_folder(self, animation_data: dict, target_folder: str):
        """Move animation to folder via context menu with targeted updates"""
        animation_id = animation_data.get('id')
        if not animation_id:
            return
            
        try:
            print(f"🎬 CONTEXT MOVE: Moving animation {animation_id} to folder '{target_folder}'")
            
            # Get current animation to check source folder
            animation = self.library_manager.get_animation(animation_id)
            source_folder = "Root"
            if animation:
                source_folder = getattr(animation, 'folder_path', 'Root')
                print(f"🎬 CONTEXT MOVE: Current folder: '{source_folder}' → Target folder: '{target_folder}'")
            
            # Check if we need to create the folder first
            folder_stats = self.library_manager.get_folder_statistics()
            if target_folder not in folder_stats and target_folder != "Root":
                # Create the folder
                success = self.library_manager.create_folder(target_folder)
                if not success:
                    QMessageBox.warning(self, "Folder Creation Failed", f"Failed to create folder '{target_folder}'")
                    return
            
            # Move the animation in library
            success = self.library_manager.move_animation_to_folder(animation_id, target_folder)
            
            if success:
                # Get animation name for status message
                animation_name = animation.name if animation else "Animation"
                
                print(f"🎬 CONTEXT MOVE: Animation {animation_name} moved to folder: '{target_folder}'")
                
                # CRITICAL FIX: Use targeted updates instead of refresh_library_display()
                
                # 1. Update folder counts in folder tree
                folder_tree = self.layout_manager.get_widget('folder_tree')
                if folder_tree and source_folder != target_folder:
                    # Decrement source folder count
                    if source_folder != "Root":
                        folder_tree.increment_folder_count(source_folder, -1)
                    # Increment target folder count
                    folder_tree.increment_folder_count(target_folder, 1)
                    
                    # Update root count based on whether we're moving to/from root
                    if source_folder == "Root" and target_folder != "Root":
                        folder_tree.increment_folder_count("Root", -1)
                    elif source_folder != "Root" and target_folder == "Root":
                        folder_tree.increment_folder_count("Root", 1)
                
                # 2. Update folder tree counts
                self.update_folder_tree_counts_only()
                
                # 3. Check if animation should still be visible in current filter
                current_filter = getattr(self, 'current_filter', 'all')
                should_remain_visible = True
                
                if current_filter == "all":
                    should_remain_visible = True
                elif current_filter.startswith("folder:"):
                    filter_folder = current_filter.split(":", 1)[1]
                    should_remain_visible = (target_folder == filter_folder)
                else:
                    # For other filters (rig_type, storage, etc.), animation should still be visible
                    should_remain_visible = True
                
                # 4. Remove card only if it should no longer be visible in current filter
                if not should_remain_visible:
                    animation_grid = self.layout_manager.get_widget('animation_grid')
                    if animation_grid and hasattr(animation_grid, 'safe_delete_animation_card'):
                        card_removed = animation_grid.safe_delete_animation_card(animation_id)
                        if card_removed:
                            print(f"🎬 CONTEXT MOVE: Removed card from current view (moved to different folder)")
                    else:
                        print(f"🎬 CONTEXT MOVE: Animation grid doesn't support safe card removal")
                else:
                    print(f"🎬 CONTEXT MOVE: Card remains visible in current view")
                
                # 5. Show success message
                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage(f"Moved '{animation_name}' to folder '{target_folder}'", 3000)
                print(f"✅ CONTEXT MOVE: Successfully moved {animation_name} to {target_folder}")
                
            else:
                print(f"❌ CONTEXT MOVE: Failed to move animation to folder '{target_folder}'")
                QMessageBox.warning(self, "Move Failed", f"Failed to move animation to folder '{target_folder}'")
                
        except Exception as e:
            logger.error(f"Failed to move animation {animation_id}: {e}")
            QMessageBox.warning(self, "Move Error", f"Error moving animation:\n{str(e)}")
    
    def delete_animation(self, animation_data: dict):
        """Delete animation from library with proper UI cleanup"""
        reply = QMessageBox.question(
            self, "Delete Animation",
            f"Are you sure you want to delete '{animation_data['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            animation_id = animation_data['id']
            animation_grid = self.layout_manager.get_widget('animation_grid')
            
            print(f"🗑️ Starting deletion of animation: {animation_data['name']} (ID: {animation_id})")
            
            # Get the animation's current folder for count update
            animation = self.library_manager.get_animation(animation_id)
            source_folder = "Root"
            if animation:
                source_folder = getattr(animation, 'folder_path', 'Root')
            
            # Step 1: Remove the card from UI immediately for better UX
            card_removed = animation_grid.safe_delete_animation_card(animation_id)
            if card_removed:
                print(f"✅ Animation card removed from UI")
            
            # Step 2: Remove animation from library backend
            success = self.library_manager.remove_animation(animation_id)
            
            if success:
                # Update folder count immediately
                folder_tree = self.layout_manager.get_widget('folder_tree')
                folder_tree.increment_folder_count(source_folder, -1)
                
                # Update other UI components without full refresh if card was already removed
                if not card_removed:
                    # If individual card removal failed, do full refresh
                    print("⚠️ Card removal failed, doing full refresh")
                    self.refresh_library_display()
                else:
                    # Just update counts and filters since card is already gone
                    self.update_statistics()
                    self.update_tag_filter()
                
                # Clear metadata panel
                metadata_panel = self.layout_manager.get_widget('metadata_panel')
                metadata_panel.show_no_selection()
                
                # Force cleanup of any remaining orphaned widgets
                animation_grid.force_layout_cleanup()
                
                self.status_bar.showMessage(f"Deleted animation '{animation_data['name']}'", 3000)
                print(f"✅ Successfully deleted animation '{animation_data['name']}' from folder '{source_folder}'")
            else:
                QMessageBox.warning(self, "Delete Failed", f"Failed to delete animation '{animation_data['name']}'")
                print(f"❌ Failed to delete animation '{animation_data['name']}''")
            
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
            self.update_folder_tree()
            
            count = len(self.library_manager.get_all_animations())
            self.status_bar.showMessage(f"Loaded {count} animations from library", 3000)
            print(f"📚 Loaded {count} animations from library")
            
        except Exception as e:
            logger.error(f"Failed to load library: {e}")
            QMessageBox.warning(self, "Load Error", f"Failed to load animation library:\n{str(e)}")
    
    def update_folder_tree(self):
        """Update the folder tree with current library structure"""
        folder_tree = self.layout_manager.get_widget('folder_tree')
        
        # Get folder structure from library manager
        folder_structure = self.library_manager.get_folder_structure()
        print(f"🔄 Main window: Updating folder tree with structure: {list(folder_structure.keys())}")
        
        # Update folder structure and refresh tree
        folder_tree.update_folder_structure(folder_structure)
        
        # Update folder counts
        folder_stats = self.library_manager.get_folder_statistics()
        folder_tree.update_folder_counts_only(folder_stats)
    
    def refresh_library_display(self):
        """Refresh the animation library display with proper cleanup"""
        # CRITICAL: Don't refresh during drag operations to prevent cards from disappearing
        if self.drag_in_progress:
            print("⏸️ SKIPPING refresh - drag operation in progress")
            return
            
        print("🔄 Starting library display refresh...")
        
        animations = self.get_filtered_animations()
        animation_grid = self.layout_manager.get_widget('animation_grid')
        
        # Check if we have a large dataset and enable performance mode
        is_large_dataset = len(animations) > 200
        if is_large_dataset:
            print(f"📊 Large dataset detected ({len(animations)} animations) - enabling performance mode")
            animation_grid.update_grid_performance_mode(large_dataset=True)
        
        # Step 1: Clear all existing cards with proper memory cleanup
        print(f"🧹 Clearing existing cards before adding {len(animations)} new ones")
        animation_grid.clear_cards()
        
        # Step 2: Force Qt to process pending deletions
        QApplication.processEvents()
        
        # Step 3: Create new animation cards (but don't add them one by one)
        new_cards = []
        cards_created = 0
        
        for animation_data in animations:
            try:
                card = AnimationCard(animation_data.to_dict())
                
                # Connect signals
                card.apply_requested.connect(self.apply_animation)
                card.preview_requested.connect(self.preview_animation)
                card.edit_requested.connect(self.edit_animation)
                card.delete_requested.connect(self.delete_animation)
                card.move_to_folder_requested.connect(self.move_animation_to_folder)
                
                new_cards.append(card)
                cards_created += 1
                
            except Exception as e:
                print(f"⚠️ Failed to create card for animation {animation_data.name}: {e}")
                continue
        
        # Step 4: Add all cards at once for better performance
        if new_cards:
            if is_large_dataset:
                # Use bulk add for large datasets
                animation_grid.bulk_add_cards(new_cards)
            else:
                # Use regular add for smaller datasets
                for card in new_cards:
                    animation_grid.add_card(card)
        
        # Step 5: Re-enable updates if we disabled them
        if is_large_dataset:
            animation_grid.update_grid_performance_mode(large_dataset=False)
        
        # Step 6: Update other UI components
        self.update_statistics()
        self.update_folder_tree()
        
        print(f"✅ Library display refreshed: {cards_created}/{len(animations)} cards created successfully")
        
        # Step 7: Final cleanup and validation
        if cards_created != len(animations):
            print(f"⚠️ Warning: Created {cards_created} cards but expected {len(animations)}")
            
        # Force cleanup of any orphaned widgets
        animation_grid.force_layout_cleanup()
        
        # Final memory cleanup
        QApplication.processEvents()
        self.update_folder_tree()
        print(f"🔄 Refreshed display: {len(animations)} animations shown")
    
    def get_filtered_animations(self) -> list:
        """Get animations filtered by current criteria"""
        all_animations = self.library_manager.get_all_animations()
        toolbar = self.layout_manager.get_widget('toolbar')
        
        # Debug: Show all animation folder paths
        print(f"🔍 All animations and their folders:")
        for anim in all_animations:
            folder_path = getattr(anim, 'folder_path', 'Root')
            print(f"   - {anim.name}: folder_path = '{folder_path}'")
        
        # Apply folder filter
        if self.current_filter != "all":
            if self.current_filter.startswith("rig_type:"):
                rig_type = self.current_filter.split(":", 1)[1]
                all_animations = [anim for anim in all_animations if anim.rig_type == rig_type]
            elif self.current_filter.startswith("storage:"):
                storage_method = self.current_filter.split(":", 1)[1]
                all_animations = [anim for anim in all_animations if anim.storage_method == storage_method]
            elif self.current_filter.startswith("category:"):
                category = self.current_filter.split(":", 1)[1]
                all_animations = [anim for anim in all_animations 
                                if any(category in tag.lower() for tag in anim.tags)]
            elif self.current_filter.startswith("folder:"):
                folder_name = self.current_filter.split(":", 1)[1]
                print(f"🔍 FILTERING: Applying folder filter for: '{folder_name}'")
                print(f"🔍 FILTERING: Total animations before filter: {len(all_animations)}")
                
                # Filter animations by exact folder path match (flat folders only)
                filtered_animations = []
                for anim in all_animations:
                    anim_folder = getattr(anim, 'folder_path', 'Root')
                    matches_folder = anim_folder == folder_name
                    print(f"   - Checking {anim.name}: folder='{anim_folder}' matches '{folder_name}' ? {matches_folder}")
                    if matches_folder:
                        filtered_animations.append(anim)
                        print(f"     ✅ INCLUDED: {anim.name}")
                    else:
                        print(f"     ❌ EXCLUDED: {anim.name}")
                
                all_animations = filtered_animations
                print(f"🔍 FILTERING: Found {len(all_animations)} animations in flat folder '{folder_name}'")
        
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
    
    def update_folder_tree_counts_only(self):
        """Update only the folder counts without rebuilding the tree structure"""
        folder_tree = self.layout_manager.get_widget('folder_tree')
        
        # Get folder statistics from library manager
        folder_stats = self.library_manager.get_folder_statistics()
        
        # Use the efficient count update method
        folder_tree.update_folder_counts_only(folder_stats)
        print(f"📊 Updated folder counts: {folder_stats}")
    
    def on_preview_updated(self, animation_name: str):
        """Handle preview updated confirmation from Blender with AGGRESSIVE refresh"""
        # Simple debounce - ignore if same animation was just updated
        if hasattr(self, '_last_preview_update'):
            if (self._last_preview_update[0] == animation_name and 
                time.time() - self._last_preview_update[1] < 1.0):  # 1 second debounce
                return
        
        self._last_preview_update = (animation_name, time.time())
        
        try:
            print(f"🔄 MAIN: Received preview update for: {animation_name}")
            
            # STEP 1: Refresh animation grid cards
            animation_grid = self.layout_manager.get_widget('animation_grid')
            if animation_grid:
                print(f"🎬 MAIN: Refreshing animation grid...")
                animation_grid.refresh_preview(animation_name)
            
            # STEP 2: Refresh metadata panel if it's showing this animation
            metadata_panel = self.layout_manager.get_widget('metadata_panel')
            if metadata_panel and metadata_panel.current_animation:
                if animation_name == metadata_panel.current_animation.name:
                    print(f"🖼️ MAIN: Refreshing metadata panel...")
                    metadata_panel.refresh_preview(animation_name)
            
            # STEP 3: Force application-wide refresh
            print(f"🔄 MAIN: Forcing application refresh...")
            QApplication.processEvents()
            
            # STEP 4: Delayed additional refresh
            QTimer.singleShot(300, lambda: [
                QApplication.processEvents(),
                print(f"✅ MAIN: Delayed refresh completed for: {animation_name}")
            ])
            
            logger.info(f"✅ Preview refreshed across all components for: {animation_name}")
            
        except Exception as e:
            logger.error(f"❌ Error handling preview update: {e}")
            import traceback
            traceback.print_exc()

    # ==================================================
    # MAYA-STYLE ENHANCEMENT SIGNAL HANDLERS
    # ==================================================
    
    def on_multi_folder_selected(self, folder_names: List[str]):
        """Handle multiple folder selection for Maya-style batch operations"""
        print(f"📁 Multi-folder selection: {len(folder_names)} folders selected")
        print(f"📁 Selected folders: {', '.join(folder_names)}")
        
        # Update status bar with multi-selection info
        if len(folder_names) > 1:
            self.status_bar.showMessage(f"Selected {len(folder_names)} folders for batch operations", 3000)
        
        # Could update UI to show batch operation options
        # For example, enable batch rename, merge, export options
    
    def on_folder_auto_expanded(self, folder_name: str):
        """Handle auto-expansion of folders during drag operations"""
        print(f"📁 Auto-expanded folder: {folder_name}")
        
        # Could track auto-expanded folders for cleanup after drag operations
        # Or provide user feedback about the expansion
    
    def on_batch_move_started(self, folder_names: List[str], target_folder: str):
        """Handle start of batch folder move operations"""
        print(f"📁 Batch move started: {len(folder_names)} folders")
        print(f"📁 Source folders: {', '.join(folder_names)}")
        print(f"📁 Target folder: {target_folder}")
        
        # Show progress indicator for large batch operations
        if len(folder_names) > 5:
            self.status_bar.showMessage(f"Moving {len(folder_names)} folders...", 5000)
        
        # Could implement actual batch move logic here
        # For now, just provide user feedback
    
    def on_folder_organization_changed(self, organization_rules: Dict[str, Any]):
        """Handle changes to folder organization structure"""
        print(f"📁 Folder organization changed with rules: {organization_rules}")
        
        # Update folder tree and refresh display
        self.update_folder_tree()
        self.refresh_library_display()
        
        # Show success message
        self.status_bar.showMessage("Folder organization updated", 3000)
    
    def on_folder_moved(self, source_folder: str, target_folder: str):
        """Handle folder reorganization from tree widget"""
        try:
            print(f"📁 Main window: Moving folder '{source_folder}' to '{target_folder}'")
            
            # Move folder through library manager
            success = self.library_manager.move_folder(source_folder, target_folder)
            
            if success:
                print(f"✅ Main window: Folder move successful")
                
                # Update folder tree display (reload structure from library)
                self.update_folder_tree()
                
                # Refresh animation display to reflect new organization
                self.refresh_library_display()
                
                # Show success message
                self.status_bar.showMessage(f"Moved folder '{source_folder}' to '{target_folder}'", 3000)
                print(f"✅ Main window: Folder moved successfully: '{source_folder}' → '{target_folder}'")
            else:
                print(f"❌ Main window: Folder move failed")
                QMessageBox.warning(self, "Folder Move Failed", f"Failed to move folder '{source_folder}' to '{target_folder}'")
                
        except Exception as e:
            logger.error(f"Failed to move folder {source_folder} to {target_folder}: {e}")
            QMessageBox.warning(self, "Folder Move Error", f"Error moving folder:\n{str(e)}")


def main():
    """Main entry point for the application"""
    import sys
    from PySide6.QtWidgets import QApplication
    
    # Create the application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = AnimationLibraryMainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()