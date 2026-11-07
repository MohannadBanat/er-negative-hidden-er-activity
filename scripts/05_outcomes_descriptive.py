"""Step 5: plan section 6 - descriptive outcome counts only (no HR, no p, no KM comparison).
Run after analysis_plan_2026-10-25.md was hashed (889f096c...f843)."""
import sys, json, pathlib
import numpy as np, pandas as pd

D, O = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
t = pd.read_csv(O / "neg_tumours_table.csv", index_col=0)
oc = pd.read_parquet(D / "LOCKED_outcomes.parquet").set_index("title").loc[t.index]
s = pd.read_parquet(D / "sampdesc.parquet").set_index("title").loc[t.index]
days = pd.to_numeric(oc.ovrallSurvDays, errors="coerce"); ev = pd.to_numeric(oc.ovrallSurvEvent, errors="coerce")

def reverse_km_median(time, event):
    # median follow-up: KM with censoring as the event
    tt, cc = time.values, (1 - event).values
    order = np.argsort(tt); tt, cc = tt[order], cc[order]
    surv, n = 1.0, len(tt)
    for i, (ti, ci) in enumerate(zip(tt, cc)):
        if ci == 1:
            surv *= 1 - 1 / (n - i)
            if surv <= 0.5: return float(ti)
    return float("nan")

res = {}
for g in ["HEA", "silent_ESR1", "act_wo_ESR1", "true_neg"]:
    m = (t.group == g) & days.notna() & ev.notna()
    res[g] = {"n": int((t.group == g).sum()), "n_with_followup": int(m.sum()), "deaths": int(ev[m].sum()),
              "median_followup_years": round(reverse_km_median(days[m], ev[m]) / 365.25, 2),
              "endocrine_treated": int((s.loc[t.group == g, "endocrine_treated"] == "1").sum()),
              "chemo_treated": int((s.loc[t.group == g, "chemo_treated"] == "1").sum())}
json.dump(res, open(O / "outcomes_descriptive.json", "w"), indent=1)
print(json.dumps(res, indent=1))
