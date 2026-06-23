from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Entry:
    rowId: int
    keyParts: List[Any]
    value: str


@dataclass
class ChapterDoc:
    chapter: int
    entries: List[Entry] = field(default_factory=list)


@dataclass
class BookDoc:
    bookId: str
    testament: str
    order: int
    title: Optional[str] = None
    abbreviation: Optional[str] = None
    chapters: List[ChapterDoc] = field(default_factory=list)


@dataclass
class TranslationDoc:
    translationId: str
    name: str
    abbreviation: str
    language: str
    copyright: Optional[str] = None
    books: List[BookDoc] = field(default_factory=list)