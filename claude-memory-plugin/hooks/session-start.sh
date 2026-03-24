#!/usr/bin/env bash
# SessionStart hook: initialize zvec memory session.
# Uses global configuration from ~/.zvec/zvec.conf

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

log "=== SessionStart hook triggered ==="
log "input: $INPUT"

if [ ! -f "$BRIDGE" ]; then
  BRIDGE="$PROJECT_DIR/plugins/claude-memory-plugin/scripts/memory_zvec.py"
fi

# Run session-start to initialize (no --project-dir needed, uses global config)
OUT="$(python3 "$BRIDGE" session-start 2>/dev/null || true)"

log "session-start output: $OUT"

OK=$(echo "$OUT" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print('ok' in d and d['ok'])" 2>/dev/null || echo "false")
STATUS=$(echo "$OUT" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('status_line', '[memory-zvec] initialization failed'))" 2>/dev/null || echo "[memory-zvec] initialization failed")
ADDL=$(echo "$OUT" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('additional_context', ''))" 2>/dev/null || echo "")

json_status=$(python3 -c "import sys,json; print(json.dumps(sys.argv[1]))" "$STATUS" 2>/dev/null || echo '""')

if [[ "$OK" == "True" && -n "$ADDL" ]]; then
  json_addl=$(python3 -c "import sys,json; print(json.dumps(sys.argv[1]))" "$ADDL" 2>/dev/null || echo '""')
  echo "{\"systemMessage\": $json_status, \"hookSpecificOutput\": {\"hookEventName\": \"SessionStart\", \"additionalContext\": $json_addl}}"
  exit 0
fi

echo "{\"systemMessage\": $json_status}"
