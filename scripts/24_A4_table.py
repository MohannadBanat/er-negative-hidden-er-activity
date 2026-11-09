"""Table 5 (external cohort GSE25066 beside SCAN-B), as markdown, from the result files. Usage: python3 -I 24_A4_table.py <out dir> <table.md>"""
import sys, json, pathlib
import pandas as pd
from statsmodels.stats.proportion import proportion_confint
O = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
a = json.load(open(O / "A4_external_GSE25066.json")); r = json.load(open(O / "results.json")); t = pd.read_csv(O / "neg_tumours_table.csv", index_col=0)
def f(k, n):
    lo, hi = proportion_confint(k, n, method="wilson"); return f"{k} ({100*k/n:.1f}%; {100*lo:.1f}–{100*hi:.1f})"
nA, nS = a["n_neg"], r["n_neg"]
rows = [("**Groups (primary definition)**", "", "")]
for g, gs, lab in [("HEA", "HEA", "Hidden ER activity"), ("silent_ESR1", "silent_ESR1", "Silent ESR1"), ("act_wo_ESR1", "act_wo_ESR1", "Activity without ESR1"), ("low_low", "true_neg", "Concordant ER-negative")]:
    rows.append((lab, f(a["V1_groups"][g][0], nA), f(r["P1_groups"][gs][0], nS)))
rows.append(("**HEA under other definitions**", "", ""))
S = {"primary_1pct": r["P4"]["1"][0], "primary_10pct": r["P4"]["10"][0], "early_only": r["P3_n_pos"]["HEA_early"], "late_only": r["P3_n_pos"]["HEA_late"],
     "canonical5": r["P3_n_pos"]["HEA_canon"], "ESR1_high_alone": r["P3_n_pos"]["ESR1_high"], "deposited_esr1_status_P": r["P3_n_pos"]["er_SGC"]}
for d, lab in [("primary_1pct", "1st-percentile thresholds"), ("primary_10pct", "10th-percentile thresholds"), ("early_only", "Hallmark early only"), ("late_only", "Hallmark late only"),
               ("canonical5", "Five canonical targets"), ("ESR1_high_alone", "ESR1 high alone"), ("deposited_esr1_status_P", "Deposited single-gene ESR1 call")]:
    rows.append((lab, f(a["V2_counts"][d][0], nA), f(S[d], nS)))
rows.append(("**PAM50 of HEA tumours**", "", ""))
ph = a["V3_pam50_by_group"]["HEA"]; kA = sum(ph.values()); sh = t[t.group == "HEA"].pam50_subtype.value_counts(); kS = int(sh.sum())
for lab, ks in [("Luminal A or B", ["LumA", "LumB"]), ("Normal-like", ["Normal"]), ("Basal-like", ["Basal"]), ("HER2-enriched", ["Her2"])]:
    x, y = sum(ph.get(k, 0) for k in ks), int(sum(sh.get(k, 0) for k in ks)); rows.append((lab, f"{x}/{kA} ({100*x/kA:.0f}%)", f"{y}/{kS} ({100*y/kS:.0f}%)"))
rows.append(("**Activity without ESR1 group**", "", ""))
pw = a["V3_pam50_by_group"]["act_wo_ESR1"]; kw = sum(pw.values()); sw = t[t.group == "act_wo_ESR1"].pam50_subtype.value_counts(); ksw = int(sw.sum())
rows.append(("PAM50 HER2-enriched", f"{pw.get('Her2',0)}/{kw} ({100*pw.get('Her2',0)/kw:.0f}%)", f"{int(sw.get('Her2',0))}/{ksw} ({100*sw.get('Her2',0)/ksw:.0f}%)"))
md = ["**Table 5.** External cohort (GSE25066) beside SCAN-B. Values are n (%; Wilson 95% CI) among IHC ER-negative tumours unless stated. Thresholds were anchored within each cohort to its own IHC ER-positive tumours. The deposited single-gene call is `esr1_status` in GSE25066 and the SGC classifier in SCAN-B.", "",
      f"| Measure | GSE25066 (n = {nA}) | SCAN-B (n = {nS}) |", "| --- | --- | --- |"] + [f"| {x} | {y} | {z} |" for x, y, z in rows]
OUT.write_text("\n".join(md).replace("`esr1_status`", "esr1_status") + "\n"); print("\n".join(md))
