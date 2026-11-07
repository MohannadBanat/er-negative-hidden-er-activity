# Deviations log (from analysis_plan_2026-10-25.md, SHA-256 889f096c…f843)

## D1 — 2026-10-25 — P6 mitochondrial feature dropped
The plan listed "median log2 expression of mitochondrial (MT-) genes" as a technical feature. The deposited GSE96058 matrix (UCSC knownGene annotation, nuclear chromosomes only) contains no mitochondrially encoded genes, so the feature cannot be computed. It is dropped; the other technical features are unchanged. Found when the scores were computed, before any model was fitted and before any outcome was viewed.

## E1–E3 — 2026-10-25 — exploratory checks added after seeing P6
The P6 technical-only model gave a cross-validated AUC of 0.67 (range across repeats 0.62–0.75), so the pre-specified "no technical artefact" reading did not hold. Three checks were added and are labelled exploratory: E1, a label-permutation null for the AUC (200 permutations, 5 repeats each); E2, a refit excluding PAM50 Normal-like tumours; E3, Spearman correlation of each technical feature with the adipose/normal proxy, plus univariate AUCs. Added before any outcome was viewed.

## V1 — 2026-10-25 — data provenance check (as promised in plan section 3)
Checked against GEO directly in a browser: (a) rows 1–5 of GSE96058_gene_expression_3273_samples_and_136_replicates_transformed.csv.gz for samples F11, F17, F20, F2516 and F741 equal the local values to 4 decimal places; (b) unique-tumour IHC ER counts in both series matrices equal the local counts exactly (GPL11154: 214 ER-negative / 2,569 ER-positive / 186 NA; GPL18573: 27 / 263 / 14). No discrepancy found.

## E4 — 2026-10-25 — exploratory: is "mean expression" a technical feature?
E3 showed that most of the technical-model signal comes from mean log2 expression across all genes (univariate AUC 0.76), not from platform (0.47). E4 tests whether mean expression differs by tumour biology across the whole cohort: AUC for PAM50 LumA vs Basal and for IHC ER-positive vs ER-negative among unique tumours, and within IHC ER-negative tumours for PAM50 luminal vs basal. Added before any outcome-based analysis.

Note on E1 run: the first serial run was too slow for its time limit and was stopped before finishing. It was re-run with the same 200 permutations (identical seed and sequence) split over 2 CPU cores. Results: observed AUC 0.678 (5 repeats); permutation null mean 0.487, 95th percentile 0.601; permutation p = 0.010.

## A1 — 2026-10-25 — amendment committed (amendment_A1_2026-10-25.md, SHA-256 3fa02b5b…ded8)
Purity-adjusted re-call (A1), ESR1-targeting miRNA layer (A2) and cell-line layer (A3), added at the author's request. Notes on how it was run:
- The cloud workspace cannot reach GEO, so GSE38167 values, GSE337499 FPKM rows and GSE337500 bigWig windows were read in a browser on the author's computer (scripts 10_ and 12_, kept in the repository). The GSE38167 per-miRNA column sums computed in the browser equal those recomputed from the saved file (checksums in A2_GSE38167.json).
- A3 Spearman p-values are printed by the script but are not reported (the plan says descriptive only).
- TFF1, PGR and GREB1 in the cell-line table are exploratory additions (canonical ER targets already in score S-c).

## A2 — 2026-11-03 — amendment committed (amendment_A2_2026-11-03.md, SHA-256 7f7c178b…ca31)
Four post hoc, exploratory checks requested during co-author review: E5 HER2 stratification, E6 near-threshold stability, E7 technical-only model split by component (ESR1-high vs activity-high), and E8 description of tumours with missing IHC ER status. The amendment was hashed before the checks were run. The main results were already known, so all four are labelled exploratory. GSE96058 only; no thresholds, groups or pre-specified analyses changed; no outcome data used. Scripts 19_A2_coauthor_checks.py and 20_A2_tableS1.py; output A2_coauthor_checks.json and TableS1_A2.md.
Notes on how it was run:
- The near-threshold result for ESR1 was reported as found. The two ESR1-discordant replicate pairs lay outside the ±2 SD zone, 3.6–3.7 technical SDs below the threshold in the original library.
- E7 seed robustness (seeds 1 and 2) was added to script 19 after the first run and re-run. The 20261025-seed results were unchanged.
- All counts were reproduced by an independent re-computation (pandas only, separate code).

## A3 — 2026-11-03 — amendment committed (amendment_A3_2026-11-03.md, SHA-256 29a65841…38c4)
Sensitivity analysis for P2b (reclassification probability) using expression-dependent technical noise. It was prompted by A2 check E6, where the two ESR1-discordant replicate pairs lay 3.6–3.7 SDs from the threshold. Post hoc and exploratory.
- **Disclosure.** The tertile SDs were inspected while designing the noise model. No simulation was run before the amendment was hashed.
- **Result.** By the pre-stated decision rule, the P2b conclusion stands:
  - primary tertile model: 18/20 HEA tumours with probability < 10% (constant SD: 18); expected HEA changes 0.85 (constant SD: 0.81);
  - quintile model: 18/20 and 1.02;
  - non-HEA uncertainty increased (24 → 36 of 241 tumours with probability ≥ 10%).
- The constant-SD recomputation with the new draws reproduced P2b (0.81 vs 0.82; 18 vs 18).
- Script 21_A3_heteroscedastic_reclass.py; output A3_heteroscedastic_reclass.json. Rows added to Table S1 (script 20).
