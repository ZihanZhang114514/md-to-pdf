---
name: md-to-pdf
description: Convert a Markdown file (Chinese or English, with LaTeX math) into a print-quality A4 PDF fully offline, without Microsoft Office, LibreOffice or a TeX distribution. Use when the user asks to turn a .md into a PDF, or when a report or note needs a PDF deliverable and an office suite cannot be assumed. Pipes markdown-it + KaTeX pre-rendered formulas into headless Chromium printing and stamps page numbers with PyMuPDF; also records the Word-COM, LibreOffice and XeLaTeX fallback routes and the layout pitfalls hit while building this pipeline.
whenToUse: A .md file must become a PDF deliverable (report, note, handout), especially Chinese text with math formulas, and you want a reproducible one-command conversion with no GUI app.
---

# Markdown → PDF（离线、中文、公式）

一条命令把 `.md` 变成可交付的 A4 PDF：**markdown-it 解析 → KaTeX 预渲染公式 → 无头 Edge 打印 → PyMuPDF 补页码**。全程离线，不依赖 Word / LibreOffice / TeX；公式是真正的矢量排版，不是截图。

本 skill 目录下的 `scripts/` 自带可直接运行的实现（含 `node_modules`，KaTeX 字体随包带上），照抄命令即可，不要重写一套。

## 适合 / 不适合

**适合**：中文实验报告、讲义、笔记；含 `\( ... \)`、`\[ ... \]` 公式；需要页边距、首行缩进、页码；成果要能复现（同一份 md 反复出同一份 pdf）。

**不适合**：需要邮件合并、批注、修订、目录域、母版；或者用户要的是**能在 Word 里继续编辑**的稿子 —— 那就走 docx 路线（python-docx + OMML），再按需导出 PDF。

## 三个引擎怎么选

| 引擎 | 中文 | 公式质量 | 依赖 | 何时用 |
|---|---|---|---|---|
| **KaTeX + 无头 Chromium**（主路线） | 好（系统字体） | 极好，与网页一致 | Node + Edge（系统自带） | 从 md 出 pdf，首选 |
| **Word COM**（`python-docx` → `ExportAsFixedFormat`） | 最好（宋体/黑体原生） | 好（OMML 原生公式，可编辑） | 装了 Office | 用户要 docx，或要 Word 级中文排版 |
| **LibreOffice headless** | 良好 | 一般（OMML 间距偏紧、公式变 Math 对象） | LibreOffice | 无 Office 环境做 docx/xlsx/pptx → pdf |
| **XeLaTeX + ctex** | 极好 | 极好（最专业） | 完整 TeX 发行版 | 学术排版、复杂数学 |

同一份中文报告实测：Word ≈ KaTeX > XeLaTeX(配置得当) > LibreOffice。**md 进、pdf 出，就走主路线**，别为了公式去装 4 GB 的 TeX。

## 主路线：命令

```powershell
# 从任意位置调用；脚本会自行定位 node / python / Edge
& "<skill-dir>\scripts\md2pdf.ps1" `
    -InputPath  "D:\工作\报告.md" `
    -OutputPath "D:\工作\报告.pdf" `
    -Title      "报告标题" `
    -Subtitle   "副 标 题"
```

最省事的入口：把 `.md` 拖到 `<skill-dir>\scripts\Drop-MD-Here.bat` 上，同目录生成同名 PDF（标题取文件名）。

只想渲染不补页码：`node <skill-dir>\scripts\md2pdf.js <in.md> <out.pdf> [标题] [副标题]`。

## 排版配方（中文 A4 报告）

```
@page { size: A4; margin: 2.4cm 2.5cm 2.2cm 2.6cm; }
body  12pt / line-height 1.72 / text-align justify / 宋体(SimSun) / Times New Roman 配西文
h2    黑体 15pt，h3 黑体 12.5pt，margin 16pt/11pt，page-break-after: avoid
p     text-indent 2em；公式块独立居中，page-break-inside: avoid
页码  9pt 下方居中，由 PyMuPDF 后置写入（Chromium 不支持 @page 的页边盒子）
```

## 踩坑清单（都踩过，照做即可）

