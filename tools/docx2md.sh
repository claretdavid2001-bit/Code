#!/usr/bin/env bash
# Convierte todos los .docx de tfm/ a Markdown en tfm/_md/ para que los agentes los lean.
# Uso: bash tools/docx2md.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p tfm/_md
shopt -s nullglob
for f in tfm/*.docx; do
  out="tfm/_md/$(basename "${f%.docx}").md"
  pandoc "$f" -t gfm --wrap=none --track-changes=accept -o "$out"
  echo "→ $out"
done
