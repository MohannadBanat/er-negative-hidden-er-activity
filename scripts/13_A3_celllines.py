"""Amendment A3: per-line table of expression (GSE337499) and TSS accessibility relative to GAPDH (GSE337500)."""
import sys, json, pathlib
import numpy as np, pandas as pd
from scipy import stats
O = pathlib.Path(sys.argv[1])
r = json.load(open(O / "A3_GSE337499_fpkm_extract.json")); a = json.load(open(O / "A3_GSE337500_atac_extract.json"))
lines = ["BT549", "HCC1599", "HCC1937", "HCC2157", "MDA_MB_231", "MDA_MB_453", "MDA_MB_468", "SUM185PE"]
rna = pd.DataFrame(r["fpkm"], index=r["columns"]); rna["line"] = [c.rsplit("_rep", 1)[0] for c in rna.index]
rna = np.log2(rna.groupby("line").mean() + 1).loc[lines]
at = pd.DataFrame(a).T; at["line"] = [k.split("_", 1)[1].rsplit("_rep", 1)[0].replace("BT_549", "BT549") for k in at.index]
rel = at[["ESR1", "AR", "FOXA1"]].div(at["GAPDH"], axis=0); rel["line"] = at["line"]
rel = rel.groupby("line").mean().loc[lines]
tab = rna.add_prefix("log2FPKM_").join(rel.add_prefix("ATAC_rel_GAPDH_"))
res = {"table": tab.round(3).to_dict(orient="index"),
       "spearman_ESR1_expr_vs_ESR1_TSS_access": [float(x) for x in stats.spearmanr(tab["log2FPKM_ESR1"], tab["ATAC_rel_GAPDH_ESR1"])],
       "spearman_AR_expr_vs_AR_TSS_access": [float(x) for x in stats.spearmanr(tab["log2FPKM_AR"], tab["ATAC_rel_GAPDH_AR"])],
       "note": "n = 8 lines, descriptive only; TFF1/PGR/GREB1 exploratory"}
tab.to_csv(O / "A3_cellline_table.csv"); json.dump(res, open(O / "A3_celllines.json", "w"), indent=1)
print(tab.round(2).to_string()); print(json.dumps({k: v for k, v in res.items() if k != "table"}, indent=1))
