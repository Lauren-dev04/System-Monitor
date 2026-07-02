"""
UI module for System Monitor application.
Contains all user interface components.
"""

# Import UI classes for easier access
from .main_window import MainWindow
from .sidebar import Sidebar

# Define public API
__all__ = ['MainWindow', 'Sidebar']
