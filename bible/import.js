const { MongoClient } = require("mongodb");
const fs = require("fs");

// --- PARSE THE FILE ---
function parseDebugFile(filePath) {
  const lines = fs.readFileSync(filePath, "utf8").split("\n").filter(Boolean);

  const chapter = { label: null, sections: [], paragraphs: {} };
  let currentHeading = null;

  for (const line of lines) {
    const [rawKey, ...valueParts] = line.split("\t");
    const value = valueParts.join("\t").trim();

    // Parse the key array, e.g. ['p1', 'verse', 'v1', 'label']
    const key = JSON.parse(rawKey.replace(/'/g, '"'));

    if (key[0] === "label") {
      chapter.label = parseInt(value);
      continue;
    }

    if (key[0] === "s" && key[1] === "heading") {
      currentHeading = value;
      continue;
    }

    // Paragraph/verse entries: ['p1', 'verse', 'v3', 'label'/'content']
    const [para, , verse, field] = key;

    if (!chapter.paragraphs[para]) {
      chapter.paragraphs[para] = { id: para, heading: currentHeading, verses: {} };
    }

    if (!chapter.paragraphs[para].verses[verse]) {
      chapter.paragraphs[para].verses[verse] = { id: verse };
    }

    if (field === "label") {
      chapter.paragraphs[para].verses[verse].number = parseInt(value);
    } else if (field === "content" && value) {
      chapter.paragraphs[para].verses[verse].text = value;
    }
  }

  // Convert paragraphs map → clean array
  const paragraphsArray = Object.values(chapter.paragraphs).map((p) => ({
    ...p,
    verses: Object.values(p.verses).filter((v) => v.text), // remove empty verses
  }));

  return {
    book: "Acts",
    chapter: chapter.label,
    language: "pt",
    paragraphs: paragraphsArray,
  };
}

// --- INSERT INTO MONGODB ---
async function main() {
  const uri = "mongodb://localhost:27017"; // 🔁 Change to your connection string
  const client = new MongoClient(uri);

  try {
    await client.connect();
    console.log("✅ Connected to MongoDB");

    const db = client.db("bible"); // DB name
    const collection = db.collection("chapters"); // Collection name

    const document = parseDebugFile("debug_ACT_12_1608.txt");

    // Optional: avoid duplicates
    await collection.deleteOne({ book: document.book, chapter: document.chapter });

    const result = await collection.insertOne(document);
    console.log("✅ Inserted document with ID:", result.insertedId);

    // Preview what was inserted
    console.log("\n📄 Sample structure:");
    console.log(JSON.stringify(document.paragraphs[0], null, 2));

  } catch (err) {
    console.error("❌ Error:", err);
  } finally {
    await client.close();
  }
}

main();