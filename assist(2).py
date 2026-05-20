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
KNOWN_PREFIXES: set[str] = {"tn", "sn", "tc"}

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
_NOTE_BOUNDARY = re.compile(r'(?:^|(?<=[.!?"\])])) *(tn|sn|tc)(?= )')




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
            f"tc={len(self.footnotes_by_type('tc'))}])"
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


# ── Local HTML parser for saved API output (KOV format) ───────────────────────

def parse_chapter_from_html(html: str, source_url: str = "") -> ChapterPage:
    """Build ChapterPage from offline HTML saved by assist(2)."""
    soup = BeautifulSoup(html, "lxml")

    version_div = soup.find("div", class_="version")
    version = version_div.get("data-vid", "").strip() if version_div else ""

    book_div = soup.find("div", class_="book")
    book = "" if not book_div else book_div.get("class", [])
    if isinstance(book, list):
        # e.g. ['book', 'bkGEN']
        book = next((c[2:] for c in book if c.startswith("bk")), "").upper()

    chapter_div = soup.find("div", class_="chapter")
    chapter = 0
    if chapter_div:
        ch_usfm = chapter_div.get("data-usfm", "")
        if "." in ch_usfm:
            try:
                chapter = int(ch_usfm.split(".")[1])
            except ValueError:
                chapter = 0

    title = f"{book} {chapter}" if book and chapter else ""

    cp = ChapterPage(book=book or "", chapter=chapter, version=version or "", title=title, source_url=source_url)
    section = Section(heading=None)

    if chapter_div:
        for p_tag in chapter_div.find_all("div", class_="p"):
            paragraph = Paragraph()
            verse_spans = p_tag.find_all("span", class_=re.compile(r"\bverse\b"))
            if not verse_spans:
                # fallback: any text available if no explicit verse spans
                text = p_tag.get_text(" ", strip=True)
                if text:
                    paragraph.verses.append(Verse(number=None, chunks=[Chunk(text=text)]))
            else:
                for verse_span in verse_spans:
                    num = None
                    label = verse_span.find("span", class_="label")
                    if label and label.get_text(strip=True).isdigit():
                        num = int(label.get_text(strip=True))

                    chunks: list[Chunk] = []
                    content_spans = verse_span.find_all("span", class_="content")
                    for c in content_spans:
                        text = c.get_text(" ", strip=True)
                        if text:
                            chunks.append(Chunk(text=text))

                    if not chunks:
                        raw = verse_span.get_text(" ", strip=True)
                        chunks.append(Chunk(text=raw))

                    paragraph.verses.append(Verse(number=num, chunks=chunks))

            if paragraph.verses:
                section.paragraphs.append(paragraph)

    if section.paragraphs:
        cp.sections.append(section)

    return cp


def print_structure(cp: ChapterPage, show_footnotes: bool = True) -> None:
    """Pretty print the in-memory structure for debugging."""
    fn = cp.all_footnotes
    print("=" * 70)
    print(f"title       : {cp.title}")
    print(f"book/ch/ver : {cp.book} / {cp.chapter} / {cp.version}")
    print(f"url         : {cp.source_url}")
    print(f"sections    : {len(cp.sections)}")
    print(f"verses      : {len(cp.all_verses)}")
    print(f"footnotes   : {len(fn)}  "
          f"(tn={len(cp.footnotes_by_type('tn'))}, "
          f"sn={len(cp.footnotes_by_type('sn'))}, "
          f"tc={len(cp.footnotes_by_type('tc'))})")
    print("=" * 70)

    for s_i, section in enumerate(cp.sections, 1):
        heading = section.heading or '(no heading)'
        if section.heading_footnotes:
            print(f"\n-- Section {s_i}: {heading}")
            if show_footnotes:
                for fn in section.heading_footnotes:
                    print(f"   [{fn.type.upper()}] {fn.text}")
        else:
            print(f"\n-- Section {s_i}: {heading}")

        for p_i, para in enumerate(section.paragraphs, 1):
            print(f"   Paragraph {p_i}:")
            for verse in para.verses:
                print(f"     [v{verse.number if verse.number is not None else '(line)'}] {verse.plain_text}")
                if show_footnotes:
                    for chunk in verse.chunks:
                        for fn2 in chunk.footnotes:
                            print(f"              [{fn2.type.upper()}] {fn2.text}")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Example 1: parse local HTML produced by your API fetch (attachment file):
    if len(sys.argv) > 1 and Path(sys.argv[1]).suffix == ".html":
        input_path = Path(sys.argv[1])
        html_text = input_path.read_text(encoding="utf-8")
        chapter_page = parse_chapter_from_html(html_text, source_url=input_path.as_uri())
        print_structure(chapter_page)
        print("Done: parsed HTML into ChapterPage structure.")
        sys.exit(0)

    # Example 2: fetch directly from bible.com API and write out HTML
    bookChapter = "GEN.1"
    bibleId = 1270  # KOV
    response = get_chapter_data("3.3", bibleId, bookChapter)
    chapterCode = response['reference']['usfm'][0]
    chapter = response['reference']['human']
    html = BeautifulSoup(response['content'], 'lxml')

    with open("output_" + chapter + "_" + str(bibleId) + ".html", "w", encoding="utf-8") as _f:
        _f.write(html.prettify())

    print(f"Wrote parsed source to output_{chapter}_{bibleId}.html")




if __name__ == "__main__":
    import sys

    bookChapter = "GEN.1"
    # bookChapter = "PSA.119"
    # bibleId = 107 # NET Bible
    bibleId = 1270 # KOV

    response = get_chapter_data("3.3", bibleId, bookChapter)
    chapterCode = response['reference']['usfm'][0]
    chapter = response['reference']['human']
    textHtml = BeautifulSoup(response['content'], 'lxml')


    print(f'Processing {chapter}...')


    # with open("output_" + chapter  + "_" + str(bibleId) + ".html", "w", encoding="utf-8") as _f:
    #         sys.stdout = _f
    #         print(textHtml.prettify())
    #         sys.stdout = sys.__stdout__






  
   
   
    


