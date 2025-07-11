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
    QScrollArea, QTextEdit, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.animation_data import AnimationMetadata


class MetadataPanel(QWidget):
    """Professional metadata panel matching Studio Library style"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_animation = None
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
        """Show detailed metadata for selected animation"""
        self.current_animation = animation
        self.clear_content()
        
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
        storage_label.setStyleSheet(f"font-weight: bold; color: {'#51cf66' if animation.is_blend_file_storage() else '#ffd43b'};")
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