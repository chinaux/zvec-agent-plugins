#!/usr/bin/env bash
# SessionEnd hook: commit and optimize zvec memory session.
# Uses global configuration from ~/.zvec/zvec.conf

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

log "=== SessionEnd hook triggered ==="
log "input: $INPUT"

if [ ! -f "$BRIDGE" ]; then
  BRIDGE="$PROJECT_DIR/plugins/claude-memory-plugin/scripts/memory_zvec.py"
fi

# Run session-end to commit and optimize (no --project-dir needed, uses global config)
OUT="$(python3 "$BRIDGE" session-end 2>/dev/null || true)"
STATUS=$(echo "$OUT" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('status_line', '[memory-zvec] Session ended'))" 2>/dev/null || echo "[memory-zvec] Session ended")

json_status=$(python3 -c "import sys,json; print(json.dumps(sys.argv[1]))" "$STATUS" 2>/dev/null || echo '""')
echo "{\"systemMessage\": $json_status}"
