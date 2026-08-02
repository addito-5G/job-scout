#!/usr/bin/env bash
# Local agent toolchain for NextMove (idempotent).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Ollama"
if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama not installed. Install from https://ollama.com then re-run."
  exit 1
fi
if ! curl -sf http://127.0.0.1:11434/api/tags >/dev/null; then
  echo "Ollama not running. Start it (open the Ollama app) then re-run."
  exit 1
fi
echo "Ollama is up."

need_pull=()
for model in qwen2.5-coder:7b qwen2.5:14b; do
  if ! ollama list 2>/dev/null | awk '{print $1}' | grep -qx "$model"; then
    need_pull+=("$model")
  fi
done
for model in "${need_pull[@]+"${need_pull[@]}"}"; do
  echo "Pulling $model ..."
  ollama pull "$model"
done
echo "Code/chat models present."

echo "==> Playwright MCP package cache"
if command -v npx >/dev/null 2>&1; then
  npx -y @playwright/mcp@latest --help >/dev/null
  echo "Playwright MCP package OK."
else
  echo "npx missing — install Node.js LTS, then re-run."
  exit 1
fi

echo "==> Project MCP"
if [[ -f .cursor/mcp.json ]]; then
  echo ".cursor/mcp.json ready (Playwright)."
else
  cp .cursor/mcp.json.example .cursor/mcp.json
  echo "Created .cursor/mcp.json from example."
fi

echo
echo "Done. Human steps: SETUP_FOR_YOU.md"
echo "Critic: @challenge / поспорь  |  Canon: agents/README.md"
