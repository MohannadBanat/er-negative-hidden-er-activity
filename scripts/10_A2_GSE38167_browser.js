// Amendment A2, GSE38167 extraction. Run in a browser tab on https://ftp.ncbi.nlm.nih.gov (same origin).
// The cloud workspace cannot reach GEO, so this runs on the author's computer and returns only the
// per-sample values the amendment needs (5 candidate miRNAs + per-sample 75th percentile).
// Value = median over a miRNA's features of log2(max(signal,1)) minus the sample's 75th percentile
// of log2(max(signal,1)) across all features (amendment_A1_2026-10-25.md, A2).
async function gunz(url){const r=await fetch(url); return await new Response(r.body.pipeThrough(new DecompressionStream("gzip"))).text();}
const m = await gunz("/geo/series/GSE38nnn/GSE38167/matrix/GSE38167_series_matrix.txt.gz");
const L = m.split("\n");
const gpl = L.find(l=>l.startsWith("!Series_platform_id")).split("\t")[1].replace(/"/g,"");
const titles = L.find(l=>l.startsWith("!Sample_title")).split("\t").slice(1).map(x=>x.replace(/"/g,""));
const gsms = L.find(l=>l.startsWith("!Sample_geo_accession")).split("\t").slice(1).map(x=>x.replace(/"/g,""));
const i0 = L.findIndex(l=>l.startsWith("!series_matrix_table_begin"));
const i1 = L.findIndex(l=>l.startsWith("!series_matrix_table_end"));
const rows = L.slice(i0+2, i1).map(l=>l.split("\t"));
const ids = rows.map(r=>r[0].replace(/"/g,""));
const vals = rows.map(r=>r.slice(1).map(Number));
// platform annotation
const gplNum = gpl.slice(3); const gnnn = "GPL" + (gplNum.length>3 ? gplNum.slice(0,-3) : "") + "nnn";
const soft = await gunz(`/geo/platforms/${gnnn}/${gpl}/soft/${gpl}_family.soft.gz`);
const S = soft.split("\n"); const b = S.findIndex(l=>l.startsWith("!platform_table_begin"));
const hdr = S[b+1].split("\t"); const e = S.findIndex(l=>l.startsWith("!platform_table_end"));
const nameCol = hdr.findIndex(h=>/^(miRNA_ID|miRNA_ID_LIST|SystematicName|GeneName|NAME|SPOT_ID)$/i.test(h));
const map = {}; for (const l of S.slice(b+2, e)) { const f=l.split("\t"); map[f[0]] = f[nameCol]; }
const want = {"miR-18a":/^hsa-miR-18a(-5p)?$/i, "miR-22":/^hsa-miR-22(-3p)?$/i, "miR-206":/^hsa-miR-206$/i,
              "miR-221":/^hsa-miR-221(-3p)?$/i, "miR-222":/^hsa-miR-222(-3p)?$/i};
const lg = v => Math.log2(Math.max(v,1));
const nS = titles.length; const p75 = [];
for (let j=0;j<nS;j++){ const col = vals.map(r=>lg(r[j])).sort((a,b)=>a-b); p75.push(col[Math.floor(0.75*(col.length-1))]); }
const med = a => { const s=[...a].sort((x,y)=>x-y); const n=s.length; return n%2? s[(n-1)/2] : (s[n/2-1]+s[n/2])/2; };
const out = {}; const featN = {};
for (const [k,re] of Object.entries(want)) {
  const idx = ids.map((id,i)=>[id,i]).filter(([id])=>re.test((map[id]||"").trim())).map(([,i])=>i);
  featN[k] = [idx.length, [...new Set(idx.map(i=>map[ids[i]]))]];
  out[k] = titles.map((_,j)=> idx.length ? +(med(idx.map(i=>lg(vals[i][j]))) - p75[j]).toFixed(4) : null);
}
JSON.stringify({gpl, nameColumn: hdr[nameCol], nFeatures: ids.length, nSamples: nS, featN, gsms, titles, p75: p75.map(x=>+x.toFixed(4)), values: out});
