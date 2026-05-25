from __future__ import annotations

from dataclasses import asdict
import re
# from dataclasses import dataclass, field
from typing import List, Literal
import sys
from unittest import case
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import csv
import model as model
import json
import re
from pymongo import MongoClient
import os

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


 

def write_rows_to_csv(fileName: str) -> None:
#    for id, tag, text in zip(ids, tags, texts):
#     rows.append([id, tag, text])
    """Write rows of data to a CSV file with proper handling of newlines and special characters."""
    # with open(filename, "w", newline="", encoding="utf-8") as f:

    # remove all rows that text is empty or just whitespace
    rows_to_write = [row for row in rows if isinstance(row[2], str) and row[2].strip()]
    
    with open(fileName, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f,  dialect=csv.excel, quoting=csv.QUOTE_MINIMAL)
        writer.writerows(rows_to_write)




def extract_tags_from_chapter(chapter_tag: Tag, rows: list, lineNumber: int, plain_text: list) -> list[model.Entry]: 
    entries: list[model.Entry] = []
    entry = model.Entry(rowId=0, keyParts=[], value="")

    paragraphNumber = 0  # Define globally before use
    q1Number = 0
    q2Number = 0
    q3Number = 0
    mNumber = 0
    
    ids = [str]
    tags = [str]
    texts = [str]
    
    verse_qtt = 0
    # chunk = 0
    
    tag_classes = []  # Initialize  tag_classes 
    child_classes = []  # Initialize child_classes 
    nephew_classes = []  # Initialize nephew_classes 
    classes = [] 
   
    for tag in chapter_tag:

        if isinstance(tag, Tag):
            tag_classes = []
            tag_classes = tag.attrs.get('class', [])
            # if tag.attrs.get('class', []) = 'p' then add an integer to the tag_classes list to indicate the paragraph number, and increment the paragraph number for the next paragraph tag
            match tag.attrs.get(['class'][0])[0]:  
                case 'p': 
                    paragraphNumber += 1
                    if 'p' in tag_classes:
                        tag_classes[tag_classes.index('p')] = f"p{paragraphNumber}"
                case 'm':
                    mNumber += 1
                    if 'm' in tag_classes:  
                        tag_classes[tag_classes.index('m')] = f"m{mNumber}" 
                case 'q1':
                    q1Number += 1
                    if 'q1' in tag_classes:
                        tag_classes[tag_classes.index('q1')] = f"q1_{q1Number}"  
                case 'q2':
                    q2Number += 1
                    if 'q2' in tag_classes:
                        tag_classes[tag_classes.index('q2')] = f"q2_{q2Number}"  
                case 'q3':
                    q3Number += 1
                    if 'q3' in tag_classes:
                        tag_classes[tag_classes.index('q3')] = f"q3_{q3Number}"  
                case _:
                    pass

            # check if tag has children, if it does, iterate through the children and print their text content, otherwise print the tag's text content
            for child in tag.children:
                child_classes = []
                
                if isinstance(child, Tag):
                    child_classes = child.attrs.get('class', []) # need to check if it is a note  child_classes = ['note', 'f']
                    nephew_classes = [] 
                    # check if child has children, if it does, iterate through the children and print their text content, otherwise print the child's text content
                    for nephew in child.children:
                        if isinstance(nephew, Tag) and nephew.get_text(strip=True): # check if nephew is a Tag and not empty or just whitespace
                            nephew_classes = nephew.attrs.get('class', [])  # need to check if it is a note  nephew_classes = ['note', 'f'] and ['body']
                            classes = [lineNumber] + tag_classes + child_classes + nephew_classes
                            entry.rowId = lineNumber
                            entry.keyParts = classes
                            #check if classes contains 'note' and 'f', if it does, need split if footenote
                            if {'note', 'f'}.issubset(classes):
                                if len(nephew.get_text(strip=True)) > 1:
                                    _BOUNDARY = re.compile(
                                        r'(?:'
                                        r' # '                             # Type A: explicit " # " separator
                                        r'|'
                                        r'(?<=[.!?"\u201d\u2019\])])\s*'  # Type B: after punctuation (incl. curly quotes)
                                        r')'
                                        r'(tn|sn|tc|map)'                  # capture the prefix
                                        r'(?= )'                           # followed by a space
                                    )

                                    result = _BOUNDARY.sub(r'\n\1', nephew.get_text(strip=True))
                                    footnotes = result.splitlines()
                                    strTemp = ''''''
                                    for i, footenote in enumerate(footnotes):
                                        if footenote.startswith(('#')):
                                                footenote = footenote[1:].strip()  # Remove the leading '#' and any extra whitespace
                                        #a linha abaixo da erro em GKHB gen 3.6, pois o footnote n~ao tem as marcacoes do NET bible (tn|sn|tc|map)
                                        
                                        #XXXX Version GKHB PSALMs 119 ver 30 there is a footnote that does not have the prefix tn/sn/tc/map, so it is not split into two lines, but it should be. Need to find a way to split it into two lines without the prefix
                                        footnote_type, footnote_text = footenote.split(" ", 1)

                                        if i < len(footnotes) - 1:
                                            strTemp += footenote + '\n' 
                                        else:
                                            strTemp += footenote
                                    entry.rowId = lineNumber
                                    entry.value = strTemp
                                    entries.append(entry)
                                    entry = model.Entry(rowId=0, keyParts=[], value="")
                                    print( str(classes)  + "\t" + strTemp)
                                    rows.append([lineNumber, str(classes), strTemp])
                                    lineNumber+=1

                            else: 
                                if {'verse', 'label'}.issubset(classes):
                                    verse_qtt+=1
                                    # XXXX
                                    # add a entry keyParts  plain_text whenever a new verse is scraped
                                    classes = [lineNumber] + tag_classes + child_classes + ["plain_text"]
                                    entry.rowId = lineNumber
                                    entry.value = nephew.get_text(strip=True)
                                    entries.append(entry)
                                    print( str(classes)  + "\t" + nephew.get_text(strip=True))
                                    rows.append([lineNumber, str(classes), nephew.get_text(strip=True)])

                                    entry = model.Entry(rowId=0, keyParts=[], value="") 
                                    lineNumber +=1

                                entry.rowId = lineNumber
                                entry.value = nephew.get_text(strip=True)
                                entries.append(entry)
                                entry = model.Entry(rowId=0, keyParts=[], value="")    
                                print( str(classes)  + "\t" + nephew.get_text(strip=True))      # if classes = ['p1', 'verse', 'v1', 'note', 'f'] nephew.get_text(strip=True) is a footnote content
                                                                                                # if classes = ['s1', 'note', 'f', 'body'] nephew.get_text(strip=True) is footnote content
                                rows.append([lineNumber, str(classes), nephew.get_text(strip=True)])
                                lineNumber+=1
                        else:
                           
                            if nephew.get_text(strip=True): 
                                classes = [lineNumber] + tag_classes + child_classes
                                entry.rowId = lineNumber
                                entry.keyParts = tag_classes + child_classes 
                                entry.value = nephew.get_text(strip=True)
                                entries.append(entry)  
                                entry = model.Entry(rowId=0, keyParts=[], value="")                            
                                print(str(classes)  + "\t" + str(nephew)) # print 's', 'headings'
                                rows.append([lineNumber, str(classes), nephew.get_text(strip=True)])
                                lineNumber+=1
                else:
                    classes = [lineNumber] + tag_classes 
                    entry.keyParts = tag_classes
                    entry.rowId = lineNumber
                    entry.value = child.get_text(strip=True)
                    entries.append(entry)
                    entry = model.Entry(rowId=0, keyParts=[], value="")
                    print(str(classes)  + "\t" + str(child))
                    
                    rows.append([lineNumber, str(classes), str(child)])
                    lineNumber+=1

        else:
            pass
        tag_classes = []  # Reset tag_classes for the next tag
        child_classes = []  # Reset child_classes for the next tag
        nephew_classes = []  # Reset nephew_classes for the next tag
        classes = []  # Reset classes for the next tag
        entry = model.Entry(rowId=0, keyParts=[], value="")

    return entries 
    
