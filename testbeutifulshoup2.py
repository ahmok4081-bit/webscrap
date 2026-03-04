from bs4 import BeautifulSoup
import requests
url = "https://www.newegg.ca/intel-core-i9-12th-gen-core-i9-12900k-alder-lake-lga-1700-desktop-cpu-processor/p/N82E16819118339?Item=N82E16819118339"
result = requests.get(url)
doc = BeautifulSoup(result.text, "html.parser")
prices = doc.find_all (text = "$")
parent = prices[0].parent
strong = parent.find('strong')
print(strong.string)