# 踩坑清单（都踩过，照做即可）

> Field notes for `md-to-pdf`. Written while building the pipeline, in Chinese
> because that is how they were recorded; every item was measured, none is
> folklore. Numbers continue across this file and `no-chromium.md`.

## 主路线（Chromium + KaTeX）

1. **公式必须在 markdown 解析之前抽出来**。先正则抠 `\[...\]` / `\(...\)` 换成占位符，渲染完 markdown 再把 KaTeX 的 HTML 塞回占位符，否则 `_ ^ \` 会被 markdown 吃掉。
2. **独立公式要换成"独占一段"的占位符**（如 `\n\nZZEQTOKEN0ZZEQTOKEN\n\n`），渲染后匹配 `<p>占位符</p>` 整段替换成 `<div class="eqblock">`。用行内占位符塞回会出现公式缩进、被并进上一段。
3. **中文 md 常按行书写**：连续非空行会被 markdown 合并成同一段。需要一件一条时，先做行切分预处理（每个非空行插一个空行），否则 `（1）`、`（2）` 会挤在一起。
4. **标题里的公式同样要过渲染器**。只处理正文、忘了 heading，就会出现标题里裸露 `\(I-U_{AK}\)` 的事故（真发生过）。所有文本入口（h2/h3/正文/表格单元格）都走同一个 inline 渲染函数。
5. **`**粗体整行**` 是伪标题**：先转成 `###`，再把 `###` 统一降级成 `##`，否则层级乱。
6. **KaTeX 字体要跟着 HTML 走**：把 `katex/dist/fonts` 复制到输出目录，并把 CSS 里的 `url(fonts/` 改写成相对路径，否则公式回退成豆腐块。
7. **无头 Edge 的 stderr 噪音会打断 PowerShell**：`--print-to-pdf` 会往 stderr 吐 QQBrowser/扩展缓存之类的 ERROR，在 `$ErrorActionPreference='Stop'` 下会变成终止错误。用 `stdio: 'ignore'`（Node）或 `2>$null` 包住，只看退出码。
8. **PowerShell 参数别叫 `$Input` / `$Output`**：它们是自动变量，会被静默改写，导致实参错位（输出文件名变成标题）。用 `$InputPath` / `$OutputPath`。
9. **执行策略**：`RemoteSigned` 下本地 `.ps1` 可跑；从网上下载过的脚本带 MOTW 会被拒。稳妥写法 `powershell -NoProfile -ExecutionPolicy Bypass -File ...`，或干脆走 `.bat`。
10. **公式语法定界**：KaTeX 要求 `\( \)` / `\[ \]`；`$...$` 不会被识别（构建时会打印一行警告指出是哪一段）。换行公式 `\[` 后必须独占一行，否则解析器抓不到。
11. **不要用 `--headless` 旧参数拼版面**：`--print-to-pdf` 只认 `@page` 的 `size/margin`；页眉页脚要 `--no-pdf-header-footer`，页码自己补。
12. **Word 路线补充**：中文必须显式设 `w:eastAsia` 字体；OMML 里字母自动斜体、数字直立，所以只需写 `<m:r><m:t>E</m:t></m:r>`；`$Input` 之外的坑是 `xelatex` 之类 CLI 的 stderr 同样会被 PS 当成错误。
13. **LibreOffice 免管理员**：`msiexec /a pkg.msi /qn TARGETDIR=D:\Tools\LibreOffice` 解包即用；`soffice --headless --convert-to pdf --outdir <dir> <file>`。首次运行要 30 s（建用户配置）；同一份 docx 的版面不如 Word。
14. **不要为了"装齐"去装 4 GB 的 TeX**：MiKTeX basic + `--private` 就够，并且必须把包源改成清华 CTAN，否则首次编译会去连国外源。

## 代码块与排版补丁（v1.1 修掉的两个）

31. **行切分预处理必须跳过 ``` 围栏**。中文「一行一段」的预处理会把代码块的每一行之间塞一个空行，代码在 PDF 里变成隔行；围栏内的 `^### ` 也会被标题归一化误伤。做法：解析前先把围栏整块换成占位符，数学抽取、标题归一化、行切分都跑完再还原。
32. **相对输出路径在 Chromium 下会静默失败**。Chromium 用**自己的**工作目录解析 `--print-to-pdf`，所以 `md2pdf.js in.md out.pdf` 会打印 `PDF -> out.pdf` 却什么都不写。必须先 `path.resolve()`；写完再 `existsSync` 复核，缺失就退出 4。

## 英文 Markdown 相关

27. **默认的「一行一段」会把英文段落拆碎**。英文 `.md` 常把一句话软换行成几行，旧逻辑会把一段拆成四段（实测：一条 4 行的引言变成 4 个 `<p>`，句意断成碎片）。现在只有判为中文才开这个行为，英文按标准 Markdown 合并；要手工关用 `MD2PDF_LINE_ORIENTED=0`。
28. **`###` 被统一降级成 `##` 会把英文文档的层级压平**。英文报告惯用 `## 1.` + `### 1.1`，旧逻辑把 1.1 抬到与 1. 同级。现在只在**整篇一个 `##` 都没有**时才降级（那是扁平中文报告的写法）。
29. **英文两端对齐必须配断词**。缺 `hyphens: auto` 与 `lang="en"` 时，长单词撑开的空隙会形成明显的「白色河流」，比中文难看得多。
30. **英文别照抄 2em 首行缩进**。中英混排若被判成中文，英文段落会缩进两个字，像排版错误；混排以中文为主时属正常，介意就 `MD2PDF_LANG=en` 强制。
