import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import json
import threading

class ProvidersWindow:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("AI Dev IDE - Providers & Models")
        self.window.geometry("900x700")
        self.window.configure(bg="#1e1e1e")
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Initialize variables
        self.allow_multiple_providers_var = tk.BooleanVar(value=self.app.settings.get("allow_multiple_providers", False))
        self.active_provider_id = None
        self.provider_ids = []
        
        self.setup_ui()

    def setup_ui(self):
        """Setup the Providers UI with Tabs"""
        # Main notebook
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- Tab 1: AI Providers ---
        self.providers_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.providers_tab, text="AI Providers")
        self.setup_providers_tab()
        
        # --- Tab 2: Model Manager ---
        self.models_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.models_tab, text="Model Manager")
        self.setup_models_tab()
        
        # --- Bottom Buttons ---
        bottom_buttons = ttk.Frame(self.window)
        bottom_buttons.pack(side="bottom", fill="x", padx=10, pady=10)
        
        ttk.Button(bottom_buttons, text="Reset to Defaults", command=self.reset_to_defaults).pack(side="left")
        ttk.Button(bottom_buttons, text="Save & Close", command=self.save_and_close).pack(side="right", padx=5)
        ttk.Button(bottom_buttons, text="Cancel", command=self.window.destroy).pack(side="right", padx=5)

    def setup_providers_tab(self):
        """Setup the Providers management tab"""
        # Main container
        main_frame = ttk.Frame(self.providers_tab)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Paned Window for split view
        paned = ttk.PanedWindow(main_frame, orient="horizontal")
        paned.pack(fill="both", expand=True)
        
        # --- Left Side: Provider List ---
        left_frame = ttk.Frame(paned, width=250)
        paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="AI Providers", font=("Segoe UI", 10, "bold")).pack(pady=(0, 5))
        
        # Multi-provider toggle
        ttk.Checkbutton(left_frame, text="Allow Multiple Active", 
                       variable=self.allow_multiple_providers_var, 
                       command=self.on_multi_provider_toggle).pack(pady=5)
        
        self.provider_listbox = tk.Listbox(left_frame, bg="#2d2d2d", fg="white", 
                                          selectbackground="#0e639c", font=("Segoe UI", 10))
        self.provider_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.provider_listbox.bind("<<ListboxSelect>>", self.on_provider_select)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(btn_frame, text="+ Add", width=8, command=self.add_new_provider).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="- Remove", width=8, command=self.remove_provider).pack(side="left", padx=2)
        
        # --- Right Side: Configuration ---
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)
        
        self.config_container = ttk.Frame(right_frame)
        self.config_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.refresh_provider_list()
        
        # Select first provider by default if available
        if self.provider_ids:
            self.provider_listbox.selection_set(0)
            self.on_provider_select(None)

    def setup_models_tab(self):
        """Setup the Model management tab"""
        main_frame = ttk.Frame(self.models_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- Top Section: Provider Selection ---
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(top_frame, text="Select Provider:").pack(side="left", padx=5)
        self.model_mgr_provider_var = tk.StringVar()
        self.model_mgr_provider_combo = ttk.Combobox(top_frame, textvariable=self.model_mgr_provider_var, state="readonly")
        self.model_mgr_provider_combo.pack(side="left", padx=5)
        self.model_mgr_provider_combo.bind("<<ComboboxSelected>>", self.refresh_models_manager_list)
        
        ttk.Button(top_frame, text="Fetch Available", command=self.fetch_provider_models).pack(side="left", padx=5)
        
        # --- Middle Section: Model List ---
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True)
        
        self.model_tree = ttk.Treeview(list_frame, columns=("Model ID", "Status"), show="headings")
        self.model_tree.heading("Model ID", text="Model ID")
        self.model_tree.heading("Status", text="Status")
        self.model_tree.column("Model ID", width=400)
        self.model_tree.column("Status", width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.model_tree.yview)
        self.model_tree.configure(yscrollcommand=scrollbar.set)
        
        self.model_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- Bottom Section: Actions ---
        actions = ttk.Frame(main_frame)
        actions.pack(fill="x", pady=10)
        
        ttk.Button(actions, text="Pull (Ollama)", command=self.pull_selected_ollama_model).pack(side="left", padx=5)
        ttk.Button(actions, text="Add Manually", command=self.add_model_manually).pack(side="left", padx=5)
        ttk.Button(actions, text="Delete Selected", command=self.delete_selected_model).pack(side="left", padx=5)
        ttk.Button(actions, text="Clear All Cache", command=self.clear_model_cache).pack(side="left", padx=5)
        
        # Progress for pulls
        self.pull_progress_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.pull_progress_var, foreground="#007acc").pack(side="bottom", fill="x")

        self.update_model_mgr_providers()

    def update_model_mgr_providers(self):
        """Update provider list in Model Manager tab"""
        providers = self.app.ai_manager.get_providers()
        ids = list(providers.keys())
        self.model_mgr_provider_combo['values'] = ids
        if ids and not self.model_mgr_provider_var.get():
            self.model_mgr_provider_var.set(ids[0])
            self.refresh_models_manager_list()

    def refresh_models_manager_list(self, event=None):
        """Refresh the model list for the selected provider"""
        pid = self.model_mgr_provider_var.get()
        if not pid: return
        
        for i in self.model_tree.get_children(): self.model_tree.delete(i)
        
        # 1. Get cached models
        cached = self.app.settings.get(f"cached_models_{pid}", [])
        
        # 2. If Ollama, also show popular library models
        if pid == "ollama":
            downloaded = self.app.ai_manager.fetch_available_models("ollama")
            library = self.app.ai_manager.get_ollama_library()
            
            # Show downloaded first
            for m in downloaded:
                self.model_tree.insert("", tk.END, values=(m, "Downloaded"))
            
            # Show library models that aren't downloaded
            for m in library:
                if not any(d.startswith(m) for d in downloaded):
                    self.model_tree.insert("", tk.END, values=(m, "Available in Library"))
        else:
            # For other providers, just show cached
            for m in cached:
                self.model_tree.insert("", tk.END, values=(m, "Cached"))
            
            if not cached:
                # Show defaults as "Default Suggestion"
                defaults = self.app.ai_manager.get_allowed_models(pid)
                for m in defaults:
                    self.model_tree.insert("", tk.END, values=(m, "Default"))

    def fetch_provider_models(self):
        """Fetch models for the selected provider in Model Manager"""
        pid = self.model_mgr_provider_var.get()
        if not pid: return
        
        self.pull_progress_var.set(f"Fetching models for {pid}...")
        
        def do_fetch():
            models = self.app.ai_manager.fetch_available_models(pid)
            if models:
                self.app.settings[f"cached_models_{pid}"] = models
                self.app.save_settings(self.app.settings)
                self.window.after(0, lambda: self.pull_progress_var.set(f"Successfully fetched {len(models)} models."))
                self.window.after(0, self.refresh_models_manager_list)
            else:
                self.window.after(0, lambda: self.pull_progress_var.set(f"Failed to fetch models for {pid}."))
                
        threading.Thread(target=do_fetch, daemon=True).start()

    def pull_selected_ollama_model(self):
        """Pull the selected model via Ollama"""
        pid = self.model_mgr_provider_var.get()
        if pid != "ollama":
            messagebox.showwarning("Not Supported", "Pull is only supported for Ollama.")
            return
            
        selection = self.model_tree.selection()
        if not selection:
            messagebox.showwarning("Selection", "Please select a model to pull.")
            return
            
        model_name = self.model_tree.item(selection[0])['values'][0]
        status = self.model_tree.item(selection[0])['values'][1]
        
        if status == "Downloaded":
            if not messagebox.askyesno("Confirm", f"Model {model_name} is already downloaded. Pull again to update?"):
                return

        def run_pull():
            self.window.after(0, lambda: self.pull_progress_var.set(f"Pulling {model_name}..."))
            
            def progress(s):
                p = s.get("status", "Processing")
                if "completed" in s and "total" in s:
                    perc = (s["completed"] / s["total"]) * 100
                    p = f"{perc:.1f}% - {s.get('status', '')}"
                self.window.after(0, lambda: self.pull_progress_var.set(f"Pulling {model_name}: {p}"))

            success = self.app.ai_manager.pull_ollama_model(model_name, progress)
            if success:
                self.window.after(0, lambda: self.pull_progress_var.set(f"Successfully pulled {model_name}!"))
                self.window.after(0, self.refresh_models_manager_list)
            else:
                self.window.after(0, lambda: self.pull_progress_var.set(f"Failed to pull {model_name}."))

        threading.Thread(target=run_pull, daemon=True).start()

    def add_model_manually(self):
        """Manually add a model ID to the cache"""
        pid = self.model_mgr_provider_var.get()
        if not pid: return
        
        model_id = simpledialog.askstring("Add Model", f"Enter model ID for {pid}:")
        if model_id:
            cached = self.app.settings.get(f"cached_models_{pid}", [])
            if model_id not in cached:
                cached.append(model_id)
                self.app.settings[f"cached_models_{pid}"] = cached
                self.app.save_settings(self.app.settings)
                self.refresh_models_manager_list()

    def delete_selected_model(self):
        """Delete a model from the cache and physically remove if local"""
        pid = self.model_mgr_provider_var.get()
        selection = self.model_tree.selection()
        if not pid or not selection: return
        
        model_id = self.model_tree.item(selection[0])['values'][0]
        status = self.model_tree.item(selection[0])['values'][1]
        
        confirm_msg = f"Are you sure you want to remove model '{model_id}'?"
        if status == "Downloaded" and pid == "ollama":
            confirm_msg = f"Are you sure you want to PHYSICALLY DELETE '{model_id}' from your PC storage?"
            
        if not messagebox.askyesno("Confirm Deletion", confirm_msg):
            return

        # Physical deletion for local models
        if status == "Downloaded" and pid == "ollama":
            self.pull_progress_var.set(f"Deleting {model_id} from storage...")
            success = self.app.ai_manager.delete_ollama_model(model_id)
            if success:
                self.pull_progress_var.set(f"Successfully deleted {model_id} from storage.")
            else:
                self.pull_progress_var.set(f"Failed to delete {model_id} from storage.")
                messagebox.showerror("Error", f"Failed to physically delete {model_id}. Check if Ollama is running.")
                return

        # Always remove from IDE cache
        cached = self.app.settings.get(f"cached_models_{pid}", [])
        if model_id in cached:
            cached.remove(model_id)
            self.app.settings[f"cached_models_{pid}"] = cached
            self.app.save_settings(self.app.settings)
        
        self.refresh_models_manager_list()

    def clear_model_cache(self):
        """Clear all cached models for the provider"""
        pid = self.model_mgr_provider_var.get()
        if not pid: return
        
        if messagebox.askyesno("Confirm", f"Clear all cached models for {pid}?"):
            if f"cached_models_{pid}" in self.app.settings:
                del self.app.settings[f"cached_models_{pid}"]
                self.app.save_settings(self.app.settings)
                self.refresh_models_manager_list()

    def on_multi_provider_toggle(self):
        """Handle multi-provider toggle change"""
        self.app.settings["allow_multiple_providers"] = self.allow_multiple_providers_var.get()
        if not self.allow_multiple_providers_var.get():
            active = self.app.ai_manager.get_active_providers()
            if len(active) > 1:
                self.app.ai_manager.set_provider(active[0], active=True, allow_multiple=False)
        self.app.save_settings(self.app.settings)
        self.refresh_provider_list()
        if self.active_provider_id:
            self.show_provider_config(self.active_provider_id)

    def refresh_provider_list(self):
        """Refresh the listbox with all providers"""
        self.provider_listbox.delete(0, tk.END)
        providers = self.app.ai_manager.get_providers()
        active_ids = self.app.ai_manager.get_active_providers()
        
        self.provider_ids = list(providers.keys())
        for pid in self.provider_ids:
            name = providers[pid].get("name", pid)
            if pid in active_ids:
                name += " (Active)"
            self.provider_listbox.insert(tk.END, name)

    def on_provider_select(self, event):
        """Handle provider selection in listbox"""
        selection = self.provider_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        pid = self.provider_ids[idx]
        self.active_provider_id = pid
        self.show_provider_config(pid)

    def show_provider_config(self, pid):
        """Show configuration UI for a specific provider"""
        for child in self.config_container.winfo_children():
            child.destroy()
            
        providers = self.app.ai_manager.get_providers()
        config = providers.get(pid, {})
        
        ttk.Label(self.config_container, text=f"Configuring: {config.get('name', pid)}", 
                  font=("Segoe UI", 11, "bold")).pack(pady=(0, 5), anchor="w")
        
        # Active status toggle
        is_active = pid in self.app.ai_manager.get_active_providers()
        active_var = tk.BooleanVar(value=is_active)
        ttk.Checkbutton(self.config_container, text="Active (Enabled)", variable=active_var).pack(pady=(0, 10), anchor="w")
        
        # Form fields
        form = ttk.Frame(self.config_container)
        form.pack(fill="x")
        
        row = 0
        ttk.Label(form, text="Provider Name:").grid(row=row, column=0, sticky="w", pady=5)
        name_var = tk.StringVar(value=config.get("name", ""))
        ttk.Entry(form, textvariable=name_var, width=40).grid(row=row, column=1, sticky="w", padx=10)
        row += 1
        
        ttk.Label(form, text="Type:").grid(row=row, column=0, sticky="w", pady=5)
        type_var = tk.StringVar(value=config.get("type", "openai"))
        types = ["openai", "ollama", "huggingface", "anthropic", "google"]
        ttk.Combobox(form, textvariable=type_var, values=types, state="readonly").grid(row=row, column=1, sticky="w", padx=10)
        row += 1
        
        ttk.Label(form, text="API URL:").grid(row=row, column=0, sticky="w", pady=5)
        url_var = tk.StringVar(value=config.get("url", ""))
        ttk.Entry(form, textvariable=url_var, width=50).grid(row=row, column=1, sticky="w", padx=10)
        row += 1
        
        ttk.Label(form, text="Default Model:").grid(row=row, column=0, sticky="w", pady=5)
        model_var = tk.StringVar(value=config.get("model", ""))
        ttk.Entry(form, textvariable=model_var, width=30).grid(row=row, column=1, sticky="w", padx=10)
        row += 1
        
        ttk.Label(form, text="API Key:").grid(row=row, column=0, sticky="w", pady=5)
        key_val = self._decrypt_secret(self.app.settings.get(f"{pid}_key", ""))
        if not key_val and pid in self.app.ai_manager.default_providers:
             key_val = self._decrypt_secret(self.app.settings.get(f"{config.get('type')}_key", ""))
        
        key_var = tk.StringVar(value=key_val)
        ttk.Entry(form, textvariable=key_var, width=50, show="*").grid(row=row, column=1, sticky="w", padx=10)
        row += 1
        
        # Action Buttons
        actions = ttk.Frame(self.config_container)
        actions.pack(fill="x", pady=20)
        
        def save_this_config():
            if not self.active_provider_id: return
            new_config = {
                "name": name_var.get(),
                "type": type_var.get(),
                "url": url_var.get(),
                "model": model_var.get()
            }
            self.app.settings[f"{self.active_provider_id}_key"] = self._encrypt_secret(key_var.get().strip())
            custom_providers = self.app.settings.get("custom_providers", {})
            custom_providers[self.active_provider_id] = new_config
            self.app.settings["custom_providers"] = custom_providers
            
            try:
                allow_multiple = self.allow_multiple_providers_var.get()
                self.app.ai_manager.set_provider(self.active_provider_id, active=active_var.get(), allow_multiple=allow_multiple)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update active state: {e}")

            self.app.save_settings(self.app.settings)
            messagebox.showinfo("Success", "Configuration saved.")
            self.refresh_provider_list()
            self.show_provider_config(self.active_provider_id)

        def set_active():
            try:
                allow_multiple = self.allow_multiple_providers_var.get()
                self.app.ai_manager.set_provider(pid, active=True, allow_multiple=allow_multiple)
                self.app.save_settings(self.app.settings)
                self.refresh_provider_list()
                self.show_provider_config(pid)
                messagebox.showinfo("Success", f"'{pid}' is now active.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to set active provider: {e}")

        def test_this_connection():
            orig_key = self.app.settings.get(f"{pid}_key", "")
            self.app.settings[f"{pid}_key"] = self._encrypt_secret(key_var.get())
            success, msg = self.app.ai_manager.test_connection(pid)
            if success:
                messagebox.showinfo("Connection Test", f"Successfully connected to {pid}!\n\n{msg}")
            else:
                messagebox.showerror("Connection Test", f"Failed to connect to {pid}:\n\n{msg}")

        def refresh_models():
            if not self.active_provider_id: return
            # Temporarily save key for fetch
            old_key = self.app.settings.get(f"{self.active_provider_id}_key", "")
            self.app.settings[f"{self.active_provider_id}_key"] = self._encrypt_secret(key_var.get())
            
            models = self.app.ai_manager.fetch_available_models(self.active_provider_id)
            if models:
                self.app.settings[f"cached_models_{self.active_provider_id}"] = models
                self.app.save_settings(self.app.settings)
                messagebox.showinfo("Success", f"Fetched {len(models)} models for {self.active_provider_id}")
                # Update model entry if it was empty
                if not model_var.get() and models:
                    model_var.set(models[0])
            else:
                # Restore old key if fetch failed and it was a temporary change
                self.app.settings[f"{self.active_provider_id}_key"] = old_key
                messagebox.showwarning("Warning", f"Could not fetch models for {self.active_provider_id}. Check your API key and URL.")

        ttk.Button(actions, text="Save Changes", command=save_this_config).pack(side="left", padx=5)
        ttk.Button(actions, text="Set as Active", command=set_active).pack(side="left", padx=5)
        ttk.Button(actions, text="Test Connection", command=test_this_connection).pack(side="left", padx=5)
        ttk.Button(actions, text="Refresh Models", command=refresh_models).pack(side="left", padx=5)
        
        # Usage Logs
        logs_frame = ttk.LabelFrame(self.config_container, text="Recent Usage Logs")
        logs_frame.pack(fill="both", expand=True, pady=10)
        
        log_tree = ttk.Treeview(logs_frame, columns=("Time", "Model", "Tokens"), show="headings", height=5)
        log_tree.heading("Time", text="Time")
        log_tree.heading("Model", text="Model")
        log_tree.heading("Tokens", text="Tokens")
        log_tree.column("Time", width=150)
        log_tree.column("Model", width=150)
        log_tree.column("Tokens", width=80)
        log_tree.pack(fill="both", expand=True)
        
        provider_logs = [l for l in getattr(self.app.ai_manager, 'usage_logs', []) if l.get('provider') == pid]
        for log in reversed(provider_logs[-20:]):
            log_tree.insert("", tk.END, values=(log['timestamp'][:19].replace('T', ' '), log['model'], log['tokens']))

    def add_new_provider(self):
        new_id = simpledialog.askstring("New Provider", "Enter unique ID for the provider:")
        if new_id:
            if new_id in self.app.ai_manager.get_providers():
                messagebox.showerror("Error", "Provider ID already exists.")
                return
            self.app.ai_manager.add_custom_provider(new_id, {
                "name": new_id.capitalize(), "type": "openai", "url": "http://localhost:8080/v1", "model": "gpt-3.5-turbo"
            })
            self.refresh_provider_list()

    def remove_provider(self):
        if not self.active_provider_id or self.active_provider_id in self.app.ai_manager.default_providers:
            return
        if messagebox.askyesno("Confirm", f"Remove provider '{self.active_provider_id}'?"):
            self.app.ai_manager.delete_custom_provider(self.active_provider_id)
            self.active_provider_id = None
            self.refresh_provider_list()
            for child in self.config_container.winfo_children(): child.destroy()

    def reset_to_defaults(self):
        if messagebox.askyesno("Reset", "Reset all provider settings to defaults?"):
            self.app.ai_manager.reset_to_defaults()
            self.refresh_provider_list()
            if self.active_provider_id: self.show_provider_config(self.active_provider_id)

    def save_and_close(self):
        self.app.save_settings(self.app.settings)
        self.window.destroy()

    def _encrypt_secret(self, plain_text):
        try:
            import ctypes, base64
            if not plain_text: return ""
            CRYPTPROTECT_LOCAL_MACHINE = 0x00000004
            data_in = ctypes.create_string_buffer(plain_text.encode('utf-8'))
            class DATA_BLOB(ctypes.Structure):
                _fields_ = [("cbData", ctypes.c_uint), ("pbData", ctypes.c_void_p)]
            in_blob = DATA_BLOB(len(data_in.raw), ctypes.cast(ctypes.byref(data_in), ctypes.c_void_p))
            out_blob = DATA_BLOB()
            if ctypes.windll.crypt32.CryptProtectData(ctypes.byref(in_blob), None, None, None, None, CRYPTPROTECT_LOCAL_MACHINE, ctypes.byref(out_blob)):
                try:
                    buf = ctypes.string_at(out_blob.pbData, out_blob.cbData)
                    return "enc:" + base64.b64encode(buf).decode('ascii')
                finally: ctypes.windll.kernel32.LocalFree(out_blob.pbData)
        except: pass
        return plain_text

    def _decrypt_secret(self, cipher_text):
        try:
            import ctypes, base64
            if not cipher_text or not cipher_text.startswith("enc:"): return cipher_text or ""
            raw = base64.b64decode(cipher_text[4:])
            class DATA_BLOB(ctypes.Structure):
                _fields_ = [("cbData", ctypes.c_uint), ("pbData", ctypes.c_void_p)]
            in_blob = DATA_BLOB(len(raw), ctypes.cast(ctypes.create_string_buffer(raw), ctypes.c_void_p))
            out_blob = DATA_BLOB()
            if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
                try:
                    buf = ctypes.string_at(out_blob.pbData, out_blob.cbData)
                    return buf.decode('utf-8')
                finally: ctypes.windll.kernel32.LocalFree(out_blob.pbData)
        except: pass
        return cipher_text or ""
