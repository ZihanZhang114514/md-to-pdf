# md-to-pdf

A **DSH skill** that turns a Markdown file — Chinese text, LaTeX math and all — into a print-quality A4 PDF **fully offline**, without Microsoft Office, LibreOffice or a TeX distribution.

```
markdown-it  →  KaTeX (pre-rendered to HTML)  →  headless Chromium print  →  PyMuPDF page numbers
```

Formulas are real vector typesetting (not screenshots), and the same `.md` always produces the same `.pdf`.

---

## Features

- ✅ `\( … \)` / `\[ … \]` math rendered with KaTeX (fonts vendored, no network needed)
- ✅ Chinese typography recipe: A4, 宋体/黑体, 1.72 line-height, 2-character first-line indent, justified
- ✅ Page numbers stamped after printing (Chromium has no `@page` margin boxes)
- ✅ Headings, tables, lists, code blocks; heading-level normalisation (`###` → `##`, `**bold line**` → `###`)
- ✅ One command, or drag-and-drop a `.md` onto a `.bat`
- ✅ Self-contained: `scripts/node_modules` ships with the repo — no `npm install`

## Requirements

| Need | Check |
|---|---|
| Node.js ≥ 18 | `node -v` |
| Python 3 + `pymupdf` (page numbers, previews) | `python -c "import pymupdf"` — install with `pip install pymupdf -i https://pypi.tuna.tsinghua.edu.cn/simple` |
| Microsoft Edge or Google Chrome | `MD2PDF_EDGE` env var if not in a standard location |
| 宋体 / 黑体 (SimSun / SimHei) | Windows built-in; on Linux swap the CSS font stack for Noto Sans CJK |

## Quick start

```powershell
# Windows PowerShell
& ".\scripts\md2pdf.ps1" `
    -InputPath  "D:\work\report.md" `
    -OutputPath "D:\work\report.pdf" `
    -Title      "报告标题" `
    -Subtitle   "实 验 报 告"
```

Or drag any `.md` onto `scripts\Drop-MD-Here.bat` — the PDF appears next to the source file.

Render-only (no page numbers):

```sh
node scripts/md2pdf.js input.md output.pdf "Title" "Subtitle"
```

Check that the toolchain is complete:

```sh
node scripts/md2pdf.js --selftest
```

Inspect the result (rasterise pages to PNG for a visual check):

```sh
python scripts/pdf_pages.py report.pdf preview 140
```

## Layout in this repo

```
SKILL.md                  skill manifest + decision table + 14 hard-won pitfalls
scripts/
  md2pdf.js               md → KaTeX → HTML → headless Chromium → PDF
  md2pdf.ps1              one-command wrapper, auto-detects node / python / browser
  add_pageno.py           PyMuPDF page numbers
  pdf_pages.py            PDF → PNG for visual verification
  Drop-MD-Here.bat        drag-and-drop entry point
  package.json, node_modules/   vendored katex + markdown-it
```

## Use it as a DSH skill

Clone this repo as a skill folder and let the harness discover it:

```powershell
git clone https://github.com/ZihanZhang114514/md-to-pdf "$env:USERPROFILE\.dsh\skills\md-to-pdf"
```

or point the filesystem skill provider at a custom root:

```yaml
customSkillDirs:
  - D:\dsh_skills
```

A skill folder is discovered only as `<root>/<name>/SKILL.md` — nested manifest files are ignored.

## How it compares with the other engines

| Engine | Chinese | Math | When |
|---|---|---|---|
| **KaTeX + headless Chromium** (this repo) | good | excellent | `.md` → PDF, the default |
| Word COM (`python-docx` + OMML) | best | good (editable formulas) | user wants an editable `.docx` |
| LibreOffice headless | fair | fair (OMML spacing degrades) | no Office, other formats → PDF |
| XeLaTeX + ctex | excellent | excellent | academic typesetting, heavy install |

Measured on the same Chinese lab report: **Word ≈ KaTeX > XeLaTeX > LibreOffice**. Do not install a 4 GB TeX distribution just to print formulas.

## Gotchas

See the "踩坑清单" section of [SKILL.md](SKILL.md) — including why math must be extracted *before* markdown parsing, why display equations need a standalone placeholder, why `$Input`/`$Output` must never be PowerShell parameter names, and why headless Chromium's stderr output kills a strict PowerShell script.
