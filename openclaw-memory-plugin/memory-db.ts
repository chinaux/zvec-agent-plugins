// Zvec Memory Database Implementation
// Based on official Zvec Node.js API: https://zvec.org/api-reference/nodejs/

import { randomUUID } from "node:crypto";
import fs from "node:fs/promises";
import {
  ZVecCreateAndOpen,
  ZVecOpen,
  ZVecCollectionSchema,
  ZVecDocInput,
  ZVecQuery,
  ZVecHnswIndexParams,
  ZVecIndexType,
  ZVecMetricType,
  ZVecDataType,
  ZVecLogLevel,
  ZVecInitialize,
  isZVecError,
} from "@zvec/zvec";

// Types
interface VectorDatabase {
  connect(path: string): Promise<VectorConnection>;
}

interface VectorConnection {
  createCollection(name: string, options: { dimensions: number }): Promise<VectorCollection>;
  getCollection(name: string): Promise<VectorCollection>;
  listCollections(): Promise<string[]>;
}

interface VectorCollection {
  insert(records: VectorRecord[]): Promise<void>;
  search(
    vector: number[],
    options: { limit: number; minScore?: number },
  ): Promise<VectorSearchResult[]>;
  delete(id: string): Promise<void>;
  count(): Promise<number>;
  close(): void;
}

interface VectorRecord {
  id: string;
  text: string;
  vector: number[];
  importance: number;
  category: string;
  createdAt: number;
}

interface VectorSearchResult {
  id: string;
  text: string;
  vector: number[];
  importance: number;
  category: string;
  createdAt: number;
  score: number;
}

// ZVec implementation
const zvecDatabase: VectorDatabase = {
  connect: async (path: string) => {
    const collections = new Map<string, VectorCollection>();

    return {
      createCollection: async (name: string, options: { dimensions: number }) => {
        // Define schema for our memory collection
        const schema = new ZVecCollectionSchema({
          name: name,
          vectors: [
            {
              name: "embedding",
              dataType: ZVecDataType.VECTOR_FP32,
              dimension: options.dimensions,
              indexParams: {
                indexType: ZVecIndexType.HNSW,
                metricType: ZVecMetricType.L2,
              } as ZVecHnswIndexParams,
            },
          ],
          fields: [
            {
              name: "text",
              dataType: ZVecDataType.STRING,
            },
            {
              name: "importance",
              dataType: ZVecDataType.FLOAT,
            },
            {
              name: "category",
              dataType: ZVecDataType.STRING,
            },
            {
              name: "createdAt",
              dataType: ZVecDataType.INT64,
            },
          ],
        });

        // Check if collection already exists
        const collectionPath = `${path}/${name}`;
        let zvecCollection;

        // Check if collection directory exists
        try {
          await fs.access(collectionPath);
          // Collection exists, open it
          zvecCollection = ZVecOpen(collectionPath);
          if (!zvecCollection) {
            throw new Error(`Failed to open existing zvec collection at ${collectionPath}`);
          }
        } catch (error) {
          // If it's not a file access error, re-throw
          if (!(error instanceof Error && (error as NodeJS.ErrnoException).code === "ENOENT")) {
            throw error;
          }
          // Collection doesn't exist, create it
          zvecCollection = ZVecCreateAndOpen(collectionPath, schema);
          if (!zvecCollection) {
            throw new Error(`Failed to create zvec collection at ${collectionPath}`);
          }
        }

        const collection: VectorCollection = {
          insert: async (records: VectorRecord[]) => {
            const docs: ZVecDocInput[] = records.map((record) => ({
              id: record.id,
              vectors: {
                embedding: new Float32Array(record.vector),
              },
              fields: {
                text: record.text,
                importance: record.importance,
                category: record.category,
                createdAt: record.createdAt,
              },
            }));

            try {
              // Insert documents
              const statuses = zvecCollection.insertSync(docs);

              // Handle insert result (assuming successful if no exception thrown)
              if (statuses && typeof statuses === "object" && "ok" in statuses) {
                const status = statuses as {
                  ok: boolean;
                  message?: string;
                  code?: number;
                };
                if (!status.ok) {
                  throw new Error(
                    `Failed to insert record: ${status.message || "unknown error"} (code: ${status.code || "unknown"})`,
                  );
                }
              }

              // Data should be written synchronously with insertSync
              // No explicit flush needed
            } catch (error) {
              if (isZVecError(error)) {
                throw new Error(`ZVec insert error: ${error.message} (code: ${error.code})`);
              }
              throw error;
            }
          },

          search: async (vector: number[], options: { limit: number; minScore?: number }) => {
            try {
              const query: ZVecQuery = {
                fieldName: "embedding",
                vector: new Float32Array(vector),
                topk: Math.max(1, options.limit), // Ensure at least 1 result
                includeVector: true,
                outputFields: ["text", "importance", "category", "createdAt"],
              };

              const results = zvecCollection.querySync(query);

              return results
                .map((doc) => ({
                  id: doc.id,
                  text: doc.fields.text,
                  vector: Array.from(doc.vectors.embedding as Float32Array),
                  importance: doc.fields.importance,
                  category: doc.fields.category,
                  createdAt: doc.fields.createdAt,
                  score: 1 / (1 + doc.score),
                }))
                .filter((entry) => !options.minScore || entry.score >= options.minScore);
            } catch (error) {
              if (isZVecError(error)) {
                throw new Error(`ZVec search error: ${error.message} (code: ${error.code})`);
              }
              throw error;
            }
          },

          delete: async (id: string) => {
            try {
              const status = zvecCollection.deleteSync(id);

              // Handle both single and batch delete results
              if (Array.isArray(status)) {
                // Should not happen for single delete, but handle gracefully
                for (const s of status) {
                  if (!s.ok) {
                    throw new Error(`Failed to delete record: ${s.message} (code: ${s.code})`);
                  }
                }
              } else {
                if (!status.ok) {
                  throw new Error(
                    `Failed to delete record: ${status.message} (code: ${status.code})`,
                  );
                }
              }
            } catch (error) {
              if (isZVecError(error)) {
                throw new Error(`ZVec delete error: ${error.message} (code: ${error.code})`);
              }
              throw error;
            }
          },

          count: async () => {
            try {
              return zvecCollection.stats.docCount;
            } catch (error) {
              if (isZVecError(error)) {
                throw new Error(`ZVec count error: ${error.message} (code: ${error.code})`);
              }
              throw error;
            }
          },

          close: () => {
            try {
              // Close the zvec collection
              // Assuming zvec has a close method - this may need adjustment
              // based on actual zvec API
              const collection = zvecCollection as unknown as {
                close?: () => void;
                closeSync?: () => void;
              };
              if (typeof collection.close === "function") {
                console.info("memory-zvec: closing zvec collection use close");
                collection.close();
              }
              if (typeof collection.closeSync === "function") {
                console.info("memory-zvec: closing zvec collection use closeSync");
                collection.closeSync();
              }
            } catch (error) {
              if (isZVecError(error)) {
                throw new Error(`ZVec close error: ${error.message} (code: ${error.code})`);
              }
              throw error;
            }
          },
        };

        collections.set(name, collection);
        return collection;
      },

      getCollection: async (name: string) => {
        const collection = collections.get(name);
        if (!collection) {
          throw new Error(`Collection ${name} not found`);
        }
        return collection;
      },

      listCollections: async () => {
        return Array.from(collections.keys());
      },
    };
  },
};

