#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${1:-8766}"
cd "$ROOT"
# Serve experiment root so /videos and /pe resolve.
exec python3 -m http.server "$PORT" --bind 0.0.0.0
