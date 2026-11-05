# Store listing copy (Agensi / Gumroad / Ko-fi)

Paste-ready English copy. The same text works on any marketplace that shows a
title, a short line, a long description and screenshots.

**Price:** $9 (Agensi keeps 30%, so ≈ $6.30 net). The platform's own guidance puts
single-purpose skills at $3–9 and "skills with scripts, references and a
thorough README" at $12–25; this sits at the bottom of that band because it has no
social proof yet (0 stars) — raise it after the first ten sales.

## What actually ships on a skill marketplace

A skill marketplace (Agensi included) delivers **text over an MCP connection** and
runs a script from a temporary file: binaries are listed but never served, and a
listing must stay under 200 text files / 6M characters. The root pipeline needs 369
files and 120 font binaries, so the artifact to list is **`agensi/`** — two text
files (`SKILL.md`, `md2pdf.py`) and one external tool:

| Listed artifact (`agensi/`) | Requires | Engine |
|---|---|---|
| 2 files, ~35 KB, no binaries | `python3` + `typst` (one static binary, ~30 MB) | Typst |

That changes the prerequisites the page must state, and the price: **$5–7**, not
$9. The repository edition (Node + Chromium, KaTeX, 14 tests) stays on GitHub and
is what the screenshots come from — but do not promise a browser-free install on
a listing that ships `agensi/`, and do not promise the reverse either.

Reproduce the listing screenshots from the single-file edition first if you want
the page to be strictly honest: `python agensi/md2pdf.py examples/zh-report.md out.pdf`.

**Screenshots, in this order** (all already in `docs/img/`):

1. `zh-report-page1.png` — the first thing a buyer must see: a real Chinese A4 page
   with a title block, KaTeX formulas and a table.
2. `zh-report-page2.png` — code block, display equation, numbered conclusions.
3. `en-note-page1.png` — proves the English typography is not an afterthought.

---

## Title

**md-to-pdf — offline Markdown → A4 PDF with real math (Claude Code / Codex skill)**

## Short line (one sentence, for the card)

Turn a Markdown file — Chinese or English, LaTeX and all — into a print-quality A4
PDF with page numbers, fully offline. No Word, no LibreOffice, no TeX.

## Long description

Most "Markdown to PDF" advice ends in one of two places: install 4 GB of TeX, or
open Word and fight the styles. This skill does neither. It renders with
`markdown-it`, pre-renders formulas with KaTeX, prints through the Edge or Chrome
you already have, and stamps page numbers with PyMuPDF — offline, deterministic,
one command.

**What makes it different**

- **Bilingual by detection.** Chinese gets 宋体 with a 2em first-line indent;
  English gets a Times-family serif, no indent, and automatic hyphenation. Same
  command, no flags. Override with `MD2PDF_LANG=zh|en`.
- **Formulas are vector typesetting**, not screenshots — `\( … \)` inline and
  `\[ … \]` display, at web-quality spacing.
- **Page numbers actually stamped**, because Chromium has no `@page` margin boxes.
- **Works inside your agent**: installers drop it into `~/.claude/skills` and
  `~/.agents/skills`, plus an `AGENTS.md`-style manifest for Codex.
- **A `--doctor` self-check** that tells you in one table whether node, the
  bundled KaTeX fonts, a browser, Python/PyMuPDF and CJK fonts are in place.
- **14 regression tests** cover page geometry, embedded fonts, page numbers and
  the two CLI bugs that used to produce silently empty output.
- **No `npm install`** — `node_modules` ships in the box.

**Built while writing real reports.** The 32 entry pitfall list in
`references/gotchas.md` is not folklore: every item was measured, including why
math has to be extracted before Markdown parsing, why fenced code blocks get
shredded by the Chinese line-oriented layout, and why Chromium resolves a relative
output path against *its own* working directory (which is why the old version
printed "PDF -> out.pdf" and wrote nothing).

## What you need (say this plainly — it prevents refunds)

| Need | Check |
|---|---|
| Node.js ≥ 18 | `node -v` |
| Microsoft Edge or Google Chrome | one of them is on every Windows/macOS box |
| Python 3 + `pymupdf` | `python -m pip install -r scripts/requirements.txt` |
| A CJK font, if the document is Chinese | Windows: built in. Linux: `fonts-noto-cjk` |

No Chromium at all (Android container, locked-down server)? There is a measured
Typst fallback that needs neither Node nor a browser.

## FAQ

**Does it work on macOS/Linux?** Yes — `install.sh` and `scripts/md2pdf.sh`. The
`.ps1` and `.bat` helpers are Windows conveniences.

**`$x$` doesn't render — why?** `$…$` is ambiguous with currency. This build reads
`\( … \)` and `\[ … \]`, and prints a warning naming any `$…$` span it sees instead
of silently emitting it.

**Can I use it commercially?** Yes. The licence is AGPL-3.0-or-later (inherited
from PyMuPDF, the page-number dependency): distribute a *modified* version and the
source stays open; use it, or ship the unmodified skill inside your own product,
freely.

**Is the code on GitHub?** Yes — the repository is the source of truth, and it is
free there. This listing buys you the packaged version, the screenshots, the
installers and the documented traps, and it funds the maintenance. If that is not
worth $9 to you, clone it — genuinely no hard feelings.

## Refund-proofing note (for the seller)

Agensi's money-back guarantee is "if a skill does not do what its page promises".
So the page must promise exactly this: A4, bilingual, formulas, page numbers, the
four prerequisites above. Do not promise Word-editable output, DOCX, or "no
dependencies".
