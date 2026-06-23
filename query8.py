import json
import sys
# Load the JSON file
with open("g:/src/python/scrap_mongoDB/app/json/ESV/NT/03_LUK/ESV_LUK_015.json", "r", encoding="utf-8") as f:
    data = json.load(f)
# # Option A: List comprehension (concise)
# # plain_text_entries = [
# #     {entry["keyParts"][0]: entry["value"]}
# #     for book in data.get("books", [])
# #     for chapter in book.get("chapters", [])
# #     for entry in chapter.get("entries", [])
# #     if entry.get("keyParts") and "plain_text" in entry.get("keyParts", [])
# # ]
# # Option B: Standard loop (easy to debug/extend)
plain_text_entries = []
for book in data.get("books", []):
    for chapter in book.get("chapters", []):
        for entry in chapter.get("entries", []):
            if entry.get("keyParts") and "plain_text" in entry.get("keyParts", []):
                plain_text_entries.append({entry["keyParts"][0]: entry["value"]})

# add portuguese translation
# with open("g:/src/python/scrap_mongoDB/app/json/NVT/NT/03_LUK/NVT_LUK_015.json", "r", encoding="utf-8") as f:
#     data = json.load(f)

# for book in data.get("books", []):
#     for chapter in book.get("chapters", []):
#         for entry in chapter.get("entries", []):
#             if entry.get("keyParts") and "plain_text" in entry.get("keyParts", []):
#                 plain_text_entries.append({entry["keyParts"][0]: entry["value"]})

# add khmer KOV  translation
# with open("g:/src/python/scrap_mongoDB/app/json/KOV/NT/03_LUK/KOV_LUK_015.json", "r", encoding="utf-8") as f:
#     data = json.load(f)

# for book in data.get("books", []):
#     for chapter in book.get("chapters", []):
#         for entry in chapter.get("entries", []):
#             if entry.get("keyParts") and "plain_text" in entry.get("keyParts", []):
#                 plain_text_entries.append({entry["keyParts"][0]: entry["value"]})

# # add khmer GKH translation
with open("g:/src/python/scrap_mongoDB/app/json/GKH/NT/03_LUK/GKH_LUK_015.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for book in data.get("books", []):
    for chapter in book.get("chapters", []):
        for entry in chapter.get("entries", []):
            if entry.get("keyParts") and "plain_text" in entry.get("keyParts", []):
                plain_text_entries.append({entry["keyParts"][0]: entry["value"]})

plain_text_entries.sort(key=lambda entry: next(iter(entry)))
# Order the extracted entries by their key in descending order
# plain_text_entries.sort(key=lambda entry: next(iter(entry)), reverse=True)

with open("g:/src/python/scrap_mongoDB/app/csv/CMP/NT/03_LUK/CMP_LUK_015.txt", "w", encoding="utf-8") as _f:
    sys.stdout = _f


    # Print the extracted entries as key;value
    for entry in plain_text_entries:
        key = next(iter(entry))
        print(f"{key}\t{entry[key]}")
