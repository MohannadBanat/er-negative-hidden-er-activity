"""Write a Word file with real tracked changes (w:ins / w:del) from a submitted file and a revised file built on the same template.
Unchanged blocks are left alone. A changed paragraph is tracked word by word when it is similar to its predecessor (formatting kept),
otherwise the old paragraph is shown as deleted and the new one as inserted. Changed tables are tracked row by row as deleted + inserted.
Usage: python3 -I track_changes.py submitted.docx revised.docx out.docx [author]"""
import sys, re, copy, difflib, datetime
import docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from lxml import etree

OLD, NEW, OUT = sys.argv[1:4]; AUTHOR = sys.argv[4] if len(sys.argv) > 4 else "Authors"
DATE = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_id = [9000]
def rev(tag):
    e = OxmlElement(f"w:{tag}"); _id[0] += 1
    e.set(qn("w:id"), str(_id[0])); e.set(qn("w:author"), AUTHOR); e.set(qn("w:date"), DATE); return e

do, dn = docx.Document(OLD), docx.Document(NEW)
def blocks(d): return [k for k in d.element.body.iterchildren() if k.tag in (qn("w:p"), qn("w:tbl"))]
def ptext(p): return "".join(t.text or "" for t in p.iter(qn("w:t"), qn("w:delText")))
def has_drawing(el): return next(el.iter(qn("w:drawing"), qn("w:pict"), qn("w:object")), None) is not None
def key(b):
    if b.tag == qn("w:tbl"): return "TBL:" + "|".join(ptext(p).strip() for p in b.iter(qn("w:p")))
    t = ptext(b).strip()
    return ("IMG:" if has_drawing(b) else "P:") + t
bo, bn = blocks(do), blocks(dn); ko, kn = [key(b) for b in bo], [key(b) for b in bn]

# ---------------------------------------------------------------- marking helpers
def runs_of(p):
    out = []
    for c in p:
        if c.tag == qn("w:r"): out.append(c)
        elif c.tag == qn("w:hyperlink"): out += [r for r in c if r.tag == qn("w:r")]
    return out
def mark_par_mark(p, tag):
    ppr = p.find(qn("w:pPr"))
    if ppr is None: ppr = OxmlElement("w:pPr"); p.insert(0, ppr)
    rpr = ppr.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr"); sect = ppr.find(qn("w:sectPr")); (sect.addprevious(rpr) if sect is not None else ppr.append(rpr))
    rpr.insert(0, rev(tag))
def wrap(r, tag):
    w = rev(tag); r.addprevious(w); w.append(r)
def mark_inserted_par(p):
    for r in runs_of(p): wrap(r, "ins")
    mark_par_mark(p, "ins")
def to_deleted_run(r):
    for t in r.findall(qn("w:t")): t.tag = qn("w:delText")
def mark_deleted_par(p, note=None):
    for r in list(runs_of(p)):
        if has_drawing(r):                               # images of the old file are not carried over; leave a deleted note instead
            for c in list(r):
                if c.tag != qn("w:rPr"): r.remove(c)
            t = OxmlElement("w:t"); t.text = note or "[figure removed from this position]"; r.append(t)
        to_deleted_run(r); wrap(r, "del")
    mark_par_mark(p, "del")
def mark_table(tbl, tag):
    for tr in tbl.iter(qn("w:tr")):
        trpr = tr.find(qn("w:trPr"))
        if trpr is None:
            trpr = OxmlElement("w:trPr"); pos = 0
            for i, c in enumerate(tr):
                if c.tag in (qn("w:tblPrEx"),): pos = i + 1
            tr.insert(pos, trpr)
        trpr.append(rev(tag))
    for p in tbl.iter(qn("w:p")):
        (mark_inserted_par if tag == "ins" else mark_deleted_par)(p)

# ---------------------------------------------------------------- word-level diff inside one paragraph
SIMPLE = {qn("w:t"), qn("w:tab"), qn("w:br"), qn("w:rPr")}
def chars(p):
    """[(char, rPr xml or '')] or None if the paragraph holds anything but plain runs."""
    out = []
    for c in p:
        if c.tag == qn("w:pPr") or c.tag in (qn("w:bookmarkStart"), qn("w:bookmarkEnd"), qn("w:proofErr")): continue
        if c.tag != qn("w:r"): return None
        rpr = c.find(qn("w:rPr")); fx = etree.tostring(rpr).decode() if rpr is not None else ""
        for k in c:
            if k.tag not in SIMPLE: return None
            if k.tag == qn("w:t"): out += [(ch, fx) for ch in (k.text or "")]
            elif k.tag == qn("w:tab"): out.append(("\t", fx))
            elif k.tag == qn("w:br"): out.append(("\n", fx))
    return out
def toks(cs):
    s = "".join(c for c, _ in cs); spans = [(m.start(), m.end()) for m in re.finditer(r"\s+|[^\s\w]|\w+", s)]
    return [s[a:b] for a, b in spans], spans
