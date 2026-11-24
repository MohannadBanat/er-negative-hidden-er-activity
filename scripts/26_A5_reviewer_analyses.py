"""Amendment A5 (2026-11-25): analyses requested in peer review (R1-R8). Post hoc. No outcome fields are read.
Usage: python3 -I 26_A5_reviewer_analyses.py <scanb data dir> <scanb out dir with scores.parquet> <repo results dir>
       <GSE25066_series_matrix.txt.gz> <GPL96.annot.gz> <h.all.v7.0.symbols.gmt> <out json>"""
import sys, json, gzip, io, pathlib, warnings
import numpy as np, pandas as pd
from scipy.stats import rankdata, spearmanr
from statsmodels.stats.proportion import proportion_confint
from sklearn.metrics import cohen_kappa_score, roc_auc_score, r2_score
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import RepeatedStratifiedKFold, RepeatedKFold, GridSearchCV, StratifiedKFold, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
warnings.filterwarnings("ignore")

D, O, RES = (pathlib.Path(a) for a in sys.argv[1:4]); SM, ANN, GMT, OUTJ = sys.argv[4:8]
SEED = 20261025; B = 2000
res = {"seed": SEED, "B": B}
wil = lambda k, n: [int(k), int(n), k / n] + [float(x) for x in proportion_confint(k, n, method="wilson")]
def newcombe(k1, n1, k2, n2):
    p1, p2 = k1 / n1, k2 / n2; l1, u1 = proportion_confint(k1, n1, method="wilson"); l2, u2 = proportion_confint(k2, n2, method="wilson")
    d = p1 - p2; return [d, d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)]
pct = lambda v, q=(2.5, 97.5): [float(x) for x in np.percentile(v, q)]
PCTS = (1, 2.5, 5, 7.5, 10)

# ------------------------------------------------------------------ SCAN-B
sc = pd.read_parquet(O / "scores.parquet")
s = pd.read_parquet(D / "sampdesc.parquet").set_index("title").loc[sc.index]
uniq = s[~s.isRepl].index
neg = s.loc[uniq][s.loc[uniq].er_Status == "0"].index; pos = s.loc[uniq][s.loc[uniq].er_Status == "1"].index
mis = uniq.difference(neg).difference(pos)
t = pd.read_csv(RES / "neg_tumours_table.csv", index_col=0)
r0 = json.load(open(RES / "results.json")); T5 = r0["thresholds"]["5"]
assert list(t.index) == list(neg) or set(t.index) == set(neg)
G = t.group.loc[neg]; hea = G.index[G == "HEA"]; tn = G.index[G == "true_neg"]
thr = lambda idx, col, p: float(np.percentile(sc.loc[idx, col], p))
assert abs(thr(pos, "ESR1", 5) - T5["ESR1"]) < 1e-5 and abs(thr(pos, "act_primary", 5) - T5["act_primary"]) < 1e-6
def call4(e, a, te, ta):
    return np.where(e >= te, np.where(a >= ta, "HEA", "silent_ESR1"), np.where(a >= ta, "act_wo_ESR1", "true_neg"))
res["scanb_n"] = {"neg": len(neg), "pos": len(pos), "missing": len(mis), "HEA": len(hea)}

# R1 observed replicate evidence for the joint call
rp = s[s.isRepl].index; op = pd.Index([x[:-4] for x in rp])
ex, ey = sc.loc[op, "ESR1"].values, sc.loc[rp, "ESR1"].values; ax, ay = sc.loc[op, "act_primary"].values, sc.loc[rp, "act_primary"].values
jx = (ex >= T5["ESR1"]) & (ax >= T5["act_primary"]); jy = (ey >= T5["ESR1"]) & (ay >= T5["act_primary"])
rng = np.random.default_rng(SEED)
def kap(i):
    return cohen_kappa_score(jx[i], jy[i]) if len(set(jx[i]) | set(jy[i])) > 1 else np.nan