1. **公式必须在 markdown 解析之前抽出来**。先正则抠 `\[...\]` / `\(...\)` 换成占位符，渲染完 markdown 再把 KaTeX 的 HTML 塞回占位符，否则 `_ ^ \` 会被 markdown 吃掉。
2. **独立公式要换成"独占一段"的占位符**（如 `\n\nZZEQTOKEN0ZZEQTOKEN\n\n`），渲染后匹配 `<p>占位符</p>` 整段替换成 `<div class="eqblock">`。用行内占位符塞回会出现公式缩进、被并进上一段。
3. **中文 md 常按行书写**：连续非空行会被 markdown 合并成同一段。需要一件一条时，先做行切分预处理（每个非空行插一个空行），否则 `（1）`、`（2）` 会挤在一起。
4. **标题里的公式同样要过渲染器**。只处理正文、忘了 heading，就会出现标题里裸露 `\(I-U_{AK}\)` 的事故（真发生过）。所有文本入口（h2/h3/正文/表格单元格）都走同一个 inline 渲染函数。
5. **`**粗体整行**` 是伪标题**：先转成 `###`，再把 `###` 统一降级成 `##`，否则层级乱。
6. **KaTeX 字体要跟着 HTML 走**：把 `katex/dist/fonts` 复制到输出目录，并把 CSS 里的 `url(fonts/` 改写成相对路径，否则公式回退成豆腐块。
7. **无头 Edge 的 stderr 噪音会打断 PowerShell**：`--print-to-pdf` 会往 stderr 吐 QQBrowser/扩展缓存之类的 ERROR，在 `$ErrorActionPreference='Stop'` 下会变成终止错误。用 `stdio: 'ignore'`（Node）或 `2>$null` 包住，只看退出码。
8. **PowerShell 参数别叫 `$Input` / `$Output`**：它们是自动变量，会被静默改写，导致实参错位（输出文件名变成标题）。用 `$InputPath` / `$OutputPath`。
9. **执行策略**：`RemoteSigned` 下本地 `.ps1` 可跑；从网上下载过的脚本带 MOTW 会被拒。稳妥写法 `powershell -NoProfile -ExecutionPolicy Bypass -File ...`，或干脆走 `.bat`。
10. **公式语法定界**：KaTeX 要求 `\( \)` / `\[ \]`；`$...$` 不会被识别。换行公式 `\[` 后必须独占一行，否则解析器抓不到。
11. **不要用 `--headless` 旧参数拼版面**：`--print-to-pdf` 只认 `@page` 的 `size/margin`；页眉页脚要 `--no-pdf-header-footer`，页码自己补。
12. **Word 路线补充**：中文必须显式设 `w:eastAsia` 字体；OMML 里字母自动斜体、数字直立，所以只需写 `<m:r><m:t>E</m:t></m:r>`；`\$Input` 之外的坑是 `xelatex` 之类 CLI 的 stderr 同样会被 PS 当成错误。
13. **LibreOffice 免管理员**：`msiexec /a pkg.msi /qn TARGETDIR=D:\Tools\LibreOffice` 解包即用；`soffice --headless --convert-to pdf --outdir <dir> <file>`。首次运行要 30 s（建用户配置）；同一份 docx 的版面不如 Word。
14. **不要为了"装齐"去装 4 GB 的 TeX**：MiKTeX basic + `--private` 就够，并且必须把包源改成清华 CTAN，否则首次编译会去连国外源。

## 校验（必须做，别凭感觉交付）

```powershell
# PDF -> PNG，人眼确认公式、分页、页码
& "<python>" "<skill-dir>\scripts\pdf_pages.py" "报告.pdf" ".\preview" 150
```

看三样：**公式有没有变成源码文本**、**中文有没有豆腐块**、**标题是否被拆到页尾**（`page-break-after: avoid` 生效则不会）。检查页数是否与预期一致；超过 2 页时确认没有孤行。

## 交付

`present({"files":[{"path":"…\\报告.pdf"}]})`；同时说明用了哪条路线、页数、以及是否做了渲染校验。若用户还要编辑版，另给 docx。

## 环境要求

| 需要 | 检查 | 缺失时的补救 |
|---|---|---|
| Node ≥ 18 | `node -v` | 装 Node，或改用 Word/LibreOffice 路线 |
| Python 3 + `pymupdf` | `python -c "import pymupdf"` | `pip install pymupdf -i https://pypi.tuna.tsinghua.edu.cn/simple` |
| Edge / Chrome | 脚本内置候选路径 | 设环境变量 `MD2PDF_EDGE` 指向可执行文件 |
| 中文字体 | — | 宋体(SimSun)、黑体(SimHei) 为 Windows 自带；Linux 改 `Noto Sans CJK` |

自检一条命令：`node <skill-dir>\scripts\md2pdf.js --selftest` 打印 Node/Edge/KaTeX 就绪情况。

不需要 `npm install`：`scripts/node_modules` 已随 skill 附带（katex、markdown-it）。
