#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
output="${1:?Provide an external PDF output directory}"
mkdir -p "$output"
output="$(realpath "$output")"
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir="$output" main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir="$output" supplementary.tex
