"""Step 6: manuscript figures (static PNG + PDF). Palette validated with the dataviz validator."""
import sys, json, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint

D, O = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); FIG = O / "figures"; FIG.mkdir(exist_ok=True)
r = json.load(open(O / "results.json")); t = pd.read_csv(O / "neg_tumours_table.csv", index_col=0)
sc = pd.read_parquet(O / "scores.parquet"); s = pd.read_parquet(D / "sampdesc.parquet").set_index("title")
INK, INK2, MUTED, GRID, BASE, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": BASE, "axes.labelcolor": INK2,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})
GC = {"HEA": "#2a78d6", "silent_ESR1": "#eb6834", "act_wo_ESR1": "#1baf7a", "true_neg": "#eda100"}
GL = {"HEA": "Hidden ER activity", "silent_ESR1": "Silent ESR1", "act_wo_ESR1": "Activity without ESR1", "true_neg": "Truly ER-negative"}
GM = {"HEA": "o", "silent_ESR1": "s", "act_wo_ESR1": "^", "true_neg": "D"}
T = r["thresholds"]["5"]
def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight"); fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight"); plt.close(fig)

# Figure 1: ESR1 vs activity
u = s[~s.isRepl]; pos = u[u.er_Status == "1"].index
fig, ax = plt.subplots(figsize=(6.2, 4.6))
ax.scatter(sc.loc[pos, "ESR1"], sc.loc[pos, "act_primary"], s=6, c=BASE, lw=0, alpha=.6, label=f"IHC ER-positive (n={len(pos):,})", zorder=1)
for g in ["true_neg", "act_wo_ESR1", "silent_ESR1", "HEA"]:
    m = t.group == g
    ax.scatter(t.loc[m, "ESR1"], t.loc[m, "act_primary"], s=26, c=GC[g], marker=GM[g], edgecolor=SURF, lw=.8, zorder=3,
               label=f"{GL[g]} (n={m.sum()})")
ax.axvline(T["ESR1"], color=INK2, lw=.8, ls=(0, (4, 3)), zorder=2); ax.axhline(T["act_primary"], color=INK2, lw=.8, ls=(0, (4, 3)), zorder=2)
ax.text(T["ESR1"] + .1, ax.get_ylim()[0] + .004, "5th percentile of\nIHC ER-positive", color=INK2, fontsize=7.5, va="bottom")
ax.set_xlabel("ESR1 expression (log2)"); ax.set_ylabel("ER-activity score (Hallmark early+late, ESR1 removed)")
ax.grid(color=GRID, lw=.5); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=7.5, loc="upper left", labelcolor=INK)
ax.set_title("IHC ER-negative tumours (n=241) placed on the ER-positive distribution", loc="left", color=INK, fontsize=10)
save(fig, "Figure1_ESR1_vs_activity")

