"""
Communication protocol for Blender Animation Library.
EXISTING SCRIPT: src/core/communication.py (FIXED INDENTATION)

Enhanced to handle .blend file storage and provide performance monitoring.
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
    
    # NEW: .blend file specific commands
    CHECK_BLEND_FILE = "check_blend_file"
    MIGRATE_ANIMATION = "migrate_animation"
    GET_PERFORMANCE_INFO = "get_performance_info"
    
    # Responses (Blender -> GUI)
    PONG = "pong"
    SCENE_INFO = "scene_info"
    SELECTION_UPDATE = "selection_update"
    ANIMATION_EXTRACTED = "animation_extracted"
    ANIMATION_APPLIED = "animation_applied"
    
    # NEW: .blend file responses
    BLEND_FILE_STATUS = "blend_file_status"
    MIGRATION_COMPLETE = "migration_complete"
    PERFORMANCE_INFO = "performance_info"


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
    
    # NEW: Performance monitoring
    enable_performance_monitoring: bool = True
    log_message_timing: bool = False


class Message:
    """Represents a communication message with performance tracking"""
    
    def __init__(self, msg_type: str, data: Optional[Dict[str, Any]] = None):
        self.type = msg_type
        self.data = data or {}
        self.timestamp = time.time()
        self.performance_data = {}  # NEW: For tracking message performance
    
    def add_performance_data(self, **kwargs):
        """Add performance metrics to message"""
        self.performance_data.update(kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        result = {
            "type": self.type,
            "timestamp": self.timestamp,
            **self.data
        }
        
        # Include performance data if present
        if self.performance_data:
            result["performance"] = self.performance_data
        
        return result
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string"""
        data = json.loads(json_str)
        msg_type = data.pop('type')
        timestamp = data.pop('timestamp', time.time())
        performance_data = data.pop('performance', {})
        
        message = cls(msg_type, data)
        message.timestamp = timestamp
        message.performance_data = performance_data
        return message
    
    @classmethod
    def command(cls, command: str, **kwargs) -> 'Message':
        """Create a command message"""
        return cls("command", {"command": command, **kwargs})
    
    @classmethod
    def response(cls, response_type: str, **kwargs) -> 'Message':
        """Create a response message"""
        return cls(response_type, kwargs)
    
    @classmethod
    def blend_file_command(cls, command: str, animation_data: Dict[str, Any], **kwargs) -> 'Message':
        """Create a .blend file specific command"""
        data = {
            "command": command,
            "animation_data": animation_data,
            "storage_method": "blend_file",
            **kwargs
        }
        message = cls("command", data)
        message.add_performance_data(expected_time=0.5, storage_type="blend_file")
        return message


class MessageBuffer:
    """Handles message buffering and framing with performance monitoring"""
    
    def __init__(self, delimiter: str = "\n###END_MESSAGE###\n"):
        self.delimiter = delimiter
        self.buffer = ""
        self.message_count = 0
        self.bytes_processed = 0
        self.start_time = time.time()
    
    def add_data(self, data: str):
        """Add data to buffer"""
        self.buffer += data
        self.bytes_processed += len(data)
    
    def get_complete_messages(self) -> List[str]:
        """Extract complete messages from buffer"""
        messages = []
        
        while self.delimiter in self.buffer:
            message_end = self.buffer.find(self.delimiter)
            complete_message = self.buffer[:message_end].strip()
            self.buffer = self.buffer[message_end + len(self.delimiter):].strip()
            
            if complete_message:
                messages.append(complete_message)
                self.message_count += 1
        
        return messages
    
    def get_stats(self) -> Dict[str, Any]:
        """Get buffer performance statistics"""
        elapsed_time = time.time() - self.start_time
        return {
            "messages_processed": self.message_count,
            "bytes_processed": self.bytes_processed,
            "messages_per_second": self.message_count / elapsed_time if elapsed_time > 0 else 0,
            "buffer_size": len(self.buffer)
        }
    
    def clear(self):
        """Clear the buffer and reset stats"""
        self.buffer = ""
        self.message_count = 0
        self.bytes_processed = 0
        self.start_time = time.time()


