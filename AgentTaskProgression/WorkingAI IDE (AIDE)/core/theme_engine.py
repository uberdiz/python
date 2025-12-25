"""
Theme Engine - Controls all UI colors
"""
import tkinter as tk
from tkinter import ttk

class ThemeEngine:
    def __init__(self, root):
        self.root = root
        self.color_map = self.create_dark_theme()
        self.setup_styles()
    
    def create_dark_theme(self):
        """Create a modern dark theme"""
        return {
            "window_bg": "#1e1e1e",
            "window_fg": "#d4d4d4",
            "editor_bg": "#1e1e1e",
            "editor_fg": "#d4d4d4",
            "editor_cursor": "#aeafad",
            "editor_selection": "#264f78",
            "editor_gutter": "#1e1e1e",
            "editor_gutter_fg": "#858585",
            "editor_line_highlight": "#2d2d30",
            "syntax_keyword": "#569cd6",
            "syntax_string": "#ce9178",
            "syntax_comment": "#6a9955",
            "syntax_function": "#dcdcaa",
            "syntax_number": "#b5cea8",
            "syntax_builtin": "#4ec9b0",
            "syntax_class": "#4ec9b0",
            "syntax_variable": "#9cdcfe",
            "tree_bg": "#252526",
            "tree_fg": "#cccccc",
            "tree_selection": "#094771",
            "panel_bg": "#2d2d30",
            "panel_fg": "#cccccc",
            "panel_border": "#3e3e42",
            "button_bg": "#0e639c",
            "button_fg": "#ffffff",
            "button_hover": "#1177bb",
            "tab_hover": "#333337",
            "tree_hover": "#2a2d2e",
            "text_bg": "#1e1e1e",
            "text_fg": "#d4d4d4",
            "text_insert": "#ffffff",
            "entry_bg": "#3c3c3c",
            "entry_fg": "#cccccc",
            "entry_border": "#007acc",
            "scroll_bg": "#424242",
            "scroll_trough": "#2d2d30",
            "tab_bg": "#2d2d30",
            "tab_fg": "#cccccc",
            "tab_selected": "#1e1e1e",
            "tab_selected_fg": "#ffffff",
            "menu_bg": "#252526",
            "menu_fg": "#cccccc",
            "menu_selection": "#094771",
            "status_bg": "#007acc",
            "status_fg": "#ffffff",
            "console_bg": "#0c0c0c",
            "console_fg": "#cccccc",
            "console_error": "#f44747",
            "console_success": "#4ec9b0",
            "activity_bar_bg": "#333333",
            "activity_bar_fg": "#858585",
            "activity_bar_active": "#007acc",
            "activity_bar_hover": "#cccccc",
        }
    
    def create_light_theme(self):
        """Create a light theme"""
        return {
            "window_bg": "#f3f3f3",
            "window_fg": "#000000",
            "editor_bg": "#ffffff",
            "editor_fg": "#000000",
            "editor_cursor": "#000000",
            "editor_selection": "#add6ff",
            "editor_gutter": "#f0f0f0",
            "editor_gutter_fg": "#333333",
            "editor_line_highlight": "#f5f5f5",
            "syntax_keyword": "#0000ff",
            "syntax_string": "#a31515",
            "syntax_comment": "#008000",
            "syntax_function": "#795e26",
            "syntax_number": "#098658",
            "syntax_builtin": "#267f99",
            "syntax_class": "#267f99",
            "tree_bg": "#f5f5f5",
            "tree_fg": "#000000",
            "tree_selection": "#cce8ff",
            "panel_bg": "#f0f0f0",
            "panel_fg": "#000000",
            "text_bg": "#ffffff",
            "text_fg": "#000000",
            "button_bg": "#0078d4",
            "button_fg": "#ffffff",
            "button_hover": "#2b88d8"
        }

    def create_nordic_theme(self):
        """Create a soft blue/grey Nordic theme"""
        return {
            "window_bg": "#2e3440",
            "window_fg": "#d8dee9",
            "editor_bg": "#2e3440",
            "editor_fg": "#d8dee9",
            "editor_cursor": "#d8dee9",
            "editor_selection": "#434c5e",
            "editor_gutter": "#2e3440",
            "editor_gutter_fg": "#4c566a",
            "syntax_keyword": "#81a1c1",
            "syntax_string": "#a3be8c",
            "syntax_comment": "#616e88",
            "syntax_function": "#88c0d0",
            "syntax_number": "#b48ead",
            "tree_bg": "#3b4252",
            "tree_fg": "#d8dee9",
            "button_bg": "#5e81ac",
            "button_fg": "#eceff4",
            "button_hover": "#81a1c1",
            "panel_bg": "#3b4252",
            "status_bg": "#5e81ac"
        }

    def create_cyberpunk_theme(self):
        """Create a vibrant Cyberpunk theme"""
        return {
            "window_bg": "#000b1e",
            "window_fg": "#00ff9f",
            "editor_bg": "#000b1e",
            "editor_fg": "#00ff9f",
            "editor_cursor": "#ff0055",
            "editor_selection": "#ff0055",
            "editor_gutter": "#000b1e",
            "editor_gutter_fg": "#00b8ff",
            "syntax_keyword": "#ff0055",
            "syntax_string": "#f3f315",
            "syntax_comment": "#00b8ff",
            "syntax_function": "#f3f315",
            "syntax_number": "#ff0055",
            "tree_bg": "#001233",
            "tree_fg": "#00ff9f",
            "button_bg": "#ff0055",
            "button_fg": "#ffffff",
            "button_hover": "#ff3377",
            "panel_bg": "#001233",
            "status_bg": "#ff0055"
        }

    def create_nebula_theme(self):
        """Create a deep space Nebula theme"""
        return {
            "window_bg": "#0b0e14",
            "window_fg": "#b3b1ad",
            "editor_bg": "#0b0e14",
            "editor_fg": "#b3b1ad",
            "editor_cursor": "#f29718",
            "editor_selection": "#253340",
            "editor_gutter": "#0b0e14",
            "editor_gutter_fg": "#5c6773",
            "syntax_keyword": "#ff7733",
            "syntax_string": "#91b362",
            "syntax_comment": "#5c6773",
            "syntax_function": "#f29718",
            "syntax_number": "#ffb454",
            "tree_bg": "#0f131a",
            "tree_fg": "#b3b1ad",
            "button_bg": "#f29718",
            "button_fg": "#0b0e14",
            "button_hover": "#ffb454",
            "panel_bg": "#0f131a",
            "status_bg": "#f29718"
        }
    
    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style(self.root)
        style.theme_use('clam')
        
        # Frame
        style.configure('TFrame', background=self.color_map["window_bg"])
        
        # Label
        style.configure('TLabel', 
                       background=self.color_map["window_bg"],
                       foreground=self.color_map["window_fg"])
        
        # Button
        style.configure('TButton',
                       background=self.color_map["button_bg"],
                       foreground=self.color_map["button_fg"],
                       borderwidth=1,
                       focusthickness=3,
                       focuscolor='none')
        style.map('TButton',
                 background=[('active', self.color_map.get("button_hover", self.color_map["button_bg"])), 
                            ('hover', self.color_map.get("button_hover", self.color_map["button_bg"]))])
        
        # Entry
        style.configure('TEntry',
                       fieldbackground=self.color_map["entry_bg"],
                       foreground=self.color_map["entry_fg"],
                       borderwidth=1,
                       insertcolor=self.color_map["editor_cursor"])
        
        # Notebook (Tabs)
        style.configure('TNotebook',
                       background=self.color_map["tab_bg"],
                       tabmargins=[2, 5, 2, 0])
        style.configure('TNotebook.Tab',
                       background=self.color_map["tab_bg"],
                       foreground=self.color_map["tab_fg"],
                       padding=[10, 2],
                       borderwidth=2)
        style.map('TNotebook.Tab',
                 background=[('selected', self.color_map["tab_selected"]),
                            ('active', self.color_map.get("tab_hover", self.color_map["tab_bg"]))],
                 foreground=[('selected', self.color_map["tab_selected_fg"]),
                            ('active', self.color_map.get("tab_fg", "#ffffff"))])
        
        # Scrollbar
        style.configure('Vertical.TScrollbar',
                       background=self.color_map["scroll_bg"],
                       troughcolor=self.color_map["scroll_trough"],
                       borderwidth=0,
                       arrowsize=14)
        
        # Treeview
        style.configure('Treeview',
                       background=self.color_map.get("tree_bg", self.color_map["window_bg"]),
                       foreground=self.color_map.get("tree_fg", self.color_map["window_fg"]),
                       fieldbackground=self.color_map.get("tree_bg", self.color_map["window_bg"]),
                       rowheight=25,
                       borderwidth=0)
        style.map('Treeview',
                 background=[('selected', self.color_map.get("tree_selection", "#094771")),
                            ('active', self.color_map.get("tree_hover", "#2a2d2e"))],
                 foreground=[('selected', self.color_map.get("tree_fg", "#ffffff"))])
                 
        # Action Button (More prominent)
        style.configure('Action.TButton',
                       background=self.color_map["status_bg"],
                       foreground=self.color_map["status_fg"],
                       font=("Segoe UI", 9, "bold"))
                       
        # Action Frame (for bars/headers)
        style.configure('Action.TFrame', background=self.color_map.get("status_bg", "#007acc"))
        
        # Action Label
        style.configure('Action.TLabel', 
                       background=self.color_map.get("status_bg", "#007acc"),
                       foreground=self.color_map.get("status_fg", "#ffffff"))
        
        # Mode Switcher buttons
        style.configure('Action.TRadiobutton',
                       background=self.color_map["panel_bg"],
                       foreground=self.color_map["panel_fg"],
                       padding=5)
                       
        # Accent Button
        style.configure('Accent.TButton', font=("Segoe UI", 9, "bold"))
        style.map('Accent.TButton',
                 background=[('active', '#107acc'), ('!disabled', '#007acc')],
                 foreground=[('!disabled', '#ffffff')])
                 
        # Ghost Button
        style.configure('Ghost.TButton', borderwidth=0, relief="flat")
        style.map('Ghost.TButton',
                 background=[('active', '#0e6d9c'), ('!disabled', self.color_map.get("status_bg", "#007acc"))],
                 foreground=[('!disabled', '#ffffff')])
    
    def apply_theme(self, theme_colors):
        """Apply theme to all widgets"""
        self.color_map.update(theme_colors)
        self.setup_styles()
        return self.color_map
    
    def get_theme(self):
        """Get current theme"""
        return self.color_map