#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${APEX_PYTHON:-python3}"
exec "$PYTHON" "$ROOT/build_backend.py" --platform linux "$@"
