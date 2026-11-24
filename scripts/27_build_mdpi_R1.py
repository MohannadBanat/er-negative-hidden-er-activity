"""Fill the official MDPI Cancers Word template with the manuscript (markdown export of the Docs draft).
Usage: python3 -I build_mdpi.py template.docx manuscript.md figdir out_main.docx out_supp.docx"""
import sys, re, copy
import docx
from docx.shared import Cm, Pt
from docx.enum.text import WD_COLOR_INDEX, WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

TPL, MD, FIGDIR, OUT, OUTS = sys.argv[1:6]
md = open(MD, encoding="utf8").read()
for a, b in [("&#91;", "["), ("&#93;", "]"), ("\\[", "["), ("\\]", "]"), ("\\*", "∗STAR"), ("\\_", "_"), ("\\#", "#"), ("\\>", ">"), ("\\-", "-")]:
    md = md.replace(a, b)
L = md.split("\n")
STAR = "∗STAR"
PLACE = re.compile(r"(\[[^\]]*[A-Za-z][^\]]*\])")          # bracketed text with letters = author placeholder (citations are numeric)

def add_runs(p, text, bold=None, size=None):
    """Inline **bold**, *italic*; highlight author placeholders in yellow."""
    for tok in re.split(r"(\*\*[^*]+\*\*|\*[^*\s][^*]*\*)", text):
        if not tok: continue
        b, it = bold, None
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4: tok, b = tok[2:-2], True
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2: tok, it = tok[1:-1], True
        for part in PLACE.split(tok):
            if not part: continue
            r = p.add_run(part.replace(STAR, "*")); r.bold = b; r.italic = it
            if size: r.font.size = size
            if PLACE.fullmatch(part): r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    return p

def set_runs(p, text, **kw):
    for r in list(p.runs): r._r.getparent().remove(r._r)
    return add_runs(p, text, **kw)

def no_bidi(doc):   # the template's section carries <w:bidi/> (right-to-left section); it reverses table columns in some renderers
    for sp in doc.element.body.iter(qn("w:sectPr")):
        for e in sp.findall(qn("w:bidi")): sp.remove(e)
d = docx.Document(TPL); no_bidi(d)
for _t in d.element.body.iter(qn('w:tblpPr')): _t.set(qn('w:tblpY'), '12000')   # sidebar 1 cm higher: at the template's 12541 it does not fit above the first-page footer in LibreOffice, which pushes the front matter to page 2
body = d.element.body
kids = list(body.iterchildren())
P = d.paragraphs
# ---- front matter -------------------------------------------------------------------------------
title = L[0].lstrip("# ").strip()
set_runs(P[0], "Article"); set_runs(P[1], title)
AUTHORS = [("Alia Abu Kiwan", "1", False), ("Hamza Abu Owida", "2", True), ("Areen Arabiat", "3", False),
           ("Mohannad Banat", "2", False), ("Manal Abbas", "1", True)]
AFFS = ["Department of Medical Laboratory Sciences, Faculty of Allied Medical Sciences, Al-Ahliyya Amman University, Amman 19328, Jordan",
        "Department of Medical Engineering, Faculty of Engineering, Al-Ahliyya Amman University, Amman 19328, Jordan",
        "Department of Communications and Computer Engineering, Faculty of Engineering, Al-Ahliyya Amman University, Amman 19328, Jordan"]
CORR = "Correspondence: h.abuowida@ammanu.edu.jo (H.A.O.); m.abbas@ammanu.edu.jo (M.A.)"
a = P[2]
for r in list(a.runs): r._r.getparent().remove(r._r)
for k, (nm, af, star) in enumerate(AUTHORS):
    sep = "" if k == 0 else (" and " if k == len(AUTHORS) - 1 else ", ")
    a.add_run(sep + nm + " ")
    r = a.add_run(af + (",*" if star else "")); r.font.superscript = True
