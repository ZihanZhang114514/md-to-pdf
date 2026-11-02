import os
import sys

import pymupdf

# usage: python pdf_pages.py <file.pdf> <outdir> [dpi]
pdf = sys.argv[1]
outdir = sys.argv[2]
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 140

os.makedirs(outdir, exist_ok=True)
doc = pymupdf.open(pdf)
print("pages:", doc.page_count, "| size:", f"{doc[0].rect.width:.0f}x{doc[0].rect.height:.0f}pt")
for i, page in enumerate(doc):
    dst = os.path.join(outdir, f"p{i + 1}.png")
    page.get_pixmap(dpi=dpi).save(dst)
    print(" ->", dst)
