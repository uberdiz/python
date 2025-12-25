"""
Layout Manager - Handles draggable windows and layout persistence
"""
import json
import os
import tkinter as tk
from tkinter import ttk

class LayoutManager:
    def __init__(self, app):
        self.app = app
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "layout_config.json")
        self.layout_groups = {}
        self.window_registry = {}
        self._drop_overlay = {}
        self.load_layout()

    def register_window(self, name, widget):
        self.window_registry[name] = widget

    def add_to_group(self, group_name, component_name):
        if group_name not in self.layout_groups:
            self.layout_groups[group_name] = []
        if component_name not in self.layout_groups[group_name]:
            self.layout_groups[group_name].append(component_name)
        self.save_layout()

    def save_layout(self):
        data = {
            "groups": self.layout_groups,
            "windows": []
        }
        for name, container in self.window_registry.items():
            zone = "left"
            try:
                parent = getattr(container, "dock_parent", None)
                if parent is self.app.sidebar_content:
                    zone = "left"
                elif parent is getattr(self.app, "right_sidebar_content", None):
                    zone = "right"
                elif parent is getattr(self.app, "bottom_panel_frame", None):
                    zone = "bottom"
            except Exception:
                pass
            entry = {"name": name, "is_undocked": getattr(container, "is_undocked", False), "zone": zone}
            try:
                if getattr(container, "is_undocked", False):
                    x = container.winfo_x()
                    y = container.winfo_y()
                    w = container.winfo_width()
                    h = container.winfo_height()
                    entry.update({"x": x, "y": y, "width": w, "height": h})
                else:
                    w = container.winfo_width()
                    h = container.winfo_height()
                    entry.update({"x": 0, "y": 0, "width": w, "height": h})
            except Exception:
                entry.update({"x": 0, "y": 0, "width": 0, "height": 0})
            data["windows"].append(entry)
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to save layout: {e}")

    def load_layout(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.layout_groups = data.get("groups", {})
                    windows = data.get("windows", [])
                    for item in windows:
                        name = item.get("name")
                        if not name or name not in self.window_registry:
                            continue
                        container = self.window_registry[name]
                        is_undocked = item.get("is_undocked", False)
                        if is_undocked:
                            if not getattr(container, "is_undocked", False):
                                btn = getattr(container, "undock_btn", None)
                                self.toggle_undock(container, btn)
                            w = item.get("width", 400)
                            h = item.get("height", 600)
                            x = item.get("x", 50)
                            y = item.get("y", 50)
                            container.place(x=int(x), y=int(y), width=int(w), height=int(h))
                        else:
                            zone = item.get("zone", "left")
                            target = self._zone_to_widget(zone)
                            if target:
                                try:
                                    container.place_forget()
                                    container.pack(in_=target, fill="both", expand=True)
                                    container.dock_parent = target
                                    container.is_undocked = False
                                except Exception:
                                    pass
            except Exception as e:
                print(f"Failed to load layout: {e}")

    def create_draggable_container(self, parent, title="Panel"):
        container = ttk.Frame(self.app.root)
        container.is_undocked = False
        container.dock_parent = parent
        container.name = title
        
        # Header for dragging/actions
        header = ttk.Frame(container, cursor="fleur", style="Header.TFrame")
        header.pack(fill="x")
        container.header = header
        
        def show_move_menu(event):
            menu = tk.Menu(header, tearoff=0)
            menu.add_command(label="Move to Left Sidebar", command=lambda: self.move_panel(container, "left"))
            menu.add_command(label="Move to Right Sidebar", command=lambda: self.move_panel(container, "right"))
            menu.add_command(label="Move to Bottom Panel", command=lambda: self.move_panel(container, "bottom"))
            menu.post(event.x_root, event.y_root)
        header.bind("<Button-3>", show_move_menu)
        
        # Style for header
        style = ttk.Style()
        bg = self.app.theme_engine.color_map.get("panel_bg", "#2d2d30")
        style.configure("Header.TFrame", background=bg)
        
        ttk.Label(header, text=title.upper(), font=("Segoe UI", 8, "bold"),
                 foreground=self.app.theme_engine.color_map.get("panel_fg", "#888888")).pack(side="left", padx=10, pady=5)
        
        # Buttons
        ttk.Button(header, text="×", width=2, command=lambda: self.hide_container(container)).pack(side="right", padx=2)
        undock_btn = ttk.Button(header, text="❐", width=2)
        undock_btn.pack(side="right", padx=2)
        undock_btn.configure(command=lambda: self.toggle_undock(container, undock_btn))
        container.undock_btn = undock_btn
        
        # Content frame where the actual widget will live
        content_frame = ttk.Frame(container)
        content_frame.pack(fill="both", expand=True)
        
        self.register_window(title, container)
        return container, content_frame

    def move_panel(self, container, target):
        """Move panel to a new zone"""
        # Remove from current
        container.pack_forget()
        
        # Determine new parent
        new_parent = None
        if target == "left":
            if hasattr(self.app, 'sidebar_content'):
                new_parent = self.app.sidebar_content
        elif target == "right":
            # Assuming there is a right sidebar, if not create/use existing
            # For now, let's assume sidebar_content is the main one.
            # If user wants 'Right', we might need to verify if app has it.
            # Fallback to sidebar_content for now or implement right sidebar logic if app supports it
            if hasattr(self.app, 'right_sidebar_content'):
                 new_parent = self.app.right_sidebar_content
            else:
                 print("Right sidebar not available")
                 new_parent = self.app.sidebar_content # Fallback
        elif target == "bottom":
            if hasattr(self.app, 'bottom_panel_content'):
                new_parent = self.app.bottom_panel_content
                
        if new_parent:
            container.pack(in_=new_parent, fill="both", expand=True)
            container.dock_parent = new_parent
            
    def hide_container(self, container):
        """Hide the container from whichever master it is in"""
        container.pack_forget()

    def toggle_undock(self, container, button):
        if not container.is_undocked:
            try:
                container.pack_forget()
                container.place(x=100, y=100, width=400, height=600)
                container.is_undocked = True
                if button:
                    button.configure(text="⤓")

                def start_drag(event):
                    container._drag_offset_x = event.x
                    container._drag_offset_y = event.y
                def on_drag(event):
                    x = container.winfo_x() - getattr(container, "_drag_offset_x", 0) + event.x
                    y = container.winfo_y() - getattr(container, "_drag_offset_y", 0) + event.y
                    container.place(x=max(0, x), y=max(0, y))
                    self._update_drop_highlight(event)
                def on_release(event):
                    self._attempt_dock(container, event)
                    self._clear_drop_highlight()
                if hasattr(container, "header"):
                    container.header.bind("<ButtonPress-1>", start_drag)
                    container.header.bind("<B1-Motion>", on_drag)
                    container.header.bind("<ButtonRelease-1>", on_release)

                resize_handle = ttk.Frame(container, cursor="size_nw_se")
                resize_handle.pack(side="right", fill="y")
                def start_resize(event):
                    container._resize_start_w = container.winfo_width()
                    container._resize_start_h = container.winfo_height()
                    container._resize_start_x = event.x
                    container._resize_start_y = event.y
                def on_resize(event):
                    dw = event.x - getattr(container, "_resize_start_x", 0)
                    dh = event.y - getattr(container, "_resize_start_y", 0)
                    w = max(200, getattr(container, "_resize_start_w", 400) + dw)
                    h = max(200, getattr(container, "_resize_start_h", 600) + dh)
                    container.place(width=int(w), height=int(h))
                resize_handle.bind("<ButtonPress-1>", start_resize)
                resize_handle.bind("<B1-Motion>", on_resize)
                container.resize_handle = resize_handle
            except Exception as e:
                print(f"Undocking failed: {e}")
                try:
                    container.pack(in_=container.dock_parent, fill="both", expand=True)
                except Exception:
                    pass
        else:
            try:
                container.place_forget()
                container.pack(in_=container.dock_parent, fill="both", expand=True)
                container.is_undocked = False
                if button:
                    button.configure(text="❐")
                if hasattr(container, "header"):
                    container.header.unbind("<ButtonPress-1>")
                    container.header.unbind("<B1-Motion>")
                    container.header.unbind("<ButtonRelease-1>")
                if hasattr(container, "resize_handle"):
                    try:
                        container.resize_handle.destroy()
                    except Exception:
                        pass
            except Exception as e:
                print(f"Redocking failed: {e}")

    def _zone_to_widget(self, zone):
        if zone == "left":
            return getattr(self.app, "sidebar_content", None)
        if zone == "right":
            return getattr(self.app, "right_sidebar_content", None)
        if zone == "bottom":
            return getattr(self.app, "bottom_panel_frame", None)
        return None

    def _get_drop_targets(self):
        targets = []
        left = getattr(self.app, "sidebar_content", None)
        if left:
            targets.append(("left", left))
        right = getattr(self.app, "right_sidebar_content", None)
        if right:
            targets.append(("right", right))
        bottom = getattr(self.app, "bottom_panel_frame", None)
        if bottom:
            targets.append(("bottom", bottom))
        return targets

    def _update_drop_highlight(self, event):
        try:
            x_root = event.widget.winfo_rootx() + event.x
            y_root = event.widget.winfo_rooty() + event.y
            hit = None
            for name, widget in self._get_drop_targets():
                wx = widget.winfo_rootx()
                wy = widget.winfo_rooty()
                ww = widget.winfo_width()
                wh = widget.winfo_height()
                if wx <= x_root <= wx + ww and wy <= y_root <= wy + wh:
                    hit = (name, widget)
                    break
            for name, widget in self._get_drop_targets():
                if hit and hit[0] == name:
                    self._show_overlay(widget)
                else:
                    self._hide_overlay(widget)
        except Exception:
            pass

    def _attempt_dock(self, container, event):
        try:
            x_root = event.widget.winfo_rootx() + event.x
            y_root = event.widget.winfo_rooty() + event.y
            for name, widget in self._get_drop_targets():
                wx = widget.winfo_rootx()
                wy = widget.winfo_rooty()
                ww = widget.winfo_width()
                wh = widget.winfo_height()
                if wx <= x_root <= wx + ww and wy <= y_root <= wy + wh:
                    container.place_forget()
                    nb = self._ensure_notebook(widget)
                    # Limit tabs per zone to avoid clutter
                    try:
                        if len(nb.tabs()) >= 8:
                            print("Dock limit reached for zone; keep floating")
                            return
                    except Exception:
                        pass
                    try:
                        nb.add(container, text=container.name)
                    except Exception:
                        # Fallback: pack without notebook
                        container.pack(in_=widget, fill="both", expand=True)
                        container.dock_parent = widget
                        container.is_undocked = False
                    else:
                        container.dock_parent = nb
                        container.is_undocked = False
                        try:
                            nb.select(container)
                        except Exception:
                            pass
                    btn = getattr(container, "undock_btn", None)
                    if btn:
                        btn.configure(text="❐")
                    self._hide_overlay(widget)
                    self.save_layout()
                    break
        except Exception:
            pass

    def _show_overlay(self, target):
        try:
            if target not in self._drop_overlay:
                ov = tk.Frame(target, bg="#ffaa00", highlightthickness=0)
                self._drop_overlay[target] = ov
            ov = self._drop_overlay[target]
            ov.place(relx=0, rely=0, relwidth=1, relheight=1)
            ov.lift()
        except Exception:
            pass

    def _hide_overlay(self, target):
        try:
            if target in self._drop_overlay:
                self._drop_overlay[target].place_forget()
        except Exception:
            pass

    def _clear_drop_highlight(self):
        for _, w in self._get_drop_targets():
            self._hide_overlay(w)

    def _ensure_notebook(self, zone_widget):
        try:
            # If a notebook already exists, return it
            for child in zone_widget.winfo_children():
                if isinstance(child, ttk.Notebook):
                    return child
            nb = ttk.Notebook(zone_widget)
            nb.pack(fill="both", expand=True)
            return nb
        except Exception:
            return zone_widget
