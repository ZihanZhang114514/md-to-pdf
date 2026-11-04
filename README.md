# md-to-pdf

[中文说明](README.zh-CN.md)

A **DSH skill** that turns a Markdown file — **Chinese or English**, LaTeX math and all — into a print-quality A4 PDF **fully offline**, without Microsoft Office, LibreOffice or a TeX distribution.

The layout language is detected from the text itself, so the same command typesets both languages correctly: Chinese gets 宋体 with 2-character first-line indent, English gets a Times-family serif, no indent and automatic hyphenation.

```
markdown-it  →  KaTeX (pre-rendered to HTML)  →  headless Chromium print  →  PyMuPDF page numbers
```

Formulas are real vector typesetting (not screenshots), and the same `.md` always produces the same `.pdf`.

---

## Features

- ✅ `\( … \)` / `\[ … \]` math rendered with KaTeX (fonts vendored, no network needed)
- ✅ **Bilingual typography**: Chinese (宋体/黑体, 2em indent) and English (Times family, no indent, `hyphens: auto`) from the same command — auto-detected, or forced with `MD2PDF_LANG=zh|en`
- ✅ A4, 1.72 line-height, justified, page numbers — identical for both languages
- ✅ Page numbers stamped after printing (Chromium has no `@page` margin boxes)
- ✅ Headings, tables, lists, code blocks; heading-level normalisation (`###` → `##`, `**bold line**` → `###`)
- ✅ One command, or drag-and-drop a `.md` onto a `.bat`
- ✅ Self-contained: `scripts/node_modules` ships with the repo — no `npm install`

## Requirements

| Need | Check |
|---|---|
| Node.js ≥ 18 | `node -v` |
| Python 3 + `pymupdf` (page numbers, previews) | `python -c "import pymupdf"` — install with `python3 -m pip install -r scripts/requirements.txt` |
| Microsoft Edge or Google Chrome | `MD2PDF_EDGE` env var if not in a standard location |
| 宋体 / 黑体 (SimSun / SimHei) | Windows built-in; on Linux swap the CSS font stack for Noto Sans CJK |
| A Latin serif for English | Times/Liberation/DejaVu Serif — one of them is on every Windows/Linux box |

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

English documents need no special flags — just run the same command:

```sh
node scripts/md2pdf.js paper.md paper.pdf "Newton's Rings" "Lab Report 4.18"
# -> html lang="en", Times-family serif, no first-line indent, hyphenation on

# mixed / ambiguous text: lock the layout language explicitly
MD2PDF_LANG=zh node scripts/md2pdf.js notes.md notes.pdf
MD2PDF_LANG=en node scripts/md2pdf.js notes.md notes.pdf
```

| | Chinese | English |
|---|---|---|
| Body font | SimSun / 宋体 | Times New Roman → Liberation Serif → DejaVu Serif |
| Headings | SimHei / 黑体 | Helvetica Neue → Arial → DejaVu Sans |
| First-line indent | 2em | none |
| Hyphenation | — | `hyphens: auto` + `<html lang="en">` |
| Soft line breaks | one paragraph per source line | standard Markdown merging |
| `###` headings | demoted to `##` only when the doc has no `##` at all | preserved |

Check that the toolchain is complete:

```sh
node scripts/md2pdf.js --selftest
```

Inspect the result (rasterise pages to PNG for a visual check):

```sh
python scripts/pdf_pages.py report.pdf preview 140
```

> **No Chromium?** On an Android phone's Ubuntu container there is no Edge/Chrome
> and snap cannot run; WeasyPrint is not a substitute either — its `ex`-unit maths
> makes inline fractions overlap the body text. Use the bundled Typst fallback
> instead: one 48 MB static binary, LaTeX-class maths, fully offline.
> `typst compile scripts/typst-template.typ /sdcard/report.pdf` — see the "No Chromium" section of SKILL.md.

## Layout in this repo

```
SKILL.md                  skill manifest + decision table + 30 hard-won pitfalls
scripts/
  md2pdf.js               md → KaTeX → HTML → headless Chromium → PDF
  md2pdf.ps1              one-command wrapper, auto-detects node / python / browser
  add_pageno.py           PyMuPDF page numbers
  pdf_pages.py            PDF → PNG for visual verification
  typst-template.typ      Chinese A4 report template for hosts without Chromium
  typst-template-en.typ   English A4 report template for the same hosts
  Drop-MD-Here.bat        drag-and-drop entry point
  requirements.txt        Python deps of add_pageno.py / pdf_pages.py (pymupdf)
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
| **Typst** (single static binary) | excellent (Noto CJK) | excellent | **no Chromium: Android / Linux container** |

Measured on the same Chinese lab report: **Word ≈ KaTeX > XeLaTeX > LibreOffice**. Do not install a 4 GB TeX distribution just to print formulas.

## Gotchas

See the "踩坑清单" section of [SKILL.md](SKILL.md) — including why math must be extracted *before* markdown parsing, why display equations need a standalone placeholder, why `$Input`/`$Output` must never be PowerShell parameter names, and why headless Chromium's stderr output kills a strict PowerShell script, why the line-oriented layout shreds English paragraphs, and why `###` must not be demoted in a document that already has real heading levels.
