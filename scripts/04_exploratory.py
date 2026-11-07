"""Step 4: EXPLORATORY checks added after seeing the P6 result (logged as E1-E3).
E1 permutation null for the technical-model AUC; E2 refit excluding PAM50 Normal-like;
E3 correlation of technical features with the adipose/normal proxy. No outcomes."""
import sys, json, pathlib
import numpy as np, pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegressionCV
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from joblib import Parallel, delayed

D, O = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
t = pd.read_csv(O / "neg_tumours_table.csv", index_col=0)
sc = pd.read_parquet(O / "scores.parquet")
s = pd.read_parquet(D / "sampdesc.parquet").set_index("title")
tok = s.loc[t.index, "scan.b_external_id"].astype(str).str.split(".").str[3:]
tokdf = pd.get_dummies(tok.apply(lambda x: pd.Series({f"tok{i}_{v}": 1 for i, v in enumerate(x)})).fillna(0))
tokdf = tokdf.loc[:, (tokdf.nunique() > 1) & (tokdf.sum() >= 3)]
F = pd.concat([(t.instrument_model == "NextSeq 500").astype(int).rename("nextseq"),
               sc.loc[t.index, ["frac_detected", "rp_median", "mean_expr"]], tokdf], axis=1).astype(float)

def cv_auc(X, y, reps, seed):
    out = []
    spl = list(RepeatedStratifiedKFold(n_splits=5, n_repeats=reps, random_state=seed).split(X, y))
    for r in range(reps):
        oof = np.full(len(y), np.nan)
        for tr, te in spl[r * 5:(r + 1) * 5]:
            m = make_pipeline(StandardScaler(), LogisticRegressionCV(Cs=10, cv=5, scoring="roc_auc", max_iter=5000))
            m.fit(X[tr], y[tr]); oof[te] = m.predict_proba(X[te])[:, 1]
        out.append(roc_auc_score(y, oof))
    return float(np.mean(out))

y = (t.group == "HEA").astype(int).values
rng = np.random.default_rng(20261025)
perms = [rng.permutation(y) for _ in range(200)]          # same sequence as the serial version
res = {}
keep = (t.pam50_subtype != "Normal").values
res["E2"] = {"n": int(keep.sum()), "n_pos": int(y[keep].sum()), "auc_excl_normal_like": cv_auc(F.values[keep], y[keep], 20, 20261025)}
res["E3"] = {c: [float(x) for x in stats.spearmanr(F[c], t.adipose_proxy)] for c in ["frac_detected", "rp_median", "mean_expr"]}
res["E3_univariate_auc"] = {c: float(roc_auc_score(y, F[c])) for c in ["frac_detected", "rp_median", "mean_expr", "nextseq"]}
print(json.dumps(res, indent=1), flush=True)
obs = cv_auc(F.values, y, 5, 1)
null = Parallel(n_jobs=2)(delayed(cv_auc)(F.values, perms[i], 5, i) for i in range(200))
res["E1"] = {"obs_auc_5rep": obs, "perm_null_mean": float(np.mean(null)), "perm_null_95": float(np.percentile(null, 95)),
             "perm_p": float((1 + sum(n >= obs for n in null)) / 201)}
json.dump(res, open(O / "exploratory.json", "w"), indent=1)
print(json.dumps(res, indent=1))
