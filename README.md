# Agent Plugins

This repository contains AI agent memory plugins.

> **Note**: This is a **demo-level project** designed to demonstrate how zvec can be used as a simple memory system in AI agents.

## Plugins

### claude-memory-plugin/
Claude Code memory plugin based on zvec vector database. Provides session hooks and skills for explicit memory management (store, recall, forget).

### openclaw-memory-plugin/
OpenClaw memory plugin using zvec as embedded vector database. Supports automatic memory capture and retrieval with multiple tools.

## Structure

```
agent-plugins/
├── claude-memory-plugin/    # Claude Code memory plugin
└── openclaw-memory-plugin/  # OpenClaw memory plugin
```