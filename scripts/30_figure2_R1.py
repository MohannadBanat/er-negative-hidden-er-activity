"""Revision 1: Figure 2 redrawn in three labelled families (Reviewer 1, comment 6), with the 2.5th and 7.5th percentiles added.
Usage: python3 -I 30_figure2_R1.py <results dir> <out dir>"""
import sys, json, pathlib
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint
R, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); OUT.mkdir(exist_ok=True)
r = json.load(open(R / "results.json")); a = json.load(open(R / "A5_reviewer_analyses.json"))["R5"]["scanb"]["counts"]
INK, INK2, GRID, BLUE = "#0b0b0b", "#52514e", "#e1e0d9", "#2a78d6"
CM = 1 / 2.54; W = 13.8 * CM
plt.rcParams.update({"font.family": "Liberation Sans", "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "axes.edgecolor": "#8a8984",
                     "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.7,
                     "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white", "pdf.fonttype": 42})
n = r["n_neg"]; P = r["P3_n_pos"]
assert a["5"][0] == r["P4"]["5"][0] == 20 and a["1"][0] == r["P4"]["1"][0] and a["10"][0] == r["P4"]["10"][0]
groups = [("Threshold, same definition", [("1st percentile", a["1"][0]), ("2.5th percentile", a["2.5"][0]), ("5th percentile (primary)", a["5"][0]), ("7.5th percentile", a["7.5"][0]), ("10th percentile", a["10"][0])]),
          ("Same construct, different signature", [("Hallmark Early set only", P["HEA_early"]), ("Hallmark Late set only", P["HEA_late"]), ("Five canonical ER targets", P["HEA_canon"])]),
          ("Different constructs", [("ESR1 high alone", P["ESR1_high"]), ("Deposited multigene classifier", P["er_MGC"]), ("Deposited single-gene classifier", P["er_SGC"])])]
fig, ax = plt.subplots(layout="constrained", figsize=(W, 9.6 * CM)); y = 0; ticks, labs = [], []
for gi, (g, rows) in enumerate(groups):
    ax.text(0.4, y, g, va="center", ha="left", fontsize=7.5, fontweight="bold", color=INK); y += 1
    for lab, k in rows:
        lo, hi = proportion_confint(k, n, method="wilson")
        ax.plot([lo * 100, hi * 100], [y, y], color=BLUE, lw=1.6, solid_capstyle="round"); ax.plot(k / n * 100, y, "o", ms=5.5, color=BLUE, mec="white", mew=.8)
        ax.text(hi * 100 + 1.0, y, f"{k}/{n}", va="center", fontsize=7, color=INK2); ticks.append(y); labs.append(lab); y += 1
    if gi < len(groups) - 1: ax.axhline(y - .5 + .0, color=GRID, lw=.7)
ax.set_yticks(ticks); ax.set_yticklabels(labs, color=INK); ax.set_ylim(y - .4, -.7)
ax.set_xlabel("Tumours called ER-active among IHC ER-negative tumours\n(%, Wilson 95% CI)"); ax.set_xlim(0, 56)
ax.grid(axis="x", color=GRID, lw=.4); ax.set_axisbelow(True); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
for ext, kw in [("png", {"dpi": 600}), ("pdf", {}), ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})]: fig.savefig(OUT / f"Figure2.{ext}", **kw)
print("ok")
