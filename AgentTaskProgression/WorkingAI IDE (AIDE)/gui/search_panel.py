"""
Search Panel - Global search across files, folders, and settings
"""
import tkinter as tk
from tkinter import ttk
import os
import threading
import re

class SearchPanel(ttk.Frame):
    """Sidebar panel for global search"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.setup_ui()
        self.bind_shortcuts()
        
    def setup_ui(self):
        # Search input
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=5, pady=5)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(fill="x", side="left", expand=True)
        self.search_entry.bind("<Return>", lambda e: self.do_search())
        
        ttk.Button(search_frame, text="🔍", width=3, command=self.do_search).pack(side="right", padx=2)
        
        # Options
        options_frame = ttk.Frame(self)
        options_frame.pack(fill="x", padx=5, pady=2)
        
        self.case_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Case Sensitive", variable=self.case_var).pack(side="left")
        
        self.regex_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Regex", variable=self.regex_var).pack(side="left")
        
        # Scope selection
        scope_frame = ttk.Frame(self)
        scope_frame.pack(fill="x", padx=5, pady=2)
        
        self.scope_var = tk.StringVar(value="files")
        ttk.Radiobutton(scope_frame, text="Files", variable=self.scope_var, value="files").pack(side="left")
        ttk.Radiobutton(scope_frame, text="Folders", variable=self.scope_var, value="folders").pack(side="left")
        ttk.Radiobutton(scope_frame, text="Settings", variable=self.scope_var, value="settings").pack(side="left")
        
        # Results
        results_frame = ttk.LabelFrame(self, text="Results")
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.results_tree = ttk.Treeview(results_frame, columns=("Match", "Location"), show="headings")
        self.results_tree.heading("Match", text="Match")
        self.results_tree.heading("Location", text="Location")
        self.results_tree.column("Match", width=200)
        self.results_tree.column("Location", width=150)
        self.results_tree.pack(fill="both", expand=True, padx=2, pady=2)
        self.results_tree.bind("<Double-1>", self.open_result)
        
        # Status
        self.status_label = ttk.Label(self, text="Ready")
        self.status_label.pack(fill="x", padx=5, pady=2)
        
    def bind_shortcuts(self):
        """Bind Ctrl+F to focus search"""
        if self.app and hasattr(self.app, 'root'):
            self.app.root.bind("<Control-f>", self.focus_search)
            
    def focus_search(self, event=None):
        """Focus the search entry and switch to search view"""
        if hasattr(self.app, 'switch_sidebar'):
            self.app.switch_sidebar("search")
        self.search_entry.focus_set()
        self.search_entry.selection_range(0, tk.END)
        return "break"
        
    def do_search(self):
        """Perform search based on scope"""
        query = self.search_var.get().strip()
        if not query:
            return
            
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        self.status_label.config(text="Searching...")
        
        scope = self.scope_var.get()
        
        def worker():
            results = []
            
            if scope == "files":
                results = self.search_files(query)
            elif scope == "folders":
                results = self.search_folders(query)
            elif scope == "settings":
                results = self.search_settings(query)
                
            self.after(0, lambda: self.display_results(results))
            
        threading.Thread(target=worker, daemon=True).start()
        
    def search_files(self, query):
        """Search in project files"""
        results = []
        
        if not self.app.project_path:
            return results
            
        case_sensitive = self.case_var.get()
        use_regex = self.regex_var.get()
        
        for root, dirs, files in os.walk(self.app.project_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', '.idea']]
            
            for file in files:
                if file.endswith(('.pyc', '.git', '.png', '.jpg', '.exe', '.dll')):
                    continue
                    
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.app.project_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if self.matches(query, line, case_sensitive, use_regex):
                                match_text = line.strip()[:50]
                                results.append((match_text, f"{rel_path}:{line_num}"))
                                
                                if len(results) >= 100:  # Limit results
                                    return results
                except:
                    pass
                    
        return results
        
    def search_folders(self, query):
        """Search folder names"""
        results = []
        
        if not self.app.project_path:
            return results
            
        case_sensitive = self.case_var.get()
        
        for root, dirs, files in os.walk(self.app.project_path):
            for d in dirs:
                if self.matches(query, d, case_sensitive, False):
                    full_path = os.path.join(root, d)
                    rel_path = os.path.relpath(full_path, self.app.project_path)
                    results.append((d, rel_path))
                    
        return results
        
    def search_settings(self, query):
        """Search in settings keys and values"""
        results = []
        
        if not self.app.settings:
            return results
            
        case_sensitive = self.case_var.get()
        
        for key, value in self.app.settings.items():
            if self.matches(query, str(key), case_sensitive, False) or self.matches(query, str(value), case_sensitive, False):
                results.append((key, str(value)[:30]))
                
        return results
        
    def matches(self, query, text, case_sensitive, use_regex):
        """Check if query matches text"""
        if use_regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                return bool(re.search(query, text, flags))
            except:
                return False
        else:
            if not case_sensitive:
                query = query.lower()
                text = text.lower()
            return query in text
            
    def display_results(self, results):
        """Display search results"""
        for match, location in results:
            self.results_tree.insert("", "end", values=(match, location))
            
        self.status_label.config(text=f"Found {len(results)} results")
        
    def open_result(self, event):
        """Open selected result"""
        sel = self.results_tree.selection()
        if not sel:
            return
            
        item = self.results_tree.item(sel[0])
        location = item['values'][1]
        
        # If it's a file:line format, open the file
        if ":" in str(location):
            parts = str(location).rsplit(":", 1)
            file_path = parts[0]
            try:
                line_num = int(parts[1]) if len(parts) > 1 else 1
            except (ValueError, IndexError):
                line_num = 1
            
            full_path = os.path.join(self.app.project_path, file_path)
            if os.path.exists(full_path) and self.app.editor_tabs:
                self.app.editor_tabs.open_file(full_path)
                # TODO: Jump to line
