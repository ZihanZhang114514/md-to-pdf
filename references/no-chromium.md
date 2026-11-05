# 没有 Chromium 时：Android / Linux 容器路线（实测通过）

> Scenario: the agent runs inside an Ubuntu container on an Android phone (aarch64),
> where Edge/Chrome are unavailable **and cannot be installed**. This route was run
> end to end once on a Chinese lab report (A4, 8 inline `\( \)` formulas + 1 display
> formula). `/sdcard` below is DSH-on-Android's shared storage — substitute your own
> output directory on other hosts.

## 实测环境

| 项目 | 值 |
|---|---|
| 容器 | Ubuntu 24.04.3 LTS / aarch64 |
| Node / Python | 24.19.0 / 3.12.3（pip 26.2.1，PEP 668，`pip` 不在 PATH，只有 `python3 -m pip`） |
| 浏览器 | **无** Edge / Chrome；`chromium-browser` 在 24.04 只是 snap 转发壳，容器内必失败 |
| 系统字体 | **`fc-list` 输出 0 行**，一个字体都没有 |
| 共享存储 | uid=0 直接读写 `/sdcard`（真挂载），产物落这里，手机文件管理器立刻可见 |
| 结论 | 主路线不可用 → WeasyPrint 顶替失败 → **Typst 兜底成功** |

## 三选一

| 方案 | 结果 |
|---|---|
| 无头 Chromium | ❌ 装不上，别用 puppeteer / playwright 硬试 |
| WeasyPrint 顶替 | ⚠️ 纯文本、表格可以；**含 `\frac` 的行内公式一定翻车**（坑 17） |
| **Typst 兜底** | ✅ 一个静态二进制，数学排版与 LaTeX 同级，离线、可复现 |

## 一条龙（照抄）

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

模板：`scripts/typst-template.typ`（中文）与 `scripts/typst-template-en.typ`（英文）。配方与 CSS 版一一对应：

| skill 配方（CSS） | Typst 写法 |
|---|---|
| `@page{size:A4;margin:…}` | `#set page(paper:"a4", margin:(top:2.4cm,bottom:2.2cm,left:2.6cm,right:2.5cm))` |
| `12pt / line-height 1.72` | `#set text(size:12pt)` + `#set par(leading: 1em)`（坑 19） |
| 宋体 / 黑体 | `font: ("Noto Serif CJK SC",)` / `("Noto Sans CJK SC", weight:"bold")` |
| `p{text-indent:2em}` | 每段前 `#h(2em)`（坑 21） |
| 页码 9pt 居中 | `#set page(footer: context{ set text(size:9pt); align(center, counter(page).display("1")) })` |
| `page-break-after: avoid` | heading 的 `block(sticky: true)` |
| 公式块不跨页 | `block(breakable: false)` |

> 注意：这条路线是"照抄一段脚本"，不是一条命令。买家要的是 `node scripts/md2pdf.js`，别把它当同等能力宣传。

## 新增踩坑（接着 gotchas.md 的编号）

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
