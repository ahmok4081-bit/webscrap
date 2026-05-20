'use strict';
const { Schema, model } = require('mongoose');
const { ContentNodeSchema } = require('./shared');

// ══════════════════════════════════════════════════════════════════════════════
// ANNOTATION — user highlights, notes, and personal cross-references
// Never modifies source text; always references by canonicalRef
// ══════════════════════════════════════════════════════════════════════════════

const SelectionSchema = new Schema(
  {
    verseId:     { type: String, required: true },
    // Character offsets within verse plainText (null endOffset = whole verse)
    startOffset: { type: Number, required: true, min: 0 },
    endOffset:   { type: Number, default: null },
  },
  { _id: false }
);

const HighlightStyleSchema = new Schema(
  {
    color:   { type: String, required: true, match: /^#[0-9A-Fa-f]{6}$/ },
    opacity: { type: Number, min: 0, max: 1, default: 0.4 },
  },
  { _id: false }
);

const NoteBodySchema = new Schema(
  {
    root:      { type: ContentNodeSchema },  // rich-text document tree
    plainText: { type: String },             // denormalised for search
  },
  { _id: false }
);

const AnnotationSchema = new Schema(
  {
    userId:       { type: String, required: true },
    type: {
      type: String,
      required: true,
      enum: ['highlight', 'note', 'crossRef', 'bookmark'],
    },

    canonicalRef: { type: String, required: true },  // 'PS.23.1'
    editionId:    { type: String, ref: 'Edition' },  // null = edition-agnostic

    // For 'highlight' and 'note'
    selection: { type: SelectionSchema },
    style:     { type: HighlightStyleSchema },

    // For 'note'
    note: { type: NoteBodySchema },

    // For 'crossRef'
    linkedCanonicalRef: { type: String },  // 'JN.10.11'

    // Shared metadata
    tags:      [{ type: String, trim: true, lowercase: true }],
    isPrivate: { type: Boolean, default: true },

    // Sharing: null = private; groupId = shared with a study group
    groupId:   { type: String, default: null },
  },
  {
    timestamps: true,
    collection: 'annotations',
  }
);

// ─── Indexes ──────────────────────────────────────────────────────────────────
AnnotationSchema.index({ userId: 1, createdAt: -1 });
AnnotationSchema.index({ userId: 1, canonicalRef: 1 });
AnnotationSchema.index({ userId: 1, type: 1 });
AnnotationSchema.index({ userId: 1, tags: 1 });
AnnotationSchema.index({ groupId: 1, canonicalRef: 1 });
AnnotationSchema.index({ 'note.plainText': 'text' });
AnnotationSchema.index({ linkedCanonicalRef: 1 });

// ── Validation: crossRef requires linkedCanonicalRef ─────────────────────────
AnnotationSchema.pre('validate', function (next) {
  if (this.type === 'crossRef' && !this.linkedCanonicalRef) {
    return next(new Error('crossRef annotations require linkedCanonicalRef'));
  }
  if (['highlight', 'note'].includes(this.type) && !this.selection) {
    return next(new Error(`${this.type} annotations require a selection`));
  }
  next();
});

// ══════════════════════════════════════════════════════════════════════════════
// READING PROGRESS — tracks where a user is in a reading plan / free reading
// ══════════════════════════════════════════════════════════════════════════════
const LastReadSchema = new Schema(
  {
    canonicalRef:  { type: String, required: true },  // 'PS.119.105'
    bookId:        { type: String, required: true },
    chapterOrder:  { type: Number, required: true },
    verseOrder:    { type: Number, required: true },
    readAt:        { type: Date,   default: Date.now },
  },
  { _id: false }
);

const ReadingProgressSchema = new Schema(
  {
    userId:    { type: String, required: true },
    editionId: { type: String, required: true, ref: 'Edition' },

    lastRead:           { type: LastReadSchema },
    completedChapters:  [{ type: String }],  // canonicalRefs: ['GN.1', 'PS.23']
    completedBooks:     [{ type: String }],  // usfmCodes: ['PSA', 'JHN']

    readingPlan: {
      type: String,
      enum: [
        'chronological_1year',
        'canonical_1year',
        'nt_30days',
        'psalms_proverbs',
        'custom',
        null,
      ],
      default: null,
    },
    readingPlanDay: { type: Number, default: null },
  },
  {
    timestamps: true,
    collection: 'readingProgress',
  }
);

ReadingProgressSchema.index({ userId: 1, editionId: 1 }, { unique: true });
ReadingProgressSchema.index({ userId: 1, 'lastRead.readAt': -1 });

module.exports = {
  Annotation:      model('Annotation',      AnnotationSchema),
  ReadingProgress: model('ReadingProgress', ReadingProgressSchema),
};
