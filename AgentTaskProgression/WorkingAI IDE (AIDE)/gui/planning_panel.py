import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class PlanningPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.planning_system = getattr(app, 'planning_system', None)
        
        self.setup_ui()
        self.refresh_timer = None
        self.schedule_refresh()

    def setup_ui(self):
        # Main container with padding
        self.container = ttk.Frame(self, padding=10)
        self.container.pack(fill="both", expand=True)

        # Toolbar
        toolbar = ttk.Frame(self.container)
        toolbar.pack(fill="x", pady=(0, 10))
        
        ttk.Label(toolbar, text="📋 Project Plan", font=("Segoe UI", 12, "bold")).pack(side="left")
        
        ttk.Button(toolbar, text="⟳", width=3, command=self.refresh_all).pack(side="right", padx=2)
        ttk.Button(toolbar, text="Undo", width=6, command=self.undo).pack(side="right", padx=2)
        ttk.Button(toolbar, text="Redo", width=6, command=self.redo).pack(side="right", padx=2)
        ttk.Button(toolbar, text="+ Goal", width=8, command=self.add_goal_dialog).pack(side="right", padx=2)
        ttk.Button(toolbar, text="+ Task", width=8, command=self.add_task_dialog).pack(side="right", padx=2)

        # Paned Window for Goals and Tasks
        self.paned = ttk.PanedWindow(self.container, orient="vertical")
        self.paned.pack(fill="both", expand=True)

        # --- Goals Section ---
        goals_frame = ttk.LabelFrame(self.paned, text="High-Level Goals")
        self.paned.add(goals_frame, weight=1)
        
        self.goals_tree = ttk.Treeview(goals_frame, columns=("Status", "Updated"), show="tree headings", height=5)
        self.goals_tree.heading("#0", text="Goal Description")
        self.goals_tree.heading("Status", text="Status")
        self.goals_tree.heading("Updated", text="Updated")
        self.goals_tree.column("#0", width=300)
        self.goals_tree.column("Status", width=100)
        self.goals_tree.column("Updated", width=150)
        self.goals_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- Tasks Section ---
        tasks_frame = ttk.LabelFrame(self.paned, text="Actionable Tasks")
        self.paned.add(tasks_frame, weight=2)
        
        self.tasks_tree = ttk.Treeview(tasks_frame, columns=("Status", "Priority", "Agent", "Updated"), show="tree headings", height=10)
        self.tasks_tree.heading("#0", text="Task Description")
        self.tasks_tree.heading("Status", text="Status")
        self.tasks_tree.heading("Priority", text="Priority")
        self.tasks_tree.heading("Agent", text="Agent")
        self.tasks_tree.heading("Updated", text="Updated")
        
        self.tasks_tree.column("#0", width=300)
        self.tasks_tree.column("Status", width=100)
        self.tasks_tree.column("Priority", width=80)
        self.tasks_tree.column("Agent", width=100)
        self.tasks_tree.column("Updated", width=150)
        
        self.tasks_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tags for status colors
        self.tasks_tree.tag_configure("pending", foreground="#bbbbbb")
        self.tasks_tree.tag_configure("in_progress", foreground="#0e639c", font=("Segoe UI", 9, "bold"))
        self.tasks_tree.tag_configure("completed", foreground="#4caf50")
        self.tasks_tree.tag_configure("failed", foreground="#f44336")

        # Context Menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Mark as In Progress", command=lambda: self.update_status("in_progress"))
        self.context_menu.add_command(label="Mark as Completed", command=lambda: self.update_status("completed"))
        self.context_menu.add_command(label="Mark as Failed", command=lambda: self.update_status("failed"))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete", command=self.delete_selected)
        
        self.tasks_tree.bind("<Button-3>", self.show_context_menu)
        self.goals_tree.bind("<Button-3>", self.show_context_menu)

    def schedule_refresh(self):
        self.refresh_all()
        self.refresh_timer = self.after(5000, self.schedule_refresh)

    def refresh_all(self):
        if not self.planning_system:
            self.planning_system = getattr(self.app, 'planning_system', None)
            if not self.planning_system: return

        state = self.planning_system.state
        
        # Refresh Goals
        selected_goal = self.goals_tree.selection()
        self.goals_tree.delete(*self.goals_tree.get_children())
        for goal in state.get("goals", []):
            self.goals_tree.insert("", "end", iid=goal["id"], text=goal["description"], 
                                  values=(goal["status"], goal.get("updated_at", "")[:16].replace("T", " ")))
        
        # Refresh Tasks
        selected_task = self.tasks_tree.selection()
        self.tasks_tree.delete(*self.tasks_tree.get_children())
        for task in state.get("tasks", []):
            status = task["status"]
            self.tasks_tree.insert("", "end", iid=task["id"], text=task["description"],
                                  values=(status, task.get("priority", "medium"), 
                                          task.get("assigned_to", "Auto"),
                                          task.get("updated_at", "")[:16].replace("T", " ")),
                                  tags=(status,))

    def show_context_menu(self, event):
        tree = event.widget
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def update_status(self, status):
        selected = self.tasks_tree.selection()
        if not selected:
            selected = self.goals_tree.selection()
            if not selected: return
            goal_id = selected[0]
            self.planning_system.update_goal(goal_id, status=status)
        else:
            task_id = selected[0]
            self.planning_system.update_task_status(task_id, status)
        self.refresh_all()

    def delete_selected(self):
        # Implementation for deletion if needed
        pass

    def undo(self):
        if self.planning_system and self.planning_system.undo():
            self.refresh_all()

    def redo(self):
        if self.planning_system and self.planning_system.redo():
            self.refresh_all()

    def add_goal_dialog(self):
        from tkinter import simpledialog
        desc = simpledialog.askstring("New Goal", "Enter high-level goal description:")
        if desc:
            goal_id = f"goal_{int(datetime.now().timestamp())}"
            self.planning_system.update_goal(goal_id, description=desc)
            self.refresh_all()

    def add_task_dialog(self):
        from tkinter import simpledialog
        desc = simpledialog.askstring("New Task", "Enter actionable task description:")
        if desc:
            self.planning_system.add_task(desc)
            self.refresh_all()
