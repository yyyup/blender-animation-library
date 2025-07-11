"""
GUI Blender Connection Handler
EXISTING SCRIPT: src/gui/utils/blender_connection.py (FIXED)

Fixed to properly handle new .blend file metadata structure
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
    thumbnail_updated = Signal(str)  # Emits animation_name when thumbnail is updated
    
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
            self.connection.register_handler("thumbnail_updated", self._on_thumbnail_updated)
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
        """Apply animation to Blender with proper data validation"""
        if not self.connection:
            logger.error("No connection to Blender")
            return False
        
        try:
            # Validate and normalize animation data
            normalized_data = self._normalize_animation_data(animation_data)
            
            # Convert ApplyOptions to dict
            apply_data = {
                'selected_only': apply_options.selected_bones_only,
                'frame_offset': apply_options.frame_offset,
                'channels': apply_options.channels,
                'bone_mapping': apply_options.bone_mapping
            }
            
            logger.info(f"Applying animation: {normalized_data.get('name', 'Unknown')}")
            logger.info(f"Storage method: {normalized_data.get('storage_method', 'unknown')}")
            
            return self.connection.apply_animation(normalized_data, apply_data)
            
        except Exception as e:
            logger.error(f"Failed to apply animation: {e}")
            self.error_received.emit(f"Application failed: {str(e)}")
            return False
    
    def update_thumbnail(self, animation_id: str) -> bool:
        """Request thumbnail update for a specific animation"""
        if self.connection:
            return self.connection.update_thumbnail(animation_id)
        return False
    
    def send_update_thumbnail(self, animation_name: str) -> bool:
        """Send update thumbnail command to Blender"""
        if not self.connection:
            logger.error("No connection to Blender")
            return False
        
        try:
            # Create the message as specified in the requirements
            message_data = {
                "command": "update_thumbnail", 
                "animation_name": animation_name
            }
            
            # Use the Message.command method to create the message
            from core.communication import Message
            message = Message.command("update_thumbnail", animation_name=animation_name)
            
            logger.info(f"Sending thumbnail update request for: {animation_name}")
            return self.connection.send_message(message)
            
        except Exception as e:
            logger.error(f"Failed to send thumbnail update: {e}")
            return False
    
    def _normalize_animation_data(self, animation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize animation data to ensure required fields are present"""
        normalized = animation_data.copy()
        
        # Ensure required fields exist
        required_fields = {
            'id': 'unknown_id',
            'name': 'Unknown Animation',
            'action_name': None,  # Will be set from name if missing
            'armature_source': 'Unknown Armature',
            'frame_range': [1, 30],
            'total_bones_animated': 0,
            'total_keyframes': 0,
            'storage_method': 'blend_file',  # Default to new method
            'created_date': '',
            'rig_type': 'Unknown'
        }
        
        for field, default_value in required_fields.items():
            if field not in normalized:
                if field == 'action_name':
                    # Use 'name' field for action_name if missing
                    normalized[field] = normalized.get('name', 'Unknown Animation')
                else:
                    normalized[field] = default_value
        
        # Ensure action_name is set (this was the source of the error)
        if not normalized.get('action_name'):
            normalized['action_name'] = normalized.get('name', 'Unknown Animation')
        
        # Add .blend file specific fields if using blend storage
        if normalized.get('storage_method') == 'blend_file':
            if 'blend_file' not in normalized:
                # Generate blend filename from ID
                animation_id = normalized.get('id', 'unknown')
                normalized['blend_file'] = f"{animation_id}.blend"
            
            if 'blend_action_name' not in normalized:
                # Use action_name as blend_action_name
                normalized['blend_action_name'] = normalized['action_name']
        
        logger.debug(f"Normalized animation data: {normalized.get('name')} ({normalized.get('storage_method')})")
        return normalized
    
    # Message handlers
    def _on_connected(self, message: Message):
        """Handle connection confirmation"""
        logger.info("Blender confirmed connection")
        # Check if Blender supports .blend file storage
        features = message.data.get('features', [])
        if 'blend_file_storage' in features:
            logger.info("✅ Blender supports .blend file storage (instant application)")
        else:
            logger.warning("⚠️ Blender using legacy storage (slow application)")
    
    def _on_scene_info(self, message: Message):
        """Handle scene info response"""
        self.scene_info_received.emit(message.data)
    
    def _on_selection_update(self, message: Message):
        """Handle selection update"""
        self.selection_updated.emit(message.data)
    
    def _on_animation_extracted(self, message: Message):
        """Handle animation extraction result"""
        # Log extraction performance
        storage_method = message.data.get('storage_method', 'unknown')
        extraction_time = message.data.get('extraction_time_seconds', 0)
        
        logger.info(f"Animation extracted using {storage_method} method in {extraction_time:.1f}s")
        
        self.animation_extracted.emit(message.data)
    
    def _on_animation_applied(self, message: Message):
        """Handle animation application result"""
        # Log application performance
        storage_method = message.data.get('source_method', 'unknown')
        application_time = message.data.get('application_time_seconds', 0)
        
        logger.info(f"Animation applied using {storage_method} method in {application_time:.1f}s")
        
        self.animation_applied.emit(message.data)
    
    def _on_thumbnail_updated(self, message: Message):
        """Handle thumbnail updated response from Blender"""
        try:
            animation_name = message.data.get("animation_name")
            status = message.data.get("status")
            
            if animation_name and status == "success":
                logger.info(f"✅ Thumbnail updated successfully for: {animation_name}")
                self.thumbnail_updated.emit(animation_name)
                print(f"📤 Emitted thumbnail_updated signal for: {animation_name}")
        except Exception as e:
            logger.error(f"❌ Error handling thumbnail update response: {e}")
    
    def refresh_thumbnail(self, animation_name: str):
        """Refresh thumbnail for the specified animation"""
        # This will trigger GUI refresh - signal is emitted above
        # Individual widget refresh is handled by the signal connections
        logger.info(f"Refreshing thumbnail for: {animation_name}")
    
    def _on_error(self, message: Message):
        """Handle error from Blender"""
        error_msg = message.data.get('message', 'Unknown error')
        error_type = message.data.get('error_type', 'general')
        
        logger.error(f"Blender error ({error_type}): {error_msg}")
        self.error_received.emit(error_msg)
    
    def _on_connection_error(self, error_msg: str):
        """Handle connection errors"""
        logger.error(f"Connection error: {error_msg}")
        self.connection_error.emit(error_msg)