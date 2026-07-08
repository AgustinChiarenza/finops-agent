#!/usr/bin/env bash
# Helper: drop FinOps documents into agent/knowledge/ and ingest them.
# This is a convenience wrapper — the knowledge base is intentionally empty
# in the repo. Nothing runs automatically.
set -euo pipefail

KNOWLEDGE_DIR="${KNOWLEDGE_DIR:-agent/knowledge}"
cd "$(dirname "$0")/.."

if [ ! -d "$KNOWLEDGE_DIR" ]; then
  echo "❌ $KNOWLEDGE_DIR no existe." >&2
  exit 1
fi

count=$(find "$KNOWLEDGE_DIR" -type f \( -name '*.pdf' -o -name '*.docx' -o -name '*.md' -o -name '*.txt' \) | wc -l)
if [ "$count" -eq 0 ]; then
  echo "⚠️  $KNOWLEDGE_DIR está vacío. Copiá tus documentos FinOps ahí y volvé a correr este script."
  exit 0
fi

echo "📚 $count documento(s) en $KNOWLEDGE_DIR. Corriendo ingest..."
python -m app.rag.ingest "$@"
