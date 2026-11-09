"""Amendment A4 (2026-11-10): external cohort GSE25066 (GPL96). Post hoc. No outcome fields are read.
Usage: python3 -I 22_A4_external_GSE25066.py <series_matrix.txt.gz> <GPL96.annot.gz> <h.all.v7.0.symbols.gmt> <out dir>"""
import sys, json, gzip, io, pathlib
import numpy as np, pandas as pd
from scipy.stats import rankdata, mannwhitneyu
from statsmodels.stats.proportion import proportion_confint
from sklearn.metrics import cohen_kappa_score

SM, ANN, GMT, O = sys.argv[1], sys.argv[2], sys.argv[3], pathlib.Path(sys.argv[4])
KEEP = {"er_status_ihc", "her2_status", "source", "esr1_status", "erbb2_status", "pam50_class"}   # outcome fields are never parsed

# ---- sample annotation: characteristics rows are ragged, so parse "key: value" per sample
meta_lines, tab = [], []
with gzip.open(SM, "rt", errors="replace") as f:
    for line in f:
        (meta_lines if line.startswith("!") else tab).append(line)
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

# ---- expression
X = pd.read_csv(io.StringIO("".join(tab)), sep="\t", index_col=0)
X = X.loc[[i for i in X.index if isinstance(i, str) and not i.startswith("!")]].astype(float)
X = X[gsm]
logged = bool(np.nanmax(X.values) <= 100)
if not logged: X = np.log2(X.clip(lower=1))
ann = pd.read_csv(ANN, sep="\t", skiprows=27, usecols=[0, 2], dtype=str).dropna()
ann.columns = ["ID", "sym"]; ann = ann[~ann.sym.str.contains("///")].set_index("ID").sym
common = X.index.intersection(ann.index)
m = X.loc[common].mean(axis=1)
best = m.groupby(ann.loc[common]).idxmax()                      # probe with the highest mean, per gene
E = X.loc[best.values]; E.index = best.index
esr1_probe = best["ESR1"]

gs = {}
for line in open(GMT):
    f = line.rstrip("\n").split("\t"); gs[f[0]] = set(f[2:])
R = np.apply_along_axis(rankdata, 0, E.values); R = (R - 1) / (R.shape[0] - 1)
Rdf = pd.DataFrame(R, index=E.index, columns=E.columns)
def rank_score(genes):
    g = [x for x in genes if x in Rdf.index and x != "ESR1"]; return Rdf.loc[g].mean(axis=0), len(g)
early, late = gs["HALLMARK_ESTROGEN_RESPONSE_EARLY"], gs["HALLMARK_ESTROGEN_RESPONSE_LATE"]
sc = pd.DataFrame(index=E.columns)
sc["ESR1"] = E.loc["ESR1"]
sc["act_primary"], n_p = rank_score(early | late); sc["act_early"], n_e = rank_score(early); sc["act_late"], n_l = rank_score(late)
canon = ["PGR", "GREB1", "TFF1", "PDZK1", "MYB"]; canon_have = [g for g in canon if g in E.index]
C = E.loc[canon_have]; sc["act_canon"] = C.sub(C.mean(1), axis=0).div(C.std(1), axis=0).mean(axis=0)
sc["AR"], sc["FOXA1"] = E.loc["AR"], E.loc["FOXA1"]

neg = meta.index[meta.er_status_ihc == "N"]; pos = meta.index[meta.er_status_ihc == "P"]
T = {p: {c: float(np.percentile(sc.loc[pos, c], p)) for c in ["ESR1", "act_primary", "act_early", "act_late", "act_canon"]} for p in (1, 5, 10)}
wil = lambda k, n: [int(k), int(n), k / n] + [float(x) for x in proportion_confint(k, n, method="wilson")]
def newcombe(k1, n1, k2, n2):
    p1, p2 = k1 / n1, k2 / n2; l1, u1 = proportion_confint(k1, n1, method="wilson"); l2, u2 = proportion_confint(k2, n2, method="wilson")
    d = p1 - p2; return [d, d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)]
def groups(act="act_primary", pct=5):
    e = sc.loc[neg, "ESR1"] >= T[pct]["ESR1"]; a = sc.loc[neg, act] >= T[pct][act]
    return pd.Series(np.select([e & a, e & ~a, ~e & a], ["HEA", "silent_ESR1", "act_wo_ESR1"], "low_low"), index=neg)
G = groups(); n = len(neg); GR = ["HEA", "silent_ESR1", "act_wo_ESR1", "low_low"]
res = {"n_samples": len(gsm), "n_neg": n, "n_pos": len(pos), "logged_in_file": logged, "n_genes": int(E.shape[0]), "ESR1_probe": esr1_probe,
       "set_sizes": {"primary": n_p, "early": n_e, "late": n_l, "canon": canon_have}, "thresholds": T}

