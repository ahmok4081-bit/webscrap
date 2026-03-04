from bs4 import BeautifulSoup
import requests
url = "https://results.first.global/"
result = requests.get(url)
print(result.text)