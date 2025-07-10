"""
Blender Animation Library Add-on
Refactored version with clean architecture and proper apply options
"""

import bpy
import sys
import os
from pathlib import Path

# Add the core modules to path
addon_dir = Path(__file__).parent.parent
if str(addon_dir) not in sys.path:
    sys.path.insert(0, str(addon_dir))

from core.communication import BlenderServer, ConnectionConfig, Message
from core.animation_data import AnimationMetadata, ApplyOptions
from bpy.types import Operator, Panel, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty
import logging

bl_info = {
    "name": "Animation Library Socket Server",
    "author": "Animation Library Team",
    "version": (2, 0, 0),
    "blender": (3, 0, 0),
    "location": "3D Viewport > Sidebar > Animation Library",
    "description": "Professional animation library system with socket server",
    "category": "Animation",
}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global server instance
animation_server = None


class AnimationLibraryServer:
    """Main server class for handling animation library operations"""
    
    def __init__(self, host='127.0.0.1', port=8080):
        self.config = ConnectionConfig(host=host, port=port)
        self.server = BlenderServer(self.config)
        self.last_selection = set()
        
        # Register message handlers
        self.server.register_handler("command", self._handle_command)
        self.server.register_error_handler(self._handle_error)
        
    def start_server(self) -> bool:
        """Start the animation library server"""
        if self.server.start_server():
            # Register Blender timer for handling connections
            bpy.app.timers.register(self.server.handle_connections, first_interval=0.1)
            bpy.app.timers.register(self._monitor_selection, first_interval=0.1)
            logger.info("Animation Library server started successfully")
            return True
        return False
    
    def stop_server(self):
        """Stop the animation library server"""
        self.server.stop_server()
        logger.info("Animation Library server stopped")
    
    def _handle_command(self, message: Message):
        """Handle incoming commands"""
        command = message.data.get('command')
        logger.info(f"Processing command: {command}")
        
        if command == 'ping':
            self._handle_ping(message)
        elif comman