'use strict';
const { Schema, model } = require('mongoose');

// ══════════════════════════════════════════════════════════════════════════════
// LEXICON  — one entry per Strong's number (H0001–H8674, G0001–G5624)
// ══════════════════════════════════════════════════════════════════════════════
const KjvUsageSchema = new Schema(
  {
    word:  { type: String, required: true },   // 'LORD'
    count: { type: Number, required: true, min: 0 },
  },
  { _id: false }
);

const LexiconSchema = new Schema(
  {
    _id: { type: String },                // 'H3068'  /  'G2316'

    language:        { type: String, required: true, enum: ['Hebrew', 'Aramaic', 'Greek'] },
    strongsNumber:   { type: String, required: true },
    lemma:           { type: String, required: true },    // original script: יְהֹוָה
    transliteration: { type: String },
    pronunciation:   { type: String },    // 'yeh-ho-vaw\''
    partOfSpeech:    { type: String },    // 'proper noun', 'verb', 'adjective', …

    definition:         { type: String, required: true },
    extendedDefinition: { type: String },
    usageNotes:         { type: String },

    kjvTranslations: { type: [KjvUsageSchema], default: [] },
    relatedStrongs:  [{ type: String }],   // ['H3069', 'H3050']
  },
  {
    _id: false,
    timestamps: true,
    collection: 'lexicon',
  }
);

LexiconSchema.index({ strongsNumber: 1 }, { unique: true });
LexiconSchema.index({ language: 1 });
LexiconSchema.index({ lemma: 'text', definition: 'text' });

// ══════════════════════════════════════════════════════════════════════════════
// VERSE ALIGNMENT — maps a canonical verse ref to per-edition verse locations
// Handles split/merged verses across traditions (e.g. LXX vs MT numbering)
// ══════════════════════════════════════════════════════════════════════════════
const VerseAlignmentSchema = new Schema(
  {
    _id: { type: String },                 // 'align_JN.3.16'

    canonicalRef: { type: String, required: true, unique: true },  // 'JN.3.16'

    // editionId → verseId  (null = verse absent in that edition)
    editions: {
      type: Map,
      of: { type: String, default: null },
    },

    verseSplitNote: { type: String, default: null },
    // e.g. 'LXX numbers this as two separate verses: LXX.PS.13.5 and LXX.PS.13.6'
  },
  {
    _id: false,
    collection: 'verseAlignments',
  }
);

VerseAlignmentSchema.index({ canonicalRef: 1 }, { unique: true });

// ══════════════════════════════════════════════════════════════════════════════
// WORD ALIGNMENT — slot-by-slot word mapping across editions for one verse
// Enables parallel Bible diff UI
// ══════════════════════════════════════════════════════════════════════════════
const WordSlotSchema = new Schema(
  {
    slot: { type: Number, required: true },
    // editionId → array of words covering this slot
    words: {
      type: Map,
      of: [String],
    },
    // Optional Strong's number for this slot (from source-language edition)
    strongsRef: { type: String, ref: 'Lexicon' },
  },
  { _id: false }
);

const WordAlignmentSchema = new Schema(
  {
    _id: { type: String },                 // 'wordalign_JN.3.16'

    canonicalRef: { type: String, required: true, unique: true },
    alignments:   { type: [WordSlotSchema], required: true },
  },
  {
    _id: false,
    collection: 'wordAlignments',
  }
);

WordAlignmentSchema.index({ canonicalRef: 1 }, { unique: true });
WordAlignmentSchema.index({ 'alignments.strongsRef': 1 });

module.exports = {
  Lexicon:        model('Lexicon',        LexiconSchema),
  VerseAlignment: model('VerseAlignment', VerseAlignmentSchema),
  WordAlignment:  model('WordAlignment',  WordAlignmentSchema),
};
