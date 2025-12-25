"""
Preview Manager - Lightweight preview system for generated apps
Runs apps in background processes (no VM overhead)
"""
import subprocess
import webbrowser
import os
import tempfile
import threading

class PreviewManager:
    """Manages lightweight preview of generated apps"""
    
    def __init__(self, app):
        self.app = app
        self.active_previews = {}  # name -> process
        
    def preview_web(self, html_content=None, html_file=None, url=None):
        """Preview web content in browser"""
        if url:
            webbrowser.open(url)
            self.log(f"Opened browser: {url}")
            return True
            
        if html_content:
            # Write to temp file and open
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_path = f.name
                
            webbrowser.open(f"file://{temp_path}")
            self.log(f"Opened temp HTML: {temp_path}")
            return True
            
        if html_file and os.path.exists(html_file):
            webbrowser.open(f"file://{os.path.abspath(html_file)}")
            self.log(f"Opened HTML file: {html_file}")
            return True
            
        return False
        
    def preview_tkinter(self, python_file=None, python_code=None):
        """Preview Tkinter app in subprocess"""
        try:
            if python_code:
                # Write to temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                    f.write(python_code)
                    python_file = f.name
                    
            if python_file and os.path.exists(python_file):
                process = subprocess.Popen(
                    ["python", python_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=os.path.dirname(python_file) or "."
                )
                
                self.active_previews["tkinter"] = process
                self.log(f"Started Tkinter preview: {python_file}")
                
                # Monitor in background
                def monitor():
                    stdout, stderr = process.communicate()
                    if stderr:
                        self.log(f"Tkinter stderr: {stderr.decode('utf-8', errors='ignore')[:200]}")
                        
                threading.Thread(target=monitor, daemon=True).start()
                return True
                
        except Exception as e:
            self.log(f"Tkinter preview error: {e}")
            
        return False
        
    def preview_roblox(self, lua_file=None, rbxl_file=None):
        """Open Roblox Studio with project"""
        try:
            # Try to find Roblox Studio
            roblox_paths = [
                os.path.expandvars(r"%LOCALAPPDATA%\Roblox\Versions"),
                r"C:\Program Files (x86)\Roblox\Versions"
            ]
            
            studio_exe = None
            for base_path in roblox_paths:
                if os.path.exists(base_path):
                    for version_dir in os.listdir(base_path):
                        potential = os.path.join(base_path, version_dir, "RobloxStudioBeta.exe")
                        if os.path.exists(potential):
                            studio_exe = potential
                            break
                            
            if studio_exe and rbxl_file and os.path.exists(rbxl_file):
                subprocess.Popen([studio_exe, rbxl_file])
                self.log(f"Opened Roblox Studio: {rbxl_file}")
                return True
            elif studio_exe:
                subprocess.Popen([studio_exe])
                self.log("Opened Roblox Studio")
                return True
            else:
                self.log("Roblox Studio not found. Please open it manually.")
                return False
                
        except Exception as e:
            self.log(f"Roblox preview error: {e}")
            return False
            
    def preview_unity(self, project_path=None, script_file=None):
        """Open Unity with project"""
        try:
            # Try to find Unity Hub or Unity Editor
            unity_hub = os.path.expandvars(r"%PROGRAMFILES%\Unity Hub\Unity Hub.exe")
            
            if os.path.exists(unity_hub):
                if project_path and os.path.exists(project_path):
                    subprocess.Popen([unity_hub, "--projectPath", project_path])
                else:
                    subprocess.Popen([unity_hub])
                self.log("Opened Unity Hub")
                return True
            else:
                self.log("Unity Hub not found. Please open Unity manually.")
                return False
                
        except Exception as e:
            self.log(f"Unity preview error: {e}")
            return False
            
    def stop_preview(self, name):
        """Stop a running preview"""
        if name in self.active_previews:
            process = self.active_previews[name]
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                process.kill()
            del self.active_previews[name]
            self.log(f"Stopped preview: {name}")
            
    def stop_all(self):
        """Stop all previews"""
        for name in list(self.active_previews.keys()):
            self.stop_preview(name)
            
    def log(self, message):
        """Log preview activity"""
        print(f"[PreviewManager] {message}")
        if hasattr(self.app, 'log_ai'):
            self.app.log_ai(f"[Preview] {message}")


def detect_app_type(code_or_file):
    """Detect what type of app the code is for"""
    content = code_or_file
    
    if os.path.exists(code_or_file):
        with open(code_or_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
    content_lower = content.lower()
    
    if "tkinter" in content_lower or "from tkinter" in content_lower:
        return "tkinter"
    elif "<html" in content_lower or "<!doctype html" in content_lower:
        return "web"
    elif "game:getservice" in content_lower or "screenGui" in content_lower.replace(" ", ""):
        return "roblox"
    elif "using unityengine" in content_lower or "monobehaviour" in content_lower:
        return "unity"
    else:
        return "unknown"
