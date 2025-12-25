"""
Output Panels for script and AI output with tkterminal integration - ULTIMATE FIX
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import sys
import threading
import queue
import time
import subprocess
import platform
import traceback

# Try to import tkterminal at module level
try:
    from tkterminal import Terminal
    TKTERMINAL_AVAILABLE = True
except ImportError:
    TKTERMINAL_AVAILABLE = False
    print("tkterminal not installed. Run: pip install tkterminal")
except Exception as e:
    TKTERMINAL_AVAILABLE = False
    print(f"Error importing tkterminal: {e}")

if TKTERMINAL_AVAILABLE:
    class FixedTerminal(Terminal):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Fix for tkterminal crash: ensure _limit_backspace is an int
            if not hasattr(self, '_limit_backspace') or self._limit_backspace is None:
                self._limit_backspace = 0
            
        def _on_keypress(self, event):
            # Safe wrapper for keypress to prevent NoneType errors
            try:
                if not hasattr(self, '_limit_backspace') or self._limit_backspace is None:
                    self._limit_backspace = 0
                return super()._on_keypress(event)
            except Exception:
                return "break"
else:
    class FixedTerminal(tk.Text):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            self.shell = False
            self.basename = "AI-IDE"

class BottomPanel:
    def __init__(self, parent_pane, app):
        self.app = app
        self.running_process = None
        self.current_working_dir = None
        self.process_terminated = False
        self.terminal_available = TKTERMINAL_AVAILABLE
        self.terminal = None
        self.terminal_text = None
        self.script_output = None # Initialize to avoid AttributeError
        
        self.notebook = ttk.Notebook(parent_pane)
        if hasattr(parent_pane, 'add'):
            parent_pane.add(self.notebook, weight=1)
        else:
            self.notebook.pack(fill="both", expand=True)
            
        # --- PROBLEMS TAB ---
        problems_frame = ttk.Frame(self.notebook)
        self.notebook.add(problems_frame, text="⚠ PROBLEMS")
        
        self.problems_tree = ttk.Treeview(problems_frame, columns=("File", "Line", "Message"), show="headings")
        self.problems_tree.heading("File", text="File")
        self.problems_tree.heading("Line", text="Line")
        self.problems_tree.heading("Message", text="Message")
        self.problems_tree.column("File", width=150)
        self.problems_tree.column("Line", width=50)
        self.problems_tree.column("Message", width=400)
        self.problems_tree.pack(fill="both", expand=True)
        
        # --- OUTPUT TAB ---
        output_frame = ttk.Frame(self.notebook)
        self.notebook.add(output_frame, text="📝 OUTPUT")
        
        self.general_output = scrolledtext.ScrolledText(
            output_frame, wrap="word", bg="#0c0c0c", fg="#cccccc",
            insertbackground="#ffffff", font=("Consolas", 10), height=10
        )
        self.general_output.pack(fill="both", expand=True)
        
        # --- DEBUG CONSOLE TAB ---
        debug_frame = ttk.Frame(self.notebook)
        self.notebook.add(debug_frame, text="🐞 DEBUG CONSOLE")
        
        self.debug_output = scrolledtext.ScrolledText(
            debug_frame, wrap="word", bg="#0c0c0c", fg="orange",
            insertbackground="#ffffff", font=("Consolas", 10), height=10
        )
        self.debug_output.pack(fill="both", expand=True)
        self.debug_output.insert("end", "Debug Console ready.\n")
        
        # Debug Input
        debug_input_frame = ttk.Frame(debug_frame)
        debug_input_frame.pack(fill="x", padx=2, pady=2)
        
        ttk.Label(debug_input_frame, text="Input:").pack(side="left")
        self.debug_input = ttk.Entry(debug_input_frame)
        self.debug_input.pack(side="left", fill="x", expand=True, padx=5)
        self.debug_input.bind("<Return>", self.send_debug_input)
        
        # --- TERMINAL TAB (Original Script/Terminal Logic) ---
        terminal_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(terminal_tab_frame, text=">_ TERMINAL")
        self.setup_terminal_tab(terminal_tab_frame)
        
        # --- PORTS TAB ---
        ports_frame = ttk.Frame(self.notebook)
        self.notebook.add(ports_frame, text="🔌 PORTS")
        
        self.ports_tree = ttk.Treeview(ports_frame, columns=("Port", "PID", "Process"), show="headings")
        self.ports_tree.heading("Port", text="Port")
        self.ports_tree.heading("PID", text="PID")
        self.ports_tree.heading("Process", text="Process")
        self.ports_tree.pack(fill="both", expand=True)
        
        # Select Terminal by default
        self.notebook.select(terminal_tab_frame)

    def setup_terminal_tab(self, parent_frame):
        """Setup the terminal interface inside the tab"""
        # (This contains the logic previously in __init__ for the script/terminal tab)
        script_frame = parent_frame
        
        if self.terminal_available:
            try:
                # Create main container with paned window for flexibility
                main_container = ttk.Panedwindow(script_frame, orient="vertical")
                main_container.pack(fill="both", expand=True, padx=2, pady=2)
                
                # Terminal frame
                terminal_frame = ttk.Frame(main_container)
                main_container.add(terminal_frame, weight=1)
                
                # Initialize terminal with our fixed version
                self.terminal = FixedTerminal(
                    terminal_frame,
                    height=15,
                    width=80,
                    bg="#0c0c0c",
                    fg="#ffffff",
                    font=("Consolas", 10),
                    cursor="xterm",
                    insertbackground="white",
                    insertwidth=8,
                    borderwidth=2,
                    relief="sunken"
                )
                self.terminal.pack(fill="both", expand=True, padx=0, pady=0)
                
                # Configure terminal
                self.terminal.configure(
                    bg="#0c0c0c",
                    fg="#ffffff",
                    insertbackground="#ffffff"
                )
                
                # Set up terminal shell properties
                self.terminal.shell = True
                self.terminal.basename = "AI-IDE"
                
                # Input frame for fallback (always available but hidden initially)
                self.input_frame = ttk.Frame(main_container)
                main_container.add(self.input_frame, weight=0)
                
                ttk.Label(self.input_frame, text="Input:", width=6).pack(side="left", padx=(5,2))
                self.input_entry = ttk.Entry(self.input_frame, width=50, font=("Consolas", 10))
                self.input_entry.pack(side="left", fill="x", expand=True, padx=2)
                self.input_entry.bind("<Return>", self.send_input)
                
                self.send_button = ttk.Button(self.input_frame, text="Send", command=self.send_input, 
                                             state="disabled", width=8)
                self.send_button.pack(side="left", padx=2)
                
                self.input_status = ttk.Label(self.input_frame, text="", foreground="gray", font=("Arial", 8))
                self.input_status.pack(side="left", padx=5)
                
                # Hide input frame initially (only show for scripts that need input)
                self.input_frame.pack_forget()
                
                # Set initial working directory
                if self.app.project_path and os.path.exists(self.app.project_path):
                    self.current_working_dir = self.app.project_path
                    os.chdir(self.current_working_dir)
                    self.update_terminal_prompt()
                
                self.log_script("Terminal ready. Type 'help' for commands.")
                self.log_script("To run a script, type: python your_script.py")
                
            except Exception as e:
                print(f"Terminal initialization error: {e}")
                traceback.print_exc()
                self.terminal = None
                self.terminal_available = False
        else:
            self.terminal = None
        
        # Fallback to regular text widget if terminal not available
        if not self.terminal_available or not self.terminal:
            # Create container for fallback mode
            fallback_container = ttk.Panedwindow(script_frame, orient="vertical")
            fallback_container.pack(fill="both", expand=True, padx=2, pady=2)

    def set_font_size(self, size):
        try:
            if self.general_output:
                self.general_output.configure(font=("Consolas", size))
            if self.debug_output:
                self.debug_output.configure(font=("Consolas", size))
            if self.terminal and hasattr(self.terminal, 'configure'):
                try:
                    self.terminal.configure(font=("Consolas", size))
                except Exception:
                    pass
            if hasattr(self, 'input_entry') and self.input_entry:
                self.input_entry.configure(font=("Consolas", size))
        except Exception:
            pass
            
            # Output area
            output_frame = ttk.Frame(fallback_container)
            fallback_container.add(output_frame, weight=1)
            
            self.script_output = scrolledtext.ScrolledText(
                output_frame,
                wrap="word",
                bg="#0c0c0c",
                fg="#cccccc",
                insertbackground="#ffffff",
                font=("Consolas", 10),
                state="normal",
                height=15
            )
            self.script_output.pack(fill="both", expand=True, padx=0, pady=0)
            
            # Input area (for user input)
            self.input_frame = ttk.Frame(fallback_container)
            fallback_container.add(self.input_frame, weight=0)
            
            ttk.Label(self.input_frame, text="Input:", width=6).pack(side="left", padx=(5,2))
            self.input_entry = ttk.Entry(self.input_frame, width=50, font=("Consolas", 10))
            self.input_entry.pack(side="left", fill="x", expand=True, padx=2)
            self.input_entry.bind("<Return>", self.send_input)
            
            self.send_button = ttk.Button(self.input_frame, text="Send", command=self.send_input, 
                                         state="disabled", width=8)
            self.send_button.pack(side="left", padx=2)
            
            self.input_status = ttk.Label(self.input_frame, text="", foreground="gray", font=("Arial", 8))
            self.input_status.pack(side="left", padx=5)
            
            self.log_script("Standard output mode (tkterminal not available)")
            self.log_script("To run a script, click the 'Run Script' button")
        
        # Control buttons (Moved to right side of terminal tab or similar, skipping specific placement for now to keep it simple)
        button_frame = ttk.Frame(script_frame)
        button_frame.pack(side="bottom", fill="x", padx=2, pady=2)
        
        ttk.Button(button_frame, text="🗑️ Clear", 
                  command=self.clear_script_output).pack(side="left", padx=2)
        ttk.Button(button_frame, text="⏹️ Stop", 
                  command=self.stop_script).pack(side="left", padx=2)
        if self.terminal_available and self.terminal:
            ttk.Button(button_frame, text="↻ Restart", 
                       command=self.restart_terminal).pack(side="left", padx=2)
                       
        # Context menus for terminal/output
        self.create_context_menu()

    def create_context_menu(self):
        """Create context menu for terminal/output"""
        self.context_menu = tk.Menu(self.notebook, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self.copy_selection)
        self.context_menu.add_command(label="Send to AI", command=self.send_selection_to_ai)
        
        # Bind right click to terminal fallback
        if self.script_output:
            self.script_output.bind("<Button-3>", self.show_context_menu)
        
        if self.terminal_available and self.terminal:
            try:
                # Bind to the text widget inside FixedTerminal (it inherits from Text)
                self.terminal.bind("<Button-3>", self.show_context_menu)
            except:
                pass
                
    def show_context_menu(self, event):
        """Show context menu"""
        try:
            self.context_menu.post(event.x_root, event.y_root)
        except:
            pass
            
    def copy_selection(self):
        """Copy selected text"""
        try:
            widget = self.notebook.select() # This gives frame name
            # We need the focused widget
            focused = self.app.root.focus_get()
            if isinstance(focused, (tk.Text, scrolledtext.ScrolledText)):
                focused.event_generate("<<Copy>>")
        except:
            pass

    def send_selection_to_ai(self):
        """Send selected text to AI panel"""
        try:
            text = ""
            focused = self.app.root.focus_get()
            
            if isinstance(focused, (tk.Text, scrolledtext.ScrolledText)):
                try:
                    text = focused.get("sel.first", "sel.last")
                except:
                    pass
            
            if text and self.app.ai_panel:
                self.app.ai_panel.set_input(text)
                # Switch to AI tab if possible?
                # self.app.switch_sidebar("ai") 
                self.app.toggle_ai_panel() # Ensure it's visible
        except Exception as e:
            print(f"Error sending to AI: {e}")
    
    def update_terminal_prompt(self):
        """Update terminal prompt to show current directory"""
        if not self.terminal_available or not self.terminal:
            return
        
        try:
            # Clear and set new prompt
            if self.current_working_dir:
                dir_name = os.path.basename(self.current_working_dir)
                self.terminal.basename = dir_name[:20]  # Truncate if too long
            else:
                self.terminal.basename = "AI-IDE"
        except:
            pass
    
    def set_terminal_directory(self):
        """Manually set terminal directory"""
        if not self.terminal_available:
            return
        
        folder = tk.filedialog.askdirectory(title="Select Terminal Working Directory")
        if folder and os.path.exists(folder):
            self.current_working_dir = folder
            os.chdir(folder)
            self.update_terminal_prompt()
            self.log_script(f"Working directory set to: {folder}")
    
    def run_script_in_terminal(self, script_path, working_dir=None):
        """Run a script - SIMPLIFIED VERSION that actually works"""
        # Always use the simple method that works
        return self.run_script_simple(script_path, working_dir)
    
    def run_script_simple(self, script_path, working_dir=None):
        """Simple, reliable method to run scripts with Multi-Language Support"""
        if not working_dir:
            working_dir = self.app.project_path or os.path.dirname(script_path)
        
        if not working_dir or not os.path.exists(working_dir):
            self.log_script(f"Error: Working directory does not exist: {working_dir}")
            return False
        
        script_name = os.path.basename(script_path)
        script_in_dir = os.path.join(working_dir, script_name)
        
        # Check if script exists
        if not os.path.exists(script_in_dir):
            # Try to copy it there if it's from elsewhere? 
            # For now assume it's correct
            pass

        self.clear_script_output()
        self.log_script(f"Running: {script_name}")
        self.log_script(f"Directory: {working_dir}")
        self.log_script("-" * 40)
        
        # Determine command
        ext = os.path.splitext(script_path)[1].lower()
        run_cmd = None
        compile_cmd = None
        
        # Configuration
        runners = {
            '.py': ["python", "-u", script_name],
            '.lua': ["lua", script_name],
            '.js': ["node", script_name],
            '.ts': ["ts-node", script_name],
            '.cs': ["dotnet", "run"],
            '.sh': ["bash", script_name],
            '.bat': [script_name],
            '.ps1': ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_name],
            '.rb': ["ruby", script_name],
            '.pl': ["perl", script_name],
            '.php': ["php", script_name],
            '.go': ["go", "run", script_name],
            '.rs': ["cargo", "run"],
        }
        
        if ext == '.html':
            import webbrowser
            self.log_script(f"Opening {script_name} in browser...")
            webbrowser.open(f"file://{os.path.abspath(script_path)}")
            return True
            
        if ext == '.cpp' or ext == '.c':
            exe_name = os.path.splitext(script_name)[0]
            if os.name == 'nt': exe_name += ".exe"
            compiler = "g++" if ext == '.cpp' else "gcc"
            compile_cmd = [compiler, script_name, "-o", exe_name]
            run_cmd = [exe_name]
        elif ext in runners:
            run_cmd = runners[ext]
        else:
            self.log_script(f"Error: No runner configured for {ext}")
            return False
            
        try:
            # Compile first if needed
            if compile_cmd:
                self.log_script(f"Compiling: {' '.join(compile_cmd)}")
                compile_result = subprocess.run(
                    compile_cmd,
                    cwd=working_dir,
                    capture_output=True,
                    text=True
                )
                if compile_result.returncode != 0:
                    self.log_script(f"Compilation Failed:\n{compile_result.stderr}")
                    return False
                self.log_script("Compilation Successful.")

            # Run
            process = subprocess.Popen(
                run_cmd,
                cwd=working_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                universal_newlines=False
            )
            
            self.running_process = process
            self.process_terminated = False
            
            # Start threads to handle input/output
            # Use binary reading
            def read_output(pipe, is_stderr=False):
                try:
                    for line in iter(pipe.readline, b''):
                        if process.poll() is not None and not line:
                            break
                        try:
                            line_str = line.decode('utf-8', errors='replace')
                        except:
                            line_str = str(line)
                        
                        line_str = line_str.replace('\r\n', '\n')
                        self.app.root.after(0, lambda m=line_str: self.log_script(m))
                except Exception:
                    pass
                finally:
                    pipe.close()

            import threading
            t1 = threading.Thread(target=read_output, args=(process.stdout, False), daemon=True)
            t2 = threading.Thread(target=read_output, args=(process.stderr, True), daemon=True)
            t1.start()
            t2.start()
            
            # Enable input field
            self.update_input_state(True)
            
            return True
            
        except Exception as e:
            self.log_script(f"Error running script: {e}")
            traceback.print_exc()
            return False
    
    def read_process_output(self, process):
        """Read output from process and display it"""
        while True:
            if process.poll() is not None:
                break
            
            try:
                # Read line by line
                line = process.stdout.readline()
                if line:
                    line = line.rstrip('\n')
                    if line:
                        self.log_script(line)
                        
                        # Check if line looks like it's asking for input
                        if any(prompt in line.lower() for prompt in ['input', 'enter', ':', '?', '>']):
                            self.update_input_state(True)
                else:
                    time.sleep(0.01)
            except Exception as e:
                break
        
        # Process ended
        return_code = process.poll()
        if return_code is not None:
            status = "successfully" if return_code == 0 else f"with code {return_code}"
            self.log_script(f"\n[Script completed {status}]")
        
        self.running_process = None
        self.update_input_state(False)
    
    def send_input(self, event=None):
        """Send input to running script"""
        if not self.running_process or self.process_terminated:
            return
        
        if self.running_process.poll() is not None:
            self.process_terminated = True
            self.update_input_state(False)
            self.log_script("[Process has terminated]")
            return
        
        user_input = self.input_entry.get()
        # Allow sending empty lines (just Enter)
        
        self.input_entry.delete(0, tk.END)
        # Echo input to terminal
        self.log_script(f"{user_input}") 
        
        try:
            if self.running_process.stdin:
                # Process was started with universal_newlines=False (binary mode)
                # so we must send bytes
                input_bytes = (user_input + "\n").encode('utf-8')
                self.running_process.stdin.write(input_bytes)
                self.running_process.stdin.flush()
        except Exception as e:
            self.log_script(f"[Error sending input: {e}]")
    
    def update_input_state(self, waiting):
        """Update input field state"""
        # Always show input if process is running, regardless of 'waiting' detection
        is_running = self.running_process is not None and not self.process_terminated
        
        # Ensure input frame logic uses stored reference
        if not hasattr(self, 'input_frame'):
            return

        if is_running:
            # Show input frame
            self.input_frame.pack(side="bottom", fill="x", padx=5, pady=(0,5))
            
            # Enable input controls
            self.input_entry.config(state="normal")
            self.send_button.config(state="normal")
            self.input_status.config(text="Interactive Mode", foreground="green")
            if waiting:
                 self.input_entry.focus_set()
        else:
            # Hide input frame
            self.input_frame.pack_forget()
            
            # Disable input controls
            self.input_entry.config(state="disabled")
            self.send_button.config(state="disabled")
            self.input_status.config(text="Not Running", foreground="gray")
    
    def stop_script(self):
        """Stop the running script and its child processes"""
        if self.running_process:
            try:
                self.log_script("\n[Stopping script...]")
                
                # Kill process tree if possible
                if platform.system() == "Windows":
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.running_process.pid)], 
                                  capture_output=True)
                else:
                    import signal
                    os.killpg(os.getpgid(self.running_process.pid), signal.SIGTERM)
                
                self.running_process.terminate()
                self.running_process = None
                self.process_terminated = True
                self.log_script("[Script stopped by user]")
                self.update_input_state(False)
            except Exception as e:
                self.log_script(f"[Error stopping script: {e}]")
                # Fallback
                try:
                    self.running_process.kill()
                    self.running_process = None
                    self.process_terminated = True
                except: pass
    
    def restart_terminal(self):
        """Properly restart the terminal"""
        if self.terminal_available and self.terminal:
            try:
                # Stop any running process
                self.stop_script()
                
                # Get the parent of the terminal (terminal_frame)
                terminal_parent = self.terminal.master
                
                # Destroy current terminal
                self.terminal.destroy()
                
                # Recreate terminal in the same parent
                self.terminal = FixedTerminal(
                    terminal_parent,
                    height=15,
                    width=80,
                    bg="#0c0c0c",
                    fg="#ffffff",
                    font=("Consolas", 10),
                    cursor="xterm",
                    insertbackground="white",
                    insertwidth=8,
                    borderwidth=2,
                    relief="sunken"
                )
                self.terminal.pack(fill="both", expand=True, padx=0, pady=0)
                self.terminal.shell = True
                self.terminal.basename = "AI-IDE"
                
                # Re-bind context menu
                self.terminal.bind("<Button-3>", self.show_context_menu)
                
                # Restore working directory
                if self.current_working_dir and os.path.exists(self.current_working_dir):
                    os.chdir(self.current_working_dir)
                    self.update_terminal_prompt()
                
                self.log_script("Terminal restarted successfully!")
                self.log_script(f"Working directory: {self.current_working_dir or 'Not set'}")
                if self.app:
                    self.app.log_ai("💻 Terminal restarted.")
                self.app.log_ai("💻 Terminal restarted.")
                
            except Exception as e:
                self.log_script(f"Error restarting terminal: {e}")
                traceback.print_exc()
    
    def log_script(self, message):
        """Log message to script output"""
        if self.terminal_available and self.terminal:
            try:
                self.terminal.insert("end", f"{message}\n")
                self.terminal.see("end")
            except Exception as e:
                print(f"Error logging to terminal: {e}")
                if hasattr(self, 'script_output'):
                    self.script_output.config(state="normal")
                    self.script_output.insert("end", f"{message}\n")
                    self.script_output.see("end")
                    self.script_output.config(state="disabled")
        else:
            if hasattr(self, 'script_output'):
                self.script_output.config(state="normal")
                self.script_output.insert("end", f"{message}\n")
                self.script_output.see("end")
                self.script_output.config(state="disabled")
    
    def log_ai(self, message):
        """Log message to AI output"""
        # Redirect to general output for now
        self.general_output.insert("end", f"[AI] {message}\n")
        self.general_output.see("end")
    
    def clear_script_output(self):
        """Clear script output"""
        if self.terminal_available and self.terminal:
            try:
                self.terminal.delete("1.0", "end")
                self.update_terminal_prompt()
                self.terminal.insert("end", f"{self.terminal.basename}$ ")
                self.terminal.mark_set("insert", "end")
                self.terminal.see("end")
            except:
                pass
        else:
            if hasattr(self, 'script_output'):
                self.script_output.config(state="normal")
                self.script_output.delete("1.0", "end")
                self.script_output.config(state="disabled")
    
    def clear_ai_output(self):
        """Clear AI output"""
        self.general_output.delete("1.0", "end")
    
    def clear_all(self):
        """Clear all outputs"""
        self.clear_script_output()
        self.clear_ai_output()
        self.debug_output.delete("1.0", "end")
    
    def apply_theme(self, color_map):
        """Apply theme colors"""
        bg_color = color_map.get("console_bg", "#0c0c0c")
        fg_color = color_map.get("console_fg", "#cccccc")
        insert_color = color_map.get("text_insert", "#ffffff")
        success_color = color_map.get("console_success", "#4ec9b0")
        
        if self.terminal_available and self.terminal:
            try:
                self.terminal.configure(
                    bg=bg_color,
                    fg=color_map.get("console_fg", "#ffffff"),
                    insertbackground=insert_color
                )
            except:
                pass
        else:
            if hasattr(self, 'script_output'):
                self.script_output.configure(
                    bg=bg_color,
                    fg=fg_color,
                    insertbackground=insert_color
                )
        
        # Configure new tabs
        self.general_output.configure(
            bg=bg_color,
            fg=fg_color,
            insertbackground=insert_color
        )
        
        self.debug_output.configure(
            bg=bg_color,
            fg=color_map.get("console_warning", "orange"),
            insertbackground=insert_color
        )
    
    def update_problems(self, issues):
        """Update problems tab with issues list"""
        # Clear current items
        for item in self.problems_tree.get_children():
            self.problems_tree.delete(item)
            
        # Add new items
        for issue in issues:
            # issue: {'line': int, 'message': str, 'type': 'error'|'warning', 'file': str}
            
            # Map type to icon/color if possible (Treeview tags)
            tag = issue.get('type', 'info')
            
            values = (
                issue.get('file', 'Current File'), 
                issue.get('line', ''), 
                issue.get('message', '')
            )
            
            self.problems_tree.insert("", "end", values=values, tags=(tag,))
            
        # Configure tags
        self.problems_tree.tag_configure('error', foreground='#ff5555') # Red
        self.problems_tree.tag_configure('warning', foreground='#ffaa00') # Orange
        self.problems_tree.tag_configure('info', foreground='#aaaaaa') # Gray
        
        # Update tab text with count
        count = len(issues)
        if count > 0:
            self.notebook.tab(0, text=f"⚠ PROBLEMS ({count})")
        else:
            self.notebook.tab(0, text="⚠ PROBLEMS")
            
    def log_debug(self, message):
        """Log to debug console"""
        self.debug_output.insert("end", message)
        self.debug_output.see("end")
        
    def send_debug_input(self, event=None):
        """Send input to running debug process"""
        text = self.debug_input.get()
        self.debug_input.delete(0, "end")
        
        self.log_debug(f"> {text}\n")
        
        if self.running_process and not self.process_terminated:
            try:
                if self.running_process.stdin:
                    input_bytes = (text + "\n").encode('utf-8')
                    self.running_process.stdin.write(input_bytes)
                    self.running_process.stdin.flush()
            except Exception as e:
                self.log_debug(f"Input error: {e}\n")
        else:
            self.log_debug("No debugger running.\n")
