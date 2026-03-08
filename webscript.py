import requests
from bs4 import BeautifulSoup
url = 'https://www.bbc.com/news/live/cz0g2yg3579t'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
headlines = soup.find_all('body')
for x in headlines:
    print(x.text)