import threading
import time
import sys
from pynput import keyboard

class HotkeyManager:
    """
    Manages global hotkeys using pynput.
    Runs in a background thread.
    """
    def __init__(self, app, callback):
        self.app = app
        self.callback = callback
        self.listener = None
        self.running = False
        self.current_keys = set()
        
    def start(self):
        """Start the global hotkey listener"""
        if self.running: return
        self.running = True
        
        # Define the hotkey string for pynput.GlobalHotKeys
        self.hotkey = keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+a': self.on_activate,
            '<ctrl>+<alt>+r': self.on_reference
        })
        self.hotkey.start()
        print("Global Hotkey Listener Started (Ctrl+Alt+A: Capture, Ctrl+Alt+R: Reference)")

    def stop(self):
        """Stop the listener"""
        self.running = False
        if hasattr(self, 'hotkey') and self.hotkey:
            self.hotkey.stop()

    def on_activate(self):
        """Called when hotkey is triggered"""
        print("Global Hotkey: Capture Triggered!")
        if self.callback:
            # Run in main thread
            self.app.root.after(0, self.callback)

    def on_reference(self):
        """Called when reference hotkey is triggered"""
        print("Global Hotkey: Reference Triggered!")
        if hasattr(self.app, 'reference_selection'):
            self.app.root.after(0, self.app.reference_selection)
