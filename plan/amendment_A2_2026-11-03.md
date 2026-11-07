# Amendment A2 to the internal analysis plan (analysis_plan_2026-10-25.md, SHA-256 889f096c…f843)

Committed on 3 November 2026, after co-author review of the draft. **All analyses in this amendment are post hoc and exploratory.** The main results were already known when they were specified. Nothing in this amendment changes a pre-specified analysis, a threshold or a group definition. Only GSE96058, which is already in Open_data.xlsx, is used. No outcome data are touched.

## Why

The co-authors proposed four checks that use data already analysed:
1. Stratify by HER2 status, because 42% of the hidden-ER-activity (HEA) group is HER2-positive.
2. Assess call stability specifically near the thresholds.
3. Find out which part of the HEA call the technical-only model predicts.
4. Describe the tumours with missing IHC ER status.

## E5 — HER2 stratification

- Among the 241 IHC ER-negative unique tumours, split by IHC/ISH HER2 status (0, 1, missing).
- Report the four-group counts with Wilson 95% CIs in each stratum.
- Report the HEA prevalence difference (HER2-positive minus HER2-negative) with a Newcombe 95% CI.
- Report the PAM50 make-up of the HEA group in each stratum.
- Thresholds are unchanged: the 5th percentile among all IHC ER-positive tumours.

## E6 — Stability near the thresholds

- **Near-threshold zone:** a tumour is "near-threshold" for a measure when |value − threshold| is no more than 2 × the replicate-derived technical SD for that measure (P2b: 0.266 for ESR1, 0.00219 for the activity score).
- **Replicate pairs:** among the 136 pairs, report high/low call agreement and Cohen's κ separately for pairs whose original library lies in the near-threshold zone and for pairs outside it.
- **IHC ER-negative tumours:**
  - the number of the 241 in the near-threshold zone for either measure;
  - their simulated flip probability from P2b, summarised as median and range;
  - the number of HEA tumours in the zone.

## E7 — Splitting the technical-only model by component

- Re-fit the P6 technical-only model as two separate models: one for ESR1-high (ESR1 ≥ threshold) and one for activity-high (activity ≥ threshold).
- Use the same features, the same nested cross-validation (20 repeats, seed 20261025) and the same 241 tumours.
- Report the mean AUC and its range across repeats for each model.
- Interpretation rule, stated in advance of running: if only one component is predicted (AUC ≥ 0.60 for that component and < 0.60 for the other), the technical signal is attributed to that component.

## E8 — Tumours with missing IHC ER status

Among unique tumours with missing IHC ER status, report:
- the number of tumours;
- the proportion with ESR1 ≥ threshold, with activity ≥ threshold, and with both, each with a Wilson 95% CI;
- their PAM50 distribution.

## Reporting

- E5–E8 go in a supplementary table, with one or two sentences each in Results.
- They are labelled exploratory everywhere they appear.
