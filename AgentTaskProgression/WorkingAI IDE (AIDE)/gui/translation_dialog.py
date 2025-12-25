import tkinter as tk
from tkinter import ttk, messagebox

class TranslationDialog:
    def __init__(self, parent, filename):
        self.filename = filename
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Translate Script: {filename}")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text=f"Translating: {self.filename}", font=("Arial", 10, "bold")).pack(pady=(0, 10))
        
        ttk.Label(main_frame, text="Select Target Language:").pack(anchor="w")
        
        self.languages = ["Python", "JavaScript", "C++", "C#", "Lua", "Go", "Java", "Rust"]
        self.lang_var = tk.StringVar(value="Python")
        self.lang_combo = ttk.Combobox(main_frame, textvariable=self.lang_var, values=self.languages, state="readonly")
        self.lang_combo.pack(fill="x", pady=5)
        
        self.copy_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Create a new copy instead of overwriting", variable=self.copy_var).pack(anchor="w", pady=10)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", side="bottom")
        
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Translate", command=self.translate).pack(side="right")
        
    def translate(self):
        self.result = {
            "language": self.lang_var.get(),
            "make_copy": self.copy_var.get()
        }
        self.dialog.destroy()

def ask_translation(parent, filename):
    dialog = TranslationDialog(parent, filename)
    parent.wait_window(dialog.dialog)
    return dialog.result
