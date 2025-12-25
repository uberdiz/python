import tkinter as tk

def ensure_window_on_screen(window):
    """
    Ensure a window is fully visible on screen and fits its elements.
    Works for both Toplevel and main Root windows.
    """
    if not window or not window.winfo_exists():
        return

    # Force a full update to ensure all widgets have calculated their sizes
    # Try multiple times as some elements might need more time
    for _ in range(3):
        try:
            window.update() 
            window.update_idletasks()
        except Exception:
            pass
    
    # Get screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Get required size (what the window needs to fit its content)
    # Use winfo_geometry if it's already set to something reasonable
    try:
        req_width = max(window.winfo_reqwidth(), window.winfo_width())
        req_height = max(window.winfo_reqheight(), window.winfo_height())
    except:
        req_width = window.winfo_reqwidth()
        req_height = window.winfo_reqheight()
    
    # Get current set geometry size
    try:
        current_geo = window.geometry().split('+')[0]
        cur_width, cur_height = map(int, current_geo.split('x'))
    except Exception:
        cur_width, cur_height = 0, 0
        
    # Use the larger of requested or current size, but at least a reasonable minimum
    # Keep minimums small enough for dialogs but large enough for visibility
    width = max(req_width, cur_width, 300)
    height = max(req_height, cur_height, 200)
    
    # Adjust size if it's too big for screen
    # Leave 100px buffer for taskbars/titlebars/padding
    new_width = min(width, screen_width - 100)
    new_height = min(height, screen_height - 100)
    
    # Get current position
    x = window.winfo_x()
    y = window.winfo_y()
    
    # If window is not positioned (usually 0,0 or 1,1 in Tkinter)
    if x <= 10 and y <= 10:
        new_x = (screen_width - new_width) // 2
        new_y = (screen_height - new_height) // 2
    else:
        # Keep it on screen with 20px margin
        new_x = max(20, min(x, screen_width - new_width - 20))
        new_y = max(20, min(y, screen_height - new_height - 20))
    
    # Apply geometry
    window.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")
    
    # Final update and lifting
    try:
        window.update()
        window.update_idletasks()
        window.lift()
        if isinstance(window, tk.Toplevel):
            window.focus_force()
    except:
        pass
    
    # For Toplevels, ensure they are usable
    if isinstance(window, tk.Toplevel):
        window.minsize(300, 200)
        window.lift()
        window.focus_set()

def apply_global_window_fix():
    """
    Monkeypatch tk.Toplevel to automatically ensure it's on screen.
    """
    original_init = tk.Toplevel.__init__
    
    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # Schedule the fix after a longer delay to allow more elements to be added
        self.after(300, lambda: ensure_window_on_screen(self))
        # Also fix on map event (when window actually appears)
        self.bind("<Map>", lambda e: self.after(100, lambda: ensure_window_on_screen(self)), add="+")

    tk.Toplevel.__init__ = patched_init
    print("AI IDE: Global Toplevel fix applied.")
