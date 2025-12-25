import os
import json
import shutil

class VSCodeImporter:
    def __init__(self):
        self.home = os.path.expanduser("~")
        self.extensions_path = os.path.join(self.home, ".vscode", "extensions")
        self.settings_path = os.path.join(self.home, "AppData", "Roaming", "Code", "User", "settings.json")
        if os.name != 'nt': # Linux/Mac
             self.settings_path = os.path.join(self.home, ".config", "Code", "User", "settings.json")
             
    def get_installed_extensions(self):
        """Get list of installed VS Code extensions"""
        extensions = []
        if os.path.exists(self.extensions_path):
            for item in os.listdir(self.extensions_path):
                if os.path.isdir(os.path.join(self.extensions_path, item)):
                    extensions.append(item)
        return extensions

    def import_keybindings(self):
        """Mock import of keybindings"""
        return "Imported Standard VS Code Keymap"

    def import_theme_colors(self):
        """Try to read current VS Code theme colors"""
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    # JSON with comments might fail, standard json lib doesn't support comments
                    # We'll try a simple load
                    content = f.read()
                    # Strip comments if possible (simple regex)
                    import re
                    content = re.sub(r'//.*', '', content)
                    data = json.loads(content)
                    return data.get("workbench.colorCustomizations", {})
            except:
                pass
        return {}
