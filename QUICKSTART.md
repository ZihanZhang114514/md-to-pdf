# Quick start (5 minutes, no GUI)

You bought / cloned a skill that turns a Markdown file into a **print-quality A4 PDF** — Chinese or English, LaTeX formulas included — with **no** Word, no LibreOffice, no TeX, no internet.

```
markdown → HTML (KaTeX formulas pre-rendered) → headless Chromium print → page numbers
```

## 1. Install

**Claude Code / Codex (macOS, Linux):**

```bash
./install.sh                    # symlinks into ~/.claude/skills and ~/.agents/skills
./install.sh --copy             # or copy, if you plan to move the folder later
```

**Windows (PowerShell):**

```powershell
.\install.ps1                   # copies into %USERPROFILE%\.claude\skills and .agents\skills
```

Restart the agent afterwards. Claude Code: `/md-to-pdf`. Codex: `$md-to-pdf`.

## 2. Check your machine

```bash
node scripts/md2pdf.js --doctor
```

```
  md-to-pdf doctor
  --------------------------------------------------------
  + node              ok         v22.11.0 (need >= 18)
  + katex fonts       ok         vendored
  + browser           ok         /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
  - python + pymupdf  ok         python3 / pymupdf 1.28.2
  - typst (fallback)  absent     optional: needed only when there is no browser
  - CJK fonts         ok         92 Chinese faces
  --------------------------------------------------------
  READY    node scripts/md2pdf.js in.md out.pdf
```

Only the three `+` lines block you. **No browser?** `typst compile scripts/typst-template.typ out.pdf` needs neither Node nor Chromium (templates for Chinese and English are included).

## 3. Convert

```bash
node scripts/md2pdf.js report.md report.pdf "Report title" "Subtitle"
# or, with page numbers and path handling:
./scripts/md2pdf.sh report.md report.pdf "Report title"
```

Or just ask your agent: *"convert report.md into an A4 PDF"* — it reads `SKILL.md` and does the rest.

Windows: drag any `.md` onto `scripts\Drop-MD-Here.bat`, the PDF appears next to it.

## What you get

- **Chinese typography**: 宋体/黑体 (or Songti/PingFang on macOS, Noto CJK on Linux), 1.72 line height, 2-character first-line indent, justified.
- **English typography**: Times-family serif, no first-line indent, automatic hyphenation — detected from the text, no flags.
- **Real vector formulas** from `\( … \)` / `\[ … \]`, typeset by KaTeX with the fonts bundled in this repo.
- **A4, page numbers, headings not orphaned at page bottoms.**
- **Fully offline, deterministic**: same `.md` in, same `.pdf` out.

## Limits (please read)

| Works | Doesn't |
|---|---|
| `.md` → PDF, single file | edit the PDF afterwards (ask for a `.docx` instead) |
| Headings, lists, tables, code blocks, bold | table of contents fields, cross references, mail merge |
| Chinese + English, mixed is fine | other languages' line-breaking rules |
| Page numbers (needs Python + pymupdf) | page numbers without Python — the PDF is still built, just unnumbered |

## Troubleshooting

| Message | Fix |
|---|---|
| `No Chromium-based browser found` | install Chrome/Edge, or `MD2PDF_EDGE=/path/to/chrome node scripts/md2pdf.js …`, or use the Typst templates |
| `node not found` | install Node.js ≥ 18 |
| `page numbers were not stamped` | `python3 -m pip install -r scripts/requirements.txt` |
| Chinese shows as boxes | install a CJK font (`fonts-noto-cjk` on Debian/Ubuntu; macOS/Windows ship one) |
| English paragraphs look shredded | you are on an old copy — `MD2PDF_LINE_ORIENTED=0` also fixes it |
| `###` headings collapsed into `##` | same, older copy; update the skill |

More: `SKILL.md` (the agent's manual) and `README.md`.

## License

MIT — see `LICENSE`. Use it commercially, modify it, ship it inside your own product.
