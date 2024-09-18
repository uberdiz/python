import requests
from bs4 import BeautifulSoup
from tkinter import *
url = "http://www.vanityfair.com/society/2014/06/monica-lewinsky-humiliation-culture"
r = requests.get(url)
r_html = r.text
soup = BeautifulSoup(r_html, "html.parser")
t = soup.title.string
print ("Title: ", t)
root=Tk()
#Scroll bar
scrollbar = Scrollbar(root)
scrollbar.pack(side=RIGHT, fill=Y)
mylist = Listbox(root, yscrollcommand=scrollbar.set)
#Title bar
a = Label(root, text="Title: "+ t)
a.pack()
#Text bar
T = Text(root, height=20000, width=250)
T.pack()
# Find all the text in paragraphs
def findText():
    for paragraph in soup.find_all("p", class_="paywall"):
        T.insert(END, paragraph.text.replace("\n", " ").strip())
find = findText()
#Renders all the objects we created
root.mainloop()