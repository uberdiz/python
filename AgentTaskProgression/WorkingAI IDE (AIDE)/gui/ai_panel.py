import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import os
import threading
import time
import json
from datetime import datetime
from core.base_agent import BaseAgent

class DummyAIPanelAgent(BaseAgent):
    def __init__(self, app_instance):
        self.app = app_instance
        self.orchestrator = app_instance.agent_manager.orchestrator if hasattr(app_instance, 'agent_manager') else None

    def process(self, *args, **kwargs):
        pass
try:
    from PIL import Image, ImageTk, ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

class AIPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.voice_handler = None
        self.attached_files = [] # Initialize attached files list
        self.temp_files = [] # Track temp files to cleanup
        self.thumbnails = {} # Keep references to avoid GC
        
        # Async Queue Management
        self.request_queue = []
        self.is_processing_queue = False
        self.queue_lock = threading.Lock()
        
        self.setup_ui()
        self.dummy_agent = DummyAIPanelAgent(self.app)
    
    def setup_ui(self):
        """Setup the AI panel UI (Chat Only)"""
        # --- Main View Container ---
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill="both", expand=True)
        
        # Use PanedWindow for resizable chat/input separation
        self.paned_window = ttk.PanedWindow(self.main_container, orient="vertical")
        self.paned_window.pack(fill="both", expand=True)
        
        # Chat View (Top Pane) with embedded Agent Monitor
        self.chat_display_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.chat_display_frame, weight=4)

        # Horizontal split inside chat view: left=Agent Monitor, right=Chat
        self.monitor_split = ttk.PanedWindow(self.chat_display_frame, orient="horizontal")
        self.monitor_split.pack(fill="both", expand=True)
        self.agent_monitor_frame = ttk.Frame(self.monitor_split)
        self.chat_container = ttk.Frame(self.monitor_split)
        self.monitor_split.add(self.agent_monitor_frame, weight=1)
        self.monitor_split.add(self.chat_container, weight=3)
        
        # Input Area (Bottom Pane)
        self.input_area_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.input_area_frame, weight=1)
        
        self.setup_chat_view()
        
    def setup_chat_view(self):
        """Setup conversational chat UI"""
        # --- Pending Changes Bar (Top of Chat Display) ---
        self.pending_changes_frame = ttk.Frame(self.chat_container, style="Action.TFrame")
        
        # Left side: Icon and Label
        left_info = ttk.Frame(self.pending_changes_frame, style="Action.TFrame")
        left_info.pack(side="left", padx=15, pady=5) # Increased padding
        
        ttk.Label(left_info, text="📄", font=("Segoe UI", 12), style="Action.TLabel").pack(side="left")
        self.pending_label = ttk.Label(left_info, text="0 Files With Changes", 
                                       font=("Segoe UI", 10, "bold"), style="Action.TLabel") # Slightly larger font
        self.pending_label.pack(side="left", padx=8)
        
        # Right side: Buttons
        btn_container = ttk.Frame(self.pending_changes_frame, style="Action.TFrame")
        btn_container.pack(side="right", padx=15, pady=5)
        
        # Reject all (Ghost style)
        self.reject_all_btn = ttk.Button(btn_container, text="Reject all", style="Ghost.TButton",
                                        command=self.discard_pending_changes)
        self.reject_all_btn.pack(side="left", padx=8)
        
        # Accept all (Accent style)
        self.accept_all_btn = ttk.Button(btn_container, text="Accept all", style="Accent.TButton",
                                        command=self.accept_pending_changes)
        self.accept_all_btn.pack(side="left", padx=8)
        
        ttk.Label(btn_container, text="^", font=("Segoe UI", 10), style="Action.TLabel").pack(side="left", padx=5)

        self.quick_row = ttk.Frame(self.chat_container)
        self.quick_row.pack(fill="x", padx=5, pady=(10, 5)) # Increased top padding for better separation
        
        # Get theme colors
        entry_bg = self.app.theme_engine.color_map.get("entry_bg", "#202124")
        entry_fg = self.app.theme_engine.color_map.get("entry_fg", "#ffffff")
        list_bg = self.app.theme_engine.color_map.get("panel_bg", "#2d2d30")
        list_fg = self.app.theme_engine.color_map.get("panel_fg", "#cccccc")
        select_bg = self.app.theme_engine.color_map.get("button_bg", "#094771")

        self.quick_entry = tk.Entry(self.quick_row, relief="solid", bg=entry_bg, fg=entry_fg, 
                                   insertbackground=entry_fg, borderwidth=1)
        self.quick_entry.pack(side="left", fill="x", expand=True, ipady=3) # Added internal padding
        self.quick_count = ttk.Label(self.quick_row, text="0 chars / 0 words")
        self.quick_count.pack(side="right", padx=10)
        
        self.quick_base_suggestions = [
            "open:", "folder/", "selection", "symbols", "agents", "plan", "fix", "refactor", "optimize", "test"
        ]
        self.quick_listbox = tk.Listbox(self.chat_container, height=5, width=32, 
                                      bg=list_bg, fg=list_fg, 
                                      selectbackground=select_bg, relief="flat", borderwidth=0)
        self.quick_listbox.place_forget()
        self.quick_entry.bind("<KeyRelease>", self._quick_on_key_release)
        self.quick_entry.bind("<Tab>", lambda e: self._quick_focus_list())
        self.quick_listbox.bind("<Return>", lambda e: self._quick_insert_suggestion())
        self.quick_listbox.bind("<Double-1>", lambda e: self._quick_insert_suggestion())
        self.quick_listbox.bind("<Tab>", lambda e: self._quick_focus_entry())

        self.chat_history = scrolledtext.ScrolledText(
            self.chat_container,
            height=15,
            wrap="word",
            bg="#1e1e1e",
            fg="#cccccc",
            insertbackground="#ffffff",
            font=("Segoe UI", 10),
            borderwidth=0,
            highlightthickness=0
        )
        self.chat_history.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure Bubble Styles
        self.chat_history.tag_configure("user_msg", background="#0e639c", foreground="white", 
                                       lmargin1=50, lmargin2=50, rmargin=10, 
                                       spacing1=12, spacing3=12, font=("Segoe UI", 10))
        self.chat_history.tag_configure("ai_msg", background="#3e3e42", foreground="#d4d4d4", 
                                       lmargin1=10, lmargin2=10, rmargin=50, 
                                       spacing1=12, spacing3=12, font=("Segoe UI", 10))
        self.chat_history.tag_configure("system_msg", foreground="grey", font=("Segoe UI", 9, "italic"),
                                       spacing1=5, spacing3=5)
        self.chat_history.tag_configure("header", font=("Segoe UI", 8, "bold"), spacing1=10)
        self.chat_history.tag_configure("code_block", background="#0c0c0c", foreground="#cccccc", 
                                       font=("Consolas", 9), lmargin1=25, lmargin2=25,
                                       spacing1=8, spacing3=8)
        
        self.chat_history.config(state='disabled')
        
        # --- Task List Panel (Dropdown) ---
        self.task_container = ttk.Frame(self.chat_container)
        self.task_container.pack(fill="x", side="bottom", padx=5, pady=5)
        
        self.task_header = ttk.Frame(self.task_container)
        self.task_header.pack(fill="x")
        
        self.task_toggle_btn = ttk.Button(self.task_header, text="▼ AI Tasks (0)", width=18, command=self.toggle_task_list)
        self.task_toggle_btn.pack(side="left", padx=5)
        
        self.task_list_frame = ttk.Frame(self.task_container)
        # Hidden by default, will be packed when toggled
        
        self.tasks = []
        
        # --- Enhanced Input Area (Bottom Pane) ---
        self.input_parent = ttk.Frame(self.input_area_frame, padding=10)
        self.input_parent.pack(fill="both", expand=True)
        
        # --- File Preview Area ---
        # Make this scrollable if needed, or just a frame
        self.preview_frame = ttk.Frame(self.input_parent)
        self.preview_frame.pack(fill="x", pady=(0, 5))
        
        # Container for the text area with a nice background (darker)
        text_container = tk.Frame(self.input_parent, bg="#202124", padx=10, pady=10)
        text_container.pack(fill="both", expand=True)
        
        self.text_input = tk.Text(text_container, height=3, bg="#202124", fg="#ffffff", 
                                 insertbackground="#ffffff", font=("Segoe UI", 10),
                                 borderwidth=0, highlightthickness=0, undo=True)
        self.text_input.pack(fill="both", expand=True)

        # Voice Status Label
        self.voice_status_label = tk.Label(text_container, text="", bg="#202124", fg="#888888", font=("Segoe UI", 8, "italic"))
        self.voice_status_label.pack(side="right", anchor="se", pady=(0, 2))

        
        # Placeholder logic
        self.placeholder = "Ask anything (Ctrl+L), @ to mention, / for workflows"
        self.text_input.insert("1.0", self.placeholder)
        self.text_input.config(fg="grey")
        self.text_input.bind("<FocusIn>", self._clear_placeholder)
        self.text_input.bind("<FocusOut>", self._restore_placeholder)
        self.text_input.bind("<Return>", self._handle_return)
        self.text_input.bind("<KeyRelease>", self._on_key_release)
        self.text_input.bind("<Control-v>", self._handle_paste)
        self.text_input.bind("<Tab>", self._accept_autocomplete)
        self.pending_completion = ""
        self.pending_trigger = None
        self._init_autocomplete_structures()
        self.autocomplete_system_prompt = (
            "You are an autocomplete engine embedded inside an AI-powered IDE chat. "
            "Complete grammar, commands, and structured references. "
            "Respect cursor position. Return only the completion tokens to append. "
            "Prefer minimal, high-confidence completions. Never invent commands, agents, files, or syntax. "
            "If confidence < 0.7, return nothing. Output only characters to append, no quotes, no markdown, "
            "no explanation, no newline unless required."
        )
        
        # Performance settings
        self.autocomplete_enabled = bool(self.app.settings.get("autocomplete_enabled", False))
        self._key_debounce_id = None
        self._llm_autocomplete_delay_ms = int(self.app.settings.get("autocomplete_delay_ms", 400))
        # Bottom controls row
        panel_bg = "#252526" # Standard VS Code dark panel bg
        self.controls_row = tk.Frame(self.input_parent, bg=panel_bg)
        self.controls_row.pack(fill="x", pady=(10, 0))
        
        # Initialize Prompt Settings (Hidden)
        self.setup_ai_settings_panel()

        # Agent Monitor Panel
        self.setup_agent_monitor_panel()
        self.schedule_monitor_refresh()
        
        # Left side: + and dropdowns
        left_controls = ttk.Frame(self.controls_row)
        left_controls.pack(side="left")
        
        self.plus_btn = ttk.Button(left_controls, text="+", width=3, command=self._show_plus_menu)
        self.plus_btn.pack(side="left", padx=(0, 5))
        
        # Style Comboboxes to be minimal
        style = ttk.Style()
        style.configure("Minimal.TCombobox", padding=2)
        
        # Model Selector
        self.model_var = tk.StringVar(value="gpt-4o")
        self.model_combo = ttk.Combobox(left_controls, textvariable=self.model_var, width=18, 
                                       style="Minimal.TCombobox")
        # Use IDs, not friendly names, to prevent invalid ID errors
        self.update_model_list() 
        self.model_combo.pack(side="left", padx=5)

        # Agent Selector
        self.agent_var = tk.StringVar(value="Auto")
        self.agent_combo = ttk.Combobox(left_controls, textvariable=self.agent_var, width=12, 
                                       style="Minimal.TCombobox", state="readonly")
        self.agent_combo['values'] = ["Auto"]
        self.agent_combo.pack(side="left", padx=5)
        self.agent_combo.bind("<Button-1>", self.refresh_active_agents)
        self.agent_combo.bind("<<ComboboxSelected>>", self.on_agent_selected)

        # Auto-Agent Toggle
        self.auto_agent_var = tk.BooleanVar(value=self.app.settings.get("agent_auto_approve", False))
        self.auto_agent_check = ttk.Checkbutton(left_controls, text="🚀 Auto-Agent", 
                                               variable=self.auto_agent_var,
                                               command=self.toggle_auto_agent)
        self.auto_agent_check.pack(side="left", padx=10)
        
        # Prompt Settings Toggle
        ttk.Button(left_controls, text="⚙️", width=3, command=self.toggle_ai_settings).pack(side="left", padx=5)
        
        # Enhance Button
        ttk.Button(left_controls, text="✨", width=3, command=self.enhance_prompt, style="Accent.TButton").pack(side="left", padx=5)
        self.auto_analyze_var = tk.BooleanVar(value=self.app.settings.get("auto_image_analyze", True))
        ttk.Checkbutton(left_controls, text="🖼️ Auto-Analyze", variable=self.auto_analyze_var, command=self._toggle_auto_analyze).pack(side="left", padx=5)

        # Right side: Mic, Stop, Send
        right_controls = ttk.Frame(self.controls_row)
        right_controls.pack(side="right")
        
        self.mic_btn = tk.Button(right_controls, text="🎤", font=("Segoe UI", 12), 
                                bg=panel_bg, fg="#d4d4d4", relief="flat",
                                command=self.toggle_voice_input)
        self.mic_btn.pack(side="left", padx=5)
        
        self.stop_btn = tk.Button(right_controls, text="■", bg="#f44336", fg="white", 
                                 width=3, height=1, relief="flat", font=("Arial", 11, "bold"),
                                 command=self.app.stop_agent)
        self.stop_btn.pack(side="left", padx=5)
        
        self.send_btn = tk.Button(right_controls, text="→", bg="#0e639c", fg="white",
                                 width=3, height=1, relief="flat", font=("Arial", 11, "bold"),
                                 command=self.send_message)
        self.send_btn.pack(side="left", padx=2)

    def update_model_list(self):
        """Update model list from AI Manager"""
        if hasattr(self.app, 'ai_manager'):
            models = self.app.ai_manager.get_allowed_models()
            self.model_combo['values'] = models
            
            # Ensure current selection is valid
            current = self.model_var.get()
            if current not in models and models:
                self.model_var.set(models[0])
        else:
             self.model_combo['values'] = ["gpt-4o", "gpt-4o-mini"]

    def setup_agent_monitor_panel(self):
        """Create embedded agent monitor panel within chat view"""
        # Header with detach button
        header = ttk.Frame(self.agent_monitor_frame)
        header.pack(fill="x")
        ttk.Label(header, text="Agent Monitor", font=("Segoe UI", 9, "bold")).pack(side="left", padx=6, pady=4)
        detach_btn = ttk.Button(header, text="❐", width=3, command=self.detach_agent_monitor)
        detach_btn.pack(side="right", padx=4)

        # Treeview for agents
        cols = ("Role", "Status", "Queue", "CPU%", "Mem%", "Last")
        self.agent_tree = ttk.Treeview(self.agent_monitor_frame, columns=cols, show="headings", height=8)
        for c in cols:
            self.agent_tree.heading(c, text=c)
            self.agent_tree.column(c, width=80 if c != "Last" else 160, anchor="w")
        self.agent_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Color tags
        try:
            self.agent_tree.tag_configure("idle", foreground="#bbbbbb")
            self.agent_tree.tag_configure("busy", foreground="#4caf50")
            self.agent_tree.tag_configure("error", foreground="#f44336")
        except Exception:
            pass

        # Refresh interval from settings
        self.monitor_refresh_ms = int(self.app.settings.get("agent_monitor_refresh_ms", 5000))

        # Start hidden until an agent is working
        try:
            self.monitor_split.forget(self.agent_monitor_frame)
        except Exception:
            pass
        self.agent_monitor_visible = False
        self._agent_last_status = {}

    def detach_agent_monitor(self):
        """Open the standalone Agent Monitor window and remember geometry"""
        try:
            from gui.agent_monitor import AgentMonitor
            win = AgentMonitor(self.app.root, self.app.agent_manager.orchestrator) if hasattr(self.app, 'agent_manager') else None
            if win:
                geom = self.app.settings.get("agent_monitor_geom", None)
                if geom:
                    try:
                        win.geometry(geom)
                    except Exception:
                        pass
                def remember():
                    try:
                        self.app.settings["agent_monitor_geom"] = win.geometry()
                        self.app.save_settings(self.app.settings)
                    except Exception:
                        pass
                win.bind("<Configure>", lambda e: remember())
        except Exception:
            pass

    def schedule_monitor_refresh(self):
        try:
            self.refresh_agent_monitor()
        finally:
            try:
                self.after(self.monitor_refresh_ms, self.schedule_monitor_refresh)
            except Exception:
                pass

    def _get_process_usage(self):
        cpu = "N/A"; mem = "N/A"
        try:
            import psutil, os
            p = psutil.Process(os.getpid())
            cpu = f"{p.cpu_percent(interval=None):.0f}"
            mem = f"{p.memory_percent():.0f}"
        except Exception:
            pass
        return cpu, mem

    def refresh_agent_monitor(self):
        """Refresh agent status list"""
        if not hasattr(self.app, 'agent_manager') or not self.app.agent_manager or not self.app.agent_manager.orchestrator:
            # Clear if no orchestrator
            for i in self.agent_tree.get_children():
                self.agent_tree.delete(i)
            try:
                if self.agent_monitor_visible:
                    self.monitor_split.forget(self.agent_monitor_frame)
                    self.agent_monitor_visible = False
            except Exception:
                pass
            return
        orch = self.app.agent_manager.orchestrator
        # Build rows
        for i in self.agent_tree.get_children():
            self.agent_tree.delete(i)
        cpu_all, mem_all = self._get_process_usage()
        any_working = False
        for name, agent in orch.agents.items():
            status = getattr(agent, 'status', 'idle')
            role = getattr(agent, 'role', '-')
            qsize = getattr(agent, 'message_queue', None)
            qn = qsize.qsize() if qsize else 0
            last = agent.history[-1]['content'][:60] + '...' if getattr(agent, 'history', []) else ''
            tag = 'busy' if status == 'working' else ('error' if status == 'error' else 'idle')
            self.agent_tree.insert('', 'end', values=(role, status, qn, cpu_all, mem_all, last), tags=(tag,))
            # Stream status changes into chat
            prev = self._agent_last_status.get(name)
            if prev != status:
                self._agent_last_status[name] = status
                try:
                    self.add_agent_status_box(name, status, qn, last)
                except Exception:
                    pass
            if status == 'working':
                any_working = True
        # Toggle visibility based on activity
        try:
            if any_working and not self.agent_monitor_visible:
                self.monitor_split.add(self.agent_monitor_frame, weight=1)
                self.agent_monitor_visible = True
            if not any_working and self.agent_monitor_visible:
                self.monitor_split.forget(self.agent_monitor_frame)
                self.agent_monitor_visible = False
        except Exception:
            pass

    def add_agent_status_box(self, name, status, qn, last):
        try:
            self.chat_history.config(state='normal')
            box = tk.Frame(self.chat_history, bg=self.chat_history.cget('bg'))
            inner = ttk.Frame(box, padding=6, style="Card.TFrame")
            ttk.Label(inner, text=f"Agent: {name}", font=("Segoe UI", 9, "bold")).pack(anchor='w')
            ttk.Label(inner, text=f"Status: {status.upper()}  Queue: {qn}").pack(anchor='w')
            if last:
                ttk.Label(inner, text=f"Last: {last}", wraplength=380).pack(anchor='w')
            inner.pack()
            self.chat_history.insert('end', "\n")
            self.chat_history.window_create('end', window=box)
            self.chat_history.insert('end', "\n")
            self.chat_history.config(state='disabled')
            self.chat_history.see('end')
        except Exception:
            pass

    def on_agent_selected(self, event=None):
        """Update model combo when agent is selected"""
        agent_name = self.agent_var.get()
        if agent_name != "Auto" and hasattr(self.app, 'agent_manager') and self.app.agent_manager.orchestrator:
             agent = self.app.agent_manager.orchestrator.agents.get(agent_name)
             if agent:
                 self.model_var.set(agent.model_name)
                 self.model_combo['state'] = 'disabled' # Lock model for specific agent
             else:
                 self.model_combo['state'] = 'normal'
        else:
             self.model_combo['state'] = 'normal'

    def update_file_previews(self):
        """Update the file preview area with thumbnails"""
        # Clear existing
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        
        self.thumbnails.clear()
            
        if not self.attached_files:
            return

        for i, file_path in enumerate(self.attached_files):
            frame = ttk.Frame(self.preview_frame, style="Card.TFrame")
            frame.pack(side="left", padx=5, pady=2)
            
            # Icon/Thumbnail
            name = os.path.basename(file_path)
            
            # Try to generate thumbnail if it's an image
            is_image = False
            if HAS_PIL and os.path.exists(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                    try:
                        pil_img = Image.open(file_path)
                        pil_img.thumbnail((60, 60))
                        tk_img = ImageTk.PhotoImage(pil_img)
                        self.thumbnails[file_path] = tk_img
                        
                        lbl = ttk.Label(frame, image=tk_img)
                        lbl.pack(side="top", padx=5, pady=2)
                        is_image = True
                    except Exception:
                        pass
            
            if not is_image:
                lbl = ttk.Label(frame, text="📄", font=("Segoe UI", 20))
                lbl.pack(side="top", padx=5, pady=2)
            
            name_lbl = ttk.Label(frame, text=name, font=("Segoe UI", 8), wraplength=80)
            name_lbl.pack(side="top", padx=5)
            
            # Remove button
            btn = ttk.Button(frame, text="Remove", width=8, style="Ghost.TButton",
                            command=lambda f=file_path: self.remove_attachment(f))
            btn.pack(side="top", padx=2, pady=2)

    def remove_attachment(self, file_path):
        if file_path in self.attached_files:
            self.attached_files.remove(file_path)
            self.update_file_previews()
            # Also notify chat history
            self.add_chat_message("System", f"Removed attachment: {os.path.basename(file_path)}")

    def upload_file(self):
        """Upload a file to context"""
        file_paths = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=[("All Files", "*.*"), ("Images", "*.png;*.jpg;*.jpeg;*.gif")]
        )
        if files:
            for path in files:
                if path not in self.attached_files:
                    self.attached_files.append(path)
            self.update_file_previews()
            self.text_input.focus()
            self._maybe_auto_analyze()

    def _toggle_auto_analyze(self):
        self.app.settings["auto_image_analyze"] = bool(self.auto_analyze_var.get())
        self.app.save_settings(self.app.settings)
        self.add_chat_message("System", f"Auto-Analyze is {'enabled' if self.auto_analyze_var.get() else 'disabled'}.")

    def _maybe_auto_analyze(self):
        try:
            if self.auto_analyze_var.get() and hasattr(self.app, 'run_image_analysis'):
                msg = self.text_input.get("1.0", "end-1c")
                self.app.run_image_analysis(msg)
        except Exception:
            pass

    def refresh_active_agents(self, event=None):
        """Refresh the list of active agents"""
        if hasattr(self.app, 'agent_manager') and self.app.agent_manager and self.app.agent_manager.orchestrator:
            agents = ["Auto"] + list(self.app.agent_manager.orchestrator.agents.keys())
            self.agent_combo['values'] = agents

    def setup_ai_settings_panel(self):
        """Initialize AI settings panel (Model params + Prompt Enhancer)"""
        self.ai_settings_frame = ttk.Frame(self.input_parent)
        
        notebook = ttk.Notebook(self.ai_settings_frame)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- Model Tab ---
        model_frame = ttk.Frame(notebook)
        notebook.add(model_frame, text="Model")
        
        # Temperature
        ttk.Label(model_frame, text="Temperature:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.temp_var = tk.DoubleVar(value=0.7)
        temp_scale = ttk.Scale(model_frame, from_=0.0, to=1.0, variable=self.temp_var, orient="horizontal")
        temp_scale.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Label to show value
        self.temp_lbl = ttk.Label(model_frame, text="0.7")
        self.temp_lbl.grid(row=0, column=2, padx=5, pady=5)
        
        def update_temp_lbl(val):
            self.temp_lbl.config(text=f"{float(val):.2f}")
        temp_scale.configure(command=update_temp_lbl)
        
        # Max Tokens
        ttk.Label(model_frame, text="Max Tokens:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.max_tokens_var = tk.IntVar(value=4000)
        ttk.Entry(model_frame, textvariable=self.max_tokens_var, width=10).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # System Prompt
        ttk.Label(model_frame, text="System Prompt:").grid(row=2, column=0, padx=5, pady=5, sticky="nw")
        self.system_prompt_text = tk.Text(model_frame, height=4, width=40, font=("Segoe UI", 9))
        self.system_prompt_text.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        self.system_prompt_text.insert("1.0", "You are a helpful AI assistant to enhance prompts for an AI agent manager.")

        # --- Enhancer Tab ---
        enhancer_frame = ttk.Frame(notebook)
        notebook.add(enhancer_frame, text="Prompt Enhancer")
        
        ttk.Label(enhancer_frame, text="Style:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.style_var = tk.StringVar(value="Standard")
        ttk.Combobox(enhancer_frame, textvariable=self.style_var, values=["Concise", "Standard", "Verbose", "Technical"], state="readonly").grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(enhancer_frame, text="Complexity:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.complexity_var = tk.StringVar(value="Intermediate")
        ttk.Combobox(enhancer_frame, textvariable=self.complexity_var, values=["Beginner", "Intermediate", "Advanced"], state="readonly").grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.context_aware_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(enhancer_frame, text="Context Aware", variable=self.context_aware_var).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        project_frame = ttk.Frame(notebook)
        notebook.add(project_frame, text="Project")
        ttk.Label(project_frame, text="Max Files:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.proj_max_files = tk.IntVar(value=int(self.app.settings.get("max_files", 10)))
        ttk.Entry(project_frame, textvariable=self.proj_max_files, width=8).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(project_frame, text="Max Chars:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.proj_max_chars = tk.IntVar(value=int(self.app.settings.get("max_chars", 2000)))
        ttk.Entry(project_frame, textvariable=self.proj_max_chars, width=8).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.proj_summarize = tk.BooleanVar(value=bool(self.app.settings.get("summarize_files", True)))
        ttk.Checkbutton(project_frame, text="Summarize Files", variable=self.proj_summarize).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.proj_send_modified = tk.BooleanVar(value=bool(self.app.settings.get("send_modified", True)))
        ttk.Checkbutton(project_frame, text="Send Modified Only", variable=self.proj_send_modified).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        ttk.Label(project_frame, text="Agent Done Sound:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.agent_sound_var = tk.StringVar(value=self.app.settings.get("agent_done_sound", ""))
        sound_entry = ttk.Entry(project_frame, textvariable=self.agent_sound_var, width=40)
        sound_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        def browse_sound():
            path = filedialog.askopenfilename(title="Select Sound", filetypes=[("Audio", "*.mp3 *.mp4 *.wav")])
            if path:
                self.agent_sound_var.set(path)
        ttk.Button(project_frame, text="Browse", command=browse_sound).grid(row=4, column=2, padx=5, pady=5, sticky="w")
        ttk.Button(project_frame, text="Save", command=self._save_project_settings).grid(row=5, column=2, padx=5, pady=10, sticky="e")


    def toggle_ai_settings(self):
        """Toggle visibility of AI settings"""
        if self.ai_settings_frame.winfo_ismapped():
            self.ai_settings_frame.pack_forget()
        else:
            self.ai_settings_frame.pack(fill="x", before=self.controls_row, padx=10, pady=5)

    def enhance_prompt(self):
        """Enhance the current prompt based on settings"""
        current_text = self.text_input.get("1.0", "end-1c")
        if not current_text.strip():
            return
            
        style = self.style_var.get()
        complexity = self.complexity_var.get()
        context_aware = self.context_aware_var.get()
        
        # Disable button while working
        self.text_input.config(state="disabled")
        
        def worker():
            try:
                meta_prompt = f"""
You are an expert prompt engineer for a coding IDE.
Rewrite the user's prompt into a high-clarity task brief with the following format:

Title: one-line imperative title
Goal: concise goal sentence
Context: include any referenced files, images, or project info if present
Requirements:
- enumerate concrete steps the agent should take
- include environment/version targets if mentioned
Constraints:
- list limits, preferences (style, complexity), and guardrails
Deliverables:
- list exact outputs (files, diffs, commands to run, UI changes)
Verification:
- list checks/tests the agent should perform

Tone: {style}; Complexity: {complexity}; ContextAware: {context_aware}
Do not answer the task; produce only the structured brief.

User Prompt:
{current_text}
"""
                if context_aware:
                    # Maybe add project context summary if needed, but for prompt rewriting 
                    # usually we just want style adjustment. 
                    # If "context aware" means "aware of project", we might inject file list?
                    # For now, let's keep it simple.
                    pass
                
                # Use AI Manager
                if hasattr(self.app, 'ai_manager'):
                    response = self.app.ai_manager.generate_response(
                        meta_prompt,
                        temperature=self.temp_var.get(),
                        max_tokens=self.max_tokens_var.get(),
                        system_prompt=self.system_prompt_text.get("1.0", "end-1c")
                    )
                    
                    # Update UI on main thread
                    self.after(0, lambda: self._update_enhanced_prompt(response))
                else:
                    self.after(0, lambda: self._update_enhanced_prompt(f"[Error] AI Manager not available. {current_text}"))
            except Exception as e:
                self.after(0, lambda: self._update_enhanced_prompt(f"[Error] Enhancement failed: {e}"))
        
        threading.Thread(target=worker, daemon=True).start()

    def _save_project_settings(self):
        self.app.settings["max_files"] = int(self.proj_max_files.get())
        self.app.settings["max_chars"] = int(self.proj_max_chars.get())
        self.app.settings["summarize_files"] = bool(self.proj_summarize.get())
        self.app.settings["send_modified"] = bool(self.proj_send_modified.get())
        self.app.settings["agent_done_sound"] = self.agent_sound_var.get().strip()
        self.app.save_settings(self.app.settings)
        self.add_chat_message("System", "Project settings saved.")

    def _update_enhanced_prompt(self, text):
        """Update text input with enhanced prompt"""
        self.text_input.config(state="normal")
        self.text_input.delete("1.0", "end")
        self.text_input.insert("1.0", text.strip())
        self.text_input.focus_set()

    def _show_plus_menu(self):
        """Show context menu for attachments and commands"""
        menu = tk.Menu(self.text_input, tearoff=0)
        menu.add_command(label="📁 Attach File", command=self.upload_file)
        menu.add_command(label="🖼️ Attach Image", command=self.upload_file)
        menu.add_command(label="📸 Capture Screen", command=self.capture_screen_attachment)
        menu.add_command(label="🔲 Select Region", command=self.select_region_attachment)
        menu.add_separator()
        menu.add_command(label="💻 Run Command", command=lambda: self.text_input.insert("end", "/terminal "))
        menu.add_command(label="📝 Add to Plan", command=lambda: self.text_input.insert("end", "/plan "))
        menu.add_command(label="⚙️ Project Settings", command=self.app.open_settings)
        menu.add_separator()
        
        # Workflows
        wf_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="🤖 Workflows", menu=wf_menu)
        wf_menu.add_command(label="Plan & Code", command=lambda: self.run_workflow_chat("plan_and_code"))
        wf_menu.add_command(label="Image → GUI", command=lambda: self.run_workflow_chat("image_to_gui"))
        wf_menu.add_command(label="Test & Fix", command=lambda: self.run_workflow_chat("test_and_fix"))
        
        # Position above the button
        x = self.plus_btn.winfo_rootx()
        y = self.plus_btn.winfo_rooty() - 150
        menu.post(x, y)

    def run_workflow_chat(self, workflow_name):
        """Run a workflow initiated from chat"""
        # We can implement this by inserting a command or directly calling the orchestrator
        # Inserting a command is more 'chatty'
        mapping = {
            "plan_and_code": "/workflow plan_and_code: ",
            "image_to_gui": "/workflow image_to_gui: ",
            "test_and_fix": "/workflow test_and_fix: "
        }
        cmd = mapping.get(workflow_name, "")
        if cmd:
            self.text_input.delete("1.0", "end")
            self.text_input.insert("1.0", cmd)
            self.text_input.focus_set()

    def toggle_voice_input(self):
        """Toggle voice input listening"""
        if not self.voice_handler:
            try:
                from utils.voice_handler import VoiceHandler
                self.voice_handler = VoiceHandler()
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Error", f"Could not load voice handler: {e}")
                return

        # Update device index from settings
        saved_device = self.app.settings.get("audio_device_index")
        if saved_device is not None:
            self.voice_handler.set_device(saved_device)

        if self.voice_handler.is_listening:
            self.voice_handler.stop_listening()
            self.mic_btn.config(bg="#252526", fg="#d4d4d4", text="🎤") # Reset color
        else:
            if not self.voice_handler.available:
                from tkinter import messagebox
                messagebox.showwarning("Voice Input", self.voice_handler.error_message)
                return
                
            self.mic_btn.config(bg="#ff4444", fg="white", text="🛑") # Active color
            self.voice_handler.start_listening(self.on_voice_text, self.on_voice_status)

    def on_voice_text(self, text):
        """Callback for voice text"""
        # We need to run this on main thread
        self.after(0, lambda: self._insert_voice_text(text))
        
    def _insert_voice_text(self, text):
        if self.text_input.get("1.0", "end-1c") == self.placeholder:
            self.text_input.delete("1.0", "end")
            self.text_input.config(fg="#ffffff")
            
        current = self.text_input.get("1.0", "end-1c")
        if current and not current.endswith(" "):
            self.text_input.insert("end", " ")
        self.text_input.insert("end", text)
        self.text_input.see("end")
        
    def on_voice_status(self, status):
        """Callback for voice status"""
        # If stopped, reset button
        def update_ui():
            if status == "Stopped":
                 self.mic_btn.config(bg="#252526", fg="#d4d4d4", text="🎤")
                 self.voice_status_label.config(text="")
            elif "Error" in status:
                 self.mic_btn.config(bg="#ff4444", fg="white", text="⚠️")
                 self.voice_status_label.config(text=status, fg="#ff4444")
            else:
                 self.voice_status_label.config(text=status, fg="#888888")
        
        self.after(0, update_ui)

    def _handle_paste(self, event):
        """Handle paste event to catch images"""
        if not HAS_PIL:
            return None
            
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img:
                import tempfile
                import os
                
                # Create attachments dir if needed
                attach_dir = os.path.join(self.app.project_path, ".ai_attachments") if self.app.project_path else tempfile.gettempdir()
                if not os.path.exists(attach_dir):
                    os.makedirs(attach_dir)
                    
                fname = f"clipboard_{int(time.time())}.png"
                fpath = os.path.join(attach_dir, fname)
                img.save(fpath, "PNG")
                
                self.attached_files.append(fpath)
                self.update_file_previews() # Update previews immediately
                return "break" # Prevent default paste
                
        except Exception as e:
            print(f"Paste error: {e}")
            
        return None # Allow default text paste

    def _clear_placeholder(self, event):
        if self.text_input.get("1.0", "end-1c") == self.placeholder:
            self.text_input.delete("1.0", "end")
            self.text_input.config(fg="#ffffff")

    def _restore_placeholder(self, event):
        if not self.text_input.get("1.0", "end-1c").strip():
            self.text_input.insert("1.0", self.placeholder)
            self.text_input.config(fg="grey")

    def _handle_return(self, event):
        if not event.state & 0x1: # Not Shift+Return
            self.send_message()
            return "break"
        self._auto_resize_input()
        return None

    def _auto_resize_input(self, event=None):
        """Auto-resize input field based on content"""
        try:
            num_lines = int(self.text_input.index('end-1c').split('.')[0])
            # Limit between 3 and 15 lines
            new_height = min(max(num_lines, 3), 15)
            current_height = int(self.text_input.cget("height"))
            if current_height != new_height:
                self.text_input.config(height=new_height)
        except: pass

        self.text_input.focus_set()

    def update_auto_agent_checkbox(self):
        """Update the auto-agent checkbox state based on app settings"""
        self.auto_agent_var.set(self.app.settings.get("agent_auto_approve", False))

    def toggle_auto_agent(self):
        """Toggle the auto-agent setting"""
        val = self.auto_agent_var.get()
        self.app.settings["agent_auto_approve"] = val
        self.app.save_settings(self.app.settings)
        # Notify settings window to update its checkbox
        if hasattr(self.app, 'settings_window') and self.app.settings_window and hasattr(self.app.settings_window, 'window') and self.app.settings_window.window.winfo_exists():
            try:
                self.app.settings_window.ask_for_approval_var.set(not val)
            except: pass
        status = "enabled" if val else "disabled"
        self.add_chat_message("System", f"Auto-Agent is now {status}. Agents will {'automatically' if val else 'request permission to'} execute actions.")

    def get_plan_path(self):
        if not self.app.project_path: return None
        return os.path.join(self.app.project_path, ".ai_dev_plan.json")

    def load_plan(self):
        path = self.get_plan_path()
        if not path or not os.path.exists(path):
            self.plan_editor.insert("1.0", "# Project Plan\n\n- [ ] Task 1...")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.plan_editor.delete("1.0", tk.END)
                self.plan_editor.insert("1.0", data.get("content", ""))
        except: pass

    def save_plan(self):
        path = self.get_plan_path()
        if not path: return
        content = self.plan_editor.get("1.0", "end-1c")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"content": content}, f, indent=2)
            self.app.log_ai("Plan saved.")
        except: pass

    def generate_ai_plan(self):
        if not self.app.project_path: return
        self.app.update_progress("AI Planning...", True)
        def worker():
            try:
                context = self.app.ai_manager.summarize_project(self.app.project_path)
                prompt = f"Generate a project plan based on this context:\n{context}"
                response = self.app.ai_manager.generate_response(prompt)
                self.app.root.after(0, lambda: self.plan_editor.insert(tk.END, "\n\n" + response))
                self.app.update_progress("Plan Generated", False)
            except: self.app.update_progress("Failed", False)
        threading.Thread(target=worker, daemon=True).start()

    def submit_to_agents(self):
        plan = self.plan_editor.get("1.0", "end-1c")
        if not plan.strip(): return
        if hasattr(self.app, 'agent_manager'):
            orchestrator = self.app.agent_manager.orchestrator
            for name in orchestrator.agents:
                orchestrator.route_message("user", name, f"TASK: Execute this plan segment:\n{plan}")
            self.app.log_ai(f"Plan submitted to agents.")
            self.current_mode.set("chat")
            self.switch_mode()
    
    def find_best_agent(self, mode):
        """Find the best active agent for the given mode"""
        if not hasattr(self.app, 'agent_manager') or not self.app.agent_manager or not self.app.agent_manager.orchestrator:
            return "Default"
            
        agents = self.app.agent_manager.orchestrator.agents
        if not agents:
            return "Default"
            
        # Role mapping
        role_map = {
            "Code": ["coder", "architect", "gui_coder"],
            "Test": ["tester", "qa"],
            "Plan": ["planner", "architect"],
            "Chat": ["planner", "coder", "general"]
        }
        
        target_roles = role_map.get(mode, [])
        
        # 1. Look for exact match in active agents
        for name, agent in agents.items():
            if agent.role.lower() in target_roles:
                return name
                
        # 2. If no match, return first available or Default
        return list(agents.keys())[0] if agents else "Default"

    def send_message(self, event=None):
        """Send a message to the AI with agent routing (Asynchronous Queue)"""
        message = self.text_input.get("1.0", "end-1c").strip()
        if message == self.placeholder:
            message = ""
            
        if not message and not self.attached_files:
            return

        # Clear input immediately for responsiveness
        self.text_input.delete("1.0", tk.END)
        self._restore_placeholder(None)
        self.text_input.config(height=3)

        # Capture current state for the request
        selected_model = self.model_var.get()
        target_agent = "Auto"
        if hasattr(self, 'agent_var') and self.agent_var.get() != "Auto":
             target_agent = self.agent_var.get()
        
        # Snapshot attached files before clearing
        current_attachments = list(self.attached_files)
        self.attached_files = []

        # Queue the request
        request = {
            "message": message,
            "attachments": current_attachments,
            "model": selected_model,
            "agent": target_agent,
            "timestamp": time.time()
        }
        
        with self.queue_lock:
            self.request_queue.append(request)
            if not self.is_processing_queue:
                self.is_processing_queue = True
                threading.Thread(target=self._process_request_queue, daemon=True).start()

    def _process_request_queue(self):
        """Background worker to process queued chat requests"""
        while True:
            request = None
            with self.queue_lock:
                if not self.request_queue:
                    self.is_processing_queue = False
                    break
                request = self.request_queue.pop(0)
            
            if not request:
                continue

            try:
                self._handle_request(request)
            except Exception as e:
                self.after(0, lambda: self.add_chat_message("System", f"Error processing request: {e}"))
            
            # Small delay to prevent tight loop
            time.sleep(0.1)

    def _handle_request(self, request):
        """Internal handler for a single chat request (running in worker thread)"""
        message = request["message"]
        attachments = request["attachments"]
        selected_model = request["model"]
        target_agent = request["agent"]

        # Resolve Context
        conversation_history = []
        # Get all text from the chat_history widget
        full_chat_content = self.chat_history.get("1.0", tk.END)
        # Split content by lines and process
        lines = full_chat_content.split('\n')
        current_role = None
        current_content = []
        for line in lines:
            if line.startswith("You:"):
                if current_role and current_content:
                    conversation_history.append({"role": current_role, "content": "\n".join(current_content).strip()})
                current_role = "user"
                current_content = [line[len("You:"):].strip()]
            elif line.startswith("AI:"):
                if current_role and current_content:
                    conversation_history.append({"role": current_role, "content": "\n".join(current_content).strip()})
                current_role = "assistant"
                current_content = [line[len("AI:"):].strip()]
            elif line.startswith("System:"):
                if current_role and current_content:
                    conversation_history.append({"role": current_role, "content": "\n".join(current_content).strip()})
                current_role = "system"
                current_content = [line[len("System:"):].strip()]
            else:
                current_content.append(line.strip())
        if current_role and current_content:
            conversation_history.append({"role": current_role, "content": "\n".join(current_content).strip()})
        # Limit history to 10 turns
        conversation_history = conversation_history[-10:]

        # Pass conversation history to the request for agents to use
        request["conversation_history"] = conversation_history

        # Handle slash commands (synchronous for now, but in worker thread)
        if message.startswith("/"):
            if self._handle_slash_command(message):
                return

        # Check for @agent mentions (dynamic)
        if message.startswith("@"):
            parts = message.split(" ", 1)
            mention = parts[0][1:].lower()
            names = []
            if hasattr(self.app, 'agent_manager') and self.app.agent_manager and self.app.agent_manager.orchestrator:
                names = [n.lower() for n in self.app.agent_manager.orchestrator.agents.keys()]
            
            default_known = ["coder", "architect", "terminal", "image", "default"]
            candidates = set(names or default_known)
            
            if mention in candidates:
                if names:
                    for n in self.app.agent_manager.orchestrator.agents.keys():
                        if n.lower() == mention:
                            target_agent = n
                            break
                else:
                    target_agent = mention.capitalize()
                message = parts[1] if len(parts) > 1 else ""

        if message or attachments:
            # Check for image attached - route to Vision/Image agent
            is_image = False
            if attachments:
                if any(f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')) for f in attachments):
                    target_agent = "Image"
                    is_image = True

            # Auto-detect file references and include attachments
            try:
                if hasattr(self.app, 'project_tree') and self.app.project_tree:
                    project_files = self.app.project_tree.get_all_files()
                    basenames = {os.path.basename(p): p for p in project_files}
                    tokens = [t.strip('.,:;"\'') for t in message.split()] if message else []
                    for t in tokens:
                        if t in basenames and basenames[t] not in attachments:
                            attachments.append(basenames[t])
            except Exception:
                pass

            # Include attached files in message for context
            full_message = message
            if attachments:
                file_info = "\n[Attached files: " + ", ".join(attachments) + "]"
                full_message = full_message + file_info if full_message else file_info
            
            # Apply Prompt Optimization
            if hasattr(self, 'style_var'):
                style = self.style_var.get()
                complexity = self.complexity_var.get()
                context_aware = self.context_aware_var.get()
                
                if style != "Standard" or complexity != "Intermediate" or not context_aware:
                    opt = []
                    if style != "Standard": opt.append(f"Style: {style}")
                    if complexity != "Intermediate": opt.append(f"Complexity: {complexity}")
                    if not context_aware: opt.append("Context: Ignore previous history")
                    full_message += f"\n\n[SYSTEM: {'; '.join(opt)}]"

            # Update UI on main thread - Show user message
            display_msg = full_message
            if is_image:
                 display_msg = f"🖼️ [Image Analysis Request]\n{message}"
            
            self.after(0, lambda m=display_msg: self.add_chat_message("You", m))
            
            # Resolve Context (Files, Agents, etc.)
            final_message = full_message
            try:
                from core.context_resolver import ContextResolver
                resolver = ContextResolver(self.app)
                # Ensure we pass the attachments for proper context
                final_message = resolver.resolve(full_message)
            except Exception as e:
                print(f"Context resolution failed: {e}")
            
            # Route message specifically
            try:
                if hasattr(self.app, 'route_chat_to_agent'):
                    # Use after(0, ...) if route_chat_to_agent isn't thread-safe, 
                    # but usually it starts its own worker thread anyway.
                    self.app.route_chat_to_agent(final_message, target_agent, selected_model, conversation_history)
                else:
                    self.app.process_chat_message(final_message, selected_model)
            except Exception as e:
                self.after(0, lambda err=e: self.add_chat_message("System", f"Routing error: {err}"))

    def capture_screen_attachment(self):
        try:
            from core.vision import VisionProcessor
            vp = VisionProcessor(self.app.root)
            img = vp.capture_screen()
            if img is None:
                self.add_chat_message("System", "Screen capture unavailable")
                return
            import tempfile
            fd, path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            img.save(path)
            self.attached_files.append(path)
            self.update_file_previews()
            self.add_chat_message("System", "Captured screen")
            self._maybe_auto_analyze()
        except Exception as e:
            self.add_chat_message("System", f"Capture failed: {e}")

    def select_region_attachment(self):
        try:
            from core.vision import VisionProcessor
            vp = VisionProcessor(self.app.root)
            img = vp.select_region()
            if img is None:
                self.add_chat_message("System", "No region selected")
                return
            import tempfile
            fd, path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            img.save(path)
            self.attached_files.append(path)
            self.update_file_previews()
            self.add_chat_message("System", "Captured region")
            self._maybe_auto_analyze()
        except Exception as e:
            self.add_chat_message("System", f"Region capture failed: {e}")

    def _handle_slash_command(self, text):
        """Parse and execute slash command; return True if handled"""
        cmd = text.split()
        if not cmd:
            return False
        head = cmd[0].lower()
        # /terminal <command>
        if head == "/terminal" and len(cmd) > 1:
            run_cmd = text[len(cmd[0])+1:]
            if self.dummy_agent.requires_approval():
                self.add_chat_message("System", f"💡 I suggest running command: `{run_cmd}`\n(Auto-Agent is disabled, please execute manually in terminal or enable Auto-Agent.)")
            else:
                self.add_chat_message("System", f"Running command: {run_cmd}")
                if hasattr(self.app, 'execute_shell_command'):
                    self.app.execute_shell_command(run_cmd)
            return True
        # /workflow <name>:
        if head == "/workflow" and len(cmd) > 1:
            wf = cmd[1].strip(':')
            ctx = {"project_path": self.app.project_path}
            if hasattr(self.app, 'agent_manager') and self.app.agent_manager.orchestrator:
                self.app.agent_manager.orchestrator.run_workflow(wf, ctx)
                self.add_chat_message("System", f"Workflow started: {wf}")
                return True
        # /plan <text>
        if head == "/plan" and len(cmd) > 1:
            content = text[len(cmd[0])+1:]
            try:
                if hasattr(self, 'plan_editor') and self.plan_editor:
                    self.plan_editor.insert("end", "\n\n" + content)
                    self.save_plan()
                else:
                    # Fallback: log to chat
                    self.add_chat_message("System", "Plan editor not available.")
            except Exception:
                self.add_chat_message("System", "Failed to add to plan.")
            return True
        return False
            
    def upload_file(self):
        """Upload file(s) to attach to message"""
        from tkinter import filedialog
        
        files = filedialog.askopenfilenames(
            title="Select Files to Attach",
            filetypes=[
                ("All Files", "*.*"),
                ("Images", "*.png *.jpg *.jpeg *.gif *.webp"),
                ("Code", "*.py *.js *.html *.css *.lua *.cs"),
                ("Text", "*.txt *.md *.json")
            ]
        )
        
        if files:
            self.attached_files.extend(files)
            # Show indicator
            for f in files:
                fname = os.path.basename(f)
                icon = "📸" if f.lower().endswith(('.png', '.jpg', '.jpeg')) else "📎"
                self.add_chat_message("System", f"{icon} Attached: {fname}")
            
    def set_input(self, text):
        """Set input field text"""
        self.text_input.delete("1.0", tk.END)
        self.text_input.insert("1.0", text)
        self._clear_placeholder(None)
        self.text_input.focus()
    
    def add_chat_message(self, sender, message):
        """Add a message to the chat history with bubble style and markdown support"""
        sender_lower = sender.lower()
        if sender_lower == "system":
            if not self.app.settings.get("show_system_messages", True):
                return
        
        self.chat_history.config(state='normal')
        
        tag = "ai_msg"
        if sender_lower == "you":
            tag = "user_msg"
        elif sender_lower == "system":
            tag = "system_msg"
            
        # Add avatar in header
        avatar = "🤖" if tag == "ai_msg" else ("🧑" if tag == "user_msg" else "⚙️")
        self.chat_history.insert("end", f"\n{avatar} {sender}\n", ("header", tag))
        
        # Split message into lines to handle bold headers and code blocks
        lines = message.split('\n')
        for line in lines:
            if line.startswith("**") and line.endswith("**"):
                # Markdown bold header (e.g., **PHASE 1: PLANNING**)
                header_text = line.strip("*")
                self.chat_history.insert("end", f"{header_text}\n", ("header", tag))
            elif line.startswith("```"):
                # Start or end of code block - the existing logic handles blocks but here we just pass through
                self.chat_history.insert("end", f"{line}\n", tag)
            else:
                self.chat_history.insert("end", f"{line}\n", tag)
        
        self.chat_history.config(state='disabled')
        self.chat_history.see("end")

    def toggle_task_list(self):
        """Toggle visibility of the task list"""
        if self.task_list_frame.winfo_ismapped():
            self.task_list_frame.pack_forget()
            self.task_toggle_btn.config(text=f"▼ AI Tasks ({len(self.tasks)})")
        else:
            self.task_list_frame.pack(fill="x", padx=15, pady=5)
            self.task_toggle_btn.config(text=f"▲ AI Tasks ({len(self.tasks)})")
            self._render_tasks()

    def update_tasks(self, task_list):
        """Update the task list and refresh UI"""
        self.tasks = task_list
        self.task_toggle_btn.config(text=f"{'▲' if self.task_list_frame.winfo_ismapped() else '▼'} AI Tasks ({len(self.tasks)})")
        if self.task_list_frame.winfo_ismapped():
            self._render_tasks()
        # Automatically show if there are tasks and not already showing
        elif self.tasks:
            self.toggle_task_list()

    def _render_tasks(self):
        """Render task items in the task list frame"""
        # Clear existing
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()
            
        if not self.tasks:
            ttk.Label(self.task_list_frame, text="No tasks pending", font=("Segoe UI", 9, "italic")).pack(anchor="w")
            return

        # Spinner frames for animation
        spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_spinner_frame = getattr(self, "current_spinner_frame", 0)
        spinner_char = spinner_frames[self.current_spinner_frame % len(spinner_frames)]

        for task in self.tasks:
            task_frame = ttk.Frame(self.task_list_frame)
            task_frame.pack(fill="x", pady=2)
            
            status = task.get("status", "pending")
            if task.get("done"): # Backward compatibility
                status = "completed"
            
            if status == "completed":
                status_icon = "✅"
                color = "#888888"
            elif status == "in_progress":
                status_icon = spinner_char
                color = "#ffffff"
            else:
                status_icon = "○"
                color = "#ffffff"
            
            # Try to get background from a widget that definitely has it, or use default
            bg_color = "#2d2d2d" # Default dark color
            try:
                bg_color = self.chat_history.cget("bg")
            except:
                pass
                
            lbl = tk.Label(task_frame, text=f"{status_icon} {task.get('name')}", 
                           font=("Segoe UI", 9), fg=color, bg=bg_color)
            lbl.pack(side="left")

        # If any task is in progress, schedule a redraw for the spinner
        if any(t.get("status") == "in_progress" for t in self.tasks):
            self.current_spinner_frame += 1
            self.after(100, self._render_tasks_spinner_only)

    def _render_tasks_spinner_only(self):
        """Optimized redraw for spinner animation"""
        if self.task_list_frame.winfo_ismapped():
            self._render_tasks()

    def set_chat_history(self, history_items):
        """Replace chat view with provided history items"""
        self.chat_history.config(state='normal')
        self.chat_history.delete("1.0", "end")
        for item in history_items:
            sender = item.get("from", "unknown")
            content = item.get("content", "")
            self.add_chat_message(sender if sender != "user" else "You", content)
        self.chat_history.config(state='disabled')
        self.chat_history.see("end")
    def add_action_button(self, text, command):
        """Add a button to the chat history for user actions"""
        self.chat_history.config(state='normal')
        self.chat_history.insert("end", "\n")
        
        # Create a frame for the button to give it some padding
        btn_frame = tk.Frame(self.chat_history, bg=self.chat_history.cget("bg"), padx=10, pady=5)
        
        btn = ttk.Button(btn_frame, text=text, command=command, style="Accent.TButton")
        btn.pack()
        
        self.chat_history.window_create("end", window=btn_frame)
        self.chat_history.insert("end", "\n")
        
        self.chat_history.config(state='disabled')
        self.chat_history.see("end")
    
    def display_suggested_changes(self, changes):
        """Display AI suggested changes with bubble style"""
        self.chat_history.config(state='normal')
        
        # Header for the suggestion
        self.chat_history.insert("end", "\nAI SUGGESTED CHANGES\n", ("header", "ai_msg"))
        
        if "analysis" in changes:
            self.chat_history.insert("end", f"Analysis: {changes['analysis']}\n\n", "ai_msg")
        
        if "fixes" in changes:
            for filename, content in changes["fixes"].items():
                self.chat_history.insert("end", f"File: {filename}\n", ("header", "ai_msg"))
                self.chat_history.insert("end", f"{content[:500]}...\n", ("code_block", "ai_msg"))
                self.chat_history.insert("end", "\n", "ai_msg")
        
        self.chat_history.config(state='disabled')
        self.chat_history.see("end")
    
    def display_review(self, review):
        """Display code review with bubble style"""
        self.add_chat_message("AI - Review", review)

    def show_pending_changes(self, change_count):
        """Show the pending changes bar"""
        self.pending_label.config(text=f"{change_count} Files With Changes")
        self.pending_changes_frame.pack(side="top", fill="x", before=self.chat_history)

    def hide_pending_changes(self):
        """Hide the pending changes bar"""
        self.pending_changes_frame.pack_forget()

    def accept_pending_changes(self):
        """Accept all AI suggested changes"""
        if hasattr(self.app, 'apply_ai_changes'):
            self.app.apply_ai_changes()

    def discard_pending_changes(self):
        """Discard all AI suggested changes"""
        if hasattr(self.app, 'ai_suggested_changes'):
            self.app.ai_suggested_changes = {}
            self.hide_pending_changes()
            self.add_chat_message("System", "AI suggested changes discarded.")
    
    def apply_theme(self, color_map):
        """Apply theme colors"""
        self.chat_history.configure(
            bg=color_map.get("text_bg", "#1e1e1e"),
            fg=color_map.get("text_fg", "#cccccc"),
            insertbackground=color_map.get("text_insert", "#ffffff")
        )
        
    def record_feedback(self, is_good):
        """Record feedback on AI response"""
        import json
        import os
        from datetime import datetime
        
        if not self.last_response:
            return
            
        feedback_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feedback.json")
        
        # Load existing feedback
        feedback_data = []
        if os.path.exists(feedback_path):
            try:
                with open(feedback_path, "r", encoding="utf-8") as f:
                    feedback_data = json.load(f)
            except:
                pass
                
        # Add new feedback
        feedback_data.append({
            "timestamp": datetime.now().isoformat(),
            "response_snippet": self.last_response[:100] if self.last_response else "",
            "rating": "good" if is_good else "bad",
            "model": self.app.settings.get("model", "unknown")
        })
        
        # Save
        try:
            with open(feedback_path, "w", encoding="utf-8") as f:
                json.dump(feedback_data, f, indent=2)
            
            rating = "👍" if is_good else "👎"
            self.add_chat_message("System", f"Feedback recorded: {rating}")
        except Exception as e:
            self.add_chat_message("System", f"Failed to save feedback: {e}")

    def check_autocomplete(self, event):
        """Check for autocomplete triggers"""
        content = self.text_input.get("1.0", "end-1c")
        cursor_pos = self.text_input.index(tk.INSERT)
        
        # Simple line/col parsing for Text widget
        line, col = map(int, cursor_pos.split('.'))
        
        # Get current line text up to cursor
        line_content = self.text_input.get(f"{line}.0", cursor_pos)
        
        if not line_content:
            self.hide_suggestions()
            return
            
        if "@" in line_content:
            start = line_content.rfind("@")
            query = line_content[start+1:].lower()
            if " " not in query:
                # Use dynamic agent names when available
                options = ["Coder", "Architect", "Terminal", "Image", "Default"]
                try:
                    if hasattr(self.app, 'agent_manager') and self.app.agent_manager.orchestrator:
                        options = list(self.app.agent_manager.orchestrator.agents.keys()) or options
                except Exception:
                    pass
                options = [v for v in options if v.lower().startswith(query)]
                self.show_suggestions(options, query, "@")
                return
        
        if "#" in line_content:
            start = line_content.rfind("#")
            query = line_content[start+1:].lower()
            if " " not in query:
                files = []
                try:
                    # Include open files
                    if hasattr(self.app, 'editor_tabs'):
                        files.extend([os.path.basename(f) for f in self.app.editor_tabs.get_open_files()])
                    # Include project files
                    if getattr(self.app, 'project_path', None):
                        for root, dirs, fs in os.walk(self.app.project_path):
                            dirs[:] = [d for d in dirs if d not in ['.git','__pycache__','node_modules','venv','.idea','.vscode']]
                            for fn in fs:
                                if fn.endswith(('.py','.md','.txt','.json','.yml','.yaml','.html','.css','.js')):
                                    files.append(fn)
                except Exception:
                    pass
                # Deduplicate and filter
                seen = set(); unique_files = []
                for f in files:
                    if f not in seen:
                        seen.add(f); unique_files.append(f)
                options = [f for f in unique_files if f.lower().startswith(query)]
                self.show_suggestions(options, query, "#")
                return

        if "/" in line_content:
            start = line_content.rfind("/")
            query = line_content[start+1:].lower()
            if " " not in query:
                options = ["workflow", "terminal", "plan"]
                options = [o for o in options if o.startswith(query)]
                self.show_suggestions(options, query, "/")
                return
                
        self.hide_suggestions()

    def _on_key_release(self, event):
        """Debounced key release handler for responsive typing"""
        try:
            self._auto_resize_input()
            if self._key_debounce_id:
                try:
                    self.after_cancel(self._key_debounce_id)
                except Exception:
                    pass
            def _run_checks():
                try:
                    self.check_text_quality()
                    if self.autocomplete_enabled:
                        self._update_autocomplete_state()
                except Exception:
                    pass
            self._key_debounce_id = self.after(self._llm_autocomplete_delay_ms, _run_checks)
        except Exception:
            pass

    def check_text_quality(self):
        """Lightweight grammar/text quality heuristics with inline highlights"""
        try:
            # Configure error tag once
            if not getattr(self, '_quality_tag_configured', False):
                self.text_input.tag_configure("error", underline=False, background="#3a1f1f")
                self._quality_tag_configured = True
            # Clear previous
            self.text_input.tag_remove("error", "1.0", "end")
            text = self.text_input.get("1.0", "end-1c")
            if not text or text == self.placeholder:
                return
            # Heuristics
            issues = []
            # Common misspelling
            if " teh " in f" {text} ":
                issues.append((text.find("teh"), 3))
            # No ending punctuation on long input
            if len(text) > 60 and text.strip()[-1] not in ".!?":
                issues.append((len(text)-1, 1))
            # Multiple spaces
            import re
            for m in re.finditer(r"\s{3,}", text):
                issues.append((m.start(), m.end()-m.start()))
            # Apply highlights
            for start, length in issues:
                if start >= 0:
                    linecol_start = self.text_input.index(f"1.0+{start}c")
                    linecol_end = self.text_input.index(f"1.0+{start+length}c")
                    self.text_input.tag_add("error", linecol_start, linecol_end)
            # Show status label
            count = len(issues)
            if not hasattr(self, 'quality_label'):
                self.quality_label = ttk.Label(self.controls_row, text="", foreground="#ff8888")
                self.quality_label.pack(side="right", padx=8)
            self.quality_label.config(text=f"Grammar issues: {count}" if count else "")
        except Exception:
            pass

    def show_suggestions(self, options, query, trigger):
        """Show the suggestion popup"""
        if not options:
            self.hide_suggestions()
            return
            
        if not self.suggestion_list:
            self.suggestion_list = tk.Listbox(self.app.root, height=5, width=30, 
                                            bg="#2d2d30", fg="#cccccc", selectbackground="#094771")
            self.suggestion_list.bind("<Double-1>", lambda e: self.insert_suggestion(trigger))
            self.suggestion_list.bind("<Return>", lambda e: self.insert_suggestion(trigger))
            self.suggestion_list.bind("<Tab>", lambda e: self.insert_suggestion(trigger))
            
        self.suggestion_list.delete(0, tk.END)
        for opt in options:
            self.suggestion_list.insert(tk.END, opt)
            
        # Position near input
        x = self.text_input.winfo_rootx()
        y = self.text_input.winfo_rooty() - 120 # Show above
        self.suggestion_list.place(x=x, y=y)
        self.suggestion_list.lift()
        
        # Bind Tab on text input when suggestions are shown
        self.text_input.bind("<Tab>", lambda e: self.handle_tab_key(trigger))

    def handle_tab_key(self, trigger):
        """Handle Tab key specifically to insert first or selected suggestion"""
        if not self.suggestion_list or not self.suggestion_list.winfo_viewable():
            return None # Let default Tab behavior happen if hidden
            
        if not self.suggestion_list.curselection():
            self.suggestion_list.selection_set(0)
            
        self.insert_suggestion(trigger)
        return "break" # Prevent focus change

    def hide_suggestions(self):
        """Hide the suggestion popup"""
        if self.suggestion_list:
            self.suggestion_list.place_forget()
        self.text_input.unbind("<Tab>")

    def insert_suggestion(self, trigger):
        """Insert selected suggestion into entry"""
        if not self.suggestion_list or not self.suggestion_list.curselection():
            return
            
        selection = self.suggestion_list.get(self.suggestion_list.curselection())
        cursor_pos = self.text_input.index(tk.INSERT)
        line, col = map(int, cursor_pos.split('.'))
        
        line_content = self.text_input.get(f"{line}.0", cursor_pos)
        start = line_content.rfind(trigger)
            
        if start != -1:
            frag = line_content[start+1:]
            if trigger == "#" and frag.startswith("open:"):
                base_start = start + 1 + len("open:")
                self.text_input.delete(f"{line}.{base_start}", cursor_pos)
                self.text_input.insert(f"{line}.{base_start}", selection + " ")
            elif trigger == "#" and frag.startswith("folder/"):
                base_start = start + 1 + len("folder/")
                self.text_input.delete(f"{line}.{base_start}", cursor_pos)
                # ensure trailing slash for traversal
                suff = selection
                if not suff.endswith("/"):
                    suff = suff + "/"
                self.text_input.insert(f"{line}.{base_start}", suff)
            else:
                # Delete from trigger to cursor
                self.text_input.delete(f"{line}.{start+1}", cursor_pos)
                # Insert selection
                self.text_input.insert(f"{line}.{start+1}", selection + " ")
            
        self.hide_suggestions()
        self.text_input.focus_set()

    def _quick_on_key_release(self, event):
        content = self.quick_entry.get()
        chars = len(content)
        words = len(content.strip().split()) if content.strip() else 0
        self.quick_count.config(text=f"{chars} chars / {words} words")
        if "#" not in content:
            try:
                self.quick_listbox.place_forget()
                self.quick_listbox.delete(0, tk.END)
            except Exception:
                pass
            return
        start = content.rfind("#")
        query = content[start+1:].lower()
        if (not query) or (" " in query):
            try:
                self.quick_listbox.place_forget()
                self.quick_listbox.delete(0, tk.END)
            except Exception:
                pass
            return
        matches = [s for s in self.quick_base_suggestions if s.lower().startswith(query)]
        if not matches:
            try:
                self.quick_listbox.place_forget()
                self.quick_listbox.delete(0, tk.END)
            except Exception:
                pass
            return
        try:
            self.quick_listbox.delete(0, tk.END)
            for m in matches:
                self.quick_listbox.insert(tk.END, m)
            x = self.quick_entry.winfo_rootx()
            y = self.quick_entry.winfo_rooty() + self.quick_entry.winfo_height()
            self.quick_listbox.place(x=x, y=y)
            self.quick_listbox.lift()
        except Exception:
            pass

    def _quick_focus_list(self):
        try:
            if self.quick_listbox.size() > 0:
                self.quick_listbox.focus_set()
                if not self.quick_listbox.curselection():
                    self.quick_listbox.selection_set(0)
                return "break"
        except Exception:
            return "break"

    def _quick_focus_entry(self):
        try:
            self.quick_entry.focus_set()
            return "break"
        except Exception:
            return "break"

    def _quick_insert_suggestion(self):
        try:
            if not self.quick_listbox.curselection():
                return "break"
            sel = self.quick_listbox.get(self.quick_listbox.curselection()[0])
            content = self.quick_entry.get()
            start = content.rfind("#")
            if start != -1:
                new_text = content[:start+1] + sel + " "
                self.quick_entry.delete(0, tk.END)
                self.quick_entry.insert(0, new_text)
                self.quick_entry.icursor(len(new_text))
            self.quick_listbox.place_forget()
            self.quick_entry.focus_set()
            return "break"
        except Exception:
            return "break"

    class _Trie:
        def __init__(self):
            self.t = {}
        def insert(self, w):
            n = self.t
            for c in w:
                if c not in n:
                    n[c] = {}
                n = n[c]
            n["$"] = True
        def shortest_completion(self, prefix):
            n = self.t
            for c in prefix:
                if c not in n:
                    return None
                n = n[c]
            s = ""
            while "$" not in n:
                if not n:
                    return None
                c = sorted(n.keys())[0]
                s += c
                n = n[c]
            return s

    def _init_autocomplete_structures(self):
        cmds = [
            "fix","refactor","optimize","test","explain","doc","convert","analyze","summarize","vision",
            "workflow","terminal","plan"
        ]
        self._cmd_trie = self._Trie()
        for c in cmds:
            self._cmd_trie.insert(c)
        self._grammar_freq = {
            "should": 50,"function": 40,"return": 45,"class": 35,"import": 60,"from": 55,
            "while": 30,"for": 50,"if": 70,"else": 65,"elif": 40,
            "def": 80,"try": 40,"except": 38,"finally": 25,"with": 42,
            "variable": 20,"parameters": 18,"argument": 22,"context": 15
        }

    def _inside_code_block(self, text, cursor_index):
        up_to = self.text_input.get("1.0", cursor_index)
        count = up_to.count("```")
        return count % 2 == 1

    def _list_agents(self):
        opts = []
        try:
            if hasattr(self.app, "agent_manager") and self.app.agent_manager.orchestrator:
                opts = list(self.app.agent_manager.orchestrator.agents.keys())
        except Exception:
            pass
        return opts

    def _list_open_files(self):
        names = []
        try:
            if hasattr(self.app, "editor_tabs") and self.app.editor_tabs:
                files = self.app.editor_tabs.get_open_files()
                import os
                names = [os.path.basename(f) for f in files]
        except Exception:
            pass
        return names

    def _list_open_paths(self):
        paths = []
        try:
            if hasattr(self.app, "editor_tabs") and self.app.editor_tabs:
                files = self.app.editor_tabs.get_open_files()
                import os
                base = getattr(self.app, "project_path", None)
                for f in files:
                    if base:
                        p = os.path.relpath(f, base)
                    else:
                        p = os.path.basename(f)
                    paths.append(p.replace("\\", "/"))
        except Exception:
            pass
        return paths

    def _list_project_dirs(self, max_count=300):
        items = []
        try:
            import os
            root = getattr(self.app, "project_path", None) or os.getcwd()
            for dirpath, dirnames, filenames in os.walk(root):
                rel = os.path.relpath(dirpath, root).replace("\\", "/")
                if rel == ".":
                    rel = ""
                if rel:
                    items.append(rel + "/")
                if len(items) >= max_count:
                    break
        except Exception:
            pass
        return sorted(set(items))

    def _complete_slash(self, frag):
        add = self._cmd_trie.shortest_completion(frag)
        if not add:
            return ""
        full = frag + add
        conf = len(frag) / max(1, len(full))
        return add if conf >= 0.7 else ""

    def _complete_at(self, frag):
        opts = self._list_agents()
        if not opts:
            return ""
        m = None
        low = frag.lower()
        for o in sorted(opts, key=len):
            if o.lower().startswith(low):
                m = o
                break
        if not m:
            return ""
        add = m[len(frag):]
        conf = len(frag) / max(1, len(m))
        return add if conf >= 0.7 else ""

    def _complete_hash(self, frag):
        low = frag.lower()
        reserved = ["open","selection","symbols","folder"]
        for r in reserved:
            if r.startswith(low) and low:
                add = r[len(frag):]
                conf = len(frag) / max(1, len(r))
                return add if conf >= 0.7 else ""
        if low.startswith("open/"):
            sub = frag[len("open/"):]
            paths = self._list_open_paths()
            if not paths:
                return ""
            cands = [p for p in paths if p.lower().startswith(sub.lower())]
            if not cands:
                return ""
            if len(cands) == 1:
                m = cands[0]
                add = m[len(sub):] + ":"
                conf = len(sub) / max(1, len(m))
                return add if conf >= 0.7 else ""
            cp = self._common_prefix(cands)
            if len(cp) > len(sub):
                add = cp[len(sub):]
                conf = len(sub) / max(1, len(cp))
                return add if conf >= 0.7 else ""
            return ""
        if low.startswith("folder/"):
            sub = frag[len("folder/"):]
            dirs = self._list_project_dirs()
            if not dirs:
                return ""
            cands = [d for d in dirs if d.lower().startswith(sub.lower())]
            if not cands:
                return ""
            if len(cands) == 1:
                m = cands[0]
                add = m[len(sub):]
                # ensure trailing slash remains for traversal
                if not add.endswith("/") and not m.endswith("/"):
                    add = add + "/"
                conf = len(sub) / max(1, len(m))
                return add if conf >= 0.7 else ""
            cp = self._common_prefix(cands)
            if len(cp) > len(sub):
                add = cp[len(sub):]
                if add and not add.endswith("/"):
                    add = add
                conf = len(sub) / max(1, len(cp))
                return add if conf >= 0.7 else ""
            return ""
        names = self._list_open_files()
        if not names:
            return ""
        cands = [n for n in names if n.lower().startswith(low)]
        if not cands:
            return ""
        if len(cands) == 1:
            m = cands[0]
            add = m[len(frag):]
            conf = len(frag) / max(1, len(m))
            return add if conf >= 0.7 else ""
        cp = self._common_prefix(cands)
        if len(cp) > len(frag):
            add = cp[len(frag):]
            conf = len(frag) / max(1, len(cp))
            return add if conf >= 0.7 else ""
        return ""

    def _get_current_selection(self):
        try:
            focused = self.app.root.focus_get()
            import tkinter as _tk
            if isinstance(focused, (_tk.Text,)):
                try:
                    return focused.get("sel.first", "sel.last")
                except Exception:
                    return ""
        except Exception:
            return ""
        return ""

    def _list_symbols(self):
        content = ""
        try:
            if hasattr(self.app, "editor_tabs") and self.app.editor_tabs and self.app.editor_tabs.current_file in self.app.editor_tabs.open_files:
                tw = self.app.editor_tabs.open_files[self.app.editor_tabs.current_file][0]
                content = tw.get("1.0", "end-1c")
        except Exception:
            content = ""
        import re
        defs = re.findall(r"^\s*def\s+(\w+)", content, flags=re.M)
        classes = re.findall(r"^\s*class\s+(\w+)", content, flags=re.M)
        return sorted(set(defs + classes))

    def _complete_grammar(self, frag):
        m = None
        low = frag.lower()
        for w in sorted(self._grammar_freq.keys(), key=lambda x: (-self._grammar_freq[x], len(x))):
            if w.startswith(low):
                m = w
                break
        if not m:
            return ""
        add = m[len(frag):]
        base = len(frag) / max(1, len(m))
        freq_boost = min(0.2, self._grammar_freq.get(m, 10) / 100.0)
        conf = min(1.0, base + freq_boost)
        return add if conf >= 0.7 else ""

    def _common_prefix(self, arr):
        if not arr:
            return ""
        s1 = min(arr)
        s2 = max(arr)
        i = 0
        while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
            i += 1
        return s1[:i]

    def _update_autocomplete_state(self):
        self.pending_completion = ""
        self.pending_trigger = None
        content = self.text_input.get("1.0", "end-1c")
        cursor_pos = self.text_input.index(tk.INSERT)
        line, col = map(int, cursor_pos.split("."))
        line_text = self.text_input.get(f"{line}.0", cursor_pos)
        if not line_text:
            return
        if self._inside_code_block(content, cursor_pos):
            token = line_text.split()[-1] if line_text.split() else ""
            if not token:
                return
            add = self._complete_grammar(token)
            if add:
                self.pending_completion = add
                self.pending_trigger = None
            return
        if "/" in line_text:
            s = line_text.rfind("/")
            frag = line_text[s+1:]
            if " " not in frag and frag:
                add = self._complete_slash(frag)
                if add:
                    self.pending_completion = add
                    self.pending_trigger = "/"
                    return
        if "@" in line_text:
            s = line_text.rfind("@")
            frag = line_text[s+1:]
            if " " not in frag and frag:
                add = self._complete_at(frag)
                if add:
                    self.pending_completion = add
                    self.pending_trigger = "@"
                    return
        if "#" in line_text:
            s = line_text.rfind("#")
            frag = line_text[s+1:]
            if " " not in frag and frag:
                add = self._complete_hash(frag)
                if add:
                    self.pending_completion = add
                    self.pending_trigger = "#"
                    return
                # Show dropdowns for #open: and #folder/ when appropriate
                low = frag.lower()
                if low == "open:" or low.startswith("open:"):
                    opts = self._list_open_paths()
                    if opts:
                        try:
                            self.show_suggestions(opts, frag, "#")
                        except Exception:
                            pass
                        return
                if low.startswith("folder/"):
                    dirs = self._list_project_dirs()
                    if dirs:
                        try:
                            # Only show next-level matches based on current subpath
                            sub = frag[len("folder/"):]
                            cands = [d for d in dirs if d.lower().startswith(sub.lower())]
                            self.show_suggestions(cands or dirs, frag, "#")
                        except Exception:
                            pass
                        return
                if frag == "symbols":
                    syms = self._list_symbols()
                    if syms:
                        cp = self._common_prefix(syms)
                        if len(cp) > 0:
                            self.pending_completion = cp
                            self.pending_trigger = None
                            return
        token = line_text.split()[-1] if line_text.split() else ""
        if token:
            add = self._complete_grammar(token)
            if add:
                self.pending_completion = add
                self.pending_trigger = None
                return
        if not self.pending_completion and self.autocomplete_enabled:
            try:
                if len(line_text) < 5:
                    return
                prompt = f"Fragment: {line_text}\nTrigger: {self.pending_trigger or ''}\nReturn only characters to append."
                resp = self.app.ai_manager.generate_response(
                    prompt,
                    system_prompt=self.autocomplete_system_prompt,
                    temperature=0.1,
                    max_tokens=8
                )
                if resp and "Error:" not in resp:
                    r = resp.strip()
                    if 0 < len(r) <= 10 and "\n" not in r:
                        self.pending_completion = r
                        self.pending_trigger = None
            except Exception:
                pass

    def _accept_autocomplete(self, event):
        if not self.pending_completion:
            return None
        self.text_input.insert(tk.INSERT, self.pending_completion)
        self.pending_completion = ""
        self.pending_trigger = None
        return "break"