def make_runs(cs, kind):
    """group chars by format into runs; kind in (None, 'ins', 'del')"""
    els = []; i = 0
    while i < len(cs):
        j = i
        while j < len(cs) and cs[j][1] == cs[i][1]: j += 1
        r = OxmlElement("w:r")
        if cs[i][1]: r.append(etree.fromstring(cs[i][1]))
        buf = ""
        def flush():
            nonlocal buf
            if buf:
                t = OxmlElement("w:delText" if kind == "del" else "w:t"); t.text = buf; t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve"); r.append(t); buf = ""
        for ch, _ in cs[i:j]:
            if ch == "\t": flush(); r.append(OxmlElement("w:tab"))
            elif ch == "\n": flush(); r.append(OxmlElement("w:br"))
            else: buf += ch
        flush()
        if kind: w = rev(kind); w.append(r); els.append(w)
        else: els.append(r)
        i = j
    return els
def diff_paragraph(p_new, p_old):
    """rewrite p_new in place with tracked word-level changes against p_old; False if not possible"""
    cn, co = chars(p_new), chars(p_old)
    if cn is None or co is None: return False
    tn, sn = toks(cn); to, so = toks(co)
    sm = difflib.SequenceMatcher(None, to, tn, autojunk=False); els = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal": els += make_runs(cn[sn[j1][0]:sn[j2 - 1][1]], None)
        else:
            if i2 > i1: els += make_runs(co[so[i1][0]:so[i2 - 1][1]], "del")
            if j2 > j1: els += make_runs(cn[sn[j1][0]:sn[j2 - 1][1]], "ins")
    for c in list(p_new):
        if c.tag != qn("w:pPr"): p_new.remove(c)
    for e in els: p_new.append(e)
    return True

def ratio(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sm.ratio() if sm.quick_ratio() >= 0.5 else 0.0
def style(p):
    ppr = p.find(qn("w:pPr")); st = ppr.find(qn("w:pStyle")) if ppr is not None else None
    return st.get(qn("w:val")) if st is not None else ""
def pair(olds, news):
    """order-preserving pairing of similar paragraphs (same style, ratio >= 0.55)"""
    n, m = len(olds), len(news); S = [[0.0] * m for _ in range(n)]
    for i, a in enumerate(olds):
        if a.tag != qn("w:p") or has_drawing(a): continue
        ta = ptext(a).strip()
        if len(ta) < 25: continue
        for j, b in enumerate(news):
            if b.tag != qn("w:p") or has_drawing(b) or style(a) != style(b): continue
            r = ratio(ta, ptext(b).strip()); S[i][j] = r if r >= 0.55 else 0.0
    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            D[i][j] = max(D[i + 1][j], D[i][j + 1], (S[i][j] + D[i + 1][j + 1]) if S[i][j] else 0.0)
    out = []; i = j = 0
    while i < n and j < m:
        if S[i][j] and abs(D[i][j] - (S[i][j] + D[i + 1][j + 1])) < 1e-12: out.append((i, j)); i += 1; j += 1
        elif D[i + 1][j] >= D[i][j + 1]: i += 1
        else: j += 1
    return out

# ---------------------------------------------------------------- walk the block-level diff
stat = {"equal": 0, "ins": 0, "del": 0, "word": 0}
body = dn.element.body; sect = body.find(qn("w:sectPr"))
def put_deleted(old_block, before):
    c = copy.deepcopy(old_block)
    if c.tag == qn("w:tbl"): mark_table(c, "del")
    else: mark_deleted_par(c)
    (before.addprevious(c) if before is not None else sect.addprevious(c)); stat["del"] += 1
def do_inserted(nb):
    if nb.tag == qn("w:tbl"): mark_table(nb, "ins")
    else: mark_inserted_par(nb)
    stat["ins"] += 1
for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ko, kn, autojunk=False).get_opcodes():
    if op == "equal": stat["equal"] += j2 - j1; continue
    olds, news = bo[i1:i2], bn[j1:j2]
    nxt = bn[j2] if j2 < len(bn) else None
    if op == "delete":
        for ob in olds: put_deleted(ob, nxt)
        continue
    if op == "insert":
        for nb in news: do_inserted(nb)
        continue
    pairs = pair(olds, news); pi = 0; oi = 0
    for nj, nb in enumerate(news):
        if pi < len(pairs) and pairs[pi][1] == nj:
            ti = pairs[pi][0]
            while oi < ti: put_deleted(olds[oi], nb); oi += 1
            if diff_paragraph(nb, olds[ti]): stat["word"] += 1
            else: put_deleted(olds[ti], nb); do_inserted(nb)
            oi = ti + 1; pi += 1
        else:
            do_inserted(nb)
    while oi < len(olds): put_deleted(olds[oi], nxt); oi += 1
dn.save(OUT); print(stat)
