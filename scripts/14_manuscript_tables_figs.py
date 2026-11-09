"""Table 1 (characteristics of IHC ER-negative tumours by group) and Figures 4-5 (miRNA, cell lines)."""
import sys, json, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy import stats
D, O = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); FIG = O / "figures"
t = pd.read_csv(O / "neg_tumours_table.csv", index_col=0)
s = pd.read_parquet(D / "sampdesc.parquet").set_index("title").loc[t.index]
for v in ["chemo_treated","endocrine_treated","lymphNode_Status","her2_Status","pgr_Status","nhg","pam50_subtype","instrument_model"]:
    t[v] = s[v].astype(str)
t["chemo"] = t.chemo_treated; t["endo"] = t.endocrine_treated
order = ["HEA", "silent_ESR1", "act_wo_ESR1", "true_neg"]
GL = {"HEA": "Hidden ER activity", "silent_ESR1": "Silent ESR1", "act_wo_ESR1": "Activity without ESR1", "true_neg": "Concordant ER-negative"}
rows = []
def cat(var, lev, lab):
    r = {"Characteristic": lab}
    for g in order + ["All"]:
        sub = t if g == "All" else t[t.group == g]; n = sub[var].isin(lev if isinstance(lev, list) else [lev]).sum(); k = (~sub[var].astype(str).isin(["NA","nan","None"])).sum()
        r[g] = f"{n} ({100*n/max(k,1):.0f}%)"
    rows.append(r)
def cont(var, lab):
    r = {"Characteristic": lab}
    for g in order + ["All"]:
        x = (t if g == "All" else t[t.group == g])[var].dropna()
        r[g] = f"{x.median():.0f} ({x.quantile(.25):.0f}–{x.quantile(.75):.0f})"
    rows.append(r)
rows.append({"Characteristic": "n", **{g: str((t.group == g).sum()) for g in order}, "All": str(len(t))})
cont("ageAtDx", "Age, years, median (IQR)"); cont("tumor_size", "Tumour size, mm, median (IQR)")
cat("lymphNode_Status", "NodePositive", "Node-positive"); cat("nhg", "G3", "Grade 3")
cat("her2_Status", "1", "IHC/ISH HER2-positive"); cat("pgr_Status", "1", "IHC PgR-positive")
for p, lab in [("LumA", "PAM50 Luminal A"), ("LumB", "PAM50 Luminal B"), ("Her2", "PAM50 HER2-enriched"), ("Basal", "PAM50 Basal-like"), ("Normal", "PAM50 Normal-like")]:
    cat("pam50_subtype", p, lab)
cat("chemo", "1", "Chemotherapy"); cat("endo", "1", "Endocrine therapy")
cat("instrument_model", "NextSeq 500", "Sequenced on NextSeq 500")
tab1 = pd.DataFrame(rows).rename(columns=GL); tab1.to_csv(O / "Table1.csv", index=False); print(tab1.to_string(index=False))

INK, INK2, MUTED, GRID, BASE, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": BASE, "axes.labelcolor": INK2, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})
C1, C2 = "#2a78d6", "#eb6834"
# Figure 4: paired tumour-normal differences for the 5 candidates in both datasets (dot = median, whisker = bootstrap CI, light dots = pairs)
a = json.load(open(O / "A2_GSE40049.json")); b = json.load(open(O / "A2_GSE38167.json"))
cp = pd.read_csv(O / "A2_GSE40049_cpm.csv", index_col=0); v38 = pd.read_csv(O / "A2_GSE38167_values.csv", index_col=0)
mirs = ["miR-18a", "miR-22", "miR-206", "miR-221", "miR-222"]; pre = {m: "hsa-mir-" + m.split("-")[1] for m in mirs}
def d40(m):
    T = cp[cp.type == "T"]; N = cp[cp.type == "N"]; pts = sorted(set(T.patient) & set(N.patient))
    return np.array([T[T.patient == p][pre[m]].iloc[0] - N[N.patient == p][pre[m]].iloc[0] for p in pts])
