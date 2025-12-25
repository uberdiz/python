"""
Main GUI for AI Dev IDE - Complete with Settings Integration - FULLY WORKING
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, Menu, messagebox, filedialog, simpledialog
import threading
import subprocess
import shutil
import json
import traceback
import webbrowser
import requests
import time

# Add module paths - FIXED
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'gui'))
sys.path.insert(0, os.path.join(current_dir, 'core'))
sys.path.insert(0, os.path.join(current_dir, 'agents'))
sys.path.insert(0, os.path.join(current_dir, 'utils'))
sys.path.insert(0, os.path.join(current_dir, 'github'))

# Settings file path
SETTINGS_PATH = os.path.join(os.path.expanduser("~"), ".ai_dev_ide_settings.json")

def load_settings():
        """Load settings from file"""
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    if "theme" not in settings:
                        settings["theme"] = {}
                # Enforce auto agent default if not set
                if "agent_auto_approve" not in settings:
                    settings["agent_auto_approve"] = True
                if "auto_image_analyze" not in settings:
                    settings["auto_image_analyze"] = True
                if "custom_providers" not in settings:
                    settings["custom_providers"] = {}
                return settings
            except:
                pass
        return {
            "api_provider": "openai",
            "api_url": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-3.5-turbo",
            "huggingface_token": "",
            "huggingface_url": "https://api-inference.huggingface.co/models/",
            "ollama_url": "http://localhost:11434",
            "ollama_model": "llama2",
            "openai_url": "https://api.openai.com/v1/chat/completions",
            "openai_token": "",
            "openai_model": "gpt-3.5-turbo",
            "github_token": "",
            "max_files": 10,
            "max_chars": 1500,
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
            "theme": {},
            "agent_auto_approve": True,
            "auto_image_analyze": True,
            "custom_providers": {}
        }

def save_settings(settings):
    """Save settings to file"""
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")

class AIDevIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Prometheus (PMT)")
        self.settings = load_settings()
        self.settings_window = None
        
        # Initialize basic attributes early to avoid AttributeError in manager inits
        self.project_path = None
        self.is_running_agent = False
        self.stop_event = threading.Event()
        self.ai_suggested_changes = {}
        self.current_test_results = {}
        self.auto_save_id = None
        
        # Initialize Security Manager
        try:
            from core.security import SecurityManager
            self.security_manager = SecurityManager(self)
        except Exception as e:
            print(f"Security Manager error: {e}")
            self.security_manager = None
            
        # Initialize Automation Manager
        try:
            from core.automation import AutomationManager
            self.automation_manager = AutomationManager(self)
            self.automation_manager.start_scheduler()
        except Exception as e:
            print(f"Automation Manager error: {e}")
            self.automation_manager = None

        # Initialize Linter
        try:
            from core.linter import Linter
            self.linter = Linter()
        except Exception as e:
            print(f"Linter error: {e}")
            self.linter = None

        # Initialize AI Manager
        try:
            from core.ai_manager import AIManager
            self.ai_manager = AIManager(self)
        except Exception as e:
            print(f"Error initializing AI Manager: {e}")
            # Fallback?

        # Initialize Planning System
        try:
            from core.planning_system import PlanningSystem
            self.planning_system = PlanningSystem(self)
        except Exception as e:
            print(f"Error initializing Planning System: {e}")
            self.planning_system = None
            
        # Initialize Plugin Manager
        try:
            from core.plugin_manager import PluginManager
            self.plugin_manager = PluginManager(self)
            self.plugin_manager.load_all_plugins()
        except Exception as e:
            print(f"Error initializing Plugin Manager: {e}")
            self.plugin_manager = None

        # Initialize theme engine
        try:
            from core.theme_engine import ThemeEngine
            self.theme_engine = ThemeEngine(self.root)
            theme_data = self.settings.get("theme", {})
            
            # Only generate from preset if the theme dictionary is completely empty
            if not theme_data:
                preset = self.settings.get("theme_preset", "Dark")
                if preset == "Light":
                    theme_data = self.theme_engine.create_light_theme()
                else:
                    theme_data = self.theme_engine.create_dark_theme()
                self.settings["theme"] = theme_data
                save_settings(self.settings) # Ensure initial theme is saved if it was missing
                
            if self.theme_engine:
                self.theme_engine.apply_theme(theme_data)
        except ImportError as e:
            print(f"Theme engine error: {e}")
            self.theme_engine = None

        # Initialize Managers (Clipboard, Hotkey)
        try:
            from core.clipboard_manager import ClipboardManager
            self.clipboard_manager = ClipboardManager(self)
        except Exception as e:
            print(f"Clipboard manager init error: {e}")
            self.clipboard_manager = None
            
        try:
            from core.hotkey_manager import HotkeyManager
            self.hotkey_manager = HotkeyManager(self, self.on_global_hotkey)
            self.hotkey_manager.start()
        except Exception as e:
            print(f"Hotkey manager init error: {e}")
            self.hotkey_manager = None
        
        # Initialize Sound Settings
        from utils import get_resource_path
        default_sound = get_resource_path(os.path.join("DoneSound", "smooth-completed-notify-starting-alert-274739.mp3"))
        if not self.settings.get("agent_done_sound"):
            self.settings["agent_done_sound"] = default_sound
            save_settings(self.settings)
        
        # Initialize GUI components
        self.project_tree = None
        self.editor_tabs = None
        self.ai_panel = None
        self.output_panels = None
        
        # Setup GUI
        try:
            from gui.layout_manager import LayoutManager
            self.layout_manager = LayoutManager(self)
        except ImportError:
            self.layout_manager = None
            
        self.setup_gui()
        
        # Setup auto-save if enabled
        if self.settings.get("auto_save", True):
            self.setup_auto_save()
    
    def setup_gui(self):
        """Setup the main GUI window"""
        self.root.title("AI Dev IDE - Advanced v2.0")
        self.root.geometry("1400x900")
        
        if self.theme_engine:
            self.root.configure(bg=self.theme_engine.color_map["window_bg"])
        else:
            self.root.configure(bg="#1e1e1e")
            
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Global Keybinds
        self.root.bind("<Control-l>", self.focus_ai_input)
        self.root.bind("<Control-plus>", lambda e: (self.zoom_in(), "break"))
        self.root.bind("<Control-equal>", lambda e: (self.zoom_in(), "break"))
        self.root.bind("<Control-KP_Add>", lambda e: (self.zoom_in(), "break"))
        self.root.bind("<Control-minus>", lambda e: (self.zoom_out(), "break"))
        self.root.bind("<Control-KP_Subtract>", lambda e: (self.zoom_out(), "break"))
        self.root.bind("<Control-0>", lambda e: (self.reset_zoom(), "break"))
        self.root.bind("<Control-KP_0>", lambda e: (self.reset_zoom(), "break"))
        
        # Create main frames
        self.setup_menu()
        self.setup_toolbar()
        self.setup_status_bar()
        self.setup_main_panes()
        # setup_bottom_panes integrated into setup_main_panes
        if self.layout_manager:
            try:
                self.layout_manager.load_layout()
            except Exception:
                pass
            try:
                for name, v in self.sidebar_views.items():
                    if name != "explorer" and not getattr(v, 'is_undocked', False):
                        v.pack_forget()
                if "explorer" in self.sidebar_views:
                    self.sidebar_views["explorer"].pack(in_=self.sidebar_content, fill="both", expand=True)
            except Exception:
                pass

        self.root.bind("<<AgentDone>>", lambda e: self.play_agent_done_sound())
        
        # Initial status
        self.clear_progress()
        try:
            self._apply_zoom(int(self.settings.get("zoom_level", 100)))
        except Exception:
            pass
            
        # Restore last project
        self.root.after(100, self.restore_last_project)
            
        # Bind resize for responsive layout
        self.root.bind("<Configure>", self.on_window_resize)

    def on_window_resize(self, event):
        """Handle responsive layout changes on window resize"""
        # Only handle root window resize
        if event.widget != self.root:
            return
            
        width = event.width
        # Adjust sidebar width based on screen size
        if width < 800:
            # Compact mode
            if hasattr(self, 'sidebar_frame'):
                self.sidebar_frame.configure(width=150)
            if hasattr(self, 'ai_panel') and self.ai_panel:
                # Adjust AI panel internal elements if needed
                pass
        elif width < 1200:
            # Medium mode
            if hasattr(self, 'sidebar_frame'):
                self.sidebar_frame.configure(width=200)
        else:
            # Wide mode
            if hasattr(self, 'sidebar_frame'):
                self.sidebar_frame.configure(width=300)
        
        # Ensure output panels and editor are visible
        if hasattr(self, 'main_panes'):
            # Trigger layout refresh if necessary
            pass

    def focus_ai_input(self, event=None):
        """Focus the AI chat input"""
        if self.ai_panel and self.ai_panel.winfo_ismapped():
            self.ai_panel.text_input.focus_set()
            return "break"
        # If hidden, show it
        if not self.ai_panel.winfo_ismapped():
            self.toggle_ai_panel()
            # Wait for map
            self.root.update_idletasks()
            if self.ai_panel:
                self.ai_panel.text_input.focus_set()
            return "break"

    def setup_menu(self):
        """Setup the top menu"""
        menubar = Menu(self.root, bg="#252526", fg="#cccccc")
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0, bg="#252526", fg="#cccccc")
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_existing_project)
        file_menu.add_separator()
        file_menu.add_command(label="New File", command=self.create_new_file)
        file_menu.add_command(label="Save File", command=self.save_current_file)
        file_menu.add_command(label="Save All", command=self.save_all_open_files)
        file_menu.add_separator()
        file_menu.add_command(label="Export Project", command=self.export_project)
        file_menu.add_command(label="Push to GitHub", command=self.push_to_github)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        
        # Edit menu
        edit_menu = Menu(menubar, tearoff=0, bg="#252526", fg="#cccccc")
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=self.cut)
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=self.copy)
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=self.paste)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find", accelerator="Ctrl+F", command=self.find)
        edit_menu.add_command(label="Replace", accelerator="Ctrl+H", command=self.replace)
        
        # AI menu
        self.ai_menu = Menu(menubar, tearoff=0, bg="#252526", fg="#cccccc")
        menubar.add_cascade(label="AI", menu=self.ai_menu)
        self.ai_menu.add_command(label="Open AI Chat", command=lambda: self.focus_ai_input())
        self.ai_menu.add_separator()
        self.ai_menu.add_command(label="Agent Manager", command=lambda: self.open_agent_manager())


        # Tools menu
        tools_menu = Menu(menubar, tearoff=0, bg="#252526", fg="#cccccc")
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="⚙️ Settings", command=self.open_settings)
        tools_menu.add_command(label="▶️ Run Script", command=self.save_and_run)
        tools_menu.add_command(label="🧪 Run Tests", command=self.run_tests_and_show)
        tools_menu.add_command(label="🔁 Test & Fix Loop", command=self.test_and_fix_loop)
        tools_menu.add_command(label="🐛 Debug Script", command=self.debug_script)
        tools_menu.add_separator()
        tools_menu.add_command(label="📦 Install Requirements", command=self.install_requirements)
        tools_menu.add_command(label="🔧 Format Code", command=self.format_code)
        tools_menu.add_command(label="✓ Check Syntax", command=self.check_syntax)
        tools_menu.add_command(label="📊 Test Coverage", command=self.run_test_coverage)
        tools_menu.add_command(label="📈 Generate Coverage Report", command=self.generate_coverage_report)
        tools_menu.add_separator()
        tools_menu.add_command(label="🧹 Cleanup Repository", command=self.cleanup_repo)
        tools_menu.add_command(label="📂 Restructure Project", command=self.restructure_project)
        tools_menu.add_separator()
        
        # View menu
        view_menu = Menu(menubar, tearoff=0, bg="#252526", fg="#cccccc")
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Project Tree", command=self.toggle_project_tree)
        view_menu.add_command(label="Toggle AI Panel", command=self.toggle_ai_panel)
        view_menu.add_command(label="Toggle Output Panels", command=self.toggle_output_panels)
        
        # Windows menu
        windows_menu = Menu(menubar, tearoff=0, bg="#252526", fg="#cccccc")
        menubar.add_cascade(label="Windows", menu=windows_menu)
        windows_menu.add_command(label="🗂️ Explorer", command=lambda: self.switch_sidebar("explorer"))
        windows_menu.add_command(label="🔍 Search", command=lambda: self.switch_sidebar("search"))
        windows_menu.add_command(label="🌿 Git", command=lambda: self.switch_sidebar("git"))
        # Removed Plan view from Windows menu; planning handled in AI Chat
        windows_menu.add_command(label="🤖 Agents", command=lambda: self.switch_sidebar("agents"))
        windows_menu.add_command(label="💬 AI Chat", command=lambda: self.switch_sidebar("ai"))
        windows_menu.add_separator()
        windows_menu.add_command(label="📊 Agent Monitor", command=self.open_agent_monitor)
        windows_menu.add_command(label="🔄 Reset Layout", command=self.reset_layout)
        view_menu.add_separator()
        view_menu.add_command(label="Zoom In", accelerator="Ctrl+Plus", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out", accelerator="Ctrl+Minus", command=self.zoom_out)
        view_menu.add_command(label="Reset Zoom", accelerator="Ctrl+0", command=self.reset_zoom)
        
        # Help menu
        help_menu = Menu(menubar, tearoff=0, bg="#252526", fg="#cccccc")
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.open_documentation)
        help_menu.add_command(label="Get OpenAI API Key", command=self.open_openai_key)
        help_menu.add_command(label="About", command=self.show_about)
        
    def summarize_project_ui(self):
        """Generate project summary"""
        if not self.project_path:
            self.show_message("Error", "No project open")
            return
            
        self.update_progress("Generating summary...", True)
        
        def worker():
            try:
                summary = self.ai_manager.summarize_project(self.project_path)
                
                self.root.after(0, lambda: self.show_summary_in_panel(summary))
                self.update_progress("Summary generated", False)
            except Exception as e:
                self.log_ai(f"Summary Error: {e}")
                
        threading.Thread(target=worker, daemon=True).start()

    def show_summary_in_panel(self, summary):
        """Show summary in AI output"""
        self.log_ai(summary)
        # Also open in new tab if possible?
        # For now just log it
        self.show_message("Summary Ready", "Project summary generated in Output panel.")
        # Summary is shown in Output panel; no AI menu updates required

    def translate_script_ui(self):
        """Open translation dialog and process"""
        current_file = self.editor_tabs.get_current_file() if self.editor_tabs else None
        if not current_file:
            self.show_message("Error", "No file open to translate.")
            return
            
        from gui.translation_dialog import ask_translation
        result = ask_translation(self.root, os.path.basename(current_file))
        
        if result:
            target_lang = result["language"]
            make_copy = result["make_copy"]
            
            self.update_progress(f"Translating to {target_lang}...", True)
            
            def worker():
                try:
                    # Get file content
                    with open(current_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Call AI for translation
                    prompt = f"Translate the following code from its current language to {target_lang}. Maintain logic and structure. Only return the code.\n\n```\n{content}\n```"
                    
                    # Get currently active AI settings
                    provider = self.ai_manager.get_active_provider() if hasattr(self, 'ai_manager') else self.settings.get("api_provider", "openai")
                    api_url, model, token = self.get_ai_settings(provider)
                    
                    translated_code = self.ai_manager.generate_response(prompt)
                    
                    # Clean up markdown if present
                    if "```" in translated_code:
                        import re
                        match = re.search(r'```(?:\w+)?\n(.*?)\n```', translated_code, re.DOTALL)
                        if match:
                            translated_code = match.group(1)
                    
                    def save_and_open():
                        if make_copy:
                            base, ext = os.path.splitext(current_file)
                            # Simple extension mapping
                            ext_map = {
                                "Python": ".py", "JavaScript": ".js", "C++": ".cpp", 
                                "C#": ".cs", "Lua": ".lua", "Go": ".go", 
                                "Java": ".java", "Rust": ".rs"
                            }
                            new_ext = ext_map.get(target_lang, ext)
                            new_path = f"{base}_translated{new_ext}"
                        else:
                            new_path = current_file
                            
                        with open(new_path, 'w', encoding='utf-8') as f:
                            f.write(translated_code)
                            
                        self.editor_tabs.open_file(new_path)
                        self.log_ai(f"✅ Translated to {target_lang}: {os.path.basename(new_path)}")
                        self.update_progress("Translation complete", False)
                        
                    self.root.after(0, save_and_open)
                    
                except Exception as e:
                    self.log_ai(f"Translation Error: {e}")
                    self.update_progress("Translation failed", False)
            
            threading.Thread(target=worker, daemon=True).start()
    
    def setup_toolbar(self):
        """Setup toolbar with run/test buttons"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill="x", padx=5, pady=2)
        
        # Run buttons
        ttk.Button(toolbar, text="▶ Run Script", 
                  command=self.save_and_run, width=12).pack(side="left", padx=2)
        
        ttk.Button(toolbar, text="⏹ Stop Script", 
                  command=self.stop_current_script, width=12).pack(side="left", padx=2)
        
        # Unified Auto Test & Fix button
        self.auto_test_fix_button = ttk.Button(toolbar, text="🔄 Auto Test & Fix", 
                                              command=self.test_and_fix_loop, width=20)
        self.auto_test_fix_button.pack(side="left", padx=2)
        
        # Separator
        ttk.Separator(toolbar, orient="vertical").pack(side="left", padx=10, fill="y")
        
        # AI buttons
        ttk.Button(toolbar, text="📝 Review Code", 
                  command=self.review_code, width=12).pack(side="left", padx=2)
        ttk.Button(toolbar, text="⚡ Optimize", 
                  command=self.optimize_code, width=12).pack(side="left", padx=2)
                  
        # --- Right Side Status Indicators ---
        info_frame = ttk.Frame(toolbar)
        info_frame.pack(side="right", padx=5)
        
        # Group Indicator
        self.group_label = ttk.Label(info_frame, text="Group: Default", font=("Segoe UI", 9))
        self.group_label.pack(side="left", padx=5)
        
        ttk.Separator(info_frame, orient="vertical").pack(side="left", padx=5, fill="y")
        
        # Model Indicator
        self.model_label = ttk.Label(info_frame, text="Model: --", font=("Segoe UI", 9))
        self.model_label.pack(side="left", padx=5)
        
        ttk.Separator(info_frame, orient="vertical").pack(side="left", padx=5, fill="y")

        # Progress Bar (small)
        self.progress_var = tk.DoubleVar()
        self.top_progress = ttk.Progressbar(info_frame, variable=self.progress_var, length=100, mode='determinate')
        self.top_progress.pack(side="left", padx=5)
        
        # Start status loop
        self.update_status_loop()

    def update_status_loop(self):
        """Update status indicators periodically"""
        try:
            # Update Group
            group = self.settings.get("last_agent_group", "Default")
            if hasattr(self, 'group_label'):
                self.group_label.config(text=f"Group: {group}")
            
            # Update Model (based on active agent or default)
            model = self.settings.get("model", "")
            # If we have an active agent in AI Panel, show its model
            if hasattr(self, 'ai_panel') and self.ai_panel:
                try:
                    if hasattr(self.ai_panel, 'find_best_agent') and hasattr(self.ai_panel, 'current_mode'):
                        mode = self.ai_panel.current_mode.get()
                        agent_name = self.ai_panel.find_best_agent(mode)
                        if hasattr(self, 'agent_manager') and self.agent_manager and self.agent_manager.orchestrator:
                            agent = self.agent_manager.orchestrator.get_agent(agent_name)
                            if agent:
                                model = agent.model_name
                except: pass
            
            if len(model) > 20: model = model[:17] + "..."
            if hasattr(self, 'model_label'):
                self.model_label.config(text=f"Model: {model}")
            
            # Update Progress Bar (if active task)
            # This is a simple visual indicator for now
            if hasattr(self, 'top_progress'):
                # If we have a progress manager or task running
                pass
            
        except Exception:
            pass
            
        if hasattr(self, 'root'):
            self.root.after(1000, self.update_status_loop)

    
    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill="x", padx=6, pady=(6,4))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side="left", fill="x", expand=True)
        
        # AI Provider indicator
        provider = self.ai_manager.get_active_provider() if hasattr(self, 'ai_manager') else self.settings.get("api_provider", "openai")
        _, model, _ = self.get_ai_settings(provider)
        self.provider_label = ttk.Label(self.status_frame, text=f"🤖 {provider.upper()}: {model[:15]}")
        self.provider_label.pack(side="left", padx=10)
        
        # Line and column indicator
        self.position_label = ttk.Label(self.status_frame, text="Ln 1, Col 1")
        self.position_label.pack(side="left", padx=20)
        
        # File indicator
        self.file_label = ttk.Label(self.status_frame, text="No file")
        self.file_label.pack(side="left", padx=20)
        
        self.progress_bar = ttk.Progressbar(self.status_frame, mode='indeterminate', length=200)
        self.progress_bar.pack(side="right", padx=(6,0))
        
        self.progress_text = ttk.Label(self.status_frame, text="")
        self.progress_text.pack(side="right", padx=(0,6))
    
    def setup_main_panes(self):
        """Setup the main panes with VSCode-like layout"""
        # Main container (Horizontal PanedWindow)
        self.main_pane = ttk.Panedwindow(self.root, orient="horizontal")
        self.main_pane.pack(fill="both", expand=True, padx=0, pady=0)
        
        # 1. Activity Bar (Leftmost, fixed width)
        try:
            from gui.activity_bar import ActivityBar
            # Activity bar usually stays outside the resizable sidebar pane or is part of it
            # We'll put it in its own frame to keep it fixed width while sidebar resizes
            act_container = ttk.Frame(self.main_pane)
            self.main_pane.add(act_container, weight=0)
            
            self.activity_bar = ActivityBar(act_container, self)
            self.activity_bar.pack(side="left", fill="y")
        except ImportError as e:
            print(f"Activity Bar error: {e}")
            self.activity_bar = None
            
        # 2. Sidebar (Left, resizable)
        self.sidebar_frame = ttk.Frame(self.main_pane, width=250)
        self.main_pane.add(self.sidebar_frame, weight=1)
        
        # Sidebar Content Container
        self.sidebar_content = ttk.Frame(self.sidebar_frame)
        self.sidebar_content.pack(fill="both", expand=True)
        
        # Initialize different sidebar views
        self.sidebar_views = {}
        
        # Project Tree (Explorer)
        try:
            from gui.project_tree import ProjectTree
            
            if self.layout_manager:
                explorer_draggable, explorer_content = self.layout_manager.create_draggable_container(
                    self.sidebar_content, "EXPLORER")
                self.project_tree = ProjectTree(explorer_content, self)
                self.project_tree.pack(fill="both", expand=True)
                self.sidebar_views["explorer"] = explorer_draggable
                explorer_draggable.pack(fill="both", expand=True)
            else:
                self.project_tree = ProjectTree(self.sidebar_content, self)
                self.sidebar_views["explorer"] = self.project_tree
                self.project_tree.pack(fill="both", expand=True)
        except ImportError as e:
            self.sidebar_views["explorer"] = ttk.Label(self.sidebar_content, text=f"Error: {e}")
            
        
        # AI Assistant View
        try:
            from gui.ai_panel import AIPanel
            
            if self.layout_manager:
                ai_draggable, ai_content = self.layout_manager.create_draggable_container(
                    self.sidebar_content, "AI ASSISTANT")
                self.ai_panel = AIPanel(ai_content, self)
                self.ai_panel.pack(fill="both", expand=True)
                self.sidebar_views["ai"] = ai_draggable
            else:
                self.ai_panel = AIPanel(self.sidebar_content, self)
                self.sidebar_views["ai"] = self.ai_panel
                self.ai_panel.pack(fill="both", expand=True)
        except ImportError as e:
            self.sidebar_views["ai"] = ttk.Label(self.sidebar_content, text=f"AI Error: {e}")

        # Content area (Editor + Panels)
        content_area = ttk.Panedwindow(self.main_pane, orient="vertical")
        self.main_pane.add(content_area, weight=4)
        
        # Editor Area
        editor_frame = ttk.Frame(content_area)
        content_area.add(editor_frame, weight=3)
        
        try:
            from gui.editor_tabs import EditorTabs
            self.editor_tabs = EditorTabs(editor_frame, self)
            self.editor_tabs.pack(fill="both", expand=True)
        except ImportError as e:
            ttk.Label(editor_frame, text=f"Editor Error: {e}").pack()
            
        # Output Panels (Bottom)
        self.bottom_panel_frame = ttk.Frame(content_area, height=200)
        content_area.add(self.bottom_panel_frame, weight=1)
        
        try:
            from gui.output_panels import BottomPanel
            self.output_panels = BottomPanel(self.bottom_panel_frame, self)
        except ImportError as e:
            print(f"BottomPanel error: {e}")
            pass
            
        try:
            from gui.git_panel import GitPanel
            if self.layout_manager:
                git_draggable, git_content = self.layout_manager.create_draggable_container(
                    self.sidebar_content, "GIT")
                self.git_panel = GitPanel(git_content, self)
                # GitPanel is a controller, it packs its notebook internally. No .pack() here.
                self.sidebar_views["git"] = git_draggable
            else:
                self.git_panel = GitPanel(self.sidebar_views["git"], self)
        except ImportError as e:
            if "git" in self.sidebar_views:
                ttk.Label(self.sidebar_views["git"], text=f"Git Error: {e}").pack()
            else:
                print(f"Git Error: {e}")
            
        # Search View
        try:
            from gui.search_panel import SearchPanel
            if self.layout_manager:
                search_draggable, search_content = self.layout_manager.create_draggable_container(
                    self.sidebar_content, "SEARCH")
                self.search_panel = SearchPanel(search_content, self)
                self.search_panel.pack(fill="both", expand=True)
                self.sidebar_views["search"] = search_draggable
            else:
                self.search_panel = SearchPanel(self.sidebar_views["search"], self)
        except ImportError as e:
            if "search" in self.sidebar_views:
                ttk.Label(self.sidebar_views["search"], text=f"Search Error: {e}").pack()
            else:
                print(f"Search Error: {e}")
            
        
        # 5) AI Chat View        
        # Set initial active view
        if self.activity_bar:
            self.activity_bar.set_active("explorer")
        # Ensure only Explorer shows in left sidebar at startup; keep others hidden
        try:
            for name, v in self.sidebar_views.items():
                if name != "explorer" and not getattr(v, 'is_undocked', False) and getattr(v, 'dock_parent', None) is self.sidebar_content:
                    v.pack_forget()
            # Make sure Explorer is visible
            if "explorer" in self.sidebar_views:
                self.sidebar_views["explorer"].pack(in_=self.sidebar_content, fill="both", expand=True)
        except Exception:
            pass
            
        # 6) Agent Manager View
        self.sidebar_views["agents"] = ttk.Frame(self.sidebar_frame)
        # Agent Manager Panel
        try:
            from gui.agent_manager_panel import AgentManagerPanel
            if self.layout_manager:
                agent_draggable, agent_content = self.layout_manager.create_draggable_container(
                    self.sidebar_content, "AGENTS")
                self.agent_manager = AgentManagerPanel(agent_content, self)
                self.agent_manager.pack(fill="both", expand=True) # MISSING PACK
                self.sidebar_views["agents"] = agent_draggable
            else:
                self.agent_manager = AgentManagerPanel(self.sidebar_views["agents"], self)
        except ImportError as e:
            msg = f"Agent Manager Error: {e}"
            if "agents" in self.sidebar_views:
                ttk.Label(self.sidebar_views["agents"], text=msg).pack()
            else:
                print(msg)

        # 7) Planning Panel
        try:
            from gui.planning_panel import PlanningPanel
            if self.layout_manager:
                plan_draggable, plan_content = self.layout_manager.create_draggable_container(
                    self.sidebar_content, "PLAN")
                self.planning_panel = PlanningPanel(plan_content, self)
                self.planning_panel.pack(fill="both", expand=True)
                self.sidebar_views["plan"] = plan_draggable
            else:
                self.planning_panel = PlanningPanel(self.sidebar_content, self)
                self.sidebar_views["plan"] = self.planning_panel
        except ImportError as e:
            print(f"Planning Panel error: {e}")

    def switch_sidebar(self, view_name):
        """Switch sidebar content or focus undocked window"""
        if view_name not in self.sidebar_views:
            return
            
        view = self.sidebar_views[view_name]
        
        # If undocked, just lift the window
        if hasattr(view, 'is_undocked') and view.is_undocked:
            if hasattr(view, 'floating_win'):
                view.floating_win.deiconify()
                view.floating_win.lift()
                view.floating_win.focus_set()
            return

        # If the target is docked inside a Notebook, select its tab
        dock_parent = getattr(view, 'dock_parent', self.sidebar_content)
        try:
            from tkinter import ttk as _ttk
            if isinstance(dock_parent, _ttk.Notebook):
                dock_parent.select(view)
                dock_parent.pack(in_=self.sidebar_content, fill="both", expand=True)
                return
        except Exception:
            pass

        # Fallback: only one visible in left sidebar
        for vname, v in self.sidebar_views.items():
            if not getattr(v, 'is_undocked', False) and getattr(v, 'dock_parent', None) is self.sidebar_content:
                v.pack_forget()
        view.pack(in_=self.sidebar_content, fill="both", expand=True)
    
    def setup_auto_save(self):
        """Setup auto-save timer"""
        interval = self.settings.get("auto_save_interval", 300) * 1000
        
        def auto_save():
            if self.project_path and self.editor_tabs:
                saved = self.save_all_open_files()
                if saved and not self.settings.get("disable_auto_save_notifications", False):
                    self.log_ai(f"💾 Auto-saved {len(saved)} files")
            
            # Schedule next auto-save
            self.auto_save_id = self.root.after(interval, auto_save)
        
        # Start auto-save
        self.auto_save_id = self.root.after(interval, auto_save)
    
    def open_settings(self):
        """Open settings window"""
        try:
            from gui.settings_window import SettingsWindow
            self.settings_window = SettingsWindow(self.root, self)
        except ImportError as e:
            messagebox.showerror("Error", f"Cannot open settings: {e}")

    def open_account_settings(self):
        """Open the AI Providers window"""
        try:
            from gui.providers_window import ProvidersWindow
            self.providers_window = ProvidersWindow(self.root, self)
        except ImportError as e:
            messagebox.showerror("Error", f"Cannot open providers: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            
    def open_agent_monitor(self):
        """Open the Agent Monitor window"""
        try:
            if hasattr(self, 'agent_manager') and hasattr(self.agent_manager, 'orchestrator'):
                from gui.agent_monitor import AgentMonitor
                monitor = AgentMonitor(self.root, self.agent_manager.orchestrator)
                self.agent_manager.orchestrator.agent_monitor = monitor
            else:
                messagebox.showinfo("No Agents", "Open Agent Manager first and create some agents.")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open Agent Monitor: {e}")
            
    def reset_layout(self):
        """Reset window layout to defaults"""
        try:
            from gui.layout_manager import LayoutManager
            lm = LayoutManager(self, self.root)
            lm.layout_config = lm.get_default_layout()
            lm.save_layout()
            messagebox.showinfo("Layout Reset", "Layout reset to defaults. Restart the app to apply.")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot reset layout: {e}")
            
    def open_theme_editor(self):
        """Open the Advanced Theme Editor"""
        try:
            from gui.theme_editor import ThemeEditor
            ThemeEditor(self.root, self)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open Theme Editor: {e}")
    
    def save_settings(self, new_settings):
        """Save settings"""
        # Check if theme preset changed
        old_preset = self.settings.get("theme_preset", "Dark")
        new_preset = new_settings.get("theme_preset", "Dark")
        
        self.settings.update(new_settings)
        
        if old_preset != new_preset:
            if new_preset == "Light":
                self.settings["theme"] = self.theme_engine.create_light_theme()
            elif new_preset == "Nordic":
                self.settings["theme"] = self.theme_engine.create_nordic_theme()
            elif new_preset == "Cyberpunk":
                self.settings["theme"] = self.theme_engine.create_cyberpunk_theme()
            elif new_preset == "Nebula":
                self.settings["theme"] = self.theme_engine.create_nebula_theme()
            else:
                # Check custom themes
                custom_themes = self.settings.get("custom_themes", {})
                if new_preset in custom_themes:
                    self.settings["theme"] = custom_themes[new_preset]
                else:
                    self.settings["theme"] = self.theme_engine.create_dark_theme()
        
        save_settings(self.settings)
        
        # Update status bar with correct model based on provider
        provider = self.ai_manager.get_active_provider() if hasattr(self, 'ai_manager') else self.settings.get("api_provider", "openai")
        if provider == "openai":
            model = self.settings.get("openai_model", "gpt-3.5-turbo")
        elif provider == "huggingface":
            model = self.settings.get("model", "gpt2")
        elif provider == "ollama":
            model = self.settings.get("ollama_model", "llama2")
        elif provider == "custom":
            model = self.settings.get("custom_model", "model")
        else:
            model = self.settings.get("model", "gpt-3.5-turbo")
        
        self.provider_label.config(text=f"🤖 {provider.upper()}: {model[:15]}")
        
        # Apply theme
        self.apply_theme_to_all()
        
        # Restart auto-save if needed
        if self.auto_save_id:
            self.root.after_cancel(self.auto_save_id)
            self.auto_save_id = None
        
        if self.settings.get("auto_save", True):
            self.setup_auto_save()
    
    def apply_theme_to_all(self, preset_name=None):
        """Apply theme to all components"""
        if not self.theme_engine:
            return
            
        if not preset_name:
            preset_name = self.settings.get("theme_preset", "Dark")
            
        # Standard Presets
        if preset_name == "Light":
            theme_data = self.theme_engine.create_light_theme()
        elif preset_name == "Nordic":
            theme_data = self.theme_engine.create_nordic_theme()
        elif preset_name == "Cyberpunk":
            theme_data = self.theme_engine.create_cyberpunk_theme()
        elif preset_name == "Nebula":
            theme_data = self.theme_engine.create_nebula_theme()
        elif preset_name == "Blue":
            # Attempt to use create_blue_theme if defined in engine, or fallback
            theme_data = getattr(self.theme_engine, "create_blue_theme", self.theme_engine.create_dark_theme)()
        # Add more mappings as needed or use a dictionary
        else:
            # Check custom themes in settings
            custom_themes = self.settings.get("custom_themes", {})
            if preset_name in custom_themes:
                theme_data = custom_themes[preset_name]
            else:
                # Default to dark
                theme_data = self.theme_engine.create_dark_theme()
            
        self.theme_engine.apply_theme(theme_data)
        
        # Update all major components
        if self.editor_tabs:
            self.editor_tabs.apply_theme_to_all(self.theme_engine.color_map)
        if self.ai_panel:
            self.ai_panel.apply_theme(self.theme_engine.color_map)
        if self.project_tree:
            self.project_tree.apply_theme(self.theme_engine.color_map)
        if self.output_panels:
            self.output_panels.apply_theme(self.theme_engine.color_map)
            
        # Global style refresh
        self.theme_engine.setup_styles()
    
    def open_chat_window(self):
        """Open dedicated chat window"""
        if self.ai_panel:
            # Focus on AI panel and input field
            self.ai_panel.message_entry.focus_set()
    
    def toggle_project_tree(self):
        """Toggle project tree visibility"""
        if "explorer" in self.sidebar_views:
            view = self.sidebar_views["explorer"]
            if view.winfo_ismapped():
                view.pack_forget()
            else:
                self.switch_sidebar("explorer")
    
    def toggle_ai_panel(self):
        """Toggle AI panel visibility"""
        if "ai" in self.sidebar_views:
            view = self.sidebar_views["ai"]
            if view.winfo_ismapped():
                view.pack_forget()
            else:
                self.switch_sidebar("ai")
    
    def toggle_output_panels(self):
        """Toggle output panels visibility"""
        if not hasattr(self, 'bottom_panel_frame'):
            return
            
        if self.bottom_panel_frame.winfo_ismapped():
            # Hide
            if hasattr(self, 'content_area'):
                self.content_area.forget(self.bottom_panel_frame)
            else:
                # Fallback if content_area ref missing
                self.bottom_panel_frame.pack_forget() 
        else:
            # Show
            if hasattr(self, 'content_area'):
                self.content_area.add(self.bottom_panel_frame, weight=1)
    
    def zoom_in(self):
        """Zoom in all UI elements proportionally"""
        level = int(self.settings.get("zoom_level", 100))
        level = min(level + 10, 200)
        self._apply_zoom(level)
    
    def zoom_out(self):
        """Zoom out all UI elements proportionally"""
        level = int(self.settings.get("zoom_level", 100))
        level = max(level - 10, 70)
        self._apply_zoom(level)
    
    def reset_zoom(self):
        """Reset zoom level"""
        self._apply_zoom(100)

    def _apply_zoom(self, percent):
        try:
            import tkinter.font as tkfont
            self.settings["zoom_level"] = percent
            default = tkfont.nametofont("TkDefaultFont")
            textf = tkfont.nametofont("TkTextFont")
            fixed = tkfont.nametofont("TkFixedFont")
            base = int(self.settings.get("font_size", 11))
            size = max(8, min(int(base * percent / 100), 24))
            for f in (default, textf, fixed):
                f.configure(size=size)
            if self.output_panels:
                try:
                    self.output_panels.set_font_size(size)
                except Exception:
                    pass
            self.status_label.configure(text=f"Zoom {percent}%")
            save_settings(self.settings)
        except Exception:
            pass
    
    def run_test_coverage(self):
        """Run test coverage report"""
        if not self.project_path:
            self.show_message("No Project", "Please open a project first.")
            return
        
        self.update_progress("Running test coverage...", True)
        
        def worker():
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", "--cov=.", "--cov-report=term"],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if self.output_panels:
                    self.output_panels.clear_script_output()
                    self.log_script("Test Coverage Report:\n")
                    self.log_script(result.stdout)
                    if result.stderr:
                        self.log_script(f"\nErrors:\n{result.stderr}")
                
                self.update_progress("Coverage report generated", False)
            except Exception as e:
                self.update_progress("Coverage error", False)
                self.log_script(f"Error running coverage: {e}")
        
        threading.Thread(target=worker, daemon=True).start()
    
    def generate_coverage_report(self):
        """Generate HTML coverage report"""
        if not self.project_path:
            self.show_message("No Project", "Please open a project first.")
            return
        
        self.update_progress("Generating coverage report...", True)
        
        def worker():
            try:
                # Run coverage
                result = subprocess.run(
                    ["python", "-m", "pytest", "--cov=.", "--cov-report=html"],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                # Open the report
                report_path = os.path.join(self.project_path, "htmlcov", "index.html")
                if os.path.exists(report_path):
                    webbrowser.open(f"file://{report_path}")
                    self.log_script(f"📊 Coverage report generated: {report_path}")
                else:
                    self.log_script("Failed to generate coverage report")
                
                self.update_progress("Coverage report ready", False)
            except Exception as e:
                self.update_progress("Coverage error", False)
                self.log_script(f"Error: {e}")
        
        threading.Thread(target=worker, daemon=True).start()
    
    def create_new_file(self):
        """Create a new file"""
        if not self.project_path:
            self.show_message("No Project", "Please open or create a project first.")
            return
        
        file_name = simpledialog.askstring("New File", "Enter file name (e.g., new_file.py):")
        if not file_name:
            return
        
        full_path = os.path.join(self.project_path, file_name)
        
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write('# New file created with AI Dev IDE\n')
            
            if self.project_tree:
                self.project_tree.refresh()
            
            if self.editor_tabs:
                self.editor_tabs.open_file(full_path)
            
            self.log_ai(f"Created new file: {file_name}")
        except Exception as e:
            self.show_message("Error", f"Failed to create file: {e}")
    
    def save_current_file(self):
        """Save current file"""
        if self.editor_tabs:
            self.editor_tabs.save_current_file()
    
    def save_all_open_files(self):
        """Save all open files"""
        if self.editor_tabs:
            return self.editor_tabs.save_all_files(self.project_path)
        return []
    
    def undo(self):
        if self.editor_tabs:
            self.editor_tabs.undo()
    
    def redo(self):
        if self.editor_tabs:
            self.editor_tabs.redo()
    
    def cut(self):
        if self.editor_tabs:
            self.editor_tabs.cut()
    
    def copy(self):
        if self.editor_tabs:
            self.editor_tabs.copy()
    
    def paste(self):
        if self.editor_tabs:
            self.editor_tabs.paste()
    
    def find(self):
        if self.editor_tabs:
            self.editor_tabs.find_text()
    
    def replace(self):
        if self.editor_tabs:
            self.editor_tabs.replace_text()
    
    def format_code(self):
        if self.editor_tabs:
            self.editor_tabs.format_code()
    
    def check_syntax(self):
        if self.editor_tabs:
            self.editor_tabs.check_syntax()
    
    def new_project(self):
        """Create a new project"""
        folder = filedialog.askdirectory(title="Select Folder for New Project")
        if not folder:
            return
        
        project_name = simpledialog.askstring("Project Name", "Enter project name:")
        if not project_name:
            project_name = "new_project"
        
        self.project_path = os.path.join(folder, project_name)
        os.makedirs(self.project_path, exist_ok=True)
        
        # Create project structure
        project_files = {
            "README.md": f"# {project_name}\n\nCreated with AI Dev IDE\n",
            "main.py": '#!/usr/bin/env python3\n"""Main entry point"""\n\nprint("Hello from AI Dev IDE")\n',
            "requirements.txt": "# Project dependencies\n\n",
            "test_main.py": '#!/usr/bin/env python3\n"""Tests"""\n\ndef test_example():\n    """Example test"""\n    assert True\n',
            ".gitignore": "# Python\n__pycache__/\n*.py[cod]\n*$py.class\n\n# Virtual Environment\nvenv/\nenv/\n",
            "PORTFOLIO.md": f"# {project_name} - Portfolio\n\n## Project Description\n\nAI-generated project.\n"
        }
        
        for filename, content in project_files.items():
            filepath = os.path.join(self.project_path, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        if self.project_tree:
            self.project_tree.load_project(self.project_path)
        
        main_path = os.path.join(self.project_path, "main.py")
        if self.editor_tabs:
            self.editor_tabs.open_file(main_path)
        
        self.log_ai(f"✅ Created new project: {project_name}")
    
    def open_existing_project(self):
        """Open an existing project"""
        folder = filedialog.askdirectory(title="Select Project Folder")
        if not folder:
            return
        
        self._load_project_path(folder)

    def _load_project_path(self, folder):
        """Internal project loading logic"""
        self.project_path = folder
        if self.project_tree:
            self.project_tree.load_project(folder)
        self.ensure_project_docs()
        self.log_ai(f"📂 Loaded project: {os.path.basename(folder)}")
        
        main_path = os.path.join(folder, "main.py")
        if os.path.exists(main_path) and self.editor_tabs:
            self.editor_tabs.open_file(main_path)
            
        # Save to last project
        self.settings["last_project_path"] = folder
        save_settings(self.settings)

    def restore_last_project(self):
        """Restore the project opened in last session"""
        last_path = self.settings.get("last_project_path")
        if last_path and os.path.exists(last_path):
            self._load_project_path(last_path)
    
    def ensure_project_docs(self):
        """Ensure README.md and PORTFOLIO.md exist"""
        if not self.project_path:
            return
        
        docs = {
            "README.md": lambda name: f"# {name}\n\n## Project Overview\n\n",
            "PORTFOLIO.md": lambda name: f"# {name} - Portfolio\n\n## Project Description\n\n"
        }
        
        for filename, template in docs.items():
            path = os.path.join(self.project_path, filename)
            if not os.path.exists(path):
                project_name = os.path.basename(self.project_path)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(template(project_name))
    
    def export_project(self):
        """Export project to another location"""
        if not self.project_path:
            return
        
        folder = filedialog.askdirectory(title="Export Project")
        if not folder:
            return
        
        try:
            dest = os.path.join(folder, os.path.basename(self.project_path))
            shutil.copytree(self.project_path, dest)
            self.show_message("Success", f"Project exported to:\n{dest}")
        except Exception as e:
            self.show_message("Error", f"Export failed: {e}")
    
    def push_to_github(self):
        """Push project to GitHub with repository selection"""
        if not self.project_path:
            self.show_message("No Project", "Please open or create a project first.")
            return

        choice = messagebox.askquestion("GitHub Push", 
                                       "Do you want to create a NEW repository on GitHub?\n\nSelecting 'No' will let you specify an EXISTING repository URL.",
                                       icon='question')
        
        if choice == 'no':
            repo_url = simpledialog.askstring("Existing Repository", 
                                            "Enter the git clone URL (e.g., https://github.com/user/repo.git):")
            if not repo_url:
                return
            
            self.update_progress("Pushing to existing repository...", True)
            def worker():
                try:
                    success = self.git_init_and_push_fixed(self.project_path, repo_url)
                    if success:
                        self.root.after(0, lambda: self.show_message("Success", "✅ Project pushed to existing repository!"))
                    self.update_progress("Push completed", False)
                except Exception as e:
                    self.log_ai(f"Push error: {e}")
                    self.update_progress("Push failed", False)
            
            threading.Thread(target=worker, daemon=True).start()
            return

        # Original Create New Repository Flow
        token = self.settings.get("github_token", "")
        if not token:
            token = simpledialog.askstring("GitHub Token", 
                                         "Enter GitHub Personal Access Token:", 
                                         show="*")
            if not token:
                return
            self.settings["github_token"] = token
            self.save_settings(self.settings)
        
        repo_name = simpledialog.askstring("GitHub Repository", 
                                          "Enter repository name:", 
                                          initialvalue=os.path.basename(self.project_path))
        if not repo_name:
            return
        
        description = simpledialog.askstring("Description", 
                                           "Enter repository description (optional):")
        
        private = messagebox.askyesno("Visibility", "Make repository private?")
        
        self.update_progress("Creating GitHub repository...", True)
        
        def worker():
            try:
                # Direct GitHub API implementation
                headers = {
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "name": repo_name,
                    "description": description or "",
                    "private": private,
                    "auto_init": False
                }
                
                # Create repository
                response = requests.post(
                    "https://api.github.com/user/repos",
                    headers=headers,
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 201:
                    repo_data = response.json()
                    clone_url = repo_data.get("clone_url", f"https://github.com/{repo_data.get('full_name')}.git")
                    
                    # Initialize git and push - FIXED VERSION
                    success = self.git_init_and_push_fixed(self.project_path, clone_url)
                    
                    if success:
                        self.root.after(0, lambda: self.show_message(
                            "Success", 
                            f"✅ Project pushed to GitHub!\n\n"
                            f"Repository: {repo_name}\n"
                            f"URL: https://github.com/{repo_data.get('full_name')}"
                        ))
                    else:
                        self.root.after(0, lambda: self.show_message(
                            "Partial Success", 
                            f"Repository created but push failed.\n"
                            f"Repository URL: https://github.com/{repo_data.get('full_name')}\n"
                            f"Clone URL: {clone_url}\n\n"
                            f"Try manually:\n"
                            f"cd \"{self.project_path}\"\n"
                            f"git remote add origin {clone_url}\n"
                            f"git branch -M main\n"
                            f"git push -u origin main"
                        ))
                else:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("message", f"Status code: {response.status_code}")
                    self.root.after(0, lambda: self.show_message(
                        "Error", 
                        f"Failed to create repository:\n{error_msg}"
                    ))
                
                self.update_progress("GitHub operation completed", False)
                
            except Exception as e:
                self.update_progress("GitHub error", False)
                self.root.after(0, lambda: self.show_message(
                    "Error", 
                    f"GitHub operation failed: {str(e)}"
                ))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def git_init_and_push_fixed(self, project_path, clone_url):
        """Initialize git and push to remote - FIXED VERSION"""
        try:
            import subprocess
            import os
            
            # Check if git is installed
            try:
                subprocess.run(["git", "--version"], capture_output=True, check=True)
            except:
                return False
            
            # Change to project directory
            os.chdir(project_path)
            
            # Check if already a git repository
            if not os.path.exists(".git"):
                # Initialize git if not already
                result = subprocess.run(["git", "init"], capture_output=True, text=True)
                if result.returncode != 0:
                    return False
            
            # Add all files
            result = subprocess.run(["git", "add", "."], capture_output=True, text=True)
            if result.returncode != 0:
                return False
            
            # Check if there are any changes to commit
            result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if result.stdout.strip():  # There are changes
                # Commit changes
                result = subprocess.run(["git", "commit", "-m", "Initial commit from AI Dev IDE"], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    return False
            
            # Check if remote exists
            result = subprocess.run(["git", "remote"], capture_output=True, text=True)
            if "origin" in result.stdout:
                # Update remote URL
                subprocess.run(["git", "remote", "set-url", "origin", clone_url], 
                             capture_output=True)
            else:
                # Add remote
                result = subprocess.run(["git", "remote", "add", "origin", clone_url], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    return False
            
            # Rename branch to main
            subprocess.run(["git", "branch", "-M", "main"], capture_output=True)
            
            # Push to origin
            result = subprocess.run(["git", "push", "-u", "origin", "main"], 
                                  capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Git error: {e}")
            return False
    
    def run_agent(self, agent_type):
        """Run an AI agent with feedback"""
        if self.is_running_agent:
            self.show_message("Agent Busy", "Another agent is already running.")
            return
        
        if not self.project_path:
            self.show_message("No Project", "Please open or create a project first.")
            return
        
        prompts = {
            "plan": "Create a detailed project plan with architecture",
            "code": "Generate implementation code for the project",
            "test": "Create comprehensive test suite",
            "summarize": "Generate project documentation and summaries"
        }
        
        prompt = simpledialog.askstring(
            f"{agent_type.capitalize()} Agent",
            f"Enter goal for {agent_type} agent:",
            initialvalue=prompts.get(agent_type, "")
        )
        
        if not prompt:
            return
        
        self.stop_event.clear()
        self.is_running_agent = True
        self.update_progress(f"Starting {agent_type} agent...", True)
        
        def worker():
            try:
                # Get AI settings
                # Get currently active AI settings
                provider = self.ai_manager.get_active_provider() if hasattr(self, 'ai_manager') else self.settings.get("api_provider", "openai")
                api_url, model, token = self.get_ai_settings(provider)
                
                agent_results = {}
                
                if agent_type == "plan":
                    try:
                        from agents.planner import planner_agent
                        plan = planner_agent(prompt, api_url, model, provider, token)
                        agent_results = {
                            "type": "plan",
                            "plan": plan,
                            "files_changed": [],
                            "summary": "Project plan generated"
                        }
                    except ImportError:
                        agent_results = {
                            "type": "plan",
                            "plan": {"project_name": "AI Project", "description": prompt},
                            "summary": "Generated plan"
                        }
                    
                elif agent_type == "code":
                    try:
                        from agents.coder import coder_agent
                        # Backup current files before coding
                        if self.editor_tabs:
                            self.backup_files(self.editor_tabs.get_open_files())
                        
                        files_changed = coder_agent(self, self.project_path, prompt, api_url, model, provider, token)
                        agent_results = {
                            "type": "code",
                            "files_changed": files_changed,
                            "summary": f"Generated code in {len(files_changed)} files"
                        }
                    except ImportError:
                        agent_results = {
                            "type": "code",
                            "files_changed": [],
                            "summary": "Generated code"
                        }
                    
                elif agent_type == "test":
                    try:
                        from agents.tester import tester_agent
                        # Backup project files before creating tests
                        if self.project_path:
                            all_files = []
                            for r, d, f_names in os.walk(self.project_path):
                                for fn in f_names:
                                    if fn.endswith(('.py', '.js', '.ts', '.html', '.css')):
                                        all_files.append(os.path.join(r, fn))
                            self.backup_files(all_files[:50]) # Limit to 50 files for performance
                        
                        tests_created = tester_agent(self.project_path, api_url, model, provider, token)
                        agent_results = {
                            "type": "test",
                            "files_changed": tests_created,
                            "summary": f"Created {len(tests_created)} test files"
                        }
                    except ImportError:
                        agent_results = {
                            "type": "test",
                            "files_changed": [],
                            "summary": "Created tests"
                        }
                    
                elif agent_type == "summarize":
                    try:
                        from agents.summarizer import summarizer_agent
                        # Backup project files before summarization (it might update README/docs)
                        if self.project_path:
                            all_files = []
                            for r, d, f_names in os.walk(self.project_path):
                                for fn in f_names:
                                    if fn.endswith(('.md', '.txt', 'README', 'LICENSE')):
                                        all_files.append(os.path.join(r, fn))
                            self.backup_files(all_files[:20])
                        
                        docs_updated = summarizer_agent(self.project_path, api_url, model, provider, token)
                        agent_results = {
                            "type": "documentation",
                            "files_changed": docs_updated,
                            "summary": f"Updated {len(docs_updated)} documentation files"
                        }
                    except ImportError:
                        agent_results = {
                            "type": "documentation",
                            "files_changed": [],
                            "summary": "Updated documentation"
                        }
                
                # Show agent results
                self.show_agent_results(agent_results)
                
                if self.project_tree:
                    self.root.after(100, self.project_tree.refresh)
                
                self.update_progress(f"{agent_type} agent completed", False)
                
            except Exception as e:
                self.update_progress(f"Error in {agent_type} agent", False)
                self.log_ai(f"❌ {agent_type} agent error: {e}")
                traceback.print_exc()
            finally:
                self.is_running_agent = False
        
        threading.Thread(target=worker, daemon=True).start()
    
    def get_ai_settings(self, provider):
        """Get AI settings for provider"""
        if hasattr(self, 'ai_manager'):
            config = self.ai_manager.get_provider_config(provider)
            # Ensure we return exactly 3 values for unpacking (api_url, model, token)
            # get_provider_config returns (url, model, token, type)
            return config[0], config[1], config[2]
        # Fallback if manager not ready
        api_url = ""
        model = ""
        token = ""
        
        return api_url, model, token
    
    def show_agent_results(self, results):
        """Show what the AI agent did"""
        if not results:
            return
        
        if self.ai_panel:
            message = f"🤖 {results.get('type', 'Agent').upper()} AGENT RESULTS:\n\n"
            message += f"📋 Summary: {results.get('summary', 'No summary')}\n\n"
            
            files_changed = results.get('files_changed', [])
            if files_changed:
                message += "📁 Files Changed/Created:\n"
                for file in files_changed:
                    message += f"  • {file}\n"
            
            if results.get('plan'):
                message += f"\n📝 Plan:\n{results['plan'][:1000]}..."
            
            self.ai_panel.add_chat_message("AI", message)
        
        self.log_ai(f"✅ Agent completed: {results.get('summary', 'Done')}")
        self.play_agent_done_sound()
    
    def test_and_fix_loop(self):
        """Unified loop: Runs tests or script, detects errors, and fixes them autonomously"""
        if not self.project_path:
            self.show_message("No Project", "Please open a project first.")
            return
        
        self.is_running_agent = True
        self.update_progress("Starting autonomous test-and-fix loop...", True)
        
        def worker():
            max_iterations = 10
            last_error = ""
            try:
                for iteration in range(max_iterations):
                    if not self.is_running_agent:
                        break
                        
                    self.log_ai(f"🔄 Iteration {iteration + 1}/{max_iterations}")
                    
                    # 1. Determine what to run (Tests or Main Script)
                    from core.test_runner import TestRunner
                    test_runner = TestRunner()
                    test_files = test_runner.find_test_files(self.project_path)
                    
                    error_log = ""
                    success = False
                    
                    if test_files:
                        self.log_ai("🔬 Running unit tests...")
                        results = test_runner.run_tests(self.project_path)
                        error_log = results.get("raw_output", "")
                        success = results.get("passed", 0) == results.get("total", 0) and results.get("total", 0) > 0
                        if success:
                            self.log_ai("✅ All tests passed!")
                    else:
                        # Try to run the current file or main.py
                        current_file = self.editor_tabs.get_current_file() if self.editor_tabs else None
                        file_to_run = current_file
                        
                        if not file_to_run or not file_to_run.endswith(".py"):
                            main_py = os.path.join(self.project_path, "main.py")
                            if os.path.exists(main_py):
                                file_to_run = main_py
                        
                        if file_to_run:
                            # Save before running
                            if self.editor_tabs:
                                self.editor_tabs.save_all_files()
                                
                            self.log_ai(f"▶ Running script: {os.path.basename(file_to_run)}")
                            try:
                                result = subprocess.run(
                                    [sys.executable, file_to_run],
                                    capture_output=True,
                                    text=True,
                                    timeout=30,
                                    cwd=self.project_path
                                )
                                if result.returncode == 0:
                                    success = True
                                    self.log_ai("✅ Script executed successfully!")
                                else:
                                    error_log = result.stderr or result.stdout
                                    self.log_ai("❌ Script execution failed.")
                            except subprocess.TimeoutExpired:
                                error_log = "Execution timed out after 30 seconds."
                                self.log_ai("❌ Script execution timed out.")
                            except Exception as e:
                                error_log = str(e)
                                self.log_ai(f"❌ Execution error: {e}")
                        else:
                            self.log_ai("🔬 No tests or runnable script found. Generating tests...")
                            # Fallback: Generate tests if nothing else to do
                            success = False
                            error_log = "No tests found. Please generate tests for this project."
                    
                    if success:
                        break
                    
                    # Check if we are stuck on the same error
                    if error_log == last_error:
                        self.log_ai("⚠️ Error persists unchanged. Trying more aggressive fix...")
                        error_log += "\n\nIMPORTANT: The previous fix attempt did not change this error. Please try a different approach or verify imports."
                    last_error = error_log
                    
                    # 2. Fix errors if found
                    if error_log:
                        self.log_ai("🤖 AI is fixing errors...")
                        try:
                            from agents.fixer import FixerAgent
                            fixer = FixerAgent(self)
                            
                            # Get open files for context
                            selected_files = list(self.editor_tabs.get_open_files()) if self.editor_tabs else []
                            if not selected_files and self.project_path:
                                # Fallback to all files if none open
                                for r, d, f_names in os.walk(self.project_path):
                                    for fn in f_names:
                                        if fn.endswith('.py'):
                                            selected_files.append(os.path.join(r, fn))
                            
                            # Backup files before fixing
                            self.backup_files(selected_files)
                            
                            # Use the improved FixerAgent with more iterations internally if needed
                            result = fixer.fix_errors(
                                files=[os.path.relpath(f, self.project_path) for f in selected_files if os.path.isabs(f)],
                                error_log=error_log,
                                max_iterations=2 # Allow internal retry
                            )
                            
                            if result.get("success"):
                                self.log_ai(f"✅ AI applied fixes: {', '.join(result.get('fixes', {}).keys())}")
                                # Reload modified files
                                if self.editor_tabs:
                                    for file_path in selected_files:
                                        self.root.after(0, lambda f=file_path: self.editor_tabs.open_file(f))
                                
                                # Small delay to ensure file system and UI are synced
                                import time
                                time.sleep(1)
                            else:
                                self.log_ai(f"❌ AI failed to fix: {result.get('error', 'Unknown error')}")
                                if "parsing" in result.get("error", "").lower():
                                    self.log_ai("⚠️ Parsing error detected. Loop may be stuck.")
                        except Exception as e:
                            self.log_ai(f"❌ Fixer error: {e}")
                            import traceback
                            print(traceback.format_exc())
                    else:
                        self.log_ai("No error log captured. Stopping loop.")
                        break
                        
                if success:
                    self.update_progress("Loop completed successfully!", False)
                else:
                    self.update_progress("Loop finished with issues.", False)
                    
            finally:
                self.is_running_agent = False
        
        threading.Thread(target=worker, daemon=True).start()
    
    def suggest_fixes(self):
        """Use AI to suggest and test fixes"""
        if not self.project_path:
            self.show_message("No Project", "Please open or create a project first.")
            return
        
        if self.is_running_agent:
            self.show_message("Busy", "Please wait for current operation to complete.")
            return
        
        # Get error log from output panel
        error_log = ""
        if self.output_panels:
            try:
                error_log = self.output_panels.script_output.get("1.0", "end-1c").strip()
            except:
                pass
        
        if not error_log or "Error" not in error_log and "Traceback" not in error_log:
            # Run tests to get errors
            self.run_tests_and_show()
            self.log_ai("Running tests first to get error logs...")
            self.root.after(3000, lambda: self._start_fixer(error_log))
            return
        
        self._start_fixer(error_log)
    
    def _start_fixer(self, error_log):
        """Start the fixer agent"""
        self.stop_event.clear()
        self.is_running_agent = True
        self.update_progress("Analyzing errors and testing fixes...", True)
        
        def worker():
            try:
                if not self.is_running_agent: return
                from agents.fixer import advanced_fixer_agent
                
                # Get AI settings
                # Get currently active AI settings
                provider = self.ai_manager.get_active_provider() if hasattr(self, 'ai_manager') else self.settings.get("api_provider", "openai")
                api_url, model, token = self.get_ai_settings(provider)
                
                selected_files = []
                if self.editor_tabs:
                    selected_files = list(self.editor_tabs.get_open_files())
                
                if not selected_files:
                    selected_files = [self.editor_tabs.get_current_file()] if self.editor_tabs else []
                
                # Backup files before fixing
                self.backup_files(selected_files)
                
                result = advanced_fixer_agent(
                    project_path=self.project_path,
                    files=selected_files,
                    error_log=error_log,
                    api_url=api_url,
                    model=model,
                    max_iterations=3
                )
                
                if result.get("success"):
                    self.ai_suggested_changes = result.get("fixes", {})
                    
                    if self.ai_panel:
                        self.ai_panel.display_suggested_changes({
                            "analysis": result.get("analysis", ""),
                            "fixes": result["fixes"],
                            "tests_passed": result.get("tests_passed", False),
                            "iterations": result.get("iterations", 0)
                        })
                        self.ai_panel.show_pending_changes(len(result["fixes"]))
                    
                    self.update_progress(f"Found fixes after {result.get('iterations', 0)} iterations", False)
                else:
                    self.update_progress("No working fixes found", False)
                    self.show_message("No Fixes", "AI couldn't find working fixes after multiple attempts.")
                
            except Exception as e:
                self.update_progress("Fixer error", False)
                self.log_ai(f"Fixer error: {e}")
                self.show_message("Fixer Error", f"Fixer failed: {e}")
                import traceback
                traceback.print_exc()
            finally:
                self.is_running_agent = False
        
        threading.Thread(target=worker, daemon=True).start()
    
    def apply_ai_changes(self):
        """Apply AI suggested changes"""
        if not self.ai_suggested_changes:
            self.show_message("No Changes", "No AI changes to apply.")
            return
        
        applied = 0
        for fname, new_content in self.ai_suggested_changes.items():
            try:
                full_path = os.path.join(self.project_path, fname)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                with open(full_path, 'w', encoding='utf-8') as fh:
                    fh.write(new_content)
                
                if self.editor_tabs and fname in self.editor_tabs.get_open_files():
                    self.editor_tabs.update_file_content(fname, new_content)
                
                applied += 1
                self.log_ai(f"✅ Applied changes to: {fname}")
                
            except Exception as e:
                self.log_ai(f"❌ Error applying changes to {fname}: {e}")
        
        if applied > 0:
            self.show_message("Changes Applied", f"Applied {applied} file(s) from AI suggestions.")
            self.ai_suggested_changes = {}
            if self.ai_panel:
                self.ai_panel.hide_pending_changes()
            if self.project_tree:
                self.project_tree.refresh()
            
            self.run_tests_and_show()
        else:
            self.show_message("No Changes Applied", "No changes were applied.")
    
    def review_code(self):
        """AI code review and documentation generation"""
        if not self.project_path:
            self.show_message("No Project", "Please open a project first.")
            return
            
        self.update_progress("Generating README and Portfolio...", True)
        
        def worker():
            try:
                # Get project files to understand context
                files = []
                for root, _, filenames in os.walk(self.project_path):
                    for f in filenames:
                        if not any(x in root for x in [".git", "__pycache__", "venv", "node_modules"]):
                            files.append(os.path.join(root, f))
                
                # Get contents of main files
                context = ""
                count = 0
                for f in files:
                    if count >= 10: break
                    if f.endswith(('.py', '.js', '.ts', '.html', '.css', '.md', '.txt')):
                        try:
                            with open(f, 'r', encoding='utf-8', errors='ignore') as src:
                                context += f"\nFile: {os.path.basename(f)}\n{src.read()[:500]}\n"
                                count += 1
                        except: pass
                
                # Get currently active AI settings
                provider = "openai"
                if hasattr(self, 'ai_manager'):
                    provider = self.ai_manager.get_active_provider()
                
                api_url, model, token = self.get_ai_settings(provider)
                
                from core.llm import call_llm
                
                # 1. Generate README.md
                readme_prompt = f"Based on this project context, generate a professional README.md with project title, description, features, and setup instructions:\n{context}\nOutput only the markdown content."
                readme_content = call_llm(readme_prompt, api_url, model, provider, token)
                
                # 2. Generate PORTFOLIO.md
                portfolio_prompt = f"Based on this project context, generate a professional PORTFOLIO.md for a developer showcase. Highlight technical challenges and solutions:\n{context}\nOutput only the markdown content."
                portfolio_content = call_llm(portfolio_prompt, api_url, model, provider, token)
                
                # Save files
                with open(os.path.join(self.project_path, "README.md"), 'w', encoding='utf-8') as f:
                    f.write(readme_content)
                with open(os.path.join(self.project_path, "PORTFOLIO.md"), 'w', encoding='utf-8') as f:
                    f.write(portfolio_content)
                
                self.root.after(0, lambda: self.project_tree.refresh() if self.project_tree else None)
                self.log_ai("✅ Generated README.md and PORTFOLIO.md")
                self.update_progress("Documentation generated", False)
                self.show_message("Review Code", "Documentation (README and Portfolio) generated and added to project.")
                
            except Exception as e:
                self.update_progress("Documentation failed", False)
                self.log_ai(f"Documentation error: {e}")
            finally:
                self.is_running_agent = False
        
        self.is_running_agent = True
        threading.Thread(target=worker, daemon=True).start()
    
    def optimize_code(self):
        """AI code optimization"""
        if not self.editor_tabs:
            return
        
        current_file = self.editor_tabs.get_current_file()
        if not current_file:
            self.show_message("No File", "Please open a file to optimize.")
            return
        
        try:
            with open(current_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get currently active AI settings
            provider = "openai"
            if hasattr(self, 'ai_manager'):
                provider = self.ai_manager.get_active_provider()
            
            api_url, model, token = self.get_ai_settings(provider)
            
            from core.llm import call_llm
            
            prompt = f"""Optimize this code for performance and readability:

File: {os.path.basename(current_file)}

Current Code:
{content[:3000]}

Please provide optimized version with explanations of changes made."""
            
            self.is_running_agent = True
            self.update_progress("AI optimizing code...", True)
            
            def worker():
                try:
                    optimized = call_llm(prompt, api_url, model, provider, token)
                    
                    # Try to separate code from explanation if possible
                    code = optimized
                    analysis = "Optimization suggested by AI."
                    
                    if "```" in optimized:
                        import re
                        match = re.search(r'```(?:\w+)?\n(.*?)\n```', optimized, re.DOTALL)
                        if match:
                            code = match.group(1)
                            analysis = optimized.replace(match.group(0), "").strip()
                    
                    if self.ai_panel:
                        self.ai_panel.display_suggested_changes({
                            "analysis": analysis,
                            "fixes": {current_file: code}
                        })
                        self.ai_suggested_changes = {current_file: code}
                        self.ai_panel.show_pending_changes(1)
                    self.show_message("Code Optimization", "AI optimization completed. Check AI panel for suggestions.")
                except Exception as e:
                    self.update_progress("Optimization failed", False)
                    self.log_ai(f"Optimization error: {e}")
                finally:
                    self.is_running_agent = False
            
            threading.Thread(target=worker, daemon=True).start()
            
        except Exception as e:
            self.show_message("Error", f"Failed to read file: {e}")
    
    def route_chat_to_agent(self, message, agent_name, model_name=None, conversation_history=None):
        """Route chat message to a specific agent"""
        if agent_name.lower() == "image":
            # Handle image analysis (Vision)
            self.run_image_analysis(message, model_name, conversation_history)
        elif agent_name.lower() == "terminal":
            # Direct to terminal agent if available
            self.run_agent("terminal", conversation_history)
        else:
            # Fallback to general process_chat_message
            self.process_chat_message(message, model_name, conversation_history)

    def run_image_analysis(self, message, model_name=None, conversation_history=None):
        """Run the Vision/Image agent to analyze attached screenshots"""
        if not self.ai_panel:
            return
            
        attached = self.ai_panel.attached_files
        if not attached:
            # Try to see if there's a path in the message
            import re
            match = re.search(r'([A-Za-z]:\\[^"<>|\r\n]+\.(png|jpg|jpeg|gif|webp))', message)
            if match:
                attached = [match.group(1)]
            else:
                self.ai_panel.add_chat_message("System", "No image attached or found for analysis. Paste a screenshot first!")
                return

        self.update_progress("Analyzing image(s)...", True)
        
        def worker():
            try:
                from agents.image_agent import ImageAgent
                provider = self.ai_manager.get_active_provider() if hasattr(self, 'ai_manager') else self.settings.get("api_provider", "huggingface")
                # Default model for vision if using HF
                model = model_name if model_name else self.settings.get("vision_model", "Qwen/Qwen2-VL-7B-Instruct") 
                api_url, _, token = self.get_ai_settings(provider)
                
                agent = ImageAgent(model_provider=provider, model_name=model)
                # Set token manually if from Account Dialog
                agent.set_api_token(token)
                
                for img_path in attached:
                    self.log_ai(f"🖼️ Analyzing: {os.path.basename(img_path)}")
                    task_data = {"image_path": img_path, "message": message, "conversation_history": conversation_history}
                    result = agent.process(task_data)
                    
                    if self.ai_panel:
                        self.ai_panel.add_chat_message("Image Agent", result)
                
                self.update_progress("Image analysis complete", False)
            except Exception as e:
                self.log_ai(f"Image analysis error: {e}")
                self.update_progress("Analysis failed", False)
                
        threading.Thread(target=worker, daemon=True).start()

    def process_chat_message(self, message, model_name=None, conversation_history=None):
        """Process chat message with advanced AI - FIXED VERSION"""
        if not message.strip():
            return
        
        self.is_running_agent = True
        self.stop_event.clear()
        self.update_progress("AI processing your request...", True)
        
        def worker():
            try:
                # Get currently active AI settings
                provider = self.ai_manager.get_active_provider() if hasattr(self, 'ai_manager') else self.settings.get("api_provider", "openai")
                api_url, model, token = self.get_ai_settings(provider)
                
                # Override model if provided from UI
                if model_name:
                    model = model_name

                # Use the enhanced chat agent (handles modifications automatically)
                current_file = self.editor_tabs.get_current_file() if self.editor_tabs else None
                from agents.chat_agent import chat_agent
                
                # Prepare hardware info
                hardware = {}
                try:
                    from utils.hardware_info import get_gpu_info
                    hardware = get_gpu_info()
                except:
                    pass

                context = {
                    "project_path": self.project_path,
                    "current_file": current_file,
                    "open_files": self.editor_tabs.get_open_files() if self.editor_tabs else [],
                    "project_tree": self.project_tree.get_all_files() if self.project_tree else [],
                    "conversation_history": conversation_history, # Pass conversation history
                    "hardware_info": hardware
                }

                def on_tasks_update(tasks):
                    if self.ai_panel:
                        self.root.after(0, lambda: self.ai_panel.update_tasks(tasks))
                
                phases_shown = []
                def on_phase_update(phase, content):
                    phases_shown.append(phase)
                    if self.ai_panel:
                        self.root.after(0, lambda: self.ai_panel.add_chat_message(f"AI ({phase})", content))
                
                response = chat_agent(
                    message=message,
                    api_url=api_url,
                    model=model,
                    api_provider=provider,
                    token=token,
                    context=context,
                    execute_actions=self.settings.get("agent_auto_approve", False),
                    on_tasks_update=on_tasks_update,
                    on_phase_update=on_phase_update,
                    stop_event=self.stop_event
                )
                
                if self.ai_panel and not phases_shown:
                    if isinstance(response, dict):
                        self.ai_panel.add_chat_message("AI", response.get("response", str(response)))
                    else:
                        self.ai_panel.add_chat_message("AI", str(response))
                
                self.play_agent_done_sound()
                
                # Handle actions performed
                if isinstance(response, dict):
                    # Handle manual approval requests
                    if response.get("requires_approval") and self.ai_panel:
                        if response.get("command"):
                            cmd = response.get("command")
                            self.root.after(0, lambda c=cmd: self.ai_panel.add_action_button(
                                f"Run: {c}",
                                lambda: self.execute_shell_command(c)
                            ))
                        
                        # Handle patches from the main response or actions list
                        patches_to_show = []
                        if response.get("patch") and response.get("file"):
                            patches_to_show.append((response.get("file"), response.get("patch")))
                        
                        # Add any patches from actions that weren't executed
                        for action in response.get("actions_performed", []):
                            if action.get("type") == "modify_file" and action.get("patch") and action.get("file"):
                                if (action.get("file"), action.get("patch")) not in patches_to_show:
                                    patches_to_show.append((action.get("file"), action.get("patch")))
                        
                        for file_p, patch in patches_to_show:
                            self.root.after(0, lambda f=file_p, p=patch: self.ai_panel.add_action_button(
                                f"Apply to {os.path.basename(f)}",
                                lambda: self.apply_patch_manually(f, p)
                            ))

                    actions = response.get("actions_performed", [])
                    
                    # Process ALL actions (including primary and secondary files)
                    for action in actions:
                        action_type = action.get("type")
                        if action_type == "modify_file":
                            file_path = action.get("file")
                            content = action.get("content")
                            if file_path and content:
                                # Update editor (handles opening new tabs if needed)
                                if self.editor_tabs:
                                    self.root.after(0, lambda f=file_path, c=content: self.editor_tabs.update_file_content(f, c))
                                
                                # Auto-test if Python file and auto-approve is on
                                if file_path.endswith('.py') and self.settings.get("agent_auto_approve", False):
                                    self.root.after(1000, lambda f=file_path: self.test_modified_script(f))
                        
                        elif action_type == "run_command":
                            cmd = action.get("command")
                            if cmd:
                                self.log_ai(f"🚀 AI execution: {cmd}")
                                if self.settings.get("agent_auto_approve", False):
                                    self.root.after(0, lambda c=cmd: self.execute_shell_command(c))
                        
                        self.log_ai(f"🤖 AI performed action: {action_type}")
                    
                    # Refresh project tree if files changed
                    if any(a.get("type") in ["create_file", "delete_file", "modify_file"] for a in actions):
                        if self.project_tree:
                            self.root.after(100, lambda: self.project_tree.refresh())
                
                self.update_progress("Request completed", False)
                
            except Exception as e:
                error_msg = f"Error processing chat: {str(e)}. Please check the input and try again."
                if self.ai_panel:
                    self.ai_panel.add_chat_message("AI", f"I encountered an error: {error_msg}")
                self.update_progress("Chat error", False)
                traceback.print_exc()
            finally:
                self.is_running_agent = False
        
        threading.Thread(target=worker, daemon=True).start()
    
    def ai_edit_active_editor(self):
        """AI Edit feature for selected text or whole file"""
        if not self.editor_tabs or not self.editor_tabs.current_file:
            self.show_message("No File", "Open a file first.")
            return

        from tkinter import simpledialog
        instruction = simpledialog.askstring("AI Edit", "What would you like the AI to do with this selection/file?")
        if not instruction:
            return

        text, start, end = self.editor_tabs.get_selection_info()
        if not text:
            return

        # Get AI settings
        provider = self.ai_manager.get_active_provider() if hasattr(self, 'ai_manager') else self.settings.get("api_provider", "openai")
        api_url, model, token = self.get_ai_settings(provider)

        from core.llm import call_llm
        self.update_progress("AI editing...", True)
        
        def worker():
            try:
                prompt = f"""Task: {instruction}
                
                Content to edit:
                ---
                {text}
                ---
                
                Please provide the edited version of the content above. 
                Maintain the same format and style. 
                Return ONLY the edited content, no explanations or markdown blocks."""
                
                edited_text = call_llm(prompt, api_url, model, provider, token, stop_event=self.stop_event)
                
                # Clean up if AI included markdown blocks
                if "```" in edited_text:
                    import re
                    match = re.search(r'```(?:\w+)?\n(.*?)\n```', edited_text, re.DOTALL)
                    if match:
                        edited_text = match.group(1)
                    else:
                        edited_text = edited_text.replace("```", "").strip()

                def apply_changes():
                    self.editor_tabs.replace_range(start, end, edited_text)
                    self.update_progress("AI edit complete", False)
                    self.log_ai(f"✨ AI edited selection in {os.path.basename(self.editor_tabs.current_file)}")

                self.root.after(0, apply_changes)
                
            except Exception as e:
                self.root.after(0, lambda: self.update_progress("AI edit failed", False))
                self.log_ai(f"❌ AI edit error: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def modify_current_file_with_ai(self, message, current_file, api_url, model, token):
        """Modify the current file based on AI request - Enhanced with patches and auto-test"""
        try:
            from agents.chat_agent import handle_modification_request
            
            context = {
                "current_file": current_file,
                "project_path": self.project_path,
                "open_files": self.editor_tabs.get_open_files() if self.editor_tabs else []
            }
            
            provider = self.ai_manager.get_active_provider() if hasattr(self, 'ai_manager') else self.settings.get("api_provider", "openai")
            prev = None
            try:
                with open(current_file, 'r', encoding='utf-8') as f:
                    prev = f.read()
            except Exception:
                prev = None
            def on_tasks_update(tasks):
                if self.ai_panel:
                    self.root.after(0, lambda: self.ai_panel.update_tasks(tasks))

            def on_phase_update(phase, content):
                if self.ai_panel:
                    self.root.after(0, lambda: self.ai_panel.add_chat_message(f"AI ({phase})", content))

            result = handle_modification_request(message, context, api_url, model, provider, token, on_tasks_update=on_tasks_update, on_phase_update=on_phase_update)
            
            if result.get("modified_content"):
                # Update the editor
                if self.editor_tabs:
                    self.editor_tabs.update_file_content(current_file, result["modified_content"])
                if prev is not None:
                    try:
                        self.show_diff_window(current_file, prev, result["modified_content"])
                    except Exception:
                        pass
                
                # Auto-test the script
                if current_file.endswith('.py'):
                    self.log_ai("🧪 Testing modified script...")
                    self.root.after(500, lambda: self.test_modified_script(current_file))
            
            # Show response
            if self.ai_panel:
                self.ai_panel.add_chat_message("AI", result.get("response", "Changes applied"))
            
            self.log_ai(f"✅ Modified {os.path.basename(current_file)}")
            
        except Exception as e:
            error_msg = f"Failed to modify file: {str(e)}"
            if self.ai_panel:
                self.ai_panel.add_chat_message("AI", error_msg)
            self.log_ai(f"❌ Error modifying file: {e}")
            import traceback
            traceback.print_exc()
    
    def test_modified_script(self, script_path):
        """Test a modified script automatically"""
        if not script_path or not os.path.exists(script_path):
            return
        
        def test_worker():
            try:
                # Run syntax check
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                compile(content, script_path, 'exec')
                self.log_ai("✅ Syntax check passed")
                
                # Try to run the script (with timeout)
                if self.project_path:
                    import sys
                    result = subprocess.run(
                        [sys.executable, script_path],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        self.log_ai(f"✅ Script executed successfully\n{result.stdout[:200]}")
                    else:
                        self.log_ai(f"⚠️ Script executed with errors:\n{result.stderr[:200]}")
                        
            except SyntaxError as e:
                self.log_ai(f"❌ Syntax error: {e}")
            except subprocess.TimeoutExpired:
                self.log_ai("⚠️ Script execution timed out")
            except Exception as e:
                self.log_ai(f"⚠️ Test error: {e}")
        
        threading.Thread(target=test_worker, daemon=True).start()
    
    def run_tests_and_show(self):
        """Run tests and show detailed results"""
        if not self.project_path:
            self.show_message("No Project", "Please open a project first.")
            return
        
        self.update_progress("Running tests...", True)
        
        def worker():
            try:
                from core.test_runner import TestRunner
                test_runner = TestRunner()
                
                results = test_runner.run_tests(self.project_path)
                self.current_test_results = results
                
                if self.output_panels:
                    self.output_panels.clear_script_output()
                    
                    summary = f"Test Results:\n"
                    summary += f"  Total: {results.get('total', 0)}\n"
                    summary += f"  Passed: {results.get('passed', 0)}\n"
                    summary += f"  Failed: {results.get('failed', 0)}\n"
                    summary += f"  Errors: {results.get('errors', 0)}\n"
                    
                    failures = []
                    
                    if results.get('details'):
                        summary += "\nDetails:\n"
                        for test in results['details']:
                            status = "✅ PASS" if test.get('passed') else "❌ FAIL"
                            summary += f"  {status}: {test.get('name', 'Unknown')}\n"
                            if not test.get('passed'):
                                error_msg = test.get('error', 'Test failed')
                                summary += f"     Error: {error_msg}\n"
                                
                                # Add to failures list for Problems tab
                                failures.append({
                                    'file': test.get('file', 'Unknown'),
                                    'line': 0,
                                    'message': f"Test Failed: {test.get('name')} - {error_msg}",
                                    'type': 'error'
                                })
                    
                    self.log_script(summary)
                    self.log_ai(f"Tests completed: {results.get('passed', 0)}/{results.get('total', 0)} passed")
                    
                    # Update Problems tab with failures
                    self.root.after(0, lambda: self.output_panels.update_problems(failures))
                    
                    # Switch to Output tab if passed, Problems if failed?
                    if failures:
                        self.root.after(0, lambda: self.output_panels.notebook.select(0)) # Select Problems
                    else:
                        self.root.after(0, lambda: self.output_panels.notebook.select(1)) # Select Output
                
                self.update_progress(f"Tests: {results.get('passed', 0)}/{results.get('total', 0)} passed", False)
                
            except Exception as e:
                self.update_progress("Test error", False)
                self.log_script(f"Error running tests: {e}")
        
        threading.Thread(target=worker, daemon=True).start()
    
    def stop_current_script(self):
        """Stop the currently running script or process"""
        if self.output_panels:
            self.output_panels.stop_script()
            self.log_ai("⏹ Stopping running script...")
        else:
            self.log_ai("⚠️ Output panels not available.")

    def save_and_run(self):
        """Save and run current script using terminal"""
        self.save_all_open_files()
        if not self.project_path:
            return
        
        target = None
        if self.editor_tabs:
            current_file = self.editor_tabs.get_current_file()
            if current_file:
                target = current_file
            else:
                # Try to find main.py or index.js in project
                for main_file in ["main.py", "index.js", "app.py", "server.js"]:
                    main_path = os.path.join(self.project_path, main_file)
                    if os.path.exists(main_path):
                        target = main_path
                        break
                
                if not target:
                    self.log_script("No file to run. Open a file first.")
                    return
        
        # Check if terminal is available
        if self.output_panels and hasattr(self.output_panels, 'run_script_in_terminal'):
            try:
                success = self.output_panels.run_script_in_terminal(target, self.project_path)
                if success:
                    return
            except Exception as e:
                self.log_ai(f"Terminal error: {e}")
        
        # Fallback to old method if terminal not available
        self.log_ai("Using fallback script execution")
        self.run_script_fallback(target)
    
    def apply_patch_manually(self, file_path, patch):
        """Manually apply a patch suggested by AI"""
        try:
            from agents.chat_agent import apply_patch
            abs_path = os.path.abspath(file_path)
            if not os.path.exists(abs_path):
                if not os.path.isabs(file_path) and self.project_path:
                    abs_path = os.path.abspath(os.path.join(self.project_path, file_path))
            if self.project_path:
                try:
                    proj_root = os.path.abspath(self.project_path)
                    if os.path.commonpath([abs_path, proj_root]) != proj_root:
                        self.show_message("Security", "Patch outside project is blocked.")
                        return
                except Exception:
                    pass
            file_path = abs_path
            
            content = ""
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    self.log_ai(f"❌ Error reading file: {e}")
                    return
            else:
                self.log_ai(f"📝 Creating new file: {os.path.basename(file_path)}")
            
            result = apply_patch(file_path, content, patch)
            if result.get("success"):
                self.log_ai(f"✅ Manually applied patch to {os.path.basename(file_path)}")
                if self.editor_tabs:
                    self.root.after(0, lambda: self.editor_tabs.open_file(file_path))
                
                # Refresh project tree
                if self.project_tree:
                    self.root.after(100, lambda: self.project_tree.refresh())
                try:
                    self.show_diff_window(file_path, content, result.get("modified_content", ""))
                except Exception:
                    pass
                # Test if Python file and start autonomous fix loop if needed
                if file_path.endswith('.py'):
                    self.log_ai("🔄 Patch applied. Starting autonomous verification and fix loop...")
                    self.root.after(500, self.test_and_fix_loop)
            else:
                self.show_message("Error", f"Could not apply patch: {result.get('error')}")
        except Exception as e:
            self.log_ai(f"Error applying patch manually: {e}")

    def show_diff_window(self, file_path, before, after):
        try:
            import difflib
            win = tk.Toplevel(self.root)
            win.title(f"Diff: {os.path.basename(file_path)}")
            win.geometry("900x600")
            txt = tk.Text(win, wrap="none", bg="#0c0c0c", fg="#cccccc")
            txt.pack(fill="both", expand=True)
            diff = difflib.unified_diff(
                before.splitlines(), after.splitlines(),
                fromfile=os.path.basename(file_path)+" (before)",
                tofile=os.path.basename(file_path)+" (after)",
                lineterm=""
            )
            txt.insert("1.0", "\n".join(list(diff)) or "No changes")
        except Exception:
            pass

    def install_requirements(self):
        """Install dependencies from requirements.txt using system shell"""
        if not self.project_path:
            self.show_message("No Project", "Please open a project first.")
            return
        req_path = os.path.join(self.project_path, "requirements.txt")
        if not os.path.exists(req_path):
            self.show_message("Missing File", "No requirements.txt found in project root.")
            return
        try:
            import sys
            cmd = f'"{sys.executable}" -m pip install -r requirements.txt'
            self.execute_shell_command(cmd)
        except Exception as e:
            self.log_ai(f"Error starting pip install: {e}")

    def execute_shell_command(self, cmd):
        """Execute an arbitrary shell command and show output in script panel"""
        if not cmd:
            return
            
        self.is_running_agent = True
        self.update_progress(f"Running command: {cmd[:30]}...", True)
        
        def worker():
            try:
                if self.output_panels:
                    self.output_panels.clear_script_output()
                    self.log_script(f"Executing: {cmd}\n")
                    self.log_script("="*50 + "\n")
                
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    cwd=self.project_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=0,
                    universal_newlines=False
                )
                
                if self.output_panels:
                    self.output_panels.running_process = process
                    self.output_panels.update_input_state(True)
                
                def read_output(pipe):
                    try:
                        for line in iter(pipe.readline, b''):
                            line_str = line.decode('utf-8', errors='replace')
                            self.root.after(0, lambda m=line_str: self.log_script(m))
                    except: pass
                    finally: pipe.close()

                import threading
                t1 = threading.Thread(target=read_output, args=(process.stdout,), daemon=True)
                t2 = threading.Thread(target=read_output, args=(process.stderr,), daemon=True)
                t1.start()
                t2.start()
                
                returncode = process.wait()
                
                if self.output_panels:
                    self.output_panels.process_terminated = True
                    self.output_panels.update_input_state(False)
                
                self.update_progress(f"Command finished", False)
                self.log_script(f"\n[Command exited with code {returncode}]")
                
            except Exception as e:
                self.log_script(f"Execution Error: {e}")
            finally:
                self.is_running_agent = False
        
        threading.Thread(target=worker, daemon=True).start()

    def run_script_fallback(self, script_path):
        """Run script using subprocess (fallback/main method now) - MULTI-LANGUAGE SUPPORT"""
        if not script_path or not os.path.exists(script_path):
            return
            
        self.save_all_open_files()
        
        self.is_running_agent = True
        self.update_progress(f"Running {os.path.basename(script_path)}...", True)
        
        # Determine command based on extension
        ext = os.path.splitext(script_path)[1].lower()
        
        # Configuration for runners
        runners = {
            '.py': ["python", "-u", script_path],
            '.lua': ["lua", script_path],  # Requires lua in PATH
            '.js': ["node", script_path],   # Requires node in PATH
            '.cpp': None, # Needs compilation
            '.c': None,   # Needs compilation
            '.cs': ["dotnet", "run"], # Requires project structure usually, simpler: csc? Assume dotnet run in cwd
        }
        
        # Special handling for compiled languages
        compile_cmd = None
        run_cmd = None
        
        if ext == '.cpp' or ext == '.c':
            # Simple single-file compilation
            exe_name = os.path.splitext(script_path)[0]
            if os.name == 'nt': exe_name += ".exe"
            compiler = "g++" if ext == '.cpp' else "gcc"
            compile_cmd = [compiler, script_path, "-o", exe_name]
            run_cmd = [exe_name]
        elif ext == '.cs':
            # Assuming dotnet project or use csc
            # For simplicity, let's try 'dotnet run' if project exists, or warn user
            if os.path.exists(os.path.join(self.project_path, "obj")): # Simple check for dotnet project
                 run_cmd = ["dotnet", "run"]
            else:
                 # Try simple csc??? No, let's just default to dotnet run and hope
                 run_cmd = ["dotnet", "run"]
        elif ext in runners:
            run_cmd = runners[ext]
        else:
            self.show_message("Unsupported", f"No runner configured for {ext} files.")
            self.is_running_agent = False
            self.update_progress("", False)
            return

        def worker():
            try:
                if self.output_panels:
                    self.output_panels.clear_script_output()
                    self.output_panels.running_process = None
                    self.output_panels.process_terminated = False
                    self.log_script(f"Running: {os.path.basename(script_path)}\n")
                    self.log_script("="*50 + "\n")
                
                # Compilation Step
                if compile_cmd:
                    self.log_script(f"Compiling: {' '.join(compile_cmd)}\n")
                    compile_result = subprocess.run(
                        compile_cmd,
                        cwd=os.path.dirname(script_path),
                        capture_output=True,
                        text=True
                    )
                    
                    if compile_result.returncode != 0:
                        self.log_script(f"Compilation Failed:\n{compile_result.stderr}")
                        self.update_progress("Compilation failed", False)
                        return
                    else:
                        self.log_script("Compilation Successful.\n")
                
                # Execution Step
                # Use Popen for interactive input
                process = subprocess.Popen(
                    run_cmd,
                    cwd=self.project_path if self.project_path else os.path.dirname(script_path),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=0,
                    universal_newlines=False # Binary mode for buffering control
                )
                
                if self.output_panels:
                    self.output_panels.running_process = process
                    self.output_panels.update_input_state(True)
                
                # Output reading threads (same as before)
                def read_output(pipe, is_stderr=False):
                    try:
                        for line in iter(pipe.readline, b''):
                            if process.poll() is not None and not line:
                                break
                            try:
                                line_str = line.decode('utf-8', errors='replace')
                            except:
                                line_str = str(line)
                                
                            # Convert line endings
                            line_str = line_str.replace('\r\n', '\n')
                            
                            self.root.after(0, lambda m=line_str: self.log_script(m))
                    except Exception as e:
                        pass
                    finally:
                        pipe.close()

                import threading
                t1 = threading.Thread(target=read_output, args=(process.stdout, False), daemon=True)
                t2 = threading.Thread(target=read_output, args=(process.stderr, True), daemon=True)
                t1.start()
                t2.start()
                
                returncode = process.wait()
                
                if self.output_panels:
                    self.output_panels.process_terminated = True
                    self.output_panels.update_input_state(False)
                
                status = "successfully" if returncode == 0 else "with errors"
                self.update_progress(f"Execution finished {status}", False)
                
                if returncode != 0 and returncode != -1: # -1 might be killed
                    self.log_script(f"\n[Process exited with code {returncode}]")
                elif returncode == 0:
                    self.log_script("\n[Process completed successfully]")
                    
            except Exception as e:
                self.log_script(f"Error: {e}")
                self.update_progress("Execution error", False)
                import traceback
                traceback.print_exc()
            finally:
                self.is_running_agent = False
        
        threading.Thread(target=worker, daemon=True).start()
    
    def run_without_input(self, target_path, target_name):
        """Run script without waiting for input (for test mode)"""
        try:
            # Read script and remove input() calls
            with open(target_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace input() with mock values
            import re
            # Simple pattern to find input() calls
            content = re.sub(r'input\s*\(\s*[\"\']?.*?[\"\']?\s*\)', '"test"', content)
            
            # Write temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            # Run modified script
            result = subprocess.run(
                ["python", tmp_path],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            # Show results
            if self.output_panels:
                self.output_panels.clear_script_output()
                self.log_script(f"Running {target_name} in test mode (input removed):\n")
                self.log_script(result.stdout)
                if result.stderr:
                    self.log_script(f"\nErrors:\n{result.stderr}")
                
        except Exception as e:
            self.log_script(f"Test mode error: {e}")
            import traceback
            traceback.print_exc()
    
    def debug_script(self):
        """Debug current script"""
        self.save_all_open_files()
        
        if not self.project_path:
            self.show_message("No Project", "Please open a project first.")
            return
        
        target = "main.py"
        if self.editor_tabs:
            current_file = self.editor_tabs.get_current_file()
            if current_file and current_file.endswith('.py'):
                target = os.path.basename(current_file)
        
        def worker():
            try:
                self.update_progress(f"Debugging {target}...", True)
                result = subprocess.run(
                    ["python", "-m", "pdb", target],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if self.output_panels:
                    self.output_panels.clear_script_output()
                    self.log_script(result.stdout)
                    if result.stderr:
                        self.log_script(f"Debug errors:\n{result.stderr}")
                
                self.update_progress("Debug session ended", False)
            except Exception as e:
                self.log_script(f"Debug error: {e}")
                self.update_progress("Debug error", False)
        
        threading.Thread(target=worker, daemon=True).start()
    
    def update_cursor_position(self, line, column):
        """Update cursor position in status bar"""
        self.position_label.config(text=f"Ln {line}, Col {column}")
    
    def update_file_label(self, filename):
        """Update current file label"""
        if filename:
            self.file_label.config(text=f"📄 {os.path.basename(filename)}")
        else:
            self.file_label.config(text="No file")
    
    def update_progress(self, message, show_bar=True):
        """Update progress bar and status"""
        def update():
            try:
                self.status_label.config(text=message)
                short_msg = message[:40] + "..." if len(message) > 40 else message
                self.progress_text.config(text=short_msg)
                self.progress_bar.start() if show_bar else self.progress_bar.stop()
            except:
                pass
        self.root.after(0, update)
    
    def clear_progress(self):
        """Clear progress bar"""
        self.update_progress("Ready", False)
    
    def log_ai(self, message):
        """Log message to AI output and chat panel"""
        if self.output_panels:
            self.output_panels.log_ai(message)
        # Pipe to chat for visibility
        self.log_ai_to_chat("System", message)

    def log_ai_to_chat(self, sender, message):
        """Pipe agent progress/actions to the AI Chat Panel"""
        if self.ai_panel:
            self.ai_panel.add_chat_message(sender, message)
    
    def log_debug(self, message):
        """Log message to debug console"""
        if self.output_panels:
            self.output_panels.log_debug(message)
            
    def log_script(self, message):
        """Log message to script output (thread-safe)"""
        if self.output_panels:
            self.output_panels.log_script(message)
    
    def show_message(self, title, message):
        """Show message box"""
        messagebox.showinfo(title, message)
    
    def open_documentation(self):
        """Open documentation"""
        webbrowser.open("https://github.com/your-repo/ai-dev-ide")
    
    def open_openai_key(self):
        """Open OpenAI API key page"""
        webbrowser.open("https://platform.openai.com/api-keys")
    
    def toggle_test_mode(self):
        """Toggle test mode (remove input statements)"""
        test_mode = self.test_mode_var.get()
        self.settings["test_mode_no_input"] = test_mode
        save_settings(self.settings)
        status = "enabled" if test_mode else "disabled"
        self.log_ai(f"🧪 Test mode {status} - input() statements will be removed when running scripts")
    
    def cleanup_repo(self):
        """Cleanup repository (pycache, etc)"""
        if not self.project_path: return
        
        count = 0
        for root, dirs, files in os.walk(self.project_path):
            for d in list(dirs):
                if d == "__pycache__":
                    shutil.rmtree(os.path.join(root, d))
                    count += 1
            for f in files:
                if f.endswith(".pyc") or f.endswith(".pyo"):
                    os.remove(os.path.join(root, f))
                    count += 1
        
        self.log_ai(f"✨ Cleaned up {count} items.")
        self.show_message("Cleanup Complete", f"Removed {count} temporary items.")

    def restructure_project(self):
        """AI-powered project restructuring"""
        if not self.project_path: return
        self.update_progress("Analyzing project structure...", True)
        
        def worker():
            try:
                # This would call an agent to suggest a better structure
                self.log_ai("🤖 Project restructuring agent is initializing...")
                # For now, just a placeholder message
                import time
                time.sleep(1)
                self.update_progress("Restructuring suggestion ready.", False)
                self.log_ai("💡 Suggestion: Group core logic into a 'core/' folder and UI into 'gui/'.")
            except: pass
            
        threading.Thread(target=worker, daemon=True).start()

    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About AI Dev IDE", 
                          "AI Dev IDE v2.0\n\n"
                          "An integrated development environment with AI assistance.\n"
                          "Features:\n"
                          "- AI code generation and review\n"
                          "- Test automation\n"
                          "- GitHub integration\n"
                          "- Multiple AI providers\n"
                          "- Syntax highlighting\n"
                          "- Interactive script execution\n\n"
                          "© 2024 AI Dev IDE Team")
    
    def save_current_file(self):
        """Save the current file"""
        if self.editor_tabs:
            saved_path = self.editor_tabs.save_current_file()
            if saved_path:
                self.show_message("Success", f"Saved {os.path.basename(saved_path)}")
                # Run linter on save
                self.run_linter(saved_path)
                
    def run_linter(self, file_path=None):
        """Run linter on file"""
        if not file_path:
            if self.editor_tabs:
                file_path = self.editor_tabs.get_current_file()
            
        if not file_path or not os.path.exists(file_path) or not getattr(self, 'linter', None):
            return
            
        def worker():
            try:
                issues = self.linter.lint_file(file_path)
                if self.output_panels:
                    self.root.after(0, lambda: self.output_panels.update_problems(issues))
            except Exception as e:
                print(f"Linting error: {e}")
            
        threading.Thread(target=worker, daemon=True).start()

    def stop_agent(self):
        """Stop current running AI agent task"""
        if self.is_running_agent:
            self.stop_event.set()
            self.is_running_agent = False
            self.update_progress("AI Agent stopped.", False)
            self.log_ai("⏹️ AI Agent task cancelled by user.")
            if self.ai_panel:
                self.ai_panel.add_chat_message("System", "Task cancelled.")
            
            # Ask for rollback
            self.root.after(500, self.prompt_rollback)

    def prompt_rollback(self):
        """Ask user if they want to roll back changes after cancellation or error"""
        if not hasattr(self, 'agent_file_backups') or not self.agent_file_backups:
            return
            
        if messagebox.askyesno("Rollback Changes?", "The task was cancelled or failed. Do you want to roll back any changes made to your files?"):
            self.rollback_files()

    def backup_files(self, files):
        """Create temporary backups of files before modification"""
        self.agent_file_backups = {}
        for f in files:
            full_path = os.path.join(self.project_path, f) if not os.path.isabs(f) else f
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as fh:
                        self.agent_file_backups[full_path] = fh.read()
                except Exception as e:
                    self.log_ai(f"⚠️ Could not backup {f}: {e}")

    def rollback_files(self):
        """Restore files from backup"""
        if not hasattr(self, 'agent_file_backups') or not self.agent_file_backups:
            self.log_ai("ℹ️ No backups available for rollback.")
            return
            
        restored = 0
        for full_path, content in self.agent_file_backups.items():
            try:
                with open(full_path, 'w', encoding='utf-8') as fh:
                    fh.write(content)
                
                # Update editor if open
                if self.editor_tabs:
                    self.editor_tabs.update_file_content(full_path, content)
                restored += 1
            except Exception as e:
                self.log_ai(f"❌ Error restoring {full_path}: {e}")
                
        if restored > 0:
            self.log_ai(f"⏪ Restored {restored} files to their previous state.")
            if self.project_tree:
                self.project_tree.refresh()
            messagebox.showinfo("Rollback", f"Successfully restored {restored} files.")
            self.agent_file_backups = {}
        else:
            messagebox.showwarning("Rollback", "No files were restored.")

    def on_global_hotkey(self):
        """Called when global hotkey is triggered"""
        print("Global Hotkey Action!")
        # 1. Capture content
        if self.clipboard_manager:
            content = self.clipboard_manager.get_content()
            if content:
                # 2. Format for chat
                path_or_text, display_text = self.clipboard_manager.format_for_chat(content)
                
                # 3. Bring window to front
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                
                # 4. Insert into AI Panel
                if self.ai_panel:
                    if content["type"] == "text":
                         self.ai_panel.set_input(path_or_text)
                    elif content["type"] == "image":
                         self.ai_panel.attached_files.append(path_or_text)
                         self.ai_panel.add_chat_message("System", f"📸 Captured Image from Clipboard")
                    elif content["type"] == "files":
                         # path_or_text is a formatted string for chat
                         self.ai_panel.set_input(path_or_text)

    def reference_selection(self):
        """Get selection from focused widget and add to AI chat"""
        try:
            focused = self.root.focus_get()
            if not focused: return
            
            selection = ""
            # Handle standard widgets
            if isinstance(focused, (tk.Text, tk.Entry)):
                try:
                    selection = focused.get(tk.SEL_FIRST, tk.SEL_LAST)
                except tk.TclError:
                    pass
            # Handle specialized widgets like our editor
            elif hasattr(focused, 'get_text_selection'):
                selection = focused.get_text_selection()
            
            if selection and self.ai_panel:
                # Bring window to front
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                
                # Format and insert
                formatted = f"\n[Reference]:\n```\n{selection}\n```\n"
                
                # Clear placeholder if needed
                input_text = self.ai_panel.text_input.get("1.0", "end-1c")
                if input_text == self.ai_panel.placeholder:
                    self.ai_panel.text_input.delete("1.0", tk.END)
                    self.ai_panel.text_input.config(fg="#ffffff")
                
                self.ai_panel.text_input.insert(tk.END, formatted)
                self.ai_panel.text_input.focus_set()
                self.ai_panel.text_input.see(tk.END)
        except Exception as e:
            print(f"Error referencing selection: {e}")

    def on_close(self):
        """Handle window close"""
        # Cancel auto-save timer
        if self.auto_save_id:
            self.root.after_cancel(self.auto_save_id)
            
        # Stop automation
        if hasattr(self, 'automation_manager') and self.automation_manager:
            self.automation_manager.stop_scheduler()

        # Stop hotkey manager
        if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
            self.hotkey_manager.stop()
        
        # Save current theme
        if self.theme_engine:
            self.settings["theme"] = self.theme_engine.color_map
        save_settings(self.settings)
        if self.layout_manager:
            try:
                self.layout_manager.save_layout()
            except Exception:
                pass
        
        # Save any open files
        self.save_all_open_files()
        
        # Close the window
        self.root.destroy()

    def play_agent_done_sound(self):
        try:
            import os
            path = self.settings.get("agent_done_sound", "").strip()
            vol = int(self.settings.get("agent_done_volume", 80))
            if path and os.path.exists(path):
                try:
                    self.play_media(path, vol)
                    return
                except Exception:
                    pass
            import winsound
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                winsound.Beep(800, 200)
        except Exception:
            pass

    def play_media(self, path, volume=80):
        try:
            import ctypes
            import ctypes.wintypes as wt
            alias = "ide_sound"
            mciSendString = ctypes.windll.winmm.mciSendStringW
            buf = wt.WCHAR * 255
            mciSendString(f"close {alias}", None, 0, 0)
            mciSendString(f"open \"{path}\" type mpegvideo alias {alias}", None, 0, 0)
            v = max(0, min(100, int(volume)))
            mciSendString(f"setaudio {alias} volume to {int(v*10)}", None, 0, 0)
            mciSendString(f"play {alias}", None, 0, 0)
        except Exception:
            try:
                import os
                os.startfile(path)
            except Exception:
                pass

    def open_existing_project_path(self, folder):
        """Open a project from a specific path (helper for GitPanel)"""
        if not folder or not os.path.exists(folder):
            return
            
        self.project_path = folder
        if self.project_tree:
            self.project_tree.load_project(folder)
        self.ensure_project_docs()
        self.log_ai(f"📂 Loaded project: {os.path.basename(folder)}")
        
        main_path = os.path.join(folder, "main.py")
        if os.path.exists(main_path) and self.editor_tabs:
            self.editor_tabs.open_file(main_path)
            
def main():
    """Main entry point"""
    root = tk.Tk()
    app = AIDevIDE(root)
    root.mainloop()

if __name__ == "__main__":
    main()
