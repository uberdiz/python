#!/usr/bin/env python3
"""
Launcher for AI Dev IDE
"""
import os
import sys
import subprocess
import logging
import time
from utils import get_resource_path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory or MEIPASS to the Python path
if getattr(sys, 'frozen', False):
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def launch_rescue_console(error_log):
    """Launch a simplified rescue console for manual/AI repair when main IDE fails."""
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
    import threading
    
    rescue_root = tk.Tk()
    rescue_root.title("AI Dev IDE - Rescue Console")
    rescue_root.geometry("800x600")
    
    # Header
    header = tk.Label(rescue_root, text="Rescue Mode: The IDE failed to start.", font=("Segoe UI", 14, "bold"), fg="red")
    header.pack(pady=10)
    
    # Error Display
    err_label = tk.Label(rescue_root, text="Startup Error:")
    err_label.pack(anchor="w", padx=10)
    err_text = scrolledtext.ScrolledText(rescue_root, height=8)
    err_text.insert("1.0", error_log)
    err_text.configure(state="disabled")
    err_text.pack(fill="x", padx=10, pady=5)
    
    # AI Repair Section
    ai_frame = ttk.LabelFrame(rescue_root, text="AI Repair / Coding")
    ai_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    prompt_label = tk.Label(ai_frame, text="Ask AI to fix the crash or modify code:")
    prompt_label.pack(anchor="w", padx=5, pady=5)
    
    prompt_entry = tk.Entry(ai_frame)
    prompt_entry.pack(fill="x", padx=5, pady=5)
    prompt_entry.insert(0, "Analyze the startup error and provide a fix for the IDE files.")
    
    status_var = tk.StringVar(value="Ready")
    status_label = tk.Label(ai_frame, textvariable=status_var, font=("Segoe UI", 9, "italic"))
    status_label.pack(pady=5)
    
    def run_repair():
        user_prompt = prompt_entry.get()
        status_var.set("🧠 AI is working...")
        
        def worker():
            try:
                from core.llm import call_llm
                from app import load_settings
                
                settings = load_settings()
                provider = settings.get("api_provider", "openai")
                api_url, model, token = settings.get(f"{provider}_url", ""), settings.get(f"{provider}_model", ""), settings.get(f"{provider}_token", "")
                
                if not token:
                    rescue_root.after(0, lambda: messagebox.showerror("No API Token", f"Please set {provider}_token in settings.json"))
                    return

                project_path = os.getcwd()
                
                full_prompt = f"""THE IDE FAILED TO START.
                
ERROR:
{error_log}

USER REQUEST:
{user_prompt}

FILES IN PROJECT ROOT:
{', '.join(os.listdir(project_path)[:20])}

Please provide a fix. 
RESPONSE FORMAT:
[ANALYSIS]
Your analysis
[FIX: filename.py]
```python
FULL CORRECTED CODE
```
"""
                response = call_llm(full_prompt, api_url, model, provider, token)
                
                if "[FIX:" in response:
                    import re
                    fix_match = re.search(r'\[FIX:\s*(.*?)\]\s*```(?:python)?\s*(.*?)\s*```', response, re.DOTALL)
                    if fix_match:
                        fname = fix_match.group(1).strip()
                        code = fix_match.group(2).strip()
                        target_path = os.path.join(project_path, os.path.basename(fname))
                        
                        if os.path.exists(target_path):
                            # Backup
                            with open(target_path + ".bak", 'w', encoding='utf-8') as b:
                                with open(target_path, 'r', encoding='utf-8') as original:
                                    b.write(original.read())
                            
                            with open(target_path, 'w', encoding='utf-8') as f:
                                f.write(code)
                            
                            rescue_root.after(0, lambda: messagebox.showinfo("Fix Applied", f"Applied fix to {fname}. Restarting..."))
                            rescue_root.after(0, lambda: (rescue_root.destroy(), subprocess.Popen([sys.executable] + sys.argv), sys.exit(0)))
                        else:
                            rescue_root.after(0, lambda: messagebox.showwarning("File Not Found", f"Could not find {fname} to apply fix."))
                else:
                    rescue_root.after(0, lambda: messagebox.showinfo("AI Response", response[:1000]))
            
            except Exception as e:
                rescue_root.after(0, lambda: messagebox.showerror("Repair Error", str(e)))
            finally:
                rescue_root.after(0, lambda: status_var.set("Ready"))
        
        threading.Thread(target=worker, daemon=True).start()

    repair_btn = ttk.Button(ai_frame, text="Ask AI to Fix", command=run_repair)
    repair_btn.pack(pady=10)
    
    # Manual Exit
    exit_btn = ttk.Button(rescue_root, text="Exit", command=rescue_root.destroy)
    exit_btn.pack(side="bottom", pady=20)
    
    rescue_root.mainloop()

def main_launcher():
    """Main entry point for the launcher."""
    try:
        logger.info("Starting AI Dev IDE...")
        
        logger.info(f"Current directory: {os.getcwd()}")
        
        # Hardware detection
        try:
            from utils.hardware_info import get_gpu_info
            gpu = get_gpu_info()
            if gpu["has_nvidia"]:
                logger.info(f"🚀 Hardware: {gpu['details']}")
                if gpu["cuda_available"]:
                    logger.info("✅ CUDA acceleration is available for local models.")
            else:
                logger.info("ℹ️ Hardware: Using CPU (No NVIDIA GPU detected)")
        except Exception as e:
            logger.warning(f"Hardware check skipped: {e}")

        # Standard launch (Tkinter-based Main IDE)
        # We skip the PySide placeholder by default as it's not the main application
        try:
            logger.info("Launching AI Dev IDE (Tkinter)...")
            from app import main
            main()
        except Exception as e:
            logger.critical(f"Failed to launch main application: {e}")
            
            # Diagnostic / Self-Repair Mode
            logger.info("🔧 Entering Self-Repair Mode...")
            import traceback
            error_log = traceback.format_exc()
            
            # Launch Rescue Console
            try:
                launch_rescue_console(error_log)
            except Exception as rescue_err:
                logger.error(f"Failed to launch rescue console: {rescue_err}")
                # Fallback to simple AI fix attempt (existing logic)
                try:
                    from core.llm import call_llm
                    from app import load_settings
                    # ... rest of the existing repair logic ...
                except:
                    pass
            
            # Fallback to PySide only if Tkinter fails (unlikely)
            logger.info("Attempting fallback to PySide GUI...")
            try:
                import importlib.util
                spec6 = importlib.util.find_spec("PySide6")
                spec2 = importlib.util.find_spec("PySide2")
                if spec6 or spec2:
                    from gui.pyside_app import launch
                    app = launch()
                    sys.exit(app.exec())
            except Exception as e2:
                logger.error(f"Fallback also failed: {e2}")
                raise e
    except Exception as e:
        logger.critical(f"Critical error in launcher: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_launcher()
