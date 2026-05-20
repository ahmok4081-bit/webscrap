import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import urljoin

url = "https://books.toscrape.com"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

all_books = soup.find_all("article", class_="product_pod")

for book in all_books[:5]:
    title = book.h3.a["title"]
    price = book.find("p", class_="price_color").text
    rating = book.find("p", class_="star-rating")["class"][1]
    link = urljoin(url, book.h3.a["href"])
    avaliblelity = book.find('p', class_="instock availability").text.strip()

    print(title)
    print(price)
    print(rating)
    print(avaliblelity)
    print(link)
    print(avaliblelity)
   # print(star)