// Memory types
export type MemoryCategory = "preference" | "decision" | "entity" | "fact" | "other";

export interface MemoryEntry {
  id: string;
  text: string;
  vector: number[];
  importance: number;
  category: MemoryCategory;
  createdAt: number;
}

export interface MemorySearchResult {
  entry: MemoryEntry;
  score: number;
}

const COLLECTION_NAME = "memories";

export class MemoryDB {
  private db: VectorConnection | null = null;
  private collection: VectorCollection | null = null;
  private initPromise: Promise<void> | null = null;

  constructor(
    private readonly dbPath: string,
    private readonly vectorDim: number,
  ) {}

  private async ensureInitialized(): Promise<void> {
    if (this.collection) {
      return;
    }
    if (this.initPromise) {
      return this.initPromise;
    }

    this.initPromise = this.doInitialize();
    return this.initPromise;
  }

  private async doInitialize(): Promise<void> {
    // Initialize Zvec globally
    ZVecInitialize({ logLevel: ZVecLogLevel.WARN });

    // Initialize zvec database
    this.db = await zvecDatabase.connect(this.dbPath);
    const collections = await this.db.listCollections();

    if (collections.includes(COLLECTION_NAME)) {
      this.collection = await this.db.getCollection(COLLECTION_NAME);
    } else {
      this.collection = await this.db.createCollection(COLLECTION_NAME, {
        dimensions: this.vectorDim,
      });
    }
  }

  async store(entry: Omit<MemoryEntry, "id" | "createdAt">): Promise<MemoryEntry> {
    await this.ensureInitialized();

    const fullEntry: MemoryEntry = {
      ...entry,
      id: randomUUID(),
      createdAt: Date.now(),
    };

    // Store in zvec
    await this.collection!.insert([
      {
        id: fullEntry.id,
        text: fullEntry.text,
        vector: fullEntry.vector,
        importance: fullEntry.importance,
        category: fullEntry.category,
        createdAt: fullEntry.createdAt,
      },
    ]);

    return fullEntry;
  }

  async search(vector: number[], limit = 5, minScore = 0.5): Promise<MemorySearchResult[]> {
    await this.ensureInitialized();

    // Search in zvec
    const results = await this.collection!.search(vector, {
      limit,
      minScore,
    });

    // Convert result format
    return results
      .map((row) => ({
        entry: {
          id: row.id,
          text: row.text,
          vector: row.vector,
          importance: row.importance,
          category: row.category as MemoryCategory,
          createdAt: row.createdAt,
        },
        score: row.score,
      }))
      .filter((r) => r.score >= minScore);
  }

  async delete(id: string): Promise<boolean> {
    await this.ensureInitialized();

    // Delete record
    await this.collection!.delete(id);

    // Flush after delete
    await this.flush();

    return true;
  }

  async count(): Promise<number> {
    await this.ensureInitialized();

    // Get record count
    return await this.collection!.count();
  }

  /**
   * Close the database connection and flush any pending writes
   */
  async close(): Promise<void> {
    if (this.collection) {
      try {
        // Close the collection
        this.collection.close();
        this.collection = null;
      } catch (error) {
        console.warn("Error closing zvec collection:", error);
        // Don't throw - we want to clean up as much as possible
      }
    }
    this.db = null;
  }

  /**
   * Flush pending writes to disk (no-op for zvec as writes are synchronous)
   */
  async flush(): Promise<void> {
    // Zvec writes are synchronous, so no explicit flush is needed
    // This method exists for API compatibility
  }
}
