---
name: md-to-pdf
description: Convert a Markdown file (Chinese or English, with LaTeX math) into a print-quality A4 PDF. One Python file, standard library only, and one external tool (typst). Use when a .md has to become a deliverable PDF — report, note, handout — with reproducible A4 layout, bilingual typography and numbered pages, on a machine where Office, LibreOffice and a TeX distribution are not available.
license: AGPL-3.0-or-later
compatibility: Python 3.9+ with the standard library, plus the typst CLI (a single static binary, ~30 MB) on PATH or in ~/.cache/md2pdf/. Chinese documents additionally need a CJK face — built in on Windows (SimSun), fonts-noto-cjk on Debian/Ubuntu. No Node.js, no browser, no Office, no TeX.
allowed-tools: Bash(python3 *) Bash(typst *)
metadata:
  when_to_use: A .md must become an A4 PDF with headings, tables, code and formulas, and the result has to be reproducible. Especially useful where the machine has no browser to print with and no Office suite — a container, a server, an Android-hosted Linux box.
  hosts: Claude Code, Codex, Cursor, DSH
  bundle: single-file edition (marketplace), script md2pdf.py
---

# Markdown → A4 PDF (one file, Typst backend)

**Requires:** `python3` (3.9+, standard library only) and `typst` (a single static
binary). Missing `typst`? Ask the user before downloading anything from
<https://github.com/typst/typst/releases>; cache it in `~/.cache/md2pdf/`, never
inside the skill or the project folder. A Chinese document also needs a CJK font
(Windows: built in; Debian/Ubuntu: `apt-get install -y fonts-noto-cjk`).

```bash
python md2pdf.py report.md report.pdf "报告标题" "副标题"      # --lang zh|en to force
python md2pdf.py --doctor                                     # is the environment ready?
```

The PDF is A4 (2.4/2.2/2.5/2.6 cm margins), 12pt, 1.72 line height, justified,
9pt centred page number, headings in a sans face. Chinese paragraphs get a 2em
first-line indent; English gets none and is hyphenated. Language is detected from
the text (≥ 20 CJK characters and CJK ≥ half the Latin count), and a wrong guess
changes typography only.

## What the Markdown subset covers

Headings (`#`…`###`), paragraphs, `**bold**`, `*italic*`, `` `code` ``, fenced
code (syntax highlighted, never split across pages), pipe tables with
`:--`/`--:`/`:-:` alignment, ordered and unordered lists, `>` quotes, `---` rules,
links, and math as `\( … \)` inline / `\[ … \]` on its own line.

Not supported, and not pretended: nested lists, footnotes, HTML blocks, images,
`$…$` math delimiters, and TeX commands outside the mapped set — those are passed
through verbatim and listed in a warning on stderr, so a wrong render is visible
rather than silent.

## Delivery

Give the user the absolute path of the PDF, the page count, and mention the
detected language. Verify before delivering: run
`python md2pdf.py input.md out.pdf --keep-typ` and check the exit code — 3 means
`typst` is missing, 4 means Typst rejected the document, 5 means it wrote nothing.
