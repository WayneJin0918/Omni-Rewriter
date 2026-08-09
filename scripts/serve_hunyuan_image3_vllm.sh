#!/usr/bin/env bash
# Compatibility wrapper — canonical script lives in scripts/serve/
exec "$(cd "$(dirname "$0")" && pwd)/serve/serve_hunyuan_image3_vllm.sh" "$@"
