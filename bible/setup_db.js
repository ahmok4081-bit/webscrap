#!/usr/bin/env node
/**
 * setup_db.js
 * ───────────
 * Run once to create all MongoDB collections with:
 *   - JSON Schema validators (enforced by MongoDB at write time)
 *   - All indexes
 *
 * Usage:
 *   node setup_db.js
 *   node setup_db.js --uri mongodb://user:pass@host:27017 --db bible
 *
 * Requirements:
 *   npm install mongodb
 */

'use strict';

const { MongoClient } = require('mongodb');
const fs   = require('fs');
const path = require('path');

// ── CLI args ──────────────────────────────────────────────────────────────────
const args = process.argv.slice(2).reduce((acc, val, i, arr) => {
  if (val.startsWith('--')) acc[val.slice(2)] = arr[i + 1];
  return acc;
}, {});

const URI     = args.uri || 'mongodb://localhost:27017';
const DB_NAME = args.db  || 'bible';

// ── Schema files ──────────────────────────────────────────────────────────────
const SCHEMA_DIR = path.join(__dirname, 'jsonschema');

const COLLECTION_SCHEMAS = {
  editions:        'edition.schema.json',
  books:           'book.schema.json',
  chapters:        'chapter.schema.json',
  lexicon:         'lexicon.schema.json',
  verseAlignments: 'verse-alignment.schema.json',
  wordAlignments:  'word-alignment.schema.json',
  annotations:     'annotation.schema.json',
  readingProgress: 'reading-progress.schema.json',
};

// ── Helpers ───────────────────────────────────────────────────────────────────
const log = {
  info:  (msg) => console.log(`INFO   ${msg}`),
  ok:    (msg) => console.log(`✅     ${msg}`),
  warn:  (msg) => console.warn(`WARN   ${msg}`),
  error: (msg) => console.error(`ERROR  ${msg}`),
};

function loadSchema(filename) {
  const filepath = path.join(SCHEMA_DIR, filename);
  if (!fs.existsSync(filepath)) {
    log.warn(`Schema file not found: ${filepath} — skipping validator`);
    return null;
  }
  return JSON.parse(fs.readFileSync(filepath, 'utf-8'));
}

// ── Collection creation ───────────────────────────────────────────────────────
async function createCollection(db, name, schema) {
  const validator       = schema ? { $jsonSchema: schema } : {};
  const validationLevel  = 'moderate';   // enforce on new docs, warn on existing
  const validationAction = 'error';      // reject invalid inserts/updates

  const existingCollections = await db
    .listCollections({ name })
    .toArray();

  if (existingCollections.length === 0) {
    // Collection does not exist — create it
    await db.createCollection(name, {
      validator,
      validationLevel,
      validationAction,
    });
    log.info(`Created collection:   ${name}`);
  } else {
    // Collection exists — update validator only
    await db.command({
      collMod: name,
      validator,
      validationLevel,
      validationAction,
    });
    log.info(`Updated validator:    ${name}`);
  }
}

// ── Index definitions ─────────────────────────────────────────────────────────
async function createIndexes(db) {
  log.info('Creating indexes …');

  // editions
  await db.collection('editions').createIndexes([
    { key: { abbreviation: 1 }, unique: true },
    { key: { language: 1 } },
  ]);

  // books
  await db.collection('books').createIndexes([
    { key: { editionId: 1, order: 1 } },
    { key: { editionId: 1, testament: 1, order: 1 } },
    { key: { usfmCode: 1, editionId: 1 } },
  ]);

  // chapters
  await db.collection('chapters').createIndexes([
    { key: { editionId: 1, bookId: 1, order: 1 }, unique: true },
    { key: { canonicalRef: 1 } },
    { key: { 'verses.canonicalRef': 1 } },
    { key: { 'verses.strongsRefs': 1 } },
    { key: { 'verses.crossReferences': 1 } },
    { key: { plainText: 'text', 'verses.plainText': 'text' } },
  ]);

  // lexicon
  await db.collection('lexicon').createIndexes([
    { key: { strongsNumber: 1 }, unique: true },
    { key: { language: 1 } },
    { key: { lemma: 'text', definition: 'text' } },
  ]);

  // verseAlignments
  await db.collection('verseAlignments').createIndexes([
    { key: { canonicalRef: 1 }, unique: true },
  ]);

  // wordAlignments
  await db.collection('wordAlignments').createIndexes([
    { key: { canonicalRef: 1 }, unique: true },
    { key: { 'alignments.strongsRef': 1 } },
  ]);

  // annotations
  await db.collection('annotations').createIndexes([
    { key: { userId: 1, createdAt: 1 } },
    { key: { userId: 1, canonicalRef: 1 } },
    { key: { userId: 1, type: 1 } },
    { key: { userId: 1, tags: 1 } },
    { key: { groupId: 1, canonicalRef: 1 } },
    { key: { linkedCanonicalRef: 1 } },
    { key: { 'note.plainText': 'text' } },
  ]);

  // readingProgress
  await db.collection('readingProgress').createIndexes([
    { key: { userId: 1, editionId: 1 }, unique: true },
    { key: { userId: 1, 'lastRead.readAt': -1 } },
  ]);

  log.info('All indexes created.');
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function setup() {
  log.info(`Connecting to ${URI} …`);
  const client = new MongoClient(URI, { serverSelectionTimeoutMS: 5_000 });

  try {
    await client.connect();
    await client.db('admin').command({ ping: 1 });
    log.info(`Connected. Setting up database: ${DB_NAME}`);

    const db = client.db(DB_NAME);

    // 1. Create collections with validators
    log.info('Creating collections with validators …');
    for (const [collectionName, schemaFile] of Object.entries(COLLECTION_SCHEMAS)) {
      const schema = loadSchema(schemaFile);
      await createCollection(db, collectionName, schema);
    }

    // 2. Create indexes
    await createIndexes(db);

    // 3. Summary
    console.log('');
    log.ok(`Database '${DB_NAME}' is ready.`);
    log.ok(`Collections: ${Object.keys(COLLECTION_SCHEMAS).join(', ')}`);

  } catch (err) {
    log.error(`Setup failed: ${err.message}`);
    process.exit(1);
  } finally {
    await client.close();
  }
}

setup();
