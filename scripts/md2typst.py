#!/usr/bin/env python3
"""md2typst.py — Markdown → Typst source, for reports with no math (Typst route).

`md2pdf.js` needs a Chromium-family browser. On hosts without one, `SKILL.md`
says to drive `scripts/typst-template.typ` by hand — and every hand-rolled
conversion hits the same set of *non-formula* traps, because they are width and
inline-markup bugs, not math bugs. This script encodes the fixes:

  1. **template body leak** — cut the template on its exact body marker. A
     hand-rolled `split("# ==== 正文 ====")` looks right and silently matches
     nothing (Typst comments start with `//`, not `#`), so the demo headings
     ("报告标题 / 1. 一节 / 2. 公式") ship into the deliverable. If the marker is
     absent the script cuts at the first `#heading(level: 1)` instead (with a
     warning), and stops with exit 2 only when there is nothing safe to cut.
  2. **full-width digits** — `２ ０ ２ ５` are East-Asian wide characters, so
     Typst gives each one its own word slot and the digits come out with gaps
     ("２ ０ ２ ５ 年"). Normalise full-width digits/latin to ASCII; the spacing
     disappears and the glyphs match 宋体's proportional digits.
  3. **CJK title breaks mid-word** — an h1 long enough to wrap breaks between any
     two CJK characters ("……生产关 / 系……"). Insert `#linebreak()` at a `的`
     boundary near the midpoint so the break lands where a human would put it.
  4. **first-line indent after a heading** — `#h(2em)` per paragraph (gotcha 21)
     only works because Typst used to ignore `first-line-indent` on the paragraph
     after a heading. Typst ≥ 0.13 has
     `first-line-indent: (amount: 2em, all: true)`, which is one line in the
     template and cannot be forgotten in the body. Used by default; `--indent h`
     restores the `#h(2em)` prefixes for older Typst.
  5. **bold-only line** — `**（一）小标题**` on its own line is a sub-heading in
     Chinese reports, not emphasis: render it as a sticky 黑体 block so it never
     sits alone at the bottom of a page and cannot be confused with body text.
  6. **code-mode escapes** — `#`, `$`, `*`, `_`, `@`, `[`, `]`, `<`, `>`, `` ` ``
     are markup in Typst; escape them. Section comments in emitted source must
     use `//` (a `#` comment is a compile error, not a comment).

Deliberately out of scope: math (`\\( \\)` / `\\[ \\]` — the CSS route already
owns it, and the Typst template passes `$…$` through), tables, footnotes,
reference-style links. `--check` lists what was dropped so nothing disappears
silently.

Usage
-----
    python3 scripts/md2typst.py in.md out.typ [options]
    python3 scripts/md2typst.py in.md out.typ --title "报告标题"
    typst compile out.typ out.pdf        # then verify with scripts/pdf_pages.py

Options
-------
    --template PATH   template to reuse (default: scripts/typst-template.typ)
    --title TEXT      override the document title (default: first h1)
    --indent {all,h}  all = first-line-indent all:true (Typst ≥0.13, default)
                      h   = per-paragraph #h(2em) (older Typst)
    --no-title-break  never insert #linebreak() into the h1
    --keep-fullwidth  keep ０-９ / Ａ-Ｚ / ＋ ％ as typed
    --check           print a report of unsupported constructs, exit 3 if any
    -q, --quiet       no warnings on stderr
"""

import argparse
import os
import re
import sys

BODY_MARKER_RE = re.compile(r"^//\s*=+\s*正文.*$", re.M)
FALLBACK_MARKER_RE = re.compile(r"^#heading\(level:\s*1\)\[", re.M)
TITLE_RE = re.compile(r'#set document\(title:\s*"[^"]*"\)')
INDENT_RE = re.compile(r"first-line-indent:\s*0em,[^\n]*")
INDENT_ALL_RE = re.compile(r"first-line-indent:\s*\(amount:\s*2em,\s*all:\s*true\),")

