"""
Settings Window for AI Dev IDE - COMPLETE VERSION
"""
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, simpledialog
import json
import os
import threading

SETTINGS_PATH = os.path.join(os.path.expanduser("~"), ".ai_dev_ide_settings.json")

class SettingsWindow:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        
        self.window = tk.Toplevel(parent)
        self.window.title("AI Dev IDE - Settings")
        self.window.geometry("800x700")
        self.window.configure(bg="#1e1e1e")
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Load current settings from app first, then file, then defaults
        self.current_settings = app.settings.copy() if hasattr(app, 'settings') and app.settings else self.load_settings()
        
        # Initialize all variables to avoid AttributeErrors during save
        self.allowed_models_var = tk.StringVar(value=self.current_settings.get("allowed_models", "gpt-4o,gpt-4o-mini,gpt-3.5-turbo,codellama,llama2,mistral,claude-3-opus,claude-3-sonnet,gemini-1.5-pro,gemini-1.5-flash"))
        self.model_filter_var = tk.StringVar(value="")
        
        self.auto_save_var = tk.BooleanVar(value=self.current_settings.get("auto_save", True))
        self.auto_save_interval_var = tk.StringVar(value=str(self.current_settings.get("auto_save_interval", 300)))
        self.syntax_var = tk.BooleanVar(value=self.current_settings.get("syntax_highlighting", True))
        self.line_numbers_var = tk.BooleanVar(value=self.current_settings.get("line_numbers", True))
        self.word_wrap_var = tk.BooleanVar(value=self.current_settings.get("word_wrap", True))
        self.font_family_var = tk.StringVar(value=self.current_settings.get("font_family", "Consolas"))
        self.font_size_var = tk.StringVar(value=str(self.current_settings.get("font_size", 11)))
        self.auto_reload_var = tk.BooleanVar(value=self.current_settings.get("auto_reload", True))
        
        self.max_files_var = tk.StringVar(value=str(self.current_settings.get("max_files", 10)))
        self.max_chars_var = tk.StringVar(value=str(self.current_settings.get("max_chars", 2000)))
        self.summarize_var = tk.BooleanVar(value=self.current_settings.get("summarize_files", True))
        self.send_modified_var = tk.BooleanVar(value=self.current_settings.get("send_modified", False))
        self.test_timeout_var = tk.StringVar(value=str(self.current_settings.get("test_timeout", 30)))
        self.max_test_runtime_var = tk.StringVar(value=str(self.current_settings.get("max_test_runtime", 60)))
        self.github_token_var = tk.StringVar(value=self._decrypt_secret(self.current_settings.get("github_token", "")))
        self.github_username_var = tk.StringVar(value=self.current_settings.get("github_username", ""))
        self.default_project_type_var = tk.StringVar(value=self.current_settings.get("default_project_type", "web"))
        
        self.theme_var = tk.StringVar(value=self.current_settings.get("theme_preset", "Dark"))
        
        self.project_planning_var = tk.BooleanVar(value=self.current_settings.get("project_planning", True))
        self.ask_questions_var = tk.BooleanVar(value=self.current_settings.get("ask_questions", True))
        self.auto_generate_readme_var = tk.BooleanVar(value=self.current_settings.get("auto_generate_readme", True))
        self.auto_generate_tests_var = tk.BooleanVar(value=self.current_settings.get("auto_generate_tests", True))
        self.auto_fix_var = tk.BooleanVar(value=self.current_settings.get("auto_fix", True))
        self.auto_fix_iterations_var = tk.StringVar(value=str(self.current_settings.get("auto_fix_iterations", 3)))
        self.auto_approve_minor_var = tk.BooleanVar(value=self.current_settings.get("auto_approve_minor", False))
        self.ask_for_approval_var = tk.BooleanVar(value=not self.current_settings.get("agent_auto_approve", False))
        self.test_mode_no_input_var = tk.BooleanVar(value=self.current_settings.get("test_mode_no_input", False))
        self.show_system_messages_var = tk.BooleanVar(value=self.current_settings.get("show_system_messages", True))
        self.disable_auto_save_notifications_var = tk.BooleanVar(value=self.current_settings.get("disable_auto_save_notifications", False))
        self.agent_auto_approve_var = tk.BooleanVar(value=self.current_settings.get("agent_auto_approve", False))
        self.agent_monitor_refresh_var = tk.StringVar(value=str(self.current_settings.get("agent_monitor_refresh_ms", 5000)))
        
        self.audio_device_var = tk.StringVar()
        self.agent_sound_var = tk.StringVar(value=self.current_settings.get("agent_done_sound", ""))
        self.agent_volume_var = tk.IntVar(value=self.current_settings.get("agent_done_volume", 80))
        
        self.setup_ui()

    # --- Secure storage helpers (Windows DPAPI) ---
    def _encrypt_secret(self, plain_text):
        try:
            import ctypes, base64
            if not plain_text:
                return ""
            CRYPTPROTECT_LOCAL_MACHINE = 0x00000004
            data_in = ctypes.create_string_buffer(plain_text.encode('utf-8'))
            class DATA_BLOB(ctypes.Structure):
                _fields_ = [("cbData", ctypes.c_uint), ("pbData", ctypes.c_void_p)]
            in_blob = DATA_BLOB(len(data_in.raw), ctypes.cast(ctypes.byref(data_in), ctypes.c_void_p))
            out_blob = DATA_BLOB()
            CryptProtectData = ctypes.windll.crypt32.CryptProtectData
            if CryptProtectData(ctypes.byref(in_blob), None, None, None, None, CRYPTPROTECT_LOCAL_MACHINE, ctypes.byref(out_blob)):
                try:
                    buf = ctypes.string_at(out_blob.pbData, out_blob.cbData)
                    return "enc:" + base64.b64encode(buf).decode('ascii')
                finally:
                    ctypes.windll.kernel32.LocalFree(out_blob.pbData)
        except Exception:
            pass
        return plain_text

    def _decrypt_secret(self, cipher_text):
        try:
            import ctypes, base64
            if not cipher_text or not cipher_text.startswith("enc:"):
                return cipher_text or ""
            raw = base64.b64decode(cipher_text[4:])
            class DATA_BLOB(ctypes.Structure):
                _fields_ = [("cbData", ctypes.c_uint), ("pbData", ctypes.c_void_p)]
            in_blob = DATA_BLOB(len(raw), ctypes.cast(ctypes.create_string_buffer(raw), ctypes.c_void_p))
            out_blob = DATA_BLOB()
            CryptUnprotectData = ctypes.windll.crypt32.CryptUnprotectData
            if CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
                try:
                    buf = ctypes.string_at(out_blob.pbData, out_blob.cbData)
                    return buf.decode('utf-8')
                finally:
                    ctypes.windll.kernel32.LocalFree(out_blob.pbData)
        except Exception:
            pass
        return cipher_text or ""
        
    def load_settings(self):
        """Load settings from file"""
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        
        # Default settings
        return {
            "api_provider": "openai",
            "api_url": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-4o-mini",
            "huggingface_token": "",
            "ollama_url": "http://localhost:11434",
            "ollama_model": "llama2",
            "openai_url": "https://api.openai.com/v1/chat/completions",
            "openai_token": "",
            "openai_model": "gpt-4o-mini",
            "github_token": "",
            "max_files": 10,
            "max_chars": 2000,
            "summarize_files": True,
            "send_modified": False,
            "theme_preset": "Dark",
            "auto_save": True,
            "auto_save_interval": 300,
            "syntax_highlighting": True,
            "line_numbers": True,
            "word_wrap": True,
            "font_size": 11,
            "font_family": "Consolas",
            "test_timeout": 30,
            "max_test_runtime": 60,
            "auto_fix": True,
            "auto_fix_iterations": 3,
            "auto_reload": True,
            "project_planning": True,
            "ask_questions": True,
            "auto_generate_readme": True,
            "auto_generate_tests": True,
            "agent_auto_approve": False,
            "default_project_type": "web"
        }
    
    def save_settings(self, settings):
        """Save settings to file"""
        try:
            os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            return False
    
    def setup_ui(self):
        """Setup the settings UI"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Editor Settings Tab
        self.setup_editor_tab(notebook)
        
        # Project Settings Tab
        self.setup_project_tab(notebook)
        
        # Theme Settings Tab
        self.setup_theme_tab(notebook)
        
        # Features Tab
        self.setup_features_tab(notebook)
        
        # Audio Tab
        self.setup_audio_tab(notebook)
        
        # Chat Settings Tab
        self.setup_chat_settings_tab(notebook)
        
        # Extensions Tab
        self.setup_extensions_tab(notebook)
        
        # Buttons at bottom
        self.setup_buttons()
    
    def sync_approval_vars(self):
        """Synchronize agent_auto_approve_var with ask_for_approval_var"""
        self.ask_for_approval_var.set(not self.agent_auto_approve_var.get())

    def setup_editor_tab(self, notebook):
        """Setup editor settings tab"""
        editor_frame = ttk.Frame(notebook)
        notebook.add(editor_frame, text="✏️ Editor")
        
        row = 0
        
        # Auto-save
        ttk.Checkbutton(editor_frame, text="Enable auto-save", 
                       variable=self.auto_save_var).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        ttk.Label(editor_frame, text="Auto-save interval (seconds):").grid(row=row, column=0, padx=30, pady=5, sticky="w")
        ttk.Entry(editor_frame, textvariable=self.auto_save_interval_var, width=10).grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1
        
        # Syntax highlighting
        ttk.Checkbutton(editor_frame, text="Enable syntax highlighting", 
                       variable=self.syntax_var).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        # Line numbers
        ttk.Checkbutton(editor_frame, text="Show line numbers", 
                       variable=self.line_numbers_var).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        # Word wrap
        ttk.Checkbutton(editor_frame, text="Enable word wrap", 
                       variable=self.word_wrap_var).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        # Font settings
        ttk.Label(editor_frame, text="Font Family:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        font_families = ["Consolas", "Courier New", "Monaco", "Menlo", "DejaVu Sans Mono", "Ubuntu Mono", "Fira Code", "JetBrains Mono"]
        ttk.Combobox(editor_frame, textvariable=self.font_family_var, values=font_families, width=20).grid(row=row, column=1, padx=10, pady=10)
        row += 1
        
        ttk.Label(editor_frame, text="Font Size:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        ttk.Entry(editor_frame, textvariable=self.font_size_var, width=10).grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1
        
        # Auto-reload
        ttk.Checkbutton(editor_frame, text="Auto-reload modified files", 
                       variable=self.auto_reload_var).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
    
    def setup_project_tab(self, notebook):
        """Setup project settings tab"""
        project_frame = ttk.Frame(notebook)
        notebook.add(project_frame, text="📁 Project")
        
        row = 0
        
        # Max files to send to AI
        ttk.Label(project_frame, text="Max files to send to AI:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        ttk.Entry(project_frame, textvariable=self.max_files_var, width=10).grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1
        
        # Max chars per file
        ttk.Label(project_frame, text="Max characters per file:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        ttk.Entry(project_frame, textvariable=self.max_chars_var, width=10).grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1
        
        # Summarize files
        ttk.Checkbutton(project_frame, text="Summarize files for AI context", 
                       variable=self.summarize_var).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        # Send modified only
        ttk.Checkbutton(project_frame, text="Send only modified files to AI", 
                       variable=self.send_modified_var).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        # Test timeout
        ttk.Label(project_frame, text="Test timeout (seconds):").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        ttk.Entry(project_frame, textvariable=self.test_timeout_var, width=10).grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1
        
        # Max test runtime
        ttk.Label(project_frame, text="Max test runtime (seconds):").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        ttk.Entry(project_frame, textvariable=self.max_test_runtime_var, width=10).grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1
        
        # GitHub token
        ttk.Label(project_frame, text="GitHub Token:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        ttk.Entry(project_frame, textvariable=self.github_token_var, width=40, show="*").grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1
        
        # Default project type
        ttk.Label(project_frame, text="Default Project Type:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        project_types = ["web", "cli", "desktop", "api", "library", "data", "ai", "mobile", "game", "other"]
        ttk.Combobox(project_frame, textvariable=self.default_project_type_var, values=project_types, width=15).grid(row=row, column=1, padx=10, pady=10)
        row += 1
    
    def setup_theme_tab(self, notebook):
        """Setup theme settings tab"""
        theme_frame = ttk.Frame(notebook)
        notebook.add(theme_frame, text="🎨 Theme")
        
        # Split into left (controls) and right (preview/editor)
        paned = ttk.PanedWindow(theme_frame, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(paned)
        right_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        paned.add(right_frame, weight=2)
        
        # --- Left Frame: Selection & Actions ---
        ttk.Label(left_frame, text="Select Theme:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.custom_list = list(self.current_settings.get("custom_themes", {}).keys())
        self.presets = ["Dark", "Light", "Blue", "Green", "Purple", "Solarized", "Monokai", "Nordic", "Cyberpunk", "Nebula"]
        theme_values = self.presets + self.custom_list
        
        self.theme_combo = ttk.Combobox(left_frame, textvariable=self.theme_var, 
                                  values=theme_values, 
                                  state="readonly")
        self.theme_combo.pack(fill="x", pady=(0, 10))
        self.theme_combo.bind("<<ComboboxSelected>>", self.on_theme_selected)
        
        # Actions
        btn_frame = ttk.LabelFrame(left_frame, text="Actions")
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="Apply Theme", command=self.apply_theme_preview).pack(fill="x", padx=5, pady=5)
        ttk.Button(btn_frame, text="Save as New Theme...", command=self.save_as_new_theme).pack(fill="x", padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Copy Theme JSON", command=self.copy_theme_to_clipboard).pack(fill="x", padx=5, pady=5)
        ttk.Button(btn_frame, text="Paste Theme JSON", command=self.paste_theme_from_clipboard).pack(fill="x", padx=5, pady=5)
        
        self.btn_delete = ttk.Button(btn_frame, text="Delete Custom Theme", command=self.delete_custom_theme, state="disabled")
        self.btn_delete.pack(fill="x", padx=5, pady=5)

        # --- Right Frame: Preview & Editor ---
        
        # Live Preview
        preview_labelframe = ttk.LabelFrame(right_frame, text="Live Preview")
        preview_labelframe.pack(fill="x", pady=(0, 10))
        
        self.preview_text = tk.Text(preview_labelframe, height=8, width=40)
        self.preview_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.preview_text.insert("1.0", """def example_function():
    '''Example Python code'''
    numbers = [1, 2, 3, 4, 5]
    total = sum(numbers)
    
    if total > 10:
        print("Total is greater than 10")
    else:
        print("Total is 10 or less")
    
    return total""")
        self.preview_text.config(state="disabled")
        
        # Theme Editor
        self.editor_labelframe = ttk.LabelFrame(right_frame, text="Theme Editor")
        self.editor_labelframe.pack(fill="both", expand=True)
        
        # Scrollable editor area
        canvas = tk.Canvas(self.editor_labelframe, bg="#2d2d30")
        scrollbar = ttk.Scrollbar(self.editor_labelframe, orient="vertical", command=canvas.yview)
        self.editor_scroll_frame = ttk.Frame(canvas)
        
        self.editor_scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.editor_scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Color vars storage
        self.color_vars = {}
        self.color_buttons = {}
        
        # Initial population
        self.populate_editor()
        self.on_theme_selected()

    def populate_editor(self):
        """Populate the theme editor with color pickers"""
        # Clear existing
        for widget in self.editor_scroll_frame.winfo_children():
            widget.destroy()
            
        # Define categories and keys
        categories = {
            "Window": ["window_bg", "window_fg"],
            "Editor": ["editor_bg", "editor_fg", "editor_cursor", "editor_selection", "editor_gutter", "editor_gutter_fg"],
            "Syntax": ["syntax_keyword", "syntax_string", "syntax_comment", "syntax_function", "syntax_number", "syntax_builtin", "syntax_class"],
            "UI Elements": ["tree_bg", "tree_fg", "tree_selection", "panel_bg", "panel_fg", "text_bg", "text_fg", "button_bg", "button_fg", "console_bg", "console_fg"]
        }
        
        row = 0
        for category, keys in categories.items():
            ttk.Label(self.editor_scroll_frame, text=category, font=("Segoe UI", 9, "bold")).grid(row=row, column=0, columnspan=2, pady=(10, 5), sticky="w", padx=5)
            row += 1
            
            for key in keys:
                nice_name = key.replace("_", " ").title()
                ttk.Label(self.editor_scroll_frame, text=nice_name + ":").grid(row=row, column=0, padx=5, pady=2, sticky="w")
                
                # Color preview/picker button
                self.color_vars[key] = tk.StringVar(value="#000000")
                
                btn = tk.Button(self.editor_scroll_frame, textvariable=self.color_vars[key], width=10, relief="flat")
                btn.configure(command=lambda k=key, b=btn: self.pick_color(k, b))
                btn.grid(row=row, column=1, padx=5, pady=2, sticky="w")
                self.color_buttons[key] = btn
                
                # Trace changes to update preview
                # self.color_vars[key].trace_add("write", lambda *args: self.update_preview_from_editor())
                
                row += 1

    def pick_color(self, key, btn):
        """Open color picker for a key"""
        current = self.color_vars[key].get()
        color = colorchooser.askcolor(initialcolor=current, title=f"Choose {key}")
        if color[1]:
            self.color_vars[key].set(color[1])
            btn.configure(bg=color[1])
            # Check brightness for text color on button
            # Simple heuristic
            try:
                r = int(color[1][1:3], 16)
                g = int(color[1][3:5], 16)
                b = int(color[1][5:7], 16)
                brightness = (r * 299 + g * 587 + b * 114) / 1000
                btn.configure(fg="#000000" if brightness > 128 else "#ffffff")
            except: pass
            
            self.update_preview_from_editor()

    def on_theme_selected(self, event=None):
        """Handle theme selection"""
        theme_name = self.theme_var.get()
        theme_data = self.get_theme_data(theme_name)
        
        # Update editor values
        for key, var in self.color_vars.items():
            color = theme_data.get(key, "#000000")
            var.set(color)
            if key in self.color_buttons:
                self.color_buttons[key].configure(bg=color)
                # Adjust text color
                try:
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    brightness = (r * 299 + g * 587 + b * 114) / 1000
                    self.color_buttons[key].configure(fg="#000000" if brightness > 128 else "#ffffff")
                except: pass
        
        # Enable/Disable delete button
        if theme_name in self.presets:
            self.btn_delete.configure(state="disabled")
            # Maybe disable editing too? Or allow editing but require "Save As"
            # For now, let's allow editing as a "preview" of changes, but saving requires a new name.
        else:
            self.btn_delete.configure(state="normal")
            
        self.update_preview_from_editor()

    def update_preview_from_editor(self):
        """Update the preview text based on current editor values"""
        bg = self.color_vars.get("window_bg", tk.StringVar(value="#1e1e1e")).get()
        fg = self.color_vars.get("window_fg", tk.StringVar(value="#d4d4d4")).get()
        
        # Also get syntax colors for more accurate preview if we want to go deep
        # But text widget global bg/fg is the main one for the window feel
        # Let's try to tag the text for syntax highlighting preview
        
        self.preview_text.config(state="normal")
        self.preview_text.config(bg=bg, fg=fg)
        
        # Simple syntax highlighting for preview
        self.preview_text.tag_configure("keyword", foreground=self.color_vars.get("syntax_keyword", tk.StringVar(value="#ff0000")).get())
        self.preview_text.tag_configure("string", foreground=self.color_vars.get("syntax_string", tk.StringVar(value="#00ff00")).get())
        self.preview_text.tag_configure("comment", foreground=self.color_vars.get("syntax_comment", tk.StringVar(value="#888888")).get())
        self.preview_text.tag_configure("function", foreground=self.color_vars.get("syntax_function", tk.StringVar(value="#0000ff")).get())
        
        # Re-apply content to clear old tags
        content = """def example_function():
    '''Example Python code'''
    numbers = [1, 2, 3, 4, 5]
    total = sum(numbers)
    
    if total > 10:
        print("Total is greater than 10")
    else:
        print("Total is 10 or less")
    
    return total"""
        
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", content)
        
        # Apply tags manually for this static content
        self.preview_text.tag_add("keyword", "1.0", "1.3") # def
        self.preview_text.tag_add("function", "1.4", "1.20") # example_function
        self.preview_text.tag_add("comment", "2.4", "2.25") # docstring
        self.preview_text.tag_add("keyword", "6.4", "6.6") # if
        self.preview_text.tag_add("keyword", "8.4", "8.8") # else
        self.preview_text.tag_add("keyword", "11.4", "11.10") # return
        self.preview_text.tag_add("string", "7.14", "7.40") # print string
        self.preview_text.tag_add("string", "9.14", "9.35") # print string
        
        self.preview_text.config(state="disabled")

    def get_theme_data(self, theme_name):
        """Get data for a theme by name"""
        if theme_name == "Dark":
            return self.app.theme_engine.create_dark_theme() if hasattr(self.app, 'theme_engine') else {}
        elif theme_name == "Light":
            return self.app.theme_engine.create_light_theme() if hasattr(self.app, 'theme_engine') else {}
        elif theme_name == "Blue":
            return self.create_blue_theme()
        elif theme_name == "Green":
            return self.create_green_theme()
        elif theme_name == "Purple":
            return self.create_purple_theme()
        elif theme_name == "Solarized":
            return self.create_solarized_theme()
        elif theme_name == "Monokai":
            return self.create_monokai_theme()
        elif theme_name == "Nordic":
            return self.create_nordic_theme()
        elif theme_name == "Cyberpunk":
            return self.create_cyberpunk_theme()
        elif theme_name == "Nebula":
            return self.create_nebula_theme()
        else:
            custom_themes = self.current_settings.get("custom_themes", {})
            return custom_themes.get(theme_name, {})

    def copy_theme_to_clipboard(self):
        """Copy current theme configuration to clipboard"""
        try:
            theme_data = {}
            for key, var in self.color_vars.items():
                theme_data[key] = var.get()
            
            json_str = json.dumps(theme_data, indent=2)
            self.window.clipboard_clear()
            self.window.clipboard_append(json_str)
            messagebox.showinfo("Success", "Theme JSON copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy theme: {e}")

    def paste_theme_from_clipboard(self):
        """Paste theme configuration from clipboard"""
        try:
            json_str = self.window.clipboard_get()
            if not json_str:
                return
                
            theme_data = json.loads(json_str)
            
            # Basic validation - check if it looks like a theme
            valid_keys = 0
            for key in self.color_vars.keys():
                if key in theme_data:
                    valid_keys += 1
            
            if valid_keys < 5:
                # Try to be lenient or show error?
                if not messagebox.askyesno("Warning", "Clipboard content doesn't look like a valid theme. Try to apply anyway?"):
                    return
            
            # Apply values
            for key, value in theme_data.items():
                if key in self.color_vars:
                    self.color_vars[key].set(value)
                    if key in self.color_buttons:
                        self.color_buttons[key].configure(bg=value)
                        # Adjust text color
                        try:
                            r = int(value[1:3], 16)
                            g = int(value[3:5], 16)
                            b = int(value[5:7], 16)
                            brightness = (r * 299 + g * 587 + b * 114) / 1000
                            self.color_buttons[key].configure(fg="#000000" if brightness > 128 else "#ffffff")
                        except: pass
            
            self.update_preview_from_editor()
            messagebox.showinfo("Success", "Theme pasted from clipboard!")
            
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Clipboard does not contain valid JSON.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste theme: {e}")

    def save_as_new_theme(self):
        """Save current editor colors as a new theme"""
        from tkinter import simpledialog
        name = simpledialog.askstring("Save Theme", "Enter name for new theme:")
        if not name:
            return
            
        if name in self.presets:
            messagebox.showerror("Error", f"Cannot overwrite default theme '{name}'. Please choose a different name.")
            return
            
        # Collect data
        theme_data = {}
        for key, var in self.color_vars.items():
            theme_data[key] = var.get()
            
        # Save to settings
        if "custom_themes" not in self.current_settings:
            self.current_settings["custom_themes"] = {}
            
        self.current_settings["custom_themes"][name] = theme_data
        
        # Update list
        self.custom_list = list(self.current_settings.get("custom_themes", {}).keys())
        theme_values = self.presets + self.custom_list
        self.theme_combo['values'] = theme_values
        self.theme_var.set(name)
        
        messagebox.showinfo("Success", f"Theme '{name}' saved.")
        self.on_theme_selected()

    def delete_custom_theme(self):
        """Delete selected custom theme"""
        name = self.theme_var.get()
        if name in self.presets:
            return
            
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete theme '{name}'?"):
            del self.current_settings["custom_themes"][name]
            
            # Update list
            self.custom_list = list(self.current_settings.get("custom_themes", {}).keys())
            theme_values = self.presets + self.custom_list
            self.theme_combo['values'] = theme_values
            self.theme_var.set("Dark")
            self.on_theme_selected()

    def update_theme_preview(self, event=None):
        """Compatibility wrapper for update_theme_preview"""
        self.on_theme_selected(event)

    def apply_theme_preview(self):
        """Apply theme preview"""
        # We apply what is currently in the editor, effectively
        # But strictly we should apply the saved theme. 
        # If the user modified colors but didn't save, we should warn or apply the custom colors temporarily?
        # The original behavior was "apply selected preset". 
        # But now we have an editor.
        
        # Let's see if the current editor matches the saved preset. 
        # If not, we might want to ask to save first? 
        # Or just apply the current editor colors as a "temporary" custom theme?
        
        # For simplicity: If it's a saved theme (preset or custom), apply it.
        # If modified, maybe save as "Current Custom"?
        
        # Actually, let's just apply the current editor state.
        theme_data = {}
        for key, var in self.color_vars.items():
            theme_data[key] = var.get()
            
        if hasattr(self.app, 'theme_engine'):
            self.app.theme_engine.apply_theme(theme_data)
            messagebox.showinfo("Theme Applied", "Theme applied successfully!")

    
    def create_solarized_theme(self):
        """Create solarized theme"""
        return {
            "window_bg": "#002b36",
            "window_fg": "#839496",
            "editor_bg": "#002b36",
            "editor_fg": "#839496",
            "editor_cursor": "#93a1a1",
            "editor_selection": "#073642",
            "editor_gutter": "#002b36",
            "editor_gutter_fg": "#586e75",
            "syntax_keyword": "#859900",
            "syntax_string": "#2aa198",
            "syntax_comment": "#586e75",
            "syntax_function": "#b58900",
            "syntax_number": "#d33682",
            "syntax_builtin": "#cb4b16",
            "syntax_class": "#268bd2",
            "tree_bg": "#073642",
            "tree_fg": "#93a1a1",
            "tree_selection": "#586e75",
            "panel_bg": "#073642",
            "panel_fg": "#93a1a1",
            "text_bg": "#002b36",
            "text_fg": "#839496",
            "button_bg": "#859900",
            "button_fg": "#002b36",
            "console_bg": "#002b36",
            "console_fg": "#839496",
        }
    
    def create_monokai_theme(self):
        """Create monokai theme"""
        return {
            "window_bg": "#272822",
            "window_fg": "#f8f8f2",
            "editor_bg": "#272822",
            "editor_fg": "#f8f8f2",
            "editor_cursor": "#f8f8f0",
            "editor_selection": "#49483e",
            "editor_gutter": "#272822",
            "editor_gutter_fg": "#90908a",
            "syntax_keyword": "#f92672",
            "syntax_string": "#e6db74",
            "syntax_comment": "#75715e",
            "syntax_function": "#a6e22e",
            "syntax_number": "#ae81ff",
            "syntax_builtin": "#66d9ef",
            "syntax_class": "#a6e22e",
            "tree_bg": "#272822",
            "tree_fg": "#f8f8f2",
            "tree_selection": "#49483e",
            "panel_bg": "#272822",
            "panel_fg": "#f8f8f2",
            "text_bg": "#272822",
            "text_fg": "#f8f8f2",
            "button_bg": "#f92672",
            "button_fg": "#f8f8f2",
            "console_bg": "#272822",
            "console_fg": "#f8f8f2",
        }
    
    def create_blue_theme(self):
        """Create a blue theme"""
        return {
            "window_bg": "#0a1929",
            "window_fg": "#b3cde0",
            "editor_bg": "#0a1929",
            "editor_fg": "#b3cde0",
            "editor_cursor": "#66b3ff",
            "editor_selection": "#1e3a5f",
            "editor_gutter": "#0a1929",
            "editor_gutter_fg": "#5078a0",
            "syntax_keyword": "#66b3ff",
            "syntax_string": "#ff9966",
            "syntax_comment": "#5c9e5c",
            "syntax_function": "#ffcc66",
            "syntax_number": "#99cc99",
            "syntax_builtin": "#66cccc",
            "syntax_class": "#66cccc",
            "tree_bg": "#132f4c",
            "tree_fg": "#b3cde0",
            "tree_selection": "#1e3a5f",
            "panel_bg": "#1a365d",
            "panel_fg": "#b3cde0",
            "text_bg": "#0a1929",
            "text_fg": "#b3cde0",
            "button_bg": "#2d5a9c",
            "button_fg": "#ffffff",
            "console_bg": "#0a1929",
            "console_fg": "#b3cde0",
        }
    
    def create_green_theme(self):
        """Create a green theme"""
        return {
            "window_bg": "#0d1f0d",
            "window_fg": "#c8e6c9",
            "editor_bg": "#0d1f0d",
            "editor_fg": "#c8e6c9",
            "editor_cursor": "#81c784",
            "editor_selection": "#2e5c2e",
            "editor_gutter": "#0d1f0d",
            "editor_gutter_fg": "#5a8c5a",
            "syntax_keyword": "#81c784",
            "syntax_string": "#ffb74d",
            "syntax_comment": "#a5d6a7",
            "syntax_function": "#fff176",
            "syntax_number": "#a5d6a7",
            "syntax_builtin": "#4db6ac",
            "syntax_class": "#4db6ac",
            "tree_bg": "#1b351b",
            "tree_fg": "#c8e6c9",
            "tree_selection": "#2e5c2e",
            "panel_bg": "#1b351b",
            "panel_fg": "#c8e6c9",
            "text_bg": "#0d1f0d",
            "text_fg": "#c8e6c9",
            "button_bg": "#388e3c",
            "button_fg": "#ffffff",
            "console_bg": "#0d1f0d",
            "console_fg": "#c8e6c9",
        }
    
    def create_purple_theme(self):
        """Create a purple theme"""
        return {
            "window_bg": "#1a0d2e",
            "window_fg": "#d1c4e9",
            "editor_bg": "#1a0d2e",
            "editor_fg": "#d1c4e9",
            "editor_cursor": "#ba68c8",
            "editor_selection": "#4a1a6b",
            "editor_gutter": "#1a0d2e",
            "editor_gutter_fg": "#7b5fa6",
            "syntax_keyword": "#ba68c8",
            "syntax_string": "#ff8a65",
            "syntax_comment": "#a5a5d6",
            "syntax_function": "#ffd54f",
            "syntax_number": "#ce93d8",
            "syntax_builtin": "#80deea",
            "syntax_class": "#80deea",
            "tree_bg": "#2d1b44",
            "tree_fg": "#d1c4e9",
            "tree_selection": "#4a1a6b",
            "panel_bg": "#2d1b44",
            "panel_fg": "#d1c4e9",
            "text_bg": "#1a0d2e",
            "text_fg": "#d1c4e9",
            "button_bg": "#7b1fa2",
            "button_fg": "#ffffff",
            "console_bg": "#1a0d2e",
            "console_fg": "#d1c4e9",
        }

    def create_nordic_theme(self):
        """Create nordic theme"""
        return {
            "window_bg": "#2e3440",
            "window_fg": "#d8dee9",
            "editor_bg": "#2e3440",
            "editor_fg": "#d8dee9",
            "editor_cursor": "#88c0d0",
            "editor_selection": "#434c5e",
            "editor_gutter": "#2e3440",
            "editor_gutter_fg": "#4c566a",
            "syntax_keyword": "#81a1c1",
            "syntax_string": "#a3be8c",
            "syntax_comment": "#616e88",
            "syntax_function": "#88c0d0",
            "syntax_number": "#b48ead",
            "syntax_builtin": "#81a1c1",
            "syntax_class": "#8fbcbb",
            "tree_bg": "#3b4252",
            "tree_fg": "#d8dee9",
            "tree_selection": "#4c566a",
            "panel_bg": "#3b4252",
            "panel_fg": "#d8dee9",
            "text_bg": "#2e3440",
            "text_fg": "#d8dee9",
            "button_bg": "#5e81ac",
            "button_fg": "#eceff4",
            "console_bg": "#2e3440",
            "console_fg": "#d8dee9",
        }

    def create_cyberpunk_theme(self):
        """Create cyberpunk theme"""
        return {
            "window_bg": "#000b1e",
            "window_fg": "#00ff9f",
            "editor_bg": "#000b1e",
            "editor_fg": "#00ff9f",
            "editor_cursor": "#ff0055",
            "editor_selection": "#1a1a40",
            "editor_gutter": "#000b1e",
            "editor_gutter_fg": "#005f73",
            "syntax_keyword": "#ff0055",
            "syntax_string": "#fcee0a",
            "syntax_comment": "#005f73",
            "syntax_function": "#00ff9f",
            "syntax_number": "#00b8ff",
            "syntax_builtin": "#bd00ff",
            "syntax_class": "#00ff9f",
            "tree_bg": "#05162e",
            "tree_fg": "#00ff9f",
            "tree_selection": "#ff0055",
            "panel_bg": "#05162e",
            "panel_fg": "#00ff9f",
            "text_bg": "#000b1e",
            "text_fg": "#00ff9f",
            "button_bg": "#ff0055",
            "button_fg": "#000000",
            "console_bg": "#000b1e",
            "console_fg": "#00ff9f",
        }

    def create_nebula_theme(self):
        """Create nebula theme"""
        return {
            "window_bg": "#0b0e14",
            "window_fg": "#b3b1ad",
            "editor_bg": "#0b0e14",
            "editor_fg": "#b3b1ad",
            "editor_cursor": "#e6b450",
            "editor_selection": "#1f2430",
            "editor_gutter": "#0b0e14",
            "editor_gutter_fg": "#3e4b59",
            "syntax_keyword": "#ff8f40",
            "syntax_string": "#aad94c",
            "syntax_comment": "#62696e",
            "syntax_function": "#ffb454",
            "syntax_number": "#d2a6ff",
            "syntax_builtin": "#f29668",
            "syntax_class": "#ffb454",
            "tree_bg": "#0f131a",
            "tree_fg": "#b3b1ad",
            "tree_selection": "#1f2430",
            "panel_bg": "#0f131a",
            "panel_fg": "#b3b1ad",
            "text_bg": "#0b0e14",
            "text_fg": "#b3b1ad",
            "button_bg": "#ff8f40",
            "button_fg": "#0b0e14",
            "console_bg": "#0b0e14",
            "console_fg": "#b3b1ad",
        }
    
    def setup_features_tab(self, notebook):
        """Setup features settings tab"""
        features_frame = ttk.Frame(notebook)
        notebook.add(features_frame, text="⚡ Features")
        
        row = 0
        
        # Project planning
        ttk.Checkbutton(features_frame, text="Enable project planning assistant", 
                       variable=self.project_planning_var).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        # Ask questions
        ttk.Checkbutton(features_frame, text="Ask clarifying questions for projects", 
                       variable=self.ask_questions_var).grid(row=row, column=0, padx=30, pady=5, sticky="w")
        row += 1
        
        # Auto generate README
        ttk.Checkbutton(features_frame, text="Auto-generate README.md", 
                       variable=self.auto_generate_readme_var).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        # Auto generate tests
        ttk.Checkbutton(features_frame, text="Auto-generate test files", 
                       variable=self.auto_generate_tests_var).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        # Auto fix
        ttk.Checkbutton(features_frame, text="Enable auto-fix for errors", 
                       variable=self.auto_fix_var).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        ttk.Label(features_frame, text="Max auto-fix iterations:").grid(row=row, column=0, padx=30, pady=5, sticky="w")
        ttk.Entry(features_frame, textvariable=self.auto_fix_iterations_var, width=10).grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1
        
        # Code approval
        ttk.Label(features_frame, text="Code Approval:", font=("Arial", 10, "bold")).grid(row=row, column=0, padx=10, pady=15, sticky="w", columnspan=2)
        row += 1
        
        ttk.Checkbutton(features_frame, text="Auto-approve minor changes", 
                       variable=self.auto_approve_minor_var).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        row += 1
        
        ttk.Checkbutton(features_frame, text="Always ask for approval before applying changes", 
                       variable=self.ask_for_approval_var, command=self._on_ask_for_approval_toggle).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        row += 1

        # Testing options
        ttk.Label(features_frame, text="Testing:", font=("Arial", 10, "bold")).grid(row=row, column=0, padx=10, pady=15, sticky="w", columnspan=2)
        row += 1
        
        ttk.Checkbutton(features_frame, text="Test mode: Remove input() statements when running scripts", 
                       variable=self.test_mode_no_input_var).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        row += 1
        
        ttk.Checkbutton(features_frame, text="Show System Messages (Logs, Status updates)", 
                       variable=self.show_system_messages_var).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        row += 1
        
        ttk.Checkbutton(features_frame, text="Auto-Agent: Automatically allow commands and file edits", 
                       variable=self.agent_auto_approve_var, command=self.sync_approval_vars).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        row += 1

        # Agent monitor refresh
        ttk.Label(features_frame, text="Agent monitor refresh (ms):").grid(row=row, column=0, padx=10, pady=5, sticky="w")
        ttk.Entry(features_frame, textvariable=self.agent_monitor_refresh_var, width=10).grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1

    def _on_ask_for_approval_toggle(self):
        # Update the app's agent_auto_approve setting
        self.app.settings["agent_auto_approve"] = not self.ask_for_approval_var.get()
        self.app.save_settings(self.app.settings)
        # Notify AI panel to update its checkbox
        if self.app.ai_panel:
            self.app.ai_panel.update_auto_agent_checkbox()
    
    def setup_audio_tab(self, notebook):
        """Setup audio settings tab"""
        audio_frame = ttk.Frame(notebook)
        notebook.add(audio_frame, text="🎙️ Audio")
        
        row = 0
        
        ttk.Label(audio_frame, text="Microphone Device:", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        # Device list
        # Add "Windows Default" option
        self.device_combo = ttk.Combobox(audio_frame, textvariable=self.audio_device_var, width=50, state="readonly")
        self.device_combo.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        self.device_combo.bind("<<ComboboxSelected>>", self.on_audio_device_selected)
        row += 1
        
        # Refresh button
        ttk.Button(audio_frame, text="Refresh Devices", command=self.refresh_audio_devices).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        row += 1

        # Agent completion sound
        ttk.Label(audio_frame, text="Agent Completion Sound:", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        # Sound Selection Row
        sound_sel_row = ttk.Frame(audio_frame)
        sound_sel_row.grid(row=row, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        
        # Dropdown for sounds in DoneSound folder
        self.sound_dropdown_var = tk.StringVar()
        self.sound_dropdown = ttk.Combobox(sound_sel_row, textvariable=self.sound_dropdown_var, width=40, state="readonly")
        self.sound_dropdown.pack(side="left", padx=5)
        self.sound_dropdown.bind("<<ComboboxSelected>>", self.on_sound_dropdown_selected)
        
        sound_entry = ttk.Entry(sound_sel_row, textvariable=self.agent_sound_var, width=40)
        sound_entry.pack(side="left", padx=5)
        
        row += 1

        # Volume Row
        vol_row = ttk.Frame(audio_frame)
        vol_row.grid(row=row, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        
        ttk.Label(vol_row, text="Volume:").pack(side="left", padx=5)
        self.agent_volume_var = tk.IntVar(value=self.current_settings.get("agent_done_volume", 80))
        vol = ttk.Scale(vol_row, from_=0, to=100, orient="horizontal", length=200, command=lambda v: self.agent_volume_var.set(int(float(v))))
        vol.set(self.agent_volume_var.get())
        vol.pack(side="left", padx=10)
        
        def browse_sound():
            path = tk.filedialog.askopenfilename(title="Select Sound", filetypes=[("Audio", "*.mp3 *.mp4 *.wav")])
            if path:
                self.agent_sound_var.set(path)
                self.sound_dropdown_var.set("Custom...")
        
        def test_sound():
            try:
                import os
                path = self.agent_sound_var.get().strip()
                vol_level = int(self.agent_volume_var.get())
                if path and os.path.exists(path):
                    try:
                        self.app.play_media(path, vol_level)
                        return
                    except Exception:
                        pass
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
        
        ttk.Button(vol_row, text="Browse", command=browse_sound).pack(side="left", padx=5)
        ttk.Button(vol_row, text="Test", command=test_sound).pack(side="left", padx=5)
        row += 1

        # Microphone Test Section
        ttk.Label(audio_frame, text="Microphone Test:", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        test_frame = ttk.Frame(audio_frame)
        test_frame.grid(row=row, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        
        self.mic_test_btn = ttk.Button(test_frame, text="Start Test", command=self.toggle_mic_test)
        self.mic_test_btn.pack(side="left", padx=5)
        
        self.mic_level_var = tk.DoubleVar(value=0)
        self.mic_progress = ttk.Progressbar(test_frame, variable=self.mic_level_var, maximum=100, length=200)
        self.mic_progress.pack(side="left", padx=10, fill="x", expand=True)
        
        self.mic_status_label = ttk.Label(test_frame, text="Idle")
        self.mic_status_label.pack(side="left", padx=5)
        
        self.mic_db_label = ttk.Label(test_frame, text="0 dB")
        self.mic_db_label.pack(side="left", padx=5)
        
        row += 1
        
        # Initial population
        self.refresh_audio_devices()
        self.refresh_sound_list()

    def refresh_sound_list(self):
        """Populate the sound dropdown with files from DoneSound directory"""
        try:
            from utils import get_resource_path
            sound_dir = get_resource_path("DoneSound")
            if not os.path.exists(sound_dir):
                os.makedirs(sound_dir, exist_ok=True)
            
            sounds = ["None"]
            for f in os.listdir(sound_dir):
                if f.endswith(('.mp3', '.wav', '.mp4')):
                    sounds.append(f)
            
            sounds.append("Custom...")
            self.sound_dropdown['values'] = sounds
            
            # Match current path to dropdown
            current_path = self.agent_sound_var.get()
            if not current_path:
                self.sound_dropdown.set("None")
            else:
                filename = os.path.basename(current_path)
                if filename in sounds:
                    self.sound_dropdown.set(filename)
                else:
                    self.sound_dropdown.set("Custom...")
        except Exception:
            pass

    def on_sound_dropdown_selected(self, event=None):
        import os
        val = self.sound_dropdown_var.get()
        if val == "None":
            self.agent_sound_var.set("")
        elif val == "Custom...":
            pass # Keep current or wait for browse
        else:
            from utils import get_resource_path
            path = get_resource_path(os.path.join("DoneSound", val))
            self.agent_sound_var.set(path)

    def toggle_mic_test(self):
        if hasattr(self, "mic_testing") and self.mic_testing:
            self.stop_mic_test()
        else:
            self.start_mic_test()

    def start_mic_test(self):
        self.mic_testing = True
        self.mic_test_btn.config(text="Stop Test")
        self.mic_status_label.config(text="Testing...", foreground="orange")
        self.mic_test_thread = threading.Thread(target=self._mic_test_loop, daemon=True)
        self.mic_test_thread.start()

    def stop_mic_test(self):
        self.mic_testing = False
        self.mic_test_btn.config(text="Start Test")
        self.mic_level_var.set(0)
        self.mic_db_label.config(text="0 dB")
        # Final pass/fail check based on last max level
        if hasattr(self, "last_max_db") and self.last_max_db > -40:
             self.mic_status_label.config(text="PASS", foreground="green")
        else:
             self.mic_status_label.config(text="FAIL/QUIET", foreground="red")

    def _mic_test_loop(self):
        try:
            import sounddevice as sd
            import numpy as np
            import math
            
            dev_str = self.device_combo.get()
            sd_idx = None
            if dev_str == "Windows Default":
                sd_idx = None # sounddevice default
            elif dev_str.startswith("SD:"):
                try:
                    sd_idx = int(dev_str.split()[0].split(":")[1])
                except Exception:
                    pass
            else:
                # For SR indices, we might need to find the matching SD device
                # but for now let's just use None (default) if it's not an SD prefix
                sd_idx = None
            
            self.last_max_db = -100
            
            def callback(indata, frames, time, status):
                if not self.mic_testing:
                    return
                if status:
                    print(f"Mic Test Status: {status}")
                
                # RMS to dB
                rms = np.sqrt(np.mean(indata**2))
                if rms > 0:
                    db = 20 * math.log10(rms)
                else:
                    db = -100
                
                self.last_max_db = max(self.last_max_db, db)
                
                # Update UI
                # db usually -60 to 0. Map to 0-100 progress
                level = min(100, max(0, (db + 60) * 1.6))
                self.window.after(0, lambda l=level, d=db: self._update_mic_ui(l, d))

            with sd.InputStream(device=sd_idx, channels=1, callback=callback):
                while self.mic_testing:
                    sd.sleep(100)
                    
        except Exception as e:
            self.window.after(0, lambda err=e: messagebox.showerror("Mic Test Error", f"Failed to test microphone: {err}"))
            self.window.after(0, self.stop_mic_test)

    def _update_mic_ui(self, level, db):
        self.mic_level_var.set(level)
        self.mic_db_label.config(text=f"{db:.1f} dB")

    def refresh_audio_devices(self):
        """Refresh the list of available audio devices"""
        try:
            from utils.voice_handler import VoiceHandler
            handler = VoiceHandler()
            
            if not handler.available:
                self.device_combo['values'] = ["Voice input not available"]
                self.device_combo.current(0)
                self.device_combo.config(state="disabled")
                return
                
            devices = handler.get_device_list()
            if not devices:
                self.device_combo['values'] = ["No devices found"]
                self.device_combo.current(0)
                return

            self.device_combo['values'] = devices
            
            # Select current
            current_idx = self.current_settings.get("audio_device_index", 0)
            
            # If we have a saved index, try to select it
            if 0 <= current_idx < len(devices):
                self.device_combo.current(current_idx)
            else:
                # Default to "Windows Default" which is the first one now
                self.device_combo.current(0)
            
            # Update the handler immediately to ensure the correct device is ready
            handler.set_device(self.device_combo.current())
                    
        except Exception as e:
            self.device_combo['values'] = [f"Error: {e}"]
            self.device_combo.current(0)

    def on_audio_device_selected(self, event=None):
        """Persist selected audio device index"""
        try:
            idx = self.device_combo.current()
            if idx is not None and idx >= 0:
                self.current_settings["audio_device_index"] = idx
        except Exception:
            pass

    def setup_chat_settings_tab(self, notebook):
        """Setup AI Chat settings tab"""
        chat_frame = ttk.Frame(notebook)
        notebook.add(chat_frame, text="💬 Chat")
        
        row = 0
        
        ttk.Label(chat_frame, text="AI Chat Output Controls", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        # System messages toggle
        ttk.Checkbutton(chat_frame, text="Show system messages", 
                       variable=self.show_system_messages_var).grid(row=row, column=0, padx=20, pady=5, sticky="w")
        row += 1
        
        # Auto-save notifications toggle
        ttk.Checkbutton(chat_frame, text="Disable auto-save notifications", 
                       variable=self.disable_auto_save_notifications_var).grid(row=row, column=0, padx=20, pady=5, sticky="w")
        row += 1
        
        ttk.Separator(chat_frame, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1
        
        ttk.Label(chat_frame, text="Advanced AI Chat Options", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        row += 1
        
        # Additional chat controls can go here
        ttk.Label(chat_frame, text="Agent Monitor Refresh (ms):").grid(row=row, column=0, padx=20, pady=5, sticky="w")
        ttk.Entry(chat_frame, textvariable=self.agent_monitor_refresh_var, width=10).grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1
        
    def setup_extensions_tab(self, notebook):
        """Setup extensions/external tools integration tab"""
        ext_frame = ttk.Frame(notebook)
        notebook.add(ext_frame, text="🧩 Services")
        
        # Create a scrollable canvas for the whole tab
        canvas = tk.Canvas(ext_frame, bg="#1e1e1e")
        scrollbar = ttk.Scrollbar(ext_frame, orient="vertical", command=canvas.yview)
        scroll_content = ttk.Frame(canvas)
        
        scroll_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- GITHUB / SOURCE CONTROL ---
        git_group = ttk.LabelFrame(scroll_content, text="GitHub / Source Control")
        git_group.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(git_group, text="GitHub Username:").pack(padx=10, pady=(10, 2), anchor="w")
        ttk.Entry(git_group, textvariable=self.github_username_var, width=40).pack(padx=10, pady=2, anchor="w")
        
        header = ttk.Frame(git_group)
        header.pack(fill="x", padx=10, pady=(10, 2))
        ttk.Label(header, text="GitHub Token:").pack(side="left")
        import webbrowser
        link = tk.Label(header, text="(Get Token)", fg="#4a9eff", cursor="hand2", bg="#2d2d2d")
        link.pack(side="left", padx=5)
        link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/settings/tokens"))
        
        ttk.Entry(git_group, textvariable=self.github_token_var, width=50, show="*").pack(padx=10, pady=2, anchor="w")
        ttk.Label(git_group, text="Note: Token requires 'repo' and 'user' scopes.", font=("Segoe UI", 8), foreground="gray").pack(padx=10, pady=(2, 10), anchor="w")

        # VS Code Integration
        vscode_row = ttk.LabelFrame(scroll_content, text="VS Code / Cursor")
        vscode_row.pack(fill="x", padx=10, pady=5)
        
        ttk.Checkbutton(vscode_row, text="Enable Antigravity Extension Sync").pack(padx=10, pady=5, anchor="w")
        ttk.Checkbutton(vscode_row, text="Allow external inputs from VS Code extensions").pack(padx=10, pady=5, anchor="w")
        
        # Import Tools
        import_frame = ttk.Frame(vscode_row)
        import_frame.pack(fill="x", padx=10, pady=5)
        
        def do_import():
            try:
                from utils.vscode_importer import VSCodeImporter
                importer = VSCodeImporter()
                exts = importer.get_installed_extensions()
                if not exts:
                    messagebox.showinfo("Import", "No VS Code extensions found.")
                    return
                    
                # Show selection dialog
                d = tk.Toplevel(self.window)
                d.title(f"Import Extensions ({len(exts)} found)")
                d.geometry("500x400")
                
                list_frame = ttk.Frame(d)
                list_frame.pack(fill="both", expand=True, padx=10, pady=10)
                
                lb = tk.Listbox(list_frame, selectmode="multiple", bg="#2d2d30", fg="#d4d4d4")
                lb.pack(fill="both", expand=True)
                
                for e in exts:
                    lb.insert("end", e)
                    
                def save_import():
                    selected = [lb.get(i) for i in lb.curselection()]
                    if selected:
                        self.current_settings["imported_extensions"] = selected
                        messagebox.showinfo("Success", f"Imported {len(selected)} extensions (configuration only).")
                        d.destroy()
                        
                ttk.Button(d, text="Import Selected", command=save_import).pack(pady=10)
                
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {e}")
        
        ttk.Button(import_frame, text="Import VS Code Extensions", command=do_import).pack(side="left", padx=5)
        
        # Cursor Integration
        cursor_row = ttk.LabelFrame(ext_frame, text="Cursor")
        cursor_row.pack(fill="x", padx=10, pady=5)
        ttk.Checkbutton(cursor_row, text="Deep integration with Cursor rules (.cursorrules)").pack(padx=10, pady=5, anchor="w")
        
        ttk.Label(ext_frame, text="Note: These features require the Antigravity extension installed in VS Code/Cursor.", 
                 foreground="grey", wraplength=400).pack(padx=20, pady=20)

    def setup_buttons(self):
        """Setup save/cancel buttons"""
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self.save_all_settings).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_to_defaults).pack(side="left", padx=5)
    
    def save_all_settings(self):
        """Save all settings"""
        try:
            # Get current settings from app to ensure we don't lose anything (like active_providers)
            new_settings = self.app.settings.copy() if hasattr(self.app, 'settings') else self.current_settings.copy()
            
            # Validate custom endpoint URL
            try:
                from urllib.parse import urlparse
                custom_url = self.current_settings.get("custom_endpoint", "")
                if custom_url and urlparse(custom_url).scheme not in ("http", "https"):
                    messagebox.showwarning("Invalid URL", "Custom endpoint must start with http or https.")
            except Exception:
                pass

            # Update with UI values
            new_settings.update({
                "show_system_messages": self.show_system_messages_var.get(),
                "disable_auto_save_notifications": self.disable_auto_save_notifications_var.get(),
                "agent_auto_approve": self.agent_auto_approve_var.get(),
                "allowed_models": self.allowed_models_var.get(),
                "max_files": int(self.max_files_var.get()) if self.max_files_var.get().strip() else 10,
                "max_chars": int(self.max_chars_var.get()) if self.max_chars_var.get().strip() else 2000,
                "summarize_files": self.summarize_var.get(),
                "send_modified": self.send_modified_var.get(),
                "theme_preset": self.theme_var.get(),
                "auto_save": self.auto_save_var.get(),
                "auto_save_interval": int(self.auto_save_interval_var.get()) if self.auto_save_interval_var.get().strip() else 300,
                "syntax_highlighting": self.syntax_var.get(),
                "line_numbers": self.line_numbers_var.get(),
                "word_wrap": self.word_wrap_var.get(),
                "font_size": int(self.font_size_var.get()) if self.font_size_var.get().strip() else 11,
                "font_family": self.font_family_var.get(),
                "test_timeout": int(self.test_timeout_var.get()) if self.test_timeout_var.get().strip() else 30,
                "max_test_runtime": int(self.max_test_runtime_var.get()) if self.max_test_runtime_var.get().strip() else 60,
                "auto_fix": self.auto_fix_var.get(),
                "auto_fix_iterations": int(self.auto_fix_iterations_var.get()) if self.auto_fix_iterations_var.get().strip() else 3,
                "auto_reload": self.auto_reload_var.get(),
                "project_planning": self.project_planning_var.get(),
                "ask_questions": self.ask_questions_var.get(),
                "auto_generate_readme": self.auto_generate_readme_var.get(),
                "auto_generate_tests": self.auto_generate_tests_var.get(),
                "auto_approve_minor": self.auto_approve_minor_var.get(),
                "ask_for_approval": self.ask_for_approval_var.get(),
                "agent_auto_approve": not self.ask_for_approval_var.get(),
                "github_token": self._encrypt_secret(self.github_token_var.get()),
                "github_username": self.github_username_var.get(),
                "default_project_type": self.default_project_type_var.get(),
                "test_mode_no_input": self.test_mode_no_input_var.get(),
                "agent_monitor_refresh_ms": int(self.agent_monitor_refresh_var.get()) if self.agent_monitor_refresh_var.get().strip() else 5000,
                "agent_done_sound": self.agent_sound_var.get().strip(),
                "agent_done_volume": int(self.agent_volume_var.get())
            })

            # Handle device combo if it exists
            if hasattr(self, 'device_combo'):
                new_settings["audio_device_index"] = self.device_combo.current()

            # Update local current_settings
            self.current_settings = new_settings

            # Save to file
            if self.save_settings(new_settings):
                # Update app settings using app's save_settings method
                self.app.save_settings(new_settings)
                try:
                    messagebox.showinfo("Settings", "Settings saved successfully.")
                except Exception:
                    pass

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            import traceback
            traceback.print_exc()
            return

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?"):
            # Delete settings file
            if os.path.exists(SETTINGS_PATH):
                os.remove(SETTINGS_PATH)
            
            # Reload defaults
            self.current_settings = self.load_settings()
            
            # Update UI
            self.update_ui_with_settings()
            
            messagebox.showinfo("Settings Reset", "Settings have been reset to defaults.")

    def update_ui_with_settings(self):
        """Update UI with current settings"""
        # Update other settings
        self.max_files_var.set(str(self.current_settings.get("max_files", 10)))
        self.max_chars_var.set(str(self.current_settings.get("max_chars", 2000)))
        self.summarize_var.set(self.current_settings.get("summarize_files", True))
        self.send_modified_var.set(self.current_settings.get("send_modified", False))
        self.theme_var.set(self.current_settings.get("theme_preset", "Dark"))
        self.auto_save_var.set(self.current_settings.get("auto_save", True))
        self.auto_save_interval_var.set(str(self.current_settings.get("auto_save_interval", 300)))
        self.syntax_var.set(self.current_settings.get("syntax_highlighting", True))
        self.line_numbers_var.set(self.current_settings.get("line_numbers", True))
        self.word_wrap_var.set(self.current_settings.get("word_wrap", True))
        self.font_size_var.set(str(self.current_settings.get("font_size", 11)))
        self.font_family_var.set(self.current_settings.get("font_family", "Consolas"))
        self.test_timeout_var.set(str(self.current_settings.get("test_timeout", 30)))
        self.max_test_runtime_var.set(str(self.current_settings.get("max_test_runtime", 60)))
        self.auto_fix_var.set(self.current_settings.get("auto_fix", True))
        self.auto_fix_iterations_var.set(str(self.current_settings.get("auto_fix_iterations", 3)))
        self.auto_reload_var.set(self.current_settings.get("auto_reload", True))
        self.project_planning_var.set(self.current_settings.get("project_planning", True))
        self.ask_questions_var.set(self.current_settings.get("ask_questions", True))
        self.auto_generate_readme_var.set(self.current_settings.get("auto_generate_readme", True))
        self.auto_generate_tests_var.set(self.current_settings.get("auto_generate_tests", True))
        self.auto_approve_minor_var.set(self.current_settings.get("auto_approve_minor", False))
        self.ask_for_approval_var.set(not self.current_settings.get("agent_auto_approve", False))
        self.default_project_type_var.set(self.current_settings.get("default_project_type", "web"))
        self.test_mode_no_input_var.set(self.current_settings.get("test_mode_no_input", False))
        # Audio tab fields
        if hasattr(self, 'agent_sound_var'):
            self.agent_sound_var.set(self.current_settings.get("agent_done_sound", ""))
        if hasattr(self, 'agent_volume_var'):
            self.agent_volume_var.set(self.current_settings.get("agent_done_volume", 80))
        
        # Update theme preview
        self.update_theme_preview()