# Figure 2: PAM50 by group (100% stacked horizontal)
PAM = ["LumA", "LumB", "Her2", "Basal", "Normal"]; PC = dict(zip(PAM, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
PLAB = {"LumA": "Luminal A", "LumB": "Luminal B", "Her2": "HER2-enriched", "Basal": "Basal-like", "Normal": "Normal-like"}
order = ["HEA", "silent_ESR1", "act_wo_ESR1", "true_neg"]
ct = pd.crosstab(t.group, t.pam50_subtype).reindex(index=order, columns=PAM).fillna(0)
fr = ct.div(ct.sum(1), axis=0)
fig, ax = plt.subplots(figsize=(6.6, 2.8))
for i, g in enumerate(order):
    left = 0
    for p in PAM:
        w = fr.loc[g, p]
        if w > 0:
            ax.barh(i, w - .004, left=left + .002, color=PC[p], height=.62, edgecolor="none")
            if ct.loc[g, p] >= 2 and w > .06:
                ax.text(left + w / 2, i, int(ct.loc[g, p]), ha="center", va="center", fontsize=7.5, color="#0b0b0b" if p == "Basal" else "#ffffff")
        left += w
ax.set_yticks(range(4)); ax.set_yticklabels([f"{GL[g]} (n={int(ct.loc[g].sum())})" for g in order], color=INK)
ax.invert_yaxis(); ax.set_xlim(0, 1); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
h = [plt.Rectangle((0, 0), 1, 1, color=PC[p]) for p in PAM]
ax.legend(h, [PLAB[p] for p in PAM], ncol=5, frameon=False, fontsize=7.5, loc="lower left", bbox_to_anchor=(0, 1.0), labelcolor=INK)
ax.set_xlabel("Share of group (PAM50 subtype; numbers are tumour counts)")
save(fig, "Figure3_PAM50_by_group")

# Figure 3: prevalence by definition (dot + Wilson CI)
n = r["n_neg"]; rows = []
def add(lab, k): lo, hi = proportion_confint(k, n, method="wilson"); rows.append((lab, k / n, lo, hi, k))
add("HEA, primary score, 5th pct (primary)", r["P4"]["5"][0]); add("HEA, primary score, 1st pct", r["P4"]["1"][0]); add("HEA, primary score, 10th pct", r["P4"]["10"][0])
for k, lab in [("HEA_early", "HEA, Hallmark early only"), ("HEA_late", "HEA, Hallmark late only"), ("HEA_canon", "HEA, 5 canonical targets"),
               ("ESR1_high", "ESR1 high alone"), ("er_MGC", "Deposited multigene classifier"), ("er_SGC", "Deposited single-gene classifier")]:
    add(lab, r["P3_n_pos"][k])
fig, ax = plt.subplots(figsize=(6.4, 3.6))
for i, (lab, p, lo, hi, k) in enumerate(rows):
    ax.plot([lo * 100, hi * 100], [i, i], color=GC["HEA"], lw=2, solid_capstyle="round")
    ax.plot(p * 100, i, "o", ms=8, color=GC["HEA"], mec=SURF, mew=1.5)
    ax.text(hi * 100 + 1.2, i, f"{k}/{n}", va="center", fontsize=7.5, color=INK2)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r_[0] for r_ in rows], color=INK); ax.invert_yaxis()
ax.axhline(2.5, color=GRID, lw=.8); ax.axhline(5.5, color=GRID, lw=.8)
ax.set_xlabel("Tumours called ER-active among IHC ER-negative (%, Wilson 95% CI)"); ax.set_xlim(0, 55)
ax.grid(axis="x", color=GRID, lw=.5); ax.set_axisbelow(True); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
save(fig, "Figure2_prevalence_by_definition")

# Supplementary Figure S1: replicate agreement
rp = s[s.isRepl].index; op = [x[:-4] for x in rp]
cross = s.loc[rp, "instrument_model"].values != s.loc[op, "instrument_model"].values
fig, axs = plt.subplots(1, 2, figsize=(7, 3.3))
for ax, col, lab in [(axs[0], "ESR1", "ESR1 (log2)"), (axs[1], "act_primary", "ER-activity score")]:
    x, y = sc.loc[op, col].values, sc.loc[rp, col].values
    ax.scatter(x[~cross], y[~cross], s=14, c=GC["HEA"], lw=0, label=f"Same platform (n={(~cross).sum()})")
    ax.scatter(x[cross], y[cross], s=18, c=GC["silent_ESR1"], marker="^", lw=0, label=f"Cross-platform (n={cross.sum()})")
    lo, hi = min(x.min(), y.min()), max(x.max(), y.max()); ax.plot([lo, hi], [lo, hi], color=MUTED, lw=.8, zorder=0)
    ax.axvline(T[col], color=INK2, lw=.6, ls=(0, (4, 3))); ax.axhline(T[col], color=INK2, lw=.6, ls=(0, (4, 3)))
    ic = r["P2"][f"{col}_all"]; ax.set_title(f"{lab}: ICC {ic['icc']:.3f} ({ic['ci'][0]:.3f}–{ic['ci'][1]:.3f})", loc="left", fontsize=8.5, color=INK)
    ax.set_xlabel("Original library"); ax.set_ylabel("Technical replicate"); ax.grid(color=GRID, lw=.5); ax.set_axisbelow(True)
axs[0].legend(frameon=False, fontsize=7, labelcolor=INK)
fig.tight_layout(); save(fig, "FigureS1_replicate_agreement")
print(sorted(p.name for p in FIG.iterdir()))
