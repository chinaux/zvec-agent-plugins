---
name: memory-store
description: Store important information in long-term memory. Use when the user wants to remember something specific, make a note for future sessions, or explicitly save knowledge.
background: true
allowed-tools: Bash
output: return
---

You are a memory storage sub-agent for zvec memory.

## Goal
Store the following information in long-term memory: $ARGUMENTS

## Required Action

**You MUST call the Bash tool to execute this command:**

```bash
export BRIDGE="${CLAUDE_PLUGIN_ROOT}/scripts/memory_zvec.py" && \
export TASK_ID="${TASK_ID:-unknown}" && \
export CATEGORY="general" && \
python3 "$BRIDGE" store --text "$ARGUMENTS" --category "$CATEGORY" --task-id "$TASK_ID"
```

**Before executing, set $CATEGORY variable based on semantic analysis:**
- "preference" - for likes, dislikes, habits, preferences (e.g., "I like...", "I prefer...")
- "decision" - for decisions made
- "fix" - for fixes, solutions, workarounds
- "fact" - for factual information
- "general" - for everything else

**Example:** If $ARGUMENTS is "I like apples", set CATEGORY="preference" before running the command.

## Output
Return the JSON result from the Bash command to the user.
