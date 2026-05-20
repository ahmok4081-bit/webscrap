'use strict';
const { Schema, model } = require('mongoose');
const { ContentNodeSchema, FootnoteSchema } = require('./shared');

// ─── Verse (embedded inside Chapter) ────────────────────────────────────────
const VerseSchema = new Schema(
  {
    verseId:    { type: String, required: true },   // 'ps_119_1'
    order:      { type: Number, required: true, min: 1 },
    reference:  { type: String, required: true },   // 'Psalms 119:1'
    canonicalRef: { type: String, required: true }, // 'PS.119.1'  — stable cross-edition key

    root: { type: ContentNodeSchema, required: true },

    // Denormalised for fast search — populated from root at save time
    plainText:  { type: String, required: true },
    wordCount:  { type: Number, default: 0 },

    // Strong's numbers present in this verse (denormalised from marks)
    strongsRefs: [{ type: String }],   // ['H3068', 'H1961', 'H7462']

    footnotes:      { type: [FootnoteSchema], default: [] },
    crossReferences: [{ type: String }],  // canonicalRefs: ['PS.23.1', 'JN.10.11']

    // Selah, Amen, doxology, stanza break, acrostic letter, etc.
    liturgicalMarkers: [{ type: String }],
  },
  { _id: false }
);

// ─── Chapter ─────────────────────────────────────────────────────────────────
const ChapterSchema = new Schema(
  {
    _id: { type: String },              // 'ch_kjv_ps_119'

    editionId:   { type: String, required: true, ref: 'Edition' },
    bookId:      { type: String, required: true, ref: 'Book' },
    order:       { type: Number, required: true, min: 1 },
    reference:   { type: String, required: true },    // 'Psalms 119'
    canonicalRef: { type: String, required: true },   // 'PS.119'

    totalVerses: { type: Number, required: true, min: 1 },
    verses:      { type: [VerseSchema], required: true },

    // Full chapter plain text — concatenation of all verse plainTexts
    // Indexed for full-text search
    plainText:   { type: String, required: true },

    // Acrostic section titles (Psalms 119: Aleph, Beth, Gimel…)
    sectionHeadings: [
      {
        beforeVerse: { type: Number },
        text:        { type: String },
        _id: false,
      },
    ],

    schemaVersion: { type: Number, default: 1 },
  },
  {
    _id: false,
    timestamps: true,
    collection: 'chapters',
  }
);

// ─── Indexes ──────────────────────────────────────────────────────────────────
ChapterSchema.index({ editionId: 1, bookId: 1, order: 1 }, { unique: true });
ChapterSchema.index({ canonicalRef: 1 });
ChapterSchema.index({ 'verses.canonicalRef': 1 });
ChapterSchema.index({ 'verses.strongsRefs': 1 });
ChapterSchema.index({ 'verses.crossReferences': 1 });
ChapterSchema.index({ plainText: 'text', 'verses.plainText': 'text' });

// ─── Pre-save hook: auto-populate plainText & wordCount ──────────────────────
ChapterSchema.pre('save', function (next) {
  for (const verse of this.verses) {
    verse.wordCount = verse.plainText.trim().split(/\s+/).length;
  }
  this.plainText = this.verses.map((v) => v.plainText).join(' ');
  next();
});

module.exports = model('Chapter', ChapterSchema);
