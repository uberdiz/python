import requests
from bs4 import BeautifulSoup
import time
import matplotlib.pyplot as plt

# Request the page
url = 'https://www.google.com/finance/markets/most-active?hl=en'
def load_page():
    # Make an HTTP request to fetch the page content
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    return soup
def reload_page():
    # Reload the page at the specified interval
    soup = load_page()
    print(soup.title.string)  # Example of using the parsed content
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
    print("Ran find stocks")
    # Call the function to extract data
    name, pps, perc, high_low = print_all_names()

    # Remove the first 10 items from the pps list
    pps = pps[10:]
    perc = perc[16:67]
    high_low = high_low[5:]

    # Print the data together in the desired format
    f = open("!StockHelper_List.csv", "w")
    for i in range(min(len(name), len(pps), len(perc), len(high_low))):
        f.write(f"{name[i]} , {pps[i]}, {perc[i]}, {high_low[i]}\n")
    f.close()
    print(pps[0])
    return pps
times = 0
y = []
x = []
def graph():
    find_stocks()
    # Convert the stock price to a float (you may need to remove currency symbols first)
    price = float(pps[z + 10].replace('$', '').replace(',', ''))  # Ensure price is numerical
    y.append(price)
def repeat_graph():
    plt.clf()
    x.append(len(x) + 1)
    graph()
    # Reverse the y-axis values to show a higher-to-lower effect
    plt.gca()

    # Naming the x-axis
    plt.ylabel(name[numtotrack - 10])

    # Naming the y-axis
    plt.xlabel("By change in price")

    plt.plot(x, y)
    plt.show()
plt.ion()
soup = load_page()
find_stocks()
choice = input("Choose a company to follow: ")
for z in range(len(name)):
    if name[z] == choice:
        print(f"{choice}'s current price is: {pps[z + 10]}")
        numtotrack = z + 10
        while True:
            pp_copy = pps[z + 10]  # Set the previous value for comparison
            print(f"pps: {pps[z + 10]}")
            print(f"copy: {pp_copy}")
            time.sleep(0.5)
            reload_page()
            find_stocks()
            new_value = pps[z + 10]
            print(f"New value: {new_value}")
                
            if pp_copy != new_value:
                pp_copy = new_value  # Update the `pp_copy` to the new value
                pps[z + 10] = pp_copy  # Store the new value in pps
                repeat_graph()  # Call the graphing function to update the plot
