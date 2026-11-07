# Amendment A3 to the internal analysis plan (analysis_plan_2026-10-25.md, SHA-256 889f096c…f843)

Committed on 3 November 2026, after amendment A2 (SHA-256 7f7c178b…ca31). **This analysis is post hoc and exploratory.** It is a sensitivity analysis for pre-specified analysis P2b (reclassification probability) and changes nothing that was pre-specified. Only GSE96058 is used. No outcome data are touched.

## Why

- In amendment A2 check E6, the two replicate pairs that disagreed on the ESR1 call lay 3.6–3.7 technical SDs from the threshold. That points to larger measurement noise at low ESR1 than the single constant technical SD used in P2b.
- **Disclosure.** While designing the noise model below, I inspected the technical SD of replicate differences within tertiles of pair-mean expression:
  - ESR1: 0.45, 0.07 and 0.06 log2 units from the lowest to the highest tertile;
  - activity score: 0.0031, 0.0017 and 0.0014.
- No simulation was run before this amendment was hashed.

## A3 — Reclassification probability with expression-dependent noise

**Noise model (primary).**
- For each measure separately (ESR1 and the primary activity score), the 136 replicate pairs are split into tertiles of the pair mean.
- Each tertile gets a technical SD equal to the SD of the differences divided by √2.
- A tumour's SD is found by linear interpolation between the tertile mean positions, held constant beyond the outermost positions.
- The ESR1–activity noise correlation is fixed at the P2b value (0.47).

**Noise model (secondary, for robustness).** The same, using quintiles instead of tertiles.

**Simulation.**
- For each of the 241 IHC ER-negative tumours: 10,000 correlated normal draws (seed 20261025), scaled by that tumour's two SDs and added to its observed values. The four groups are re-called at the unchanged thresholds.
- For a like-for-like comparison, the constant-SD model of P2b is recomputed with the same draws.

**Reported for each model.**
- Expected number of HEA tumours that change group.
- Number of HEA tumours with reclassification probability < 10%.
- Expected number of new HEA calls among non-HEA tumours.
- Number of the 241 tumours with reclassification probability ≥ 10%.
- Per-tumour reclassification probabilities for the 20 HEA tumours.

**Decision rule (stated before running).**
- The P2b conclusion, that HEA calls are largely robust to re-measurement, stands if, under the primary heteroscedastic model, at least 16 of the 20 HEA tumours have reclassification probability < 10% and the expected number of HEA tumours changing group is no more than 2.
- Otherwise, the manuscript will state that P2b underestimated reclassification and report the heteroscedastic estimates as the preferred values.
