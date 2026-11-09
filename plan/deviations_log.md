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

## A4 — 2026-11-10 — amendment committed (amendment_A4_2026-11-10.md, SHA-256 ffad9bcf…f1a8)
External cohort GSE25066 added at the co-authors' request. This extends the data list by one GEO series; the study stays GEO-only. Post hoc.
- **Order of events.** Only the sample annotation was read before hashing (ER status counts, field names, overall PAM50 distribution). The amendment and its three decision rules were hashed at 22:11 UTC on 9 November (10 November local time). Expression values were read after that.
- **Result against the pre-stated rules.**
  - Prevalence: NOT consistent. HEA 39/205 (19.0%, 14.2–24.9) against 11/165 in the SCAN-B HER2-negative stratum; difference 12.4 points (5.5–19.0).
  - Dependence on definition: replicated. 23 to 119 tumours across definitions (5.2-fold).
  - Composition: NOT replicated in full. Condition (a) met (20/39 HEA luminal or Normal-like). Condition (b) not met (AR in activity-without-ESR1 against low/low: p = 0.13).
- The outcome fields of GSE25066 were never parsed (script 22 keeps a fixed list of six annotation fields).
- The HEA count and the ESR1 values were reproduced by a separate code path reading probe set 205225_at directly from the series matrix.
- Scripts 22_A4_external_GSE25066.py and 24_A4_table.py; outputs A4_external_GSE25066.json, A4_GSE25066_neg_tumours.csv, A4_GSE25066_scores_all.csv, Table5_A4.md.

## 2026-11-10 — full provenance check of GSE96058 (not an analysis)
The GEO supplementary expression file (MD5 4362d1d9b5e80a6e1409cd7b9dc4a0ab) was downloaded and compared with the analysed matrix: 30,865 genes × 3409 libraries present in both; 105,218,785 values compared; largest absolute difference 9.5e-07; none above 1e-06. Script 23_provenance_full_check.py; output provenance_full_check.json. This replaces the earlier 5 × 5 spot check.

## 2026-11-10 — wording changes requested by co-authors (no analysis changed)
- The group "truly ER-negative" is renamed "concordant ER-negative" in text, tables and figures. The co-authors proposed "non-HER2 ER-negative"; that label was not used because 30 of the 160 tumours in the group are HER2-positive (and 9 have missing HER2 status), so it would misdescribe the group. Internal variable names (true_neg) are unchanged.
- New, shorter title. The microRNA and cell-line sections are reframed as exploratory context and moved after the external cohort; claims about them are removed from the Simple Summary, Abstract and Conclusions.
- The GEO-only data rule is stated in Methods 2.1.
- GRRAS and REMARK were already cited separately (now references 48 and 49); no change was needed.

## 2026-11-10 — ER definition in GSE25066 checked against the source paper (no analysis changed)
- The source publication (Hatzis et al., JAMA 2011) states that patients with any nuclear ER immunostaining in tumour cells were considered eligible for endocrine therapy, and that biopsies were fine-needle aspirates or core biopsies taken before systemic therapy. The paper does not state how the deposited binary ER field was defined.
- The Discussion had offered a higher historical ER cut-off (ER-low tumours counted as negative) as one possible explanation for the higher prevalence in GSE25066. That explanation is now described as unlikely, and the biopsy type is added as a cohort difference. Methods 2.7 states both facts. No number changed.
