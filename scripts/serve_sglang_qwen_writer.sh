#!/usr/bin/env bash
set -euo pipefail
exec "$(cd "$(dirname "$0")" && pwd)/serve/serve_sglang_qwen_writer.sh" "$@"