def get_chapter_data(version: str, book_id: int, reference: str) -> dict:
    """
    Fetch chapter data from bible.com API.
    
    Args:
        API version:  "3.1" or "3.2"or "3.3"
        book_id: Book ID number
        reference: Chapter reference (e.g., "GEN.1")
    
    Returns:
        JSON response from the API
    """

    url = f"https://nodejs.bible.com/api/bible/chapter/{version}"
    params = {
        "id": book_id,
        "reference": reference
    }
    
    response = requests.get(url, params=params, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def load_ot_books_from_json(path: str) -> List:
    ot = {}
    nt = {}  
    """Load books from a JSON file"""
    with open(path + "/old.json") as f:
        ot = json.load(f)
    return ot

def load_nt_books_from_json(path: str) -> List:
    nt = {}  
    """Load books from a JSON file"""
    with open(path + "/new.json") as f:
        nt = json.load(f)
    return nt


def get_translation_by_id(
    translation_id: str,
    db_name: str = "bible",
    collection_name: str = "translation",
) -> dict | None:
    """Fetch a translation document from MongoDB by translationId."""
    client = MongoClient("mongodb://localhost:27017")
    collection = client[db_name][collection_name]
    return collection.find_one({"translationId": translation_id})


def get_book_from_translation(translation: dict | None, book_id: str) -> dict | None:
    """Return a book object from a translation document by bookId or abbreviation."""
    if not translation:
        return None
    return next(
        (
            book
            for book in translation.get("books", [])
            if book.get("bookId") == book_id or book.get("abbreviation") == book_id
        ),
        None,
    )

def get_chapter_from_book(book: dict | None, chapter_number: int) -> dict | None:
    """Return a chapter object from a book object by chapter number."""
    if not book:
        return None
    return next(
        (chapter for chapter in book.get("chapters", []) if chapter.get("chapter") == chapter_number),
        None,
    )

def dict_to_entry(entry: dict) -> model.Entry:
    return model.Entry(
        rowId=entry.get("rowId", 0),
        keyParts=entry.get("keyParts", []),
        value=entry.get("value", ""),
    )

def dict_to_chapter(chapter: dict) -> model.ChapterDoc:
    return model.ChapterDoc(
        chapter=chapter.get("chapter", 0),
        entries=[dict_to_entry(entry) for entry in chapter.get("entries", [])],
    )

def dict_to_book(book: dict) -> model.BookDoc:
    return model.BookDoc(
        bookId=book.get("bookId", ""),
        title=book.get("title"),
        abbreviation=book.get("abbreviation"),
        chapters=[dict_to_chapter(chapter) for chapter in book.get("chapters", [])],
    )

def dict_to_translation(translation: dict) -> model.TranslationDoc:
    return model.TranslationDoc(
        translationId=translation.get("translationId", ""),
        name=translation.get("name", ""),
        abbreviation=translation.get("abbreviation", ""),
        language=translation.get("language", ""),
        copyright=translation.get("copyright", ""),
        books=[dict_to_book(book) for book in translation.get("books", [])],
    )

def find_book_in_translation_doc(
    translation: model.TranslationDoc,
    book_id: str,
) -> model.BookDoc | None:
    return next(
        (
            book
            for book in translation.books
            if book.bookId == book_id or book.abbreviation == book_id
        ),
        None,
    )

def find_chapter_in_book_doc(
    book: model.BookDoc,
    chapter_number: int,
) -> model.ChapterDoc | None:
    return next(
        (chapter for chapter in book.chapters if chapter.chapter == chapter_number),
        None,
    )

def get_chapter_document(
    translation_id: str,
    book_id: str,
    chapter_number: int,
    db_name: str = "bible",
    collection_name: str = "translation",
) -> dict | None:
    """Fetch a chapter nested doc by translationId, bookId, and chapter number."""
    translation = get_translation_by_id(translation_id, db_name, collection_name)
    book = get_book_from_translation(translation, book_id)
    return get_chapter_from_book(book, chapter_number)


if __name__ == "__main__":
    import sys
    rows = [["id","tag","text"]]
    lineNumber = 0
    # ot and nt files not needed since we extract book titles directly from response

    book_chapter = "GEN.1"
    # book_chapter = "GEN.2"
    # bookChapter = "GEN.3"
    # bookChapter = "GEN.4"
    # bookChapter = "PSA.77"
    # book_chapter = "PSA.119"  
    # bookChapter = "MRK.1"
    # bookChapter = "ROM.1"
    # bookChapter = "ACT.20"
    # bookChapter = "REV.21"

    bibleId = 107 # NET Bible
    # bibleId = 2287  #GKHB
    # bibleId = 1270  #KOV
    # bibleId = 1930 #  NVT
    # bibleId = 1608 # ARA



    # for book_name, book_data in ot.items():
    #     book_id = book_data["book_id"]
    #     # Loop through each chapter (1-indexed based on the index in the chapters list)
    #     for chapter_num in range(1, len(book_data["chapters"]) + 1):
    #         lineNumber = 0
    #         book_chapter = f"{book_id}.{chapter_num}"
    #         print(book_chapter)  # Outputs: GEN.1, GEN.2, ..., EXO.1, etc.

    response = get_chapter_data("3.3", bibleId, book_chapter)

    chapterCode = response['reference']['usfm'][0]
    # response['next']['usfm'][0] has the next chapter to scrap
    
    bookName  = response['reference']['human']
    bookAbbreviation, chapter_num = chapterCode.split(".")
    if " " in bookName:
        bookName = bookName.rsplit(" ", 1)[0]


    versionId = response['reference']['version_id']
    match versionId:  
        case 107: 
            translationAbbreviation = "NET"
            translationName = "New English Translation"
            language = "English"
        case 2287: 
            translationAbbreviation = "GKHB"
            translationName = "Global Khmer Bible"
            language = "Khmer"
        case 1270: 
            translationAbbreviation = "KOV"
            translationName = "Khmer Old Version"
            language = "Khmer"
        case 1930: 
            translationAbbreviation = "NVT"
            translationName = "Nova Versão Transformadora"
            language = "Portuguese"
        case 1608: 
            translationAbbreviation = "ARA"
            translationName = "Almeida Revista e Atualizada"
            language = "Portuguese"

    copyright = response['copyright']['html']

    
    soup = BeautifulSoup(copyright, "html.parser")
    # This removes all tags and returns just the text
    clean_text = soup.get_text()
    copyrightText = response['copyright']['text']

    translation: model.TranslationDoc | None = None
    book: model.BookDoc | None = None
    chapter: model.ChapterDoc | None = None

    translation = get_translation_by_id(translationAbbreviation, db_name="bible", collection_name="translation")
    if isinstance(translation, dict):
        translation = dict_to_translation(translation)

    if isinstance(translation, model.TranslationDoc):
        book = find_book_in_translation_doc(translation, bookAbbreviation)
    else:
        book_dict = get_book_from_translation(translation, bookAbbreviation)
        if isinstance(book_dict, dict):
            book = dict_to_book(book_dict)

    if isinstance(book, model.BookDoc):
        chapter = find_chapter_in_book_doc(book, int(chapter_num))
    elif isinstance(book, dict):
        chapter = get_chapter_from_book(book, int(chapter_num))
        if isinstance(chapter, dict):
            chapter = dict_to_chapter(chapter)

    if translation is None:
        translation = model.TranslationDoc( translationId = translationAbbreviation,   name= translationName, abbreviation= translationAbbreviation,  language=language,copyright=copyrightText, books = [])
    if book is None:
        book = model.BookDoc(bookId = bookAbbreviation, title = bookName, abbreviation = bookAbbreviation, chapters = [])

    if chapter is None:   
        chapter = model.ChapterDoc(chapter = int(chapter_num), entries = [])
    

    textHtml = BeautifulSoup(response['content'], 'lxml')

    # XXXX ================================================ 
    # need to check, gen 1 is generting 33 verses instead of 31
    # texto_html = BeautifulSoup(
    # self.__capitulo_atual['content'], 'html.parser')

    

    verse_reg_expression = re.compile(r'\d+')
    plain_text = []
    # plain_text[0] = "In the beginning God created the heavens and the earth."
    # plain_text[1] = "Now the earth was formless and empty, darkness was over the surface of the deep, and the Spirit of God was hovering over the waters."
    i = 0; 
    for verse in textHtml.find_all(
            'span', {'data-usfm': re.compile("GEN" + '.[0-9]*')}):
        verse_number = int(verse_reg_expression.findall(
            verse.attrs['class'][1])[0])

        temp_var = ''.join([s.get_text() for s in verse.find_all(
            'span', {'class': 'content'})])
        plain_text.append(temp_var)
        

        # remove all spaces, tabs and newlines from plain_text
        if not plain_text[i].strip():
            continue
        i += 1
        # ================================================ 


    # if I use class="book" it will not work, because the structure is based on 3 levels after chapter 
    # chapter_tag: Tag | None = textHtml.find(class_="book")
    # 2,"['chapter', 'ch1', 'label']",1
    chapter_tag: Tag | None = textHtml.find(class_="chapter")


    if chapter_tag:
        # Define output directories
        json_dir = os.path.join("app", "json", bookAbbreviation)
        txt_dir = os.path.join("app", "txt", bookAbbreviation)
        csv_dir = os.path.join("app", "csv", bookAbbreviation)

        # Ensure directories exist
        os.makedirs(json_dir, exist_ok=True)
        os.makedirs(txt_dir, exist_ok=True)
        os.makedirs(csv_dir, exist_ok=True)

        chapter_num = int(chapter_num)
        filename = translationAbbreviation + "_" + bookAbbreviation + "_" + f"{chapter_num:03d}"

        fileName_txt = os.path.join(txt_dir, f"{filename}.txt")
        rows.append([lineNumber, book_chapter,versionId])
        lineNumber+=1
        with open(fileName_txt, "w", encoding="utf-8") as _f:
            sys.stdout = _f
            
            entries = extract_tags_from_chapter(chapter_tag, rows,lineNumber, plain_text)
            chapter.entries = entries

            existing_book = None
            if isinstance(translation, model.TranslationDoc):
                existing_book = find_book_in_translation_doc(translation, bookAbbreviation)

            if existing_book is None:
                if book is None:
                    book = model.BookDoc(bookId=bookAbbreviation, title=bookName, abbreviation=bookAbbreviation, chapters=[])
                translation.books.append(book)
            else:
                book = existing_book

            existing_chapter = None
            if isinstance(book, model.BookDoc):
                existing_chapter = find_chapter_in_book_doc(book, int(chapter_num))

            if existing_chapter is None:
                book.chapters.append(chapter)
            else:
                existing_chapter.entries = entries
                chapter = existing_chapter

            client = MongoClient("mongodb://localhost:27017")
            db = client["bible"]
            collection = db["translation"]

            # Create a separate, clean document just for the current chapter's JSON file
            current_chapter_only_book = model.BookDoc(
                bookId=book.bookId,
                title=book.title,
                abbreviation=book.abbreviation,
                chapters=[chapter]
            )
            current_book_only_translation = model.TranslationDoc(
                translationId=translation.translationId,
                name=translation.name,
                abbreviation=translation.abbreviation,
                language=translation.language,
                copyright=translation.copyright,
                books=[current_chapter_only_book]
            )
            doc_json = asdict(current_book_only_translation)

            # create a json file =================================================
            fileNameJson = os.path.join(json_dir, f"{filename}.json")
            with open(fileNameJson, "w", encoding="utf-8") as f:
                json.dump(doc_json, f, ensure_ascii=False, indent=2)
                
            # inserting using json file =================================================
            # client = MongoClient("mongodb://localhost:27017")
            # db = client["your_db"]
            # collection = db["your_collection"]

            # with open(fileNameJson, "r", encoding="utf-8") as f:
            #     doc = json.load(f)

            # collection.insert_one(doc)
            # inserting using json file =================================================

            # For MongoDB, write the entire accumulated translation (all books & chapters)
            doc_db = asdict(translation)
            existing = collection.find_one({"translationId": translation.translationId})
            if existing:
                doc_db["_id"] = existing["_id"]
                collection.replace_one({"_id": existing["_id"]}, doc_db)
            else:
                collection.insert_one(doc_db)

            fileNameCsv = os.path.join(csv_dir, f"{filename}.csv")
            write_rows_to_csv(fileNameCsv)
        
    else:
        print("Chapter tag not found")

    # Restore stdout
    sys.stdout = sys.__stdout__  
            

# usfm tags_
# \p	Normal paragraph	Indented
# \m	Paragraph (no indent)	❌ No indent
# \q	Poetry / quote	Styled (indent varies)
# .verse
# .content
# .note
# tn/sn/tc
# sc small caps?
               