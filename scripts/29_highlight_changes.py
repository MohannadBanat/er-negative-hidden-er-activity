"""Mark changed paragraphs (citation numbers are ignored, because references were renumbered): any paragraph (body or table cell) of the revised file whose text is not in the submitted file is highlighted in yellow.
Usage: python3 -I highlight_changes.py submitted.docx revised.docx out.docx [submitted2.docx ...]"""
import sys, re, docx
from docx.enum.text import WD_COLOR_INDEX
def paras(d):
    for p in d.paragraphs: yield p
    for t in d.tables:
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs: yield p
norm = lambda t: re.sub(r'\[\d+(?:[–,]\d+)*\]', '[]', re.sub(r'Table \d|Section \d\.\d+', '#', t.strip()))
old = set()
for f in [sys.argv[1]] + sys.argv[4:]:
    old |= {norm(p.text) for p in paras(docx.Document(f))}
d = docx.Document(sys.argv[2]); n = tot = 0
for p in paras(d):
    t = p.text.strip()
    if not t: continue
    tot += 1
    if norm(t) not in old:
        n += 1
        for r in p.runs: r.font.highlight_color = WD_COLOR_INDEX.YELLOW
d.save(sys.argv[3]); print(f"highlighted {n} of {tot} paragraphs")
