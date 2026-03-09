import requests
from bs4 import BeautifulSoup

url = 'https://books.toscrape.com'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

divs = soup.find_all("div", class_ = "page_inner")

for div in divs :
    print(div.text)
    