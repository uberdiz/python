import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading

class PlanPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(toolbar, text="⬅ Back to AI Chat", command=lambda: self.app.switch_sidebar("ai") if hasattr(self.app, 'switch_sidebar') else None).pack(side="left", padx=2)
        ttk.Button(toolbar, text="💾 Save Plan", command=self.save_plan).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🤖 Generate Plan (AI)", command=self.generate_ai_plan).pack(side="left", padx=2)
        ttk.Button(toolbar, text="📤 Submit to Agents", command=self.submit_to_agents).pack(side="right", padx=2)
        
        # Review message bar (top right area)
        review_frame = ttk.Frame(self)
        review_frame.pack(fill="x", padx=5, pady=2)
        
        ttk.Label(review_frame, text="Message for Agents:").pack(side="left", padx=2)
        self.review_message = ttk.Entry(review_frame)
        self.review_message.pack(side="left", fill="x", expand=True, padx=5)
        
        # Plan Editor (Text Area)
        self.text_area = tk.Text(self, wrap="word", font=("Consolas", 11), undo=True)
        self.text_area.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Comment system
        self.comments = {}  # line_start -> {"text": "", "color": ""}
        self.text_area.tag_configure("highlight", background="#3a3a00")
        self.text_area.tag_configure("commented", background="#2d4a2d")
        
        # Right-click context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="💬 Add Comment", command=self.add_comment)
        self.context_menu.add_command(label="🔦 Highlight", command=self.highlight_selection)
        self.context_menu.add_command(label="❌ Remove Highlight", command=self.remove_highlight)
        self.text_area.bind("<Button-3>", self.show_context_menu)
        
        # Comments sidebar
        self.comments_frame = ttk.LabelFrame(self, text="Comments")
        self.comments_frame.pack(fill="x", padx=5, pady=5)
        
        self.comments_list = tk.Listbox(self.comments_frame, height=4)
        self.comments_list.pack(fill="x", padx=2, pady=2)
        
        # Apply theme if available
        if self.app.theme_engine:
            bg = self.app.theme_engine.color_map.get("editor_bg", "#1e1e1e")
            fg = self.app.theme_engine.color_map.get("editor_fg", "#d4d4d4")
            self.text_area.configure(bg=bg, fg=fg, insertbackground=fg)
            self.comments_list.configure(bg=bg, fg=fg)
            
        # Load existing plan
        self.load_plan()

    def get_plan_path(self):
        if not self.app.project_path:
            return None
        # Hidden file to store the plan
        return os.path.join(self.app.project_path, ".ai_dev_plan.json")

    def load_plan(self):
        path = self.get_plan_path()
        if not path or not os.path.exists(path):
            self.text_area.insert("1.0", "# Project Plan\n\nAdd your project goals and tasks here.")
            return
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                content = data.get("content", "")
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", content)
        except Exception as e:
            self.app.log_ai(f"Error loading plan: {e}")

    def save_plan(self):
        path = self.get_plan_path()
        if not path:
            messagebox.showwarning("Warning", "Open a project first.")
            return
            
        content = self.text_area.get("1.0", "end-1c")
        data = {"content": content}
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self.app.log_ai("Plan saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save plan: {e}")

    def generate_ai_plan(self):
        if not self.app.project_path:
            return
            
        self.app.update_progress("Generating Plan...", True)
        
        def worker():
            try:
                # Use summarize_project logic to get context
                context = self.app.ai_manager.summarize_project(self.app.project_path)
                
                prompt = (
                    f"Based on this project summary, generate a detailed development plan.\n"
                    f"Include: Architecture, Features, and Next Steps.\n\n"
                    f"Project Context:\n{context}"
                )
                
                response = self.app.ai_manager.generate_response(prompt)
                
                self.app.root.after(0, lambda: self.append_plan(response))
                self.app.update_progress("Plan Generated", False)
                
            except Exception as e:
                self.app.log_ai(f"Plan Generation Error: {e}")
                self.app.update_progress("Error", False)
                
        threading.Thread(target=worker, daemon=True).start()

    def append_plan(self, text):
        self.text_area.insert(tk.END, "\n\n" + text)
        self.save_plan()
        
    def submit_to_agents(self):
        """Submit the plan with a message to agents"""
        plan_content = self.text_area.get("1.0", "end-1c")
        message = self.review_message.get().strip()
        
        if not plan_content.strip():
            from tkinter import messagebox
            messagebox.showwarning("Empty Plan", "Write a plan first.")
            return
            
        # Get agent orchestrator
        if hasattr(self.app, 'agent_manager') and hasattr(self.app.agent_manager, 'orchestrator'):
            orchestrator = self.app.agent_manager.orchestrator
            
            # Combine message and plan
            full_message = f"USER MESSAGE: {message}\n\nPROJECT PLAN:\n{plan_content}"
            
            # Route to all agents
            for agent_name in orchestrator.agents:
                orchestrator.route_message("user_review", agent_name, full_message)
                
            self.app.log_ai(f"Submitted plan to {len(orchestrator.agents)} agent(s)")
            self.review_message.delete(0, "end")
        else:
            from tkinter import messagebox
            messagebox.showinfo("No Agents", "Create agents in Agent Manager first.")
            
    def show_context_menu(self, event):
        """Show right-click context menu"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
            
    def add_comment(self):
        """Add a comment to selected text"""
        try:
            sel_start = self.text_area.index("sel.first")
            sel_end = self.text_area.index("sel.last")
            selected_text = self.text_area.get(sel_start, sel_end)
        except tk.TclError:
            messagebox.showinfo("Select Text", "Select some text first.")
            return
            
        from tkinter import simpledialog
        comment = simpledialog.askstring("Add Comment", f"Comment on: '{selected_text[:30]}...'")
        
        if comment:
            # Store comment
            self.comments[sel_start] = {
                "text": comment,
                "selected": selected_text[:50],
                "end": sel_end
            }
            
            # Apply visual tag
            self.text_area.tag_add("commented", sel_start, sel_end)
            
            # Update comments list
            self.refresh_comments_list()
            self.save_plan()
            
    def highlight_selection(self):
        """Highlight selected text"""
        try:
            sel_start = self.text_area.index("sel.first")
            sel_end = self.text_area.index("sel.last")
            self.text_area.tag_add("highlight", sel_start, sel_end)
        except tk.TclError:
            pass
            
    def remove_highlight(self):
        """Remove highlight from selected text"""
        try:
            sel_start = self.text_area.index("sel.first")
            sel_end = self.text_area.index("sel.last")
            self.text_area.tag_remove("highlight", sel_start, sel_end)
            self.text_area.tag_remove("commented", sel_start, sel_end)
            
            # Remove comment if exists
            if sel_start in self.comments:
                del self.comments[sel_start]
                self.refresh_comments_list()
        except tk.TclError:
            pass
            
    def refresh_comments_list(self):
        """Refresh the comments sidebar list"""
        self.comments_list.delete(0, tk.END)
        for pos, data in self.comments.items():
            display = f"[{pos}] {data['text'][:30]}..."
            self.comments_list.insert(tk.END, display)