kb = [kap(rng.integers(0, len(jx), len(jx))) for _ in range(B)]
lo_e, hi_e = sc.loc[hea, "ESR1"].min(), sc.loc[hea, "ESR1"].max(); lo_a, hi_a = sc.loc[hea, "act_primary"].min(), sc.loc[hea, "act_primary"].max()
inr = (ex >= lo_e) & (ex <= hi_e) & (ax >= lo_a) & (ax <= hi_a)
er_op = s.loc[op, "er_Status"].values
res["R1"] = {"pairs": len(rp), "joint_both_high_orig": int(jx.sum()), "joint_both_high_repl": int(jy.sum()),
             "agree": float((jx == jy).mean()), "discordant": int((jx != jy).sum()), "kappa": float(cohen_kappa_score(jx, jy)), "kappa_ci": pct(np.array(kb)[~np.isnan(kb)]),
             "HEA_range": {"ESR1": [float(lo_e), float(hi_e)], "activity": [float(lo_a), float(hi_a)]},
             "pairs_in_HEA_range": {"n": int(inr.sum()), "ihc_er_status_of_originals": pd.Series(er_op[inr]).fillna("NA").value_counts().to_dict(),
                                    "both_high_orig": int(jx[inr].sum()), "both_high_repl": int(jy[inr].sum()), "agree_n": int((jx[inr] == jy[inr]).sum()),
                                    "kappa": (float(cohen_kappa_score(jx[inr], jy[inr])) if inr.sum() > 1 and len(set(jx[inr]) | set(jy[inr])) > 1 else None)},
             "neg_pairs_n": int((er_op == "0").sum()), "neg_pairs_HEA": int(((er_op == "0") & jx).sum())}
print("R1", json.dumps(res["R1"]), flush=True)

# R2 technical model by feature type, scaler fitted inside the inner folds
tok = s.loc[neg, "scan.b_external_id"].astype(str).str.split(".").str[3:]
tokdf = pd.get_dummies(tok.apply(lambda x: pd.Series({f"tok{i}_{v}": 1 for i, v in enumerate(x)})).fillna(0))
tokdf = tokdf.loc[:, (tokdf.nunique() > 1) & (tokdf.sum() >= 3)]
Fmeta = pd.concat([(s.loc[neg, "instrument_model"] == "NextSeq 500").astype(int).rename("nextseq"), tokdf], axis=1).astype(float)
Fexpr = sc.loc[neg, ["frac_detected", "rp_median", "mean_expr"]].astype(float)
FS = {"all": pd.concat([Fmeta, Fexpr], axis=1), "metadata_only": Fmeta, "expression_derived_only": Fexpr}
gadj = pd.read_csv(RES / "groups_adjusted.csv", index_col=0).iloc[:, 0].reindex(neg)
YB = {"HEA": (G == "HEA").astype(int).values, "ESR1_high": (sc.loc[neg, "ESR1"] >= T5["ESR1"]).astype(int).values,
      "activity_high": (sc.loc[neg, "act_primary"] >= T5["act_primary"]).astype(int).values, "HEA_composition_adjusted": (gadj == "HEA").astype(int).values}
def cv_auc(X, y):
    spl = list(RepeatedStratifiedKFold(n_splits=5, n_repeats=20, random_state=SEED).split(X, y)); out = []
    for k in range(20):
        oof = np.full(len(y), np.nan)
        for tr, te in spl[k * 5:(k + 1) * 5]:
            m = GridSearchCV(Pipeline([("sc", StandardScaler()), ("lr", LogisticRegression(penalty="l2", max_iter=5000))]), {"lr__C": np.logspace(-4, 4, 10)},
                             scoring="roc_auc", cv=StratifiedKFold(5), n_jobs=-1)
            m.fit(X[tr], y[tr]); oof[te] = m.predict_proba(X[te])[:, 1]
        out.append(roc_auc_score(y, oof))
    return out
def cv_r2(X, y):
    spl = list(RepeatedKFold(n_splits=5, n_repeats=20, random_state=SEED).split(X)); out = []
    for k in range(20):
        oof = np.full(len(y), np.nan)
        for tr, te in spl[k * 5:(k + 1) * 5]:
            m = GridSearchCV(Pipeline([("sc", StandardScaler()), ("rg", Ridge())]), {"rg__alpha": np.logspace(-3, 3, 13)}, scoring="r2", cv=KFold(5), n_jobs=-1)
            m.fit(X[tr], y[tr]); oof[te] = m.predict(X[te])
        out.append(r2_score(y, oof))
    return out
res["R2"] = {"features": {k: v.columns.tolist() for k, v in FS.items()}, "auc": {}, "r2_activity_score": {}}
for yl, y in YB.items():
    res["R2"]["auc"][yl] = {"n_pos": int(y.sum())}
    for fl, F in FS.items():
        a = cv_auc(F.values, y); res["R2"]["auc"][yl][fl] = {"mean": float(np.mean(a)), "range": [float(min(a)), float(max(a))], "p2.5_97.5": pct(a)}
        print("R2", yl, fl, res["R2"]["auc"][yl][fl], flush=True)