extra = copy.deepcopy(P[4]._p); P[4]._p.addnext(extra)          # template has two affiliation lines; add a third
AFFP = [P[3], P[4], docx.text.paragraph.Paragraph(extra, d)]
CORRP = docx.text.paragraph.Paragraph(extra.getnext(), d)
for p, num, txt in [(AFFP[0], "1", AFFS[0]), (AFFP[1], "2", AFFS[1]), (AFFP[2], "3", AFFS[2]), (CORRP, "*", CORR)]:
    for r in list(p.runs): r._r.getparent().remove(r._r)
    r = p.add_run(num); r.font.superscript = num != "*" or None
    p.add_run("\t"); add_runs(p, txt)
FRONT = [P[2]._p] + [p._p for p in AFFP] + [CORRP._p]
def section(name):
    i = L.index(f"## {name}") + 1; out = []
    while not L[i].startswith("## "):
        if L[i].strip(): out.append(L[i].strip())
        i += 1
    return out
ss = section("Simple Summary"); ab = section("Abstract")
set_runs(P[7], " ".join(ss))
abs_txt = " ".join(x for x in ab if not x.startswith("**Keywords"))
set_runs(P[9], abs_txt.replace(":** ", "**: ").replace(":**", "**:"))
kw = next(x for x in ab if x.startswith("**Keywords")).split(":**", 1)[1].strip()
p = P[10]; set_runs(p, "**Keywords:** " + kw)
print("Simple Summary words:", len(" ".join(ss).split()), "| Abstract words:", len(re.sub(r"\*\*[^*]+\*\*", "", abs_txt).split()))

# ---- remove template guidance between the rule line and the Disclaimer --------------------------
disc = next(k for k in kids if k.tag == qn("w:p") and "Disclaimer/Publisher" in "".join(k.itertext()))
start = kids.index(P[11]._p) + 1
for k in kids[start:kids.index(disc)]: body.remove(k)
anchor = docx.text.paragraph.Paragraph(disc, d)

def para(text, style, **kw):
    p = anchor.insert_paragraph_before("", style=style); return add_runs(p, text, **kw)

def border(tag, sz):
    e = OxmlElement(f"w:{tag}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), "0"); e.set(qn("w:color"), "auto"); return e

def table(rows, doc=None, place=None, fracs=None, left_cols=(0,)):
    doc = doc or d
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head, data = cells[0], cells[2:]
    n = len(head); full = n >= 5 or any(len(c) > 40 for r in data for c in r)
    W = 10466 if full else 7857
    first = int(W * (0.15 if n >= 7 else 0.27 if n >= 5 else 0.36)); rest = (W - first) // (n - 1)
    widths = [first] + [rest] * (n - 1)
    if fracs: widths = [int(W * f_) for f_ in fracs]
    widths[-1] += W - sum(widths)
    t = doc.add_table(rows=len(data) + 1, cols=n)
    tblPr = t._tbl.tblPr
    for tag in ("w:tblStyle",):
        e = tblPr.find(qn(tag))
        if e is not None: tblPr.remove(e)
    tw = OxmlElement("w:tblW"); tw.set(qn("w:w"), str(W)); tw.set(qn("w:type"), "dxa"); tblPr.append(tw)
    ti = OxmlElement("w:tblInd"); ti.set(qn("w:w"), "0" if full else "2608"); ti.set(qn("w:type"), "dxa"); tblPr.append(ti)
    tb = OxmlElement("w:tblBorders"); tb.append(border("top", 8)); tb.append(border("bottom", 8)); tblPr.append(tb)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    mar = OxmlElement("w:tblCellMar")
    for side in ("left", "right"):
        e = OxmlElement(f"w:{side}"); e.set(qn("w:w"), "57"); e.set(qn("w:type"), "dxa"); mar.append(e)
    tblPr.append(mar)
    for j, gc in enumerate(t._tbl.tblGrid.findall(qn("w:gridCol"))): gc.set(qn("w:w"), str(widths[j]))
    for i, row in enumerate([head] + data):
        tr = t.rows[i]._tr
        if i == 0:
            trPr = tr.get_or_add_trPr(); h = OxmlElement("w:tblHeader"); trPr.append(h)
        else:
            trPr = tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); trPr.append(cs)
        for j, txt in enumerate(row):
            c = t.cell(i, j); c.width = widths[j]
            tcPr = c._tc.get_or_add_tcPr()
            tcw = tcPr.find(qn("w:tcW")); tcw.set(qn("w:w"), str(widths[j])); tcw.set(qn("w:type"), "dxa")
            if i == 0:
                tcb = OxmlElement("w:tcBorders"); tcb.append(border("bottom", 4)); tcPr.append(tcb)
            va = OxmlElement("w:vAlign"); va.set(qn("w:val"), "center"); tcPr.append(va)
            p = c.paragraphs[0]; p.style = doc.styles["MDPI_4.2_table_body"]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j in left_cols else WD_ALIGN_PARAGRAPH.CENTER
            add_runs(p, txt, bold=True if i == 0 else None)
    (place or anchor._p.addprevious)(t._tbl)

