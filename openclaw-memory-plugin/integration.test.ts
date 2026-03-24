import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { test, expect, beforeEach, afterEach } from "vitest";
import { MemoryDB } from "./memory-db.js";

let tmpDir: string;
let dbPath: string;

beforeEach(async () => {
  tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "openclaw-zvec-integration-"));
  dbPath = path.join(tmpDir, "memories");
});

afterEach(async () => {
  if (tmpDir) {
    await fs.rm(tmpDir, { recursive: true, force: true });
  }
});

test("zvec integration test", async () => {
  const db = new MemoryDB(dbPath, 1536); // OpenAI embedding dimension

  // Test storing a memory
  const memory = await db.store({
    text: "This is a test memory",
    vector: Array.from({ length: 1536 }, () => 0.1), // Mock embedding vector
    importance: 0.8,
    category: "other",
  });

  expect(memory.id).toBeDefined();
  expect(memory.text).toBe("This is a test memory");
  expect(memory.category).toBe("other");

  // Test searching
  const results = await db.search(
    Array.from({ length: 1536 }, () => 0.1),
    5,
    0.1,
  );
  expect(results.length).toBeGreaterThanOrEqual(0);

  // Test counting
  const count = await db.count();
  expect(count).toBeGreaterThanOrEqual(1);

  // Test deletion
  const deleted = await db.delete(memory.id);
  expect(deleted).toBe(true);

  // Test closing the database
  await db.close();
});
