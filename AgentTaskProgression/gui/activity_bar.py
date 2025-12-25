import tkinter as tk
from tkinter import ttk

class ActivityBar(ttk.Frame):
    """Activity Bar (Leftmost narrow sidebar)"""
    def __init__(self, parent, app):
        super().__init__(parent, width=50)
        self.app = app
        self.pack_propagate(False)
        
        # Style configuration
        style = ttk.Style()
        style.configure("ActivityBar.TFrame", background="#333333")
        self.configure(style="ActivityBar.TFrame")
        self.theme_colors = {"activity_bar_bg": "#333333", "activity_bar_fg": "#858585", "activity_bar_active": "#007acc"}
        
        # Buttons container
        self.buttons_frame = ttk.Frame(self, style="ActivityBar.TFrame")
        self.buttons_frame.pack(fill="x", pady=10)
        
        # Activity Bar Buttons
        self.explorer_btn = self.create_button("📁", "Explorer", lambda: self.app.switch_sidebar("explorer"))
        self.search_btn = self.create_button("🔍", "Search", lambda: self.app.switch_sidebar("search"))
        self.git_btn = self.create_button("🌿", "Source Control", lambda: self.app.switch_sidebar("git"))
        self.agents_btn = self.create_button("🤖", "Agent Manager", lambda: self.app.switch_sidebar("agents"))
        self.ai_btn = self.create_button("💬", "AI Chat", lambda: self.app.switch_sidebar("ai"))
        
        # Bottom buttons
        self.bottom_frame = ttk.Frame(self, style="ActivityBar.TFrame")
        self.bottom_frame.pack(side="bottom", fill="x", pady=10)
        
        self.settings_btn = self.create_button("⚙️", "Settings", self.app.open_settings, parent=self.bottom_frame)
        self.account_btn = self.create_button("👤", "Account", self.app.open_account_settings, parent=self.bottom_frame)
        
        self.active_btn = None
    
    def create_button(self, icon, tooltip, command, parent=None):
        if parent is None:
            parent = self.buttons_frame
            
        bg_color = self.theme_colors.get("activity_bar_bg", "#333333")
        container = tk.Frame(parent, bg=bg_color)
        container.pack(fill="x")
        
        # Indicator strip (left side)
        indicator = tk.Frame(container, width=3, bg=bg_color)
        indicator.pack(side="left", fill="y")
        
        btn = tk.Label(
            container,
            text=icon,
            font=("Arial", 16),
            bg=bg_color,
            fg="#858585",
            cursor="hand2",
            pady=10
        )
        btn.pack(side="left", fill="x", expand=True)
        
        # Store for reference
        btn.indicator = indicator
        btn.container = container
        
        btn.bind("<Enter>", lambda e: self.on_hover(btn))
        btn.bind("<Leave>", lambda e: self.on_leave(btn))
        btn.bind("<Button-1>", lambda e: self.on_click(btn, command))
        indicator.bind("<Button-1>", lambda e: self.on_click(btn, command))
        
        return btn
        
    def on_hover(self, btn):
        if btn != self.active_btn:
            btn.configure(fg=self.theme_colors.get("activity_bar_hover", "#cccccc"))
            
    def on_leave(self, btn):
        if btn != self.active_btn:
            btn.configure(fg=self.theme_colors.get("activity_bar_fg", "#858585"))
            
    def on_click(self, btn, command):
        # Update styling for active state
        bg_color = self.theme_colors.get("activity_bar_bg", "#333333")
        active_indicator = self.theme_colors.get("activity_bar_active", "#007acc")
        fg_inactive = self.theme_colors.get("activity_bar_fg", "#858585")
        
        if self.active_btn:
            self.active_btn.configure(fg=fg_inactive)
            self.active_btn.indicator.configure(bg=bg_color)
            
        self.active_btn = btn
        btn.configure(fg="#ffffff")
        btn.indicator.configure(bg=active_indicator)
        
        # Execute command
        if command:
            command()
    
    def set_active(self, mode):
        """Set active button programmatically"""
        mapping = {
            "explorer": self.explorer_btn,
            "search": self.search_btn,
            "git": self.git_btn,
            "agents": self.agents_btn,
            "ai": self.ai_btn
        }
        target = mapping.get(mode)
        if target:
            self.on_click(target, None)

    def apply_theme(self, color_map):
        """Apply theme colors"""
        self.theme_colors = color_map
        bg_color = color_map.get("activity_bar_bg", "#333333")
        fg_color = color_map.get("activity_bar_fg", "#858585")
        
        style = ttk.Style()
        style.configure("ActivityBar.TFrame", background=bg_color)
        
        self.configure(background=bg_color)
        self.buttons_frame.configure(style="ActivityBar.TFrame")
        self.bottom_frame.configure(style="ActivityBar.TFrame")
        
        def update_recursive(w):
            if isinstance(w, tk.Label):
                if w == self.active_btn:
                   w.configure(bg=bg_color, fg="#ffffff")
                else:
                   w.configure(bg=bg_color, fg=fg_color)
            elif isinstance(w, tk.Frame) and not isinstance(w, ttk.Frame):
                # Custom frame (indicator or container)
                if hasattr(w, 'pack_info') and any(child == w for child in getattr(self.active_btn.container if self.active_btn else None, 'winfo_children', lambda:[])()):
                    # Special handling for indicator if needed, but easier to just check active_btn
                    pass
                
                # Check if it's an indicator
                is_indicator = False
                for b in [self.explorer_btn, self.search_btn, self.git_btn, self.agents_btn, self.ai_btn, self.settings_btn, self.account_btn]:
                    if hasattr(b, 'indicator') and b.indicator == w:
                        is_indicator = True
                        if b == self.active_btn:
                            w.configure(bg=color_map.get("activity_bar_active", "#007acc"))
                        else:
                            w.configure(bg=bg_color)
                        break
                if not is_indicator:
                    w.configure(bg=bg_color)
            
            for child in w.winfo_children():
                update_recursive(child)

        update_recursive(self)
