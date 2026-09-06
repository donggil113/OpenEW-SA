#!/usr/bin/env bash
set -euo pipefail
repo="$(git rev-parse --show-toplevel)"
python="${PYTHON:-python3}"
exec "$python" "$repo/scripts/paper3/reviewer_remediation/build_pdfs.py" --repository "$repo" "$@"
