import requests
from bs4 import BeautifulSoup

url = 'https://books.toscrape.com'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

prices = soup.find_all("p", class_="price_color")

for price in prices:
    print(price.text)
    