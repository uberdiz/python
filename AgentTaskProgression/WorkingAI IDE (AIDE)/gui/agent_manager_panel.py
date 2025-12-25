"""
Agent Manager Panel - UI for managing AI agents
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
from gui.agent_library_panel import AgentLibraryWindow

class AgentManagerPanel(ttk.Frame):
    """Sidebar panel for managing AI agents"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.orchestrator = None
        self.agent_groups = []
        
        self.setup_ui()
        self.init_orchestrator()
        
    def open_library(self):
        """Open the Agent Group Library"""
        AgentLibraryWindow(self, self.app, self.handle_library_import)

    def handle_library_import(self, selected_groups):
        """Import agents from selected groups"""
        if not self.orchestrator: return
        
        count = 0
        imported_agents = []
        
        for group in selected_groups:
            self.append_log(f"[System] Importing group: {group['name']}")
            for agent_data in group["agents"]:
                # Unique name generation
                base_name = agent_data['name']
                name = base_name
                if name in self.orchestrator.agents:
                    name = f"{base_name}_{group['id']}"
                
                role = agent_data["role"].lower()
                model = agent_data["model"]
                provider = self._infer_provider(model)
                
                # Validate model against whitelist
                if hasattr(self.app, 'ai_manager'):
                    if not self.app.ai_manager.validate_model(model, provider):
                        allowed = self.app.ai_manager.get_allowed_models(provider)
                        if allowed:
                            self.append_log(f"[Warning] Model '{model}' not allowed for provider '{provider}'. Using '{allowed[0]}'.")
                            model = allowed[0]
                        else:
                            self.append_log(f"[Warning] Model '{model}' not allowed, but no whitelist found.")

                # Create the agent
                self.create_agent(name, role, provider, model)
                imported_agents.append(name)
                count += 1
                
        if count > 0:
            messagebox.showinfo("Import Complete", f"Successfully imported {count} agents:\n" + "\n".join(imported_agents))
        
    def setup_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(toolbar, text="+ Create", command=self.create_agent_dialog, width=8).pack(side="left", padx=1)
        ttk.Button(toolbar, text="📚 Lib", command=self.open_library, width=6).pack(side="left", padx=1)
        ttk.Button(toolbar, text="💾 Save", command=self.save_group, width=6).pack(side="left", padx=1)
        ttk.Button(toolbar, text="📂 Load", command=self.load_group, width=6).pack(side="left", padx=1)
        ttk.Button(toolbar, text="📊 Mon", command=self.open_monitor, width=6).pack(side="left", padx=1)
        ttk.Button(toolbar, text="▶ Start", command=self.start_all_agents, width=6).pack(side="left", padx=1)
        ttk.Button(toolbar, text="⏹ Stop", command=self.stop_all_agents, width=6).pack(side="right", padx=1)
        
        # Agent Group Presets
        preset_frame = ttk.Frame(self)
        preset_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(preset_frame, text="Group Presets:").pack(side="left", padx=2)
        
        self.generate_presets_all()
        group_names = [group['name'] for group in self.agent_groups]
        self.group_selection_combo = ttk.Combobox(preset_frame, values=group_names, state="readonly", width=25)
        self.group_selection_combo.pack(side="left", padx=5)
        self.group_selection_combo.bind("<<ComboboxSelected>>", self.on_group_selected)
        
        # Agent List
        list_frame = ttk.LabelFrame(self, text="Active Agents")
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.agent_tree = ttk.Treeview(list_frame, columns=("Name", "Role", "Status", "Model"), show="headings", height=6)
        self.agent_tree.heading("Name", text="Name")
        self.agent_tree.heading("Role", text="Role")
        self.agent_tree.heading("Status", text="Status")
        self.agent_tree.heading("Model", text="Model")
        self.agent_tree.column("Name", width=80)
        self.agent_tree.column("Role", width=80)
        self.agent_tree.column("Status", width=60)
        self.agent_tree.column("Model", width=100)
        self.agent_tree.pack(fill="both", expand=True, padx=2, pady=2)
        self.agent_tree.bind("<<TreeviewSelect>>", self.on_selection_changed)
        
        ctrl_frame = ttk.Frame(list_frame)
        ctrl_frame.pack(fill="x", padx=2, pady=2)
        self.edit_btn = ttk.Button(ctrl_frame, text="✎ Edit", command=self.edit_selected)
        self.edit_btn.pack(side="left", padx=2)
        self.remove_btn = ttk.Button(ctrl_frame, text="Remove", command=self.remove_selected)
        self.remove_btn.pack(side="left", padx=2)
        ttk.Button(ctrl_frame, text="⭐ Recommend", command=self.recommend_agents_dialog).pack(side="right", padx=2)
        
        # Approval Gate Section
        approval_frame = ttk.LabelFrame(self, text="Approval Gate")
        approval_frame.pack(fill="x", padx=5, pady=5)
        
        self.approval_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(approval_frame, text="Require approval before execution", 
                        variable=self.approval_var, command=self.toggle_approval).pack(side="left", padx=5, pady=2)
        
        btn_frame = ttk.Frame(approval_frame)
        btn_frame.pack(side="right", padx=5)
        ttk.Button(btn_frame, text="✓ Approve", command=self.approve_pending).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="✗ Reject", command=self.reject_pending).pack(side="left", padx=2)
        
        # Agent Chat Log
        log_frame = ttk.LabelFrame(self, text="Agent Communication")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Apply theme
        if self.app.theme_engine:
            bg = self.app.theme_engine.color_map.get("editor_bg", "#1e1e1e")
            fg = self.app.theme_engine.color_map.get("editor_fg", "#d4d4d4")
            self.log_text.configure(bg=bg, fg=fg, insertbackground=fg)

    def init_orchestrator(self):
        """Initialize the agent orchestrator"""
        try:
            from core.agent_orchestrator import AgentOrchestrator
            self.orchestrator = AgentOrchestrator(self.app)
            self.orchestrator.on_log = self.append_log
            self.append_log("[System] Agent Orchestrator initialized")
            
            # Load Last Used Group
            last_group = self.app.settings.get("last_agent_group", None)
            loaded = False
            if last_group:
                self.append_log(f"[System] Loading last used group: {last_group}")
                if self.orchestrator.load_config(last_group):
                    loaded = True
            
            # If no group loaded, load or create default
            if not loaded:
                self.append_log("[System] Loading default configuration...")
                if not self.orchestrator.load_config("default"):
                    # Create default agents if 'default' config doesn't exist
                    self.create_agent("Planner", "planner", "openai", "gpt-4o-mini")
                    self.create_agent("Coder", "coder", "openai", "gpt-4o")
                    self.create_agent("Terminal", "tester", "openai", "gpt-4o-mini")
                    self.orchestrator.save_config("default")
            
            self.refresh_agent_list()
            # Auto-start agents on load
            self.start_all_agents()
            
        except Exception as e:
            self.append_log(f"[Error] Failed to init orchestrator: {e}")

    def on_group_selected(self, event):
        """Handle selection of an agent group preset"""
        selected_name = self.group_selection_combo.get()
        selected_group = next((g for g in self.agent_groups if g['name'] == selected_name), None)
        
        if not selected_group or not self.orchestrator:
            return
            
        self.append_log(f"[System] Loading preset group: {selected_name}")
        
        # Stop and clear existing agents
        self.orchestrator.stop_all()
        names = list(self.orchestrator.agents.keys())
        for name in names:
            self.orchestrator.unregister_agent(name)
            
        # Create agents from preset
        for agent_data in selected_group["agents"]:
            name = agent_data["name"]
            role = agent_data["role"].lower()
            model = agent_data["model"]
            provider = self._infer_provider(model)
            self.create_agent(name, role, provider, model)
            
        self.refresh_agent_list()
        self.start_all_agents()
        self.append_log(f"[System] Group '{selected_name}' loaded successfully.")

    def _infer_provider(self, model):
        """Infer provider from model name"""
        model = model.lower()
        if "gpt" in model: return "openai"
        if "claude" in model: return "anthropic"
        if "gemini" in model: return "google"
        if "llama" in model or "mistral" in model or "deepseek" in model: return "ollama"
        return "huggingface"

    def generate_presets_all(self):
        """Generate preset agent groups including user-saved ones"""
        # Default Hardcoded Presets
        self.agent_groups = [
            {
                "id": "openai_squad",
                "name": "OpenAI Power Squad",
                "description": "Standard high-performance group using GPT-4o.",
                "agents": [
                    {"name": "Planner", "role": "planner", "model": "gpt-4o-mini"},
                    {"name": "Architect", "role": "coder", "model": "gpt-4o"},
                    {"name": "Reviewer", "role": "tester", "model": "gpt-4o-mini"}
                ]
            },
            {
                "id": "anthropic_team",
                "name": "Claude Creative Team",
                "description": "Uses Anthropic's Claude 3.5 models.",
                "agents": [
                    {"name": "ClaudePlanner", "role": "planner", "model": "claude-3-5-haiku-latest"},
                    {"name": "ClaudeCoder", "role": "coder", "model": "claude-3-5-sonnet-latest"},
                    {"name": "ClaudeTester", "role": "tester", "model": "claude-3-5-haiku-latest"}
                ]
            },
            {
                "id": "local_dev",
                "name": "Local Dev (Ollama)",
                "description": "Privacy-focused local models via Ollama.",
                "agents": [
                    {"name": "LocalLead", "role": "planner", "model": "llama3"},
                    {"name": "LocalCoder", "role": "coder", "model": "deepseek-coder-v2"},
                    {"name": "LocalTester", "role": "tester", "model": "mistral"}
                ]
            },
            {
                "id": "mobile_app_crew",
                "name": "Mobile App Crew",
                "description": "Specialized in iOS and Android development using React Native.",
                "agents": [
                    {"name": "MobileLead", "role": "Architect", "model": "gpt-4o"},
                    {"name": "IOS_Dev", "role": "Coder", "model": "gpt-4o"},
                    {"name": "Android_Dev", "role": "Coder", "model": "gpt-4o"},
                    {"name": "MobileTester", "role": "Tester", "model": "gpt-3.5-turbo"}
                ]
            }
        ]
        
        # Add User-Saved Groups
        user_groups = self.app.settings.get("agent_groups", {})
        for name, agents in user_groups.items():
            # Avoid duplicating if name matches a preset (though unlikely with IDs)
            if not any(g['name'] == name for g in self.agent_groups):
                self.agent_groups.append({
                    "id": f"user_{name}",
                    "name": name,
                    "description": "User-saved agent group.",
                    "agents": agents
                })

    def refresh_presets(self):
        """Refresh the presets list and combo box"""
        self.generate_presets_all()
        group_names = [group['name'] for group in self.agent_groups]
        self.group_selection_combo['values'] = group_names

    def save_group(self):
        """Save the current agent group to app settings"""
        name = simpledialog.askstring("Save Group", "Enter group name:", initialvalue="default")
        if name and self.orchestrator:
            self.orchestrator.save_config(name)
            self.app.settings["last_agent_group"] = name
            if hasattr(self.app, 'save_settings'):
                self.app.save_settings(self.app.settings)
            
            self.refresh_presets()
            messagebox.showinfo("Saved", f"Agent group '{name}' saved.")

    def load_group(self):
        """Load an agent group from app settings"""
        if not self.orchestrator: return
        groups = self.app.settings.get("agent_groups", {})
        if not groups:
            messagebox.showinfo("No Groups", "No saved agent groups found.")
            return
            
        dialog = tk.Toplevel(self)
        dialog.title("Load Group")
        dialog.geometry("300x150")
        ttk.Label(dialog, text="Select Group:").pack(pady=10)
        
        group_list = list(groups.keys())
        var = tk.StringVar(value=group_list[0])
        ttk.Combobox(dialog, textvariable=var, values=group_list, state="readonly").pack(pady=5)
        
        def do_load():
            group_name = var.get()
            if self.orchestrator.load_config(group_name):
                self.refresh_agent_list()
                self.app.settings["last_agent_group"] = group_name
                if hasattr(self.app, 'save_settings'):
                    self.app.save_settings(self.app.settings)
                dialog.destroy()
                
        ttk.Button(dialog, text="Load", command=do_load).pack(pady=10)

    def create_agent_dialog(self, edit_name=None):
        """Dialog to create or edit an agent"""
        dialog = tk.Toplevel(self)
        dialog.title("Edit Agent" if edit_name else "Create Agent")
        dialog.geometry("350x380")
        dialog.transient(self)
        dialog.grab_set()
        
        # Initial values
        initial_data = {
            "name": "my_agent",
            "role": "planner",
            "provider": self.app.settings.get("api_provider", "openai"),
            "model": ""
        }
        
        if edit_name and self.orchestrator and edit_name in self.orchestrator.agents:
            agent = self.orchestrator.agents[edit_name]
            initial_data = {
                "name": agent.name,
                "role": agent.role,
                "provider": getattr(agent, "model_provider", self._infer_provider(agent.model_name)),
                "model": agent.model_name
            }

        # Name
        ttk.Label(dialog, text="Agent Name:").pack(padx=10, pady=(10,0), anchor="w")
        name_var = tk.StringVar(value=initial_data["name"])
        ttk.Entry(dialog, textvariable=name_var).pack(fill="x", padx=10, pady=2)
        
        # Role/Type
        ttk.Label(dialog, text="Role:").pack(padx=10, pady=(10,0), anchor="w")
        role_var = tk.StringVar(value=initial_data["role"])
        role_combo = ttk.Combobox(dialog, textvariable=role_var, values=["planner", "coder", "image_agent", "gui_coder", "tester"], state="readonly")
        role_combo.pack(fill="x", padx=10, pady=2)
        
        # Model Provider
        ttk.Label(dialog, text="AI Provider:").pack(padx=10, pady=(10,0), anchor="w")
        provider_var = tk.StringVar(value=initial_data["provider"])
        
        # Get all available providers from AI Manager
        available_providers = ["openai"]
        if hasattr(self.app, 'ai_manager'):
            available_providers = list(self.app.ai_manager.get_providers().keys())
        
        provider_combo = ttk.Combobox(dialog, textvariable=provider_var, values=available_providers, state="readonly")
        provider_combo.pack(fill="x", padx=10, pady=2)
        
        # Model Name
        ttk.Label(dialog, text="Model:").pack(padx=10, pady=(10,0), anchor="w")
        model_var = tk.StringVar(value=initial_data["model"])
        model_combo = ttk.Combobox(dialog, textvariable=model_var, state="readonly")
        model_combo.pack(fill="x", padx=10, pady=2)

        def update_models(*args):
            provider = provider_var.get()
            models = []
            if hasattr(self.app, 'ai_manager'):
                models = self.app.ai_manager.get_allowed_models(provider)
            
            if not models:
                model_combo['values'] = ["No models found"]
                model_var.set("No models found")
                return

            model_combo['values'] = models
            
            # If we are editing and the model is in the list, keep it
            current_model = model_var.get()
            if current_model in models:
                return

            if models:
                # Try to pick a suggested model based on role
                suggestions = {
                    "openai": {"planner": "gpt-4o-mini", "coder": "gpt-4o", "tester": "gpt-4o-mini"},
                    "anthropic": {"planner": "claude-3-5-sonnet-latest", "coder": "claude-3-5-sonnet-latest", "tester": "claude-3-5-haiku-latest"},
                    "google": {"planner": "gemini-1.5-pro", "coder": "gemini-1.5-pro", "tester": "gemini-1.5-flash"},
                    "ollama": {"planner": "nemotron-3-nano", "coder": "qwen2.5-coder", "tester": "phi3"},
                    "huggingface": {"planner": "Qwen/Qwen2.5-7B-Instruct", "coder": "Qwen/Qwen2.5-7B-Instruct", "tester": "Qwen/Qwen2.5-7B-Instruct"},
                    "deepseek": {"planner": "deepseek-chat", "coder": "deepseek-coder", "tester": "deepseek-chat"},
                    "mistral": {"planner": "mistral-large-latest", "coder": "mistral-large-latest", "tester": "mistral-small-latest"},
                    "groq": {"planner": "llama-3.3-70b-versatile", "coder": "llama-3.3-70b-versatile", "tester": "llama-3.1-8b-instant"},
                    "together": {"planner": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "coder": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "tester": "meta-llama/Llama-3.1-8B-Instruct-Turbo"}
                }
                role = role_var.get()
                suggested = suggestions.get(provider, {}).get(role, models[0])
                if suggested in models:
                    model_var.set(suggested)
                else:
                    model_var.set(models[0])
            else:
                model_var.set("")

        provider_combo.bind("<<ComboboxSelected>>", update_models)
        role_combo.bind("<<ComboboxSelected>>", update_models)
        
        # Initial model population (only if not already set or not in allowed list)
        update_models()
        
        def save():
            name = name_var.get().strip()
            role = role_var.get()
            provider = provider_var.get()
            model = model_var.get().strip()
            if not name or not model:
                messagebox.showwarning("Missing Info", "Name and Model are required.")
                return
            
            if edit_name and self.orchestrator:
                # If name changed, unregister old one
                self.orchestrator.unregister_agent(edit_name)
            
            self.create_agent(name, role, provider, model)
            dialog.destroy()
            
        ttk.Button(dialog, text="Save" if edit_name else "Create", command=save).pack(pady=20)

    def create_agent(self, name, role, provider, model):
        """Create and register an agent using orchestrator"""
        if not self.orchestrator: return
        agent = self.orchestrator.create_agent_by_role(name, role, provider, model)
        if agent:
            self.refresh_agent_list()
            self.append_log(f"[System] Created agent: {name}")
        else:
            self.append_log(f"[Error] Failed to create agent: {name}")

    def on_selection_changed(self, event=None):
        """Update button states based on treeview selection"""
        selections = self.agent_tree.selection()
        count = len(selections)
        
        if count == 0:
            self.edit_btn.config(state="disabled")
            self.remove_btn.config(state="disabled")
        elif count == 1:
            self.edit_btn.config(state="normal")
            self.remove_btn.config(state="normal", text="Remove")
        else:
            self.edit_btn.config(state="disabled")
            self.remove_btn.config(state="normal", text=f"Remove ({count})")

    def refresh_agent_list(self):
        """Refresh the agent list display"""
        for item in self.agent_tree.get_children():
            self.agent_tree.delete(item)
        if self.orchestrator:
            for name, agent in self.orchestrator.agents.items():
                self.agent_tree.insert("", "end", values=(
                    agent.name,
                    agent.role,
                    agent.status,
                    agent.model_name[:20] + "..." if len(agent.model_name) > 20 else agent.model_name
                ))
        self.on_selection_changed()

    def remove_selected(self):
        """Remove selected agents"""
        selections = self.agent_tree.selection()
        if not selections: return
        
        if not messagebox.askyesno("Delete Agents", f"Are you sure you want to delete {len(selections)} agent(s)?"):
            return
            
        for sel in selections:
            item = self.agent_tree.item(sel)
            name = item['values'][0]
            if self.orchestrator:
                self.orchestrator.unregister_agent(name)
        
        self.refresh_agent_list()

    def edit_selected(self):
        """Edit the selected agent's configuration"""
        sel = self.agent_tree.selection()
        if not sel:
            messagebox.showinfo("Select Agent", "Select an agent first.")
            return
        
        if len(sel) > 1:
            messagebox.showwarning("Edit Agent", "Multiple agents selected. Please select only one to edit.")
            return
            
        item = self.agent_tree.item(sel[0])
        old_name = item['values'][0]
        self.create_agent_dialog(edit_name=old_name)

    def recommend_agents_dialog(self):
        """Dialog to recommend agents based on project and provider"""
        if not self.orchestrator: return
        self.append_log("[System] Analyzing project for agent recommendations...")
        
        project_path = getattr(self.app, 'project_path', None)
        active_providers = self.app.ai_manager.get_active_providers()
        if not active_providers:
            active_providers = ["openai"]
        
        # Determine recommendations based on project
        recommended_roles = []
        project_context = ""
        if project_path:
            import os
            files = []
            try:
                for root, _, filenames in os.walk(project_path):
                    for f in filenames:
                        files.append(f)
                    if len(files) > 100: break
            except: pass
            
            project_context = f"Project at {project_path} contains: {', '.join(files[:20])}"
            
            if any(f.endswith(('.py', '.ipynb')) for f in files):
                recommended_roles.append(("Python Specialist", "coder", "Expert in Python logic, data science, and backend APIs"))
            if any(f.endswith(('.js', '.ts', '.tsx', '.jsx', '.html', '.css')) for f in files):
                recommended_roles.append(("Full-stack Web Dev", "coder", "React/Vue/Node.js and modern web UI specialist"))
            if any(f.endswith(('.go', '.rs', '.cpp', '.c')) for f in files):
                recommended_roles.append(("Systems Engineer", "coder", "Expert in low-level programming and performance optimization"))
            if not any(f.lower() == 'readme.md' for f in files):
                recommended_roles.append(("Documentation Lead", "planner", "Creates comprehensive project overviews and API docs"))
            if not any('test' in f.lower() for f in files):
                recommended_roles.append(("QA Automation Engineer", "tester", "Builds robust unit, integration, and E2E testing suites"))
            if any('docker' in f.lower() or 'yml' in f.lower() for f in files):
                recommended_roles.append(("DevOps Specialist", "coder", "Docker, Kubernetes, and CI/CD pipeline expert"))
        
        if not recommended_roles:
            recommended_roles.append(("Strategic Planner", "planner", "Outlines project structure, roadmap, and task breakdown"))
            recommended_roles.append(("Core Developer", "coder", "Implements core business logic and features"))

        # Create Dialog
        dialog = tk.Toplevel(self)
        dialog.title("Intelligent Agent Recommendations")
        dialog.geometry("600x650")
        dialog.transient(self)
        dialog.grab_set()

        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Label(header_frame, text="Recommended Agents for Your Project", 
                  font=("Segoe UI", 12, "bold")).pack(anchor="w")
        
        provider_str = ", ".join([p.upper() for p in active_providers])
        ttk.Label(header_frame, text=f"Active Providers: {provider_str}", 
                  foreground="grey").pack(anchor="w")

        # Scrollable area for recommendations
        canvas = tk.Canvas(dialog, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")

        selected_agents = []
        
        # Smart assignment of providers to roles if multiple are active
        def get_best_provider_for_role(role, active_providers):
            if not active_providers: return "openai"
            if len(active_providers) == 1: return active_providers[0]
            
            # Preferences
            if role == "coder":
                for p in ["anthropic", "openai", "google"]:
                    if p in active_providers: return p
            elif role == "planner":
                for p in ["anthropic", "openai"]:
                    if p in active_providers: return p
            elif role == "tester":
                for p in ["openai", "google", "ollama"]:
                    if p in active_providers: return p
            
            return active_providers[0]

        for title, role, desc in recommended_roles:
            f = ttk.LabelFrame(scrollable_frame, text=title)
            f.pack(fill="x", pady=10, padx=5)
            
            ttk.Label(f, text=desc, wraplength=500, font=("Segoe UI", 9, "italic")).pack(padx=10, pady=5, anchor="w")
            
            config_row = ttk.Frame(f)
            config_row.pack(fill="x", padx=10, pady=10)
            
            # Provider selection for this specific agent
            ttk.Label(config_row, text="Provider:").pack(side="left")
            best_p = get_best_provider_for_role(role, active_providers)
            provider_var = tk.StringVar(value=best_p)
            provider_combo = ttk.Combobox(config_row, textvariable=provider_var, values=active_providers, state="readonly", width=15)
            provider_combo.pack(side="left", padx=5)
            
            # Model selection for this agent
            ttk.Label(config_row, text="Model:").pack(side="left", padx=(10, 0))
            model_var = tk.StringVar()
            model_combo = ttk.Combobox(config_row, textvariable=model_var, state="readonly", width=25)
            model_combo.pack(side="left", padx=5)
            
            def update_models_for_agent(p_var=provider_var, m_combo=model_combo, r=role):
                p_id = p_var.get()
                if hasattr(self.app, 'ai_manager'):
                    models = self.app.ai_manager.get_allowed_models(p_id)
                    
                    if not models:
                        # If no models found in cache or defaults, try to fetch them once
                        # We don't want to block the UI too long, so maybe just a warning
                        m_combo['values'] = ["No models found - check Provider settings"]
                        m_combo.set("No models found")
                        return
                        
                    m_combo['values'] = models
                    
                    # Smart default model selection
                    suggestions = {
                        "openai": {"planner": "gpt-4o", "coder": "gpt-4o", "tester": "gpt-4o-mini"},
                        "anthropic": {"planner": "claude-3-5-sonnet-latest", "coder": "claude-3-5-sonnet-latest", "tester": "claude-3-5-haiku-latest"},
                        "google": {"planner": "gemini-1.5-pro", "coder": "gemini-1.5-pro", "tester": "gemini-1.5-flash"},
                        "ollama": {"planner": "llama3", "coder": "deepseek-coder-v2", "tester": "mistral"},
                        "huggingface": {"planner": "Qwen/Qwen2.5-7B-Instruct", "coder": "Qwen/Qwen2.5-7B-Instruct", "tester": "Qwen/Qwen2.5-7B-Instruct"},
                        "deepseek": {"planner": "deepseek-chat", "coder": "deepseek-coder", "tester": "deepseek-chat"},
                        "mistral": {"planner": "mistral-large-latest", "coder": "mistral-large-latest", "tester": "mistral-small-latest"},
                        "groq": {"planner": "llama-3.3-70b-versatile", "coder": "llama-3.3-70b-versatile", "tester": "llama-3.1-8b-instant"}
                    }
                    suggested = suggestions.get(p_id, {}).get(r, models[0] if models else "")
                    if suggested in models:
                        m_combo.set(suggested)
                    elif models:
                        m_combo.set(models[0])

            provider_combo.bind("<<ComboboxSelected>>", lambda e, pv=provider_var, mc=model_combo, rl=role: update_models_for_agent(pv, mc, rl))
            update_models_for_agent()
            
            check_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(config_row, text="Include", variable=check_var).pack(side="right", padx=10)
            
            selected_agents.append({
                "name": title.replace(" ", ""),
                "role": role,
                "provider_var": provider_var,
                "model_var": model_var,
                "check_var": check_var
            })

        def add_selected():
            added_count = 0
            for agent in selected_agents:
                if agent["check_var"].get():
                    name = agent["name"]
                    # Ensure unique name
                    idx = 1
                    original_name = name
                    while name in self.orchestrator.agents:
                        name = f"{original_name}_{idx}"
                        idx += 1
                        
                    self.create_agent(name, agent["role"], agent["provider_var"].get(), agent["model_var"].get())
                    added_count += 1
            
            if added_count > 0:
                self.append_log(f"[System] Added {added_count} specialized agents for this project.")
                self.refresh_agent_list()
                dialog.destroy()
            else:
                messagebox.showwarning("Selection", "Please select at least one agent to add.")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill="x", padx=20, pady=20)
        ttk.Button(btn_frame, text="Add Selected Agents to Group", command=add_selected, style="Accent.TButton").pack(side="right")
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=10)

    def toggle_approval(self):
        """Toggle the approval gate"""
        if self.orchestrator:
            self.orchestrator.approval_required = self.approval_var.get()
            self.append_log(f"[System] Approval gate {'enabled' if self.orchestrator.approval_required else 'disabled'}")

    def approve_pending(self):
        """Approve pending agent tasks"""
        if self.orchestrator:
            self.orchestrator.approve_all_pending()
            self.append_log("[System] All pending tasks approved")

    def reject_pending(self):
        """Reject pending agent tasks"""
        if self.orchestrator:
            self.orchestrator.reject_all_pending()
            self.append_log("[System] All pending tasks rejected")

    def open_monitor(self):
        """Open the Agent Monitor window"""
        if self.orchestrator:
            from gui.agent_monitor import AgentMonitor
            AgentMonitor(self, self.orchestrator)

    def start_all_agents(self):
        """Start all agents"""
        if self.orchestrator:
            self.orchestrator.start_all()
            self.refresh_agent_list()

    def stop_all_agents(self):
        """Stop all agents"""
        if self.orchestrator:
            self.orchestrator.stop_all()
            self.refresh_agent_list()

    def append_log(self, message):
        """Append message to the communication log"""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
