'use strict';
const { Schema, model } = require('mongoose');

/**
 * Edition — one Bible translation / version
 * Examples: KJV, ESV, NIV, NLT, LXX, WLC (Hebrew), NA28 (Greek)
 */
const EditionSchema = new Schema(
  {
    _id: { type: String },            // e.g. 'edition_kjv'

    name:         { type: String, required: true, trim: true },   // 'King James Version'
    abbreviation: { type: String, required: true, trim: true, uppercase: true }, // 'KJV'
    language:     { type: String, required: true, trim: true },   // 'en', 'he', 'el'
    direction:    { type: String, enum: ['ltr', 'rtl'], default: 'ltr' },
    script:       { type: String },   // 'Latin', 'Hebrew', 'Greek'
    year:         { type: Number },
    publisher:    { type: String },
    copyright:    { type: String },   // 'Public Domain' or rights text

    hasRedLetters:   { type: Boolean, default: false },
    hasStrongsNumbers: { type: Boolean, default: false },
    hasWordAlignment: { type: Boolean, default: false },

    sourceTextType: {
      type: String,
      enum: ['original', 'translation', 'paraphrase', 'interlinear'],
      default: 'translation',
    },

    // Original-language editions linked to this translation
    sourceEditionIds: [{ type: String, ref: 'Edition' }],
  },
  {
    _id: false,          // we supply _id manually
    timestamps: true,
    collection: 'editions',
  }
);

EditionSchema.index({ language: 1 });
EditionSchema.index({ abbreviation: 1 }, { unique: true });

module.exports = model('Edition', EditionSchema);
