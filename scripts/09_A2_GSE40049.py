"""Amendment A2, GSE40049: ESR1-targeting miRNA precursors, tumour vs paired adjacent normal (14 pairs).
Counts = sum of reads over all alignments assigned to a precursor ID; CPM over all miRNA-assigned reads."""
import sys, json, pathlib, gzip, re
import numpy as np, pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

RAW, MAT, O = map(pathlib.Path, sys.argv[1:4])
rng = np.random.default_rng(20261025)
CAND = ["hsa-mir-18a", "hsa-mir-22", "hsa-mir-206", "hsa-mir-221", "hsa-mir-222"]
counts = {}
for f in sorted(RAW.glob("GSM*.txt.gz")):
    gsm = f.name.split("_")[0]; c = {}
    with gzip.open(f, "rt") as fh:
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) < 9: continue
            m = re.search(r'ID="([^"]+)"', p[8])
            if m: c[m.group(1)] = c.get(m.group(1), 0) + int(p[7])
    counts[gsm] = c
C = pd.DataFrame(counts).fillna(0)
# sample annotation from series matrix
L = open(MAT).read().split("\n")
def row(key, nth=0):
    rs = [l for l in L if l.startswith(key)]; return [x.strip('"') for x in rs[nth].split("\t")[1:]]
gsm, title = row("!Sample_geo_accession"), row("!Sample_title")
ch = [l for l in L if l.startswith("!Sample_characteristics_ch1")]
ann = pd.DataFrame({"title": title}, index=gsm)
for l in ch:
    vals = [x.strip('"') for x in l.split("\t")[1:]]
    k = vals[0].split(":")[0].strip(); ann[k] = [v.split(":", 1)[1].strip() if ":" in v else v for v in vals]
ann["patient"] = ann.title.str.split("_").str[0]; ann["type"] = ann.title.str.split("_").str[1]
C = C[ann.index]
lib = C.sum(0); cpm = np.log2(C.loc[[c for c in CAND if c in C.index]] / lib * 1e6 + 1)
res = {"library_size_median": float(lib.median()), "library_size_range": [float(lib.min()), float(lib.max())],
       "candidates_found": cpm.index.tolist(), "n_precursors": int(C.shape[0])}
T = ann[ann.type == "T"]; N = ann[ann.type == "N"]
pairs = sorted(set(T.patient) & set(N.patient)); res["n_pairs"] = len(pairs)
tid = [T.index[T.patient == p][0] for p in pairs]; nid = [N.index[N.patient == p][0] for p in pairs]
out, ps = {}, []
for mi in cpm.index:
    d = cpm.loc[mi, tid].values - cpm.loc[mi, nid].values
    p = stats.wilcoxon(d).pvalue if np.any(d != 0) else 1.0
    bs = [np.median(rng.choice(d, len(d))) for _ in range(2000)]
    out[mi] = {"median_log2FC": float(np.median(d)), "ci": np.percentile(bs, [2.5, 97.5]).tolist(), "p": float(p),
               "n_up": int((d > 0).sum()), "median_T": float(np.median(cpm.loc[mi, tid])), "median_N": float(np.median(cpm.loc[mi, nid]))}
    ps.append(p)
for mi, q in zip(out, multipletests(ps, method="fdr_bh")[1]): out[mi]["q_BH"] = float(q)
res["paired"] = out
# secondary: recurrence among 24 tumours
rec = T["recurrence"].astype(int); res["recurrence_n"] = int(rec.sum())
res["recurrence"] = {mi: {"median_rec": float(np.median(cpm.loc[mi, rec.index[rec == 1]])), "median_norec": float(np.median(cpm.loc[mi, rec.index[rec == 0]])),
                          "mw_p": float(stats.mannwhitneyu(cpm.loc[mi, rec.index[rec == 1]], cpm.loc[mi, rec.index[rec == 0]]).pvalue)} for mi in cpm.index}
cpm.T.join(ann).to_csv(O / "A2_GSE40049_cpm.csv")
json.dump(res, open(O / "A2_GSE40049.json", "w"), indent=1)
print(json.dumps(res, indent=1))
