"""Build Supplementary Table S1 (amendment A2, checks E5-E8) as markdown, straight from A2_coauthor_checks.json."""
import sys, json, pathlib
O = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
r = json.load(open(O / "A2_coauthor_checks.json"))
f1 = lambda x: f"{100 * x:.1f}"
def kci(k, ci, n): return f"{k} ({f1(k / n)}%; {f1(ci[0])}–{f1(ci[1])})" if n else str(k)
GL = [("HEA", "Hidden ER activity"), ("silent_ESR1", "Silent ESR1"), ("act_wo_ESR1", "Activity without ESR1"), ("true_neg", "Concordant ER-negative")]
PL = {"LumA": "Luminal A", "LumB": "Luminal B", "Her2": "HER2-enriched", "Basal": "Basal-like", "Normal": "Normal-like"}
rows = []
for h, lab in [("0", "HER2-negative"), ("1", "HER2-positive"), ("missing", "HER2 missing")]:
    v = r["E5"][h]; n = v["n"]
    for g, gl in GL:
        x = v["groups"][g]; rows.append(("E5 HER2 status", f"{lab} (n = {n}): {gl}", kci(x["k"], x["ci"], n)))
    if v["HEA_pam50"]:
        rows.append(("E5 HER2 status", f"{lab}: PAM50 of HEA tumours", "; ".join(f"{PL[k]} {c}" for k, c in sorted(v["HEA_pam50"].items(), key=lambda z: -z[1]))))
d = r["E5"]["HEA_diff_her2pos_minus_neg"]
rows.append(("E5 HER2 status", "HEA prevalence, HER2-positive minus HER2-negative", f"{f1(d[0])} percentage points ({f1(d[1])} to {f1(d[2])})"))
for col, lab in [("ESR1", "ESR1"), ("act_primary", "Activity score")]:
    for z, zl in [("near", "within 2 technical SD of threshold"), ("far", "beyond 2 technical SD")]:
        x = r["E6"][col][z]
        k = "" if x["kappa"] is None else f"; κ {x['kappa']:.2f}"
        rows.append(("E6 Near-threshold stability", f"{lab} call, replicate pairs {zl}", f"{x['n_pairs']} pairs; agreement {f1(x['agree'])}%{k}; {x['discordant']} discordant"))
x = r["E6"]["neg_tumours_near"]
rows.append(("E6 Near-threshold stability", "IHC ER-negative tumours near either threshold", f"{x['n']}/{x['of']}; median reclassification probability {f1(x['flip_median'])}% (range {f1(x['flip_range'][0])}–{f1(x['flip_range'][1])}%); {x['flip_ge_10pct']} at ≥10%; {x['HEA_near']} of 20 HEA tumours"))
for k, lab in [("ESR1_high", "ESR1-high"), ("activity_high", "Activity-high")]:
    x = r["E7"][k]
    rows.append(("E7 Technical-only model by component", f"{lab} ({x['n_pos']} of 241)", f"AUC {x['auc_mean']:.2f} (range {x['auc_range'][0]:.2f}–{x['auc_range'][1]:.2f}), 20 repeats; other seeds " + ", ".join(f"{v:.2f}" for v in x["seed_check"].values())))
x = r["E8"]; n = x["n"]
for k, lab in [("ESR1_high", "ESR1 ≥ threshold"), ("activity_high", "Activity ≥ threshold"), ("both_high", "Both ≥ threshold")]:
    rows.append(("E8 Missing IHC ER status", f"{lab} (n = {n})", kci(x[k][0], x[k][1], n)))
rows.append(("E8 Missing IHC ER status", "Neither ≥ threshold", f"{x['neither']} ({f1(x['neither'] / n)}%)"))
rows.append(("E8 Missing IHC ER status", "PAM50", "; ".join(f"{PL[k]} {c} ({f1(c / n)}%)" for k, c in sorted(x["pam50"].items(), key=lambda z: -z[1]))))
a3p = O / "A3_heteroscedastic_reclass.json"
if a3p.exists():                                     # amendment A3: P2b with expression-dependent noise
    a3 = json.load(open(a3p))
    for m, lab in [("constant", "Constant SD (P2b, recomputed)"), ("tertile", "Expression-dependent SD, tertiles (primary)"), ("quintile", "Expression-dependent SD, quintiles")]:
        x = a3[m]
        rows.append(("A3 Reclassification, expression-dependent noise", lab,
                     f"{x['HEA_robust_lt10pct']}/20 HEA with probability <10%; expected HEA changes {x['expected_HEA_flips']:.2f}; expected new HEA {x['expected_new_HEA_from_others']:.2f}; {x['n_flip_ge10pct_of_241']}/241 tumours with probability ≥10%"))
md = ["**Table S1.** Post hoc checks requested during co-author review (amendments A2 and A3; all exploratory). Values are n (%; Wilson 95% CI) unless stated. Thresholds are unchanged from the main analysis (5th percentile among IHC ER-positive tumours). Technical SD: 0.266 log2 units for ESR1 and 0.0022 for the activity score, from the replicate pairs.", "",
      "| Check | Measure | Result |", "| --- | --- | --- |"] + [f"| {a} | {b} | {c} |" for a, b, c in rows]
md = [l.replace("(-", "(−").replace(" -", " −") for l in md]
OUT.write_text("\n".join(md) + "\n"); print("\n".join(md))
