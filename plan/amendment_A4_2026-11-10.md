# Amendment A4 to the internal analysis plan (analysis_plan_2026-10-25.md, SHA-256 889f096c…f843)

Committed on 10 November 2026, after amendments A1–A3 and after the main results were known. **Everything in this amendment is post hoc.** It adds one external cohort at the request of the co-authors, who expect reviewers to question the single-cohort design.

## 1. Change to the data rule

- The original rule allowed only the datasets in Open_data.xlsx (GSE96058, GSE40049, GSE38167, GSE337499, GSE337500).
- On 10 November 2026 the authors extended the list with one dataset from a co-author's candidate file (Extra-validation_.xlsx): **GSE25066** (Hatzis et al., JAMA 2011; GPL96, Affymetrix HG-U133A; 508 pre-treatment breast cancer samples).
- The study remains restricted to the Gene Expression Omnibus. TCGA-BRCA and METABRIC are not used: they sit outside GEO and would need a separate access and harmonisation plan. GSE194040 and GSE16446 are not used in this amendment.
- GSE25066 was chosen before any of its expression values were read, because it has local IHC ER status for both ER-positive and ER-negative tumours (needed to anchor thresholds) and the largest ER-negative group among the GEO candidates.

## 2. What was seen before this amendment was hashed (disclosure)

- Only the sample annotation lines of the GEO series matrix were read. Counts seen: IHC ER status N = 205, P = 297, indeterminate 4, missing 2; platform GPL96; MAS5 processing; the names of the annotation fields; the overall PAM50 distribution of all 508 samples.
- No expression value was read. No cross-tabulation of any field with ER status was made.
- The annotation contains outcome fields (pathological response, RCB, distant relapse-free survival) and chemosensitivity predictions. These were not tabulated against anything and will not be used.

## 3. Cohort definition

- Unit: one sample per patient (the series has no technical replicates).
- IHC ER-negative set: `er_status_ihc` = N. IHC ER-positive anchor set: `er_status_ihc` = P. Indeterminate and missing are excluded.
- No further exclusion.

## 4. Measurements

- Expression: MAS5 values from the series matrix, log2-transformed if not already on a log scale (decided by the value range: maximum > 100 means not logged; values below 1 are set to 1 before the log).
- Probe-to-gene mapping: GEO GPL96 annotation. For each gene symbol, the probe set with the highest mean across all 508 samples is used. This rule is outcome-blind and applies to every gene, including ESR1. Probe sets mapping to more than one symbol are dropped.
- Gene universe for ranks: all mapped genes (a microarray has no zero-count floor, so the median > 0 filter of the main analysis does not apply).
- ESR1 axis: ESR1 log2 expression.
- Primary activity score: mean within-sample rank of the Hallmark oestrogen-response early and late genes (MSigDB v7.0, same file as the main analysis), ESR1 removed. Same code as the main analysis.
- Alternative scores: Hallmark early only; Hallmark late only; five canonical targets (PGR, GREB1, TFF1, PDZK1, MYB; mean z-score), as in the main analysis.
- Thresholds: re-anchored within this cohort. Primary: the 5th percentile of each measure among IHC ER-positive tumours. Alternatives: 1st and 10th percentiles. SCAN-B thresholds are not transferred, because the platforms differ.
- Groups among IHC ER-negative tumours: the same four groups as the main analysis (both high = hidden ER activity, HEA).

## 5. Analyses

- **V1 Prevalence.** Four-group counts and proportions with Wilson 95% CIs. Difference in HEA prevalence from the SCAN-B HER2-negative stratum (11/165) and from all SCAN-B ER-negative tumours (20/241), with Newcombe 95% CIs.
- **V2 Dependence on definition.** HEA count under: 1st, 5th and 10th percentile thresholds; early-only, late-only and canonical-target scores; ESR1-high alone; and the series' own deposited single-gene call (`esr1_status` = P). Cohen's κ between the primary HEA call and the deposited `esr1_status` among IHC ER-negative tumours.
- **V3 Composition.** Deposited PAM50 class by group. AR and FOXA1 expression in the "activity without ESR1" group against the low-ESR1/low-activity group (Mann–Whitney U, rank-biserial effect size). Deposited `erbb2_status` by group.
- **V4 Site.** HEA prevalence by contributing centre (`source`), descriptive, with a Fisher–Freeman–Halton exact test (Monte Carlo if needed). This is the only available stand-in for a technical-covariate check: the series has no replicate pairs and no library-level technical variables, so the reproducibility analysis and the technical-only model cannot be repeated.
- No outcome analysis of any kind.

## 6. Decision rules (stated before any expression value is read)

- **Prevalence** is called consistent with SCAN-B if the Newcombe 95% CI for the difference from the SCAN-B HER2-negative stratum includes zero.
- **Dependence on definition** is called replicated if the highest HEA count across the V2 definitions is at least three times the lowest.
- **Composition** is called replicated if (a) at least half of the HEA tumours are PAM50 luminal A, luminal B or Normal-like, and (b) AR is higher in the "activity without ESR1" group than in the low/low group (Mann–Whitney p < 0.05).
- Each rule is reported as met or not met. A rule that is not met is reported in the Abstract and Discussion with the same prominence as one that is met.

## 7. Known differences from SCAN-B (to be stated in the manuscript)

- Microarray, not RNA-seq; a neoadjuvant trial population selected for HER2-negative disease, not a population-based cohort; pre-treatment biopsies from several centres; IHC performed locally with the criteria of the time, so the ER cut-off may differ from 1%.
- These differences mean that agreement is evidence of generalisation and disagreement is not, by itself, evidence against the SCAN-B result.

## 8. Other changes requested by co-authors on the same date (not analyses)

- Fuller provenance check of the SCAN-B values against the GEO file (all genes and samples).
- Renaming of the low-ESR1/low-activity group; shorter title; reframing of the microRNA and cell-line sections as exploratory context; explicit statement of the GEO-only rule. These change wording only.
