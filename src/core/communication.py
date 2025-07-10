"""
Communication protocol for Blender Animation Library.
Handles socket communication between GUI and Blender add-on.
"""

import json
import socket
import threading
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Message types for communication protocol"""
    # Connection
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    
    # Commands (GUI -> Blender)
    PING = "ping"
    GET_SCENE_INFO = "get_scene_info"
    EXTRACT_ANIMATION = "extract_animation"
    APPLY_ANIMATION = "apply_animation"
    
    # Responses (Blender -> GUI)
    PONG = "pong"
    SCENE_INFO = "scene_info"
    SELECTION_UPDATE = "selection_update"
    ANIMATION_EXTRACTED = "animation_extracted"
    ANIMATION_APPLIED = "animation_applied"


@dataclass
class ConnectionConfig:
    """Configuration for socket connection"""
    host: str = "127.0.0.1"
    port: int = 8080
    timeout: float = 5.0
    buffer_size: int = 4096
    message_delimiter: str = "\n###END_MESSAGE###\n"
    reconnect_attempts: int = 3
    reconnect_delay: float = 2.0


class Message:
    """Represents a communication message"""
    
    def __init__(self, msg_type: str, data: Optional[Dict[str, Any]] = None):
        self.type = msg_type
        self.data = data or {}
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "type": self.type,
            "timestamp": self.timestamp,
            **self.data
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string"""
        data = json.loads(json_str)
        msg_type = data.pop('type')
        timestamp = data.pop('timestamp', time.time())
        
        message = cls(msg_type, data)
        message.timestamp = timestamp
        return message
    
    @classmethod
    def command(cls, command: str, **kwargs) -> 'Message':
        """Create a command message"""
        return cls("command", {"command": command, **kwargs})
    
    @classmethod
    def response(cls, response_type: str, **kwargs) -> 'Message':
        """Create a response message"""
        return cls(response_type, kwargs)


class MessageBuffer:
    """Handles message buffering and framing"""
    
    def __init__(self, delimiter: str = "\n###END_MESSAGE###\n"):
        self.delimiter = delimiter
        self.buffer = ""
    
    def add_data(self, data: str):
        """Add data to buffer"""
        self.buffer += data
    
    def get_complete_messages(self) -> List[str]:
        """Extract complete messages from buffer"""
        messages = []
        
        while self.delimiter in self.buffer:
            message_end = self.buffer.find(self.delimiter)
            complete_message = self.buffer[:message_end].strip()
            self.buffer = self.buffer[message_end + len(self.delimiter):].strip()
            
            if complete_message:
                messages.append(complete_message)
        
        return messages
    
    def clear(self):
        """Clear the buffer"""
        self.buffer = ""


