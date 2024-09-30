import requests
from bs4 import BeautifulSoup
import time
import matplotlib.pyplot as plt

# Request the page
url = 'https://www.google.com/finance/markets/most-active?hl=en'
r = requests.get(url)

# Extract the HTML content
r_html = r.text

# Parse the HTML using BeautifulSoup
soup = BeautifulSoup(r_html, 'html.parser')

# Get the title of the page
t = soup.title.string
print("Title: ", t)

# Lists to store extracted data
name = []
pps = []
perc = []
high_low = []

# Function to print all names
def print_all_names():
    # Extract stock names
    for heading in soup.find_all('div', class_='ZvmM7'):
        # If the heading has a link, extract text from the link
        if heading.a:
            name_text = heading.a.text.strip()
        else:
            name_text = heading.contents[0].strip()
        name.append(name_text)
    
    # Extract stock price (current price per share)
    for price in soup.find_all('div', class_='YMlKec'):
        pps_text = price.text.strip()
        pps.append(pps_text)
    
    # Extract high/low range (if available)
    for range_info in soup.find_all('div', class_='JwB6zf'):
        range_text = range_info.text.strip()
        perc.append(range_text)

    for hl in soup.find_all("span", {"class":["P2Luy Ebnabc", "P2Luy Ez2Ioe"]}):
        hl_text = hl.text.strip()
        high_low.append(hl_text)
    return name, pps, perc, high_low
def find_stocks():
    # Call the function to extract data
    name, pps, perc, high_low = print_all_names()

    # Remove the first 10 items from the pps list
    pps = pps[10:]
    perc = perc[16:67]
    high_low = high_low[5:]

    # Print the data together in the desired format
    f = open("!StockHelper_List.csv", "a")
    for i in range(min(len(name), len(pps), len(perc), len(high_low))):
        f.write(f"{name[i]} , {pps[i]}, {perc[i]}, {high_low[i]}\n")
    f.close()
times = 0
y = []
x = [1,2,3]
def graph():
    find_stocks()
    y.append(high_low[0]) 
plt.show()
graph()
time.sleep(10)
graph()
time.sleep(10)
graph()
# naming the x axis
plt.ylabel(name[0])
# naming the y axis
plt.xlabel("Time by 10 sec")
plt.plot(x, y)
plt.show()
'''running = True
while running:
    find_stocks()
    time.sleep(10)'''
