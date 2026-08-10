#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v latexmk >/dev/null 2>&1; then
  echo "latexmk is required but was not found on PATH." >&2
  exit 127
fi

latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
