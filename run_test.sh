#!/usr/bin/env bash
set -euo pipefail

# Simple run: 10 conversations (1× each) via protected .so in Core/

ROOT="$(cd "$(dirname "$0")" && pwd)"

: "${OPENAI_API_KEY:?OPENAI_API_KEY is required}"

export PYTHONPATH="${PYTHONPATH:-$ROOT/Core}"
export DATA_DIR="${DATA_DIR:-$ROOT/data}"
export MODELS_DIR="${MODELS_DIR:-$ROOT/models}"
export RESULTS_DIR="${RESULTS_DIR:-$ROOT/results}"
# Ollama for synonym expansion
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
export OLLAMA_URL="${OLLAMA_URL:-$OLLAMA_BASE_URL}"

mkdir -p "$RESULTS_DIR"

for conv in {0..9}; do
  echo "=== Conversation ${conv} ==="
  LOCOMO_CONV_INDEX=$conv SEED=2001 python3 - <<'PY'
import vac_memory_system_v1_test_locomo as m
m.run_pipeline_v4()
PY

  # Санитизируем summary в последнем файле результатов для данного конвоя
  latest="$(ls -t "$RESULTS_DIR"/vac_v1_conv${conv}_seed${SEED:-2001}_*.json 2>/dev/null | head -n1 || true)"
  if [ -n "$latest" ]; then
    echo "Sanitizing summary in $latest"
    python3 "$ROOT/code/sanitize_summary.py" "$latest" || true
  fi
done

echo "Done."
