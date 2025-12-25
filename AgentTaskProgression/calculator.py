import tkinter as tk
from tkinter import ttk
import math

class Calculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Advanced Calculator")
        self.geometry("400x600")
        self.configure(bg="#1e1e1e")
        self.resizable(False, False)
        
        self.expression = ""
        self.history = []
        
        self.setup_ui()
        self.style_widgets()

    def setup_ui(self):
        # Display Area
        self.display_frame = tk.Frame(self, bg="#1e1e1e", pady=20, padx=20)
        self.display_frame.pack(fill="both")
        
        self.history_label = tk.Label(self.display_frame, text="", bg="#1e1e1e", fg="#888888", font=("Segoe UI", 12), anchor="e")
        self.history_label.pack(fill="x")
        
        self.result_var = tk.StringVar(value="0")
        self.result_label = tk.Label(self.display_frame, textvariable=self.result_var, bg="#1e1e1e", fg="#ffffff", font=("Segoe UI", 36, "bold"), anchor="e")
        self.result_label.pack(fill="x")

        # Buttons Area
        self.buttons_frame = tk.Frame(self, bg="#1e1e1e", padx=10, pady=10)
        self.buttons_frame.pack(fill="both", expand=True)

        buttons = [
            ('C', 0, 0, "#ff5f56"), ('(', 0, 1, "#3e3e42"), (')', 0, 2, "#3e3e42"), ('/', 0, 3, "#0e639c"),
            ('sin', 1, 0, "#3e3e42"), ('cos', 1, 1, "#3e3e42"), ('tan', 1, 2, "#3e3e42"), ('*', 1, 3, "#0e639c"),
            ('7', 2, 0, "#2d2d2d"), ('8', 2, 1, "#2d2d2d"), ('9', 2, 2, "#2d2d2d"), ('-', 2, 3, "#0e639c"),
            ('4', 3, 0, "#2d2d2d"), ('5', 3, 1, "#2d2d2d"), ('6', 3, 2, "#2d2d2d"), ('+', 3, 3, "#0e639c"),
            ('1', 4, 0, "#2d2d2d"), ('2', 4, 1, "#2d2d2d"), ('3', 4, 2, "#2d2d2d"), ('log', 4, 3, "#3e3e42"),
            ('0', 5, 0, "#2d2d2d"), ('.', 5, 1, "#2d2d2d"), ('^', 5, 2, "#3e3e42"), ('=', 5, 3, "#4caf50"),
            ('sqrt', 6, 0, "#3e3e42"), ('pi', 6, 1, "#3e3e42"), ('e', 6, 2, "#3e3e42"), ('ln', 6, 3, "#3e3e42")
        ]

        for (text, row, col, color) in buttons:
            btn = tk.Button(self.buttons_frame, text=text, width=5, height=2, 
                            bg=color, fg="white", font=("Segoe UI", 14), 
                            relief="flat", activebackground="#444444", activeforeground="white",
                            command=lambda t=text: self.on_button_click(t))
            btn.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)

        for i in range(7):
            self.buttons_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            self.buttons_frame.grid_columnconfigure(i, weight=1)

    def style_widgets(self):
        style = ttk.Style()
        style.theme_use('clam')

    def on_button_click(self, char):
        if char == 'C':
            self.expression = ""
            self.result_var.set("0")
            self.history_label.config(text="")
        elif char == '=':
            try:
                # Replace scientific functions with math module equivalents
                expr = self.expression.replace('sin', 'math.sin').replace('cos', 'math.cos').replace('tan', 'math.tan')
                expr = expr.replace('log', 'math.log10').replace('ln', 'math.log').replace('sqrt', 'math.sqrt')
                expr = expr.replace('pi', 'math.pi').replace('e', 'math.e').replace('^', '**')
                
                result = eval(expr)
                self.history_label.config(text=f"{self.expression} =")
                self.result_var.set(str(round(result, 8)))
                self.expression = str(result)
            except Exception as e:
                self.result_var.set("Error")
                self.expression = ""
        else:
            if char in ['sin', 'cos', 'tan', 'log', 'ln', 'sqrt']:
                self.expression += f"{char}("
            else:
                self.expression += str(char)
            self.result_var.set(self.expression)

if __name__ == "__main__":
    app = Calculator()
    app.mainloop()
