#!/bin/bash

# OpenClaw Memory Plugin Switcher
# Usage: ./switch-memory.sh [memory-core|memory-zvec]

CONFIG="$HOME/.openclaw/openclaw.json"
BACKUP="$CONFIG.bak"

if [ ! -f "$CONFIG" ]; then
    echo "❌ Error: Config file not found at $CONFIG"
    exit 1
fi

# Create backup
cp "$CONFIG" "$BACKUP"
echo "✓ Backup created: $BACKUP"

if [ "$1" == "memory-zvec" ]; then
    # Switch to memory-zvec
    if grep -q '"memory": "memory-core"' "$CONFIG"; then
        sed -i.bak 's/"memory": "memory-core"/"memory": "memory-zvec"/g' "$CONFIG"
        echo "✅ Switched to memory-zvec"
    else
        echo "ℹ️  Already using memory-zvec"
    fi
elif [ "$1" == "memory-core" ]; then
    # Switch to memory-core
    if grep -q '"memory": "memory-zvec"' "$CONFIG"; then
        sed -i.bak 's/"memory": "memory-zvec"/"memory": "memory-core"/g' "$CONFIG"
        echo "✅ Switched to memory-core"
    else
        echo "ℹ️  Already using memory-core"
    fi
else
    # Show current status
    CURRENT=$(grep '"memory":' "$CONFIG" | head -1)
    echo "📊 Current memory plugin:"
    echo "   $CURRENT"
    echo ""
    echo "Usage:"
    echo "  $0 memory-core   - Switch to default memory-core"
    echo "  $0 memory-zvec   - Switch to memory-zvec plugin"
    exit 0
fi

# Verify the change
echo ""
echo "Current configuration:"
grep -A 2 '"slots"' "$CONFIG" | grep '"memory"'
echo ""
echo "Restart OpenClaw to apply changes:"
echo "  openclaw gateway run"
