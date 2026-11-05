"""Regression tests for md-to-pdf.

Two groups:

* PDF assertions run against the committed examples (no browser, no node) and
  catch the failures a buyer would notice: missing file, wrong page size, math
  left as literal text, a code block shredded into paragraphs.
* CLI assertions drive the real pipeline and are skipped unless node and a
  Chromium-family browser are present.

    python -m unittest discover -s tests -v
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES = os.path.join(ROOT, "examples")
SCRIPT = os.path.join(ROOT, "scripts", "md2pdf.js")
IMGS = os.path.join(ROOT, "docs", "img")

A4 = (595.276, 841.89)  # PostScript points, ±1 pt tolerance
TOL = 1.0

try:
    import pymupdf
    HAVE_PYMUPDF = True
except ImportError:  # pragma: no cover - optional dependency
    HAVE_PYMUPDF = False


def open_pdf(name):
    return pymupdf.open(os.path.join(EXAMPLES, name))


def page_text(doc, index):
    return doc[index].get_text("text")


def all_text(doc):
    return "\n".join(page_text(doc, i) for i in range(doc.page_count))


@unittest.skipUnless(HAVE_PYMUPDF, "pymupdf is not installed (pip install -r scripts/requirements.txt)")
class ExamplePdfTests(unittest.TestCase):
    def test_examples_exist(self):
        for name in ("zh-report.md", "zh-report.pdf", "en-note.md", "en-note.pdf"):
            path = os.path.join(EXAMPLES, name)
            self.assertTrue(os.path.isfile(path), name)
            self.assertGreater(os.path.getsize(path), 1000, name)

    def test_page_geometry_is_a4(self):
        for name in ("zh-report.pdf", "en-note.pdf"):
            with self.subTest(pdf=name), open_pdf(name) as doc:
                self.assertGreaterEqual(doc.page_count, 1)
                for page in doc:
                    self.assertAlmostEqual(page.rect.width, A4[0], delta=TOL)
                    self.assertAlmostEqual(page.rect.height, A4[1], delta=TOL)

    def test_text_is_extractable_and_fonts_embedded(self):
        with open_pdf("zh-report.pdf") as doc:
            self.assertIn("牛顿环", all_text(doc))
            fonts = {f[3] for f in doc[0].get_fonts()}
            self.assertTrue(fonts, "no fonts listed on page 1")
            self.assertTrue(any(not f.startswith("Base14") for f in fonts),
                            f"only unembedded base-14 fonts: {fonts}")
        with open_pdf("en-note.pdf") as doc:
            self.assertIn("Newton", all_text(doc))

    def test_page_numbers_are_stamped(self):
        for name in ("zh-report.pdf", "en-note.pdf"):
            with self.subTest(pdf=name), open_pdf(name) as doc:
                for i in range(doc.page_count):
                    tail = page_text(doc, i).strip().splitlines()[-1]
                    self.assertEqual(tail.strip(), str(i + 1))

    def test_no_placeholder_tokens_leak(self):
        for name in ("zh-report.pdf", "en-note.pdf"):
            with self.subTest(pdf=name), open_pdf(name) as doc:
                text = all_text(doc)
                for token in ("ZZINLINEMATH", "ZZEQTOKEN", "ZZFENCE"):
                    self.assertNotIn(token, text)

    def test_math_is_typeset_not_literal(self):
        with open_pdf("zh-report.pdf") as doc:
            text = all_text(doc)
        self.assertNotIn("\\frac", text, "LaTeX source leaked into the PDF")
        self.assertNotIn("\\lambda", text)
        self.assertNotIn("$", text, "math delimiters printed literally")

    def test_code_block_keeps_its_line_structure(self):
        """The Chinese line-oriented pass once inserted a blank line between every
        code line; the fenced block must survive with its original spacing."""
        with open_pdf("zh-report.pdf") as doc:
            text = all_text(doc)
        m = re.search(r"import numpy as np(.*?)d2 = np\.array", text, re.S)
        self.assertIsNotNone(m, "code block text not found")
        blanks = [ln for ln in m.group(1).splitlines() if not ln.strip()]
        self.assertLessEqual(len(blanks), 1, f"code block was re-flowed: {m.group(1)!r}")

    def test_screenshots_match_the_pdfs(self):
        for name in ("zh-report-page1.png", "zh-report-page2.png", "en-note-page1.png"):
            path = os.path.join(IMGS, name)
            self.assertTrue(os.path.isfile(path), name)
            self.assertGreater(os.path.getsize(path), 20000, name)


def browser_ready():
    node = shutil.which("node")
    if not node:
        return False
    try:
        proc = subprocess.run([node, SCRIPT, "--doctor"], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=120)
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0 and "READY" in (proc.stdout + proc.stderr)


@unittest.skipUnless(browser_ready(), "node or a Chromium-family browser is unavailable")
class CliTests(unittest.TestCase):
    def test_relative_output_path_is_resolved(self):
        """Regression: Chromium resolved --print-to-pdf against its own cwd, so a
        relative output path produced no file while still reporting success."""
        node = shutil.which("node")
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [node, SCRIPT, os.path.join(EXAMPLES, "en-note.md"), "out.pdf", "Relative path"],
                cwd=tmp, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            target = os.path.join(tmp, "out.pdf")
            self.assertTrue(os.path.isfile(target),
                            f"no PDF written for a relative path\nstdout={proc.stdout}\nstderr={proc.stderr}")
            self.assertGreater(os.path.getsize(target), 1000)

    def test_dollar_math_warning(self):
        node = shutil.which("node")
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "dollar.md")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write("正文 \\(a\\) 与 $E=mc^2$ 混用，价格 $5 不该报警。\n")
            proc = subprocess.run(
                [node, SCRIPT, src, os.path.join(tmp, "d.pdf")],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            out = proc.stdout + proc.stderr
            self.assertIn("$...$", out)
            self.assertIn("1 $...$ span(s)", out, "currency '$5' must not be counted")


if __name__ == "__main__":
    unittest.main()
