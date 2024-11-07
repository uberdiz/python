import tkinter as tk
from tkinter import ttk
import time

# Create the main application window
window = tk.Tk()
window.title("Calculator")
window.geometry("500x400")

# Create the result label
result_label = tk.Label(window, text="", font=("Arial", 12))
result_label.pack(pady=10)

# Label to display the equation
eq_label = tk.Label(window, text="", font=("Arial", 12))
eq_label.pack(pady=10)

# Create a frame to hold the number buttons
number_frame = tk.Frame(window, bg="grey", padx=10, pady=10)
number_frame.pack(pady=10)

n1 = []
n2 = []
sign = ""
count = 0
equ = ""
calculation_done = False
button_color = "#F4743B"
hover_color = "#F79E78"

class CustomButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            relief=tk.FLAT,  # Remove button relief
            bd=0,  # Remove border
            highlightthickness=0,  # Remove highlight
            padx=10,  # Add horizontal padding
            pady=5,  # Add vertical padding
            font=("Arial", 12),  # Set font
            foreground="white",  # Text color
            background=button_color,  # Background color
        )
        # Bind events
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)

    def on_hover(self, event):
        self.config(background=hover_color)  # Change color on hover

    def on_leave(self, event):
        self.config(background=button_color)  # Restore original color



# Function to handle number buttons
def button_number(number):
    global count, sign, equ, calculation_done
    
    # Clear previous result if calculation was done
    if calculation_done:
        n1.clear()
        n2.clear()
        equ = ""
        sign = ""
        count = 0
        calculation_done = False
    
    # Append number to the appropriate list
    if count == 0:
        n1.append(str(number))
        equ = "".join(n1)
    else:
        n2.append(str(number))
        equ = "".join(n1) + sign + "".join(n2)
    eq_label.config(text=equ)

# Function to handle operator buttons
def button_sign(signs):
    global count, sign, equ, calculation_done
    calculation_done = False  # Reset flag when a new operator is pressed
    if signs in ["+", "-", "*", "/"]:
        sign = signs
        count = 1
        equ = "".join(n1) + sign
        eq_label.config(text=equ)
    elif signs == "-/+":
        if count == 0:
            if n1 and n1[0] == "-":
                n1.pop(0)
            else:
                n1.insert(0, "-")
            equ = "".join(n1)
        else:
            if n2 and n2[0] == "-":
                n2.pop(0)
            else:
                n2.insert(0, "-")
            equ = "".join(n1) + sign + "".join(n2)
        eq_label.config(text=equ)
def button_dec():
    global equ, count
    if count == 0:
        n1.append(".")
        equ = "".join(n1)
    else:
        n2.append(".")
        equ = "".join(n1) + sign + "".join(n2)
    eq_label.config(text=equ)
# Function to calculate result
def calculate_result():
    global count, sign, equ, n1, n2, calculation_done
    if n1 and n2:
        num1 = float("".join(n1))
        num2 = float("".join(n2))
        result = 0
        if sign == "+":
            result = num1 + num2
        elif sign == "-":
            result = num1 - num2
        elif sign == "*":
            result = num1 * num2
        elif sign == "/":
            result = num1 / num2 if num2 != 0 else "Error"

        # Display only the result
        eq_label.config(text=str(result))

        # Reset all variables for new calculation
        n1, n2 = list(str(result)), []
        equ, sign, count = str(result), "", 0
        calculation_done = True  # Set flag to indicate calculation completion
def clear_all():
    global n1, n2, equ, sign, count, calculation_done, result
    
    def gradually_clear(label, text_list):
        if text_list:
            text_list.pop()  # Remove the last character
            label.config(text="".join(text_list))  # Update the label text
            label.after(100, gradually_clear, label, text_list)  # Schedule next update
        # Decide whether to clear the result or current equation
    text_to_clear = list(str(result) if calculation_done else equ)
    gradually_clear(eq_label, text_to_clear)
    n1, n2, equ, sign, count, calculation_done, result = [], [], "", "", 0, False, ""
    eq_label.config(text="")
    result_label.config(text="")
# Create buttons with delayed function calls
buttons = [ # (text, row, col)
    ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
    ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
    ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
    ('0', 3, 1), ('+', 0, 3), ('-', 1, 3),
    ('*', 2, 3), ('/', 3, 3), ('=', 4, 3),
    ('-/+', 3, 0), ("C", 4, 4), (".", 3, 2)
]
for (text, row, col) in buttons:
    if text.isdigit():  # Number buttons
        command = lambda txt=text: button_number(int(txt))
    elif text == "=":  # Equal button
        command = calculate_result
    elif text == "C":  # Clear button
        command = clear_all
    elif text == ".":  # Decimal point button
        command = lambda: button_dec()
    else:  # Operator buttons
        command = lambda txt=text: button_sign(txt)
    button = CustomButton(number_frame, text=text, command=command)
    button.grid(row=row, column=col, padx=10, pady=10, columnspan=1, sticky="NSWE")

# Run the application
window.mainloop()
