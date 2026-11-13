---
name: md-to-pdf
description: Convert a Markdown file (Chinese or English, with LaTeX math) into a print-quality A4 PDF, fully offline — no Microsoft Office, no LibreOffice, no TeX distribution. Use when a .md must become a PDF deliverable (report, note, handout) whose layout has to be reproducible, or when an office suite or browser cannot be assumed. Pipes markdown-it and pre-rendered KaTeX into headless Chromium printing, then stamps page numbers with PyMuPDF; ships a Chromium-free Typst route for Android and locked-down containers.
license: AGPL-3.0-or-later
compatibility: Node.js >= 18, Microsoft Edge or Google Chrome for printing, Python 3 with pymupdf for page numbers and previews, and SimSun/SimHei (Windows) or fonts-noto-cjk (Linux) for Chinese text. The Typst fallback needs only one static binary. Windows, macOS and Linux; install.ps1 / install.sh.
allowed-tools: Bash(node *) Bash(python3 *) Bash(typst *)
metadata:
  when_to_use: A .md file must become a PDF deliverable (report, note, handout), Chinese or English, with or without math, and the result has to be reproducible with no GUI app — on Windows/macOS/Linux with Edge or Chrome, or on a host where no Chromium exists at all.
  hosts: DSH, Claude Code, Codex, Cursor
  homepage: https://github.com/ZihanZhang114514/md-to-pdf
---

# Markdown → PDF (offline, bilingual, real math)

One command turns a `.md` into a deliverable A4 PDF: **markdown-it → KaTeX
pre-rendered → headless Chromium print → PyMuPDF page numbers**. Fully offline —
no Word, no LibreOffice, no TeX. Formulas are vector typesetting, not screenshots.

Typographic language is inferred from the text itself: Chinese gets 宋体/SimSun
with a 2em first-line indent, English gets a Times-family serif with no indent and
automatic hyphenation. Force it with `MD2PDF_LANG=zh|en`; a wrong guess changes the
styling only, never the content.

Use the bundled implementation (`scripts/`), which ships `node_modules` — there is
no `npm install`. Do not write a second renderer.

## First 30 seconds

```bash
./install.sh                      # link into ~/.claude/skills and ~/.agents/skills (+ ~/.dsh when present)
node scripts/md2pdf.js --doctor   # node / vendored fonts / browser / python+pymupdf / CJK fonts
```

Windows: `.\install.ps1`. In the doctor table only the `+` rows are hard
requirements; the rest are hints.

## Convert

```bash
node scripts/md2pdf.js in.md out.pdf "Title" "Subtitle"   # render only
python scripts/add_pageno.py out.pdf                      # then stamp page numbers
./scripts/md2pdf.sh in.md out.pdf "Title"                 # macOS/Linux: render + stamp in one go
```

```powershell
& "<skill-dir>\scripts\md2pdf.ps1" -InputPath "报告.md" -OutputPath "报告.pdf" `
    -Title "报告标题" -Subtitle "副 标 题"
```

Or drag the `.md` onto `scripts\Drop-MD-Here.bat` (PDF appears next to the source,
title taken from the filename).

`out.pdf` is resolved to an absolute path; if the browser writes nothing the run
exits 4 instead of claiming success.

**Math delimiters:** `\( … \)` inline, `\[ … \]` display (on its own line). `$…$`
is *not* rendered and the build warns with the offending span — do not hand the
user a PDF full of `$E=mc^2$`.

## Layout recipe (A4)

```
@page { size: A4; margin: 2.4cm 2.5cm 2.2cm 2.6cm; }
body  12pt / line-height 1.72 / justify / 宋体(SimSun) + Times New Roman for Latin
h2    黑体 15pt, h3 黑体 12.5pt, margins 16pt/11pt, break-after: avoid
p     text-indent 2em; display equations centred, break-inside: avoid
page  9pt centred, stamped afterwards by PyMuPDF (Chromium has no @page margin boxes)
```

## English documents

Same command, no flags. A text is treated as Chinese only when it has ≥ 20 CJK
characters and CJK ≥ half the Latin count.

| | Chinese (zh) | English (en) |
|---|---|---|
| body | SimSun | Times New Roman → Liberation Serif → DejaVu Serif |
| headings | SimHei | Helvetica Neue → Arial → DejaVu Sans |
| first-line indent | 2em | 0 |
| hyphens | not needed | `hyphens: auto` + `lang="en"`, else justified text grows white rivers |
| one line = one paragraph | on (Chinese reports are written that way) | off (standard Markdown merging) |

## Verify before delivering

```bash
python scripts/pdf_pages.py report.pdf preview 150
```

Look for three things: formulas rendered as math (not source text), Chinese glyphs
present (no tofu), headings not stranded at a page bottom. Check the page count
against expectation. For English, also check that paragraphs were not shredded and
that hyphenation actually fired.

## Delivery

Hand over the absolute path (DSH: `present`, other agents: print the path). Say
which route was used, how many pages, and whether the render was visually checked.

## Requirements

| Need | Check | Without it |
|---|---|---|
| Node ≥ 18 | `node -v` | install Node, or use the Typst route |
| Python 3 + `pymupdf` | `python -c "import pymupdf"` | `python3 -m pip install -r scripts/requirements.txt` (PEP 668: add `--break-system-packages`) |
| Edge or Chrome | built-in candidate scan, `MD2PDF_EDGE` to override | no browser at all → Typst route |
| CJK font | `fc-list :lang=zh` | Windows has SimSun/SimHei; Debian/Ubuntu: `fonts-noto-cjk`; Android containers start with zero fonts |

`node scripts/md2pdf.js --selftest` prints the same readiness check.

## No Chromium?

See [`references/no-chromium.md`](references/no-chromium.md) — a measured route for
Android/Linux containers using a single static Typst binary, including the font
package, the `leading` conversion and the six Typst-specific traps.

For a report **without math**, don't hand-roll the conversion — one command:

```bash
python3 scripts/md2typst.py 报告.md 报告.typ --check   # then typst compile 报告.typ 报告.pdf
```

`--indent h` for Typst < 0.13, plus `--keep-fullwidth`, `--no-title-break`,
`--template`. It fixes the five non-formula traps a hand-rolled script silently
ships (demo body leak, full-width digits spaced one by one, h1 broken mid-word,
indent lost after a heading, `**bold**` line leaking into body text); each is a
test in `tests/test_md2typst.py`.

## Pitfalls

[`references/gotchas.md`](references/gotchas.md) — 32 numbered items, all measured:
why math must be extracted before markdown parsing, why fences must be protected
from the line-oriented layout, why the output path must be absolute, why headless
Chromium's stderr kills a strict PowerShell script, and why `###` must not be
demoted in a document that already has real heading levels.
