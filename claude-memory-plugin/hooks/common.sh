#!/usr/bin/env bash
# Common utilities for zvec memory hooks.

set -euo pipefail

# Log file
export ZVEC_LOG_FILE="${ZVEC_LOG_FILE:-/tmp/memory-zvec-hooks.log}"

# Read stdin JSON into INPUT (Claude Code passes hook data via stdin)
INPUT="$(cat)"

# Configuration and state files
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
ZVEC_CONF="$HOME/.zvec/zvec.conf"
BRIDGE="$PLUGIN_ROOT/scripts/memory_zvec.py"
_json_encode_str() {
    printf '%s' "$1" | python3 -c '
import json
import sys
print(json.dumps(sys.stdin.read()))
'
}

_json_val() {
    local json_input="$1"
    local key="$2"
    local default="${3:-}"

    printf '%s' "$json_input" | python3 -c "
import json
import sys
try:
    data = json.loads(sys.stdin.read())
    val = data.get('$key')
    if val is None:
        print('$default')
    else:
        print(val)
except Exception as e:
    print('$default')
"
}

# Run bridge command (uses global config, no --project-dir needed)
run_bridge() {
    local cmd="$1"
    shift
    python3 "$BRIDGE" "$cmd" "$@"
}

# Log message to /tmp file
log() {
    echo "[$(date -Iseconds)] [memory-zvec] $*" >> "$ZVEC_LOG_FILE"
}