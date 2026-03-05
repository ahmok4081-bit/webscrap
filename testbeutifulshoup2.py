from bs4 import BeautifulSoup

html = """
<html>
  <body>
    <p class="msg">Hello</p>
    <p class="msg">World</p>
  </body>
</html>
"""

soup = BeautifulSoup(html, "html.parser")

# find() → first match only
first_p = soup.find("p", class_="msg")
print(first_p.text)   # Output: Hello

# find_all() → all matches
all_p = soup.find_all("p", class_="msg")
for p in all_p:
    print(p.text)     # Output: Hello, World
#Use find() when you expect or only care about one element.

#Use find_all() when you want to collect and iterate over multiple elements.

#Think of find() as "give me the first match" and find_all() as "give me everything that matches."