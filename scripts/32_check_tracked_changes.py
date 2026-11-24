"""accept-all text must equal the clean revised file; reject-all text must equal the submitted file (non-empty paragraphs, in order)."""
import sys, copy, docx
from docx.oxml.ns import qn
def texts(body, mode):
    out = []
    for p in body.iter(qn("w:p")):
        ppr = p.find(qn("w:pPr")); rpr = ppr.find(qn("w:rPr")) if ppr is not None else None
        pins = rpr is not None and rpr.find(qn("w:ins")) is not None; pdel = rpr is not None and rpr.find(qn("w:del")) is not None
        s = ""
        for t in p.iter(qn("w:t"), qn("w:delText")):
            anc = [a.tag for a in t.iterancestors()]
            ins = qn("w:ins") in anc; dl = qn("w:del") in anc
            if mode == "accept" and dl: continue
            if mode == "reject" and ins: continue
            s += t.text or ""
        if (mode == "accept" and pdel) or (mode == "reject" and pins): 
            if s.strip(): out.append("§MERGE§" + s)
            continue
        if s.strip(): out.append(s.strip())
    return out
def plain(f): return [p for p in texts(docx.Document(f).element.body, "accept")]
trk, clean, sub = sys.argv[1:4]
b = docx.Document(trk).element.body
acc = texts(b, "accept"); rej = texts(b, "reject"); c = plain(clean); s_ = plain(sub)
print("accept == clean:", acc == c, len(acc), len(c)); print("reject == submitted:", rej == s_, len(rej), len(s_))
for name, a, x in (("accept", acc, c), ("reject", rej, s_)):
    if a != x:
        d = [(i, u[:70], v[:70]) for i, (u, v) in enumerate(zip(a, x)) if u != v][:4]; print(name, "first diffs", d)
