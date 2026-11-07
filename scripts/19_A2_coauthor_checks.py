"""Amendment A2 (2026-11-03): exploratory checks E5-E8 requested by co-authors. GSE96058 only; no outcomes."""
import sys, json, pathlib
import numpy as np, pandas as pd
from statsmodels.stats.proportion import proportion_confint
from sklearn.metrics import roc_auc_score, cohen_kappa_score
from sklearn.linear_model import LogisticRegressionCV
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

D, O = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
r = json.load(open(O / "results.json")); T = r["thresholds"]["5"]; SD = r["P2b_tech_sd"]
t = pd.read_csv(O / "neg_tumours_table.csv", index_col=0)
sc = pd.read_parquet(O / "scores.parquet")
s = pd.read_parquet(D / "sampdesc.parquet").set_index("title")
wil = lambda k, n: [float(x) for x in proportion_confint(k, n, method="wilson")] if n else [None, None]
def newcombe(k1, n1, k2, n2):
    p1, p2 = k1 / n1, k2 / n2; l1, u1 = wil(k1, n1); l2, u2 = wil(k2, n2)
    d = p1 - p2
    return [d, d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)]
res = {}

# E5 HER2 stratification
her2 = s.loc[t.index, "her2_Status"].astype(str).replace({"NA": "missing", "nan": "missing", "None": "missing"})
res["E5"] = {}
for h in ["0", "1", "missing"]:
    sub = t[her2 == h]; n = len(sub)
    res["E5"][h] = {"n": n, "groups": {g: {"k": int((sub.group == g).sum()), "ci": wil(int((sub.group == g).sum()), n)} for g in ["HEA", "silent_ESR1", "act_wo_ESR1", "true_neg"]},
                    "HEA_pam50": sub[sub.group == "HEA"].pam50_subtype.value_counts().to_dict()}
k1, n1 = res["E5"]["1"]["groups"]["HEA"]["k"], res["E5"]["1"]["n"]; k0, n0 = res["E5"]["0"]["groups"]["HEA"]["k"], res["E5"]["0"]["n"]
res["E5"]["HEA_diff_her2pos_minus_neg"] = newcombe(k1, n1, k0, n0)

# E6 near-threshold stability
rp = s[s.isRepl].index; op = [x[:-4] for x in rp]
res["E6"] = {}
for col in ["ESR1", "act_primary"]:
    x, y = sc.loc[op, col].values, sc.loc[rp, col].values
    near = np.abs(x - T[col]) <= 2 * SD[col]
    out = {}
    for lab, m in [("near", near), ("far", ~near)]:
        a, b = x[m] >= T[col], y[m] >= T[col]
        out[lab] = {"n_pairs": int(m.sum()), "agree": float((a == b).mean()) if m.sum() else None,
                    "kappa": float(cohen_kappa_score(a, b)) if m.sum() and len(set(a) | set(b)) > 1 else None, "discordant": int((a != b).sum())}
    res["E6"][col] = out
nearN = (np.abs(t.ESR1 - T["ESR1"]) <= 2 * SD["ESR1"]) | (np.abs(t.act_primary - T["act_primary"]) <= 2 * SD["act_primary"])
fp = t.loc[nearN, "flip_prob"]
res["E6"]["neg_tumours_near"] = {"n": int(nearN.sum()), "of": len(t), "HEA_near": int((nearN & (t.group == "HEA")).sum()),
                                 "flip_median": float(fp.median()), "flip_range": [float(fp.min()), float(fp.max())],
                                 "flip_ge_10pct": int((fp >= .10).sum())}

# E7 technical model split by component (same features and CV as P6/E2)
tok = s.loc[t.index, "scan.b_external_id"].astype(str).str.split(".").str[3:]
tokdf = pd.get_dummies(tok.apply(lambda x: pd.Series({f"tok{i}_{v}": 1 for i, v in enumerate(x)})).fillna(0))
tokdf = tokdf.loc[:, (tokdf.nunique() > 1) & (tokdf.sum() >= 3)]
F = pd.concat([(t.instrument_model == "NextSeq 500").astype(int).rename("nextseq"),
               sc.loc[t.index, ["frac_detected", "rp_median", "mean_expr"]], tokdf], axis=1).astype(float).values
def cv_auc(X, y, reps, seed):
    out = []; spl = list(RepeatedStratifiedKFold(n_splits=5, n_repeats=reps, random_state=seed).split(X, y))
    for k in range(reps):
        oof = np.full(len(y), np.nan)
        for tr, te in spl[k * 5:(k + 1) * 5]:
            m = make_pipeline(StandardScaler(), LogisticRegressionCV(Cs=10, cv=5, scoring="roc_auc", max_iter=5000))
            m.fit(X[tr], y[tr]); oof[te] = m.predict_proba(X[te])[:, 1]
        out.append(roc_auc_score(y, oof))
    return out
res["E7"] = {}
for lab, y in [("ESR1_high", (t.ESR1 >= T["ESR1"]).astype(int).values), ("activity_high", (t.act_primary >= T["act_primary"]).astype(int).values)]:
    a = cv_auc(F, y, 20, 20261025)
    res["E7"][lab] = {"n_pos": int(y.sum()), "auc_mean": float(np.mean(a)), "auc_range": [float(min(a)), float(max(a))]}
    res["E7"][lab]["seed_check"] = {str(sd): float(np.mean(cv_auc(F, y, 20, sd))) for sd in (1, 2)}   # robustness to the CV seed
    print(lab, res["E7"][lab], flush=True)

# E8 missing IHC ER
u = s[~s.isRepl]; miss = u[~u.er_Status.isin(["0", "1"])].index
e, a_ = sc.loc[miss, "ESR1"] >= T["ESR1"], sc.loc[miss, "act_primary"] >= T["act_primary"]; n = len(miss)
res["E8"] = {"n": n, "ESR1_high": [int(e.sum()), wil(int(e.sum()), n)], "activity_high": [int(a_.sum()), wil(int(a_.sum()), n)],
             "both_high": [int((e & a_).sum()), wil(int((e & a_).sum()), n)], "neither": int((~e & ~a_).sum()),
             "pam50": u.loc[miss, "pam50_subtype"].value_counts().to_dict()}
json.dump(res, open(O / "A2_coauthor_checks.json", "w"), indent=1)
print(json.dumps(res, indent=1))
