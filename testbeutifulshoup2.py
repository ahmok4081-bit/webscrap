from bs4 import BeautifulSoup

with open("index.html","r") as f:
    doc = BeautifulSoup(f, "html.parser")
#print(doc.prettify())

tag = doc.find_all("p")[0]
print(tag.find_all("b"))