class SocketCommunicator:
    """Base class for socket communication"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.message_buffer = MessageBuffer(config.message_delimiter)
        self.message_handlers: Dict[str, Callable] = {}
        self.error_handlers: List[Callable] = []
        
    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler"""
        self.message_handlers[message_type] = handler
    
    def register_error_handler(self, handler: Callable):
        """Register an error handler"""
        self.error_handlers.append(handler)
    
    def send_message(self, message: Message) -> bool:
        """Send a message through the socket"""
        if not self.connected or not self.socket:
            logger.warning("Cannot send message: not connected")
            return False
        
        try:
            json_str = message.to_json()
            framed_message = json_str + self.config.message_delimiter
            self.socket.send(framed_message.encode('utf-8'))
            logger.debug(f"Sent message: {message.type}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self._handle_error(f"Send error: {e}")
            return False
    
    def _process_received_data(self, data: bytes):
        """Process received data"""
        try:
            text_data = data.decode('utf-8')
            self.message_buffer.add_data(text_data)
            
            # Process complete messages
            complete_messages = self.message_buffer.get_complete_messages()
            for message_str in complete_messages:
                try:
                    message = Message.from_json(message_str)
                    self._handle_message(message)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    self._handle_error(f"Invalid JSON: {e}")
                    
        except Exception as e:
            logger.error(f"Data processing error: {e}")
            self._handle_error(f"Data processing error: {e}")
    
    def _handle_message(self, message: Message):
        """Handle a received message"""
        handler = self.message_handlers.get(message.type)
        if handler:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")
                self._handle_error(f"Handler error: {e}")
        else:
            logger.warning(f"No handler for message type: {message.type}")
    
    def _handle_error(self, error_msg: str):
        """Handle errors"""
        for handler in self.error_handlers:
            try:
                handler(error_msg)
            except Exception as e:
                logger.error(f"Error handler failed: {e}")
    
    def disconnect(self):
        """Disconnect from socket"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.message_buffer.clear()
        logger.info("Disconnected")


class BlenderConnection(SocketCommunicator):
    """Client connection to Blender"""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.running = False
        self.listen_thread: Optional[threading.Thread] = None
    
    def connect(self) -> bool:
        """Connect to Blender"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.config.timeout)
            self.socket.connect((self.config.host, self.config.port))
            
            self.connected = True
            self.running = True
            
            # Start listening thread
            self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listen_thread.start()
            
            logger.info(f"Connected to Blender at {self.config.host}:{self.config.port}")
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._handle_error(f"Connection failed: {e}")
            return False
    
    def _listen_loop(self):
        """Main listening loop"""
        while self.running and self.connected:
            try:
                data = self.socket.recv(self.config.buffer_size)
                if data:
                    self._process_received_data(data)
                else:
                    logger.info("Connection closed by Blender")
                    self.connected = False
                    break
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Listen error: {e}")
                    self._handle_error(f"Listen error: {e}")
                break
        
        self.connected = False
        logger.info("Listen loop ended")
    
    def disconnect(self):
        """Disconnect from Blender"""
        self.running = False
        super().disconnect()
        
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1.0)
    
    # Command methods
    def ping(self) -> bool:
        """Send ping command"""
        return self.send_message(Message.command("ping"))
    
    def get_scene_info(self) -> bool:
        """Request scene information"""
        return self.send_message(Message.command("get_scene_info"))
    
    def extract_animation(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Request animation extraction"""
        return self.send_message(Message.command("extract_animation", **(options or {})))
    
    def apply_animation(self, animation_data: Dict[str, Any], apply_options: Dict[str, Any]) -> bool:
        """Apply animation to Blender"""
        return self.send_message(Message.command("apply_animation", 
                                                animation_data=animation_data,
                                                **apply_options))


class BlenderServer(SocketCommunicator):
    """Server running in Blender"""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.server_socket: Optional[socket.socket] = None
        self.running = False
    
    def start_server(self) -> bool:
        """Start the server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.setblocking(False)
            self.server_socket.bind((self.config.host, self.config.port))
            self.server_socket.listen(1)
            
            self.running = True
            logger.info(f"Server started on {self.config.host}:{self.config.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            self._handle_error(f"Server start failed: {e}")
            return False
    
    def handle_connections(self):
        """Handle incoming connections (called from Blender timer)"""
        if not self.running:
            return None
        
        try:
            # Accept new connections
            if not self.connected:
                try:
                    import select
                    ready, _, _ = select.select([self.server_socket], [], [], 0)
                    if ready:
                        client_socket, addr = self.server_socket.accept()
                        client_socket.setblocking(False)
                        
                        self.socket = client_socket
                        self.connected = True
                        
                        # Send connection confirmation
                        self.send_message(Message.response("connected", status="success"))
                        logger.info(f"Client connected: {addr}")
                        
                except socket.error:
                    pass
            
            # Handle client messages
            if self.connected and self.socket:
                try:
                    import select
                    ready, _, _ = select.select([self.socket], [], [], 0)
                    if ready:
                        data = self.socket.recv(self.config.buffer_size)
                        if data:
                            self._process_received_data(data)
                        else:
                            logger.info("Client disconnected")
                            self.socket.close()
                            self.socket = None
                            self.connected = False
                            self.message_buffer.clear()
                            
                except socket.error as e:
                    logger.error(f"Client communication error: {e}")
                    if self.socket:
                        self.socket.close()
                        self.socket = None
                    self.connected = False
                    self.message_buffer.clear()
                    
        except Exception as e:
            logger.error(f"Server error: {e}")
            self._handle_error(f"Server error: {e}")
        
        return 0.1  # Return interval for next check
    
    def stop_server(self):
        """Stop the server"""
        self.running = False
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
            
        self.connected = False
        self.message_buffer.clear()
        logger.info("Server stopped")
    
    # Response methods
    def send_scene_info(self, scene_data: Dict[str, Any]) -> bool:
        """Send scene information"""
        return self.send_message(Message.response("scene_info", **scene_data))
    
    def send_selection_update(self, selection_data: Dict[str, Any]) -> bool:
        """Send selection update"""
        return self.send_message(Message.response("selection_update", **selection_data))
    
    def send_animation_extracted(self, animation_data: Dict[str, Any]) -> bool:
        """Send animation extraction result"""
        return self.send_message(Message.response("animation_extracted", **animation_data))
    
    def send_animation_applied(self, result_data: Dict[str, Any]) -> bool:
        """Send animation application result"""
        return self.send_message(Message.response("animation_applied", **result_data))
    
    def send_error(self, error_msg: str) -> bool:
        """Send error message"""
        return self.send_message(Message.response("error", message=error_msg))