import requests
from bs4 import BeautifulSoup

url = 'https://books.toscrape.com'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

divs = soup.find_all("div")

for book in divs:
    a_tag = book.find("a")
    
    print(a_tag)