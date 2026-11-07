"""Final manuscript figures for MDPI Cancers: no in-figure titles (captions carry them), (a)/(b) panel
labels, Liberation Sans (Arial metrics) 8 pt at final size, 13.8 cm wide (MDPI body column), 600 dpi PNG + vector PDF + TIFF,
labels placed explicitly so nothing overlaps. Data and numbers are unchanged from scripts 03, 09, 11, 13."""
import sys, json, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint
from scipy import stats

D, O = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
FIG = O / "figures_final"; FIG.mkdir(exist_ok=True)
r = json.load(open(O / "results.json")); t = pd.read_csv(O / "neg_tumours_table.csv", index_col=0)
sc = pd.read_parquet(O / "scores.parquet"); s = pd.read_parquet(D / "sampdesc.parquet").set_index("title")
INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#6f6d68", "#e1e0d9", "#c3c2b7"
CM = 1 / 2.54; W = 13.8 * CM
plt.rcParams.update({"font.family": "Liberation Sans", "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5,
                     "ytick.labelsize": 7.5, "legend.fontsize": 7.5, "axes.edgecolor": "#8a8984", "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.linewidth": 0.7, "xtick.major.width": 0.7, "ytick.major.width": 0.7,
                     "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white", "pdf.fonttype": 42})
GC = {"HEA": "#2a78d6", "silent_ESR1": "#eb6834", "act_wo_ESR1": "#1baf7a", "true_neg": "#eda100"}
GL = {"HEA": "Hidden ER activity", "silent_ESR1": "Silent ESR1", "act_wo_ESR1": "Activity without ESR1", "true_neg": "Truly ER-negative"}
GM = {"HEA": "o", "silent_ESR1": "s", "act_wo_ESR1": "^", "true_neg": "D"}
T = r["thresholds"]["5"]
def panel(ax, lab): ax.text(-0.13, 1.03, lab, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="left")
def save(fig, name):
    for ext, kw in [("png", {"dpi": 600}), ("pdf", {}), ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})]:
        fig.savefig(FIG / f"{name}.{ext}", **kw)  # constrained layout: page size is exactly the figsize (13.8 cm wide)
    plt.close(fig)

# Figure 1
u = s[~s.isRepl]; pos = u[u.er_Status == "1"].index
fig, ax = plt.subplots(layout="constrained", figsize=(W, 9.5 * CM))
ax.scatter(sc.loc[pos, "ESR1"], sc.loc[pos, "act_primary"], s=3, c=BASE, lw=0, alpha=.7, rasterized=True, label=f"IHC ER-positive (n = {len(pos):,})", zorder=1)
for g in ["true_neg", "act_wo_ESR1", "silent_ESR1", "HEA"]:
    m = t.group == g
    ax.scatter(t.loc[m, "ESR1"], t.loc[m, "act_primary"], s=16, c=GC[g], marker=GM[g], edgecolor="white", lw=.5, zorder=3, label=f"{GL[g]} (n = {m.sum()})")
ax.axvline(T["ESR1"], color=INK2, lw=.7, ls=(0, (4, 3)), zorder=2); ax.axhline(T["act_primary"], color=INK2, lw=.7, ls=(0, (4, 3)), zorder=2)
ax.set_xlabel("ESR1 expression (log2 FPKM)"); ax.set_ylabel("ER-activity score (rank-based, ESR1 excluded)")
ax.set_ylim(0.40, 0.73); ax.set_xlim(-1.6, 10)
ax.annotate("ESR1 threshold", (T["ESR1"], 0.41), xytext=(4, 0), textcoords="offset points", fontsize=7, color=INK2, va="bottom")
ax.annotate("Activity threshold", (9.95, T["act_primary"]), xytext=(0, 3), textcoords="offset points", fontsize=7, color=INK2, ha="right", va="bottom", bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=.85))
ax.grid(color=GRID, lw=.4); ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper left", handletextpad=.3, borderaxespad=.2, markerscale=1.2)
save(fig, "Figure1")

