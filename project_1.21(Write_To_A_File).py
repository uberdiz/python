import requests
from bs4 import BeautifulSoup
 
base_url = 'https://abcnews.go.com/'
r = requests.get(base_url)
soup = BeautifulSoup(r.text, 'html.parser')

filename = "file_to_save.txt"
#argument one is the name of the file and the second argument is the way you want to access the file 
with open(filename, 'w') as f:
  for story_heading in soup.find_all('h2', class_='News__Item__Headline enableHeadlinePremiumLogo'): 
      if story_heading.a: 
          f.write(story_heading.a.text.replace("\n", " ").strip() + "\n")
      else: 
          f.write(story_heading.contents[0].strip() + "\n")