for fl, F in FS.items():
    a = cv_r2(F.values, sc.loc[neg, "act_primary"].values); res["R2"]["r2_activity_score"][fl] = {"mean": float(np.mean(a)), "p2.5_97.5": pct(a)}
    print("R2 r2", fl, res["R2"]["r2_activity_score"][fl], flush=True)
res["R2"]["previous_values"] = {"HEA_all": r0["P6"]["auc_mean"], "r2_all": r0["P6"]["r2_mean"]}

# R3 bounds for missing IHC ER status
mb = int(((sc.loc[mis, "ESR1"] >= T5["ESR1"]) & (sc.loc[mis, "act_primary"] >= T5["act_primary"])).sum()); nm = len(mis)
res["R3"] = {"missing_n": nm, "missing_both_high": mb, "observed": wil(len(hea), len(neg)),
             "lower_bound": [len(hea), len(neg) + nm - mb, len(hea) / (len(neg) + nm - mb)], "upper_bound": [len(hea) + mb, len(neg) + mb, (len(hea) + mb) / (len(neg) + mb)]}
print("R3", res["R3"], flush=True)

# R8 two-group bootstrap of the adipose-proxy Hodges-Lehmann shift
xh, xt = sc.loc[hea, "adipose_proxy"].values, sc.loc[tn, "adipose_proxy"].values
rng = np.random.default_rng(SEED)
hl = lambda a, b: float(np.median(np.subtract.outer(a, b)))
bs = [hl(xh[rng.integers(0, len(xh), len(xh))], xt[rng.integers(0, len(xt), len(xt))]) for _ in range(B)]
res["R8"] = {"HL_shift": hl(xh, xt), "ci_two_group_bootstrap": pct(bs), "previous_ci_HEA_only": r0["P7"]["adipose_HL_ci_boot_HEA"], "n": [len(xh), len(xt)]}
print("R8", res["R8"], flush=True)

# ------------------------------------------------------------------ GSE25066 (same loading as script 22; outcome fields never parsed)
KEEP = {"er_status_ihc", "her2_status", "source", "esr1_status", "erbb2_status", "pam50_class"}
meta_lines, tab = [], []
with gzip.open(SM, "rt", errors="replace") as f:
    for line in f: (meta_lines if line.startswith("!") else tab).append(line)
gsm = None; chars = []
for l in meta_lines:
    p = [x.strip().strip('"') for x in l.rstrip("\n").split("\t")]
    if p[0] == "!Sample_geo_accession": gsm = p[1:]
    if p[0] == "!Sample_characteristics_ch1": chars.append(p[1:])
meta = pd.DataFrame(index=gsm, columns=sorted(KEEP))
for row in chars:
    for g, cell in zip(gsm, row):
        if ":" in cell:
            k, v = cell.split(":", 1); k = k.strip(); v = v.strip()
            if k in KEEP: meta.loc[g, k] = v
X = pd.read_csv(io.StringIO("".join(tab)), sep="\t", index_col=0)
X = X.loc[[i for i in X.index if isinstance(i, str) and not i.startswith("!")]].astype(float)[gsm]
if np.nanmax(X.values) > 100: X = np.log2(X.clip(lower=1))
ann = pd.read_csv(ANN, sep="\t", skiprows=27, usecols=[0, 2], dtype=str).dropna(); ann.columns = ["ID", "sym"]
ann = ann[~ann.sym.str.contains("///")].set_index("ID").sym
common = X.index.intersection(ann.index); best = X.loc[common].mean(axis=1).groupby(ann.loc[common]).idxmax()
E2 = X.loc[best.values]; E2.index = best.index
neg2 = meta.index[meta.er_status_ihc == "N"]; pos2 = meta.index[meta.er_status_ihc == "P"]
gs = {}
for line in open(GMT):
    f = line.rstrip("\n").split("\t"); gs[f[0]] = set(f[2:])
sig = gs["HALLMARK_ESTROGEN_RESPONSE_EARLY"] | gs["HALLMARK_ESTROGEN_RESPONSE_LATE"]
def rank_score(E, genes):
    R = np.apply_along_axis(rankdata, 0, E.values); R = (R - 1) / (R.shape[0] - 1)
    g = [x for x in genes if x in E.index and x != "ESR1"]
    return pd.Series(R[E.index.get_indexer(g)].mean(axis=0), index=E.columns), len(g)
a2, n2sig = rank_score(E2, sig)
sc2 = pd.DataFrame({"ESR1": E2.loc["ESR1"], "act_primary": a2})
old2 = pd.read_csv(RES / "A4_GSE25066_neg_tumours.csv", index_col=0)
assert np.abs(sc2.loc[old2.index, "act_primary"] - old2.act_primary).max() < 1e-9 and (old2.group == "HEA").sum() == 39
res["gse25066_n"] = {"neg": len(neg2), "pos": len(pos2), "genes": int(E2.shape[0]), "signature_genes": n2sig}

