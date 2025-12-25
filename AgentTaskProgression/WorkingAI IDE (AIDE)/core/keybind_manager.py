"""
Keybind Manager - Customizable keyboard shortcuts
"""
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

# Default keybinds
DEFAULT_KEYBINDS = {
    "run_file": "<F5>",
    "save_file": "<Control-s>",
    "open_search": "<Control-f>",
    "open_settings": "<Control-comma>",
    "new_project": "<Control-n>",
    "open_project": "<Control-o>",
    "close_tab": "<Control-w>",
    "toggle_terminal": "<Control-grave>"
}

class KeybindManager:
    """Manages customizable keyboard shortcuts"""
    
    def __init__(self, app):
        self.app = app
        self.keybinds = {}
        self.actions = {}
        
        self.load_keybinds()
        self.register_default_actions()
        self.bind_all()
        
    def get_keybind_path(self):
        """Get keybinds file path"""
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "keybinds.json")
        
    def load_keybinds(self):
        """Load keybinds from file or use defaults"""
        path = self.get_keybind_path()
        
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.keybinds = json.load(f)
            except:
                self.keybinds = DEFAULT_KEYBINDS.copy()
        else:
            self.keybinds = DEFAULT_KEYBINDS.copy()
            self.save_keybinds()
            
    def save_keybinds(self):
        """Save keybinds to file"""
        path = self.get_keybind_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.keybinds, f, indent=2)
        except Exception as e:
            print(f"Failed to save keybinds: {e}")
            
    def register_default_actions(self):
        """Register default action handlers"""
        self.actions = {
            "run_file": lambda: self.app.save_and_run() if hasattr(self.app, 'save_and_run') else None,
            "save_file": lambda: self.app.save_current_file() if hasattr(self.app, 'save_current_file') else None,
            "open_search": lambda: self.app.switch_sidebar("search") if hasattr(self.app, 'switch_sidebar') else None,
            "open_settings": lambda: self.app.open_settings() if hasattr(self.app, 'open_settings') else None,
            "new_project": lambda: self.app.create_new_project() if hasattr(self.app, 'create_new_project') else None,
            "open_project": lambda: self.app.open_existing_project() if hasattr(self.app, 'open_existing_project') else None,
            "close_tab": lambda: self.app.editor_tabs.close_current_tab() if hasattr(self.app, 'editor_tabs') and self.app.editor_tabs else None,
            "toggle_terminal": lambda: self.toggle_terminal()
        }
        
    def toggle_terminal(self):
        """Toggle terminal visibility"""
        # Placeholder - would need bottom panel reference
        pass
        
    def bind_all(self):
        """Bind all keybinds to root"""
        if not hasattr(self.app, 'root'):
            return
            
        for action_name, key in self.keybinds.items():
            if action_name in self.actions:
                try:
                    self.app.root.bind(key, lambda e, a=action_name: self.execute_action(a))
                except:
                    pass
                    
    def unbind_all(self):
        """Unbind all keybinds"""
        if not hasattr(self.app, 'root'):
            return
            
        for key in self.keybinds.values():
            try:
                self.app.root.unbind(key)
            except:
                pass
                
    def execute_action(self, action_name):
        """Execute action by name"""
        if action_name in self.actions:
            try:
                self.actions[action_name]()
            except Exception as e:
                print(f"Action {action_name} failed: {e}")
        return "break"  # Prevent default
        
    def set_keybind(self, action_name, new_key):
        """Change a keybind"""
        # Unbind old
        if action_name in self.keybinds:
            try:
                self.app.root.unbind(self.keybinds[action_name])
            except:
                pass
                
        # Set and bind new
        self.keybinds[action_name] = new_key
        if action_name in self.actions:
            try:
                self.app.root.bind(new_key, lambda e, a=action_name: self.execute_action(a))
            except:
                pass
                
        self.save_keybinds()
        
    def register_action(self, action_name, handler):
        """Register a new action"""
        self.actions[action_name] = handler


class KeybindSettingsDialog:
    """Dialog for editing keybinds"""
    
    def __init__(self, parent, keybind_manager):
        self.manager = keybind_manager
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Keyboard Shortcuts")
        self.dialog.geometry("450x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.entries = {}
        self.setup_ui()
        
    def setup_ui(self):
        ttk.Label(self.dialog, text="Customize Keyboard Shortcuts", font=("Arial", 11, "bold")).pack(pady=10)
        
        # Scrollable frame
        canvas = tk.Canvas(self.dialog)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")
        
        # Keybind entries
        for action, key in self.manager.keybinds.items():
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill="x", pady=2)
            
            label = action.replace("_", " ").title()
            ttk.Label(frame, text=label, width=20).pack(side="left", padx=5)
            
            var = tk.StringVar(value=key)
            entry = ttk.Entry(frame, textvariable=var, width=20)
            entry.pack(side="left", padx=5)
            self.entries[action] = var
            
        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", pady=10, padx=10)
        
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Reset Defaults", command=self.reset).pack(side="left", padx=5)
        
    def save(self):
        for action, var in self.entries.items():
            new_key = var.get().strip()
            if new_key:
                self.manager.set_keybind(action, new_key)
        messagebox.showinfo("Saved", "Keybinds saved!")
        self.dialog.destroy()
        
    def reset(self):
        if messagebox.askyesno("Reset", "Reset all keybinds to defaults?"):
            self.manager.keybinds = DEFAULT_KEYBINDS.copy()
            self.manager.save_keybinds()
            self.manager.unbind_all()
            self.manager.bind_all()
            self.dialog.destroy()
