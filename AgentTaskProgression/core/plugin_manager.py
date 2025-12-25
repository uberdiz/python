"""
Plugin Manager for AI Dev IDE
Allows extending functionality via Python scripts in 'plugins' directory.
"""
import os
import importlib.util
import sys
import traceback

class PluginManager:
    def __init__(self, app):
        self.app = app
        self.plugins = {}
        self.plugin_dir = os.path.join(os.getcwd(), 'plugins')
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            
    def discover_plugins(self):
        """Find plugins in plugins directory"""
        found = []
        if not os.path.exists(self.plugin_dir):
            return found
            
        for name in os.listdir(self.plugin_dir):
            path = os.path.join(self.plugin_dir, name)
            if os.path.isdir(path):
                # Check for __init__.py or main.py?
                if os.path.exists(os.path.join(path, "__init__.py")):
                    found.append(name)
            elif name.endswith(".py"):
                found.append(name[:-3])
                
        return found
        
    def load_plugin(self, plugin_name):
        """Load and enable a plugin"""
        if plugin_name in self.plugins:
            return True
            
        try:
            # Try loading as module or file
            path = os.path.join(self.plugin_dir, plugin_name)
            spec = None
            
            if os.path.isdir(path):
                init_path = os.path.join(path, "__init__.py")
                if os.path.exists(init_path):
                    spec = importlib.util.spec_from_file_location(plugin_name, init_path)
            elif os.path.exists(path + ".py"):
                spec = importlib.util.spec_from_file_location(plugin_name, path + ".py")
                
            if not spec or not spec.loader:
                print(f"Could not find plugin: {plugin_name}")
                return False
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = module
            spec.loader.exec_module(module)
            
            # Check for setup function
            if hasattr(module, "setup"):
                module.setup(self.app)
                self.plugins[plugin_name] = module
                print(f"Loaded plugin: {plugin_name}")
                return True
            else:
                print(f"Plugin {plugin_name} has no setup() function")
                return False
                
        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {e}")
            traceback.print_exc()
            return False
            
    def load_all_plugins(self):
        """Load all discovered plugins"""
        for name in self.discover_plugins():
            self.load_plugin(name)
            
    def get_loaded_plugins(self):
        """Return list of loaded plugin names"""
        return list(self.plugins.keys())