FIGS = {"1": "Figure1.png", "2": "Figure2.png", "3": "Figure3.png", "4": "Figure4.png", "5": "Figure5.png", "S1": "FigureS1.png", "S2": "Figure4.png", "S3": "Figure5.png"}
CAPFIX = {
    "2": lambda c: c.replace("; pct, percentile of IHC ER-positive tumours used as the threshold", "; percentile thresholds are percentiles of the score among IHC ER-positive tumours"),
    "S1": lambda c: "Technical replicate agreement for (**a**) ESR1 and (**b**) the ER-activity score in 136 replicate pairs. Triangles mark cross-platform pairs; dashed lines mark the 5th-percentile thresholds; the solid line is the line of identity.",
}
def figure(doc_anchor_fn, num, cap):
    cap = CAPFIX.get(num, lambda c: c)(cap)
    p = doc_anchor_fn("", "MDPI_5.2_figure"); p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(f"{FIGDIR}/{FIGS[num]}", width=Cm(13.8))
    c = doc_anchor_fn("", "MDPI_5.1_figure_caption"); r = c.add_run(f"Figure {num}. "); r.bold = True; add_runs(c, cap)

# ---- body ----------------------------------------------------------------------------------------
i = L.index("## 1. Introduction"); inrefs = False; supp_caption = None; last = None
while i < len(L):
    s = L[i].rstrip()
    if s.startswith("## Before submission"): break
    if not s.strip(): i += 1; continue
    if s.startswith("## "):
        h = s[3:].strip(); inrefs = h == "References"
        if h == "Supplementary Materials":
            j = i + 1
            while not L[j].startswith("**Author Contributions"):
                m = re.match(r"^\[image: Figure S1\. (.*?)\]?$", L[j].strip())
                if m: supp_caption = m.group(1).rstrip("]")
                j += 1
            sm = next(x.strip() for x in L[i + 1:j] if x.strip() and not x.strip().startswith("[image"))
            para("**Supplementary Materials:** The following supporting information can be downloaded at: https://www.mdpi.com/article/doi/s1, " + sm, "MDPI_6.2_back_matter")
            i = j; continue
        if h == "References":
            # abbreviations before references (MDPI back-matter order)
            para("The following abbreviations are used in this manuscript:", "MDPI_3.2_text_no_indent")
            ABBR = [("AR", "androgen receptor"), ("AUC", "area under the receiver operating characteristic curve"), ("CI", "confidence interval"), ("CV", "cross-validation"),
                    ("ER", "oestrogen receptor"), ("FPKM", "fragments per kilobase of transcript per million mapped reads"), ("GEO", "Gene Expression Omnibus"), ("HEA", "hidden ER activity"),
                    ("ICC", "intraclass correlation coefficient"), ("IHC", "immunohistochemistry"), ("IQR", "interquartile range"), ("LAR", "luminal androgen receptor"), ("MGC", "multigene classifier"),
                    ("PgR", "progesterone receptor"), ("SCAN-B", "Sweden Cancerome Analysis Network—Breast"), ("SD", "standard deviation"), ("SGC", "single-gene classifier"), ("TNBC", "triple-negative breast cancer")]
            t = d.add_table(rows=len(ABBR), cols=2)
            tblPr = t._tbl.tblPr; e = tblPr.find(qn("w:tblStyle"))
            if e is not None: tblPr.remove(e)
            ti = OxmlElement("w:tblInd"); ti.set(qn("w:w"), "2608"); ti.set(qn("w:type"), "dxa"); tblPr.append(ti)
            lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
            for j, gc in enumerate(t._tbl.tblGrid.findall(qn("w:gridCol"))): gc.set(qn("w:w"), str((1588, 6269)[j]))
            for k, (ab_, full) in enumerate(ABBR):
                for j, txt in enumerate((ab_, full)):
                    c = t.cell(k, j); c.width = (1588, 6269)[j] * 635
                    p = c.paragraphs[0]; p.style = d.styles["MDPI_7.1_footnote"] if "MDPI_7.1_footnote" in [x.name for x in d.styles] else d.styles["MDPI_4.2_table_body"]
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT; p.add_run(txt)
            p0 = anchor._p; p0.addprevious(t._tbl)
            # put the heading "Abbreviations" before the intro sentence
            intro = t._tbl.getprevious(); hp = anchor.insert_paragraph_before("Abbreviations", style="MDPI_2.1_heading1"); intro.addprevious(hp._p)
        para(h, "MDPI_2.1_heading1"); i += 1; continue
    if s.startswith("### "):
        para(s[4:].strip(), "MDPI_2.2_heading2"); i += 1; continue
    m = re.match(r"^\[image: Figure (S?\d+)\. (.*?)\]?$", s.strip())
    if m:
        figure(lambda t_, st: anchor.insert_paragraph_before(t_, style=st), m.group(1), m.group(2).rstrip("]")); i += 1; continue
    if s.startswith("|"):
        rows = []
        while i < len(L) and L[i].startswith("|"): rows.append(L[i]); i += 1
        table(rows); continue
    if re.match(r"^\*\*Table S?\d+\.\*\*", s):
        p = para(s, "MDPI_4.1_table_caption"); p.paragraph_format.keep_with_next = True; i += 1; continue
    m = re.match(r"^(\d+)\.\s+(.*)$", s)
    if m:
        if inrefs: para(m.group(2), "MDPI_8.1_references")
        else:
            if last is not None and last.style.name == "MDPI_3.1_text": last.style = d.styles["MDPI_3.5_text_before_list"]
            last = para(m.group(2), "MDPI_3.7_itemize")
        i += 1; continue
    if re.match(r"^\s*- ", s):
        if last is not None and last.style.name == "MDPI_3.1_text": last.style = d.styles["MDPI_3.5_text_before_list"]
        last = para(re.sub(r"^\s*-\s+", "", s), "MDPI_3.8_bullet"); i += 1; continue
    if re.match(r"^\*\*(Author Contributions|Funding|Institutional Review Board Statement|Informed Consent Statement|Data Availability Statement|Acknowledgments|Conflicts of Interest):\*\*", s):
        last = para(s.replace(":** ", "**: ", 1).replace(":**", "**:", 1) if False else s, "MDPI_6.2_back_matter"); i += 1; continue
    last = para(s, "MDPI_3.1_text"); i += 1