# R4 common gene universe and matched reference group
expr = pd.read_parquet(D / "expr.parquet")
universe = expr.index[np.median(expr.loc[:, uniq].values, axis=1) > 0]
cu = universe.intersection(E2.index); cu = cu[~cu.duplicated()]
E1c = expr.loc[cu, uniq]; E1c = E1c[~E1c.index.duplicated()]
a1c, n1c = rank_score(E1c, sig); a2c, n2c = rank_score(E2.loc[E1c.index], sig)
assert n1c == n2c
her2 = s.loc[uniq, "her2_Status"]
neg_h = neg[her2.loc[neg] == "0"]; pos_h = pos[her2.loc[pos] == "0"]
def hea_calls(esr, act, ref, tgt, p):
    te, ta = np.percentile(esr.loc[ref], p), np.percentile(act.loc[ref], p); return (esr.loc[tgt] >= te) & (act.loc[tgt] >= ta)
R4 = {"scanb_universe": len(universe), "gse25066_genes": int(E2.shape[0]), "common_universe": len(E1c), "common_signature_genes": n1c,
      "scanb_reference_HER2neg_ERpos": len(pos_h), "scanb_target_HER2neg_ERneg": len(neg_h), "by_percentile": {}}
for p in (1, 5, 10):
    c1 = hea_calls(sc.loc[uniq, "ESR1"], a1c, pos_h, neg_h, p); c2 = hea_calls(sc2.ESR1, a2c, pos2, neg2, p)
    R4["by_percentile"][str(p)] = {"scanb": wil(int(c1.sum()), len(c1)), "gse25066": wil(int(c2.sum()), len(c2)), "diff_gse_minus_scanb": newcombe(int(c2.sum()), len(c2), int(c1.sum()), len(c1))}
    if p == 5:
        o1 = (G.loc[neg_h] == "HEA").values; o2 = (old2.group.loc[neg2] == "HEA").values
        R4["kappa_common_vs_original_call"] = {"scanb": float(cohen_kappa_score(c1.values, o1)), "gse25066": float(cohen_kappa_score(c2.values, o2)),
                                               "scanb_original_HER2neg": int(o1.sum()), "gse25066_original": int(o2.sum())}
# same universe, original (all ER-positive) SCAN-B reference, for comparison
c1b = hea_calls(sc.loc[uniq, "ESR1"], a1c, pos, neg_h, 5); R4["scanb_common_universe_all_ERpos_reference"] = wil(int(c1b.sum()), len(c1b))
res["R4"] = R4; print("R4", json.dumps(R4), flush=True)

# R5 operating thresholds and threshold uncertainty; R6 dependence between axes
def r5(esr, act, pos_i, neg_i, tag):
    out = {"counts": {}}
    for p in PCTS:
        c = hea_calls(esr, act, pos_i, neg_i, p); out["counts"][str(p)] = wil(int(c.sum()), len(c))
    rng = np.random.default_rng(SEED); ep, ap = esr.loc[pos_i].values, act.loc[pos_i].values; en, an = esr.loc[neg_i].values, act.loc[neg_i].values
    te, ta, kf, pc = [], [], [], []
    for _ in range(B):
        i = rng.integers(0, len(ep), len(ep)); a, b = np.percentile(ep[i], 5), np.percentile(ap[i], 5); te.append(a); ta.append(b)
        kf.append(int(((en >= a) & (an >= b)).sum()))
        j = rng.integers(0, len(en), len(en)); pc.append(float(((en[j] >= a) & (an[j] >= b)).mean()))
    out["threshold_bootstrap"] = {"ESR1": pct(te), "activity": pct(ta), "HEA_count_fixed_negatives": pct(kf), "HEA_count_min_max": [int(min(kf)), int(max(kf))],
                                  "prevalence_combined_interval": pct(pc)}
    return out
res["R5"] = {"scanb": r5(sc.loc[uniq, "ESR1"], sc.loc[uniq, "act_primary"], pos, neg, "scanb"), "gse25066": r5(sc2.ESR1, sc2.act_primary, pos2, neg2, "gse")}
print("R5", json.dumps(res["R5"]), flush=True)
def r6(esr, act, sets):
    out = {}; rng = np.random.default_rng(SEED)
    for k, idx in sets.items():
        x, y = esr.loc[idx].values, act.loc[idx].values
        bs = [spearmanr(x[i], y[i])[0] for i in (rng.integers(0, len(x), len(x)) for _ in range(B))]
        out[k] = {"n": len(x), "rho": float(spearmanr(x, y)[0]), "ci": pct(bs)}
    return out
