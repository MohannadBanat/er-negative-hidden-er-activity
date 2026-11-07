// Amendment A3, GSE337500 ATAC-seq: base-pair-weighted mean RPKM coverage over TSS +/-1 kb windows (hg38),
// read from each replicate bigWig by HTTP range requests with @gmod/bbi 5.0.2.
// Run in a browser tab on https://ftp.ncbi.nlm.nih.gov (same origin as the files).
const {BigWig} = await import("https://esm.sh/@gmod/bbi@5.0.2");
function fh(url){ return {
  async read(a,b,c,d){ let length, position, buf=null, off=0;
    if (typeof a === "number"){ length=a; position=b; } else { buf=a; off=b; length=c; position=d; }
    const r = await fetch(url,{headers:{Range:`bytes=${position}-${position+length-1}`}});
    const u = new Uint8Array(await r.arrayBuffer());
    if (buf){ buf.set(u, off); return {bytesRead:u.length, buffer:buf}; } return u; },
  async readFile(){ return new Uint8Array(await (await fetch(url)).arrayBuffer()); },
  async stat(){ const r=await fetch(url,{method:"HEAD"}); return {size:+r.headers.get("content-length")}; },
  async close(){} }; }
const W = {ESR1:["chr6",151806318,151808318], AR:["chrX",67543031,67545031], FOXA1:["chr14",37594120,37596120], GAPDH:["chr12",6533404,6535404]};
const files = ["GSM9856660_BT_549_rep1","GSM9856661_BT_549_rep2","GSM9856662_HCC1599_rep1","GSM9856663_HCC1599_rep2",
  "GSM9856664_HCC1937_rep1","GSM9856665_HCC1937_rep2","GSM9856666_HCC2157_rep1","GSM9856667_HCC2157_rep2",
  "GSM9856668_MDA_MB_231_rep1","GSM9856669_MDA_MB_231_rep2","GSM9856670_MDA_MB_453_rep1","GSM9856671_MDA_MB_453_rep2",
  "GSM9856672_MDA_MB_468_rep1","GSM9856673_MDA_MB_468_rep2","GSM9856674_SUM185PE_rep1","GSM9856675_SUM185PE_rep2"];
const out = {};
for (const f of files){
  const gsm = f.split("_")[0];
  const bw = new BigWig({filehandle: fh(`/geo/samples/GSM9856nnn/${gsm}/suppl/${f}.bw`)});
  out[f] = {};
  for (const [g,[chr,s,e]] of Object.entries(W)){
    const feats = await bw.getFeatures(chr, s, e);
    let acc = 0;
    for (const x of feats){ const a=Math.max(x.start,s), b=Math.min(x.end,e); if (b>a) acc += (b-a)*x.score; }
    out[f][g] = +(acc/(e-s)).toFixed(5);   // bases with no feature count as 0
  }
}
JSON.stringify(out);
