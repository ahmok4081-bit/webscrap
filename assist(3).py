"""
bible_structure.py
──────────────────
Hierarchical data structure for bible.com NET Bible chapters.

PYTHON OBJECT HIERARCHY
═══════════════════════
ChapterPage
 ├── book, chapter, version, title, source_url
 └── sections[]
      ├── heading         (str | None)
      │     └── footnotes[]
      │               ├── type    ("tn" | "sn" | "tc" | "unknown")
      │               └── text    (str — full note body)
      │   
      └── paragraphs[]
           └── verses[]
                ├── number     (int | None)
                └── chunks[]
                     ├── text          (str — Bible text fragment)
                     └── footnotes[]
                          ├── type    ("tn" | "sn" | "tc" | "unknown")
                          └── text    (str — full note body)

HOW THE RAW TEXT IS STRUCTURED
═══════════════════════════════
The raw paragraph text uses '#' as the delimiter between Bible text and footnotes:

    "1 In the beginning#tn Note body.sn Another note. God#sn Note. created#tn Note."
     ─── bible ─────── ─── notes block ─────────────────── ─── notes ─── ────────

  - '#' always introduces a footnote block.
  - Inside a block, multiple notes are concatenated after punctuation:
        "tn First note body.sn Second note body."
  - The note type is the first 2 characters: tn / sn / tc.
  - Trailing bible text (e.g. "God", "created") lives at the END of a
    non-last block, after the final note's closing punctuation.

FOOTNOTE TYPES
══════════════
  tn  Translator's Note   -- translation choices, Hebrew/Greek word meanings
  sn  Study Note          -- biblical, historical, theological context
  tc  Textual Criticism   -- manuscript variants and textual traditions
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

import requests
from bs4 import BeautifulSoup, NavigableString, Tag


# ── Constants ─────────────────────────────────────────────────────────────────

FootnoteType = Literal["tn", "sn", "tc", "unknown"]
# https://bible.org/list-abbreviations-net-bible-footnotes
KNOWN_PREFIXES: set[str] = {"tn", "sn", "tc", " map"}

CLS_HEADING = "s1"
CLS_CHAPTER = "chapter"
CLS_P       = "p"
CLS_FT      = "ft"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Note boundary: start-of-string OR after punctuation, then known prefix + space
_NOTE_BOUNDARY = re.compile(r'(?:^|(?<=[.!?"\])])) *(tn|sn|tc|map)(?= )')




# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class Footnote:
    """One tn / sn / tc annotation attached to a Bible text chunk."""
    type: FootnoteType
    text: str

    def __repr__(self) -> str:
        return f"Footnote(type={self.type!r}, text={self.text[:60]!r})"


@dataclass
class Chunk:
    """
    Atomic unit: a Bible text fragment + its immediately following footnotes.
    Preserves the inline order the text will be displayed:
        text -> [fn, fn, ...] -> next text -> [fn] -> ...
    """
    text: str
    footnotes: list[Footnote] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Chunk({self.text[:45]!r}, fns={len(self.footnotes)})"


@dataclass
class Verse:
    """One verse (or unnumbered poetic line) composed of ordered Chunks."""
    number: int | None
    chunks: list[Chunk] = field(default_factory=list)

    @property
    def plain_text(self) -> str:
        return " ".join(c.text for c in self.chunks if c.text).strip()

    @property
    def all_footnotes(self) -> list[Footnote]:
        return [fn for chunk in self.chunks for fn in chunk.footnotes]

    def footnotes_by_type(self, ftype: FootnoteType) -> list[Footnote]:
        return [fn for fn in self.all_footnotes if fn.type == ftype]

    def __repr__(self) -> str:
        return (
            f"Verse(number={self.number}, "
            f"chunks={len(self.chunks)}, "
            f"footnotes={len(self.all_footnotes)})"
        )


@dataclass
class Paragraph:
    """One <div class='__p'> block -- a group of consecutive verses."""
    verses: list[Verse] = field(default_factory=list)

    @property
    def plain_text(self) -> str:
        return " ".join(v.plain_text for v in self.verses).strip()

    def __repr__(self) -> str:
        return f"Paragraph(verses={len(self.verses)})"


@dataclass
class Section:
    """One heading + its paragraphs.
    heading_footnotes holds any footnotes attached directly to the heading
    (e.g. the psalm-intro note on Psalm 119).
    """
    heading:            str | None
    heading_footnotes:  list[Footnote] = field(default_factory=list)
    paragraphs:         list[Paragraph] = field(default_factory=list)

    def __repr__(self) -> str:
        fn = f", {len(self.heading_footnotes)} fn" if self.heading_footnotes else ""
        return f"Section(heading={self.heading!r}{fn}, paragraphs={len(self.paragraphs)})"


@dataclass
class ChapterPage:
    """Root object for one scraped Bible chapter page."""
    book:       str
    chapter:    int
    version:    str
    title:      str
    source_url: str
    sections:   list[Section] = field(default_factory=list)

    @property
    def all_paragraphs(self) -> list[Paragraph]:
        return [p for s in self.sections for p in s.paragraphs]

    @property
    def all_verses(self) -> list[Verse]:
        return [v for p in self.all_paragraphs for v in p.verses]

    @property
    def all_footnotes(self) -> list[Footnote]:
        return [fn for v in self.all_verses for fn in v.all_footnotes]

    def footnotes_by_type(self, ftype: FootnoteType) -> list[Footnote]:
        return [fn for fn in self.all_footnotes if fn.type == ftype]

    def __repr__(self) -> str:
        return (
            f"ChapterPage(book={self.book!r}, chapter={self.chapter}, "
            f"version={self.version!r}, "
            f"sections={len(self.sections)}, "
            f"verses={len(self.all_verses)}, "
            f"footnotes={len(self.all_footnotes)} "
            f"[tn={len(self.footnotes_by_type('tn'))} "
            f"sn={len(self.footnotes_by_type('sn'))} "
            f"tc={len(self.footnotes_by_type('tc'))} " 
            f"map={len(self.footnotes_by_type('map'))}])"
        )
# ── API Functions ─────────────────────────────────────────────────────────────

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


if __name__ == "__main__":
    import sys

    bookChapter = "GEN.3"
    bookChapter = "GEN.1"
    # bookChapter = "PSA.119"
    bibleId = 107 # NET Bible
    response = get_chapter_data("3.3", bibleId, bookChapter)

    # with open("output_" + bookChapter  + "_" + str(bibleId) + ".xml", "w", encoding="utf-8") as _f:
    #         sys.stdout = _f
    #         print(response['content'])
    #         sys.stdout = sys.__stdout__


    # print(response['previous'] ) #{'canonical': True, 'usfm': ['GEN.2'], 'human': 'Genesis 2', 'toc': True, 'version_id': 107}
    # print(response['next'] ) # {'canonical': True, 'usfm': ['GEN.4'], 'human': 'Genesis 4', 'toc': True, 'version_id': 107}

    chapterCode = response['reference']['usfm'][0]
    title  = response['reference']['human']
    book, chapter = chapterCode.split(".")
    version_id = response['reference']['version_id']
    copyright = response['copyright']['html']
    soup = BeautifulSoup(copyright, "html.parser")
    # This removes all tags and returns just the text
    clean_text = soup.get_text()
    copyrightText = response['copyright']['text']
    

    cp = ChapterPage(
        book=book, chapter=chapter, version=version_id,
        title=title, source_url='https://nodejs.bible.com/api/bible/chapter/{version}?id={book_id}&reference={reference}'.format(version="3.3", book_id=bibleId, reference=bookChapter)
    )


    textHtml = BeautifulSoup(response['content'], 'lxml')

    # get all s1 and p elements, which contain the headings, verses and footnotes
    tags = textHtml.find_all(class_ = ["s1", "p", "verse", "ft"]) 
    # items = textHtml.select('.s1 .p')
    paragraphNumber = 1
    
    for tag in tags:
        # footnotes:  list[Footnote] = []
        # print("ITEM: " + str(tag.name) + "  " + str(tag.attrs.get("class")))
        # print("ITEM TEXT: " + tag.get_text(strip=True))

        # print(item.get_text(strip=True))
        # item.attrs = {'class': ['s1']} how to compare is it is equal "s1"
        # IS THERE SWITCH IN PYTHON
        print(tag.attrs.get(['class'][0])[0])

        match tag.attrs.get(['class'][0])[0]:  
            case 's1': 
                # print("Matched heading")
                # print("HEADING: " + tag.get_text(strip=True))
                # print("HEADING: " + tag.contents[0].get_text(strip=True))
                s1Tags = tag.find_all(class_ = ["s1", "p", "verse", "ft"]) 
                for content in tag.contents:
                        print("Class: " + str(content.attrs.get('class')) if isinstance(content, Tag) else "N/A")
                        print( str(content.get_text(strip=True)) if isinstance(content, Tag) else "N/A")

                # if not s1Tags:
                #     # print("PARAGRAPH: " + tag.get_text(strip=True))
                #     print("S1 TITLE: ")
                #     for content in tag.contents:
                #         print("Class: " + str(content.attrs.get('class')) if isinstance(content, Tag) else "N/A")
                #         print( str(content.get_text(strip=True)) if isinstance(content, Tag) else "N/A")
                # for s1Tag in s1Tags:
                #     match s1Tag.attrs.get(['class'][0])[0]: 
                #         case 'ft':
                #             print("Matched footnote in heading")
                #             # print("FOOTNOTE: " + s1Tag.get_text(strip=True)) 
                #             print("FOOTNOTE: " + s1Tag.contents[0].get_text(strip=True))    

                # paragraphNumber = 1
                # print("Matched heading")
                # footnotes = tag.find_all(class_ = ["ft"])
                # for fn in footnotes:
                #     print("FOOTNOTE: " + fn.get_text(strip=True))
            case 'p':
                # print("Matched paragraph")
                pTags = tag.find_all(class_ = ["s1", "p", "verse", "ft"]) 

                # for content in tag.contents:
                #         print("Class: " + str(content.attrs.get('class')) if isinstance(content, Tag) else "N/A")
                #         print( str(content.get_text(strip=True)) if isinstance(content, Tag) else "N/A")

                # if pTags is empty it means that there are no verses or footnotes in the paragraph, so we can just print the paragraph text
                if not pTags:
                    # print("PARAGRAPH: " + tag.get_text(strip=True))
                    # print("PARAGRAPH TITLE: ")
                    for content in tag.contents:
                        print("Class: " + str(content.attrs.get('class')) if isinstance(content, Tag) else "N/A")
                        print( str(content.get_text(strip=True)) if isinstance(content, Tag) else "N/A")
                else:
                    for pTag in pTags:
                        match pTag.attrs.get(['class'][0])[0]:
                            case 'verse':
                                # print("Matched verse in paragraph")
                                for content in pTag.contents:
                                    print("Class: " + str(content.attrs.get('class')) if isinstance(content, Tag) else "N/A")
                                    print( str(content.get_text(strip=True)) if isinstance(content, Tag) else "N/A")
                                    
                                
                                # verseTags = pTag.find_all(class_ = ["label", "verse", "ft"]) 
                                # print("LABEL: " + pTag.contents[0].get_text(strip=True))
                                # print("VERSE: " + pTag.contents[1].get_text(strip=True))
                                # print("FOOTNOTE: " + pTag.contents[2].get_text(strip=True))

                                # for verseTag in verseTags:
                                #     match verseTag.attrs.get(['class'][0])[0]:
                                #         case 'label':
                                #             print("Matched label in paragraph in verse")
                                #             print("LABEL: " + verseTag.contents[0].get_text(strip=True))
                                #         case 'verse':
                                #             print("Matched verse in paragraph in verse")
                                #             print("VERSE: " + verseTag.contents[1].get_text(strip=True))
                                #         case 'ft':
                                #             print("Matched footnote in paragraph in verse")
                                #             print("FOOTNOTE: " + verseTag.contents[0].get_text(strip=True))

                # print("PARAGRAPH: " + tag.get_text(strip=True))
                # print(str(paragraphNumber) + "  Matched PARAGRAPH")
                # count = 1
                
                # re_numero_ver = re.compile(r'\d+')
                # for versiculo in textHtml.find_all(
                #         'span', {'data-usfm': re.compile(book + '.[0-9]*')}):
                #     numero_versiculo = int(re_numero_ver.findall(
                #         versiculo.attrs['class'][1])[0])


                

                # contents = tag.find_all(class_=["content"])
                # count = 1
                # for c in contents:
                #     print("CONTENT: " + str(count) + " " + c.get_text(strip=True))
                #     count += 1

                # footnotes = tag.find_all(class_ = ["ft"])
                # for fn in footnotes:
                #     print("FOOTNOTE: " + fn.get_text(strip=True))
                # numP = numP + 1 nao pode ser aqui devido a estrutura do html, tem que ser depois de processar o paragrafo inteiro veja Gen.1.27
            # case 'verse':   
            #     print("Matched verse")
            #     verseTags = tag.find_all(class_ = ["s1", "p", "verse", "ft"]) 
                # print("VERSE: " + tag.get_text(strip=True)) 
            # case 'ft':
            #     print("Matched footnote")
            #     print("FOOTNOTE: " + tag.get_text(strip=True))  
            #     ftTags = tag.find_all(class_ = ["s1", "p", "verse", "ft"])     
            case _:
                print("Default case")

        # if item.attrs.get("class") == ["s1"]:
        #     print("exact match")

    # extract the chapter title
   
    print(f'Processing {chapter}...')


    with open("output_" + chapter  + "_" + str(bibleId) + ".txt", "w", encoding="utf-8") as _f:
            sys.stdout = _f
            print(textHtml.prettify())
            sys.stdout = sys.__stdout__
    


