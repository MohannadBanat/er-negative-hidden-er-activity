"""E4 (exploratory): does mean log2 expression track tumour biology across the cohort?"""
import sys, json, pathlib
import pandas as pd
from sklearn.metrics import roc_auc_score
D, O = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
sc = pd.read_parquet(O / "scores.parquet"); s = pd.read_parquet(D / "sampdesc.parquet").set_index("title").loc[sc.index]
u = s[~s.isRepl]; m = sc.loc[u.index]
res = {}
for f in ["mean_expr", "frac_detected"]:
    lb = u.pam50_subtype.isin(["LumA", "Basal"]); res[f"{f}_LumA_vs_Basal"] = roc_auc_score(u[lb].pam50_subtype == "LumA", m.loc[lb[lb].index, f])
    er = u.er_Status.isin(["0", "1"]); res[f"{f}_ERpos_vs_ERneg"] = roc_auc_score(u[er].er_Status == "1", m.loc[er[er].index, f])
    n = u[(u.er_Status == "0") & u.pam50_subtype.isin(["LumA", "LumB", "Basal"])]
    res[f"{f}_withinERneg_luminal_vs_basal_n{len(n)}"] = roc_auc_score(n.pam50_subtype.isin(["LumA", "LumB"]), m.loc[n.index, f])
json.dump(res, open(O / "exploratory_E4.json", "w"), indent=1); print(json.dumps(res, indent=1))
