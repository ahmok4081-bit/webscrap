'use strict';
const { Schema } = require('mongoose');

// ─── Mark (inline formatting applied to a text node) ───────────────────────
const MarkSchema = new Schema(
  {
    type: {
      type: String,
      required: true,
      enum: [
        'bold', 'italic', 'underline', 'strikethrough',
        'superscript', 'subscript', 'smallCaps',
        'redLetter',          // Words of Jesus (NT)
        'selah',              // Psalms liturgical marker
        'poetryIndent',       // Hebrew poetry line indent
        'color',              // { value: '#hex' }
        'font',               // { family, size }
        'highlight',          // { color: '#hex' }
        'footnoteMarker',     // { ref: 'a' }
        'crossRefMarker',     // { ref: 'b' }
        'strongs',            // { ref: 'H3068' }
      ],
    },
    // type-specific payload
    value:  { type: String  },   // color hex
    family: { type: String  },   // font family
    size:   { type: Number  },   // font size (pt)
    ref:    { type: String  },   // footnote/crossRef/strongs reference
    level:  { type: Number  },   // poetryIndent depth
    color:  { type: String  },   // highlight color
  },
  { _id: false }
);

// ─── Generic content node (recursive via Mixed children) ───────────────────
// Full recursive schemas are not supported natively in Mongoose,
// so children are stored as Mixed and validated at the application layer
// or via the companion JSON Schema (see /jsonschema/).
const ContentNodeSchema = new Schema(
  {
    type: {
      type: String,
      required: true,
      enum: [
        'document', 'heading', 'paragraph', 'blockquote',
        'list', 'listItem', 'table', 'tableRow', 'tableCell',
        'verse', 'verseNumber', 'section',
        'text', 'hardBreak',
      ],
    },
    text:     { type: String },          // leaf text nodes only
    marks:    { type: [MarkSchema], default: undefined },
    attrs:    { type: Schema.Types.Mixed },  // heading level, list ordered, align, etc.
    children: { type: [Schema.Types.Mixed], default: undefined },
  },
  { _id: false }
);

// ─── Footnote ────────────────────────────────────────────────────────────
const FootnoteSchema = new Schema(
  {
    marker: { type: String, required: true },   // 'a', 'b', '1', ...
    text:   { type: String, required: true },
  },
  { _id: false }
);

module.exports = { MarkSchema, ContentNodeSchema, FootnoteSchema };