# Figure 2: prevalence by definition
n = r["n_neg"]; rows = []
def add(lab, k): lo, hi = proportion_confint(k, n, method="wilson"); rows.append((lab, k / n, lo, hi, k))
add("HEA, 5th-percentile threshold (primary)", r["P4"]["5"][0]); add("HEA, 1st-percentile threshold", r["P4"]["1"][0]); add("HEA, 10th-percentile threshold", r["P4"]["10"][0])
for k, lab in [("HEA_early", "HEA, Hallmark Early set only"), ("HEA_late", "HEA, Hallmark Late set only"), ("HEA_canon", "HEA, five canonical ER targets"),
               ("ESR1_high", "ESR1 high alone"), ("er_MGC", "Deposited multigene classifier"), ("er_SGC", "Deposited single-gene classifier")]:
    add(lab, r["P3_n_pos"][k])
fig, ax = plt.subplots(layout="constrained", figsize=(W, 7.5 * CM))
for i, (lab, p, lo, hi, k) in enumerate(rows):
    ax.plot([lo * 100, hi * 100], [i, i], color=GC["HEA"], lw=1.6, solid_capstyle="round")
    ax.plot(p * 100, i, "o", ms=5.5, color=GC["HEA"], mec="white", mew=.8)
    ax.text(hi * 100 + 1.0, i, f"{k}/{n}", va="center", fontsize=7, color=INK2)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([x[0] for x in rows], color=INK); ax.invert_yaxis()
for yline in (2.5, 5.5): ax.axhline(yline, color=GRID, lw=.7)
ax.set_xlabel("Tumours called ER-active among IHC ER-negative tumours\n(%, Wilson 95% CI)"); ax.set_xlim(0, 56)
ax.grid(axis="x", color=GRID, lw=.4); ax.set_axisbelow(True); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
save(fig, "Figure2")

