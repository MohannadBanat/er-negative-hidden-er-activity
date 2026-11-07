"""Amendment A2, GSE38167: paired IDC vs NAT (and LN vs IDC, descriptive) for the 5 candidates,
from the values extracted on GEO by 10_A2_GSE38167_browser.js."""
import sys, json, pathlib
import numpy as np, pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
O = pathlib.Path(sys.argv[1]); rng = np.random.default_rng(20261025)
x = json.load(open(O / "A2_GSE38167_extract.json"))
df = pd.DataFrame(x["values"], index=x["titles"]); df["gsm"] = x["gsms"]
df["patient"] = df.index.str.split("_").str[0]; df["type"] = df.index.str.split("_").str[1]
res = {"checksums": {k: round(float(np.sum(v)), 3) for k, v in x["values"].items()}, "n_by_type": df.type.value_counts().to_dict()}
def paired(a, b):
    pts = sorted(set(df.patient[df.type == a]) & set(df.patient[df.type == b]))
    out, ps = {}, []
    for mi in x["values"]:
        d = np.array([df.loc[(df.patient == p) & (df.type == a), mi].iloc[0] - df.loc[(df.patient == p) & (df.type == b), mi].iloc[0] for p in pts])
        p = float(stats.wilcoxon(d).pvalue) if np.any(d != 0) else 1.0
        bs = [np.median(rng.choice(d, len(d))) for _ in range(2000)]
        out[mi] = {"median_diff": float(np.median(d)), "ci": np.percentile(bs, [2.5, 97.5]).tolist(), "p": p, "n_up": int((d > 0).sum())}
        ps.append(p)
    for mi, q in zip(out, multipletests(ps, method="fdr_bh")[1]): out[mi]["q_BH"] = float(q)
    return len(pts), out
res["IDC_vs_NAT_npairs"], res["IDC_vs_NAT"] = paired("IDC", "NAT")
res["LN_vs_IDC_npairs"], res["LN_vs_IDC"] = paired("LN", "IDC")
# detection: fraction of samples at the floor (signal <= 1 gives value = -p75)
p75 = pd.Series(x["p75"], index=x["titles"])
res["frac_at_floor"] = {mi: float(np.mean(np.isclose(df[mi], -p75, atol=1e-3))) for mi in x["values"]}
df.to_csv(O / "A2_GSE38167_values.csv")
json.dump(res, open(O / "A2_GSE38167.json", "w"), indent=1)
print(json.dumps(res, indent=1))
