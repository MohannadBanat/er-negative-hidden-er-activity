"""Step 3: pre-specified analyses P1-P8 (analysis_plan_2026-10-25.md). No outcomes."""
import sys, json, pathlib, re
import numpy as np, pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportion_confint, confint_proportions_2indep
from sklearn.metrics import cohen_kappa_score, roc_auc_score, r2_score
from sklearn.linear_model import LogisticRegressionCV, RidgeCV
from sklearn.model_selection import RepeatedStratifiedKFold, RepeatedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

D, O = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
rng = np.random.default_rng(20261025)
sc = pd.read_parquet(O / "scores.parquet")
s = pd.read_parquet(D / "sampdesc.parquet").set_index("title").loc[sc.index]
res = {}

uniq = s[~s.isRepl].index
neg = s.loc[uniq][s.loc[uniq].er_Status == "0"].index
pos = s.loc[uniq][s.loc[uniq].er_Status == "1"].index
res["n_unique"], res["n_neg"], res["n_pos"] = len(uniq), len(neg), len(pos)

ACT = {"primary": "act_primary", "early": "act_early", "late": "act_late", "canon": "act_canon"}
def thr(col, pct): return float(np.percentile(sc.loc[pos, col], pct))
T = {p: {c: thr(c, p) for c in ["ESR1"] + list(ACT.values())} for p in (1, 5, 10)}
res["thresholds"] = T

def groups(idx, act="act_primary", pct=5):
    e = sc.loc[idx, "ESR1"] >= T[pct]["ESR1"]; a = sc.loc[idx, act] >= T[pct][act]
    g = np.select([e & a, e & ~a, ~e & a], ["HEA", "silent_ESR1", "act_wo_ESR1"], "true_neg")
    return pd.Series(g, index=idx)

def wilson(k, n):
    lo, hi = proportion_confint(k, n, method="wilson"); return [k, n, k / n, lo, hi]

# P1
G = groups(neg)
res["P1_groups"] = {g: wilson(int((G == g).sum()), len(neg)) for g in ["HEA", "silent_ESR1", "act_wo_ESR1", "true_neg"]}

# P2 replicates
rp = s[s.isRepl].index; op = [t[:-4] for t in rp]
cross = (s.loc[rp, "instrument_model"].values != s.loc[op, "instrument_model"].values)
def icc_a1(x, y):
    M = np.c_[x, y]; n, k = M.shape; gm = M.mean()
    msr = k * ((M.mean(1) - gm) ** 2).sum() / (n - 1)
    msc = n * ((M.mean(0) - gm) ** 2).sum() / (k - 1)
    sse = ((M - M.mean(1, keepdims=True) - M.mean(0, keepdims=True) + gm) ** 2).sum()
    mse = sse / ((n - 1) * (k - 1))
    return (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n)
def boot(f, n, B=2000):
    v = [f(rng.integers(0, n, n)) for _ in range(B)]; return np.nanpercentile(v, [2.5, 97.5]).tolist()
P2 = {}
for col in ["ESR1", "act_primary", "act_canon"]:
    x, y = sc.loc[op, col].values, sc.loc[rp, col].values
    for lab, m in [("all", np.ones(len(x), bool)), ("cross_platform", cross)]:
        xx, yy = x[m], y[m]
        P2[f"{col}_{lab}"] = {"n": int(m.sum()), "icc": icc_a1(xx, yy), "ci": boot(lambda i: icc_a1(xx[i], yy[i]), len(xx))}
    hx, hy = x >= T[5][col], y >= T[5][col]
    P2[f"{col}_call"] = {"pct_agree": float((hx == hy).mean()), "kappa": float(cohen_kappa_score(hx, hy)), "discordant": int((hx != hy).sum())}
gx, gy = groups(pd.Index(op)), groups(rp)
P2["group_call_agree_all"] = float((gx.values == gy.values).mean())
negpairs = np.array([s.loc[o, "er_Status"] == "0" for o in op])
P2["neg_pairs"] = {"n": int(negpairs.sum()), "group_agree": float((gx.values[negpairs] == gy.values[negpairs]).mean()),
                    "orig_groups": gx.values[negpairs].tolist(), "repl_groups": gy.values[negpairs].tolist()}
res["P2"] = P2

# P2b reclassification probability
d = np.c_[sc.loc[op, "ESR1"].values - sc.loc[rp, "ESR1"].values,
          sc.loc[op, "act_primary"].values - sc.loc[rp, "act_primary"].values]
