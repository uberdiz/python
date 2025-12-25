import tkinter as tk
from tkinter import messagebox
import threading
import time
import platform
import sys

# Try to import dependencies for advanced features
try:
    from PIL import ImageGrab, Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import win32clipboard
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class ClipboardManager:
    """
    Manages clipboard operations including text, images, and files.
    Cross-platform support with Windows optimizations.
    """
    def __init__(self, app):
        self.app = app
        self.last_content = None
        
    def get_content(self):
        """
        Smartly retrieve clipboard content.
        Returns a dict with 'type' and 'data'.
        """
        # 1. Try Image
        if HAS_PIL:
            try:
                img = ImageGrab.grabclipboard()
                if isinstance(img, Image.Image):
                    return {"type": "image", "data": img}
                elif isinstance(img, list): # List of files (Windows)
                    return {"type": "files", "data": img}
            except Exception as e:
                print(f"Clipboard Image Error: {e}")

        # 2. Try Files (Windows specific via win32clipboard if PIL missed it)
        if HAS_WIN32 and platform.system() == "Windows":
            try:
                win32clipboard.OpenClipboard()
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                    files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                    win32clipboard.CloseClipboard()
                    if files:
                        return {"type": "files", "data": list(files)}
                else:
                    win32clipboard.CloseClipboard()
            except Exception as e:
                try:
                    win32clipboard.CloseClipboard()
                except: pass
                print(f"Clipboard Win32 Error: {e}")

        # 3. Try Text (Universal)
        try:
            text = self.app.root.clipboard_get()
            if text:
                # Check if text looks like file paths
                import os
                lines = text.strip().split('\n')
                if all(os.path.exists(line.strip()) for line in lines) and len(lines) > 0:
                     return {"type": "files", "data": [line.strip() for line in lines]}
                return {"type": "text", "data": text}
        except tk.TclError:
            pass # Clipboard empty or incompatible
            
        return None

    def format_for_chat(self, content):
        """Format captured content for the AI chat"""
        if not content:
            return None, "No content in clipboard"
            
        c_type = content["type"]
        data = content["data"]
        
        if c_type == "text":
            return data, f"Captured text ({len(data)} chars)"
            
        elif c_type == "files":
            file_list = "\n".join(data)
            return f"I have selected these files:\n{file_list}\n\nPlease analyze them.", f"Captured {len(data)} files"
            
        elif c_type == "image":
            # Save to temp file to attach
            import tempfile
            import os
            fd, path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            data.save(path)
            return path, "Captured image"
            
        return None, "Unknown format"
