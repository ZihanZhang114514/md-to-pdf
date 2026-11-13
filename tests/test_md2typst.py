"""Regression tests for scripts/md2typst.py (the no-Chromium Typst route).

These lock the six *non-formula* layout traps documented in the script header:
they are width/inline-markup bugs, so they only show up in the rendered PDF —
which makes them exactly the kind of thing that silently comes back.

Group 1 (always runs): pure text assertions on the generated Typst source.
Group 2 (opt-in): compiles the .typ with a real `typst` binary and inspects the
PDF. Skipped unless `typst` is on PATH or $MD2PDF_TYPST points at it.

    python -m unittest discover -s tests -v
"""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "md2typst.py")
TEMPLATE = os.path.join(ROOT, "scripts", "typst-template.typ")


def load_module():
    spec = importlib.util.spec_from_file_location("md2typst", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


md2typst = load_module()

SAMPLE = """# 关于某个热点问题的某个马原理理论解读

专业班级：＿＿＿＿＿　姓名：＿＿＿＿＿

## 一、介绍热点话题

２０２５年发生了很多事情，２．５亿人次参与，Ａ股上涨。

## 二、分析

**（一）第一个小标题**

正文段落，带 #井号 和 $美元 和 *星号。
"""


def convert(md_text, *extra, output="out.typ"):
    """Run the converter in-process and return the generated Typst source."""
    tmp = tempfile.mkdtemp()
    try:
        src = os.path.join(tmp, "in.md")
        dst = os.path.join(tmp, output)
        with open(src, "w", encoding="utf-8") as fh:
            fh.write(md_text)
        rc = md2typst.main([src, dst, "-q", *extra])
        with open(dst, encoding="utf-8") as fh:
            return fh.read(), rc
    finally:
        shutil.rmtree(tmp)


class TemplateCutTests(unittest.TestCase):
    """Trap 1: the template's demo body must never reach the deliverable."""

    def test_demo_body_is_stripped(self):
        out, _ = convert(SAMPLE)
        for leak in ("报告标题", "1. 一节", "2. 公式", "3. 列表"):
            self.assertNotIn(leak, out, "template demo body leaked: %r" % leak)

    def test_marker_comment_uses_slashes(self):
        # A `# ====` marker would be a code-mode comment and a compile error.
        out, _ = convert(SAMPLE)
        self.assertIn("// ============ 正文 ============", out)
        self.assertNotIn("\n# ============", out)

    def test_missing_marker_falls_back_to_first_heading(self):
        tmp = tempfile.mkdtemp()
        try:
            tpl = os.path.join(tmp, "t.typ")
            with open(tpl, "w", encoding="utf-8") as fh:
                fh.write("#set text(size: 12pt)\n\n#heading(level: 1)[demo]\n")
            out, _ = convert(SAMPLE, "--template", tpl)
            self.assertNotIn("demo", out)          # cut before it, not shipped
            self.assertIn("#heading(level: 2)[一、介绍热点话题]", out)
        finally:
            shutil.rmtree(tmp)

    def test_no_marker_and_no_heading_fails_loudly(self):
        tmp = tempfile.mkdtemp()
        try:
            tpl = os.path.join(tmp, "t.typ")
            with open(tpl, "w", encoding="utf-8") as fh:
                fh.write("#set text(size: 12pt)\n")
            with self.assertRaises(SystemExit) as ctx:
                convert(SAMPLE, "--template", tpl)
            self.assertNotEqual(ctx.exception.code, 0)
        finally:
            shutil.rmtree(tmp)


class FullWidthTests(unittest.TestCase):
    """Trap 2: ０１２ are East-Asian wide and get word slots of their own."""

    def test_digits_and_signs_become_ascii(self):
        out, _ = convert(SAMPLE)
        for wide in ("０", "１", "２", "．", "％", "Ａ"):
            self.assertNotIn(wide, out)
        self.assertIn("2025年", out)
        self.assertIn("2.5亿", out)
        self.assertIn("A股", out)

    def test_keep_fullwidth_switch(self):
        out, _ = convert(SAMPLE, "--keep-fullwidth")
        self.assertIn("２０２５年", out)


class TitleBreakTests(unittest.TestCase):
    """Trap 3: a long CJK h1 must not break mid-word."""

    def test_long_title_gets_linebreak(self):
        # 20 pt 黑体在 A4 正文宽度上约 22 个汉字一行，超过就会在字与字之间断开
        long_title = "# 人工智能时代普通劳动者就业结构变化趋势的矛盾分析及其应对"
        out, _ = convert(long_title + "\n\n## 一节\n\n正文。\n")
        self.assertRegex(out, r"#heading\(level: 1\)\[[^\]]*#linebreak\(\)")

    def test_short_title_left_alone(self):
        md = "# 短标题\n\n## 一节\n\n正文。\n"
        out, _ = convert(md)
        self.assertNotIn("#linebreak()", out)

    def test_switch_off(self):
        out, _ = convert(SAMPLE, "--no-title-break")
        self.assertNotIn("#linebreak()", out)

    def test_break_lands_after_de(self):
        line1, line2 = md2typst.split_title("人形机器人“量产元年”热点问题的生产力与生产关系辩证运动解读")
        self.assertTrue(line1.endswith("的"))
        self.assertGreaterEqual(len(line1), 8)
        self.assertGreaterEqual(len(line2), 7)


class InlineTests(unittest.TestCase):
    """Trap 6: markup characters must be escaped; bold handled separately."""

    def test_specials_escaped(self):
        out, _ = convert(SAMPLE)
        self.assertIn("\\#井号", out)
        self.assertIn("\\$美元", out)
        self.assertIn("\\*星号", out)

    def test_bold_inline_becomes_strong(self):
        out, _ = convert("段落里 **粗体** 收尾。\n")
        self.assertIn("*粗体*", out)
        self.assertNotIn("**粗体**", out)

    def test_bold_only_line_becomes_subheading(self):
        """Trap 5: `**（一）小标题**` is a sub-heading, not emphasis."""
        out, _ = convert(SAMPLE)
        self.assertIn("sticky: true", out)
        self.assertIn("#text(font: (\"Noto Sans CJK SC\",), weight: \"bold\", size: 12pt)", out)

    def test_signature_line_is_centred(self):
        out, _ = convert(SAMPLE)
        self.assertIn("align(center)", out)


class IndentTests(unittest.TestCase):
    """Trap 4: indent after headings, one line in the template, not per block."""

    def test_default_uses_all_true(self):
        out, _ = convert(SAMPLE)
        self.assertIn("first-line-indent: (amount: 2em, all: true),", out)
        body = out.split("// ============ 正文 ============")[1]
        self.assertNotIn("#h(2em)", body)

    def test_legacy_h_mode(self):
        out, _ = convert(SAMPLE, "--indent", "h")
        self.assertIn("#h(2em)", out)


class ListTests(unittest.TestCase):
    def test_bullets_and_numbers(self):
        md = "## 一节\n\n- 第一项\n- 第二项\n\n1. 编号一\n2. 编号二\n"
        out, _ = convert(md)
        self.assertIn("- 第一项", out)
        self.assertIn("+ 编号一", out)


class CheckTests(unittest.TestCase):
    def test_check_reports_tables(self):
        md = "## 一节\n\n| a | b |\n| - | - |\n"
        _, rc = convert(md, "--check")
        self.assertEqual(rc, 3)


def find_typst():
    env = os.environ.get("MD2PDF_TYPST")
    if env and os.path.isfile(env) and os.access(env, os.X_OK):
        return env
    return shutil.which("typst")


@unittest.skipUnless(find_typst(), "no typst binary (set MD2PDF_TYPST)")
class CompileTests(unittest.TestCase):
    """End-to-end: the generated source must compile and keep the demo out."""

    def test_compiles_and_drops_demo(self):
        typst = find_typst()
        tmp = tempfile.mkdtemp()
        try:
            src = os.path.join(tmp, "in.md")
            typ = os.path.join(tmp, "out.typ")
            pdf = os.path.join(tmp, "out.pdf")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(SAMPLE)
            md2typst.main([src, typ, "-q"])
            subprocess.run([typst, "compile", typ, pdf], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.assertTrue(os.path.getsize(pdf) > 1000)
            try:
                import pymupdf
            except ImportError:  # pragma: no cover - optional dependency
                return
            doc = pymupdf.open(pdf)
            text = "".join(page.get_text() for page in doc)
            self.assertNotIn("报告标题", text)
            self.assertIn("2025", text)      # normalised digits survived
            self.assertGreaterEqual(doc.page_count, 1)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