cov = np.cov(d.T) / 2
res["P2b_tech_sd"] = {"ESR1": float(np.sqrt(cov[0, 0])), "act_primary": float(np.sqrt(cov[1, 1])),
                      "corr": float(cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1]))}
L = np.linalg.cholesky(cov); Z = rng.standard_normal((10000, 2)) @ L.T
te, ta = T[5]["ESR1"], T[5]["act_primary"]
flip = {}
for t in neg:
    v = np.array([sc.loc[t, "ESR1"], sc.loc[t, "act_primary"]]) + Z
    gsim = np.where(v[:, 0] >= te, np.where(v[:, 1] >= ta, "HEA", "silent_ESR1"), np.where(v[:, 1] >= ta, "act_wo_ESR1", "true_neg"))
    flip[t] = float((gsim != G[t]).mean())
flip = pd.Series(flip)
hea = G[G == "HEA"].index
res["P2b"] = {"n_HEA": len(hea), "expected_HEA_flips": float(flip[hea].sum()),
              "HEA_robust_lt10pct": int((flip[hea] < 0.10).sum()),
              "expected_new_HEA_from_others": float(sum(
                  ((np.array([sc.loc[t, "ESR1"], sc.loc[t, "act_primary"]]) + Z)[:, 0] >= te).__and__(
                   (np.array([sc.loc[t, "ESR1"], sc.loc[t, "act_primary"]]) + Z)[:, 1] >= ta).mean()
                  for t in G[G != "HEA"].index)),
              "HEA_flip_probs": flip[hea].round(3).to_dict()}

# P3 definition agreement
calls = pd.DataFrame(index=neg)
calls["HEA_primary"] = G == "HEA"
for k in ["early", "late", "canon"]: calls[f"HEA_{k}"] = groups(neg, ACT[k]) == "HEA"
calls["ESR1_high"] = sc.loc[neg, "ESR1"] >= T[5]["ESR1"]
calls["er_MGC"] = s.loc[neg, "er_MGC"] == "1"; calls["er_SGC"] = s.loc[neg, "er_SGC"] == "1"
cols = calls.columns.tolist(); K = {}
for i, a in enumerate(cols):
    for b in cols[i + 1:]:
        x, y = calls[a].values, calls[b].values
        K[f"{a}|{b}"] = [float(cohen_kappa_score(x, y)), boot(lambda j: cohen_kappa_score(x[j], y[j]), len(x), 1000)]
res["P3_n_pos"] = calls.sum().astype(int).to_dict(); res["P3_kappa"] = K
core = calls.HEA_primary & calls.HEA_canon & calls.er_SGC
res["P3_core"] = int(core.sum()); res["P3_positive_any"] = int(calls.any(axis=1).sum())

# P4 thresholds
res["P4"] = {p: wilson(int((groups(neg, pct=p) == "HEA").sum()), len(neg)) for p in (1, 5, 10)}

# P5 platform split
plat = s.loc[neg, "instrument_model"]
P5 = {}
for pl in ["HiSeq 2000", "NextSeq 500"]:
    m = plat == pl; P5[pl] = wilson(int((G[m] == "HEA").sum()), int(m.sum()))
k1, n1, k2, n2 = P5["HiSeq 2000"][0], P5["HiSeq 2000"][1], P5["NextSeq 500"][0], P5["NextSeq 500"][1]
P5["diff_newcombe"] = [k1 / n1 - k2 / n2, *confint_proportions_2indep(k1, n1, k2, n2, method="newcomb")]
res["P5"] = P5

# P6 technical-only negative control
tok = s.loc[neg, "scan.b_external_id"].astype(str).str.split(".").str[3:]
tokdf = pd.get_dummies(tok.apply(lambda t: pd.Series({f"tok{i}_{v}": 1 for i, v in enumerate(t)})).fillna(0))
tokdf = tokdf.loc[:, tokdf.nunique() > 1]
tokdf = tokdf.loc[:, tokdf.sum() >= 3]
F = pd.concat([(plat == "NextSeq 500").astype(int).rename("nextseq"),
               sc.loc[neg, ["frac_detected", "rp_median", "mean_expr"]], tokdf], axis=1).astype(float)
y = calls.HEA_primary.astype(int).values
aucs, r2s = [], []
outer = RepeatedStratifiedKFold(n_splits=5, n_repeats=20, random_state=20261025)
for rep in range(20):
    oof = np.full(len(y), np.nan)
    for k, (tr, te_) in enumerate(list(outer.split(F, y))[rep * 5:(rep + 1) * 5]):
        m = make_pipeline(StandardScaler(), LogisticRegressionCV(Cs=10, cv=5, penalty="l2", scoring="roc_auc", max_iter=5000))
        m.fit(F.values[tr], y[tr]); oof[te_] = m.predict_proba(F.values[te_])[:, 1]
    aucs.append(roc_auc_score(y, oof))
