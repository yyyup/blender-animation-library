"""
Studio Layout Manager
Manages the 3-panel Studio Library layout
"""

import sys
from pathlib import Path

# Add core modules to path
gui_dir = Path(__file__).parent.parent.parent
if str(gui_dir) not in sys.path:
    sys.path.insert(0, str(gui_dir))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
    QTabWidget, QGroupBox, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt

from gui.widgets.folder_tree import FolderTreeWidget
from gui.widgets.metadata_panel import MetadataPanel
from gui.widgets.toolbar import AnimationToolbar
from gui.widgets.animation_card import AnimationCardGrid


class StudioLayoutManager:
    """Manages the Studio Library 3-panel layout"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.widgets = {}
    
    def setup_layout(self) -> QWidget:
        """Setup the complete Studio Library layout"""
        # Central widget with main splitter
        central_widget = QWidget()
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Main horizontal splitter (3 panels)
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left panel - Folder tree
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Center panel - Animation grid with toolbar
        center_panel = self.create_center_panel()
        main_splitter.addWidget(center_panel)
        
        # Right panel - Metadata and controls
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions: 300px | expand | 350px
        main_splitter.setSizes([300, 900, 350])
        main_splitter.setCollapsible(0, False)  # Don't collapse folder panel
        main_splitter.setCollapsible(2, False)  # Don't collapse metadata panel
        
        print("✅ Studio Library layout created!")
        return central_widget
    
    def create_left_panel(self) -> QWidget:
        """Create the left panel with folder tree"""
        panel = QWidget()
        panel.setMinimumWidth(250)
        panel.setMaximumWidth(400)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QLabel("Folders")
        header.setStyleSheet("""
            QLabel {
                background-color: #4a4a4a;
                color: white;
                padding: 12px;
                font-weight: bold;
                font-size: 12px;
                border-bottom: 1px solid #555;
            }
        """)
        layout.addWidget(header)
        
        # Folder tree
        self.widgets['folder_tree'] = FolderTreeWidget()
        layout.addWidget(self.widgets['folder_tree'])
        
        # Apply panel styling
        panel.setStyleSheet("""
            QWidget {
                background-color: #393939;
                border-right: 1px solid #555;
            }
        """)
        
        return panel
    
    def create_center_panel(self) -> QWidget:
        """Create the center panel with toolbar and animation grid"""
        panel = QWidget()
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        self.widgets['toolbar'] = AnimationToolbar()
        layout.addWidget(self.widgets['toolbar'])
        
        # Animation grid
        self.widgets['animation_grid'] = AnimationCardGrid()
        layout.addWidget(self.widgets['animation_grid'])
        
        # Apply panel styling
        panel.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
            }
        """)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel with metadata and apply options"""
        panel = QWidget()
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(500)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab widget for different sections
        tab_widget = QTabWidget()
        
        # Metadata tab
        self.widgets['metadata_panel'] = MetadataPanel()
        tab_widget.addTab(self.widgets['metadata_panel'], "Details")
        
        # Apply options tab
        apply_options_widget = self.create_apply_options_widget()
        tab_widget.addTab(apply_options_widget, "Apply Options")
        
        # Selection info tab
        selection_widget = self.create_selection_widget()
        tab_widget.addTab(selection_widget, "Selection")
        
        layout.addWidget(tab_widget)
        
        # Apply panel styling
        panel.setStyleSheet("""
            QWidget {
                background-color: #393939;
                border-left: 1px solid #555;
            }
            
            QTabWidget::pane {
                border: none;
                background-color: #393939;
            }
            
            QTabBar::tab {
                background-color: #4a4a4a;
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: #4a90e2;
            }
            
            QTabBar::tab:hover {
                background-color: #525252;
            }
        """)
        
        return panel
    
    def create_apply_options_widget(self) -> QWidget:
        """Create apply options widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Apply options group
        options_group = QGroupBox("Application Settings")
        options_layout = QVBoxLayout(options_group)
        
        # Selected bones only option
        self.widgets['selected_bones_only_cb'] = QCheckBox("Apply to selected bones only")
        self.widgets['selected_bones_only_cb'].setChecked(False)
        options_layout.addWidget(self.widgets['selected_bones_only_cb'])
        
        # Frame offset
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(QLabel("Start at frame:"))
        
        self.widgets['frame_offset_spin'] = QSpinBox()
        self.widgets['frame_offset_spin'].setRange(1, 9999)
        self.widgets['frame_offset_spin'].setValue(1)
        frame_layout.addWidget(self.widgets['frame_offset_spin'])
        frame_layout.addStretch()
        
        options_layout.addLayout(frame_layout)
        
        # Channel selection
        channels_group = QGroupBox("Channels to Apply")
        channels_layout = QHBoxLayout(channels_group)
        
        self.widgets['location_cb'] = QCheckBox("Location")
        self.widgets['location_cb'].setChecked(True)
        channels_layout.addWidget(self.widgets['location_cb'])
        
        self.widgets['rotation_cb'] = QCheckBox("Rotation")
        self.widgets['rotation_cb'].setChecked(True)
        channels_layout.addWidget(self.widgets['rotation_cb'])
        
        self.widgets['scale_cb'] = QCheckBox("Scale")
        self.widgets['scale_cb'].setChecked(True)
        channels_layout.addWidget(self.widgets['scale_cb'])
        
        options_layout.addWidget(channels_group)
        
        layout.addWidget(options_group)
        
        # Compatibility info
        compat_group = QGroupBox("Rig Compatibility")
        compat_layout = QVBoxLayout(compat_group)
        
        self.widgets['current_rig_label'] = QLabel("Current Rig: Not detected")
        compat_layout.addWidget(self.widgets['current_rig_label'])
        
        # Compatibility guide
        guide_text = (
            "🟢 Rigify → Rigify rigs\n"
            "🔵 Auto-Rig Pro → Auto-Rig Pro rigs\n"
            "🟡 Mixamo → Mixamo rigs\n"
            "⚪ Unknown rigs (user discretion)"
        )
        guide_label = QLabel(guide_text)
        guide_label.setStyleSheet("font-size: 10px; color: #aaa; padding: 4px;")
        compat_layout.addWidget(guide_label)
        
        layout.addWidget(compat_group)
        
        layout.addStretch()
        
        return widget
    
    def create_selection_widget(self) -> QWidget:
        """Create selection info widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Current selection group
        selection_group = QGroupBox("Current Selection")
        selection_layout = QVBoxLayout(selection_group)
        
        self.widgets['armature_label'] = QLabel("No armature selected")
        selection_layout.addWidget(self.widgets['armature_label'])
        
        self.widgets['bones_label'] = QLabel("No bones selected")
        selection_layout.addWidget(self.widgets['bones_label'])
        
        self.widgets['frame_label'] = QLabel("Frame: --")
        selection_layout.addWidget(self.widgets['frame_label'])
        
        # Selected bones info
        self.widgets['selected_bones_info'] = QLabel("No bones selected")
        self.widgets['selected_bones_info'].setStyleSheet("font-size: 9px; color: #888; padding: 2px 8px;")
        selection_layout.addWidget(self.widgets['selected_bones_info'])
        
        layout.addWidget(selection_group)
        
        # Performance info
        perf_group = QGroupBox("Performance Info")
        perf_layout = QVBoxLayout(perf_group)
        
        perf_info_text = (
            "⚡ .blend files: ~0.5s application\n"
            "⏳ JSON files: ~30s application\n"
            "💾 .blend files: 90% smaller\n"
            "🎯 Perfect animation fidelity"
        )
        perf_info_label = QLabel(perf_info_text)
        perf_info_label.setStyleSheet("font-size: 10px; color: #aaa; padding: 4px;")
        perf_layout.addWidget(perf_info_label)
        
        layout.addWidget(perf_group)
        
        layout.addStretch()
        
        return widget
    
    def get_widget(self, name: str):
        """Get a widget by name"""
        return self.widgets.get(name)