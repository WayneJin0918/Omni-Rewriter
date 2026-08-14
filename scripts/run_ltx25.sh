#!/usr/bin/env bash
# Compatibility wrapper — canonical script lives in scripts/serve/
exec "$(cd "$(dirname "$0")" && pwd)/serve/run_ltx25.sh" "$@"