# MDPI orders back matter: Supplementary Materials, Author Contributions, Funding, IRB, Consent, Data, Acknowledgments, Conflicts, Abbreviations, References
ORDER = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing",
         "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption", "tblDescription"]
def tidy(doc):   # schema order inside w:tblPr, one tblW only (the last one set)
    for tp in doc.element.body.iter(qn("w:tblPr")):
        kids = list(tp)
        seen = {}
        for k in kids: seen[k.tag] = k          # last wins
        for k in kids: tp.remove(k)
        for name in ORDER:
            e = seen.get(qn(f"w:{name}"))
            if e is not None: tp.append(e)
d.core_properties.author = "; ".join(n for n, _, _ in AUTHORS); d.core_properties.title = title
tidy(d); d.save(OUT)

# ---- supplementary file: same template, front matter kept, body = Figure S1 ------------------------
s = docx.Document(TPL); no_bidi(s); b2 = s.element.body; k2 = list(b2.iterchildren()); P2 = s.paragraphs
set_runs(P2[0], "Supplementary Materials"); set_runs(P2[1], title)
anchor2 = P2[2]._p
for src in FRONT: anchor2.addprevious(copy.deepcopy(src))
for old_ in (P2[2]._p, P2[3]._p, P2[4]._p, P2[5]._p): b2.remove(old_)
k2 = list(b2.iterchildren())
last_front = [k for k in k2 if k.tag == qn("w:p") and "Correspondence:" in "".join(k.itertext())][0]
cut = k2.index(last_front)
for k in k2[cut + 1:]:
    if k.tag != qn("w:sectPr"): b2.remove(k)