def d38(m):
    pts = sorted(set(v38.patient[v38.type == "IDC"]) & set(v38.patient[v38.type == "NAT"]))
    return np.array([v38[(v38.patient == p) & (v38.type == "IDC")][m].iloc[0] - v38[(v38.patient == p) & (v38.type == "NAT")][m].iloc[0] for p in pts])
fig, ax = plt.subplots(figsize=(6.6, 3.4)); rng = np.random.default_rng(1)
for i, m in enumerate(mirs):
    for off, d, res, col, lab in [(-0.17, d40(m), a["paired"][pre[m]], C1, "GSE40049 (small RNA-seq, 14 pairs)"),
                                  (0.17, d38(m), b["IDC_vs_NAT"][m], C2, "GSE38167 (array, 21 pairs)")]:
        ax.scatter(i + off + rng.uniform(-.05, .05, len(d)), d, s=7, color=col, alpha=.35, lw=0)
        med = res.get("median_log2FC", res.get("median_diff")); lo, hi = res["ci"]
        ax.plot([i + off] * 2, [lo, hi], color=col, lw=2, solid_capstyle="round")
        ax.plot(i + off, med, "o", ms=7, color=col, mec=SURF, mew=1.2, label=lab if i == 0 else None)
        q = res["q_BH"]; lab_q = "q<0.001" if q < .001 else (f"q={q:.3f}" if q < .01 else f"q={q:.2f}")
        ax.text(i + off, max(hi, np.max(d)) + (.35 if off < 0 else .9), lab_q, ha="center", fontsize=6.5, color=INK2)
ax.axhline(0, color=INK2, lw=.8); ax.set_xticks(range(5)); ax.set_xticklabels(mirs, color=INK)
ax.set_ylabel("Tumour − paired normal (log2)"); ax.grid(axis="y", color=GRID, lw=.5); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=7.5, loc="lower left", labelcolor=INK)
fig.savefig(FIG / "Figure4_ESR1_targeting_miRNAs.png", dpi=300, bbox_inches="tight"); fig.savefig(FIG / "Figure4_ESR1_targeting_miRNAs.pdf", bbox_inches="tight"); plt.close(fig)
# Figure 5: cell lines - expression vs accessibility, two panels
c = pd.read_csv(O / "A3_cellline_table.csv", index_col=0)
fig, axs = plt.subplots(1, 2, figsize=(7, 3.2))
for ax, g in [(axs[0], "ESR1"), (axs[1], "AR")]:
    x, y = c[f"ATAC_rel_GAPDH_{g}"], c[f"log2FPKM_{g}"]
    ax.scatter(x, y, s=40, color=C1, edgecolor=SURF, lw=1)
    low = [ln for ln in c.index if y[ln] < 0.1 and x[ln] < 0.06]
    for ln in c.index:
        if ln not in low: ax.annotate(ln.replace("_", "-"), (x[ln], y[ln]), xytext=(4, 3), textcoords="offset points", fontsize=7, color=INK2)
    if low: ax.annotate(", ".join(l.replace("_", "-") for l in low), (max(x[low]), 0), xytext=(6, 10), textcoords="offset points", fontsize=6.5, color=INK2)
    rho = stats.spearmanr(x, y)[0]
    ax.set_title(f"{g} (Spearman ρ = {rho:.2f}, n = 8)", loc="left", fontsize=8.5, color=INK)
    ax.set_xlabel(f"ATAC signal at {g} TSS ±1 kb / GAPDH"); ax.set_ylabel(f"{g} log2(FPKM + 1)"); ax.grid(color=GRID, lw=.5); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(FIG / "Figure5_cellline_ESR1_AR_locus.png", dpi=300, bbox_inches="tight"); fig.savefig(FIG / "Figure5_cellline_ESR1_AR_locus.pdf", bbox_inches="tight"); plt.close(fig)
print("figures ok")
