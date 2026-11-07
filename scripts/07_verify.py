"""Step 7: independent re-computation of the headline numbers from the raw expression
file, sharing no code with steps 2-3 (different ranking routine, ICC via a statsmodels two-way ANOVA)."""
import sys, pathlib, json
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm

D, O = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
e = pd.read_parquet(D / "expr.parquet"); s = pd.read_parquet(D / "sampdesc.parquet").set_index("title").loc[e.columns]
gmt = {l.split("\t")[0]: set(l.strip().split("\t")[2:]) for l in open(pathlib.Path(sys.argv[3]))}
u = ~s.isRepl
uni = e.index[e.loc[:, u].median(axis=1) > 0]
rk = e.loc[uni].rank(axis=0, method="average")
rk = (rk - 1) / (len(uni) - 1)
genes = sorted((gmt["HALLMARK_ESTROGEN_RESPONSE_EARLY"] | gmt["HALLMARK_ESTROGEN_RESPONSE_LATE"]) - {"ESR1"})
genes = [g for g in genes if g in rk.index]
act = rk.loc[genes].mean()
esr1 = e.loc["ESR1"]
pos = s.index[u & (s.er_Status == "1")]; neg = s.index[u & (s.er_Status == "0")]
te, ta = np.percentile(esr1[pos], 5), np.percentile(act[pos], 5)
hea = ((esr1[neg] >= te) & (act[neg] >= ta))
out = {"n_neg": len(neg), "HEA": int(hea.sum()), "silent": int(((esr1[neg] >= te) & (act[neg] < ta)).sum()),
       "act_wo": int(((esr1[neg] < te) & (act[neg] >= ta)).sum())}
rp = s.index[s.isRepl]; op = [x[:-4] for x in rp]
for name, v in [("ESR1", esr1), ("act", act)]:
    df = pd.DataFrame({"pair": list(range(len(rp))) * 2, "rater": ["o"] * len(rp) + ["r"] * len(rp),
                       "y": np.r_[v[op].values, v[rp].values]})
    a = anova_lm(smf.ols("y ~ C(pair) + C(rater)", data=df).fit())
    n = len(rp); msr = a.loc["C(pair)", "mean_sq"]; msc = a.loc["C(rater)", "mean_sq"]; mse = a.loc["Residual", "mean_sq"]
    out[f"ICC2_{name}"] = round(float((msr - mse) / (msr + mse + 2 * (msc - mse) / n)), 4)
prev = json.load(open(O / "results.json"))
out["matches_step3"] = (out["HEA"] == prev["P1_groups"]["HEA"][0] and out["act_wo"] == prev["P1_groups"]["act_wo_ESR1"][0]
                        and abs(out["ICC2_ESR1"] - prev["P2"]["ESR1_all"]["icc"]) < 1e-3
                        and abs(out["ICC2_act"] - prev["P2"]["act_primary_all"]["icc"]) < 1e-3)
print(json.dumps(out, indent=1))