SPECIAL = set("\\#$*_`<>@[]")
WIDE_DIGITS = {chr(0xFF10 + i): str(i) for i in range(10)}
WIDE_LATIN = {chr(0xFF21 + i): chr(ord("A") + i) for i in range(26)}
WIDE_LATIN.update({chr(0xFF41 + i): chr(ord("a") + i) for i in range(26)})
WIDE_SIGNS = {"＋": "+", "％": "%", "．": "."}

SIGNATURE_RE = re.compile(r"^(专业班级|班级|姓名|学号|学院|指导教师)[:：]")
FENCE_RE = re.compile(r"^(```+|~~~+)(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
OL_RE = re.compile(r"^\s*(\d+)[.)]\s+(.*)$")
UL_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
QUOTE_RE = re.compile(r"^>\s?(.*)$")

CJK_RE = re.compile(r"[\u3400-\u9fff\u3000-\u303f\uff00-\uffef]")


# --------------------------------------------------------------------------- #
# text helpers


def normalise_wide(text):
    """Full-width digits/latin → ASCII (trap 2)."""
    out = []
    for ch in text:
        out.append(WIDE_DIGITS.get(ch) or WIDE_LATIN.get(ch) or WIDE_SIGNS.get(ch) or ch)
    return "".join(out)


def escape(text):
    """Escape Typst markup (trap 6)."""
    return "".join("\\" + ch if ch in SPECIAL else ch for ch in text)


def inline(text):
    """`**bold**` → `*bold*`, everything else escaped."""
    parts = text.split("**")
    out = []
    for i, part in enumerate(parts):
        if i % 2 and part:
            out.append("*" + escape(part) + "*")
        else:
            out.append(escape(part))
    return "".join(out)


def split_title(title, min_len=23, keep=7):
    """Return (line1, line2) for a long CJK title, or None (trap 3)."""
    if len(CJK_RE.findall(title)) < min_len:
        return None
    mid = len(title) / 2
    cuts = [i + 1 for i, ch in enumerate(title)
            if ch == "的" and 6 <= i <= len(title) - keep]
    if not cuts:
        return None
    cut = min(cuts, key=lambda i: abs(i - mid))
    return title[:cut], title[cut:]


# --------------------------------------------------------------------------- #
# template


def template_head(template_path, title, indent_mode, warn):
    """Everything before the template's body marker (trap 1)."""
    with open(template_path, encoding="utf-8") as fh:
        tpl = fh.read()

    match = BODY_MARKER_RE.search(tpl)
    if match:
        head = tpl[: match.start()].rstrip() + "\n"
    else:
        fallback = FALLBACK_MARKER_RE.search(tpl)
        if not fallback:
            sys.exit(
                "md2typst: no body marker in %s.\n"
                "  expected a line like `// ============ 正文 ============`\n"
                "  (Typst comments are `//`; a `# ====` marker never matches)" % template_path
            )
        warn("template has no body marker; cut before the first heading instead")
        head = tpl[: fallback.start()].rstrip() + "\n"

    if title and TITLE_RE.search(head):
        head = TITLE_RE.sub('#set document(title: "%s")' % escape(title), head, count=1)
    elif title:
        head += '\n#set document(title: "%s")\n' % escape(title)

    if indent_mode == "all":
        if INDENT_RE.search(head):
            head = INDENT_RE.sub("first-line-indent: (amount: 2em, all: true),", head, count=1)
        elif not INDENT_ALL_RE.search(head):
            warn("template has neither `first-line-indent: 0em,` nor all:true; indent left as-is")
    return head


# --------------------------------------------------------------------------- #
# body


def convert_body(md, indent_mode, title_break, dropped):
    blocks = []
    lines = md.splitlines()
    i = 0
    first_h1 = None

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        if not line:
            i += 1
            continue

        fence = FENCE_RE.match(line)
        if fence:
            marker, lang = fence.group(1), fence.group(2).strip()
            body = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(marker):
                body.append(lines[i])
                i += 1
            i += 1
            text = "\n".join(body)
            blocks.append(
                "#block(above: 0.6em, below: 0.6em, breakable: false)"
                '[#raw(block: true, lang: "%s", "%s")]'
                % (escape(lang), text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n"))
            )
            continue

        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2).strip()
            if level == 1 and first_h1 is None:
                first_h1 = text
            split = split_title(text) if (level == 1 and title_break) else None
            if split:
                payload = "%s#linebreak()%s" % (escape(split[0]), escape(split[1]))
            else:
                payload = inline(text)
            blocks.append("#heading(level: %d)[%s]" % (min(level, 3), payload))
            i += 1
            continue

        quote = QUOTE_RE.match(line)
        if quote:
            text = quote.group(1)
            blocks.append("#quote(block: true)[%s]" % inline(text))
            i += 1
            continue

        ordered = OL_RE.match(line)
        unordered = UL_RE.match(line)
        if ordered or unordered:
            items = []
            while i < len(lines):
                cur = lines[i].strip()
                m_ol, m_ul = OL_RE.match(cur), UL_RE.match(cur)
                if m_ol or m_ul:
                    items.append(inline((m_ol or m_ul).group(2) if m_ol else m_ul.group(1)))
                    i += 1
                elif cur and not HEADING_RE.match(cur) and not FENCE_RE.match(cur):
                    if items:
                        items[-1] += " " + inline(cur)   # lazy continuation line
                    i += 1
                else:
                    break
            bullet = "+ " if ordered else "- "
            blocks.append("\n".join(bullet + it for it in items))
            continue

        bold_only = line.startswith("**") and line.endswith("**") and line.count("**") == 2
        if bold_only:
            blocks.append(
                '#block(above: 0.95em, below: 0.25em, sticky: true)['
                '#text(font: ("Noto Sans CJK SC",), weight: "bold", size: 12pt)[%s]]'
                % escape(line[2:-2])
            )
            i += 1
            continue

        if SIGNATURE_RE.match(line):
            blocks.append(
                "#{ set par(first-line-indent: 0em); set text(size: 10.5pt);"
                " align(center)[%s] }" % inline(line)
            )
            i += 1
            continue

        if line.startswith("|"):
            dropped.append("table row: " + line[:40])
        elif re.search(r"\[\^[^\]]+\]", line):
            dropped.append("footnote reference: " + line[:40])

        if indent_mode == "h":
            blocks.append("#h(2em)" + inline(line))
        else:
            blocks.append(inline(line))
        i += 1

    return blocks, first_h1


# --------------------------------------------------------------------------- #
# main


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    default_template = os.path.join(here, "typst-template.typ")

    ap = argparse.ArgumentParser(
        prog="md2typst.py",
        description="Markdown → Typst source (no Chromium; non-math layout traps handled).",
    )
    ap.add_argument("input", help="input .md")
    ap.add_argument("output", help="output .typ")
    ap.add_argument("--template", default=default_template)
    ap.add_argument("--title", default=None)
    ap.add_argument("--indent", choices=("all", "h"), default="all")
    ap.add_argument("--no-title-break", action="store_true")
    ap.add_argument("--keep-fullwidth", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args(argv)

    def warn(msg):
        if not args.quiet:
            print("md2typst: " + msg, file=sys.stderr)

    with open(args.input, encoding="utf-8") as fh:
        md = fh.read()
    if not args.keep_fullwidth:
        md = normalise_wide(md)

    dropped = []
    blocks, first_h1 = convert_body(md, args.indent, not args.no_title_break, dropped)
    if not blocks:
        sys.exit("md2typst: nothing to convert in %s" % args.input)

    title = args.title or first_h1 or os.path.splitext(os.path.basename(args.output))[0]
    if not args.keep_fullwidth:
        title = normalise_wide(title)

    head = template_head(args.template, title, args.indent, warn)
    out = head + "\n// ============ 正文 ============\n\n" + "\n\n".join(blocks) + "\n"

    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(out)

    if not args.quiet:
        print("wrote %s  (%d blocks, title: %s)" % (args.output, len(blocks), title))
    if args.check and dropped:
        print("dropped (unsupported):")
        for item in dropped:
            print("  - " + item)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
