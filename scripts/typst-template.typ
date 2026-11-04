// typst-template.typ —— 中文 A4 报告模板（无 Chromium 的容器 / Android 上用）
//
// 用法：
//   typst compile typst-template.typ 报告.pdf
// 依赖：Typst ≥ 0.13；中文用 Noto CJK（Debian/Ubuntu: apt install fonts-noto-cjk）
//
// 本模板的每个数值都是实测调出来的，别凭直觉改（详见 SKILL.md「没有 Chromium 时」一节的坑 19-24）：
//   leading: 1em      → 基线步进 20.75pt ≈ 1.72 倍行距
//   spacing: 1.55em   → 段间距与行距协调（Typst 段间距 = 8.75pt + spacing，不接行距）
//   逐段 #h(2em)      → Typst 不给标题后首段自动缩进，手写最稳

#set document(title: "报告标题")

#set page(
  paper: "a4",
  margin: (top: 2.4cm, bottom: 2.2cm, left: 2.6cm, right: 2.5cm),
  numbering: none,
  footer: context {
    set text(font: ("Noto Serif CJK SC",), size: 9pt)
    align(center, counter(page).display("1"))
  },
)

#set text(
  font: ("Noto Serif CJK SC", "DejaVu Serif"),
  size: 12pt,
  lang: "zh",
  region: "cn",
)

#set par(
  justify: true,
  leading: 1em,          // ≈ 1.72 倍行距
  first-line-indent: 0em, // 关掉，改用 #h(2em) 手工缩进
  spacing: 1.55em,
)

// 标题：h1 居中 + 分隔线，h2 黑体且不落在页尾
#show heading.where(level: 1): it => block(
  width: 100%,
  below: 18pt,
  align(center)[
    #set text(font: ("Noto Sans CJK SC",), size: 20pt, weight: "bold")
    #it.body
    #v(7pt)
    #line(length: 100%, stroke: 1.2pt)
  ],
)

#show heading.where(level: 2): it => block(
  above: 19pt,
  below: 9pt,
  sticky: true,
)[
  #set text(font: ("Noto Sans CJK SC",), size: 15pt, weight: "bold")
  #it.body
]

// 正文强调用黑体
#show strong: it => text(font: ("Noto Sans CJK SC",), weight: "bold", it.body)

// 行内公式整体成盒，避免分式在等号处被拆到两行
#show math.equation.where(block: false): it => box(it)

// 独立公式：上下留白、不跨页拆开、居中
#show math.equation.where(block: true): it => block(
  above: 10pt,
  below: 10pt,
  breakable: false,
  align(center, it),
)

// 有序列表：body-indent 0 会把序号粘住正文，spacing 0 会让条目重叠
#set enum(indent: 2em, body-indent: 0.4em, spacing: 0.9em)

// ============ 正文 ============

#heading(level: 1)[报告标题]

#heading(level: 2)[1. 一节]

#h(2em)正文段落，首行缩进由 `#h(2em)` 提供，段与段之间用空行分隔。

#h(2em)（1）全角括号开头的段落也统一缩进，不会左挂。

#heading(level: 2)[2. 公式]

#h(2em)行内公式：$Delta = 2e_k + lambda/2$，分式不会被拆行。

#h(2em)独立公式：

$ R = (D_m^2 - D_n^2) / (4 (m - n) lambda) $

#heading(level: 2)[3. 列表]

+ *小标题*：条目正文，序号与正文间距由 `enum(body-indent: 0.4em)` 控制。

+ *小标题*：条目之间由 `enum(spacing: 0.9em)` 撑开，不会上下重叠。
