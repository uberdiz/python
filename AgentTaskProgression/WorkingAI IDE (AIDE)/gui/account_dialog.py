import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

class AccountDialog:
    def __init__(self, parent, app):
        self.app = app
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Account & API Keys")
        self.dialog.geometry("500x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Apply theme
        if self.app.theme_engine:
            bg = self.app.theme_engine.color_map["window_bg"]
            fg = self.app.theme_engine.color_map.get("window_fg", "#d4d4d4")
            self.dialog.configure(bg=bg)
        
        self.setup_ui()
        
    def setup_ui(self):
        pad = 10
        
        # Title
        ttk.Label(self.dialog, text="Account & External Services", font=("Arial", 12, "bold")).pack(pady=pad)
        
        # Notebook for categories
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill="both", expand=True, padx=pad, pady=pad)
        
        # --- REDIRECT TO SETTINGS ---
        ai_frame = ttk.Frame(notebook)
        notebook.add(ai_frame, text="AI Providers")
        
        ttk.Label(ai_frame, text="AI Provider API keys are now managed in Settings.", font=("Arial", 10)).pack(pady=(20, 10), padx=pad)
        
        def open_settings_api():
            self.dialog.destroy()
            self.app.open_settings()
            # We don't have a direct way to select the API tab yet, 
            # but opening settings is the right direction.
            
        ttk.Button(ai_frame, text="Go to Settings -> Providers", command=open_settings_api).pack(pady=10)
        
        # --- SOURCE CONTROL ---
        git_frame = ttk.Frame(notebook)
        notebook.add(git_frame, text="Source Control")
        
        self.create_key_entry(git_frame, "GitHub Username", "github_username", "")
        self.create_key_entry(git_frame, "GitHub Token", "github_token", "https://github.com/settings/tokens")
        ttk.Label(git_frame, text="Note: Token requires 'repo' and 'user' scopes.", font=("Arial", 8)).pack(pady=5)

        store_frame = ttk.Frame(notebook)
        notebook.add(store_frame, text="Key Store")
        self._setup_store_tab(store_frame)
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=pad, pady=pad)
        
        ttk.Button(btn_frame, text="Save & Close", command=self.save_and_close).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).pack(side="right")
        
    def create_key_entry(self, parent, label_text, setting_key, link_url):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=10, pady=5)
        
        header = ttk.Frame(frame)
        header.pack(fill="x")
        
        ttk.Label(header, text=label_text).pack(side="left")
        if link_url:
            link = tk.Label(header, text="(Get Key)", fg="#4a9eff", cursor="hand2")
            if self.app.theme_engine:
                link.configure(bg=self.app.theme_engine.color_map["window_bg"])
            link.pack(side="left", padx=5)
            link.bind("<Button-1>", lambda e: webbrowser.open(link_url))
            
        entry = ttk.Entry(frame, show="*")
        entry.pack(fill="x", pady=(2, 0))
        
        # Load existing value
        val = self.app.settings.get(setting_key, "")
        if val:
            entry.insert(0, val)
            
        # Store reference to save later
        if not hasattr(self, "entries"):
            self.entries = {}
        self.entries[setting_key] = entry

    def save_and_close(self):
        def encrypt(val):
            try:
                import ctypes, base64
                if not val:
                    return ""
                class DATA_BLOB(ctypes.Structure):
                    _fields_ = [("cbData", ctypes.c_uint), ("pbData", ctypes.c_void_p)]
                buf = ctypes.create_string_buffer(val.encode('utf-8'))
                in_blob = DATA_BLOB(len(buf.raw), ctypes.cast(ctypes.byref(buf), ctypes.c_void_p))
                out_blob = DATA_BLOB()
                if ctypes.windll.crypt32.CryptProtectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
                    try:
                        raw = ctypes.string_at(out_blob.pbData, out_blob.cbData)
                        return "enc:" + base64.b64encode(raw).decode('ascii')
                    finally:
                        ctypes.windll.kernel32.LocalFree(out_blob.pbData)
            except Exception:
                pass
            return val
        changed = False
        for key, entry in self.entries.items():
            new_val = encrypt(entry.get().strip()) if key.endswith("_key") else entry.get().strip()
            if self.app.settings.get(key) != new_val:
                self.app.settings[key] = new_val
                changed = True
        if changed:
            self.app.save_settings(self.app.settings)
            messagebox.showinfo("Saved", "API Keys saved successfully.")
        
        self.dialog.destroy()

    def _setup_store_tab(self, parent):
        top = ttk.Frame(parent)
        top.pack(fill="both", expand=True, padx=10, pady=10)
        cols = ("Provider", "URL", "Key")
        self.store_tree = ttk.Treeview(top, columns=cols, show="headings")
        for c in cols:
            self.store_tree.heading(c, text=c)
            self.store_tree.column(c, width=180 if c != "Key" else 220)
        self.store_tree.pack(fill="both", expand=True)
        btns = ttk.Frame(parent)
        btns.pack(fill="x", padx=10, pady=6)
        ttk.Button(btns, text="Add", command=self._store_add).pack(side="left")
        ttk.Button(btns, text="Edit", command=self._store_edit).pack(side="left", padx=6)
        ttk.Button(btns, text="Delete", command=self._store_delete).pack(side="left")
        self._store_load()

    def _store_load(self):
        for i in self.store_tree.get_children():
            self.store_tree.delete(i)
        store = self.app.settings.get("api_key_store", [])
        for item in store:
            prov = item.get("provider", "")
            url = item.get("url", "")
            key = item.get("key", "")
            masked = ("*" * 24) if key else ""
            self.store_tree.insert("", "end", values=(prov, url, masked))

    def _store_save(self, store):
        self.app.settings["api_key_store"] = store
        self.app.save_settings(self.app.settings)
        self._store_load()

    def _store_add(self):
        self._store_edit_dialog()

    def _store_edit(self):
        sel = self.store_tree.selection()
        if not sel:
            return
        values = self.store_tree.item(sel[0], "values")
        self._store_edit_dialog(initial={"provider": values[0], "url": values[1]})

    def _store_delete(self):
        sel = self.store_tree.selection()
        if not sel:
            return
        values = self.store_tree.item(sel[0], "values")
        store = self.app.settings.get("api_key_store", [])
        new_store = [s for s in store if not (s.get("provider") == values[0] and s.get("url") == values[1])]
        self._store_save(new_store)

    def _store_edit_dialog(self, initial=None):
        d = tk.Toplevel(self.dialog)
        d.title("API Key Entry")
        d.geometry("420x240")
        ttk.Label(d, text="Provider").pack(anchor="w", padx=10, pady=(10,2))
        prov_var = tk.StringVar(value=(initial or {}).get("provider", "openai"))
        prov_cb = ttk.Combobox(d, textvariable=prov_var, values=["openai","huggingface","ollama","anthropic","google","custom"], state="readonly")
        prov_cb.pack(fill="x", padx=10)
        ttk.Label(d, text="Base URL").pack(anchor="w", padx=10, pady=(10,2))
        url_var = tk.StringVar(value=(initial or {}).get("url", ""))
        url_en = ttk.Entry(d, textvariable=url_var)
        url_en.pack(fill="x", padx=10)
        ttk.Label(d, text="API Key").pack(anchor="w", padx=10, pady=(10,2))
        key_var = tk.StringVar(value="")
        key_en = ttk.Entry(d, textvariable=key_var, show="*")
        key_en.pack(fill="x", padx=10)
        status = ttk.Label(d, text="", foreground="gray")
        status.pack(fill="x", padx=10, pady=6)
        def validate_and_save():
            from urllib.parse import urlparse
            prov = prov_var.get().strip().lower()
            url = url_var.get().strip()
            key = key_var.get().strip()
            if url and urlparse(url).scheme not in ("http","https"):
                status.configure(text="Invalid URL")
                return
            if key and len(key) < 20:
                status.configure(text="Key too short")
                return
            store = self.app.settings.get("api_key_store", [])
            for s in store:
                if s.get("provider") == prov and s.get("url","") == url:
                    status.configure(text="Duplicate entry")
                    return
            def enc(v):
                try:
                    import ctypes, base64
                    if not v:
                        return ""
                    class DATA_BLOB(ctypes.Structure):
                        _fields_ = [("cbData", ctypes.c_uint), ("pbData", ctypes.c_void_p)]
                    buf = ctypes.create_string_buffer(v.encode('utf-8'))
                    in_blob = DATA_BLOB(len(buf.raw), ctypes.cast(ctypes.byref(buf), ctypes.c_void_p))
                    out_blob = DATA_BLOB()
                    if ctypes.windll.crypt32.CryptProtectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
                        try:
                            raw = ctypes.string_at(out_blob.pbData, out_blob.cbData)
                            return "enc:" + base64.b64encode(raw).decode('ascii')
                        finally:
                            ctypes.windll.kernel32.LocalFree(out_blob.pbData)
                except Exception:
                    pass
                return v
            store.append({"provider": prov, "url": url, "key": enc(key)})
            self._store_save(store)
            d.destroy()
        ttk.Button(d, text="Save", command=validate_and_save).pack(side="right", padx=10, pady=10)
        ttk.Button(d, text="Cancel", command=d.destroy).pack(side="right", pady=10)
