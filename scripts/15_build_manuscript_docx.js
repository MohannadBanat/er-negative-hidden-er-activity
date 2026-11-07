// Build an MDPI Cancers-style .docx from the manuscript markdown exported from the doc.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType,
  AlignmentType, BorderStyle, Header, Footer, PageNumber, LevelFormat, TabStopType,
} = require("docx");

const [, , MD, FIGDIR, OUT] = process.argv;
let md = fs.readFileSync(MD, "utf8");
md = md.replace(/&#91;/g, "[").replace(/&#93;/g, "]").replace(/\\\]/g, "]").replace(/\\\[/g, "[");
const lines = md.split("\n");

const FONT = "Palatino Linotype";
const BODY = 20;   // half-points: 10 pt
const SMALL = 18;  // 9 pt
const PAGE_W = 11906, MARG_L = 1134, MARG_R = 1134; // A4, 2 cm margins
const TEXT_W = PAGE_W - MARG_L - MARG_R;

const FIG = {
  "1": "Figure1_ESR1_vs_activity.png", "2": "Figure2_prevalence_by_definition.png",
  "3": "Figure3_PAM50_by_group.png", "4": "Figure4_ESR1_targeting_miRNAs.png",
  "5": "Figure5_cellline_ESR1_AR_locus.png", "S1": "FigureS1_replicate_agreement.png",
};

// inline markdown -> runs (bold **, italic *, unescape \*)
function runs(text, opts = {}) {
  const size = opts.size || BODY;
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*)/g;
  let last = 0, m;
  const clean = s => s.replace(/\\\*/g, "*").replace(/\\_/g, "_").replace(/\\#/g, "#").replace(/\\>/g, ">");
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: clean(text.slice(last, m.index)), font: FONT, size, bold: opts.bold, italics: opts.italics }));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(new TextRun({ text: clean(tok.slice(2, -2)), font: FONT, size, bold: true, italics: opts.italics }));
    else out.push(new TextRun({ text: clean(tok.slice(1, -1)), font: FONT, size, italics: true, bold: opts.bold }));
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(new TextRun({ text: clean(text.slice(last)), font: FONT, size, bold: opts.bold, italics: opts.italics }));
  return out;
}
const para = (text, o = {}) => new Paragraph({
  children: runs(text, o), alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { after: o.after ?? 120, before: o.before ?? 0, line: 260 }, indent: o.indent,
  keepNext: o.keepNext,
});

function pngSize(file) {
  const b = fs.readFileSync(file); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
function figure(num, caption) {
  const f = path.join(FIGDIR, FIG[num]);
  const { w, h } = pngSize(f);
  const maxW = 620; // px at 96 dpi ~ 16.4 cm
  const width = maxW, height = Math.round(maxW * h / w);
  const cap = caption.replace(/^Figure (S?\d+)\.\s*/, "");
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 }, keepNext: true,
      children: [new ImageRun({ type: "png", data: fs.readFileSync(f), transformation: { width, height } })] }),
    new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 200 }, children: [
      new TextRun({ text: `Figure ${num}. `, bold: true, font: FONT, size: SMALL }), ...runs(cap, { size: SMALL })] }),
  ];
}

const thin = { style: BorderStyle.SINGLE, size: 6, color: "000000" };
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
function table(rows) {
  const cells = rows.map(r => r.replace(/^\||\|$/g, "").split("|").map(c => c.trim()));
  const header = cells[0]; const body = cells.slice(2);
  const n = header.length;
  // column widths: first column wider
  const first = Math.round(TEXT_W * (n > 5 ? 0.24 : 0.30));
  const rest = Math.floor((TEXT_W - first) / (n - 1));
  const widths = [first, ...Array(n - 1).fill(rest)];
  widths[n - 1] += TEXT_W - widths.reduce((a, b) => a + b, 0);
  const mk = (txt, i, isHead, isLast) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    borders: { top: isHead ? thin : none, bottom: (isHead || isLast) ? thin : none, left: none, right: none },
    margins: { top: 40, bottom: 40, left: 60, right: 60 },
    children: [new Paragraph({ alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER, spacing: { after: 0 },
      children: runs(txt, { size: 16, bold: isHead }) })],
  });
  const trs = [new TableRow({ tableHeader: true, children: header.map((t, i) => mk(t, i, true, false)) })];
  body.forEach((r, k) => trs.push(new TableRow({ cantSplit: true, children: r.map((t, i) => mk(t, i, false, k === body.length - 1)) })));
  return new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: widths, rows: trs });
}

