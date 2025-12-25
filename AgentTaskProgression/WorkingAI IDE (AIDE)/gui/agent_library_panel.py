import tkinter as tk
from tkinter import ttk, scrolledtext
import json

class AgentLibraryWindow(tk.Toplevel):
    def __init__(self, parent, app, on_import_callback):
        super().__init__(parent)
        self.app = app
        self.on_import_callback = on_import_callback
        self.title("Agent Group Library")
        self.geometry("1200x800")
        
        # Mock Data
        self.agent_groups = [
            {
                "id": "web_dev_squad",
                "name": "Web Development Squad",
                "description": "Full-stack web development team with frontend, backend, and testing specialists.",
                "agent_count": 3,
                "tags": ["React", "Django", "Testing"],
                "performance": 95,
                "agents": [
                    {"name": "FrontendDev", "role": "Coder", "model": "gpt-4"},
                    {"name": "BackendDev", "role": "Coder", "model": "gpt-4"},
                    {"name": "QA_Tester", "role": "Tester", "model": "gpt-3.5-turbo"}
                ]
            },
            {
                "id": "data_science_team",
                "name": "Data Science Team",
                "description": "Experts in data analysis, visualization, and machine learning modeling.",
                "agent_count": 2,
                "tags": ["Python", "Pandas", "ML"],
                "performance": 88,
                "agents": [
                    {"name": "DataAnalyst", "role": "Planner", "model": "gpt-4"},
                    {"name": "ML_Engineer", "role": "Coder", "model": "gpt-4"}
                ]
            },
            {
                "id": "mobile_app_crew",
                "name": "Mobile App Crew",
                "description": "Specialized in iOS and Android development using React Native.",
                "agent_count": 4,
                "tags": ["Mobile", "React Native", "iOS", "Android"],
                "performance": 92,
                "agents": [
                    {"name": "MobileLead", "role": "Architect", "model": "gpt-4"},
                    {"name": "IOS_Dev", "role": "Coder", "model": "gpt-4"},
                    {"name": "Android_Dev", "role": "Coder", "model": "gpt-4"},
                    {"name": "MobileTester", "role": "Tester", "model": "gpt-3.5-turbo"}
                ]
            },
            {
                "id": "security_audit",
                "name": "Security Audit Force",
                "description": "Penetration testing and vulnerability assessment specialists.",
                "agent_count": 2,
                "tags": ["Security", "Pentesting", "Audit"],
                "performance": 98,
                "agents": [
                    {"name": "SecAnalyst", "role": "Planner", "model": "gpt-4"},
                    {"name": "WhiteHat", "role": "Tester", "model": "gpt-4"}
                ]
            },
            {
                "id": "content_creation",
                "name": "Content Creation Hub",
                "description": "SEO-optimized content generation and review.",
                "agent_count": 2,
                "tags": ["SEO", "Content", "Marketing"],
                "performance": 85,
                "agents": [
                    {"name": "Writer", "role": "Planner", "model": "gpt-3.5-turbo"},
                    {"name": "Editor", "role": "Summarizer", "model": "gpt-4"}
                ]
            }
        ]
        
        self.selected_groups = set() # Set of group IDs
        self.filtered_groups = list(self.agent_groups)
        
        self.setup_styles()
        self.setup_ui()
        self.bind("<Configure>", self.on_resize)
        
    def setup_styles(self):
        style = ttk.Style()
        style.configure("Card.TFrame", background="#252526", relief="flat")
        style.configure("CardHeader.TLabel", background="#252526", foreground="#ffffff", font=("Segoe UI", 12, "bold"))
        style.configure("CardText.TLabel", background="#252526", foreground="#cccccc", font=("Segoe UI", 10))
        style.configure("Tag.TLabel", background="#0e639c", foreground="#ffffff", font=("Segoe UI", 8), padding=2)
        style.configure("Selected.Card.TFrame", background="#37373d", relief="solid", borderwidth=2)
        
    def setup_ui(self):
        # --- Top Bar (Filtering) ---
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=10, pady=10)
        
        # Search
        ttk.Label(filter_frame, text="Search:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.apply_filters)
        ttk.Entry(filter_frame, textvariable=self.search_var, width=30).pack(side="left", padx=5)
        
        # Sort
        ttk.Label(filter_frame, text="Sort by:").pack(side="left", padx=10)
        self.sort_var = tk.StringVar(value="Relevance")
        sort_combo = ttk.Combobox(filter_frame, textvariable=self.sort_var, 
                                 values=["Relevance", "Performance", "Agent Count", "Alphabetical"], 
                                 state="readonly")
        sort_combo.pack(side="left", padx=5)
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())
        
        # Agent Count Range
        ttk.Label(filter_frame, text="Min Agents:").pack(side="left", padx=10)
        self.min_agents_var = tk.IntVar(value=0)
        tk.Spinbox(filter_frame, from_=0, to=10, textvariable=self.min_agents_var, width=3, command=self.apply_filters).pack(side="left", padx=5)
        
        # --- Main Content (Grid) ---
        self.canvas = tk.Canvas(self, bg="#1e1e1e", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True, padx=10)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # --- Bottom Bar (Selection & Action) ---
        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.selection_label = ttk.Label(action_frame, text="0 groups selected (0 agents total)", font=("Segoe UI", 10, "bold"))
        self.selection_label.pack(side="left", padx=10)
        
        ttk.Button(action_frame, text="Cancel", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(action_frame, text="Import Selected", command=self.confirm_import, style="Accent.TButton").pack(side="right", padx=5)
        
        # Initial Render
        self.render_grid()
        
    def _on_mousewheel(self, event):
        try:
            if self.canvas.winfo_exists():
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except: pass
        
    def apply_filters(self, *args):
        search_term = self.search_var.get().lower()
        min_agents = self.min_agents_var.get()
        sort_mode = self.sort_var.get()
        
        self.filtered_groups = []
        for group in self.agent_groups:
            # Text Search
            if search_term and (search_term not in group["name"].lower() and 
                              search_term not in group["description"].lower() and
                              not any(search_term in t.lower() for t in group["tags"])):
                continue
                
            # Range Filter
            if group["agent_count"] < min_agents:
                continue
                
            self.filtered_groups.append(group)
            
        # Sorting
        if sort_mode == "Performance":
            self.filtered_groups.sort(key=lambda x: x.get("performance", 0), reverse=True)
        elif sort_mode == "Agent Count":
            self.filtered_groups.sort(key=lambda x: x["agent_count"], reverse=True)
        elif sort_mode == "Alphabetical":
            self.filtered_groups.sort(key=lambda x: x["name"])
        
        self.render_grid()
        
    def render_grid(self):
        # Clear existing
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        # Calculate columns based on width
        width = self.winfo_width()
        if width < 100: width = 1000 # Default if not yet drawn
        col_width = 300
        cols = max(1, width // (col_width + 20))
        
        for i, group in enumerate(self.filtered_groups):
            row = i // cols
            col = i % cols
            self.create_card(group, row, col)
            
    def create_card(self, group, row, col):
        is_selected = group["id"] in self.selected_groups
        style_prefix = "Selected." if is_selected else ""
        
        card = ttk.Frame(self.scrollable_frame, style=f"{style_prefix}Card.TFrame", padding=10, width=280, height=200)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False) # Fixed size cards
        
        # Header
        header = ttk.Frame(card, style="Card.TFrame")
        header.pack(fill="x", pady=(0, 5))
        
        # Checkbox
        var = tk.BooleanVar(value=is_selected)
        chk = ttk.Checkbutton(header, variable=var, command=lambda g=group: self.toggle_selection(g["id"]))
        chk.pack(side="left")
        
        ttk.Label(header, text=group["name"], style="CardHeader.TLabel").pack(side="left", padx=5)
        
        # Badge
        ttk.Label(header, text=f"{group['agent_count']} 🤖", style="CardText.TLabel").pack(side="right")
        
        # Description
        ttk.Label(card, text=group["description"], wraplength=260, style="CardText.TLabel").pack(fill="x", pady=5)
        
        # Tags
        tag_frame = ttk.Frame(card, style="Card.TFrame")
        tag_frame.pack(fill="x", pady=5)
        for tag in group["tags"][:3]: # Show first 3 tags
            lbl = tk.Label(tag_frame, text=tag, bg="#0e639c", fg="white", font=("Segoe UI", 8), padx=4, pady=2)
            lbl.pack(side="left", padx=2)
            
        # Performance
        if "performance" in group:
            perf_frame = ttk.Frame(card, style="Card.TFrame")
            perf_frame.pack(fill="x", pady=5, side="bottom")
            ttk.Label(perf_frame, text=f"Performance: {group['performance']}%", style="CardText.TLabel").pack(side="left")
            
            # Simple bar
            canvas = tk.Canvas(perf_frame, width=100, height=6, bg="#333", highlightthickness=0)
            canvas.pack(side="right")
            canvas.create_rectangle(0, 0, group['performance'], 6, fill="#4caf50", width=0)

        # Hover effect
        card.bind("<Enter>", lambda e: self.on_card_hover(e, card, True))
        card.bind("<Leave>", lambda e: self.on_card_hover(e, card, False))
        card.bind("<Button-1>", lambda e: self.preview_group(group))
        
    def on_card_hover(self, event, widget, enter):
        if "Selected" in widget.winfo_class(): return
        widget.configure(style="Selected.Card.TFrame" if enter else "Card.TFrame")
        
    def toggle_selection(self, group_id):
        if group_id in self.selected_groups:
            self.selected_groups.remove(group_id)
        else:
            self.selected_groups.add(group_id)
        self.update_selection_counter()
        self.render_grid() # Re-render to show selection border
        
    def update_selection_counter(self):
        total_agents = sum(g["agent_count"] for g in self.agent_groups if g["id"] in self.selected_groups)
        count = len(self.selected_groups)
        self.selection_label.config(text=f"{count} groups selected ({total_agents} agents total)")
        
    def preview_group(self, group):
        # Preview Dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"Preview: {group['name']}")
        dialog.geometry("400x500")
        
        ttk.Label(dialog, text=group["name"], font=("Segoe UI", 14, "bold")).pack(pady=10)
        ttk.Label(dialog, text=group["description"], wraplength=350).pack(pady=5)
        
        list_frame = ttk.LabelFrame(dialog, text="Agents in Group")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for agent in group["agents"]:
            f = ttk.Frame(list_frame)
            f.pack(fill="x", pady=2)
            ttk.Label(f, text=f"• {agent['name']}", font=("Segoe UI", 10, "bold")).pack(side="left")
            ttk.Label(f, text=f"({agent['role']}) - {agent['model']}").pack(side="left", padx=5)
            
    def on_resize(self, event):
        # Debounce or simple check to avoid too many redraws
        if event.widget == self:
            self.render_grid()
            
    def confirm_import(self):
        if not self.selected_groups:
            return
            
        selected_data = [g for g in self.agent_groups if g["id"] in self.selected_groups]
        
        # Confirmation Dialog
        confirm = tk.Toplevel(self)
        confirm.title("Confirm Import")
        confirm.geometry("400x400")
        
        ttk.Label(confirm, text="Import Summary", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        text = scrolledtext.ScrolledText(confirm, height=10)
        text.pack(fill="both", expand=True, padx=10)
        
        total_agents = 0
        for g in selected_data:
            text.insert(tk.END, f"{g['name']} ({g['agent_count']} agents)\n")
            for a in g["agents"]:
                text.insert(tk.END, f"  - {a['name']}: {a['role']}\n")
            total_agents += g["agent_count"]
            
        ttk.Label(confirm, text=f"Total Agents to Create: {total_agents}").pack(pady=10)
        
        btn_frame = ttk.Frame(confirm)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame, text="Cancel", command=confirm.destroy).pack(side="right", padx=10)
        ttk.Button(btn_frame, text="Confirm Import", 
                  command=lambda: [confirm.destroy(), self.execute_import(selected_data)]).pack(side="right", padx=10)
                  
    def execute_import(self, selected_data):
        self.on_import_callback(selected_data)
        self.destroy()
