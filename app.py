import tkinter as tk

# Create the main application window
window = tk.Tk()
window.title("Calculator")
window.geometry("400x400")

# Create a frame to hold the greeting label and entry box
input_frame = tk.Frame(window, bg="lightblue", padx=10, pady=10)
input_frame.pack(pady=20)
# Create a label and position it in row 0, column 0
label = tk.Label(input_frame, text="Enter your name:", font=("Arial", 12))
label.grid(row=0, column=0, padx=10, pady=10)

# Create an entry box and position it in row 0, column 1
entry = tk.Entry(input_frame, font=("Arial", 12))
entry.grid(row=0, column=1, padx=10, pady=10)

# Define an event handler function for the button
def greet_user():
    name = entry.get() # Get the text from the entry box
    greeting_label.config(text=f"Hello, {name}!")

# Create a button, link it to the event handler, and position it in row 1, column 0
button = tk.Button(input_frame, text="Greet Me", command=greet_user, font=("Arial", 12))
button.grid(row=1, column=0, columnspan=2, pady=10)

# Create an ouput Frame
output_frame = tk.Frame(window, bg="white", padx=10, pady=10)
output_frame.pack(pady=10)

# Add a label to display the greeting message, positioned in row 2, column 0, spanning 2 columns
greeting_label = tk.Label(output_frame, text="", font=("Arial", 12), bg="white")
greeting_label.grid(row=2, column=0, columnspan=2, pady=10)

# Run the application 
window.mainloop()
