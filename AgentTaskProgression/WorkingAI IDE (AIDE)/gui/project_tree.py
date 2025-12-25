"""
Project Tree with Folder Navigation - FIXED
"""
import os
import tkinter as tk
from tkinter import ttk, Menu

class ProjectTree(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.project_path = None
        self.tree = None
        
        self.setup_tree()
    
    def setup_tree(self):
        """Setup the tree view"""
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)
        
        self.tree = ttk.Treeview(tree_frame, selectmode="browse")
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Button-2>", self.on_middle_click)  # Middle click for closing
        
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Open", command=self.open_selected)
        self.context_menu.add_command(label="New File", command=self.create_new_file)
        self.context_menu.add_command(label="New Folder", command=self.create_new_folder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Refresh", command=self.refresh)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Open in Explorer", command=self.open_in_explorer)
        
        self.setup_toolbar()
    
    def setup_toolbar(self):
        """Setup toolbar buttons"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(toolbar, text="📁", command=self.load_project_dialog,
                  width=3).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🔄", command=self.refresh,
                  width=3).pack(side="left", padx=2)
        ttk.Button(toolbar, text="➕", command=self.create_new_file,
                  width=3).pack(side="left", padx=2)
        ttk.Button(toolbar, text="📁➕", command=self.create_new_folder,
                  width=3).pack(side="left", padx=2)
    
    def load_project(self, project_path):
        """Load a project into the tree"""
        self.project_path = project_path
        self.refresh()
    
    def load_project_dialog(self):
        """Open project dialog"""
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Select Project Folder")
        if folder:
            self.load_project(folder)
            if self.app:
                self.app.project_path = folder
    
    def refresh(self):
        """Refresh the tree view"""
        if not self.project_path or not os.path.exists(self.project_path):
            return
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        root_name = os.path.basename(self.project_path)
        root_id = self.tree.insert("", "end", text=root_name, open=True)
        self.tree.item(root_id, tags=("root",))
        
        self.build_tree(root_id, self.project_path)
        self.tree.item(root_id, open=True)
    
    def build_tree(self, parent_id, path):
        """Build tree recursively - FIXED to expand folders"""
        try:
            items = os.listdir(path)
            dirs = []
            files = []
            
            for item in sorted(items, key=lambda x: x.lower()):
                if item.startswith('.') or item in ['__pycache__', '.git', '.venv', 'venv']:
                    continue
                
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    dirs.append(item)
                else:
                    files.append(item)
            
            for dir_name in dirs:
                dir_path = os.path.join(path, dir_name)
                dir_id = self.tree.insert(parent_id, "end", text=dir_name, tags=("folder",))
                self.tree.item(dir_id, open=False)
                
                # FIXED: Recursively build subdirectories
                try:
                    sub_items = os.listdir(dir_path)
                    if sub_items:
                        for sub_item in sub_items:
                            if not sub_item.startswith('.'):
                                sub_path = os.path.join(dir_path, sub_item)
                                if os.path.isdir(sub_path):
                                    self.tree.insert(dir_id, "end", text=sub_item, tags=("folder",))
                                else:
                                    if sub_item.endswith('.py'):
                                        self.tree.insert(dir_id, "end", text=sub_item, tags=("file", "python"))
                                    else:
                                        self.tree.insert(dir_id, "end", text=sub_item, tags=("file",))
                except PermissionError:
                    pass
                except Exception:
                    pass
            
            for file_name in files:
                file_path = os.path.join(path, file_name)
                file_id = self.tree.insert(parent_id, "end", text=file_name, tags=("file",))
                
                if file_name.endswith('.py'):
                    self.tree.item(file_id, tags=("file", "python"))
        
        except PermissionError:
            pass
        except Exception as e:
            print(f"Error building tree: {e}")
    
    def on_double_click(self, event):
        """Handle double-click on tree item - FIXED for folders"""
        item_id = self.tree.selection()[0] if self.tree.selection() else None
        if item_id:
            item_tags = self.tree.item(item_id, "tags")
            
            if "folder" in item_tags:
                # Toggle folder open/closed state
                current_state = self.tree.item(item_id, "open")
                self.tree.item(item_id, open=not current_state)
            else:
                self.open_item(item_id)
    
    def on_middle_click(self, event):
        """Handle middle-click (close tab)"""
        if self.app and self.app.editor_tabs:
            self.app.editor_tabs.close_current_tab()
    
    def open_item(self, item_id):
        """Open the selected item"""
        item_tags = self.tree.item(item_id, "tags")
        
        if "file" in item_tags:
            file_path = self.get_full_path(item_id)
            if file_path and os.path.isfile(file_path):
                if self.app and self.app.editor_tabs:
                    self.app.editor_tabs.open_file(file_path)
    
    def get_full_path(self, item_id):
        """Get full path for a tree item"""
        if not self.project_path:
            return None
        
        hierarchy = []
        current_id = item_id
        
        while current_id:
            text = self.tree.item(current_id, "text")
            hierarchy.insert(0, text)
            current_id = self.tree.parent(current_id)
        
        if hierarchy:
            path = self.project_path
            
            for part in hierarchy[1:]:  # Skip the root (already in project_path)
                path = os.path.join(path, part)
            
            return path
        
        return None
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.context_menu.post(event.x_root, event.y_root)
    
    def open_selected(self):
        """Open selected item"""
        item_id = self.tree.selection()[0] if self.tree.selection() else None
        if item_id:
            self.open_item(item_id)
    
    def create_new_file(self):
        """Create a new file"""
        from tkinter import simpledialog
        
        item_id = self.tree.selection()[0] if self.tree.selection() else None
        parent_path = self.project_path
        
        if item_id:
            selected_path = self.get_full_path(item_id)
            if selected_path and os.path.isdir(selected_path):
                parent_path = selected_path
            elif selected_path:
                parent_path = os.path.dirname(selected_path)
        
        filename = simpledialog.askstring("New File", "Enter filename:")
        if filename:
            full_path = os.path.join(parent_path, filename)
            
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write('# New file\n')
                
                self.refresh()
                
                if self.app and self.app.editor_tabs:
                    self.app.editor_tabs.open_file(full_path)
                
                if self.app:
                    self.app.log_ai(f"Created: {filename}")
            except Exception as e:
                if self.app:
                    self.app.log_ai(f"Error creating file: {e}")
    
    def create_new_folder(self):
        """Create a new folder"""
        from tkinter import simpledialog
        
        item_id = self.tree.selection()[0] if self.tree.selection() else None
        parent_path = self.project_path
        
        if item_id:
            selected_path = self.get_full_path(item_id)
            if selected_path and os.path.isdir(selected_path):
                parent_path = selected_path
            elif selected_path:
                parent_path = os.path.dirname(selected_path)
        
        foldername = simpledialog.askstring("New Folder", "Enter folder name:")
        if foldername:
            full_path = os.path.join(parent_path, foldername)
            
            try:
                os.makedirs(full_path, exist_ok=True)
                self.refresh()
                
                if self.app:
                    self.app.log_ai(f"Created folder: {foldername}")
            except Exception as e:
                if self.app:
                    self.app.log_ai(f"Error creating folder: {e}")
    
    def open_in_explorer(self):
        """Open selected item in windows explorer"""
        item_id = self.tree.selection()[0] if self.tree.selection() else None
        if not item_id: return
        
        path = self.get_full_path(item_id)
        if not path: return
        
        try:
            if os.path.isdir(path):
                os.startfile(path)
            else:
                # Open parent and select file
                import subprocess
                subprocess.run(['explorer', '/select,', os.path.normpath(path)])
        except Exception as e:
            if self.app:
                self.app.log_ai(f"Error opening explorer: {e}")

    def get_all_files(self):
        """Get all files in project"""
        if not self.project_path:
            return []
        
        files = []
        for root, dirs, filenames in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                if not filename.startswith('.'):
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, self.project_path)
                    files.append(rel_path)
        
        return files
    
    def apply_theme(self, color_map):
        """Apply theme to tree"""
        style = ttk.Style()
        
        style.configure("Treeview",
                       background=color_map.get("tree_bg", "#252526"),
                       foreground=color_map.get("tree_fg", "#cccccc"),
                       fieldbackground=color_map.get("tree_bg", "#252526"),
                       borderwidth=0)
        
        style.map("Treeview",
                 background=[("selected", color_map.get("tree_selection", "#094771"))],
                 foreground=[("selected", color_map.get("tree_fg", "#ffffff"))])