# Bible NoSQL Schema

Complete Mongoose models and JSON Schema validation specs for a multi-translation Bible database with Strong's numbers, user annotations, and parallel translation support.

---

## Collections Overview

| Collection | Documents | Purpose |
|---|---|---|
| `editions` | ~10–50 | Bible translations (KJV, ESV, NIV, LXX…) |
| `books` | 66 × editions | Canonical books per edition |
| `chapters` | 1,189 × editions | Chapters with embedded verses + rich-text tree |
| `lexicon` | ~13,000 | Strong's Hebrew (H) + Greek (G) entries |
| `verseAlignments` | ~31,100 | Canonical ref → per-edition verse location |
| `wordAlignments` | ~31,100 | Word-level diff slots across editions |
| `annotations` | unbounded | User highlights, notes, cross-refs, bookmarks |
| `readingProgress` | 1 per user/edition | Reading position + plan tracking |

---

## File Structure

```
bible-schema/
├── index.js                      ← master export (models + schema paths)
├── mongoose/
│   ├── shared.js                 ← MarkSchema, ContentNodeSchema, FootnoteSchema
│   ├── Edition.js
│   ├── Book.js
│   ├── Chapter.js                ← includes embedded VerseSchema
│   ├── Lexicon.js                ← Lexicon + VerseAlignment + WordAlignment
│   └── Annotation.js             ← Annotation + ReadingProgress
└── jsonschema/
    ├── edition.schema.json
    ├── book.schema.json
    ├── chapter.schema.json       ← most complex; includes mark/node definitions
    ├── lexicon.schema.json
    ├── verse-alignment.schema.json
    ├── word-alignment.schema.json
    ├── annotation.schema.json
    └── reading-progress.schema.json
```

---

## Key Design Decisions

### canonicalRef — the stable cross-edition key
Every verse carries a `canonicalRef` string (`PS.119.1`, `JN.3.16`). This is edition-agnostic and survives verse-numbering differences between traditions. The `verseAlignments` collection maps canonical refs to edition-specific verse IDs.

### Verses embedded in Chapters
Verses are embedded arrays inside Chapter documents rather than separate documents. Rationale:
- A chapter is always read as a unit
- Even the longest chapter (Psalms 119, 176 verses) is ~15 KB — well under MongoDB's 16 MB limit
- Atomic chapter saves prevent partial-verse inconsistency

### Marks array on text nodes
Inline formatting (bold, italic, color, Strong's, footnote markers) is stored as a flat `marks` array on text nodes rather than nested wrapper elements. This is the same model used by ProseMirror / Tiptap and makes rendering straightforward.

### plainText denormalisation
Every verse and chapter stores a `plainText` field populated at save time. This field is full-text indexed and used for search, avoiding the need to traverse the content tree at query time.

### strongsRefs denormalisation
Verses store a `strongsRefs: [String]` array (e.g. `['H3068','H7462']`) populated from marks at save time. This enables `{ "verses.strongsRefs": "H3068" }` index queries without scanning the content tree.

---

## Indexes Summary

```js
// editions
{ abbreviation: 1 }                         unique

// books
{ editionId: 1, order: 1 }
{ editionId: 1, testament: 1, order: 1 }
{ usfmCode: 1, editionId: 1 }

// chapters
{ editionId: 1, bookId: 1, order: 1 }       unique
{ canonicalRef: 1 }
{ 'verses.canonicalRef': 1 }
{ 'verses.strongsRefs': 1 }
{ 'verses.crossReferences': 1 }
{ plainText: 'text', 'verses.plainText': 'text' }

// lexicon
{ strongsNumber: 1 }                        unique
{ language: 1 }
{ lemma: 'text', definition: 'text' }

// verseAlignments
{ canonicalRef: 1 }                         unique

// wordAlignments
{ canonicalRef: 1 }                         unique
{ 'alignments.strongsRef': 1 }

// annotations
{ userId: 1, createdAt: -1 }
{ userId: 1, canonicalRef: 1 }
{ userId: 1, type: 1 }
{ userId: 1, tags: 1 }
{ groupId: 1, canonicalRef: 1 }
{ linkedCanonicalRef: 1 }
{ 'note.plainText': 'text' }

// readingProgress
{ userId: 1, editionId: 1 }                unique
```

---

## Common Query Patterns

```js
// Fetch a chapter (Psalms 23, KJV)
Chapter.findOne({ editionId: 'edition_kjv', bookId: 'book_kjv_psalms', order: 23 })

// Fetch a single verse by canonical ref (all editions)
const alignment = await VerseAlignment.findOne({ canonicalRef: 'JN.3.16' })

// Lookup Strong's entry
Lexicon.findOne({ _id: 'H3068' })

// All verses containing H3068 (LORD) in KJV
Chapter.find({ editionId: 'edition_kjv', 'verses.strongsRefs': 'H3068' })

// Verses with both H7462 (shepherd) AND H4325 (water)
Chapter.find({ 'verses.strongsRefs': { $all: ['H7462', 'H4325'] } })

// All chapters of Psalms, ordered, no verse content (fast TOC)
Chapter.find({ bookId: 'book_kjv_psalms' }, { verses: 0 }).sort({ order: 1 })

// Full-text search across entire Bible
Chapter.find({ $text: { $search: 'still waters' } })

// User's highlights on Psalms 23:1
Annotation.find({ userId: 'user_42', canonicalRef: 'PS.23.1', type: 'highlight' })

// User's notes tagged 'comfort'
Annotation.find({ userId: 'user_42', tags: 'comfort', type: 'note' })

// All verses that cross-reference Psalms 23:1
Chapter.find({ 'verses.crossReferences': 'PS.23.1' })
```

---

## Mark Types Reference

| Mark type | Extra fields | Description |
|---|---|---|
| `bold` | — | Bold text |
| `italic` | — | Italic (often translator additions) |
| `underline` | — | Underline |
| `smallCaps` | — | LORD / GOD (Tetragrammaton) |
| `redLetter` | — | Words of Jesus (NT) |
| `superscript` | — | Verse numbers |
| `selah` | — | Psalms liturgical marker |
| `poetryIndent` | `level` | Hebrew poetry line indentation |
| `color` | `value` (#hex) | Text color |
| `font` | `family`, `size` | Font override |
| `highlight` | `color` (#hex) | Background highlight |
| `footnoteMarker` | `ref` (letter) | Footnote anchor |
| `crossRefMarker` | `ref` (letter) | Cross-reference anchor |
| `strongs` | `ref` (H/G + 4 digits) | Strong's concordance link |

---

## canonicalRef Format

```
BOOK_CODE.CHAPTER.VERSE
  PS.119.1     → Psalms 119:1
  JN.3.16      → John 3:16
  GN.1.1       → Genesis 1:1

Chapter-level:
  PS.119        → Psalms chapter 119
  JN.3          → John chapter 3
```

Book codes use USFM abbreviations in uppercase: `GN`, `EX`, `PS`, `PRV`, `ISA`, `MT`, `MK`, `LK`, `JN`, `RO`, `REV`, etc.