# Figure 3: PAM50 by group
PAM = ["LumA", "LumB", "Her2", "Basal", "Normal"]; PC = dict(zip(PAM, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
PLAB = {"LumA": "Luminal A", "LumB": "Luminal B", "Her2": "HER2-enriched", "Basal": "Basal-like", "Normal": "Normal-like"}
order = ["HEA", "silent_ESR1", "act_wo_ESR1", "true_neg"]
ct = pd.crosstab(t.group, t.pam50_subtype).reindex(index=order, columns=PAM).fillna(0).astype(int); fr = ct.div(ct.sum(axis=1), axis=0)
fig, ax = plt.subplots(layout="constrained", figsize=(W, 5.6 * CM))
for i, g in enumerate(order):
    left = 0
    for p in PAM:
        w = fr.loc[g, p]
        if w > 0:
            ax.barh(i, w - .004, left=left + .002, color=PC[p], height=.64, edgecolor="none")
            if w >= .05:  # label inside when there is room
                ax.text(left + w / 2, i, int(ct.loc[g, p]), ha="center", va="center", fontsize=7, color="#0b0b0b" if p in ("Basal", "Normal") else "white")
            else:          # tiny segments: label just right of the bar end
                ax.text(1.012, i, f"{PLAB[p]} {int(ct.loc[g, p])}", ha="left", va="center", fontsize=6.5, color=INK2)
        left += w
ax.set_yticks(range(4)); ax.set_yticklabels([f"{GL[g]} (n = {int(ct.loc[g].sum())})" for g in order], color=INK)
ax.invert_yaxis(); ax.set_xlim(0, 1); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
h = [plt.Rectangle((0, 0), 1, 1, color=PC[p]) for p in PAM]
ax.legend(h, [PLAB[p] for p in PAM], ncol=5, frameon=False, loc="lower center", bbox_to_anchor=(.5, 1.0), handlelength=1.0, columnspacing=1.2)
ax.set_xlabel("Share of group (PAM50 subtype); numbers are tumour counts")
save(fig, "Figure3")

# Figure 4: miRNA paired differences, q-values in a fixed row above each series
a = json.load(open(O / "A2_GSE40049.json")); b = json.load(open(O / "A2_GSE38167.json"))
cp = pd.read_csv(O / "A2_GSE40049_cpm.csv", index_col=0); v38 = pd.read_csv(O / "A2_GSE38167_values.csv", index_col=0)
mirs = ["miR-18a", "miR-22", "miR-206", "miR-221", "miR-222"]; pre = {m: "hsa-mir-" + m.split("-")[1] for m in mirs}
def d40(m):
    Tt = cp[cp.type == "T"]; N = cp[cp.type == "N"]; pts = sorted(set(Tt.patient) & set(N.patient))
    return np.array([Tt[Tt.patient == p][pre[m]].iloc[0] - N[N.patient == p][pre[m]].iloc[0] for p in pts])
def d38(m):
    pts = sorted(set(v38.patient[v38.type == "IDC"]) & set(v38.patient[v38.type == "NAT"]))
    return np.array([v38[(v38.patient == p) & (v38.type == "IDC")][m].iloc[0] - v38[(v38.patient == p) & (v38.type == "NAT")][m].iloc[0] for p in pts])
C1, C2 = "#2a78d6", "#eb6834"
fig, ax = plt.subplots(layout="constrained", figsize=(W, 8 * CM)); rng = np.random.default_rng(1)
qfmt = lambda q: "q < 0.001" if q < .001 else (f"q = {q:.3f}" if q < .01 else f"q = {q:.2f}")
for i, m in enumerate(mirs):
    for off, d, res, col, row in [(-0.18, d40(m), a["paired"][pre[m]], C1, 7.6), (0.18, d38(m), b["IDC_vs_NAT"][m], C2, 6.9)]:
        ax.scatter(i + off + rng.uniform(-.05, .05, len(d)), d, s=6, color=col, alpha=.35, lw=0)
        med = res.get("median_log2FC", res.get("median_diff")); lo, hi = res["ci"]
        ax.plot([i + off] * 2, [lo, hi], color=col, lw=1.8, solid_capstyle="round")
        ax.plot(i + off, med, "o", ms=5.5, color=col, mec="white", mew=.8)
        ax.text(i, row, qfmt(res["q_BH"]), ha="center", va="center", fontsize=6.5, color=col)
ax.axhline(0, color=INK2, lw=.7); ax.set_xticks(range(5)); ax.set_xticklabels(mirs, color=INK)
ax.set_ylim(-6.6, 8.1); ax.set_xlim(-.6, 4.6); ax.set_yticks(range(-6, 7, 2))
ax.set_ylabel("Tumour minus paired normal (log2)"); ax.grid(axis="y", color=GRID, lw=.4); ax.set_axisbelow(True)
h = [plt.Line2D([], [], marker="o", ls="", color=C1, ms=5), plt.Line2D([], [], marker="o", ls="", color=C2, ms=5)]
ax.legend(h, ["GSE40049, small RNA-seq (14 pairs)", "GSE38167, miRNA array (21 pairs)"], frameon=False, loc="upper center", bbox_to_anchor=(.5, -0.09), ncol=2, borderaxespad=0)
save(fig, "Figure4")

# Figure 5: two panels, explicit label offsets (points) chosen so no label overlaps a point or another label
c = pd.read_csv(O / "A3_cellline_table.csv", index_col=0)
NAME = {"BT549": "BT-549", "HCC1599": "HCC1599", "HCC1937": "HCC1937", "HCC2157": "HCC2157", "MDA_MB_231": "MDA-MB-231",
        "MDA_MB_453": "MDA-MB-453", "MDA_MB_468": "MDA-MB-468", "SUM185PE": "SUM185PE"}
OFF = {"ESR1": {"HCC1937": (5, 0, "left"), "MDA_MB_468": (5, 0, "left"), "HCC1599": (-5, 6, "right"), "SUM185PE": (5, 0, "left"),
                "MDA_MB_453": (5, 4, "left")},
       "AR": {"MDA_MB_453": (-5, 6, "right"), "SUM185PE": (0, -9, "center"), "BT549": (5, 0, "left"), "HCC1599": (5, 0, "left")}}
GOFF = {"ESR1": (8, 14), "AR": (45, 6)}
GROUPLAB = {"ESR1": "BT-549, HCC2157,\nMDA-MB-231", "AR": "HCC1937, HCC2157,\nMDA-MB-231, MDA-MB-468"}
fig, axs = plt.subplots(1, 2, layout="constrained", figsize=(W, 7 * CM))
for ax, g, lab in [(axs[0], "ESR1", "(a)"), (axs[1], "AR", "(b)")]:
    x, y = c[f"ATAC_rel_GAPDH_{g}"], c[f"log2FPKM_{g}"]
    ax.scatter(x, y, s=22, color=C1, edgecolor="white", lw=.6, zorder=3)
    for ln, (dx, dy, ha) in OFF[g].items():
        ax.annotate(NAME[ln], (x[ln], y[ln]), xytext=(dx, dy), textcoords="offset points", fontsize=7, color=INK, ha=ha, va="center")
    low = [ln for ln in c.index if ln not in OFF[g]]
    ax.annotate(GROUPLAB[g], (max(x[low]), max(y[low])), xytext=GOFF[g], textcoords="offset points", fontsize=6.5, color=INK2, ha="left", va="bottom",
                arrowprops=dict(arrowstyle="-", lw=.5, color=MUTED, shrinkA=0, shrinkB=3))
    rho = stats.spearmanr(x, y)[0]
    ax.text(.98, .03, f"Spearman ρ = {rho:.2f} (n = 8)", transform=ax.transAxes, ha="right", va="bottom", fontsize=7, color=INK2)
    ax.set_xlabel(f"ATAC signal at {g} TSS ±1 kb\n(relative to GAPDH)"); ax.set_ylabel(f"{g} expression, log2(FPKM + 1)")
    ax.margins(x=.12, y=.12); ax.grid(color=GRID, lw=.4); ax.set_axisbelow(True); panel(ax, lab)
axs[1].set_xlim(-0.03, 0.66)
fig.get_layout_engine().set(wspace=0.08); save(fig, "Figure5")

# Figure S1
rp = s[s.isRepl].index; op = [x[:-4] for x in rp]
cross = s.loc[rp, "instrument_model"].values != s.loc[op, "instrument_model"].values
fig, axs = plt.subplots(1, 2, layout="constrained", figsize=(W, 7 * CM))
for ax, col, lab, pl in [(axs[0], "ESR1", "ESR1 (log2 FPKM)", "(a)"), (axs[1], "act_primary", "ER-activity score", "(b)")]:
    x, y = sc.loc[op, col].values, sc.loc[rp, col].values
    ax.scatter(x[~cross], y[~cross], s=9, c=C1, lw=0, label=f"Same platform (n = {(~cross).sum()})")
    ax.scatter(x[cross], y[cross], s=11, c=C2, marker="^", lw=0, label=f"Cross-platform (n = {cross.sum()})")
    lo, hi = min(x.min(), y.min()), max(x.max(), y.max()); ax.plot([lo, hi], [lo, hi], color=MUTED, lw=.6, zorder=0)
    ax.axvline(T[col], color=INK2, lw=.5, ls=(0, (4, 3))); ax.axhline(T[col], color=INK2, lw=.5, ls=(0, (4, 3)))
    ic = r["P2"][f"{col}_all"]
    ax.text(.03, .97, f"ICC {ic['icc']:.3f} (95% CI {ic['ci'][0]:.3f}–{ic['ci'][1]:.3f})", transform=ax.transAxes, va="top", fontsize=7, color=INK2,
            bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"), zorder=5)
    ax.set_xlabel(f"Original library: {lab}"); ax.set_ylabel(f"Technical replicate: {lab}"); ax.grid(color=GRID, lw=.4); ax.set_axisbelow(True); panel(ax, pl)
axs[1].legend(*axs[0].get_legend_handles_labels(), frameon=False, loc="lower right", borderaxespad=.2)
fig.get_layout_engine().set(wspace=0.08); save(fig, "FigureS1")
print(sorted(p.name for p in FIG.iterdir()))