res["R6"] = {"scanb": r6(sc.ESR1, sc.act_primary, {"er_negative": neg, "er_positive": pos, "all": uniq}),
             "gse25066": r6(sc2.ESR1, sc2.act_primary, {"er_negative": neg2, "er_positive": pos2, "all": neg2.union(pos2)})}
print("R6", json.dumps(res["R6"]), flush=True)

# R7 reclassification simulation with uncertain thresholds and noise parameters
d_e = sc.loc[op, "ESR1"].values - sc.loc[rp, "ESR1"].values; d_a = sc.loc[op, "act_primary"].values - sc.loc[rp, "act_primary"].values
m_e = (sc.loc[op, "ESR1"].values + sc.loc[rp, "ESR1"].values) / 2; m_a = (sc.loc[op, "act_primary"].values + sc.loc[rp, "act_primary"].values) / 2
e0, a0 = sc.loc[neg, "ESR1"].values, sc.loc[neg, "act_primary"].values; is_hea = (G == "HEA").values
ep, ap = sc.loc[pos, "ESR1"].values, sc.loc[pos, "act_primary"].values
def curve(m, d, k=3):
    b = np.digitize(m, np.quantile(m, np.arange(1, k) / k)); return np.array([m[b == j].mean() for j in range(k)]), np.array([d[b == j].std(ddof=1) / np.sqrt(2) for j in range(k)])
def sim(i_pairs, i_pos, rng, ndraw=2000):
    de, da, me, ma = d_e[i_pairs], d_a[i_pairs], m_e[i_pairs], m_a[i_pairs]
    te, ta = np.percentile(ep[i_pos], 5), np.percentile(ap[i_pos], 5)
    base = call4(e0, a0, te, ta); cov = np.cov(np.c_[de, da].T) / 2; rho = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
    Z = rng.standard_normal((ndraw, 2)) @ np.linalg.cholesky(np.array([[1, rho], [rho, 1]])).T
    out = {}
    ce, ca = curve(me, de), curve(ma, da)
    for model, (se, sa) in {"constant": (np.full(len(e0), np.sqrt(cov[0, 0])), np.full(len(e0), np.sqrt(cov[1, 1]))),
                            "tertile": (np.interp(e0, *ce), np.interp(a0, *ca))}.items():
        g = call4(e0[None, :] + Z[:, [0]] * se[None, :], a0[None, :] + Z[:, [1]] * sa[None, :], te, ta)
        flip = (g != base[None, :]).mean(axis=0)
        out[model] = {"robust_lt10": int((flip[is_hea] < .10).sum()), "expected_flips_20": float(flip[is_hea].sum()), "still_HEA_under_boot_thresholds": int((base[is_hea] == "HEA").sum()),
                      "n_flip_ge10_of_241": int((flip >= .10).sum())}
    out["sd_e"], out["sd_a"], out["rho"] = float(np.sqrt(cov[0, 0])), float(np.sqrt(cov[1, 1])), float(rho)
    return out
rng = np.random.default_rng(SEED)
point = sim(np.arange(len(d_e)), np.arange(len(ep)), rng)
bt = [sim(rng.integers(0, len(d_e), len(d_e)), rng.integers(0, len(ep), len(ep)), rng) for _ in range(500)]
R7 = {"point_estimate_original_parameters": point, "bootstrap_n": 500, "draws": 2000}
for model in ("constant", "tertile"):
    R7[model] = {k: pct([b[model][k] for b in bt]) for k in ("robust_lt10", "expected_flips_20", "still_HEA_under_boot_thresholds", "n_flip_ge10_of_241")}
    R7[model]["robust_lt10_min_max"] = [int(min(b[model]["robust_lt10"] for b in bt)), int(max(b[model]["robust_lt10"] for b in bt))]
R7["sd_ESR1_interval"] = pct([b["sd_e"] for b in bt]); R7["sd_activity_interval"] = pct([b["sd_a"] for b in bt]); R7["rho_interval"] = pct([b["rho"] for b in bt])
R7["definition"] = "flip = P(call under the bootstrap thresholds changes after adding Gaussian technical error to the observed values); reported for the 20 tumours called HEA in the main analysis"
res["R7"] = R7; print("R7", json.dumps(R7), flush=True)

json.dump(res, open(OUTJ, "w"), indent=1)
print("written", OUTJ)
