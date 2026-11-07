"""Step 2: compute ESR1 axis and ER-activity scores for all 3,409 libraries
exactly as defined in analysis_plan_2026-10-25.md section 4. No outcomes used."""
import sys, pathlib
import numpy as np, pandas as pd
from scipy.stats import rankdata

D = pathlib.Path(sys.argv[1]); REF = pathlib.Path(sys.argv[2]); OUT = pathlib.Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)
expr = pd.read_parquet(D / "expr.parquet")
samp = pd.read_parquet(D / "sampdesc.parquet").set_index("title").loc[expr.columns]
uniq = ~samp.isRepl.values

gs = {}
for line in open(REF / "h.all.v7.0.symbols.gmt"):
    f = line.rstrip("\n").split("\t"); gs[f[0]] = set(f[2:])

universe = expr.index[np.median(expr.values[:, uniq], axis=1) > 0]
E = expr.loc[universe]
R = np.apply_along_axis(rankdata, 0, E.values)          # within-sample ranks
R = (R - 1) / (R.shape[0] - 1)
Rdf = pd.DataFrame(R, index=universe, columns=E.columns)

def rank_score(genes):
    g = [x for x in genes if x in Rdf.index and x != "ESR1"]
    return Rdf.loc[g].mean(axis=0), len(g)

early = gs["HALLMARK_ESTROGEN_RESPONSE_EARLY"]; late = gs["HALLMARK_ESTROGEN_RESPONSE_LATE"]
sc = pd.DataFrame(index=expr.columns)
sc["ESR1"] = expr.loc["ESR1"]
sc["act_primary"], n_p = rank_score(early | late)
sc["act_early"], n_e = rank_score(early)
sc["act_late"], n_l = rank_score(late)
canon = ["PGR", "GREB1", "TFF1", "PDZK1", "MYB"]
X = expr.loc[canon]
mu, sd = X.loc[:, uniq].mean(axis=1), X.loc[:, uniq].std(axis=1)
sc["act_canon"] = ((X.sub(mu, axis=0)).div(sd, axis=0)).mean(axis=0)

# extra variables for P6-P8
sc["AR"] = expr.loc["AR"]; sc["FOXA1"] = expr.loc["FOXA1"]
adip = ["ADIPOQ", "PLIN1", "LEP", "CIDEA"]
A = expr.loc[adip]; am, asd = A.loc[:, uniq].mean(axis=1), A.loc[:, uniq].std(axis=1)
sc["adipose_proxy"] = ((A.sub(am, axis=0)).div(asd, axis=0)).mean(axis=0)
floor = expr.values.min()
sc["frac_detected"] = (expr.values > floor + 1e-6).mean(axis=0)
mt = [g for g in expr.index if g.startswith("MT-")]
rp = [g for g in expr.index if pd.Series([g]).str.match(r"^RP[LS]\d+[A-Z]?\d*$").iloc[0]]
sc["mt_median"] = expr.loc[mt].median(axis=0)
sc["rp_median"] = expr.loc[rp].median(axis=0)
sc["mean_expr"] = expr.mean(axis=0)
sc.to_parquet(OUT / "scores.parquet")
print(f"universe={len(universe)} genes; set sizes primary={n_p} early={n_e} late={n_l}; MT={len(mt)} RP={len(rp)}; floor={floor:.3f}")
print(sc.describe().T.round(3))
