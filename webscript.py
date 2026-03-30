import requests
from bs4 import BeautifulSoup
import csv

with open("books.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Title", "Price", "Rating", "Link"])

    for page in range(1, 51):   # change to 51 later
        url = f"https://books.toscrape.com/catalogue/page-{page}.html"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        all_books = soup.find_all("article", class_="product_pod")

        for book in all_books:
            title = book.h3.a["title"]
            price = book.find("p", class_="price_color").text
            rating = book.find("p", class_="star-rating")["class"][1]
            link = book.h3.a["href"]

            writer.writerow([title, price, rating, link])

print("Done scraping!")