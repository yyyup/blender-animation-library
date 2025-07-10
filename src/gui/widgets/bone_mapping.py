"""
Bone Mapping Widget
Advanced bone mapping interface with drag & drop and auto-mapping
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QComboBox, QHeaderView,
    QProgressBar, QGroupBox, QCheckBox, QSpinBox, QFrame,
    QToolButton, QMenu, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QAction, QIcon
from typing import Dict, List, Optional, Set, Tuple
import difflib
import sys
from pathlib import Path

# Add core modules to path
gui_dir = Path(__file__).parent.parent.parent
if str(gui_dir) not in sys.path:
    sys.path.insert(0, str(gui_dir))

from core.animation_data import ApplyOptions


class BoneMappingWorker(QThread):
    """Worker thread for bone mapping calculations"""
    
    mapping_completed = Signal(dict)
    progress_updated = Signal(int)
    
    def __init__(self, source_bones: List[str], target_bones: List[str]):
        super().__init__()
        self.source_bones = source_bones
        self.target_bones = target_bones
        self.threshold = 0.6
    
    def run(self):
        """Calculate bone mappings in background"""
        mappings = {}
        total_bones = len(self.source_bones)
        
        for i, source_bone in enumerate(self.source_bones):
            best_match, best_score = self.find_best_match(source_bone)
            
            if best_score >= self.threshold:
                mappings[source_bone] = best_match
            
            # Update progress
            progress = int((i + 1) / total_bones * 100)
            self.progress_updated.emit(progress)
        
        self.mapping_completed.emit(mappings)
    
    def find_best_match(self, source_bone: str) -> Tuple[Optional[str], float]:
        """Find the best matching target bone"""
        best_match = None
        best_score = 0.0
        
        for target_bone in self.target_bones:
            score = self.calculate_similarity(source_bone, target_bone)
            if score > best_score:
                best_score = score
                best_match = target_bone
        
        return best_match, best_score
    
    def calculate_similarity(self, bone1: str, bone2: str) -> float:
        """Calculate similarity between bone names"""
        bone1_clean = self.clean_bone_name(bone1)
        bone2_clean = self.clean_bone_name(bone2)
        
        # Exact match
        if bone1_clean == bone2_clean:
            return 1.0
        
        # Check if one contains the other
        if bone1_clean in bone2_clean or bone2_clean in bone1_clean:
            return 0.9
        
        # Use difflib for sequence matching
        matcher = difflib.SequenceMatcher(None, bone1_clean, bone2_clean)
        ratio = matcher.ratio()
        
        # Bonus for same side (L/R)
        if self.same_side(bone1, bone2):
            ratio += 0.1
        
        # Bonus for similar length
        length_diff = abs(len(bone1_clean) - len(bone2_clean))
        if length_diff <= 2:
            ratio += 0.05
        
        return min(ratio, 1.0)
    
    def clean_bone_name(self, bone_name: str) -> str:
        """Clean bone name for comparison"""
        cleaned = bone_name.lower()
        
        # Remove common prefixes
        prefixes = ['def_', 'mch_', 'org_', 'ctrl_']
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
                break
        
        # Remove common suffixes
        suffixes = ['.l', '.r', '_l', '_r', '.left', '.right']
        for suffix in suffixes:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)]
                break
        
        return cleaned
    
    def same_side(self, bone1: str, bone2: str) -> bool:
        """Check if bones are on the same side (L/R)"""
        bone1_lower = bone1.lower()
        bone2_lower = bone2.lower()
        
        left_indicators = ['.l', '_l', '.left', 'left']
        right_indicators = ['.r', '_r', '.right', 'right']
        
        bone1_is_left = any(indicator in bone1_lower for indicator in left_indicators)
        bone1_is_right = any(indicator in bone1_lower for indicator in right_indicators)
        
        bone2_is_left = any(indicator in bone2_lower for indicator in left_indicators)
        bone2_is_right = any(indicator in bone2_lower for indicator in right_indicators)
        
        return (bone1_is_left and bone2_is_left) or (bone1_is_right and bone2_is_right)


class BoneMappingWidget(QWidget):
    """Advanced bone mapping widget with auto-mapping and manual override"""
    
    mapping_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.source_bones: List[str] = []
        self.target_bones: List[str] = []
        self.bone_mapping: Dict[str, str] = {}
        self.auto_mapping_worker: Optional[BoneMappingWorker] = None
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the bone mapping UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Header with title and controls
        header_widget = self.create_header_widget()
        layout.addWidget(header_widget)
        
        # Mapping table
        self.mapping_table = self.create_mapping_table()
        layout.addWidget(self.mapping_table)
        
        # Controls section
        controls_widget = self.create_controls_widget()
        layout.addWidget(controls_widget)
        
        # Apply options
        apply_options_widget = self.create_apply_options_widget()
        layout.addWidget(apply_options_widget)
    
    def create_header_widget(self) -> QWidget:
        """Create header with title and search"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("Bone Mapping")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search bones...")
        self.search_box.setMaximumWidth(200)
        self.search_box.textChanged.connect(self.filter_mapping_table)
        layout.addWidget(self.search_box)
        
        return widget
    
    def create_mapping_table(self) -> QTableWidget:
        """Create the bone mapping table"""
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Source Bone", "→", "Target Bone", "Score"])
        
        # Configure headers
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        
        table.setColumnWidth(1, 30)
        table.setColumnWidth(3, 60)
        
        # Style the table
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                alternate-background-color: #353535;
                color: #ffffff;
                gridline-color: #555;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
        """)
        
        return table
    
    def create_controls_widget(self) -> QWidget:
        """Create mapping controls"""
        widget = QGroupBox("Mapping Controls")
        layout = QHBoxLayout(widget)
        
        # Auto-map button
        self.auto_map_btn = QPushButton("Auto-Map Similar Names")
        self.auto_map_btn.clicked.connect(self.start_auto_mapping)
        layout.addWidget(self.auto_map_btn)
        
        # Clear mapping button
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_mapping)
        layout.addWidget(clear_btn)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Mapping statistics
        self.stats_label = QLabel("No mapping loaded")
        self.stats_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.stats_label)
        
        layout.addStretch()
        
        # Presets menu button
        presets_btn = QToolButton()
        presets_btn.setText("Presets")
        presets_btn.setToolTip("Load bone mapping presets")
        
        presets_menu = QMenu(self)
        
        # Common rig presets
        rigify_action = QAction("Rigify → Rigify", self)
        rigify_action.triggered.connect(lambda: self.load_preset("rigify"))
        presets_menu.addAction(rigify_action)
        
        makehuman_action = QAction("MakeHuman → Rigify", self)
        makehuman_action.triggered.connect(lambda: self.load_preset("makehuman_rigify"))
        presets_menu.addAction(makehuman_action)
        
        mixamo_action = QAction("Mixamo → Rigify", self)
        mixamo_action.triggered.connect(lambda: self.load_preset("mixamo_rigify"))
        presets_menu.addAction(mixamo_action)
        
        presets_menu.addSeparator()
        
        save_preset_action = QAction("Save Current as Preset...", self)
        save_preset_action.triggered.connect(self.save_preset)
        presets_menu.addAction(save_preset_action)
        
        presets_btn.setMenu(presets_menu)
        presets_btn.setPopupMode(QToolButton.InstantPopup)
        layout.addWidget(presets_btn)
        
        return widget
    
    def create_apply_options_widget(self) -> QWidget:
        """Create apply options section"""
        widget = QGroupBox("Apply Options")
        layout = QVBoxLayout(widget)
        
        # Selected bones only
        self.selected_only_cb = QCheckBox("Apply to selected bones only")
        self.selected_only_cb.setChecked(True)
        self.selected_only_cb.toggled.connect(self.on_options_changed)
        layout.addWidget(self.selected_only_cb)
        
        # Frame offset
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(QLabel("Frame Offset:"))
        
        self.frame_offset_spin = QSpinBox()
        self.frame_offset_spin.setRange(-1000, 1000)
        self.frame_offset_spin.setValue(1)
        self.frame_offset_spin.valueChanged.connect(self.on_options_changed)
        frame_layout.addWidget(self.frame_offset_spin)
        
        frame_layout.addStretch()
        layout.addLayout(frame_layout)
        
        # Channel selection
        channels_layout = QHBoxLayout()
        channels_layout.addWidget(QLabel("Channels:"))
        
        self.location_cb = QCheckBox("Location")
        self.location_cb.setChecked(True)
        self.location_cb.toggled.connect(self.on_options_changed)
        channels_layout.addWidget(self.location_cb)
        
        self.rotation_cb = QCheckBox("Rotation")
        self.rotation_cb.setChecked(True)
        self.rotation_cb.toggled.connect(self.on_options_changed)
        channels_layout.addWidget(self.rotation_cb)
        
        self.scale_cb = QCheckBox("Scale")
        self.scale_cb.setChecked(True)
        self.scale_cb.toggled.connect(self.on_options_changed)
        channels_layout.addWidget(self.scale_cb)
        
        channels_layout.addStretch()
        layout.addLayout(channels_layout)
        
        return widget
    
    def setup_connections(self):
        """Setup signal connections"""
        self.mapping_table.cellChanged.connect(self.on_mapping_changed)
    
    def update_bones(self, source_bones: List[str], target_bones: List[str]):
        """Update available bones for mapping"""
        self.source_bones = source_bones
        self.target_bones = target_bones
        self.refresh_mapping_table()
        self.update_statistics()
    
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
            
            # Similarity score
            score_item = QTableWidgetItem("")
            score_item.setFlags(score_item.flags() & ~Qt.ItemIsEditable)
            score_item.setTextAlignment(Qt.AlignCenter)
            self.mapping_table.setItem(i, 3, score_item)
    
    def filter_mapping_table(self):
        """Filter table based on search text"""
        search_text = self.search_box.text().lower()
        
        for i in range(self.mapping_table.rowCount()):
            source_item = self.mapping_table.item(i, 0)
            if source_item:
                source_bone = source_item.text().lower()
                target_combo = self.mapping_table.cellWidget(i, 2)
                target_bone = target_combo.currentText().lower() if target_combo else ""
                
                # Show row if search text matches source or target bone
                visible = (search_text in source_bone or 
                          search_text in target_bone or 
                          not search_text)
                
                self.mapping_table.setRowHidden(i, not visible)
    
    def update_mapping(self, source_bone: str, target_bone: str):
        """Update bone mapping when user changes selection"""
        if target_bone:
            self.bone_mapping[source_bone] = target_bone
        elif source_bone in self.bone_mapping:
            del self.bone_mapping[source_bone]
        
        self.update_statistics()
        self.mapping_changed.emit(self.bone_mapping)
    
    def start_auto_mapping(self):
        """Start automatic bone mapping in background"""
        if not self.source_bones or not self.target_bones:
            return
        
        # Disable controls during mapping
        self.auto_map_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start worker thread
        self.auto_mapping_worker = BoneMappingWorker(self.source_bones, self.target_bones)
        self.auto_mapping_worker.progress_updated.connect(self.progress_bar.setValue)
        self.auto_mapping_worker.mapping_completed.connect(self.on_auto_mapping_completed)
        self.auto_mapping_worker.start()
    
    def on_auto_mapping_completed(self, mappings: Dict[str, str]):
        """Handle completed auto-mapping"""
        # Update bone mapping
        self.bone_mapping.update(mappings)
        
        # Refresh table
        self.refresh_mapping_table()
        self.update_similarity_scores()
        
        # Re-enable controls
        self.auto_map_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Clean up worker
        if self.auto_mapping_worker:
            self.auto_mapping_worker.deleteLater()
            self.auto_mapping_worker = None
        
        self.update_statistics()
        self.mapping_changed.emit(self.bone_mapping)
    
    def update_similarity_scores(self):
        """Update similarity scores in the table"""
        if not self.auto_mapping_worker:
            return
        
        for i, source_bone in enumerate(self.source_bones):
            if source_bone in self.bone_mapping:
                target_bone = self.bone_mapping[source_bone]
                
                # Calculate similarity score
                worker = BoneMappingWorker([source_bone], [target_bone])
                _, score = worker.find_best_match(source_bone)
                
                # Update score item
                score_item = self.mapping_table.item(i, 3)
                if score_item:
                    score_text = f"{score:.2f}"
                    score_item.setText(score_text)
                    
                    # Color code based on score
                    if score >= 0.8:
                        score_item.setBackground(QColor(0, 120, 0, 100))  # Green
                    elif score >= 0.6:
                        score_item.setBackground(QColor(255, 165, 0, 100))  # Orange
                    else:
                        score_item.setBackground(QColor(255, 0, 0, 100))  # Red
    
    def clear_mapping(self):
        """Clear all bone mappings"""
        self.bone_mapping.clear()
        self.refresh_mapping_table()
        self.update_statistics()
        self.mapping_changed.emit(self.bone_mapping)
    
    def load_preset(self, preset_name: str):
        """Load a bone mapping preset"""
        # This would load from a preset file in a real implementation
        presets = {
            "rigify": {},  # Rigify to Rigify would be 1:1 mapping
            "makehuman_rigify": {
                # Example MakeHuman to Rigify mappings
                "spine01": "spine_fk.001",
                "spine02": "spine_fk.002",
                "spine03": "spine_fk.003",
                "upperarm_l": "upper_arm_fk.L",
                "upperarm_r": "upper_arm_fk.R",
                "lowerarm_l": "forearm_fk.L",
                "lowerarm_r": "forearm_fk.R",
            },
            "mixamo_rigify": {
                # Example Mixamo to Rigify mappings
                "mixamorig:Hips": "hips",
                "mixamorig:Spine": "spine_fk.001",
                "mixamorig:Spine1": "spine_fk.002",
                "mixamorig:Spine2": "spine_fk.003",
                "mixamorig:LeftArm": "upper_arm_fk.L",
                "mixamorig:RightArm": "upper_arm_fk.R",
            }
        }
        
        preset_mapping = presets.get(preset_name, {})
        
        # Apply preset mappings where possible
        for source_bone, target_bone in preset_mapping.items():
            if source_bone in self.source_bones and target_bone in self.target_bones:
                self.bone_mapping[source_bone] = target_bone
        
        self.refresh_mapping_table()
        self.update_statistics()
        self.mapping_changed.emit(self.bone_mapping)
    
    def save_preset(self):
        """Save current mapping as a preset"""
        # In a real implementation, this would open a dialog to save the preset
        print("Save preset functionality would be implemented here")
    
    def update_statistics(self):
        """Update mapping statistics display"""
        total_bones = len(self.source_bones)
        mapped_bones = len(self.bone_mapping)
        
        if total_bones > 0:
            percentage = (mapped_bones / total_bones) * 100
            self.stats_label.setText(f"Mapped: {mapped_bones}/{total_bones} ({percentage:.1f}%)")
        else:
            self.stats_label.setText("No bones to map")
    
    def on_mapping_changed(self):
        """Handle manual mapping changes"""
        self.update_statistics()
        self.mapping_changed.emit(self.bone_mapping)
    
    def on_options_changed(self):
        """Handle apply options changes"""
        # Emit signal with current apply options
        apply_options = self.get_apply_options()
        # Could emit a signal here if needed
    
    def get_apply_options(self) -> ApplyOptions:
        """Get current apply options"""
        return ApplyOptions(
            selected_bones_only=self.selected_only_cb.isChecked(),
            frame_offset=self.frame_offset_spin.value(),
            channels={
                'location': self.location_cb.isChecked(),
                'rotation': self.rotation_cb.isChecked(),
                'scale': self.scale_cb.isChecked()
            },
            bone_mapping=self.bone_mapping.copy()
        )
    
    def set_apply_options(self, apply_options: ApplyOptions):
        """Set apply options in the UI"""
        self.selected_only_cb.setChecked(apply_options.selected_bones_only)
        self.frame_offset_spin.setValue(apply_options.frame_offset)
        
        self.location_cb.setChecked(apply_options.channels.get('location', True))
        self.rotation_cb.setChecked(apply_options.channels.get('rotation', True))
        self.scale_cb.setChecked(apply_options.channels.get('scale', True))
        
        self.bone_mapping = apply_options.bone_mapping.copy()
        self.refresh_mapping_table()
        self.update_statistics()