class PerformanceMonitor:
    """NEW: Monitors communication and animation performance"""
    
    def __init__(self):
        self.message_times = {}
        self.animation_stats = {
            "extractions": [],
            "applications": [],
            "blend_file_operations": [],
            "json_operations": []
        }
    
    def start_operation(self, operation_id: str, operation_type: str):
        """Start timing an operation"""
        self.message_times[operation_id] = {
            "start_time": time.time(),
            "type": operation_type
        }
    
    def end_operation(self, operation_id: str, success: bool = True, **kwargs):
        """End timing an operation"""
        if operation_id in self.message_times:
            start_data = self.message_times[operation_id]
            duration = time.time() - start_data["start_time"]
            
            result = {
                "duration": duration,
                "success": success,
                "type": start_data["type"],
                **kwargs
            }
            
            # Categorize by operation type
            if start_data["type"] in ["extract_animation", "apply_animation"]:
                storage_method = kwargs.get("storage_method", "unknown")
                if storage_method == "blend_file":
                    self.animation_stats["blend_file_operations"].append(result)
                else:
                    self.animation_stats["json_operations"].append(result)
            
            del self.message_times[operation_id]
            return result
        return None
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for display"""
        blend_ops = self.animation_stats["blend_file_operations"]
        json_ops = self.animation_stats["json_operations"]
        
        summary = {
            "total_operations": len(blend_ops) + len(json_ops),
            "blend_file_operations": len(blend_ops),
            "json_operations": len(json_ops)
        }
        
        if blend_ops:
            avg_blend_time = sum(op["duration"] for op in blend_ops) / len(blend_ops)
            summary["avg_blend_time"] = avg_blend_time
            summary["blend_success_rate"] = sum(1 for op in blend_ops if op["success"]) / len(blend_ops)
        
        if json_ops:
            avg_json_time = sum(op["duration"] for op in json_ops) / len(json_ops)
            summary["avg_json_time"] = avg_json_time
            summary["json_success_rate"] = sum(1 for op in json_ops if op["success"]) / len(json_ops)
        
        if blend_ops and json_ops:
            summary["performance_improvement"] = avg_json_time / avg_blend_time if avg_blend_time > 0 else 1
        
        return summary


class SocketCommunicator:
    """Base class for socket communication with performance monitoring"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.message_buffer = MessageBuffer(config.message_delimiter)
        self.message_handlers: Dict[str, Callable] = {}
        self.error_handlers: List[Callable] = []
        
        # NEW: Performance monitoring
        self.performance_monitor = PerformanceMonitor() if config.enable_performance_monitoring else None
        self.last_message_time = time.time()
        
    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler"""
        self.message_handlers[message_type] = handler
    
    def register_error_handler(self, handler: Callable):
        """Register an error handler"""
        self.error_handlers.append(handler)
    
    def send_message(self, message: Message) -> bool:
        """Send a message through the socket with performance tracking"""
        if not self.connected or not self.socket:
            logger.warning("Cannot send message: not connected")
            return False
        
        try:
            # Start performance tracking
            operation_id = f"{message.type}_{time.time()}"
            if self.performance_monitor:
                self.performance_monitor.start_operation(operation_id, message.type)
            
            json_str = message.to_json()
            framed_message = json_str + self.config.message_delimiter
            self.socket.send(framed_message.encode('utf-8'))
            
            # End performance tracking
            if self.performance_monitor:
                message_size = len(framed_message)
                self.performance_monitor.end_operation(
                    operation_id, 
                    success=True,
                    message_size=message_size,
                    storage_method=message.data.get('storage_method', 'unknown')
                )
            
            if self.config.log_message_timing:
                logger.debug(f"Sent message: {message.type} ({len(framed_message)} bytes)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            if self.performance_monitor:
                self.performance_monitor.end_operation(operation_id, success=False, error=str(e))
            self._handle_error(f"Send error: {e}")
            return False
    
    def _process_received_data(self, data: bytes):
        """Process received data with performance tracking"""
        try:
            text_data = data.decode('utf-8')
            self.message_buffer.add_data(text_data)
            
            # Process complete messages
            complete_messages = self.message_buffer.get_complete_messages()
            for message_str in complete_messages:
                try:
                    message_start_time = time.time()
                    message = Message.from_json(message_str)
                    
                    # Add processing time to performance data
                    processing_time = time.time() - message_start_time
                    message.add_performance_data(processing_time=processing_time)
                    
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
                
                # Log performance for animation operations
                if (self.performance_monitor and 
                    message.type in ["animation_extracted", "animation_applied"] and
                    "performance" in message.data):
                    
                    perf_data = message.data["performance"]
                    storage_method = message.data.get("storage_method", "unknown")
                    
                    logger.info(f"Animation {message.type}: {storage_method} method, "
                              f"took {perf_data.get('duration', 'unknown')}s")
                
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
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get communication performance statistics"""
        stats = {
            "connected": self.connected,
            "buffer_stats": self.message_buffer.get_stats()
        }
        
        if self.performance_monitor:
            stats["performance"] = self.performance_monitor.get_performance_summary()
        
        return stats
    
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
    """Client connection to Blender with .blend file support"""
    
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
    
    # Command methods with .blend file support
    def ping(self) -> bool:
        """Send ping command"""
        return self.send_message(Message.command("ping"))
    
    def get_scene_info(self) -> bool:
        """Request scene information"""
        return self.send_message(Message.command("get_scene_info"))
    
    def extract_animation(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Request animation extraction (uses .blend file storage by default)"""
        extract_options = options or {}
        extract_options.setdefault('storage_method', 'blend_file')  # Default to .blend files
        extract_options.setdefault('prefer_blend_storage', True)
        
        message = Message.command("extract_animation", **extract_options)
        message.add_performance_data(expected_method="blend_file", expected_time=1.5)
        
        return self.send_message(message)
    
    def apply_animation(self, animation_data: Dict[str, Any], apply_options: Dict[str, Any]) -> bool:
        """Apply animation to Blender (optimized for .blend files)"""
        # Detect storage method and set performance expectations
        storage_method = animation_data.get('storage_method', 'json_keyframes')
        
        message = Message.blend_file_command("apply_animation", animation_data, **apply_options)
        
        if storage_method == 'blend_file':
            message.add_performance_data(expected_time=0.5, optimization="blend_file_direct")
        else:
            message.add_performance_data(expected_time=30.0, optimization="json_recreation")
        
        return self.send_message(message)
    
    def check_blend_file(self, blend_filename: str) -> bool:
        """Check if .blend file exists and is valid"""
        return self.send_message(Message.command("check_blend_file", blend_filename=blend_filename))
    
    def migrate_animation(self, animation_id: str) -> bool:
        """Request migration of JSON animation to .blend file"""
        return self.send_message(Message.command("migrate_animation", animation_id=animation_id))
    
    def get_performance_info(self) -> bool:
        """Request performance information from Blender"""
        return self.send_message(Message.command("get_performance_info"))
    
    def update_thumbnail(self, animation_id: str) -> bool:
        """Request thumbnail update for a specific animation"""
        return self.send_message(Message.command("update_thumbnail", animation_id=animation_id))


class BlenderServer(SocketCommunicator):
    """Server running in Blender with .blend file optimization"""
    
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
            logger.info("🚀 Enhanced with .blend file storage for instant animation application!")
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
                        
                        # Send connection confirmation with performance info
                        connection_msg = Message.response("connected", 
                                                        status="success",
                                                        features=["blend_file_storage", "instant_application"])
                        self.send_message(connection_msg)
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
    
    # Enhanced response methods with performance data
    def send_scene_info(self, scene_data: Dict[str, Any]) -> bool:
        """Send scene information"""
        message = Message.response("scene_info", **scene_data)
        return self.send_message(message)
    
    def send_selection_update(self, selection_data: Dict[str, Any]) -> bool:
        """Send selection update"""
        message = Message.response("selection_update", **selection_data)
        return self.send_message(message)
    
    def send_animation_extracted(self, animation_data: Dict[str, Any]) -> bool:
        """Send animation extraction result with performance data"""
        storage_method = animation_data.get('storage_method', 'blend_file')
        extraction_time = animation_data.get('extraction_time_seconds', 1.5)
        
        message = Message.response("animation_extracted", **animation_data)
        message.add_performance_data(
            storage_method=storage_method,
            extraction_time=extraction_time,
            performance_level="instant" if storage_method == "blend_file" else "slow"
        )
        
        return self.send_message(message)
    
    def send_animation_applied(self, result_data: Dict[str, Any]) -> bool:
        """Send animation application result with performance data"""
        application_time = result_data.get('application_time_seconds', 0.5)
        storage_method = result_data.get('source_method', 'blend_file')
        
        message = Message.response("animation_applied", **result_data)
        message.add_performance_data(
            storage_method=storage_method,
            application_time=application_time,
            performance_level="instant" if application_time < 2.0 else "slow"
        )
        
        return self.send_message(message)
    
    def send_performance_info(self, performance_data: Dict[str, Any]) -> bool:
        """Send performance information"""
        message = Message.response("performance_info", **performance_data)
        return self.send_message(message)
    
    def send_error(self, error_msg: str, error_type: str = "general") -> bool:
        """Send error message with context"""
        message = Message.response("error", message=error_msg, error_type=error_type)
        return self.send_message(message)


# NEW: Utility functions for .blend file communication
def create_blend_file_message(command: str, animation_data: Dict[str, Any], **kwargs) -> Message:
    """Create a message optimized for .blend file operations"""
    message = Message.command(command, animation_data=animation_data, **kwargs)
    message.add_performance_data(
        storage_method="blend_file",
        expected_performance="instant"
    )
    return message

def detect_message_performance_level(message: Message) -> str:
    """Detect expected performance level from message"""
    if message.data.get('storage_method') == 'blend_file':
        return "instant"
    elif message.data.get('storage_method') == 'json_keyframes':
        return "slow"
    else:
        return "unknown"