const children = [];
let i = 0, inRefs = false, skip = false;
const title = lines[0].replace(/^#\s+/, "");
children.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Article", italics: true, font: FONT, size: SMALL })] }));
children.push(new Paragraph({ spacing: { after: 240 }, children: [new TextRun({ text: title, bold: true, font: FONT, size: 36 })] }));
i = 1;
while (i < lines.length) {
  let L = lines[i];
  if (/^Oct \d+, \d{4} · @/.test(L) || /^\*\*Article type:\*\*/.test(L)) { i++; continue; }      // doc byline / note
  if (/^## Before submission/.test(L)) { skip = true; }
  if (skip) { i++; continue; }
  if (!L.trim()) { i++; continue; }
  if (/^## /.test(L)) {
    const h = L.replace(/^##\s+/, "");
    inRefs = h === "References";
    const unnumbered = /^(Simple Summary|Abstract|Supplementary Materials|References)$/.test(h);
    children.push(new Paragraph({ keepNext: true, spacing: { before: 240, after: 120 },
      children: [new TextRun({ text: h, bold: true, font: FONT, size: unnumbered ? SMALL + 2 : BODY })] }));
    i++; continue;
  }
  if (/^### /.test(L)) {
    children.push(new Paragraph({ keepNext: true, spacing: { before: 180, after: 100 },
      children: [new TextRun({ text: L.replace(/^###\s+/, ""), italics: true, font: FONT, size: BODY })] }));
    i++; continue;
  }
  const fig = L.match(/^\[image: (Figure (S?\d+)\..*?)\]?\s*$/);
  if (fig) { children.push(...figure(fig[2], fig[1].replace(/\]$/, ""))); i++; continue; }
  if (/^\|/.test(L)) {
    const rows = []; while (i < lines.length && /^\|/.test(lines[i])) rows.push(lines[i++]);
    children.push(table(rows)); children.push(new Paragraph({ spacing: { after: 160 }, children: [] }));
    continue;
  }
  if (/^\*\*Table \d+\.\*\*/.test(L)) {   // table caption, above table
    children.push(new Paragraph({ keepNext: true, spacing: { before: 120, after: 80 }, alignment: AlignmentType.JUSTIFIED, children: runs(L, { size: SMALL }) }));
    i++; continue;
  }
  if (/^\d+\.\s/.test(L)) {
    const num = L.match(/^(\d+)\./)[1]; const txt = L.replace(/^\d+\.\s+/, "");
    if (inRefs) children.push(new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 60 }, indent: { left: 397, hanging: 397 },
      tabStops: [{ type: TabStopType.LEFT, position: 397 }],
      children: [new TextRun({ text: `${num}.\t`, font: FONT, size: SMALL }), ...runs(txt, { size: SMALL })] }));
    else children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 80 }, indent: { left: 397, hanging: 397 },
      tabStops: [{ type: TabStopType.LEFT, position: 397 }],
      children: [new TextRun({ text: `${num}.\t`, font: FONT, size: BODY }), ...runs(txt)] }));
    i++; continue;
  }
  if (/^\s*- /.test(L)) {
    const lvl = L.match(/^\s*/)[0].length >= 2 ? 1 : 0;
    children.push(new Paragraph({ numbering: { reference: "bul", level: lvl }, alignment: AlignmentType.JUSTIFIED,
      spacing: { after: 60 }, children: runs(L.replace(/^\s*-\s+/, "")) }));
    i++; continue;
  }
  // front matter / back-matter statements and normal paragraphs
  const small = /^(¹|²|\\\* Correspondence|\* Correspondence|ORCID:|\*\*(Author Contributions|Funding|Institutional Review Board Statement|Informed Consent Statement|Data Availability Statement|Acknowledgments|Conflicts of Interest|Keywords):)/.test(L);
  children.push(para(L, { size: small ? SMALL : BODY, after: small ? 80 : 120 }));
  i++;
}

const doc = new Document({
  creator: "Hamza Abu Owida; Mohannad Banat", title,
  styles: { default: { document: { run: { font: FONT, size: BODY } } } },
  numbering: { config: [{ reference: "bul", levels: [
    { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 397, hanging: 284 } } } },
    { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 794, hanging: 284 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: 1134, bottom: 1134, left: MARG_L, right: MARG_R } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.LEFT, children: [
      new TextRun({ text: "Cancers ", italics: true, font: FONT, size: 16 }), new TextRun({ text: "2026", bold: true, font: FONT, size: 16 }),
      new TextRun({ text: " — draft for co-author review, not yet submitted", font: FONT, size: 16 })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
      new TextRun({ children: [PageNumber.CURRENT, " of ", PageNumber.TOTAL_PAGES], font: FONT, size: 16 })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(OUT, b); console.log("wrote", OUT, b.length); });