yc = sc.loc[neg, "act_primary"].values
for rep, (tr, te_) in enumerate(RepeatedKFold(n_splits=5, n_repeats=20, random_state=20261025).split(F)):
    pass
oofs = []
rkf = list(RepeatedKFold(n_splits=5, n_repeats=20, random_state=20261025).split(F))
for rep in range(20):
    oof = np.full(len(yc), np.nan)
    for tr, te_ in rkf[rep * 5:(rep + 1) * 5]:
        m = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13), cv=5)); m.fit(F.values[tr], yc[tr]); oof[te_] = m.predict(F.values[te_])
    r2s.append(r2_score(yc, oof))
res["P6"] = {"features": F.columns.tolist(), "n_pos": int(y.sum()),
             "auc_mean": float(np.mean(aucs)), "auc_2.5_97.5": np.percentile(aucs, [2.5, 97.5]).tolist(),
             "r2_mean": float(np.mean(r2s)), "r2_2.5_97.5": np.percentile(r2s, [2.5, 97.5]).tolist()}

# P7 contamination
tn = G[G == "true_neg"].index
pam = s.loc[neg, "pam50_subtype"]
a = int((pam[hea] == "Normal").sum()); b = len(hea) - a; c = int((pam[tn] == "Normal").sum()); dd = len(tn) - c
orr, pf = stats.fisher_exact([[a, b], [c, dd]])
t2 = stats.contingency.odds_ratio([[a, b], [c, dd]]).confidence_interval()
xh, xt = sc.loc[hea, "adipose_proxy"].values, sc.loc[tn, "adipose_proxy"].values
hl = float(np.median(np.subtract.outer(xh, xt)))
hlci = boot(lambda i: np.median(np.subtract.outer(xh[i % len(xh)], xt)), len(xh), 2000)
res["P7"] = {"normal_like_HEA": [a, len(hea)], "normal_like_trueneg": [c, len(tn)], "OR": orr, "OR_ci": [t2.low, t2.high], "fisher_p": pf,
             "adipose_HL_shift": hl, "adipose_HL_ci_boot_HEA": hlci, "mw_p": float(stats.mannwhitneyu(xh, xt).pvalue)}

# P8 description
desc = pd.concat([G.rename("group"), s.loc[neg, ["pam50_subtype", "nhg", "her2_Status", "pgr_Status", "ki67_Status", "lymphNode_Status", "instrument_model"]],
                  s.loc[neg, ["ageAtDx", "tumor_size"]].apply(pd.to_numeric, errors="coerce"), sc.loc[neg, ["ESR1", "act_primary", "AR", "FOXA1", "adipose_proxy"]],
                  calls[["er_MGC", "er_SGC"]], flip.rename("flip_prob")], axis=1)
desc.to_csv(O / "neg_tumours_table.csv")
P8 = {}
for v in ["pam50_subtype", "nhg", "her2_Status", "pgr_Status", "ki67_Status", "lymphNode_Status"]:
    P8[v] = pd.crosstab(desc.group, desc[v]).to_dict()
for v in ["ageAtDx", "tumor_size", "AR", "FOXA1"]:
    gsx = [desc.loc[desc.group == g, v].dropna() for g in desc.group.unique()]
    P8[v] = {"median_by_group": desc.groupby("group")[v].median().round(2).to_dict(), "kw_p": float(stats.kruskal(*gsx).pvalue)}
res["P8"] = P8
res["P8_pam50_fisher_HEA_vs_trueneg_luminal"] = None
lum = desc.pam50_subtype.isin(["LumA", "LumB"])
tab = [[int(lum[hea].sum()), len(hea) - int(lum[hea].sum())], [int(lum[tn].sum()), len(tn) - int(lum[tn].sum())]]
res["P8_luminal_HEA_vs_trueneg"] = {"table": tab, "fisher_p": float(stats.fisher_exact(tab)[1])}

json.dump(res, open(O / "results.json", "w"), indent=1, default=float)
print(json.dumps({k: v for k, v in res.items() if k not in ("P3_kappa", "P8", "P2b")}, indent=1, default=float))
print("P2b", {k: v for k, v in res["P2b"].items()})
