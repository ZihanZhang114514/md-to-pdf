"""Tests for the single-file marketplace edition (agensi/).

Two kinds of coverage:

* the delivery contract of the marketplace — text files only, 200 files / 6M
  characters, spec-legal frontmatter, standard library only, and it has to work
  when the script is copied alone into an empty temporary directory;
* the rendering behaviour of `md2pdf.py` against the shared examples.

The rendering tests need the `typst` binary and are skipped without it.

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
AGENSI = os.path.join(ROOT, "agensi")
SCRIPT = os.path.join(AGENSI, "md2pdf.py")
SKILL = os.path.join(AGENSI, "SKILL.md")
EXAMPLES = os.path.join(ROOT, "examples")

MAX_FILES = 200
MAX_CHARS = 6_000_000
BINARY_EXT = {".ttf", ".otf", ".woff", ".woff2", ".pdf", ".png", ".jpg",
              ".jpeg", ".zip", ".exe", ".bin", ".so", ".dylib", ".pyc"}

sys.path.insert(0, AGENSI)
try:
    import md2pdf  # noqa: E402
    HAVE_MODULE = True
except Exception:  # pragma: no cover
    HAVE_MODULE = False

try:
    import pymupdf  # noqa: E402
    HAVE_PYMUPDF = True
except ImportError:  # pragma: no cover
    HAVE_PYMUPDF = False


def text_files():
    for dirpath, dirnames, filenames in os.walk(AGENSI):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            yield os.path.join(dirpath, name)


class DeliveryContractTests(unittest.TestCase):
    """What the marketplace promises the buyer must still be true."""

    def test_text_only(self):
        for path in text_files():
            ext = os.path.splitext(path)[1].lower()
            self.assertNotIn(ext, BINARY_EXT, f"binary in the listing: {path}")
            with open(path, "rb") as fh:
                raw = fh.read()
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), f"BOM in {path}")
            raw.decode("utf-8")

    def test_size_limits(self):
        files = list(text_files())
        self.assertLessEqual(len(files), MAX_FILES, "200-file listing limit")
        total = sum(os.path.getsize(p) for p in files)
        self.assertLessEqual(total, MAX_CHARS, "6M-character listing limit")

    def test_no_third_party_imports(self):
        with open(SCRIPT, encoding="utf-8") as fh:
            source = fh.read()
        imports = set(re.findall(r"^\s*(?:import|from)\s+([a-zA-Z_][\w.]*)", source, re.M))
        allowed = {"os", "re", "sys", "shutil", "subprocess", "argparse", "time", "__future__"}
        self.assertTrue(imports <= allowed, f"non-stdlib imports: {imports - allowed}")

    def test_manifest_is_spec_legal(self):
        with open(SKILL, encoding="utf-8") as fh:
            text = fh.read()
        self.assertTrue(text.startswith("---"))
        end = text.find("\n---", 3)
        keys = {}
        for line in text[3:end].strip("\n").splitlines():
            if line.startswith(" "):
                continue
            k, _, v = line.partition(":")
            keys[k.strip()] = v.strip()
        allowed = {"name", "description", "license", "compatibility",
                   "metadata", "allowed-tools"}
        self.assertTrue(set(keys) <= allowed, set(keys) - allowed)
        self.assertLessEqual(len(keys["description"]), 1024)
        self.assertLessEqual(len(keys["compatibility"]), 500)
        self.assertIn("Requires:", text, "the platform surfaces a Requires: line")

    def test_runs_when_copied_alone(self):
        """The agent writes the script to a temp file and runs it there: no
        relative imports, no sibling assets, no cwd assumptions."""
        binary = md2pdf.typst_binary() if HAVE_MODULE else None
        if not binary:
            self.skipTest("typst not installed")
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copy2(SCRIPT, os.path.join(tmp, "md2pdf.py"))
            src = os.path.join(tmp, "doc.md")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write("## One\n\nText with \\(a^2+b^2\\) inline.\n\n"
                         "| a | b |\n|---|---|\n| 1 | 2 |\n")
            proc = subprocess.run(
                [sys.executable, os.path.join(tmp, "md2pdf.py"), "doc.md", "out.pdf", "T"],
                cwd=tmp, capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=300)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertTrue(os.path.isfile(os.path.join(tmp, "out.pdf")))


class TexConverterTests(unittest.TestCase):
    """The TeX→Typst mapping is the part most likely to be silently wrong."""

    def setUp(self):
        if not HAVE_MODULE:
            self.skipTest("md2pdf.py not importable")
        self.tex = md2pdf.TexConverter()

    def test_word_command_does_not_merge_with_digits(self):
        out = self.tex.convert(r"\times10^{-6}")
        self.assertNotIn("times10", out)
        self.assertIn("times", out)

    def test_unit_inside_mathrm(self):
        self.assertEqual(self.tex.convert(r"\mathrm{nm}"), 'upright("nm")')
        self.assertEqual(self.tex.convert(r"\mathrm{mm^2}"), 'upright("mm")^2')

    def test_fraction_variants(self):
        self.assertEqual(self.tex.convert(r"\frac{a}{b}"), "frac(a, b)")
        self.assertEqual(self.tex.convert(r"\dfrac{a}{b}"), "frac(a, b)")

    def test_unknown_commands_are_reported(self):
        self.tex.convert(r"\weirdcmd{x}")
        self.assertIn("\\weirdcmd", self.tex.unknown)

    def test_scripts_and_accent(self):
        self.assertEqual(self.tex.convert(r"d_{k+1}^{2}"), "d_(k+1)^(2)")
        self.assertEqual(self.tex.convert(r"\overline{ab}"), "overline(ab)")

    def test_text_runs_are_quoted(self):
        self.assertEqual(self.tex.convert(r"\text{if } x"), '"if " x')


@unittest.skipUnless(HAVE_MODULE, "md2pdf.py not importable")
class InlineTests(unittest.TestCase):
    def render(self, s):
        return md2pdf.Renderer("en", md2pdf.TexConverter()).inline(s)

    def test_markup_is_escaped(self):
        self.assertEqual(self.render("a_b*c"), "a\\_b\\*c")

    def test_emphasis_and_code(self):
        self.assertEqual(self.render("**bold**"), "*bold*")
        self.assertEqual(self.render("*ital*"), "_ital_")
        self.assertEqual(self.render("`x_y`"), "`x_y`")

    def test_links(self):
        self.assertEqual(self.render("[t](https://e.com)"), '#link("https://e.com")[t]')


@unittest.skipUnless(HAVE_PYMUPDF, "pymupdf not installed")
@unittest.skipUnless(HAVE_MODULE and md2pdf.typst_binary(), "typst not installed")
class RenderingTests(unittest.TestCase):
    def render(self, name, title, subtitle, lang=None):
        out = os.path.join(tempfile.mkdtemp(), "out.pdf")
        args = [os.path.join(EXAMPLES, name), out, title, subtitle]
        if lang:
            args += ["--lang", lang]
        code = md2pdf.main(args)
        self.assertEqual(code, 0)
        return out

    def test_chinese_example(self):
        import pymupdf
        pdf = self.render("zh-report.md", "牛顿环法测量平凸透镜曲率半径", "大学物理实验报告")
        with pymupdf.open(pdf) as doc:
            self.assertGreaterEqual(doc.page_count, 2)
            for page in doc:
                self.assertAlmostEqual(page.rect.width, 595.28, delta=1)
                self.assertAlmostEqual(page.rect.height, 841.89, delta=1)
            text = "\n".join(p.get_text("text") for p in doc)
            self.assertIn("牛顿环", text)
            self.assertIn("5.417", text)
            self.assertNotIn("\\frac", text)
            self.assertNotIn("upright(", text)
            self.assertNotIn("\x00", text)
            self.assertEqual(doc[-1].get_text("text").strip().splitlines()[-1].strip(),
                             str(doc.page_count))

    def test_english_example(self):
        import pymupdf
        pdf = self.render("en-note.md", "Newton's Rings", "Physics Lab 4.18")
        with pymupdf.open(pdf) as doc:
            text = "\n".join(p.get_text("text") for p in doc)
            self.assertIn("Newton", text)
            self.assertIn("589.3", text)
            self.assertNotIn("\\lambda", text)


if __name__ == "__main__":
    unittest.main()
