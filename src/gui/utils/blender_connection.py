"""
GUI Blender Connection Handler
Manages the connection between Qt GUI and Blender with proper signal handling
"""

from PySide6.QtCore import QObject, Signal, QThread
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add core modules to path
gui_dir = Path(__file__).parent.parent.parent
if str(gui_dir) not in sys.path:
    sys.path.insert(0, str(gui_dir))

from core.communication import BlenderConnection, ConnectionConfig, Message
from core.animation_data import ApplyOptions
import logging

logger = logging.getLogger(__name__)


class BlenderConnectionHandler(QObject):
    """Handles Blender connection with Qt signals"""
    
    # Signals for UI updates
    connected = Signal()
    disconnected = Signal()
    connection_error = Signal(str)
    
    # Data signals
    scene_info_received = Signal(dict)
    selection_updated = Signal(dict)
    animation_extracted = Signal(dict)
    animation_applied = Signal(dict)
    error_received = Signal(str)
    
    def __init__(self, host='127.0.0.1', port=8080):
        super().__init__()
        
        self.config = ConnectionConfig(host=host, port=port)
        self.connection: Optional[BlenderConnection] = None
        self.connection_thread: Optional[QThread] = None
        
    def connect_to_blender(self) -> bool:
        """Connect to Blender in a separate thread"""
        try:
            # Create connection
            self.connection = BlenderConnection(self.config)
            
            # Register message handlers
            self.connection.register_handler("connected", self._on_connected)
            self.connection.register_handler("scene_info", self._on_scene_info)
            self.connection.register_handler("selection_update", self._on_selection_update)
            self.connection.register_handler("animation_extracted", self._on_animation_extracted)
            self.connection.register_handler("animation_applied", self._on_animation_applied)
            self.connection.register_handler("error", self._on_error)
            self.connection.register_error_handler(self._on_connection_error)
            
            # Connect in thread
            if self.connection.connect():
                self.connected.emit()
                logger.info("Connected to Blender successfully")
                
                # Request initial scene info
                self.get_scene_info()
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connection_error.emit(str(e))
            return False
    
    def disconnect_from_blender(self):
        """Disconnect from Blender"""
        if self.connection:
            self.connection.disconnect()
            self.connection = None
        
        self.disconnected.emit()
        logger.info("Disconnected from Blender")
    
    def is_connected(self) -> bool:
        """Check if connected to Blender"""
        return self.connection and self.connection.connected
    
    # Command methods
    def ping(self) -> bool:
        """Send ping to Blender"""
        if self.connection:
            return self.connection.ping()
        return False
    
    def get_scene_info(self) -> bool:
        """Request scene information from Blender"""
        if self.connection:
            return self.connection.get_scene_info()
        return False
    
    def extract_animation(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Request animation extraction from Blender"""
        if self.connection:
            return self.connection.extract_animation(options)
        return False
    
    def apply_animation(self, animation_data: Dict[str, Any], apply_options: ApplyOptions) -> bool:
        """Apply animation to Blender"""
        if self.connection:
            apply_data = {
                'selected_only': apply_options.selected_bones_only,
                'frame_offset': apply_options.frame_offset,
                'channels': apply_options.channels,
                'bone_mapping': apply_options.bone_mapping
            }
            return self.connection.apply_animation(animation_data, apply_data)
        return False
    
    # Message handlers
    def _on_connected(self, message: Message):
        """Handle connection confirmation"""
        logger.info("Blender confirmed connection")
    
    def _on_scene_info(self, message: Message):
        """Handle scene info response"""
        self.scene_info_received.emit(message.data)
    
    def _on_selection_update(self, message: Message):
        """Handle selection update"""
        self.selection_updated.emit(message.data)
    
    def _on_animation_extracted(self, message: Message):
        """Handle animation extraction result"""
        self.animation_extracted.emit(message.data)
    
    def _on_animation_applied(self, message: Message):
        """Handle animation application result"""
        self.animation_applied.emit(message.data)
    
    def _on_error(self, message: Message):
        """Handle error from Blender"""
        error_msg = message.data.get('message', 'Unknown error')
        self.error_received.emit(error_msg)
    
    def _on_connection_error(self, error_msg: str):
        """Handle connection errors"""
        self.connection_error.emit(error_msg)