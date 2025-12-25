"""
GUI module for AI Dev IDE
"""

from .ai_panel import AIPanel
from .editor_tabs import EditorTabs
from .output_panels import BottomPanel
from .project_tree import ProjectTree
from .settings_window import SettingsWindow

__all__ = [
    'AIPanel',
    'EditorTabs',
    'BottomPanel',
    'ProjectTree',
    'SettingsWindow'
]