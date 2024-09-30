import requests
from bs4 import BeautifulSoup

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
        high_low.append(range_text)

    return name, pps, high_low

# Call the function to extract data
name, pps, high_low = print_all_names()

# Remove the first 10 items from the pps list
pps = pps[10:]

# Print the data together in the desired format
for i in range(min(len(name), len(pps), len(high_low))):
    print(f"{name[i]}, {pps[i]}, {high_low[i]}")
