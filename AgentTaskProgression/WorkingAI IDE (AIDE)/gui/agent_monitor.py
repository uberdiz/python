"""
Agent Monitor - Real-time view of all agent activities
Shows what each agent is doing, their output, and time estimates
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import threading

class AgentMonitor(tk.Toplevel):
    """Window showing real-time agent activity with tabs per agent"""
    
    def __init__(self, parent, orchestrator):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.title("Agent Monitor - Live Activity")
        self.geometry("900x600")
        
        self.agent_tabs = {}  # agent_name -> tab frame
        self.agent_logs = {}  # agent_name -> text widget
        self.agent_status = {}  # agent_name -> status label
        self.agent_timers = {}  # agent_name -> start time
        
        self.setup_ui()
        self.start_refresh()
        
    def setup_ui(self):
        # Top bar with overall status
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        self.overall_status = ttk.Label(top_frame, text="Agents: 0 active", font=("Arial", 11, "bold"))
        self.overall_status.pack(side="left")
        
        ttk.Button(top_frame, text="Refresh", command=self.refresh_all).pack(side="right", padx=5)
        ttk.Button(top_frame, text="Clear All Logs", command=self.clear_all_logs).pack(side="right", padx=5)
        
        # Notebook with tabs per agent
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Summary tab (always present)
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="📊 Summary")
        self.setup_summary_tab()
        
        # Initial agent tabs
        self.refresh_agent_tabs()
        
    def setup_summary_tab(self):
        """Setup the summary overview tab"""
        # Agent status table
        columns = ("Agent", "Role", "Status", "Task", "Time Running", "ETA")
        self.summary_tree = ttk.Treeview(self.summary_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.summary_tree.heading(col, text=col)
            self.summary_tree.column(col, width=120)
            
        self.summary_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Overall log
        log_frame = ttk.LabelFrame(self.summary_frame, text="All Agent Communications")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.all_logs_text = tk.Text(log_frame, height=10, wrap="word", state="disabled")
        self.all_logs_text.pack(fill="both", expand=True, padx=2, pady=2)
        
    def refresh_agent_tabs(self):
        """Refresh tabs for all agents"""
        if not self.orchestrator:
            return
            
        for name, agent in self.orchestrator.agents.items():
            if name not in self.agent_tabs:
                self.create_agent_tab(name, agent)
                
    def create_agent_tab(self, name, agent):
        """Create a tab for an agent"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=f"🤖 {name}")
        self.agent_tabs[name] = tab
        
        # Header with status
        header = ttk.Frame(tab)
        header.pack(fill="x", padx=5, pady=5)
        
        status_label = ttk.Label(header, text=f"Status: {agent.status}", font=("Arial", 10, "bold"))
        status_label.pack(side="left")
        self.agent_status[name] = status_label
        
        role_label = ttk.Label(header, text=f"Role: {agent.role} | Model: {agent.model_name}")
        role_label.pack(side="right")
        
        # Time info
        time_frame = ttk.Frame(tab)
        time_frame.pack(fill="x", padx=5, pady=2)
        
        self.agent_timers[name] = {
            "start": None,
            "label": ttk.Label(time_frame, text="Time: --:--"),
            "eta_label": ttk.Label(time_frame, text="ETA: Unknown")
        }
        self.agent_timers[name]["label"].pack(side="left", padx=5)
        self.agent_timers[name]["eta_label"].pack(side="left", padx=5)
        
        # Current task display
        task_frame = ttk.LabelFrame(tab, text="Current Task / Thinking")
        task_frame.pack(fill="x", padx=5, pady=5)
        
        task_text = tk.Text(task_frame, height=4, wrap="word", state="disabled")
        task_text.pack(fill="x", padx=2, pady=2)
        
        # Output/Activity log
        log_frame = ttk.LabelFrame(tab, text="Agent Activity Log")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        log_text = tk.Text(log_frame, height=15, wrap="word", state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
        log_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        log_text.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.agent_logs[name] = log_text
        
        # Preview area (for code, images, etc.)
        preview_frame = ttk.LabelFrame(tab, text="Output Preview")
        preview_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        preview_text = tk.Text(preview_frame, height=10, wrap="word", state="disabled")
        preview_text.pack(fill="both", expand=True, padx=2, pady=2)
        
    def refresh_all(self):
        """Refresh all agent data"""
        self.refresh_agent_tabs()
        self.update_summary()
        self.update_agent_status()
        
    def update_summary(self):
        """Update the summary table"""
        # Clear existing
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
            
        if not self.orchestrator:
            return
            
        active_count = 0
        for name, agent in self.orchestrator.agents.items():
            status = agent.status
            if status == "working":
                active_count += 1
                
            # Calculate time running
            time_running = "--:--"
            eta = "Unknown"
            if name in self.agent_timers and self.agent_timers[name]["start"]:
                elapsed = datetime.now() - self.agent_timers[name]["start"]
                time_running = str(elapsed).split(".")[0]
                # Simple ETA estimate (assume tasks take ~30s on average)
                eta = "~30s" if status == "working" else "Idle"
                
            self.summary_tree.insert("", "end", values=(
                name,
                agent.role,
                status.upper(),
                "Processing..." if status == "working" else "Waiting",
                time_running,
                eta
            ))
            
        self.overall_status.config(text=f"Agents: {active_count} active / {len(self.orchestrator.agents)} total")
        
    def update_agent_status(self):
        """Update individual agent status displays"""
        if not self.orchestrator:
            return
            
        for name, agent in self.orchestrator.agents.items():
            if name in self.agent_status:
                status = agent.status.upper()
                color = "green" if status == "WORKING" else "gray"
                self.agent_status[name].config(text=f"Status: {status}")
                
            # Track working time
            if agent.status == "working":
                if name not in self.agent_timers or not self.agent_timers[name].get("start"):
                    self.agent_timers[name]["start"] = datetime.now()
            else:
                if name in self.agent_timers:
                    self.agent_timers[name]["start"] = None
                    
    def append_log(self, agent_name, message):
        """Append to agent's log"""
        if agent_name in self.agent_logs:
            log = self.agent_logs[agent_name]
            log.configure(state="normal")
            timestamp = datetime.now().strftime("%H:%M:%S")
            log.insert("end", f"[{timestamp}] {message}\n")
            log.see("end")
            log.configure(state="disabled")
            
        # Also add to all logs
        self.all_logs_text.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.all_logs_text.insert("end", f"[{timestamp}] [{agent_name}] {message}\n")
        self.all_logs_text.see("end")
        self.all_logs_text.configure(state="disabled")
        
    def clear_all_logs(self):
        """Clear all log displays"""
        for log in self.agent_logs.values():
            log.configure(state="normal")
            log.delete("1.0", "end")
            log.configure(state="disabled")
            
        self.all_logs_text.configure(state="normal")
        self.all_logs_text.delete("1.0", "end")
        self.all_logs_text.configure(state="disabled")
        
    def start_refresh(self):
        """Start auto-refresh with safety check"""
        def refresh():
            if self.winfo_exists():
                self.refresh_all()
                self.after(2000, refresh)
        
        self.after(2000, refresh)



def open_agent_monitor(app):
    """Open the Agent Monitor window"""
    if hasattr(app, 'agent_manager') and hasattr(app.agent_manager, 'orchestrator'):
        monitor = AgentMonitor(app.root, app.agent_manager.orchestrator)
        return monitor
    else:
        from tkinter import messagebox
        messagebox.showwarning("No Agents", "No agent orchestrator available. Create agents first.")
        return None
