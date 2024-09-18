from tkinter import *
# This handle allows us to put the contents in the window and reconfigure it as necessary.
# Now we create a root widget/window, by calling the Tk()
root=Tk()
#Now we create a Label widget as a child to the root window.
a = Label(root, text="Hello, world!")
#Fits the screen to the text
a.pack()
#Renders all the objects we created
root.mainloop()