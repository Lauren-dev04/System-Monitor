"""
Hardware module for System Monitor application.
Contains functions to read system hardware data.
"""

# Import hardware monitoring functions for easier access
from .monitor import get_cpu_info, get_ram_info, get_gpu_info, get_disk_info

# Define public API
__all__ = ['get_cpu_info', 'get_ram_info', 'get_gpu_info', 'get_disk_info']
