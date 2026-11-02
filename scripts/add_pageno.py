import sys

import pymupdf

# usage: python add_pageno.py <file.pdf> [fontsize]
pdf = sys.argv[1]
fs = float(sys.argv[2]) if len(sys.argv) > 2 else 9.0
font = "times-roman"

doc = pymupdf.open(pdf)
for i, page in enumerate(doc):
    text = str(i + 1)
    w = pymupdf.get_text_length(text, fontname=font, fontsize=fs)
    page.insert_text(((page.rect.width - w) / 2, page.rect.height - 40),
                     text, fontname=font, fontsize=fs, color=(0, 0, 0))
doc.saveIncr()
n = doc.page_count
doc.close()
print(f"page numbers added to {pdf} ({n} pages)")
