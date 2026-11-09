"""Full provenance check (requested 2026-11-10): every value of the analysed SCAN-B matrix (read from the GitHub package
12379monty/gse96058) against the GEO supplementary file. Usage: python3 -I 23_provenance_full_check.py <GEO csv.gz> <expr.parquet> <out.json>"""
import sys, json, hashlib
import numpy as np, pandas as pd
GEO, PQ, OUT = sys.argv[1:4]
md5 = hashlib.md5(); 
with open(GEO, "rb") as f:
    for b in iter(lambda: f.read(1 << 24), b""): md5.update(b)
E = pd.read_parquet(PQ)
res = {"geo_file": GEO.split("/")[-1], "geo_md5": md5.hexdigest(), "analysed_shape": list(E.shape)}
seen, maxdiff, n_cmp, n_bad, missing_genes, bad_examples = 0, 0.0, 0, 0, [], []
cols_checked = False
for ch in pd.read_csv(GEO, index_col=0, chunksize=2000):
    if not cols_checked:
        res["geo_n_samples"] = ch.shape[1]
        res["samples_only_in_geo"] = sorted(set(ch.columns) - set(E.columns))[:10]; res["samples_only_in_analysed"] = sorted(set(E.columns) - set(ch.columns))[:10]
        res["same_sample_set"] = set(ch.columns) == set(E.columns); cols_checked = True
    seen += len(ch)
    idx = ch.index.intersection(E.index); missing_genes += list(ch.index.difference(E.index)[:5])
    a = ch.loc[idx, E.columns].values.astype(float); b = E.loc[idx].values.astype(float)
    d = np.abs(a - b); nan_mis = np.isnan(a) != np.isnan(b)
    n_cmp += a.size; maxdiff = max(maxdiff, float(np.nanmax(d))); bad = (d > 1e-6) | nan_mis; n_bad += int(bad.sum())
    if bad.any() and len(bad_examples) < 5:
        i, j = np.argwhere(bad)[0]; bad_examples.append([idx[i], E.columns[j], float(a[i, j]), float(b[i, j])])
res.update({"geo_n_genes": seen, "genes_in_geo_not_analysed_examples": missing_genes[:10], "n_genes_analysed_not_in_geo": int(len(E.index) - n_cmp / E.shape[1]) ,
            "values_compared": n_cmp, "max_abs_difference": maxdiff, "values_differing_by_more_than_1e-6": n_bad, "examples": bad_examples})
json.dump(res, open(OUT, "w"), indent=1); print(json.dumps(res, indent=1))
