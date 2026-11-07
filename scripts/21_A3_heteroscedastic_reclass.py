"""Amendment A3 (2026-11-03): P2b reclassification probability with expression-dependent technical noise. Exploratory."""
import sys, json, pathlib
import numpy as np, pandas as pd

D, O = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
r = json.load(open(O / "results.json")); T = r["thresholds"]["5"]; RHO = r["P2b_tech_sd"]["corr"]
sc = pd.read_parquet(O / "scores.parquet"); s = pd.read_parquet(D / "sampdesc.parquet").set_index("title")
t = pd.read_csv(O / "neg_tumours_table.csv", index_col=0)
rp = s[s.isRepl].index; op = [x[:-4] for x in rp]
COLS = ["ESR1", "act_primary"]

def sd_curve(col, k):
    x, y = sc.loc[op, col].values, sc.loc[rp, col].values
    m, d = (x + y) / 2, x - y
    b = np.digitize(m, np.quantile(m, np.arange(1, k) / k))
    pos = np.array([m[b == j].mean() for j in range(k)]); sd = np.array([d[b == j].std(ddof=1) / np.sqrt(2) for j in range(k)])
    return pos, sd                               # np.interp holds the end values constant beyond the outer positions

def const_sd(col):
    d = sc.loc[op, col].values - sc.loc[rp, col].values
    return float(d.std(ddof=1) / np.sqrt(2))

rng = np.random.default_rng(20261025)
Z = rng.standard_normal((10000, 2)) @ np.linalg.cholesky(np.array([[1, RHO], [RHO, 1]])).T   # unit-variance correlated draws
G = t.group
def call(e, a):
    return np.where(e >= T["ESR1"], np.where(a >= T["act_primary"], "HEA", "silent_ESR1"), np.where(a >= T["act_primary"], "act_wo_ESR1", "true_neg"))

def run(sdfun):
    flip, newhea = {}, {}
    for tm in t.index:
        e0, a0 = t.loc[tm, "ESR1"], t.loc[tm, "act_primary"]
        se, sa = sdfun("ESR1", e0), sdfun("act_primary", a0)
        g = call(e0 + Z[:, 0] * se, a0 + Z[:, 1] * sa)
        flip[tm] = float((g != G[tm]).mean()); newhea[tm] = float((g == "HEA").mean())
    flip = pd.Series(flip); hea = G[G == "HEA"].index
    return {"expected_HEA_flips": float(flip[hea].sum()), "HEA_robust_lt10pct": int((flip[hea] < .10).sum()),
            "expected_new_HEA_from_others": float(pd.Series(newhea)[G != "HEA"].sum()),
            "n_flip_ge10pct_of_241": int((flip >= .10).sum()), "HEA_flip_probs": flip[hea].round(3).to_dict(),
            "median_flip_HEA": float(flip[hea].median())}

CS = {c: const_sd(c) for c in COLS}
res = {"rho": RHO, "constant_sd": CS}
res["constant"] = run(lambda c, v: CS[c])
for k, lab in [(3, "tertile"), (5, "quintile")]:
    curves = {c: sd_curve(c, k) for c in COLS}
    res[f"{lab}_curve"] = {c: {"pos": curves[c][0].round(4).tolist(), "sd": curves[c][1].round(5).tolist()} for c in COLS}
    res[lab] = run(lambda c, v, cv=curves: float(np.interp(v, cv[c][0], cv[c][1])))
p = res["tertile"]
res["decision"] = {"rule": "P2b conclusion stands if >=16/20 HEA have flip <10% and expected HEA flips <=2 (primary tertile model)",
                   "HEA_robust_lt10pct": p["HEA_robust_lt10pct"], "expected_HEA_flips": p["expected_HEA_flips"],
                   "stands": bool(p["HEA_robust_lt10pct"] >= 16 and p["expected_HEA_flips"] <= 2)}
json.dump(res, open(O / "A3_heteroscedastic_reclass.json", "w"), indent=1)
for m in ["constant", "tertile", "quintile"]:
    print(m, {k: v for k, v in res[m].items() if k != "HEA_flip_probs"})
print(res["decision"]); print(res["tertile_curve"])
