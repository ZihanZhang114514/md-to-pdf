// typst-template-en.typ —— English A4 report template (for hosts without Chromium)
//
// usage:
//   typst compile typst-template-en.typ report.pdf
// deps: Typst >= 0.13; a serif Latin face (DejaVu Serif ships with most distros,
//       `apt install fonts-dejavu-core`). Noto CJK is only the fallback for stray Chinese.
//
// Compared with the Chinese template (typst-template.typ) this profile differs in:
//   * Latin-first font stack, `lang: "en"` so Typst hyphenates correctly
//   * no first-line indent (English reports/notes usually don't), space between paragraphs
//   * headings in a sans face
// Everything else (A4 geometry, 12pt / 1.72 line height, 9pt centred page number) is identical.

#set document(title: "Report Title")

#set page(
  paper: "a4",
  margin: (top: 2.4cm, bottom: 2.2cm, left: 2.6cm, right: 2.5cm),
  numbering: none,
  footer: context {
    set text(font: ("DejaVu Serif",), size: 9pt)
    align(center, counter(page).display("1"))
  },
)

#set text(
  font: ("DejaVu Serif", "Noto Serif CJK SC"),   // 装了 Times/Liberation 可自行换到最前
  size: 12pt,
  lang: "en",
  hyphenate: true,      // justified Latin text needs hyphenation, otherwise rivers appear
)

#set par(
  justify: true,
  leading: 1em,         // ≈ 1.72 line height (measured: 12pt × 1 + 1em − 3.25pt)
  first-line-indent: 0em,
  spacing: 1.55em,
)

#show heading.where(level: 1): it => block(
  width: 100%,
  below: 18pt,
  align(center)[
    #set text(font: ("DejaVu Sans", "Noto Sans CJK SC"), size: 20pt, weight: "bold")
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
  #set text(font: ("DejaVu Sans", "Noto Sans CJK SC"), size: 15pt, weight: "bold")
  #it.body
]

#show heading.where(level: 3): it => block(
  above: 13pt,
  below: 6pt,
  sticky: true,
)[
  #set text(font: ("DejaVu Sans", "Noto Sans CJK SC"), size: 12.5pt, weight: "bold")
  #it.body
]

#show strong: it => text(font: ("DejaVu Sans", "Noto Sans CJK SC"), weight: "bold", it.body)

// inline maths stays one box, so a fraction never breaks at the equals sign
#show math.equation.where(block: false): it => box(it)

#show math.equation.where(block: true): it => block(
  above: 10pt,
  below: 10pt,
  breakable: false,
  align(center, it),
)

// enum defaults glue the number to the text (body-indent: 0em) and overlap rows (spacing: 0em)
#set enum(indent: 1.6em, body-indent: 0.4em, spacing: 0.6em)

// ============ content ============

#heading(level: 1)[Report Title]

#heading(level: 2)[1. Introduction]

Newton's rings are a classic equal-thickness interference phenomenon. When a plano-convex lens rests on a flat glass plate, a thin air film forms between them and the light reflected from its two surfaces interferes. The optical path difference is $Delta = 2e_k + lambda/2$.

#heading(level: 3)[1.1 Radius of curvature]

From the geometry $r_k^2 approx 2e_k R$, the radius of curvature follows from the diameters of two dark rings:

$ R = (D_m^2 - D_n^2) / (4 (m - n) lambda) $

#heading(level: 2)[2. Procedure]

+ Place the Newton's rings assembly on the stage and align the cross-hair.
+ Measure the dark rings from the 30th down to the 11th on one side.
+ Continue through the centre and repeat on the other side.
