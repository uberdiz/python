import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import subprocess
import threading
import json
import webbrowser
import requests

class GitPanel:
    def __init__(self, parent_frame, app):
        self.app = app
        self.parent = parent_frame
        
        # Create Notebook for Git Tabs
        self.notebook = ttk.Notebook(parent_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # --- TAB 1: LOCAL GIT ---
        self.local_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.local_frame, text="Local Repo")
        self.setup_local_tab()
        
        # --- TAB 2: GITHUB REPO MANAGER ---
        self.github_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.github_frame, text="GitHub Manager")
        self.setup_github_tab()
        
    def setup_local_tab(self):
        """Setup local git controls"""
        # Status Frame
        status_frame = ttk.LabelFrame(self.local_frame, text="Status")
        status_frame.pack(fill="x", padx=5, pady=5)
        
        self.branch_label = ttk.Label(status_frame, text="Branch: --")
        self.branch_label.pack(side="left", padx=5, pady=5)
        
        ttk.Button(status_frame, text="Refresh", command=self.refresh_local).pack(side="right", padx=5, pady=5)
        ttk.Button(status_frame, text="Init Repo", command=self.init_repo).pack(side="right", padx=5)
        
        # Changes Frame
        changes_frame = ttk.LabelFrame(self.local_frame, text="Changes")
        changes_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # List of changed files
        self.changes_list = tk.Listbox(changes_frame, selectmode="extended", height=10)
        self.changes_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(changes_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(btn_frame, text="Stage Selected", command=self.stage_selected).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Stage All (+)", command=self.stage_all).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Unstage All (-)", command=self.unstage_all).pack(side="left", padx=2)
        
        # Commit Frame
        commit_frame = ttk.LabelFrame(self.local_frame, text="Commit")
        commit_frame.pack(fill="x", padx=5, pady=5)
        
        self.commit_entry = ttk.Entry(commit_frame)
        self.commit_entry.pack(fill="x", padx=5, pady=5)
        self.commit_entry.insert(0, "Update")
        
        ttk.Button(commit_frame, text="Commit", command=self.commit_changes).pack(fill="x", padx=5, pady=5)
        
        # Sync Frame
        sync_frame = ttk.LabelFrame(self.local_frame, text="Sync")
        sync_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(sync_frame, text="Pull ⬇", command=self.git_pull).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(sync_frame, text="Push ⬆", command=self.git_push).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(sync_frame, text="Push To... 🚀", command=self.push_to_remote).pack(side="left", fill="x", expand=True, padx=2)

    def setup_github_tab(self):
        """Setup GitHub Repo Manager"""
        # Control Frame
        ctrl_frame = ttk.Frame(self.github_frame)
        ctrl_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(ctrl_frame, text="Refresh Repos", command=self.load_github_repos).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="Create New Repo", command=self.create_remote_repo).pack(side="right", padx=5)
        
        # Repo List
        self.repo_tree = ttk.Treeview(self.github_frame, columns=("Name", "Private", "Url"), show="headings")
        self.repo_tree.heading("Name", text="Repository")
        self.repo_tree.heading("Private", text="Visibility")
        self.repo_tree.heading("Url", text="Clone URL")
        self.repo_tree.column("Name", width=150)
        self.repo_tree.column("Private", width=80)
        self.repo_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.repo_tree.bind("<Button-3>", self.show_repo_menu)
        
        # Repo Menu
        self.repo_menu = tk.Menu(self.github_frame, tearoff=0)
        self.repo_menu.add_command(label="🚀 Set as Origin Remote", command=self.set_as_origin)
        self.repo_menu.add_command(label="➕ Add as Custom Remote", command=self.add_custom_remote)
        self.repo_menu.add_separator()
        self.repo_menu.add_command(label="🌐 Open in Browser", command=self.open_in_browser)
        self.repo_menu.add_separator()
        self.repo_menu.add_command(label="📤 Push Project to this Repository", command=self.push_project_to_repo)
        self.repo_menu.add_command(label="📁 Push Project to Subfolder...", command=self.push_project_to_subfolder)
        
        # Actions
        action_frame = ttk.Frame(self.github_frame)
        action_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(action_frame, text="Clone & Open", command=self.clone_selected).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Open in Browser", command=self.open_in_browser).pack(side="left", padx=5)

    def run_git(self, args):
        """Run git command in project path"""
        if not self.app.project_path:
            return None, "No project open"
            
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.app.project_path,
                capture_output=True,
                text=True,
                encoding='utf-8' # Ensure UTF-8
            )
            return result.stdout, result.stderr
        except FileNotFoundError:
            return None, "Git not installed"
        except Exception as e:
            return None, str(e)

    def refresh_local(self):
        """Refresh local git status"""
        if not self.app.project_path:
            return

        # Check branch
        out, err = self.run_git(["branch", "--show-current"])
        if out:
            self.branch_label.config(text=f"Branch: {out.strip()}")
        else:
            self.branch_label.config(text="Branch: -- (Not a repo?)")
            
        # Check status
        out, err = self.run_git(["status", "--porcelain"])
        self.changes_list.delete(0, tk.END)
        if out:
            for line in out.split('\n'):
                if line.strip():
                    self.changes_list.insert(tk.END, line.strip())

    def init_repo(self):
        if not self.app.project_path: return
        out, err = self.run_git(["init"])
        if out:
            self.app.log_ai(f"Git Init: {out}")
            self.refresh_local()
        else:
            self.app.log_ai(f"Git Init Error: {err}")

    def stage_selected(self):
        selected = self.changes_list.curselection()
        if not selected: return
        for idx in selected:
            line = self.changes_list.get(idx)
            # Porcelain format: "XY path"
            if len(line) > 3:
                filepath = line[3:].strip()
                self.run_git(["add", filepath])
        self.refresh_local()

    def stage_all(self):
        self.run_git(["add", "."])
        self.refresh_local()
        
    def unstage_all(self):
        self.run_git(["reset"])
        self.refresh_local()

    def commit_changes(self):
        msg = self.commit_entry.get()
        if not msg:
            messagebox.showwarning("Commit", "Enter commit message")
            return
            
        out, err = self.run_git(["commit", "-m", msg])
        if out:
            self.app.log_ai(f"Commit: {out}")
            self.commit_entry.delete(0, tk.END)
            self.refresh_local()
        else:
             self.app.log_ai(f"Commit Error: {err}")

    def git_push(self):
        def worker():
            self.app.update_progress("Pushing...", True)
            out, err = self.run_git(["push"])
            if out or not err: # sometimes err has progress info
                self.app.log_ai(f"Push Output: {out}\n{err}")
                self.app.show_message("Git Push", "Push command executed.")
            else:
                self.app.log_ai(f"Push Error: {err}")
            self.app.update_progress("Push complete", False)
        threading.Thread(target=worker, daemon=True).start()

    def push_to_remote(self):
        """Push to a specific remote selected by user"""
        out, err = self.run_git(["remote"])
        if not out:
            messagebox.showinfo("Git", "No remotes found.")
            return
            
        remotes = out.strip().split('\n')
        remote = tk.simpledialog.askstring("Push To", f"Select remote (Current: {', '.join(remotes)}):", initialvalue=remotes[0])
        
        if not remote: return
        
        def worker():
            self.app.update_progress(f"Pushing to {remote}...", True)
            # Get current branch
            branch_out, _ = self.run_git(["branch", "--show-current"])
            branch = branch_out.strip() if branch_out else "main"
            
            out, err = self.run_git(["push", remote, branch])
            self.app.log_ai(f"Push to {remote} Output: {out}\n{err}")
            self.app.show_message("Git Push", f"Pushed {branch} to {remote}.")
            self.app.update_progress("Push complete", False)
            
        threading.Thread(target=worker, daemon=True).start()

    def git_pull(self):
        def worker():
            self.app.update_progress("Pulling...", True)
            out, err = self.run_git(["pull"])
            self.app.log_ai(f"Pull Output: {out}\n{err}")
            self.app.update_progress("Pull complete", False)
            self.app.project_tree.refresh() # Refresh files
        threading.Thread(target=worker, daemon=True).start()

    # --- GITHUB METHODS ---
    
    def get_headers(self):
        token = self.app.settings.get("github_token", "")
        if not token:
            return None
        return {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def load_github_repos(self):
        token = self.app.settings.get("github_token", "")
        if not token:
            token = simpledialog.askstring("GitHub Token", "Enter GitHub Token:")
            if token:
                self.app.settings["github_token"] = token
                self.app.save_settings(self.app.settings)
            else:
                return

        def worker():
            try:
                # Logic to support "curl -u user:token" style (Basic Auth) or Token Header
                username = self.app.settings.get("github_username", "")
                
                # If username is present, prefer Basic Auth if token exists
                auth = None
                headers = {}
                
                if username and token:
                    auth = (username, token)
                elif token:
                     headers = {"Authorization": f"token {token}"}
                
                headers["Accept"] = "application/vnd.github.v3+json"
                
                # Endpoint
                url = "https://api.github.com/user/repos" 
                # If username provided, maybe user wants that specific user's repos? 
                # But 'user/repos' lists ALL repos for the authenticated user (including private)
                
                resp = requests.get(url, headers=headers, auth=auth, params={"sort": "updated", "per_page": 50})
                
                if resp.status_code == 200:
                    repos = resp.json()
                    self.app.root.after(0, lambda: self.populate_repos(repos))
                else:
                    self.app.log_ai(f"GitHub Error: {resp.status_code} {resp.text}")
            except Exception as e:
                self.app.log_ai(f"GitHub Connection Error: {e}")
        
        threading.Thread(target=worker, daemon=True).start()

    def populate_repos(self, repos):
        for item in self.repo_tree.get_children():
            self.repo_tree.delete(item)
            
        for repo in repos:
            name = repo.get("name", "Unknown")
            private = "Private" if repo.get("private") else "Public"
            url = repo.get("clone_url", "")
            self.repo_tree.insert("", "end", values=(name, private, url))

    def clone_selected(self):
        sel = self.repo_tree.selection()
        if not sel: return
        item = self.repo_tree.item(sel[0])
        url = item['values'][2]
        
        folder = tk.filedialog.askdirectory(title="Select Folder to Clone Into")
        if not folder: return
        
        def worker():
            self.app.update_progress(f"Cloning {url}...", True)
            try:
                subprocess.run(["git", "clone", url], cwd=folder, check=True)
                repo_name = url.split("/")[-1].replace(".git", "")
                full_path = os.path.join(folder, repo_name)
                
                self.app.root.after(0, lambda: self.app.open_existing_project_path(full_path))
                self.app.log_ai(f"Cloned {repo_name} successfully.")
            except Exception as e:
                self.app.log_ai(f"Clone Failed: {e}")
            self.app.update_progress("Clone complete", False)
            
        threading.Thread(target=worker, daemon=True).start()

    def show_repo_menu(self, event):
        item = self.repo_tree.identify_row(event.y)
        if item:
            self.repo_tree.selection_set(item)
            self.repo_menu.post(event.x_root, event.y_root)

    def set_as_origin(self):
        sel = self.repo_tree.selection()
        if not sel: return
        url = self.repo_tree.item(sel[0])['values'][2]
        
        if messagebox.askyesno("Git Remote", f"Set {url} as 'origin'?"):
            self.run_git(["remote", "remove", "origin"])
            self.run_git(["remote", "add", "origin", url])
            self.app.log_ai(f"Origin set to {url}")

    def add_custom_remote(self):
        sel = self.repo_tree.selection()
        if not sel: return
        url = self.repo_tree.item(sel[0])['values'][2]
        
        name = simpledialog.askstring("Remote Name", "Enter remote name:")
        if name:
            self.run_git(["remote", "add", name, url])
            self.app.log_ai(f"Remote {name} added for {url}")

    def open_in_browser(self):
        sel = self.repo_tree.selection()
        if not sel: return
        item = self.repo_tree.item(sel[0])
        url = item['values'][2].replace(".git", "") # Approximate
        webbrowser.open(url)

    def create_remote_repo(self):
        # reuse existing logic from app.py or implement fresh
        name = simpledialog.askstring("New Repo", "Repository Name:")
        if not name: return
        
        token = self.app.settings.get("github_token", "")
        if not token: return
        
        def worker():
            try:
                headers = self.get_headers()
                data = {"name": name, "private": True} # Default private
                resp = requests.post("https://api.github.com/user/repos", headers=headers, json=data)
                
                if resp.status_code == 201:
                    repo_info = resp.json()
                    clone_url = repo_info['clone_url']
                    self.app.log_ai(f"Created Repo: {clone_url}")
                    self.load_github_repos() # Refresh list
                    
                    # Optionally push current project
                    if self.app.project_path and messagebox.askyesno("Push", "Push current project to new repo?"):
                         self.run_git(["remote", "add", "origin", clone_url])
                         self.run_git(["branch", "-M", "main"])
                         self.run_git(["push", "-u", "origin", "main"])
                else:
                    self.app.log_ai(f"Create Repo Failed: {resp.text}")
            except Exception as e:
                self.app.log_ai(f"Error: {e}")
                
        threading.Thread(target=worker, daemon=True).start()

    def push_project_to_repo(self):
        """Push current project to selected GitHub repository"""
        selected = self.repo_tree.selection()
        if not selected:
            messagebox.showinfo("Git", "Please select a repository first.")
            return
            
        values = self.repo_tree.item(selected[0], 'values')
        repo_name = values[0]
        repo_url = values[2] # Clone URL
        
        if not self.app.project_path:
            messagebox.showerror("Error", "No project open.")
            return

        if not messagebox.askyesno("Push to GitHub", f"Do you want to push the current project to '{repo_name}'?\n\nURL: {repo_url}"):
            return
            
        def worker():
            self.app.update_progress(f"Pushing to {repo_name}...", True)
            try:
                # Use the app's git_init_and_push_fixed which handles origin setup etc.
                success = self.app.git_init_and_push_fixed(self.app.project_path, repo_url)
                if success:
                    self.app.show_message("Success", f"✅ Project pushed to {repo_name}!")
                self.app.update_progress("Push complete", False)
            except Exception as e:
                self.app.log_ai(f"Push error: {e}")
                self.app.update_progress("Push failed", False)
                
        threading.Thread(target=worker, daemon=True).start()

    def push_project_to_subfolder(self):
        """Push current project to a specific subfolder of selected repository"""
        selected = self.repo_tree.selection()
        if not selected:
            messagebox.showinfo("Git", "Please select a repository first.")
            return
            
        values = self.repo_tree.item(selected[0], 'values')
        repo_url = values[2]
        
        if not self.app.project_path:
            messagebox.showerror("Error", "No project open.")
            return
            
        subfolder = simpledialog.askstring("GitHub Subfolder", "Enter remote subfolder name:")
        if not subfolder: return
        
        def worker():
            self.app.update_progress(f"Pushing to folder '{subfolder}'...", True)
            try:
                import tempfile
                import shutil
                
                # Use authenticated URL if token is available
                auth_url = repo_url
                token = self.app.settings.get("github_token", "")
                if token and "github.com" in repo_url:
                    auth_url = repo_url.replace("https://", f"https://{token}@")

                with tempfile.TemporaryDirectory() as temp_dir:
                    self.app.log_ai(f"Cloning template to {temp_dir}...")
                    
                    # Ensure we are in an empty temp dir and clone into 'repo'
                    # Use a unique name for the clone dir just in case
                    clone_dir_name = "repo_clone"
                    
                    try:
                        subprocess.run(["git", "clone", auth_url, clone_dir_name], cwd=temp_dir, check=True, capture_output=True, text=True)
                    except subprocess.CalledProcessError as e:
                        self.app.log_ai(f"Clone failed: {e.stderr}")
                        # If clone fails because repo is empty, we might need to init it
                        if "could not find remote branch" in e.stderr.lower() or "empty repository" in e.stderr.lower():
                            self.app.log_ai("Repository seems empty. Initializing...")
                            repo_path = os.path.join(temp_dir, clone_dir_name)
                            os.makedirs(repo_path, exist_ok=True)
                            subprocess.run(["git", "init"], cwd=repo_path, check=True)
                            subprocess.run(["git", "remote", "add", "origin", auth_url], cwd=repo_path, check=True)
                        else:
                            raise e
                            
                    repo_path = os.path.join(temp_dir, clone_dir_name)
                    
                    # Create subfolder
                    target_path = os.path.join(repo_path, subfolder)
                    os.makedirs(target_path, exist_ok=True)
                    
                    # Copy project files (excluding .git)
                    self.app.log_ai(f"Copying files to {subfolder}...")
                    for item in os.listdir(self.app.project_path):
                        if item == ".git": continue
                        s = os.path.join(self.app.project_path, item)
                        d = os.path.join(target_path, item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)
                            
                    # Check for default branch (main or master)
                    branch_check = subprocess.run(["git", "branch", "-r"], cwd=repo_path, capture_output=True, text=True)
                    remote_branches = branch_check.stdout
                    target_branch = "main"
                    if "origin/master" in remote_branches and "origin/main" not in remote_branches:
                        target_branch = "master"
                    
                    # Commit and push
                    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
                    # Check if there are changes to commit
                    status_check = subprocess.run(["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True)
                    if status_check.stdout.strip():
                        subprocess.run(["git", "commit", "-m", f"Push from AI Dev IDE to subfolder: {subfolder}"], 
                                      cwd=repo_path, check=True)
                        
                        self.app.log_ai(f"Pushing to branch: {target_branch}")
                        subprocess.run(["git", "push", "origin", f"HEAD:{target_branch}"], cwd=repo_path, check=True)
                        self.app.log_ai(f"✅ Successfully pushed to {subfolder}")
                        self.app.show_message("Success", f"Project pushed to {subfolder} in the remote repository.")
                    else:
                        self.app.log_ai("No changes detected to push.")
                        self.app.show_message("Info", "No changes detected to push.")
                    
            except Exception as e:
                error_msg = str(e)
                if hasattr(e, 'stderr') and e.stderr:
                    error_msg += f"\nDetails: {e.stderr}"
                self.app.log_ai(f"Push to subfolder failed: {error_msg}")
                self.app.show_message("Error", f"Failed to push to subfolder: {error_msg}")
            
            self.app.update_progress("Push complete", False)
                
        threading.Thread(target=worker, daemon=True).start()
