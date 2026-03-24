# zvec Claude Memory Plugin

Claude Code memory plugin built on **zvec embedded vector database**.

- **Hybrid Architecture**: Session hooks + explicit skills for flexible memory management
- **SessionStart Hook**: Initialize memory session and state
- **SessionEnd Hook**: Commit session and optimize collection for better performance
- **Skills**: Use `memory-recall`, `memory-store`, and `memory-forget` for explicit control
- **Vector-based storage**: Uses zvec for efficient similarity search
- **Multiple embedding providers**: Supports OpenAI and compatible providers (e.g., DashScope, Sentence Transformers)
- **Local storage**: Embedded database with no external dependencies

## Features

- **Explicit Memory Control**: Manually store, recall, and forget memories via skills
- **Vector Search**: Semantic similarity-based memory retrieval
- **Persistent Storage**: Long-term memory across all sessions
- **Category Support**: Organize memories by category (decision, fix, preference, etc.)

## Design Choices

- **Storage**: Embedded zvec vector database
- **Mode**: Local-only (no HTTP server required)
- **Config**: Global config at `~/.zvec/zvec.conf`
- **Memory dir**: Configurable via `dbPath` in zvec.conf (default: `~/.zvec/memory.zvec`)

## Structure

```
claude-memory-plugin/
├── hooks/
│   ├── hooks.json
│   ├── session-start.sh      # Initialize session
│   └── session-end.sh        # Commit and optimize collection
├── scripts/
│   ├── memory_zvec.py        # Main memory bridge script
│   └── test_memory_zvec.py   # Test script
├── skills/
│   ├── memory-recall/
│   │   └── SKILL.md          # Retrieve memories from long-term storage
│   ├── memory-store/
│   │   └── SKILL.md          # Store important information
│   ├── memory-forget/
│   │   └── SKILL.md          # Delete specific memories
├── example.zvec.conf
└── README.md
```

## Configuration

Global configuration file at `~/.zvec/zvec.conf`:

```bash
mkdir -p ~/.zvec/
cp example.zvec.conf ~/.zvec/zvec.conf
# Edit ~/.zvec/zvec.conf with your API key
```

```json
{
  "embedding": {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "apiKey": "sk-your-openai-key",
    "apiUrl": "https://api.openai.com/v1/embeddings"
  },
  "dbPath": "~/.zvec/memory/database",
  "autoCapture": true,
  "autoRecall": true,
  "captureMaxChars": 500
}

```

### Configuration Options

- `embedding.provider`: `"openai"` or `"sentence-transformers"`
- `embedding.model`: Embedding model name (default: `"text-embedding-3-small"`)
- `embedding.apiKey`: API key for embedding service
- `embedding.apiUrl`: Custom API endpoint (optional)
- `dbPath`: Path to zvec database (default: `"~/.zvec/memory/database"`)
- `autoRecall`: Enable automatic memory injection (default: `true`)

## Hook Behavior

- `SessionStart`
  - Validate `zvec.conf` exists
  - Initialize global database path
  - Return session information for Claude context
- `SessionEnd`
  - Create memory collection if it doesn't exist (with proper schema)
  - Call `collection.optimize()` to improve query performance
  - Commit session data and report memory count

## Skills

All skills use relative paths via `${CLAUDE_PLUGIN_ROOT}` environment variable for portability.

### memory-recall

Search and retrieve relevant memories from long-term storage when you need context about user preferences, history, or personal information.

**Usage:**
```
Use memory-recall when:
- You need to access stored user memories from long-term storage
- Recall user preferences, interests, or personal context
- Get background information about the user that may be relevant
- Retrieve historical context that was previously saved
```

**Example:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_zvec.py recall --query "authentication fix" --top-k 5 --task-id "$TASK_ID"
```

### memory-store

Store important information in long-term memory. Use when the user wants to remember something specific, make a note for future sessions, or explicitly save knowledge.

**Usage:**
```
Use memory-store when:
- User asks you to remember something specific
- Important decisions are made
- Key fixes or solutions are discovered
- User preferences should be saved
```

**Categories:**
- `preference`: User likes/dislikes
- `decision`: Important decisions
- `fix`: Solutions to problems
- `fact`: Factual information
- `general`: Default category

**Example:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_zvec.py store --text "Use JWT tokens for authentication" --category "decision" --task-id "$TASK_ID"
```

### memory-forget

Delete specific memories from long-term storage. Use when the user wants to remove outdated information, incorrect memories, or no longer relevant data.

**Usage:**
```
Use memory-forget when:
- User requests deletion of specific information
- Outdated or incorrect memories need removal
- Cleaning up obsolete data
```

**Important Notes:**
- Always get explicit user confirmation before deleting memories
- When searching for memories to delete, show all matches and let user choose
- Memory IDs have format: `m_<12_character_hex>`
- Inform user that deletion is permanent

**Example:**
```bash
# Delete by memory ID
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_zvec.py forget --memory-id "m_abc123def456" --task-id "$TASK_ID"

# First search, then delete
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_zvec.py recall --query "outdated info" --top-k 10
```

## Installation

1. Quick Install (Plugin Marketplace)
```bash
/plugin marketplace add chinaux/zvec-agent-plugins
/plugin install memory-zvec
```

2. Local Installation:
```bash
git clone https://github.com/chinaux/zvec-agent-plugins.git
cd zvec-agent-plugins
claude --plugin-dir ./claude-memory-plugin
```

3. Create Configuration File:
```bash
mkdir -p ~/.zvec/
cp example.zvec.conf ~/.zvec/zvec.conf
# Edit ~/.zvec/zvec.conf with your settings
```

4. The plugin will automatically be loaded by Claude Code.

## API Reference

### Command Line Interface

**Store Memory:**
```bash
python3 scripts/memory_zvec.py store \
  --text "<memory text>" \
  --category "<category>"
```

**Recall Memories:**
```bash
python3 scripts/memory_zvec.py recall \
  --query "<search query>" \
  --top-k <number of results>
```

**Forget Memory:**
```bash
python3 scripts/memory_zvec.py forget \
  --memory-id "<memory_id>"
```

**API Response Format:**

All commands return JSON to stdout:

**Success:**
```json
{
  "ok": true,
  "status_line": "[memory-zvec] Operation successful",
  ...
}
```

**Error:**
```json
{
  "ok": false,
  "status_line": "[memory-zvec] Error description"
}
```

## Notes

- This plugin requires the zvec Python package to be installed
- Database files are stored locally in `.zvec/memory/database/`
- All sessions share the same global database for long-term memory
- Memory IDs have format: `m_<12_character_hex>`
- All skills use `${CLAUDE_PLUGIN_ROOT}` for portable paths
- Scripts include built-in error handling with stderr warnings for failures
- No debug logging - production-ready code

## Troubleshooting

Common issues:

1. **"zvec not available"**: Install zvec Python package
   ```bash
   pip install zvec
   ```

2. **Configuration errors**: Check `zvec.conf` syntax and required fields

3. **Permission errors**: Ensure write access to `.zvec/memory/database/` directory

4. **Memory not found**: Verify memory ID format (`m_<12_char_hex>`)

5. **No memories recalled**: Ensure autoRecall is enabled in config

## License

Apache 2.0
