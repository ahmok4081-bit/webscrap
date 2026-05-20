'use strict';
/**
 * Bible NoSQL Schema — Master Export
 * ===================================
 * Mongoose models + JSON Schema paths for all collections.
 *
 * Collections
 * ───────────
 *   editions          — Bible translations / versions
 *   books             — Canonical books (one per edition)
 *   chapters          — Chapters with embedded verses + rich-text tree
 *   lexicon           — Strong's Hebrew (H) and Greek (G) entries
 *   verseAlignments   — Canonical ref → per-edition verse location map
 *   wordAlignments    — Slot-level word diff across editions
 *   annotations       — User highlights, notes, cross-refs, bookmarks
 *   readingProgress   — User reading position and plan tracking
 */

const Edition        = require('./mongoose/Edition');
const Book           = require('./mongoose/Book');
const Chapter        = require('./mongoose/Chapter');
const { Lexicon, VerseAlignment, WordAlignment } = require('./mongoose/Lexicon');
const { Annotation, ReadingProgress }            = require('./mongoose/Annotation');

const path = require('path');
const jsonSchemas = {
  edition:         path.join(__dirname, 'jsonschema/edition.schema.json'),
  book:            path.join(__dirname, 'jsonschema/book.schema.json'),
  chapter:         path.join(__dirname, 'jsonschema/chapter.schema.json'),
  lexicon:         path.join(__dirname, 'jsonschema/lexicon.schema.json'),
  verseAlignment:  path.join(__dirname, 'jsonschema/verse-alignment.schema.json'),
  wordAlignment:   path.join(__dirname, 'jsonschema/word-alignment.schema.json'),
  annotation:      path.join(__dirname, 'jsonschema/annotation.schema.json'),
  readingProgress: path.join(__dirname, 'jsonschema/reading-progress.schema.json'),
};

module.exports = {
  // Mongoose models
  Edition,
  Book,
  Chapter,
  Lexicon,
  VerseAlignment,
  WordAlignment,
  Annotation,
  ReadingProgress,

  // JSON Schema file paths (use with ajv or similar validator)
  jsonSchemas,
};
