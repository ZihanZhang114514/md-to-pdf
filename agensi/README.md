# Single-file edition (marketplace)

This folder is the *other* shape of the same skill, for marketplaces that deliver
skills as text over an MCP connection and run them from a temporary file.

| | This folder | Repository root |
|---|---|---|
| Files | **2** (`SKILL.md`, `md2pdf.py`) | 369 |
| Text size | ~35 KB | 5.8 MB |
| External tools | `typst` (one static binary) | Node 18+, Edge/Chrome, Python+PyMuPDF |
| Binaries shipped | none | vendored `node_modules`, 120 font files |
| Engine | Typst | KaTeX + headless Chromium |
| Math quality | Typst native (LaTeX-class) | KaTeX |
| Math delimiters | `\( … \)`, `\[ … \]` | same |

Why: a marketplace listing must stay under 200 text files / 6M characters, and
binaries (fonts, PDFs, images) are listed but never delivered. The root pipeline
needs 120 font binaries and a 369-file tree, so it cannot be delivered that way.
This edition trades the browser for a single Typesetting tool that bundles nothing.

```bash
python md2pdf.py --doctor
python md2pdf.py ../../examples/zh-report.md /tmp/out.pdf "牛顿环法测量平凸透镜曲率半径" "大学物理实验报告"
```

It renders the same `examples/` documents to A4 with the same geometry and page
numbers; the typography differs (Typst sets tables and code blocks itself, and
hyphenates through its own dictionary). Both outputs are checked by
`tests/test_agensi_single_file.py`.

Constraints this folder must keep satisfying — asserted by that test:

- every file here is text (no `.ttf`, `.pdf`, `.png`, `.exe`);
- ≤ 200 files and ≤ 6,000,000 characters in total;
- `SKILL.md` frontmatter uses only Agent Skills keys and carries `compatibility`;
- the script imports nothing outside the Python standard library;
- it works when copied alone into a temporary directory (that is how it runs).