# V1
res["V1_groups"] = {g: wil(int((G == g).sum()), n) for g in GR}
k = res["V1_groups"]["HEA"][0]
res["V1_diff_vs_SCANB_HER2neg_11_165"] = newcombe(k, n, 11, 165)
res["V1_diff_vs_SCANB_all_20_241"] = newcombe(k, n, 20, 241)

# V2
defs = {"primary_5pct": int((G == "HEA").sum()), "primary_1pct": int((groups(pct=1) == "HEA").sum()), "primary_10pct": int((groups(pct=10) == "HEA").sum()),
        "early_only": int((groups("act_early") == "HEA").sum()), "late_only": int((groups("act_late") == "HEA").sum()), "canonical5": int((groups("act_canon") == "HEA").sum()),
        "ESR1_high_alone": int((sc.loc[neg, "ESR1"] >= T[5]["ESR1"]).sum()), "deposited_esr1_status_P": int((meta.loc[neg, "esr1_status"] == "P").sum())}
res["V2_counts"] = {d: wil(v, n) for d, v in defs.items()}
vals = list(defs.values()); res["V2_max_over_min"] = (max(vals) / min(vals)) if min(vals) > 0 else None
res["V2_min_max"] = [min(vals), max(vals)]
res["V2_kappa_HEA_vs_deposited_esr1"] = float(cohen_kappa_score((G == "HEA").values, (meta.loc[neg, "esr1_status"] == "P").values))

# V3
res["V3_pam50_by_group"] = pd.crosstab(G, meta.loc[neg, "pam50_class"]).reindex(GR).fillna(0).astype(int).to_dict("index")
res["V3_erbb2_by_group"] = pd.crosstab(G, meta.loc[neg, "erbb2_status"]).reindex(GR).fillna(0).astype(int).to_dict("index")
res["V3_her2_clinical_by_group"] = pd.crosstab(G, meta.loc[neg, "her2_status"].fillna("NA")).reindex(GR).fillna(0).astype(int).to_dict("index")
for gene in ["AR", "FOXA1"]:
    a, b = sc.loc[G.index[G == "act_wo_ESR1"], gene], sc.loc[G.index[G == "low_low"], gene]
    if len(a) and len(b):
        U, p = mannwhitneyu(a, b, alternative="two-sided")
        res[f"V3_{gene}_actwo_vs_lowlow"] = {"n": [len(a), len(b)], "median": [float(a.median()), float(b.median())], "p": float(p), "rank_biserial": float(2 * U / (len(a) * len(b)) - 1)}
hea = G.index[G == "HEA"]; pam = meta.loc[hea, "pam50_class"]
res["V3_HEA_luminal_or_normal"] = [int(pam.isin(["LumA", "LumB", "Normal"]).sum()), len(hea)]

# V4 site
ct = pd.crosstab(meta.loc[neg, "source"], G == "HEA")
res["V4_site"] = {s_: wil(int(ct.loc[s_].get(True, 0)), int(ct.loc[s_].sum())) for s_ in ct.index}
rng = np.random.default_rng(20261025); obs = ct.values; lab = (G == "HEA").values.copy(); src = meta.loc[neg, "source"].values
def stat(l): return pd.crosstab(src, l).pipe(lambda c: ((c - np.outer(c.sum(1), c.sum(0)) / c.values.sum()) ** 2 / (np.outer(c.sum(1), c.sum(0)) / c.values.sum())).values.sum())
s0 = stat(lab); res["V4_site_perm_p"] = float((1 + sum(stat(rng.permutation(lab)) >= s0 - 1e-12 for _ in range(9999))) / 10000) if lab.sum() > 0 else None

# decision rules (amendment A4, section 6)
d = res["V1_diff_vs_SCANB_HER2neg_11_165"]
ar = res.get("V3_AR_actwo_vs_lowlow")
res["decision"] = {
    "prevalence_consistent": bool(d[1] <= 0 <= d[2]),
    "definition_dependence_replicated": bool(res["V2_max_over_min"] is None or res["V2_max_over_min"] >= 3),
    "composition_a_HEA_half_luminal_or_normal": bool(len(hea) > 0 and res["V3_HEA_luminal_or_normal"][0] / len(hea) >= 0.5),
    "composition_b_AR_higher_in_act_wo_ESR1": bool(ar is not None and ar["p"] < 0.05 and ar["rank_biserial"] > 0)}
res["decision"]["composition_replicated"] = res["decision"]["composition_a_HEA_half_luminal_or_normal"] and res["decision"]["composition_b_AR_higher_in_act_wo_ESR1"]
json.dump(res, open(O / "A4_external_GSE25066.json", "w"), indent=1)
out = sc.loc[neg].copy(); out["group"] = G; out = out.join(meta.loc[neg, ["pam50_class", "her2_status", "erbb2_status", "esr1_status", "source"]])
out.to_csv(O / "A4_GSE25066_neg_tumours.csv")
sc.join(meta[["er_status_ihc"]]).to_csv(O / "A4_GSE25066_scores_all.csv")
print(json.dumps(res, indent=1))
