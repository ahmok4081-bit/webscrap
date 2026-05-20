"""
setup_db.py
───────────
Run once to create all MongoDB collections with:
  - JSON Schema validators (enforced by MongoDB at write time)
  - All indexes

Usage:
    python setup_db.py
    python setup_db.py --uri mongodb://user:pass@host:27017 --db bible
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import CollectionInvalid

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── JSON Schema files (relative to this script) ───────────────────────────────
SCHEMA_DIR = Path(__file__).parent / "jsonschema"

COLLECTION_SCHEMAS = {
    "editions":        "edition.schema.json",
    "books":           "book.schema.json",
    "chapters":        "chapter.schema.json",
    "lexicon":         "lexicon.schema.json",
    "verseAlignments": "verse-alignment.schema.json",
    "wordAlignments":  "word-alignment.schema.json",
    "annotations":     "annotation.schema.json",
    "readingProgress": "reading-progress.schema.json",
}


def load_schema(filename: str) -> dict:
    path = SCHEMA_DIR / filename
    if not path.exists():
        log.warning("Schema file not found: %s — skipping validator", path)
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def create_collection(db, name: str, schema: dict) -> None:
    """Create a collection with an optional JSON Schema validator."""
    validator = {"$jsonSchema": schema} if schema else {}

    try:
        db.create_collection(
            name,
            validator=validator,
            validationLevel="moderate",   # warn on existing docs, enforce on new ones
            validationAction="error",     # reject invalid inserts/updates
        )
        log.info("  Created collection: %s", name)

    except CollectionInvalid:
        # Collection already exists — update its validator instead
        cmd = {"collMod": name, "validationLevel": "moderate", "validationAction": "error"}
        if validator:
            cmd["validator"] = validator
        db.command(cmd)
        log.info("  Updated validator:  %s", name)


def create_indexes(db) -> None:
    from pymongo import ASCENDING, TEXT

    log.info("Creating indexes …")

    db.editions.create_index("abbreviation", unique=True)
    db.editions.create_index("language")

    db.books.create_index([("editionId", ASCENDING), ("order", ASCENDING)])
    db.books.create_index([("editionId", ASCENDING), ("testament", ASCENDING), ("order", ASCENDING)])
    db.books.create_index([("usfmCode", ASCENDING), ("editionId", ASCENDING)])

    db.chapters.create_index(
        [("editionId", ASCENDING), ("bookId", ASCENDING), ("order", ASCENDING)],
        unique=True,
    )
    db.chapters.create_index("canonicalRef")
    db.chapters.create_index("verses.canonicalRef")
    db.chapters.create_index("verses.strongsRefs")
    db.chapters.create_index("verses.crossReferences")
    db.chapters.create_index([("plainText", TEXT), ("verses.plainText", TEXT)])

    db.lexicon.create_index("strongsNumber", unique=True)
    db.lexicon.create_index("language")
    db.lexicon.create_index([("lemma", TEXT), ("definition", TEXT)])

    db.verseAlignments.create_index("canonicalRef", unique=True)

    db.wordAlignments.create_index("canonicalRef", unique=True)
    db.wordAlignments.create_index("alignments.strongsRef")

    db.annotations.create_index([("userId", ASCENDING), ("createdAt", ASCENDING)])
    db.annotations.create_index([("userId", ASCENDING), ("canonicalRef", ASCENDING)])
    db.annotations.create_index([("userId", ASCENDING), ("type", ASCENDING)])
    db.annotations.create_index([("userId", ASCENDING), ("tags", ASCENDING)])
    db.annotations.create_index([("groupId", ASCENDING), ("canonicalRef", ASCENDING)])
    db.annotations.create_index("linkedCanonicalRef")
    db.annotations.create_index([("note.plainText", TEXT)])

    db.readingProgress.create_index(
        [("userId", ASCENDING), ("editionId", ASCENDING)], unique=True
    )

    log.info("All indexes created.")


def setup(uri: str, db_name: str) -> None:
    log.info("Connecting to %s …", uri)
    client = MongoClient(uri, serverSelectionTimeoutMS=5_000)

    # Verify connection
    client.admin.command("ping")
    log.info("Connected. Setting up database: %s", db_name)

    db = client[db_name]

    log.info("Creating collections with validators …")
    for collection_name, schema_file in COLLECTION_SCHEMAS.items():
        schema = load_schema(schema_file)
        create_collection(db, collection_name, schema)

    create_indexes(db)

    log.info("")
    log.info("✅  Database '%s' is ready.", db_name)
    log.info("    Collections: %s", ", ".join(COLLECTION_SCHEMAS.keys()))

    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up the Bible MongoDB database.")
    parser.add_argument("--uri", default="mongodb://localhost:27017", help="MongoDB connection URI")
    parser.add_argument("--db",  default="bible", help="Database name")
    args = parser.parse_args()

    try:
        setup(args.uri, args.db)
    except Exception as e:
        log.error("Setup failed: %s", e)
        sys.exit(1)
