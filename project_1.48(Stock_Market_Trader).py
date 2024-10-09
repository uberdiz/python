import requests
from bs4 import BeautifulSoup
import time
import matplotlib.pyplot as plt

# Request the page
#url = 'https://www.google.com/finance/markets/most-active?hl=en'
url = 'https://www.google.com/finance/markets/indexes/americas'

def load_page():
    # Make an HTTP request to fetch the page content
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    return soup

def reload_page():
    # Reload the page to fetch updated stock data
    return load_page()

# Lists to store extracted data
name = []
pps = []
perc = []
high_low = []

# Function to print all names and prices
def print_all_names(soup):
    global name, pps, perc, high_low
    name.clear()
    pps.clear()
    perc.clear()
    high_low.clear()

    # Extract stock names
    for heading in soup.find_all('div', class_='ZvmM7'):
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

def find_stocks(soup):
    # Extract and update stock data
    name, pps, perc, high_low = print_all_names(soup)

    # Remove irrelevant items from the lists
    pps = pps[10:]
    perc = perc[16:67]
    high_low = high_low[5:]
    return pps

y = []
x = []

def repeat_graph():
    plt.clf()  # Clear the previous plot
    x.append(len(x) + 1)  # Increment x-axis
    y.append(float(pps[numtotrack].replace('$', '').replace(',', ''))) # Add the new stock price
    # Naming the x-axis and y-axis
    plt.ylabel(name[numtotrack - 10])
    plt.xlabel("Price Change Event")

    plt.plot(x, y)
    plt.show()

plt.ion()  # Turn on interactive plotting

# Initial load of the page and stock data
soup = load_page()
find_stocks(soup)
choice = input("Choose a company to follow: ")

# Find the index of the chosen stock
for z in range(len(name)):
    if name[z] == choice:
        print(f"{choice}'s current price is: {pps[z + 10]}")
        numtotrack = z + 10
        # Start monitoring and updating the graph only if the stock price changes
        pp_copy = pps[numtotrack]  # Set initial stock price to track
        while True:
            print(f"Current price of {name[numtotrack - 10]}: {pps[numtotrack]}")
            time.sleep(0.5)  # Wait for 0.5 seconds before reloading the page

            # Reload the page and fetch updated stock data
            soup = reload_page()
            find_stocks(soup)
            new_value = pps[numtotrack]  # Get the updated stock price
            
            if pp_copy != new_value:  # Detect price change
                pp_copy = new_value  # Update the previous stock price
                print(f"Price changed to: {new_value}")
                repeat_graph()  # Update the graph with new data only on price change