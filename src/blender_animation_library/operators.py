"""
Animation Library Operators - Modular Structure
Main registration point for all operator modules

This file has been refactored into a modular structure:
- ops/server_ops.py - Server-related operators  
- ops/library_ops.py - Library management operators
- ops/thumbnail_ops.py - Thumbnail-related operators
- ops/utils.py - Shared utility functions
- ops/__init__.py - Registration coordination

All functionality is preserved with cleaner organization.
"""

# Import everything from the ops package
from .ops import *

# The register and unregister functions are now available from the ops package
# All operator classes and utility functions are also available