for k in list(b2.iterchildren(qn("w:tbl"))): b2.remove(k)   # sidebar not needed in the supplement
def ins2(t_, st): return s.add_paragraph(t_, style=st)
ins2("", "MDPI_1.9_line")
sect = s.element.body.find(qn("w:sectPr"))
SL = open(sys.argv[6], encoding="utf8").read()
for a_, b_ in [("&#91;", "["), ("&#93;", "]"), ("\\[", "["), ("\\]", "]"), ("\\*", "∗STAR"), ("\\_", "_"), ("\\#", "#"), ("\\>", ">"), ("\\-", "-")]:
    SL = SL.replace(a_, b_)
SL = SL.split("\n"); i = 0; inrefs = False; last = None
while i < len(SL):
    x = SL[i].rstrip()
    if not x.strip(): i += 1; continue
    if x.startswith("## "):
        inrefs = x[3:].strip().startswith("References"); ins2(x[3:].strip(), "MDPI_2.1_heading1"); i += 1; continue
    if x.startswith("### "): ins2(x[4:].strip(), "MDPI_2.2_heading2"); i += 1; continue
    m = re.match(r"^\[image: Figure (S?\d+)\. (.*?)\]?$", x.strip())
    if m: figure(ins2, m.group(1), m.group(2).rstrip("]")); i += 1; continue
    if x.startswith("|"):
        rows = []
        while i < len(SL) and SL[i].startswith("|"): rows.append(SL[i]); i += 1
        n_ = len(rows[0].strip().strip("|").split("|"))
        table(rows, doc=s, place=sect.addprevious, fracs=(0.20, 0.42, 0.38) if n_ == 3 else None, left_cols=(0, 1, 2) if n_ == 3 else (0,)); continue
    if re.match(r"^\*\*Table S?\d+\.\*\*", x):
        cp = ins2("", "MDPI_4.1_table_caption"); cp.paragraph_format.keep_with_next = True; add_runs(cp, x); i += 1; continue
    m = re.match(r"^(\d+)\.\s+(.*)$", x)
    if m and inrefs: add_runs(ins2("", "MDPI_8.1_references"), m.group(2)); i += 1; continue
    if re.match(r"^\s*- ", x):
        if last is not None and last.style.name == "MDPI_3.1_text": last.style = s.styles["MDPI_3.5_text_before_list"]
        last = add_runs(ins2("", "MDPI_3.8_bullet"), re.sub(r"^\s*-\s+", "", x)); i += 1; continue
    last = add_runs(ins2("", "MDPI_3.1_text"), x); i += 1
tidy(s)
s.save(OUTS)
print("ok", OUT, OUTS)
