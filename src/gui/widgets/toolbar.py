"""
Toolbar Widget
Professional toolbar with connection controls, search, and filters
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLineEdit, QComboBox,
    QFrame, QLabel
)
from PySide6.QtCore import Signal


class AnimationToolbar(QWidget):
    """Professional toolbar for animation library"""
    
    # Signals
    connect_requested = Signal()
    extract_requested = Signal()
    search_changed = Signal(str)
    tag_filter_changed = Signal(str)
    rig_filter_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the toolbar UI"""
        self.setFixedHeight(60)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Connection status and controls
        self.connect_btn = QPushButton("Connect to Blender")
        self.connect_btn.setObjectName("primaryButton")
        self.connect_btn.clicked.connect(self.connect_requested.emit)
        layout.addWidget(self.connect_btn)
        
        self.extract_btn = QPushButton("Extract Animation")
        self.extract_btn.setObjectName("secondaryButton")
        self.extract_btn.setEnabled(False)
        self.extract_btn.clicked.connect(self.extract_requested.emit)
        layout.addWidget(self.extract_btn)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("color: #555;")
        layout.addWidget(separator)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search animations...")
        self.search_box.textChanged.connect(self.search_changed.emit)
        self.search_box.setFixedWidth(300)
        layout.addWidget(self.search_box)
        
        # Filter dropdowns
        self.tag_filter = QComboBox()
        self.tag_filter.setMinimumWidth(120)
        self.tag_filter.addItem("All Tags")
        self.tag_filter.currentTextChanged.connect(self.tag_filter_changed.emit)
        layout.addWidget(self.tag_filter)
        
        self.rig_filter = QComboBox()
        self.rig_filter.addItem("All Rigs")
        self.rig_filter.addItem("Rigify")
        self.rig_filter.addItem("Auto-Rig Pro")
        self.rig_filter.addItem("Mixamo")
        self.rig_filter.addItem("Unknown")
        self.rig_filter.currentTextChanged.connect(self.rig_filter_changed.emit)
        layout.addWidget(self.rig_filter)
        
        layout.addStretch()
        
        # Connection indicator
        self.connection_indicator = QLabel("●")
        self.connection_indicator.setStyleSheet("color: #ff6b6b; font-size: 16px;")
        layout.addWidget(self.connection_indicator)
        
        # Stats label
        self.stats_label = QLabel("No animations loaded")
        self.stats_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.stats_label)
        
        # Apply Studio Library styling
        self.setStyleSheet("""
            /* Toolbar styling - Studio Library specifications */
            QWidget {
                background-color: #393939;
                border-bottom: 1px solid #555;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            /* Primary buttons - Studio Library blue */
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QPushButton#primaryButton {
                background-color: #4a90e2;
                color: white;
                border: none;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #357abd;
            }
            
            QPushButton#secondaryButton {
                background-color: #666;
                color: white;
                border: 1px solid #777;
            }
            
            QPushButton#secondaryButton:hover {
                background-color: #777;
                border-color: #4a90e2;
            }
            
            QPushButton#secondaryButton:disabled {
                background-color: #444;
                color: #666;
                border-color: #555;
            }
            
            /* Search box and dropdowns */
            QLineEdit {
                padding: 6px 8px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #4a4a4a;
                color: #eeeeee;
                font-size: 11px;
                width: 300px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QComboBox {
                padding: 6px 8px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #4a4a4a;
                color: #eeeeee;
                font-size: 11px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QLineEdit:focus, QComboBox:focus {
                border-color: #4a90e2;
            }
            
            QComboBox::drop-down {
                border: none;
            }
            
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)
    
    def set_connected(self, connected: bool):
        """Update UI for connection state"""
        if connected:
            self.connect_btn.setText("Disconnect")
            self.extract_btn.setEnabled(True)
            self.connection_indicator.setStyleSheet("color: #51cf66; font-size: 16px;")
        else:
            self.connect_btn.setText("Connect to Blender")
            self.extract_btn.setEnabled(False)
            self.connection_indicator.setStyleSheet("color: #ff6b6b; font-size: 16px;")
    
    def set_connecting(self, connecting: bool):
        """Update UI for connecting state"""
        if connecting:
            self.connect_btn.setText("Connecting...")
            self.connect_btn.setEnabled(False)
        else:
            self.connect_btn.setEnabled(True)
    
    def update_stats(self, stats_text: str):
        """Update the statistics label"""
        self.stats_label.setText(stats_text)
    
    def update_tag_filter(self, tags: list):
        """Update the tag filter dropdown"""
        current_tag = self.tag_filter.currentText()
        self.tag_filter.clear()
        self.tag_filter.addItem("All Tags")
        
        # Add tags to filter
        for tag in sorted(tags):
            self.tag_filter.addItem(tag)
        
        # Restore previous selection if it exists
        tag_index = self.tag_filter.findText(current_tag)
        if tag_index >= 0:
            self.tag_filter.setCurrentIndex(tag_index)