'use strict';
const { Schema, model } = require('mongoose');

/**
 * Book — one canonical book of the Bible (e.g. Genesis, Psalms, John)
 * One document per book per edition.
 */
const BookSchema = new Schema(
  {
    _id: { type: String },             // e.g. 'book_kjv_psalms'

    editionId:    { type: String, required: true, ref: 'Edition' },
    testament:    { type: String, required: true, enum: ['OT', 'NT', 'DC'] }, // DC = Deuterocanon
    order:        { type: Number, required: true, min: 1 },   // canonical order 1-66 (or more for DC)

    name:         { type: String, required: true, trim: true },  // 'Psalms'
    abbreviation: { type: String, required: true, trim: true },  // 'Ps'
    usfmCode:     { type: String, trim: true },    // USFM book code: 'PSA', 'JHN', etc.
    osis:         { type: String, trim: true },    // OSIS identifier: 'Ps', 'John'

    category: {
      type: String,
      enum: [
        'Law', 'History', 'Poetry', 'Prophecy',
        'Gospel', 'Acts', 'Epistle', 'Apocalyptic',
        'Deuterocanon',
      ],
    },

    totalChapters: { type: Number, required: true, min: 1 },
    totalVerses:   { type: Number, required: true, min: 1 },
  },
  {
    _id: false,
    timestamps: true,
    collection: 'books',
  }
);

BookSchema.index({ editionId: 1, order: 1 });
BookSchema.index({ editionId: 1, testament: 1, order: 1 });
BookSchema.index({ usfmCode: 1, editionId: 1 });

module.exports = model('Book', BookSchema);
