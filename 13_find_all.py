from bs4 import BeautifulSoup
import requests

website = 'https://subscene.com/movie/Titanic-120338'
response = requests.get(website)
content = response.text

soup = BeautifulSoup(content, 'lxml')

boxes = soup.find_all('script')
for box in boxes:
    print(box.text)