"""Amendment A1 (amendment_A1_2026-10-25.md, SHA-256 3fa02b5b...ded8): composition-adjusted HEA.
ESTIMATE stromal/immune scores reproduce tidyestimate::estimate_score (commit 7f98f86):
genes restricted to tidyestimate's common_genes, within-sample ranks scaled 10000*rank/n, ssGSEA with weight 0.25."""
import sys, json, pathlib
import numpy as np, pandas as pd, pyreadr
from scipy.stats import rankdata
from statsmodels.stats.proportion import proportion_confint
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegressionCV
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

D, O, REF, TE = map(pathlib.Path, sys.argv[1:5])   # data, out, ref, tidyestimate repo
rng = np.random.default_rng(20261025)
expr = pd.read_parquet(D / "expr.parquet")
s = pd.read_parquet(D / "sampdesc.parquet").set_index("title").loc[expr.columns]
sc = pd.read_parquet(O / "scores.parquet").loc[expr.columns]
t = pd.read_csv(O / "neg_tumours_table.csv", index_col=0)
sets = json.load(open(REF / "estimate_gene_sets.json"))
common = next(iter(pyreadr.read_r(str(TE / "data/common_genes.rda")).values()))
cg = set(common["hgnc_symbol"].dropna().astype(str))
genes = [g for g in expr.index if g in cg]
X = expr.loc[genes].values
R = np.apply_along_axis(rankdata, 0, X); R = 10000 * R / R.shape[0]

def es(setname):
    gs = set(sets[setname]); hit = np.array([g in gs for g in genes]); n_hit = hit.sum()
    out = np.empty(R.shape[1])
    for j in range(R.shape[1]):
        o = np.argsort(-R[:, j], kind="stable"); v = R[o, j] ** 0.25; h = hit[o]
        reward = np.cumsum(h * v) / v[h].sum(); pen = np.cumsum(~h) / (~h).sum()
        out[j] = (reward - pen).sum()
    return out, int(n_hit)
sc["stromal"], n_s = es("stromal_signature"); sc["immune"], n_i = es("immune_signature")
res = {"n_common_genes_in_data": len(genes), "n_stromal_genes": n_s, "n_immune_genes": n_i}

uniq = s.index[~s.isRepl]; pos = uniq[s.loc[uniq, "er_Status"] == "1"]; neg = t.index
hea = t.index[t.group == "HEA"]; tn = t.index[t.group == "true_neg"]
def hl(a, b, B=2000):
    est = float(np.median(np.subtract.outer(a, b)))
    bs = [np.median(np.subtract.outer(rng.choice(a, len(a)), rng.choice(b, len(b)))) for _ in range(B)]
    return [est, *np.percentile(bs, [2.5, 97.5]).tolist()]
res["A1a"] = {v: hl(sc.loc[hea, v].values, sc.loc[tn, v].values) for v in ["stromal", "immune", "adipose_proxy"]}

# A1b composition-adjusted recall
Z = ["stromal", "immune", "adipose_proxy"]
def resid(col):
    A = np.c_[np.ones(len(pos)), sc.loc[pos, Z].values]
    beta, *_ = np.linalg.lstsq(A, sc.loc[pos, col].values, rcond=None)
    return sc[col] - np.c_[np.ones(len(sc)), sc[Z].values] @ beta
re_, ra = resid("ESR1"), resid("act_primary")
te, ta = np.percentile(re_[pos], 5), np.percentile(ra[pos], 5)
eh, ah = re_[neg] >= te, ra[neg] >= ta
G2 = pd.Series(np.select([eh & ah, eh & ~ah, ~eh & ah], ["HEA", "silent_ESR1", "act_wo_ESR1"], "true_neg"), index=neg)
k = int((G2 == "HEA").sum()); lo, hi = proportion_confint(k, len(neg), method="wilson")
kept = hea.intersection(G2.index[G2 == "HEA"]); dropped = hea.difference(kept); new = G2.index[G2 == "HEA"].difference(hea)
res["A1b"] = {"HEA_adj": [k, len(neg), k / len(neg), lo, hi],
              "groups_adj": G2.value_counts().to_dict(),
              "retained": len(kept), "dropped": len(dropped), "new": len(new),
              "pam50_retained": t.loc[kept, "pam50_subtype"].value_counts().to_dict(),
              "pam50_dropped": t.loc[dropped, "pam50_subtype"].value_counts().to_dict(),
              "pam50_new": s.loc[new, "pam50_subtype"].value_counts().to_dict(),
              "dropped_ids": sorted(dropped), "new_ids": sorted(new)}

# A1c technical-only model against adjusted HEA (same features & CV as P6)
tok = s.loc[neg, "scan.b_external_id"].astype(str).str.split(".").str[3:]
tokdf = pd.get_dummies(tok.apply(lambda x: pd.Series({f"tok{i}_{v}": 1 for i, v in enumerate(x)})).fillna(0))
tokdf = tokdf.loc[:, (tokdf.nunique() > 1) & (tokdf.sum() >= 3)]
F = pd.concat([(s.loc[neg, "instrument_model"] == "NextSeq 500").astype(int).rename("nextseq"),
               sc.loc[neg, ["frac_detected", "rp_median", "mean_expr"]], tokdf], axis=1).astype(float).values
y = (G2 == "HEA").astype(int).values
spl = list(RepeatedStratifiedKFold(n_splits=5, n_repeats=20, random_state=20261025).split(F, y)); aucs = []
for r in range(20):
    oof = np.full(len(y), np.nan)
    for tr, tst in spl[r * 5:(r + 1) * 5]:
        m = make_pipeline(StandardScaler(), LogisticRegressionCV(Cs=10, cv=5, scoring="roc_auc", max_iter=5000)); m.fit(F[tr], y[tr]); oof[tst] = m.predict_proba(F[tst])[:, 1]
    aucs.append(roc_auc_score(y, oof))
res["A1c"] = {"auc_mean": float(np.mean(aucs)), "auc_range": [float(min(aucs)), float(max(aucs))], "n_pos": int(y.sum())}
sc[["stromal", "immune"]].to_parquet(O / "estimate_scores.parquet")
G2.rename("group_adj").to_csv(O / "groups_adjusted.csv")
json.dump(res, open(O / "A1_results.json", "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
