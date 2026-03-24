# memory-zvec Plugin

An OpenClaw memory plugin that uses zvec as the embedded vector database for long-term memory storage and retrieval.

## Features

- **Vector Storage**: Uses zvec for efficient vector similarity search
- **Auto-Recall**: Automatically injects relevant memories into agent context
- **Auto-Capture**: Automatically captures important information from conversations
- **Multiple Tools**: Provides `memory_recall`, `memory_store`, and `memory_forget` tools
- **Enhanced Resource Management**: Proper collection lifecycle handling
- **Improved Error Handling**: Robust error handling with null validation

## Project Structure

```
openclaw-memory-plugin/
├── index.ts              # Main plugin entry point
├── config.ts             # Configuration schema and utilities
├── memory-db.ts          # Database abstraction layer
├── index.test.ts         # Unit tests
├── integration.test.ts   # Integration tests
├── switch-memory.sh      # Slot switch script
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
└── README.md             # Documentation
```

## Quick Install

```bash
# Build the plugin
pnpm install && pnpm clean && pnpm build

# Create npm package
npm pack

# Install in OpenClaw
openclaw plugins install ./memory-zvec-*.tgz
```

## Configuration

Configure in `~/.openclaw/openclaw.json`:

```json
{
  "plugins": {
    "entries": {
      "memory-zvec": {
        "enabled": true,
        "config": {
          "embedding": {
            "provider": "openai",
            "apiKey": "${OPENAI_API_KEY}",
            "model": "text-embedding-3-small",
            "baseUrl": "https://api.openai.com/v1/embeddings"
          },
          "dbPath": "~/.openclaw/memory/zvec",
          "autoCapture": true,
          "autoRecall": true
        }
      }
    },
    "slots": {
      "memory": "memory-zvec"
    }
  }
}
```

Set your API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Configuration Options

**Required Settings:**
- `embedding.provider`: Embedding provider (`openai`, etc.)
- `embedding.apiKey`: API key
- `embedding.model`: Embedding model name

**Optional Settings:**
- `dbPath`: Path to store zvec database (default: `~/.openclaw/memory/zvec`)
- `autoCapture`: Enable automatic memory capture (default: `true`)
- `autoRecall`: Enable automatic memory recall (default: `true`)
- `captureMaxChars`: Maximum message length for auto-capture (default: `500`)

## Usage

### Tools

#### memory_recall
Search through long-term memories.
```json
{
  "name": "memory_recall",
  "parameters": {
    "query": "user preferences",
    "limit": 5
  }
}
```

#### memory_store
Save important information to long-term memory.
```json
{
  "name": "memory_store",
  "parameters": {
    "text": "User prefers dark mode",
    "importance": 0.8,
    "category": "preference"
  }
}
```

#### memory_forget
Delete specific memories.
```json
{
  "name": "memory_forget",
  "parameters": {
    "memoryId": "uuid-of-memory-to-delete"
  }
}
```

### Memory Categories

- `preference`: User preferences
- `fact`: Factual information
- `decision`: Past decisions
- `entity`: Contact information and entity references
- `other`: Other miscellaneous information

### Auto-Capture Triggers

The plugin automatically captures when it detects:
- Explicit remember/save instructions
- Preference expressions
- Decision statements
- Contact information (phone numbers, emails)
- Important declarations

## ZVec Integration

Uses official [@zvec/zvec](https://www.npmjs.com/package/@zvec/zvec) package for vector database operations.

**Features:**
- Real vector database with HNSW index for fast similarity search
- Multiple distance metrics: cosine similarity and L2 distance
- Schema-based storage for text, importance, category, and timestamps
- High-performance operations with memory-mapped I/O
- Comprehensive resource management and error handling

## Development & Testing

```bash
# Install dependencies
pnpm install

# Build the project
pnpm build

# Run all tests
pnpm test

# Run unit tests
pnpm test:unit

# Run integration tests
pnpm test:integration

# Watch mode development
pnpm dev

# Clean build artifacts
pnpm clean
```

### Live Testing

```bash
# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Run all tests including live API tests
pnpm test
```

## Troubleshooting

**Issue**: "vector indexer not found for field: embedding"
- **Solution**: Delete the database directory and restart

**Issue**: Permission denied errors
- **Solution**: Ensure proper read/write permissions on database directory

**Issue**: High memory usage
- **Solution**: Reduce `captureMaxChars` to limit memory consumption

**Issue**: Slow search performance
- **Solution**: Ensure sufficient RAM and fast storage for database directory

### Debug Logging

```bash
# Set log level to debug
export OPENCLAW_LOG_LEVEL=debug

# Run OpenClaw and observe memory-zvec logs
openclaw gateway run
```

## Publishing

```bash
# Update version in package.json

# Run full test suite
pnpm clean && pnpm install && pnpm test && pnpm build

# Login to npm
npm login

# Publish
npm publish --access public
```

## License

Apache 2.0
