#!/usr/bin/env python3
"""
Animation Library Qt GUI Application
Professional desktop interface for Blender animation library management
"""

import sys
import json
import socket
import threading
import time
import os
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QPushButton, QLineEdit, QComboBox, QListWidget, 
    QListWidgetItem, QTextEdit, QTreeWidget, QTreeWidgetItem, QGroupBox,
    QCheckBox, QSpinBox, QSplitter, QTabWidget, QScrollArea, QFrame,
    QMessageBox, QProgressBar, QStatusBar, QMenuBar, QMenu, QToolBar,
    QSlider, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import (
    Qt, QThread, QTimer, Signal, QSize, QPropertyAnimation, QEasingCurve
)
from PySide6.QtGui import (
    QPixmap, QIcon, QPalette, QColor, QFont, QPainter, QPen, QBrush
)

class BlenderConnection(QThread):
    """Handles socket communication with Blender in a separate thread"""
    
    # Signals for UI updates
    connected = Signal()
    disconnected = Signal()
    message_received = Signal(dict)
    connection_error = Signal(str)
    
    def __init__(self, host='127.0.0.1', port=8080):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.message_buffer = ""
        
    def connect_to_blender(self):
        """Connect to Blender and start listening"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.running = True
            self.connected.emit()
            self.start()  # Start the thread for listening
            return True
        except Exception as e:
            self.connection_error.emit(str(e))
            return False
    
    def run(self):
        """Main thread loop for listening to Blender"""
        while self.running and self.socket:
            try:
                data = self.socket.recv(4096)
                if data:
                    self.message_buffer += data.decode('utf-8')
                    self.process_messages()
                else:
                    self.running = False
                    self.disconnected.emit()
                    break
            except Exception as e:
                if self.running:
                    self.connection_error.emit(str(e))
                break
    
    def process_messages(self):
        """Process complete JSON messages from buffer"""
        print(f"DEBUG: Buffer length: {len(self.message_buffer)}")
        if self.message_buffer:
            print(f"DEBUG: Buffer start: {self.message_buffer[:100]}...")
            
        while "###END_MESSAGE###" in self.message_buffer:
            print("DEBUG: Found complete message delimiter!")
            message_end = self.message_buffer.find("###END_MESSAGE###")
            complete_message = self.message_buffer[:message_end].strip()
            self.message_buffer = self.message_buffer[message_end + len("###END_MESSAGE###"):].strip()
            
            if complete_message:
                print(f"DEBUG: Processing message type: {complete_message[:50]}...")
                try:
                    data = json.loads(complete_message)
                    print(f"DEBUG: Successfully parsed JSON, type: {data.get('type', 'unknown')}")
                    self.message_received.emit(data)
                except json.JSONDecodeError as e:
                    print(f"DEBUG: JSON decode error: {e}")
                    self.connection_error.emit(f"JSON Error: {e}")
            else:
                print("DEBUG: Empty message after stripping")
    
    def send_command(self, command_data):
        """Send command to Blender"""
        if self.socket and self.running:
            try:
                message = json.dumps(command_data)
                framed_message = message + "\n###END_MESSAGE###\n"
                self.socket.send(framed_message.encode('utf-8'))
                return True
            except Exception as e:
                self.connection_error.emit(f"Send error: {e}")
                return False
        return False
    
    def disconnect(self):
        """Disconnect from Blender"""
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None

class AnimationCard(QFrame):
    """Custom widget for displaying animation clips"""
    
    apply_requested = Signal(dict)
    
    def __init__(self, animation_data):
        super().__init__()
        self.animation_data = animation_data
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Box)
        self.setFixedSize(200, 280)
        self.setStyleSheet("""
            AnimationCard {
                border: 2px solid #555;
                border-radius: 8px;
                background-color: #2b2b2b;
            }
            AnimationCard:hover {
                border-color: #0078d4;
                background-color: #353535;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Thumbnail placeholder
        thumbnail = QLabel()
        thumbnail.setFixedSize(180, 120)
        thumbnail.setStyleSheet("""
            background-color: #1e1e1e;
            border: 1px solid #444;
            border-radius: 4px;
        """)
        thumbnail.setAlignment(Qt.AlignCenter)
        thumbnail.setText("🎬\nPreview")
        layout.addWidget(thumbnail)
        
        # Animation name
        name_label = QLabel(self.animation_data.get('name', 'Unknown'))
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        name_label.setWordWrap(True)
        name_label.setMaximumHeight(40)
        layout.addWidget(name_label)
        
        # Metadata
        duration = self.animation_data.get('duration_frames', 0)
        bones = self.animation_data.get('total_bones_animated', 0)
        keyframes = self.animation_data.get('total_keyframes', 0)
        
        meta_label = QLabel(f"{duration} frames • {bones} bones\n{keyframes} keyframes")
        meta_label.setStyleSheet("color: #aaa; font-size: 9px;")
        layout.addWidget(meta_label)
        
        # Tags
        tags = self.animation_data.get('tags', [])
        tag_text = ", ".join(tags[:3])  # Show first 3 tags
        if len(tags) > 3:
            tag_text += f" +{len(tags)-3}"
        
        tag_label = QLabel(tag_text)
        tag_label.setStyleSheet("""
            background-color: #0078d4;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 8px;
        """)
        tag_label.setMaximumHeight(20)
        layout.addWidget(tag_label)
        
        # Apply button
        apply_btn = QPushButton("Apply")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 6px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        apply_btn.clicked.connect(lambda: self.apply_requested.emit(self.animation_data))
        layout.addWidget(apply_btn)

class BoneMappingWidget(QWidget):
    """Widget for visual bone mapping"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.source_bones = []
        self.target_bones = []
        self.bone_mapping = {}
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Bone Mapping")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Mapping table
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(3)
        self.mapping_table.setHorizontalHeaderLabels(["Source Bone", "→", "Target Bone"])
        
        # Make columns resizable
        header = self.mapping_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.mapping_table.setColumnWidth(1, 30)
        
        layout.addWidget(self.mapping_table)
        
        # Auto-map button
        auto_map_btn = QPushButton("Auto-Map Similar Names")
        auto_map_btn.clicked.connect(self.auto_map_bones)
        layout.addWidget(auto_map_btn)
        
    def update_bones(self, source_bones, target_bones):
        """Update available bones for mapping"""
        self.source_bones = source_bones
        self.target_bones = target_bones
        self.refresh_mapping_table()
        
    def refresh_mapping_table(self):
        """Refresh the mapping table display"""
        self.mapping_table.setRowCount(len(self.source_bones))
        
        for i, source_bone in enumerate(self.source_bones):
            # Source bone (read-only)
            source_item = QTableWidgetItem(source_bone)
            source_item.setFlags(source_item.flags() & ~Qt.ItemIsEditable)
            self.mapping_table.setItem(i, 0, source_item)
            
            # Arrow (read-only)
            arrow_item = QTableWidgetItem("→")
            arrow_item.setFlags(arrow_item.flags() & ~Qt.ItemIsEditable)
            arrow_item.setTextAlignment(Qt.AlignCenter)
            self.mapping_table.setItem(i, 1, arrow_item)
            
            # Target bone (combo box)
            target_combo = QComboBox()
            target_combo.addItem("")  # Empty option
            target_combo.addItems(self.target_bones)
            
            # Set existing mapping if available
            if source_bone in self.bone_mapping:
                target_bone = self.bone_mapping[source_bone]
                if target_bone in self.target_bones:
                    target_combo.setCurrentText(target_bone)
            
            # Connect change signal
            target_combo.currentTextChanged.connect(
                lambda text, src=source_bone: self.update_mapping(src, text)
            )
            
            self.mapping_table.setCellWidget(i, 2, target_combo)
    
    def update_mapping(self, source_bone, target_bone):
        """Update bone mapping when user changes selection"""
        if target_bone:
            self.bone_mapping[source_bone] = target_bone
        elif source_bone in self.bone_mapping:
            del self.bone_mapping[source_bone]
    
    def auto_map_bones(self):
        """Automatically map bones with similar names"""
        for source_bone in self.source_bones:
            best_match = None
            best_score = 0
            
            for target_bone in self.target_bones:
                # Simple similarity scoring
                score = self.calculate_similarity(source_bone, target_bone)
                if score > best_score and score > 0.6:  # Threshold for auto-mapping
                    best_score = score
                    best_match = target_bone
            
            if best_match:
                self.bone_mapping[source_bone] = best_match
        
        self.refresh_mapping_table()
    
    def calculate_similarity(self, bone1, bone2):
        """Calculate similarity between bone names"""
        bone1 = bone1.lower()
        bone2 = bone2.lower()
        
        # Exact match
        if bone1 == bone2:
            return 1.0
        
        # Remove common prefixes/suffixes
        for prefix in ['def_', 'mch_', 'org_']:
            if bone1.startswith(prefix):
                bone1 = bone1[len(prefix):]
            if bone2.startswith(prefix):
                bone2 = bone2[len(prefix):]
        
        # Check if one contains the other
        if bone1 in bone2 or bone2 in bone1:
            return 0.8
        
        # Simple character overlap
        common_chars = set(bone1) & set(bone2)
        total_chars = set(bone1) | set(bone2)
        
        if total_chars:
            return len(common_chars) / len(total_chars)
        
        return 0.0

class AnimationLibraryGUI(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.blender_connection = BlenderConnection()
        self.animation_library = {"animations": [], "version": "1.0"}
        self.library_path = Path('./animation_library')
        self.current_selection = []
        self.current_armature = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_library()
        
    def setup_ui(self):
        self.setWindowTitle("Animation Library - Professional Edition")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply dark theme
        self.setStyleSheet("""
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
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #0078d4;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QLineEdit, QComboBox {
                background-color: #404040;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Animation browser and controls
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Bone mapping and details
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes
        splitter.setSizes([800, 600])
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Connection status indicator
        self.connection_status = QLabel("Disconnected")
        self.connection_status.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.connection_status)
        
    def create_left_panel(self):
        """Create the left panel with animation browser"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Connection controls
        connection_group = QGroupBox("Blender Connection")
        connection_layout = QHBoxLayout(connection_group)
        
        self.connect_btn = QPushButton("Connect to Blender")
        self.connect_btn.clicked.connect(self.toggle_connection)
        connection_layout.addWidget(self.connect_btn)
        
        self.extract_btn = QPushButton("Extract Animation")
        self.extract_btn.clicked.connect(self.extract_animation)
        self.extract_btn.setEnabled(False)
        connection_layout.addWidget(self.extract_btn)
        
        layout.addWidget(connection_group)
        
        # Search and filter
        search_group = QGroupBox("Search & Filter")
        search_layout = QVBoxLayout(search_group)
        
        search_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search animations...")
        self.search_box.textChanged.connect(self.filter_animations)
        search_row.addWidget(self.search_box)
        
        self.tag_filter = QComboBox()
        self.tag_filter.addItem("All Tags")
        self.tag_filter.currentTextChanged.connect(self.filter_animations)
        search_row.addWidget(self.tag_filter)
        
        search_layout.addLayout(search_row)
        layout.addWidget(search_group)
        
        # Animation grid
        animations_group = QGroupBox("Animation Library")
        animations_layout = QVBoxLayout(animations_group)
        
        # Scroll area for animation cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.animations_widget = QWidget()
        self.animations_layout = QGridLayout(self.animations_widget)
        self.animations_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.scroll_area.setWidget(self.animations_widget)
        animations_layout.addWidget(self.scroll_area)
        
        layout.addWidget(animations_group)
        
        return widget
    
    def create_right_panel(self):
        """Create the right panel with bone mapping and options"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Current selection info
        selection_group = QGroupBox("Current Selection")
        selection_layout = QVBoxLayout(selection_group)
        
        self.selection_label = QLabel("No armature selected")
        self.selection_label.setStyleSheet("font-size: 11px; color: #aaa;")
        selection_layout.addWidget(self.selection_label)
        
        self.bones_label = QLabel("No bones selected")
        self.bones_label.setStyleSheet("font-size: 10px; color: #aaa;")
        selection_layout.addWidget(self.bones_label)
        
        layout.addWidget(selection_group)
        
        # Apply options
        options_group = QGroupBox("Apply Options")
        options_layout = QVBoxLayout(options_group)
        
        # Selected bones only
        self.selected_only_cb = QCheckBox("Apply to selected bones only")
        self.selected_only_cb.setChecked(True)
        options_layout.addWidget(self.selected_only_cb)
        
        # Frame offset
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(QLabel("Frame Offset:"))
        self.frame_offset_spin = QSpinBox()
        self.frame_offset_spin.setRange(-1000, 1000)
        self.frame_offset_spin.setValue(1)
        frame_layout.addWidget(self.frame_offset_spin)
        frame_layout.addStretch()
        options_layout.addLayout(frame_layout)
        
        # Channel selection
        channels_layout = QHBoxLayout()
        self.location_cb = QCheckBox("Location")
        self.location_cb.setChecked(True)
        self.rotation_cb = QCheckBox("Rotation")
        self.rotation_cb.setChecked(True)
        self.scale_cb = QCheckBox("Scale")
        self.scale_cb.setChecked(True)
        
        channels_layout.addWidget(QLabel("Channels:"))
        channels_layout.addWidget(self.location_cb)
        channels_layout.addWidget(self.rotation_cb)
        channels_layout.addWidget(self.scale_cb)
        options_layout.addLayout(channels_layout)
        
        layout.addWidget(options_group)
        
        # Bone mapping
        self.bone_mapping_widget = BoneMappingWidget()
        layout.addWidget(self.bone_mapping_widget)
        
        return widget
    
    def setup_connections(self):
        """Setup signal connections"""
        self.blender_connection.connected.connect(self.on_connected)
        self.blender_connection.disconnected.connect(self.on_disconnected)
        self.blender_connection.message_received.connect(self.on_message_received)
        self.blender_connection.connection_error.connect(self.on_connection_error)
    
    def toggle_connection(self):
        """Toggle Blender connection"""
        if self.blender_connection.running:
            self.blender_connection.disconnect()
        else:
            self.blender_connection.connect_to_blender()
    
    def on_connected(self):
        """Handle successful connection"""
        self.connection_status.setText("Connected")
        self.connection_status.setStyleSheet("color: #51cf66; font-weight: bold;")
        self.connect_btn.setText("Disconnect")
        self.extract_btn.setEnabled(True)
        self.status_bar.showMessage("Connected to Blender successfully", 3000)
        
        # Request scene info
        self.blender_connection.send_command({'command': 'get_scene_info'})
    
    def on_disconnected(self):
        """Handle disconnection"""
        self.connection_status.setText("Disconnected")
        self.connection_status.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        self.connect_btn.setText("Connect to Blender")
        self.extract_btn.setEnabled(False)
        self.status_bar.showMessage("Disconnected from Blender", 3000)
    
    def on_connection_error(self, error):
        """Handle connection errors"""
        QMessageBox.warning(self, "Connection Error", f"Failed to connect to Blender:\n{error}")
        self.on_disconnected()
    
    def on_message_received(self, data):
        """Handle messages from Blender"""
        msg_type = data.get('type')
        
        if msg_type == 'selection_update':
            self.update_selection_info(data)
        elif msg_type == 'animation_extracted':
            self.on_animation_extracted(data)
        elif msg_type == 'animation_applied':
            self.on_animation_applied(data)
        elif msg_type == 'scene_info':
            self.update_scene_info(data)
        elif msg_type == 'error':
            QMessageBox.warning(self, "Blender Error", data.get('message', 'Unknown error'))
    
    def update_selection_info(self, data):
        """Update selection information display"""
        armature = data.get('armature_name')
        bones = data.get('selected_bones', [])
        
        if armature:
            self.selection_label.setText(f"Armature: {armature}")
            self.current_armature = armature
        else:
            self.selection_label.setText("No armature selected")
            self.current_armature = None
            
        self.current_selection = bones
        if bones:
            bone_text = ", ".join(bones[:3])
            if len(bones) > 3:
                bone_text += f" +{len(bones)-3} more"
            self.bones_label.setText(f"Bones: {bone_text}")
        else:
            self.bones_label.setText("No bones selected")
    
    def update_scene_info(self, data):
        """Update scene information"""
        armatures = data.get('armatures', [])
        if armatures:
            # Update bone mapping widget with available bones
            for armature in armatures:
                if armature['name'] == self.current_armature:
                    target_bones = armature['bones']
                    # For now, use the same bones as source - in real use this would be different
                    self.bone_mapping_widget.update_bones(target_bones, target_bones)
                    break
    
    def extract_animation(self):
        """Extract animation from Blender"""
        if self.blender_connection.running:
            self.blender_connection.send_command({'command': 'extract_animation'})
            self.status_bar.showMessage("Extracting animation...", 2000)
    
    def on_animation_extracted(self, data):
        """Handle extracted animation data"""
        # Store the animation
        animation_metadata = {
            "id": f"{data['armature_name']}_{data['action_name']}_{int(time.time())}",
            "name": data['action_name'],
            "description": f"Extracted from {data['armature_name']}",
            "armature_source": data['armature_name'],
            "frame_range": data['frame_range'],
            "total_bones_animated": data['total_bones_animated'],
            "total_keyframes": data['total_keyframes'],
            "bone_data": data['bone_data'],
            "created_date": datetime.now().isoformat(),
            "rig_type": "rigify" if "rigify" in data['armature_name'].lower() else "unknown",
            "tags": self.generate_tags(data),
            "category": "extracted",
            "duration_frames": data['frame_range'][1] - data['frame_range'][0] + 1
        }
        
        self.animation_library["animations"].append(animation_metadata)
        self.save_library()
        self.refresh_animations()
        self.update_tag_filter()
        
        self.status_bar.showMessage(f"Animation '{data['action_name']}' extracted successfully", 3000)
    
    def on_animation_applied(self, data):
        """Handle animation application confirmation"""
        action_name = data.get('action_name', 'Unknown')
        bones_applied = data.get('bones_applied', 0)
        keyframes_applied = data.get('keyframes_applied', 0)
        
        self.status_bar.showMessage(
            f"Applied '{action_name}': {bones_applied} bones, {keyframes_applied} keyframes", 
            3000
        )
    
    def apply_animation(self, animation_data):
        """Apply animation to current armature"""
        if not self.blender_connection.running:
            QMessageBox.warning(self, "Not Connected", "Please connect to Blender first")
            return
            
        if not self.current_armature:
            QMessageBox.warning(self, "No Armature", "Please select an armature in Blender")
            return
        
        # Get apply options
        bone_mapping = self.bone_mapping_widget.bone_mapping
        frame_offset = self.frame_offset_spin.value()
        
        command = {
            'command': 'apply_animation',
            'animation_data': animation_data,
            'bone_mapping': bone_mapping,
            'frame_offset': frame_offset,
            'selected_only': self.selected_only_cb.isChecked(),
            'channels': {
                'location': self.location_cb.isChecked(),
                'rotation': self.rotation_cb.isChecked(),
                'scale': self.scale_cb.isChecked()
            }
        }
        
        self.blender_connection.send_command(command)
        self.status_bar.showMessage(f"Applying animation '{animation_data['name']}'...", 2000)
    
    def generate_tags(self, animation_data):
        """Generate automatic tags for animation"""
        tags = []
        bone_data = animation_data.get('bone_data', {})
        animated_bones = set(bone_data.keys())
        
        # Detection logic
        leg_bones = {'thigh_fk.L', 'thigh_fk.R', 'shin_fk.L', 'shin_fk.R', 'foot_fk.L', 'foot_fk.R'}
        if animated_bones & leg_bones:
            tags.append("locomotion")
        
        arm_bones = {'upper_arm_fk.L', 'upper_arm_fk.R', 'forearm_fk.L', 'forearm_fk.R'}
        if animated_bones & arm_bones:
            tags.append("upper_body")
        
        face_bones = {'jaw', 'eyes', 'brow', 'lip', 'cheek'}
        if any(face_bone in str(animated_bones) for face_bone in face_bones):
            tags.append("facial")
        
        finger_bones = {'thumb', 'f_index', 'f_middle', 'f_ring', 'f_pinky'}
        if any(finger_bone in str(animated_bones) for finger_bone in finger_bones):
            tags.append("hands")
        
        if any('spine' in bone for bone in animated_bones):
            tags.append("spine")
        
        duration = animation_data.get('frame_range', [1, 1])[1] - animation_data.get('frame_range', [1, 1])[0] + 1
        if duration < 10:
            tags.append("short")
        elif duration > 100:
            tags.append("long")
        else:
            tags.append("medium")
        
        return tags if tags else ["uncategorized"]
    
    def load_library(self):
        """Load animation library from disk"""
        metadata_file = self.library_path / 'library_metadata.json'
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    self.animation_library = json.load(f)
                self.refresh_animations()
                self.update_tag_filter()
            except Exception as e:
                QMessageBox.warning(self, "Load Error", f"Failed to load library: {e}")
    
    def save_library(self):
        """Save animation library to disk"""
        self.library_path.mkdir(exist_ok=True)
        metadata_file = self.library_path / 'library_metadata.json'
        try:
            with open(metadata_file, 'w') as f:
                json.dump(self.animation_library, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Failed to save library: {e}")
    
    def refresh_animations(self):
        """Refresh the animation cards display"""
        # Clear existing cards
        for i in reversed(range(self.animations_layout.count())):
            child = self.animations_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add animation cards
        animations = self.get_filtered_animations()
        
        columns = 3  # Number of columns in grid
        for i, animation in enumerate(animations):
            row = i // columns
            col = i % columns
            
            card = AnimationCard(animation)
            card.apply_requested.connect(self.apply_animation)
            self.animations_layout.addWidget(card, row, col)
        
        # Add stretch to fill remaining space
        self.animations_layout.setRowStretch(len(animations) // columns + 1, 1)
    
    def get_filtered_animations(self):
        """Get animations filtered by search and tag"""
        animations = self.animation_library.get("animations", [])
        
        # Filter by search text
        search_text = self.search_box.text().lower()
        if search_text:
            animations = [
                anim for anim in animations
                if (search_text in anim.get('name', '').lower() or
                    search_text in anim.get('description', '').lower() or
                    any(search_text in tag.lower() for tag in anim.get('tags', [])))
            ]
        
        # Filter by tag
        selected_tag = self.tag_filter.currentText()
        if selected_tag != "All Tags":
            animations = [
                anim for anim in animations
                if selected_tag.lower() in [tag.lower() for tag in anim.get('tags', [])]
            ]
        
        return animations
    
    def update_tag_filter(self):
        """Update the tag filter dropdown"""
        current_tag = self.tag_filter.currentText()
        self.tag_filter.clear()
        self.tag_filter.addItem("All Tags")
        
        # Collect all unique tags
        all_tags = set()
        for animation in self.animation_library.get("animations", []):
            all_tags.update(animation.get('tags', []))
        
        # Add tags to filter
        for tag in sorted(all_tags):
            self.tag_filter.addItem(tag)
        
        # Restore previous selection if it exists
        if current_tag in [self.tag_filter.itemText(i) for i in range(self.tag_filter.count())]:
            self.tag_filter.setCurrentText(current_tag)
    
    def filter_animations(self):
        """Filter animations based on search and tag selection"""
        self.refresh_animations()
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.blender_connection.running:
            self.blender_connection.disconnect()
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Animation Library")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Animation Studio")
    
    # Create and show main window
    window = AnimationLibraryGUI()
    window.show()
    
    # Center window on screen
    screen = app.primaryScreen().geometry()
    window_geo = window.geometry()
    x = (screen.width() - window_geo.width()) // 2
    y = (screen.height() - window_geo.height()) // 2
    window.move(x, y)
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()