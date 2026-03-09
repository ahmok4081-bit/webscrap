from bs4 import BeautifulSoup
import requests
with open("index.html","r") as f:
    doc = BeautifulSoup(f, "html.parser")
tag = doc.find_all(text= re.compile("\$.*"))
print(tag)
