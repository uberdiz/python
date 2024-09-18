import requests
from bs4 import BeautifulSoup
url = 'https://abcnews.go.com/'
r = requests.get(url)

# Extracting the HTML content from the request object
r_html = r.text
# Now inside the variable r_html, you have the HTML of the page as a string. Reading (otherwise called parsing) happens with a different Python package.

# Let's use the BeautifulSoup package to parse the HTML
soup = BeautifulSoup(r_html, 'html.parser')
t = soup.title.string

print("Title: ", t)
#print(soup.find_all('h2'))
def print_all_h2s():
    for heading in soup.find_all('h2', class_='News__Item__Headline enableHeadlinePremiumLogo'):
        if heading.a:
            print(heading.a.text.replace("\n", " ").strip())
        else:
            print(heading.contents[0].strip())
print_all_h2s()