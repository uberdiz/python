"""
Editor Tabs with Syntax Highlighting - FIXED TAB CLOSING
"""
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Token

class EditorTabs(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.open_files = {}  # filename -> (text_widget, tab_id, original_hash)
        self.current_file = None
        self._ln_sched = {}
        self._quality_sched = {}
        self._suggest_popup = None
        self._spell_dict = set()
        self._init_spell_dict()
        
        self.setup_styles()
        
        self.setup_toolbar()
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.notebook.bind("<Button-3>", self.show_tab_menu)
        self.notebook.bind("<Button-2>", self.close_tab_under_cursor)  # Middle click to close
        self.notebook.bind("<Control-w>", self.close_current_tab)
        
        self.tab_menu = tk.Menu(self, tearoff=0)
        self.tab_menu.add_command(label="Close Tab", command=self.close_current_tab)
        self.tab_menu.add_command(label="Close Other Tabs", command=self.close_other_tabs)
        self.tab_menu.add_command(label="Close All Tabs", command=self.close_all_tabs)
        self.tab_menu.add_separator()
        self.tab_menu.add_command(label="Save Tab", command=self.save_current_file)
    
    def setup_toolbar(self):
        """Setup editor toolbar with optimization options"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=5, pady=2)
        
        ttk.Label(toolbar, text="Optimization:").pack(side="left", padx=5)
        
        self.opt_mode = tk.StringVar(value="Readability")
        ttk.Combobox(toolbar, textvariable=self.opt_mode, values=["Performance", "Readability", "Compact"], state="readonly", width=12).pack(side="left", padx=5)
        
        self.minify_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(toolbar, text="Minify", variable=self.minify_var).pack(side="left", padx=5)
        
        ttk.Button(toolbar, text="✨ Optimize Code", command=self.optimize_current_code).pack(side="left", padx=10)
        
        ttk.Button(toolbar, text="🤖 AI Edit", command=self.ai_edit_request).pack(side="left", padx=5)
        
    def ai_edit_request(self):
        """Request AI to edit current selection or whole file"""
        if not self.app: return
        self.app.ai_edit_active_editor()
        
    def get_selection_info(self):
        """Get current selection text and range"""
        if not self.current_file or self.current_file not in self.open_files:
            return None, None, None
        
        text_widget = self.open_files[self.current_file][0]
        try:
            if text_widget.tag_ranges("sel"):
                start = text_widget.index("sel.first")
                end = text_widget.index("sel.last")
                text = text_widget.get("sel.first", "sel.last")
                return text, start, end
            else:
                # No selection, return whole file
                return text_widget.get("1.0", "end-1c"), "1.0", "end-1c"
        except tk.TclError:
            return text_widget.get("1.0", "end-1c"), "1.0", "end-1c"

    def replace_range(self, start, end, new_text):
        """Replace a range of text in the active editor"""
        if not self.current_file or self.current_file not in self.open_files:
            return False
        
        text_widget = self.open_files[self.current_file][0]
        text_widget.delete(start, end)
        text_widget.insert(start, new_text)
        self.on_text_modified(self.current_file, text_widget)
        return True

    def optimize_current_code(self):
        """Send current code to AI for optimization"""
        if not self.current_file: return
        
        text_widget = self.open_files[self.current_file][0]
        code = text_widget.get("1.0", "end-1c")
        
        mode = self.opt_mode.get()
        minify = self.minify_var.get()
        
        prompt = f"Optimize the following code for {mode}. "
        if minify: prompt += "Also minify it. "
        prompt += f"\nCode:\n```{code}```"
        
        # Route to AI Panel
        if hasattr(self.app, 'ai_panel'):
            self.app.ai_panel.set_input(prompt)
            self.app.ai_panel.send_message()
    def setup_styles(self):
        """Setup custom styles"""
        style = ttk.Style()
        style.configure("Custom.TNotebook", background="#1e1e1e")
        style.configure("Custom.TNotebook.Tab", 
                       background="#2d2d30",
                       foreground="#cccccc",
                       padding=[15, 5])
        style.map("Custom.TNotebook.Tab",
                 background=[("selected", "#1e1e1e")],
                 foreground=[("selected", "#ffffff")])
    
    def create_editor(self, filename):
        """Create a new text editor widget"""
        frame = ttk.Frame(self.notebook)
        
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill="both", expand=True)
        
        line_numbers = tk.Text(
            text_frame,
            width=4,
            padx=3,
            takefocus=0,
            border=0,
            background="#1e1e1e",
            foreground="#858585",
            state='disabled',
            font=('Consolas', 11),
            wrap="none" # Line numbers should never wrap
        )
        line_numbers.pack(side="left", fill="y")
        
        text = tk.Text(
            text_frame,
            wrap="word",
            undo=True,
            maxundo=-1,
            font=('Consolas', 11),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#ffffff",
            selectbackground="#264f78",
            border=0,
            padx=10,
            pady=10
        )
        text.pack(side="left", fill="both", expand=True)
        
        def sync_yview(*args):
            text.yview(*args)
            line_numbers.yview_moveto(text.yview()[0])

        y_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=sync_yview)
        y_scroll.pack(side="right", fill="y")
        
        # Configure text to update line numbers on scroll
        def on_scroll(*args):
            y_scroll.set(*args)
            line_numbers.yview_moveto(args[0])
            self.update_line_numbers(text, line_numbers)

        text.configure(yscrollcommand=on_scroll)
        
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        x_scroll.pack(side="bottom", fill="x")
        text.configure(xscrollcommand=x_scroll.set)
        
        text.bind("<KeyRelease>", lambda e: self.on_text_modified(filename, text))
        text.bind("<Control-s>", lambda e: self.save_current_file())
        text.bind("<Control-f>", lambda e: self.find_text())
        text.bind("<Control-h>", lambda e: self.replace_text())
        
        # Line numbers updates
        text.bind("<Key>", lambda e: self._schedule_line_numbers(text, line_numbers))
        text.bind("<MouseWheel>", lambda e: self._schedule_line_numbers(text, line_numbers))
        text.bind("<Configure>", lambda e: self._schedule_line_numbers(text, line_numbers))
        
        text.bind("<KeyRelease>", lambda e: (self.update_cursor_position(text), self._schedule_quality_check(filename, text)), add="+")
        text.bind("<ButtonRelease>", lambda e: self.update_cursor_position(text))
        text.bind("<Control-space>", lambda e: self._trigger_autocomplete(text))
        text.bind("<Alt-Return>", lambda e: self._open_correction_popup(text))
        
        # Context menu for text area
        text_context_menu = tk.Menu(text, tearoff=0)
        text_context_menu.add_command(label="🤖 AI Edit Selection", command=self.ai_edit_request)
        text_context_menu.add_separator()
        text_context_menu.add_command(label="Cut", command=self.cut)
        text_context_menu.add_command(label="Copy", command=self.copy)
        text_context_menu.add_command(label="Paste", command=self.paste)
        
        def show_text_context_menu(event):
            text_context_menu.post(event.x_root, event.y_root)
            
        text.bind("<Button-3>", show_text_context_menu)
        
        return frame, text, line_numbers
    
    def open_file(self, filepath):
        """Open a file in a new tab"""
        try:
            # Normalize filepath for comparison
            filepath = os.path.abspath(filepath)
            
            # Check if file is already open
            to_remove = []
            for filename, (editor, tab_id, _) in self.open_files.items():
                if os.path.abspath(filename) == filepath:
                    try:
                        # Test if tab still exists
                        self.notebook.index(tab_id)
                        self.notebook.select(tab_id)
                        self.current_file = filepath
                        if self.app:
                            self.app.update_file_label(filepath)
                        return True
                    except tk.TclError:
                        to_remove.append(filename)
            
            for f in to_remove:
                del self.open_files[f]
            
            # Read file content
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Create new tab
            tab_name = os.path.basename(filepath)
            editor_frame, text_widget, line_numbers = self.create_editor(filepath)
            
            text_widget.insert("1.0", content)
            self.apply_syntax_highlighting(text_widget, filepath)
            
            self.notebook.add(editor_frame, text=tab_name)
            self.open_files[filepath] = (text_widget, editor_frame, hash(content))
            self.notebook.select(editor_frame)
            self.current_file = filepath
            if self.app:
                self.app.update_file_label(filepath)
            
            self.update_line_numbers(text_widget, line_numbers)
            self.update_cursor_position(text_widget)
            
            if self.app:
                self.app.log_ai(f"📂 Opened: {tab_name}")
            return True
            
        except Exception as e:
            if self.app:
                self.app.log_ai(f"❌ Error opening {filepath}: {e}")
            return False
    
    def close_tab_under_cursor(self, event):
        """Close tab under cursor (middle click) - FIXED"""
        try:
            # Get tab index under cursor
            tab_index = self.notebook.index(f"@{event.x},{event.y}")
            if tab_index >= 0:
                # Get the tab id at this index
                tab_ids = self.notebook.tabs()
                if 0 <= tab_index < len(tab_ids):
                    tab_id = tab_ids[tab_index]
                    self.notebook.select(tab_id)
                    self.close_current_tab()
        except tk.TclError:
            pass
    
    def close_current_tab(self, event=None):
        """Close the current tab - FIXED"""
        try:
            current_tab = self.notebook.select()
            if not current_tab:
                return False
            
            # Find which file is in this tab
            filename = None
            for fname, (_, tab_id, _) in self.open_files.items():
                if tab_id == current_tab:
                    filename = fname
                    break
            
            if not filename:
                # If we can't find the file, just close the tab
                self.notebook.forget(current_tab)
                return True
            
            # Check for unsaved changes
            text_widget = self.open_files[filename][0]
            current_content = text_widget.get("1.0", "end-1c")
            original_hash = self.open_files[filename][2]
            
            if hash(current_content) != original_hash:
                # Ask user if they want to save
                result = messagebox.askyesnocancel(
                    "Unsaved Changes",
                    f"Save changes to {os.path.basename(filename)}?"
                )
                
                if result is None:  # Cancel
                    return False
                elif result:  # Yes, save
                    self.save_file(filename, text_widget)
            
            # Close the tab
            self.notebook.forget(current_tab)
            del self.open_files[filename]
            
            # Update current file
            tabs = self.notebook.tabs()
            if tabs:
                self.notebook.select(tabs[0])
                # Find the new current file
                for fname, (_, tab_id, _) in self.open_files.items():
                    if tab_id == tabs[0]:
                        self.current_file = fname
                        if self.app:
                            self.app.update_file_label(fname)
                        break
            else:
                self.current_file = None
                if self.app:
                    self.app.update_file_label(None)
            
            return True
            
        except Exception as e:
            if self.app:
                self.app.log_ai(f"❌ Error closing tab: {e}")
            return False
    
    def close_other_tabs(self):
        """Close all tabs except current"""
        current_tab = self.notebook.select()
        if not current_tab:
            return
        
        # Find current filename
        current_filename = None
        for fname, (_, tab_id, _) in self.open_files.items():
            if tab_id == current_tab:
                current_filename = fname
                break
        
        if not current_filename:
            return
        
        # Close all other tabs
        for filename, (text_widget, tab_id, _) in list(self.open_files.items()):
            if filename != current_filename:
                # Check for unsaved changes
                current_content = text_widget.get("1.0", "end-1c")
                original_hash = self.open_files[filename][2]
                
                if hash(current_content) != original_hash:
                    result = messagebox.askyesnocancel(
                        "Unsaved Changes",
                        f"Save changes to {os.path.basename(filename)}?"
                    )
                    
                    if result is None:  # Cancel
                        continue
                    elif result:  # Yes, save
                        self.save_file(filename, text_widget)
                
                self.notebook.forget(tab_id)
                if filename in self.open_files:
                    del self.open_files[filename]
    
    def close_all_tabs(self):
        """Close all tabs"""
        if not self.open_files:
            return
        
        unsaved = []
        for filename, (text_widget, _, original_hash) in self.open_files.items():
            current_content = text_widget.get("1.0", "end-1c")
            if hash(current_content) != original_hash:
                unsaved.append(filename)
        
        if unsaved:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"There are {len(unsaved)} files with unsaved changes.\nSave all?"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes, save all
                for filename in unsaved:
                    text_widget = self.open_files[filename][0]
                    self.save_file(filename, text_widget)
        
        # Close all tabs safely
        for _, tab_widget, _ in list(self.open_files.values()):
            try:
                self.notebook.forget(tab_widget)
            except:
                pass
        
        self.open_files.clear()
        self.current_file = None
        if self.app:
            self.app.update_file_label(None)
    
    def show_tab_menu(self, event):
        """Show context menu for tab"""
        try:
            tab_index = self.notebook.index(f"@{event.x},{event.y}")
            if tab_index >= 0:
                tab_ids = self.notebook.tabs()
                if 0 <= tab_index < len(tab_ids):
                    tab_id = tab_ids[tab_index]
                    self.notebook.select(tab_id)
                    self.tab_menu.post(event.x_root, event.y_root)
        except tk.TclError:
            pass
    
    def save_current_file(self, event=None):
        """Save the current file"""
        if not self.current_file:
            return False
        
        if self.current_file in self.open_files:
            text_widget = self.open_files[self.current_file][0]
            return self.save_file(self.current_file, text_widget)
        return False
    
    def save_file(self, filename, text_widget):
        """Save a specific file"""
        try:
            content = text_widget.get("1.0", "end-1c")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update hash
            self.open_files[filename] = (
                text_widget,
                self.open_files[filename][1],
                hash(content)
            )
            
            if self.app:
                self.app.log_ai(f"💾 Saved: {os.path.basename(filename)}")
            
            # Update syntax highlighting immediately on save
            self.apply_syntax_highlighting(text_widget, filename)
            
            return True
        except Exception as e:
            if self.app:
                self.app.log_ai(f"❌ Error saving {filename}: {e}")
            return False
    
    def save_all_files(self, project_path=None):
        """Save all open files"""
        saved_files = []
        for filename, (text_widget, _, _) in self.open_files.items():
            if self.save_file(filename, text_widget):
                saved_files.append(filename)
        return saved_files
    
    def get_current_file(self):
        """Get current file path"""
        return self.current_file
    
    def get_open_files(self):
        """Get list of open files"""
        return list(self.open_files.keys())
    
    def update_file_content(self, filename, new_content):
        """Update file content (for AI suggestions). Opens file if not open."""
        # Normalize path
        filename = os.path.abspath(filename)
        
        if filename not in self.open_files:
            # Create a new tab for it
            tab_name = os.path.basename(filename)
            editor_frame, text_widget, line_numbers = self.create_editor(filename)
            
            text_widget.insert("1.0", new_content)
            self.apply_syntax_highlighting(text_widget, filename)
            
            self.notebook.add(editor_frame, text=tab_name)
            self.open_files[filename] = (text_widget, editor_frame, hash(new_content))
            self.notebook.select(editor_frame)
            self.current_file = filename
            if self.app:
                self.app.update_file_label(filename)
            
            self.update_line_numbers(text_widget, line_numbers)
            self.update_cursor_position(text_widget)
            
            if self.app:
                self.app.log_ai(f"📂 Created/Opened tab: {tab_name}")
            return

        # If already open, just update
        text_widget = self.open_files[filename][0]
        text_widget.delete("1.0", "end")
        text_widget.insert("1.0", new_content)
        
        self.apply_syntax_highlighting(text_widget, filename)
        
        # Update hash
        self.open_files[filename] = (
            text_widget,
            self.open_files[filename][1],
            hash(new_content)
        )
        
        # Update line numbers
        parent = text_widget.master
        for child in parent.winfo_children():
            if isinstance(child, tk.Text) and child.cget("width") == 4:
                self.update_line_numbers(text_widget, child)
                break

    def reload_file(self, filepath):
        """Reload a file from disk if it's open"""
        if filepath in self.open_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.update_file_content(filepath, content)
            except Exception as e:
                print(f"Reload failed: {e}")
    
    def on_tab_changed(self, event):
        """Handle tab change"""
        current_tab = self.notebook.select()
        if current_tab:
            for filename, (_, tab_id, _) in self.open_files.items():
                if tab_id == current_tab:
                    self.current_file = filename
                    if self.app:
                        self.app.update_file_label(filename)
                    break
    
    def on_text_modified(self, filename, text_widget):
        """Handle text modification"""
        # You can add auto-save or modification indicators here
        pass
    
    def update_line_numbers(self, text_widget, line_numbers):
        """Update line numbers with accurate alignment even with word wrap"""
        try:
            line_numbers.config(state='normal')
            line_numbers.delete("1.0", "end")
            
            # Get the first and last visible lines
            first = text_widget.index("@0,0")
            last = text_widget.index(f"@0,{text_widget.winfo_height()}")
            
            first_line = int(first.split('.')[0])
            last_line = int(last.split('.')[0])
            
            # Draw line numbers only for visible lines
            # This is more efficient and handles scrolling better
            for i in range(first_line, last_line + 1):
                dline = text_widget.dlineinfo(f"{i}.0")
                if dline:
                    # Line is visible, but might be a wrapped line
                    # We only want to put a number at the start of a logical line
                    line_numbers.insert("end", f"{i}\n")
                else:
                    # Line might be wrapped or not visible
                    # If it's a wrapped part of a logical line, we don't put a number
                    # But we need to keep the line numbers widget in sync vertically
                    pass

            # Precise sync: we use the same yview for both
            line_numbers.yview_moveto(text_widget.yview()[0])
            line_numbers.config(state='disabled')
        except Exception:
            pass

    def _sync_scroll(self, *args):
        """Sync line numbers scroll with text widget"""
        for filename, (text_widget, tab_id, _) in self.open_files.items():
            # Find the active text widget
            if str(text_widget) == self.notebook.select(): # This is a bit simplified
                pass
        # Better: just sync the one that triggered it
        pass

    def _schedule_line_numbers(self, text_widget, line_numbers):
        try:
            key = str(text_widget)
            if key in self._ln_sched:
                self.after_cancel(self._ln_sched[key])
            self._ln_sched[key] = self.after(50, lambda: self.update_line_numbers(text_widget, line_numbers))
        except Exception:
            pass
    
    def update_cursor_position(self, text_widget):
        """Update cursor position in status bar"""
        try:
            cursor_pos = text_widget.index("insert")
            line, col = cursor_pos.split('.')
            if self.app:
                self.app.update_cursor_position(int(line), int(col))
        except:
            pass

    def _init_spell_dict(self):
        try:
            common = [
                "the","be","to","of","and","a","in","that","have","I","it","for","not","on","with","he","as","you","do","at",
                "this","but","his","by","from","they","we","say","her","she","or","an","will","my","one","all","would","there","their",
                "is","are","was","were","can","could","should","shall","may","might","must","if","else","elif","while","for","return","class","def","import","from"
            ]
            self._spell_dict = set(common)
        except Exception:
            self._spell_dict = set()

    def _schedule_quality_check(self, filename, text_widget):
        try:
            key = str(text_widget) + ":q"
            if key in self._quality_sched:
                self.after_cancel(self._quality_sched[key])
            self._quality_sched[key] = self.after(120, lambda: self._check_grammar_spelling(filename, text_widget))
        except Exception:
            pass

    def _levenshtein(self, a, b):
        try:
            m, n = len(a), len(b)
            dp = list(range(n+1))
            for i in range(1, m+1):
                prev = dp[0]
                dp[0] = i
                for j in range(1, n+1):
                    temp = dp[j]
                    dp[j] = min(
                        dp[j] + 1,
                        dp[j-1] + 1,
                        prev + (0 if a[i-1] == b[j-1] else 1)
                    )
                    prev = temp
            return dp[n]
        except Exception:
            return 999

    def _suggest_words(self, word, limit=5):
        try:
            cands = sorted(self._spell_dict, key=lambda w: (self._levenshtein(word.lower(), w), len(w)))
            return [w for w in cands[:limit]]
        except Exception:
            return []

    def _check_grammar_spelling(self, filename, text_widget):
        try:
            text_widget.tag_delete("sp_error")
            text_widget.tag_delete("gr_error")
            text_widget.tag_configure("sp_error", underline=True, foreground="#ff6b6b")
            text_widget.tag_configure("gr_error", underline=True, foreground="#ffd166")
            content = text_widget.get("1.0", "end-1c")
            if not content:
                return
            lines = content.split('\n')
            line_no = 1
            import re
            for line in lines:
                for m in re.finditer(r"\s{3,}", line):
                    start = f"{line_no}.{m.start()}"
                    end = f"{line_no}.{m.end()}"
                    text_widget.tag_add("gr_error", start, end)
                if len(line.strip()) > 80 and line.strip()[-1] not in ".!?":
                    start = f"{line_no}.{max(0, len(line)-1)}"
                    end = f"{line_no}.{len(line)}"
                    text_widget.tag_add("gr_error", start, end)
                words = re.findall(r"[A-Za-z]{4,}", line)
                idx = 0
                for w in words:
                    j = line.find(w, idx)
                    idx = j + len(w)
                    if w.lower() not in self._spell_dict:
                        start = f"{line_no}.{j}"
                        end = f"{line_no}.{j+len(w)}"
                        text_widget.tag_add("sp_error", start, end)
                line_no += 1
        except Exception:
            pass

    def _open_correction_popup(self, text_widget):
        try:
            cursor = text_widget.index("insert")
            line = int(cursor.split('.')[0])
            tags = text_widget.tag_names(cursor)
            target_tag = None
            for t in ("sp_error", "gr_error"):
                if t in tags:
                    target_tag = t
                    break
            if not target_tag:
                return
            import re
            line_text = text_widget.get(f"{line}.0", f"{line}.end")
            col = int(cursor.split('.')[1])
            m = re.search(r"[A-Za-z_]+", line_text[col:] )
            if not m:
                return
            word = m.group(0)
            suggestions = self._suggest_words(word)
            if not suggestions:
                return
            x = text_widget.winfo_rootx() + 20
            y = text_widget.winfo_rooty() + 20
            if self._suggest_popup:
                try:
                    self._suggest_popup.destroy()
                except Exception:
                    pass
            popup = tk.Toplevel(self)
            popup.overrideredirect(True)
            popup.geometry(f"200x{min(150, 24*(len(suggestions)+1))}+{x}+{y}")
            lb = tk.Listbox(popup)
            for s in suggestions:
                lb.insert("end", s)
            lb.pack(fill="both", expand=True)
            def apply_sel(event=None):
                if lb.curselection():
                    sel = lb.get(lb.curselection()[0])
                    start = f"{line}.{col}"
                    end = f"{line}.{col+len(word)}"
                    text_widget.delete(start, end)
                    text_widget.insert(start, sel)
                try:
                    popup.destroy()
                except Exception:
                    pass
            lb.bind("<Return>", apply_sel)
            lb.bind("<Double-1>", apply_sel)
            self._suggest_popup = popup
        except Exception:
            pass

    def _collect_words_across_open_files(self):
        try:
            import re
            words = {}
            for fp, (tw, _, _) in self.open_files.items():
                text = tw.get("1.0", "end-1c")
                for w in re.findall(r"[A-Za-z_]{3,}", text):
                    words[w] = words.get(w, 0) + 1
            return sorted(words.items(), key=lambda x: (-x[1], x[0]))
        except Exception:
            return []

    def _collect_words_project(self, max_files=20):
        items = {}
        try:
            import os, re
            root = getattr(self.app, "project_path", None)
            if not root or not os.path.isdir(root):
                return []
            count = 0
            for dirpath, _, filenames in os.walk(root):
                for fn in filenames:
                    if not fn.endswith(('.py', '.md', '.txt')):
                        continue
                    try:
                        with open(os.path.join(dirpath, fn), 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                        for w in re.findall(r"[A-Za-z_]{3,}", text):
                            items[w] = items.get(w, 0) + 1
                    except Exception:
                        pass
                    count += 1
                    if count >= max_files:
                        break
                if count >= max_files:
                    break
        except Exception:
            return []
        return sorted(items.items(), key=lambda x: (-x[1], x[0]))

    def _trigger_autocomplete(self, text_widget):
        try:
            cursor = text_widget.index("insert")
            line, col = map(int, cursor.split('.'))
            prefix = text_widget.get(f"{line}.0", f"{line}.{col}").split()[-1]
            if not prefix:
                return "break"
            words_open = self._collect_words_across_open_files()
            words_proj = self._collect_words_project()
            merged = {}
            for w, n in words_open + words_proj:
                merged[w] = max(merged.get(w, 0), n)
            options = [w for w, n in sorted(merged.items(), key=lambda x: (-x[1], x[0])) if w.lower().startswith(prefix.lower())][:50]
            if not options:
                return "break"
            x = text_widget.winfo_rootx() + 10
            y = text_widget.winfo_rooty() + 10
            popup = tk.Toplevel(self)
            popup.overrideredirect(True)
            popup.geometry(f"240x160+{x}+{y}")
            lb = tk.Listbox(popup, bg="#2d2d30", fg="#cccccc", selectbackground="#094771")
            for o in options:
                lb.insert("end", o)
            lb.pack(fill="both", expand=True)
            def insert_sel(event=None):
                if lb.curselection():
                    sel = lb.get(lb.curselection()[0])
                    start = f"{line}.{col-len(prefix)}"
                    text_widget.delete(start, f"{line}.{col}")
                    text_widget.insert(start, sel)
                try:
                    popup.destroy()
                except Exception:
                    pass
            lb.bind("<Return>", insert_sel)
            lb.bind("<Double-1>", insert_sel)
            return "break"
        except Exception:
            return "break"
    
    def apply_syntax_highlighting(self, text_widget, filename):
        """Apply syntax highlighting based on file extension"""
        try:
            from pygments.lexers import (
                PythonLexer, LuaLexer, CppLexer, CSharpLexer, 
                JavascriptLexer, HtmlLexer, CssLexer, MarkdownLexer
            )
            from pygments.lexers import get_lexer_for_filename
        except ImportError:
            # Fallback for core python only if pygments partially installed?
            from pygments.lexers import PythonLexer
            get_lexer_for_filename = None

        try:
            # Determine lexer
            lexer = None
            if get_lexer_for_filename:
                try:
                    lexer = get_lexer_for_filename(filename)
                except:
                    pass
            
            # Manual fallback/override
            if not lexer:
                ext = os.path.splitext(filename)[1].lower()
                if ext == '.py': lexer = PythonLexer()
                elif ext == '.lua': lexer = LuaLexer() # Roblox uses Lua
                elif ext in ['.cpp', '.c', '.h', '.hpp']: lexer = CppLexer()
                elif ext == '.cs': lexer = CSharpLexer()
                elif ext == '.js': lexer = JavascriptLexer()
                elif ext in ['.html', '.htm']: lexer = HtmlLexer()
                elif ext == '.css': lexer = CssLexer()
                elif ext == '.md': lexer = MarkdownLexer()
            
            if not lexer:
                return

            text = text_widget.get("1.0", "end-1c")
            
            # Define generalized color map
            color_map = {
                Token.Keyword: "#569cd6",
                Token.Keyword.Constant: "#569cd6",
                Token.Keyword.Declaration: "#569cd6",
                Token.Keyword.Namespace: "#569cd6",
                Token.Keyword.Type: "#4ec9b0",
                Token.Name.Class: "#4ec9b0",
                Token.Name.Function: "#dcdcaa",
                Token.Name.Builtin: "#4ec9b0",
                Token.Name.Tag: "#569cd6",      # HTML tags
                Token.Name.Attribute: "#9cdcfe", # HTML attributes
                Token.String: "#ce9178",
                Token.String.Double: "#ce9178",
                Token.String.Single: "#ce9178",
                Token.Comment: "#6a9955",
                Token.Comment.Single: "#6a9955",
                Token.Comment.Multiline: "#6a9955",
                Token.Number: "#b5cea8",
                Token.Number.Integer: "#b5cea8",
                Token.Number.Float: "#b5cea8",
                Token.Operator: "#d4d4d4",
                Token.Name.Variable: "#9cdcfe",
            }
            
            # Clear existing tags
            for tag in list(text_widget.tag_names()):
                if tag.startswith("pygments_"):
                    text_widget.tag_delete(tag)
            
            lines = text.split('\n')
            current_line = 1
            
            for line in lines:
                try:
                    tokens = list(lexer.get_tokens(line))
                    current_col = 0
                    
                    for token_type, token_text in tokens:
                        if token_text:
                            end_col = current_col + len(token_text)
                            
                            # Find best matching color
                            color = None
                            if token_type in color_map:
                                color = color_map[token_type]
                            else:
                                # Try to match parent token types
                                parent = token_type.parent
                                while parent:
                                    if parent in color_map:
                                        color = color_map[parent]
                                        break
                                    parent = parent.parent
                            
                            if color:
                                tag_name = f"pygments_{token_type}"
                                if tag_name not in text_widget.tag_names():
                                    text_widget.tag_configure(
                                        tag_name,
                                        foreground=color
                                    )
                                
                                start_index = f"{current_line}.{current_col}"
                                end_index = f"{current_line}.{end_col}"
                                
                                text_widget.tag_add(tag_name, start_index, end_index)
                            
                            current_col = end_col
                except:
                    pass
                
                current_line += 1
                
        except Exception as e:
            # Fallback to basic highlighting if anything fails
            print(f"Syntax highlighting error: {e}")
            self.apply_basic_syntax_highlighting(text_widget, filename)
    
    def apply_basic_syntax_highlighting(self, text_widget, filename):
        """Apply basic syntax highlighting (fallback)"""
        if not filename.endswith('.py'):
            return
        
        keywords = [
            'def', 'class', 'import', 'from', 'as', 'return', 'yield',
            'if', 'elif', 'else', 'for', 'while', 'break', 'continue',
            'try', 'except', 'finally', 'raise', 'with', 'pass',
            'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is',
            'lambda', 'global', 'nonlocal', 'assert', 'del', 'async', 'await'
        ]
        
        # Clear existing tags
        for tag in ['keyword', 'string', 'comment', 'number', 'function']:
            text_widget.tag_delete(tag)
        
        # Configure tags
        text_widget.tag_configure("keyword", foreground="#569cd6")
        text_widget.tag_configure("string", foreground="#ce9178")
        text_widget.tag_configure("comment", foreground="#6a9955")
        text_widget.tag_configure("number", foreground="#b5cea8")
        text_widget.tag_configure("function", foreground="#dcdcaa")
        
        text = text_widget.get("1.0", "end-1c")
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Highlight comments
            if '#' in line:
                comment_start = line.find('#')
                start = f"{line_num}.{comment_start}"
                end = f"{line_num}.{len(line)}"
                text_widget.tag_add("comment", start, end)
            
            # Highlight strings
            in_string = False
            string_start = 0
            for j, char in enumerate(line):
                if char in ['"', "'"]:
                    if not in_string:
                        in_string = True
                        string_start = j
                    else:
                        in_string = False
                        start = f"{line_num}.{string_start}"
                        end = f"{line_num}.{j+1}"
                        text_widget.tag_add("string", start, end)
    
    def undo(self):
        if self.current_file and self.current_file in self.open_files:
            text_widget = self.open_files[self.current_file][0]
            try:
                text_widget.edit_undo()
            except:
                pass
    
    def redo(self):
        if self.current_file and self.current_file in self.open_files:
            text_widget = self.open_files[self.current_file][0]
            try:
                text_widget.edit_redo()
            except:
                pass
    
    def cut(self):
        if self.current_file and self.current_file in self.open_files:
            text_widget = self.open_files[self.current_file][0]
            text_widget.event_generate("<<Cut>>")
    
    def copy(self):
        if self.current_file and self.current_file in self.open_files:
            text_widget = self.open_files[self.current_file][0]
            text_widget.event_generate("<<Copy>>")
    
    def paste(self):
        if self.current_file and self.current_file in self.open_files:
            text_widget = self.open_files[self.current_file][0]
            text_widget.event_generate("<<Paste>>")
    
    def find_text(self):
        if self.current_file and self.current_file in self.open_files:
            text_widget = self.open_files[self.current_file][0]
            
            from tkinter import simpledialog
            search_term = simpledialog.askstring("Find", "Find:")
            if search_term:
                text_widget.tag_remove("found", "1.0", "end")
                
                start_pos = "1.0"
                while True:
                    start_pos = text_widget.search(search_term, start_pos, "end", nocase=True)
                    if not start_pos:
                        break
                    
                    end_pos = f"{start_pos}+{len(search_term)}c"
                    text_widget.tag_add("found", start_pos, end_pos)
                    start_pos = end_pos
                
                text_widget.tag_configure("found", background="yellow", foreground="black")
    
    def replace_text(self):
        if self.current_file and self.current_file in self.open_files:
            text_widget = self.open_files[self.current_file][0]
            
            from tkinter import simpledialog
            find_term = simpledialog.askstring("Replace", "Find:")
            if find_term:
                replace_term = simpledialog.askstring("Replace", f"Replace '{find_term}' with:")
                if replace_term is not None:
                    content = text_widget.get("1.0", "end-1c")
                    new_content = content.replace(find_term, replace_term)
                    text_widget.delete("1.0", "end")
                    text_widget.insert("1.0", new_content)
    
    def format_code(self):
        if self.current_file and self.current_file in self.open_files:
            text_widget = self.open_files[self.current_file][0]
            content = text_widget.get("1.0", "end-1c")
            
            # Simple formatting: adjust indentation
            lines = content.split('\n')
            formatted = []
            indent = 0
            
            for line in lines:
                stripped = line.strip()
                if stripped:
                    if stripped.startswith(('else:', 'elif', 'except', 'finally:')):
                        indent = max(0, indent - 1)
                    
                    formatted.append('    ' * indent + stripped)
                    
                    if stripped.endswith(':'):
                        indent += 1
                    elif stripped.startswith(('return', 'break', 'continue', 'pass')):
                        pass
                else:
                    formatted.append('')
            
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", '\n'.join(formatted))
            
            self.apply_syntax_highlighting(text_widget, self.current_file)
    
    def check_syntax(self):
        if self.current_file and self.current_file.endswith('.py'):
            text_widget = self.open_files[self.current_file][0]
            content = text_widget.get("1.0", "end-1c")
            
            try:
                compile(content, '<string>', 'exec')
                if self.app:
                    self.app.log_ai("✅ Syntax check passed")
            except SyntaxError as e:
                if self.app:
                    self.app.log_ai(f"❌ Syntax error: {e}")
    
    def apply_theme_to_all(self, color_map):
        """Apply theme to all editors"""
        for filename, (text_widget, _, _) in self.open_files.items():
            text_widget.configure(
                bg=color_map.get("editor_bg", "#1e1e1e"),
                fg=color_map.get("editor_fg", "#d4d4d4"),
                insertbackground=color_map.get("editor_cursor", "#ffffff"),
                selectbackground=color_map.get("editor_selection", "#264f78")
            )
            
            parent = text_widget.master
            for child in parent.winfo_children():
                if isinstance(child, tk.Text) and child.cget("width") == 4:
                    child.configure(
                        bg=color_map.get("editor_gutter", "#1e1e1e"),
                        fg=color_map.get("editor_gutter_fg", "#858585")
                    )
            
            self.apply_syntax_highlighting(text_widget, filename)
