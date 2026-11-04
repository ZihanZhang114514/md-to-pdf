---
name: md-to-pdf
description: Convert a Markdown file (Chinese or English, with LaTeX math) into a print-quality A4 PDF fully offline, without Microsoft Office, LibreOffice or a TeX distribution. Use when the user asks to turn a .md into a PDF, or when a report or note needs a PDF deliverable and an office suite cannot be assumed. Pipes markdown-it + KaTeX pre-rendered formulas into headless Chromium printing and stamps page numbers with PyMuPDF; also records the Word-COM, LibreOffice, XeLaTeX and Typst fallback routes and the layout pitfalls hit while building this pipeline, including a complete no-Chromium route for Android / Linux containers (missing fonts, WeasyPrint's maths breakage, Typst leading/spacing/indent measurements).
whenToUse: A .md file must become a PDF deliverable (report, note, handout), especially Chinese text with math formulas, and you want a reproducible conversion with no GUI app — on Windows with Edge, or on an Android / Linux container where no Chromium exists at all.
---

# Markdown → PDF（离线、中英双语、公式）

一条命令把 `.md` 变成可交付的 A4 PDF：**markdown-it 解析 → KaTeX 预渲染公式 → 无头 Edge 打印 → PyMuPDF 补页码**。全程离线，不依赖 Word / LibreOffice / TeX；公式是真正的矢量排版，不是截图。

**中英双语**：语言从正文自动判断（中文走 2em 首行缩进 + 宋体，English 走无缩进 + Times 系 + 自动断词），也可用 `MD2PDF_LANG=zh|en` 强制；判错了只影响排版风格，不影响内容。细节见「英文 Markdown」一节。

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
| **Typst**（单文件二进制） | 极好（Noto CJK） | 极好（与 LaTeX 同级） | 一个 48 MB 静态可执行文件 | **没有 Chromium 的容器 / Android**，见「没有 Chromium 时」一节 |

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

## 英文 Markdown（同一套命令，换一套排版风格）

英文 `.md` 走同一条命令，不需要额外参数。语言从正文自动判断：**正文里中日韩字符 ≥ 20 个、且不少于字母数的一半** 才判为中文，否则按英文排版。判错了只影响字体/缩进/断词，不影响内容；要锁定就设 `MD2PDF_LANG=zh` 或 `MD2PDF_LANG=en`。

| 项目 | 中文（zh） | 英文（en） |
|---|---|---|
| 正文 | `SimSun / 宋体` | `Times New Roman → Liberation Serif → DejaVu Serif` |
| 标题 | `SimHei / 黑体` | `Helvetica Neue → Arial → DejaVu Sans` |
| 首行缩进 | `2em` | `0`（英文报告惯例，靠段间距分节） |
| 行距 | 1.72 | 1.72（一致） |
| 断词 | 不需要 | `hyphens: auto` + `<html lang="en">`，否则两端对齐会出现「河」 |
| 一段一行 | 默认开启（中文实验报告按行书写） | **关闭**，按标准 Markdown 合并软换行 |
| 页码 | 9pt 居中 | 同 |

> 英文文档的 `###` 层级会被保留；只有当整篇连一个 `##` 都没有（典型的扁平中文报告）时，才会把 `###` 降级成 `##`。

Typst 路线另给了英文模板：`scripts/typst-template-en.typ`（DejaVu Serif + `lang: "en"` + 首行不缩进，A4/1.72 行距/页码与中文模板一致）。

### 英文相关的新坑（接着上面编号）

27. **默认的「一行一段」会把英文段落拆碎**。英文 `.md` 常把一句话软换行成几行，旧逻辑会把一段拆成四段（实测：一条 4 行的引言变成 4 个 `<p>`，句意断成碎片）。现在只有判为中文才开这个行为，英文按标准 Markdown 合并；要手工关用 `MD2PDF_LINE_ORIENTED=0`。
28. **`###` 被统一降级成 `##` 会把英文文档的层级压平**。英文报告惯用 `## 1.` + `### 1.1`，旧逻辑把 1.1 抬到与 1. 同级。现在只在**整篇一个 `##` 都没有**时才降级（那是扁平中文报告的写法）。
29. **英文两端对齐必须配断词**。缺 `hyphens: auto` 与 `lang="en"` 时，长单词撑开的空隙会形成明显的「白色河流」，比中文难看得多。
30. **英文别照抄 2em 首行缩进**。中英混排若被判成中文，英文段落会缩进两个字，像排版错误；混排以中文为主时属正常，介意就 `MD2PDF_LANG=en` 强制。

## 没有 Chromium 时：Android / Linux 容器路线（实测通过）

> 场景：Agent 跑在 Android 手机的 Ubuntu 容器里（aarch64），**没有 Edge/Chrome 也装不上**。
> 这条路线已完整跑通一次中文实验报告（A4 单页、8 个 `\( \)` 行内公式 + 1 个独立公式）。

### 实测环境

| 项目 | 值 |
|---|---|
| 容器 | Ubuntu 24.04.3 LTS / aarch64 |
| Node / Python | 24.19.0 / 3.12.3（pip 26.2.1，PEP 668，`pip` 不在 PATH，只有 `python3 -m pip`） |
| 浏览器 | **无** Edge / Chrome；`chromium-browser` 在 24.04 只是 snap 转发壳，容器内必失败 |
| 系统字体 | **`fc-list` 输出 0 行**，一个字体都没有 |
| 共享存储 | uid=0 直接读写 `/sdcard`（真挂载），产物落这里，手机文件管理器立刻可见 |
| 结论 | 主路线不可用 → WeasyPrint 顶替失败 → **Typst 兜底成功** |

### 三选一

| 方案 | 结果 |
|---|---|
| 无头 Chromium | ❌ 装不上，别用 puppeteer / playwright 硬试 |
| WeasyPrint 顶替 | ⚠️ 纯文本、表格可以；**含 `\frac` 的行内公式一定翻车**（坑 17） |
| **Typst 兜底** | ✅ 一个静态二进制，数学排版与 LaTeX 同级，离线、可复现 |

### 一条龙（照抄）

```bash
# 1) 中文字体：不装就是满屏豆腐块
apt-get install -y --no-install-recommends fonts-noto-cjk fontconfig
fc-list :lang=zh | head -3                  # 必须有输出

# 2) Typst：musl 静态二进制，解压即用
curl -sL -o /tmp/typst.tar.xz https://github.com/typst/typst/releases/latest/download/typst-aarch64-unknown-linux-musl.tar.xz
python3 -c "import lzma,tarfile;tarfile.open('/tmp/typst.tar.xz').extractall('/tmp')"   # 容器常无 xz
/tmp/typst-aarch64-unknown-linux-musl/typst --version
/tmp/typst-aarch64-unknown-linux-musl/typst fonts | grep -i "cjk sc"

# 3) 编译 + 校验
/tmp/typst-aarch64-unknown-linux-musl/typst compile report.typ "/sdcard/报告.pdf"
python3 -c "import pymupdf;d=pymupdf.open('/sdcard/报告.pdf');print(d.page_count);d[0].get_pixmap(dpi=150).save('/tmp/p1.png')"
```

模板：`scripts/typst-template.typ`。配方与上面的 CSS 版一一对应：

| skill 配方（CSS） | Typst 写法 |
|---|---|
| `@page{size:A4;margin:…}` | `#set page(paper:"a4", margin:(top:2.4cm,bottom:2.2cm,left:2.6cm,right:2.5cm))` |
| `12pt / line-height 1.72` | `#set text(size:12pt)` + `#set par(leading: 1em)`（坑 19） |
| 宋体 / 黑体 | `font: ("Noto Serif CJK SC",)` / `("Noto Sans CJK SC", weight:"bold")` |
| `p{text-indent:2em}` | 每段前 `#h(2em)`（坑 21） |
| 页码 9pt 居中 | `#set page(footer: context{ set text(size:9pt); align(center, counter(page).display("1")) })` |
| `page-break-after: avoid` | heading 的 `block(sticky: true)` |
| 公式块不跨页 | `block(breakable: false)` |

### 新增踩坑（接着上面编号）

15. **系统零字体是第一个坑**。容器刚建好时 `fc-list` 输出 0 行，哪个引擎都是豆腐块。装 `fonts-noto-cjk` 就够，**别顺手装 `-extra`**（多几个 GB）；装完必须 `fc-list :lang=zh` 复核。
16. **不要在容器里死磕 Chromium**。Ubuntu 24.04 的 `chromium-browser` 只是 snap 转发壳，容器内无 snapd；playwright 的 chromium 在受限容器里还常因沙箱起不来。直接跳到 Typst，省两小时。
17. **WeasyPrint 顶替 Chromium 会坏在公式上**（实测）：MathJax 输出 `<svg width="30.6ex" height="5.3ex">`，宽度用 `ex`、基线靠 `vertical-align`；WeasyPrint 的 `ex` 换算口径与浏览器不同 —— 分式的矢量宽度被算小，**公式横向压住后面的正文**，还多出一条贯穿的分数线。调 CSS 救不回来，别试。
18. **容器里 `tar` 解不开 `.tar.xz`**（`xz: Cannot exec`）。用 `python3 -c "import lzma,tarfile;tarfile.open(f).extractall(d)"`，不必为此改系统。
19. **Typst 的 `leading` ≠ CSS `line-height`**。12pt 字体实测：`0.72em`→基线步进 17.39pt，`1.0em`→20.75pt，`1.2em`→23.15pt，即 `步进 = 字号×(1+leading) − 3.25pt`。要 1.72 倍就写 `leading: 1em`，别按 0.72 去凑。
20. **Typst 的段间距不是接着行距算的**。实测段间基线距 = `8.75pt + spacing`，而段内行距是 20.7pt —— 所以默认 `spacing: 1.2em` 会给人「段比行还紧」的观感。中文报告用 `spacing: 1.55em` 才与 1.72 行距协调。
21. **Typst 不给标题后的首段自动缩进**。`par(first-line-indent:)` 对紧跟标题的段落不生效（首段与正文左对齐，后面的段落才缩进）。最稳做法：关掉自动缩进，逐段手写 `#h(2em)`。注意 `#h(2em)` 后直接接中文会被当标识符，**必须保留 `(` `)` 调用形式**；别写 `#let ip = h(2em)` 再 `#ip牛顿…`（报 `unknown variable`）。
22. **行内分式会被拆行**。`得 $R = r_k^2/(k\lambda)$` 曾在等号处断开成「得 R =」+「r_k²/(kλ)」。加 `#show math.equation.where(block: false): it => box(it)` 把行内公式整体成盒即可（这类公式都短，不会溢出）。
23. **`enum` 两个默认值会咬人**：`body-indent: 0em` 让序号粘住正文（「1.仪器调节」，要 `0.4em`）；`spacing: 0em` 会让相邻条目**上下重叠**（要 `0.9em` 左右）。
24. **全角括号开头的段落对不齐**：缩进全靠 `par(first-line-indent:)` 时，`（1）` 会左挂约 0.5em（实测 6pt）与其它段落错位；改用 `#h(2em)` 前置后，所有段落首字统一落在同一 x（实测 97.7pt）。
25. **pip 撞 PEP 668**：Ubuntu 24.04 上 `pip install weasyprint` 会被 externally-managed 拦下，用 `python3 -m pip install --break-system-packages`，或直接建 venv。
26. **产物与源同放 `/sdcard`**：容器 uid=0 直接写共享存储，中文文件名可用但脚本里一律加引号；校验用的 PNG 放 `/tmp`，别污染用户存储。

## 校验（必须做，别凭感觉交付）

```powershell
# PDF -> PNG，人眼确认公式、分页、页码
& "<python>" "<skill-dir>\scripts\pdf_pages.py" "报告.pdf" ".\preview" 150
```

看三样：**公式有没有变成源码文本**、**中文有没有豆腐块**、**标题是否被拆到页尾**（`page-break-after: avoid` 生效则不会）。检查页数是否与预期一致；超过 2 页时确认没有孤行。

英文稿额外看两样：**段落有没有被拆碎**（一段变成一串短行）、**断词是否生效**（两端对齐的长行里是否出现明显白缝）。

## 交付

`present({"files":[{"path":"…\\报告.pdf"}]})`；同时说明用了哪条路线、页数、以及是否做了渲染校验。若用户还要编辑版，另给 docx。

## 环境要求

| 需要 | 检查 | 缺失时的补救 |
|---|---|---|
| Node ≥ 18 | `node -v` | 装 Node，或改用 Word/LibreOffice 路线 |
| Python 3 + `pymupdf` | `python -c "import pymupdf"` | `pip install pymupdf -i https://pypi.tuna.tsinghua.edu.cn/simple` |
| Edge / Chrome | 脚本内置候选路径 | 设环境变量 `MD2PDF_EDGE` 指向可执行文件；**没有就改走 Typst**（「没有 Chromium 时」一节） |
| 中文字体 | `fc-list :lang=zh` | Windows 自带宋体/黑体；Debian/Ubuntu 装 `fonts-noto-cjk`；Android 容器默认 0 字体，必装 |

自检一条命令：`node <skill-dir>\scripts\md2pdf.js --selftest` 打印 Node/Edge/KaTeX 就绪情况。

不需要 `npm install`：`scripts/node_modules` 已随 skill 附带（katex、markdown-it）。
