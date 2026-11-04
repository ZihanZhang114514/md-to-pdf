#!/bin/sh
# md-to-pdf — markdown -> A4 PDF (macOS / Linux entry point).
#
#   ./md2pdf.sh report.md report.pdf ["Title"] ["Subtitle"]
#   MD2PDF_NO_PAGES=1 ./md2pdf.sh report.md report.pdf    # skip page numbers
#
# Windows users: scripts\md2pdf.ps1 or scripts\Drop-MD-Here.bat
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ "$#" -lt 2 ]; then
  printf 'usage: %s <input.md> <output.pdf> ["Title"] ["Subtitle"]\n' "$0" >&2
  exit 2
fi

NODE=${MD2PDF_NODE:-}
if [ -z "$NODE" ]; then
  NODE=$(command -v node || true)
fi
if [ -z "$NODE" ]; then
  printf 'node not found: install Node.js >= 18, or set MD2PDF_NODE to its path\n' >&2
  exit 2
fi

OUT=$2
"$NODE" "$HERE/md2pdf.js" "$@"

if [ "${MD2PDF_NO_PAGES:-0}" != "1" ]; then
  PY=${MD2PDF_PYTHON:-}
  if [ -z "$PY" ]; then
    PY=$(command -v python3 || command -v python || true)
  fi
  if [ -n "$PY" ] && "$PY" -c 'import pymupdf' 2>/dev/null; then
    "$PY" "$HERE/add_pageno.py" "$OUT" || printf 'warning: page numbers were not stamped\n' >&2
  else
    printf 'warning: pymupdf not installed, PDF built without page numbers\n' >&2
    printf '         python3 -m pip install -r %s/requirements.txt\n' "$HERE" >&2
  fi
fi

printf 'done: %s\n' "$OUT"
