# Internal analysis plan committed on 25 October 2026

Project: Hidden oestrogen-receptor (ER) activity in IHC ER-negative breast cancer
Author of plan: drafted by Claude (AI assistant) for Mohannad Banat; to be reviewed by the author.
Status: this is an internal analysis plan committed on 25 October 2026 (SHA-256 recorded separately). It is NOT registered on OSF.

## 1. Study type

Secondary analysis of public data. A measurement and reproducibility (agreement) study of a transcriptomic classification within one population-based cohort. It is not a prognostic-marker study and makes no claims about survival or endocrine-therapy benefit. Reporting follows GRRAS (Guidelines for Reporting Reliability and Agreement Studies) for the agreement analyses. The REMARK items that apply (patients, specimens, assay methods, statistical methods) are reported in a checklist.

## 2. Why this design (decision of 25 Oct 2026)

Phase 0 found that (a) Kimbung et al., Clin Cancer Res 2025, already reported that 26 of 712 (3.7%) HER2-negative IHC ER-negative SCAN-B tumours are ER-positive by an RNA-seq predictor; (b) GSE96058 records IHC ER as binary, so ER-low cannot be identified; and (c) only 11 IHC ER-negative patients received endocrine therapy, so the endocrine interaction cannot be tested. The open question this data can answer is whether a "hidden ER activity" call in IHC ER-negative tumours is technically and definitionally stable.

## 3. Data (data rule: only datasets in Open_data.xlsx)

GSE96058 only for this plan. The source is the GitHub data package 12379monty/gse96058, which splits GEO's own files without changing any values: the file GSE96058_gene_expression_3273_samples_and_136_replicates_transformed.csv.gz plus the GPL11154 and GPL18573 series matrices. The cloud workspace could not reach GEO, so this package is used instead. Values will be spot-checked against GEO directly when GEO is reachable, and any discrepancy logged as a deviation.

- Unique tumours: 3,273 (non-replicate libraries). Technical replicate pairs: 136 (36 cross platform).
- Analysis population: unique tumours with IHC er_Status = 0 (n = 241). Reference population for thresholds: er_Status = 1 (n = 2,832). er_Status = NA (n = 200) are excluded from the main analyses.
- Expression: values as deposited (log2 scale; floor −3.32 ≈ log2(0.1)).
- Outcome columns (overall survival days and event) were moved to a separate locked file at load and have not been viewed.

Data file hashes at commitment (SHA-256):
- sampdesc.parquet d2fab9ad15255c311f64b1817184e267493295a9155f6f33b7aae950b9301285
- expr.parquet 7e93d97b5ab279176c514eb70de190377340aef090a7c5a7d10cee5e80015c7a
- LOCKED_outcomes.parquet 9239ae0dd37d75d56ffce16615583486e79923ab85505af9ada78f12c0fe2079
- h.all.v7.0.symbols.gmt (MSigDB Hallmark v7.0) 4803c09aae50bbd96d53fc681bd5545a4c89278993c15145dd7b7c994f893516

## 4. Definitions (fixed before any score is computed)

**Gene universe:** genes whose median log2 expression across all unique tumours is above 0.

**ESR1 axis:** log2 ESR1 expression.

**Primary ER-activity score:** a single-sample rank score (singscore-style).
- Within each sample, rank the genes in the universe and scale the ranks to 0–1.
- The score is the mean scaled rank of the genes in HALLMARK_ESTROGEN_RESPONSE_EARLY ∪ HALLMARK_ESTROGEN_RESPONSE_LATE, with ESR1 removed. This keeps the activity axis independent of the ESR1 axis.

**Secondary scores:**
- (S-a) the same rank score using Early only;
- (S-b) the same rank score using Late only;
- (S-c) canonical targets: the mean of per-gene z-scores (standardised across all unique tumours) of PGR, GREB1, TFF1, PDZK1 and MYB.

**High:** a value at or above the 5th percentile of the same measure among IHC ER-positive unique tumours. The 1st and 10th percentiles are used for sensitivity analyses.

**Groups** (among IHC ER-negative tumours):

| ESR1 axis | Activity axis | Group |
|---|---|---|
| high | high | hidden ER activity (HEA) |
| high | low | silent ESR1 |
| low | high | activity without ESR1 |
| low | low | truly ER-negative |

**Other ER calls compared:**
- ESR1-high alone;
- the deposited RNA classifiers er_MGC and er_SGC (Brueffer 2018);
- HEA under each secondary score.

## 5. Analyses (none use outcomes)

**P1 (primary).** Prevalence of HEA among the 241 tumours, with a Wilson 95% CI. Counts are also given for all four groups.

**P2 (primary). Technical reproducibility across the 136 replicate pairs.**
- Intraclass correlation (two-way, absolute agreement, single measure) for ESR1 and the primary score, with bootstrap 95% CIs (2,000 resamples of pairs).
- Reported for all pairs and separately for the 36 cross-platform pairs.
- Agreement of the binary high/low calls on each axis: percentage agreement and Cohen's kappa.

**P2b. Reclassification probability.**
- Estimate technical measurement error from the replicate differences as SD(diff)/√2 per axis.
- Estimate the covariance between the two axes' differences.
- For each IHC ER-negative tumour, simulate 10,000 draws from a bivariate normal distribution centred on its observed values with that technical covariance.
- Record the probability that its group call changes.
- Report the expected number of HEA tumours whose call would flip on re-measurement, and the number with flip probability below 10% (the "technically robust HEA").

**P3. Definition agreement** among the 241 tumours.
- Pairwise Cohen's kappa, with bootstrap 95% CIs, between: HEA (primary); HEA under S-a, S-b and S-c; ESR1-high alone; er_MGC; er_SGC.
- The number positive under each, and the "consensus core": positive under HEA-primary, HEA-S-c and er_SGC together.

**P4. Threshold sensitivity.** HEA prevalence at the 1st, 5th and 10th percentile thresholds.

**P5. Platform split.** HEA prevalence for HiSeq 2000 and NextSeq 500 separately, with Wilson CIs and the difference with a Newcombe CI. Platform is confounded with calendar period; this is stated as a limitation.

**P6. Technical-only negative-control model.**

Features (technical only):
- sequencing platform;
- fraction of genes above the floor value;
- median log2 expression of mitochondrial (MT-) genes;
- median log2 expression of ribosomal-protein (RPL/RPS) genes;
- mean log2 expression of all genes;
- library tokens parsed from the SCAN-B external ID (used only if they vary; their meaning is not documented, so they are treated as technical batch markers).

Models:
- (a) L2-penalised logistic regression predicting HEA versus other groups among the 241 tumours.
- (b) Ridge regression predicting the continuous primary score among the 241 tumours.

Validation:
- Nested cross-validation: outer stratified 5-fold repeated 20 times; inner 5-fold to tune the penalty.
- Report the out-of-fold AUC for (a) and R² for (b), with the spread across repeats.

Interpretation: an AUC whose 95% interval includes 0.5, or an R² of about 0 or below, means there is no evidence that the call is a technical artefact. With about 12 positive tumours the AUC is imprecise, and this is stated.

**P7. Normal-tissue contamination check.** Normal breast luminal cells express ER, so HEA could reflect adjacent normal tissue. Compare HEA with truly ER-negative tumours on:
- the share of PAM50 Normal-like tumours (Fisher test, odds ratio with 95% CI);
- an adipose/normal-tissue proxy: the mean z-score of ADIPOQ, PLIN1, LEP and CIDEA (Mann–Whitney, Hodges–Lehmann shift with 95% CI).

**P8. Description (exploratory).**
- Variables by the four groups: PAM50, NHG, IHC HER2, IHC PgR, Ki67 status, age, tumour size, nodal status, AR and FOXA1 expression.
- Fisher or Kruskal–Wallis tests, effect sizes, no multiplicity claims. AR and FOXA1 are included to test the luminal-androgen-receptor explanation of "activity without ESR1" (Borgel 2025).

## 6. Outcomes (after this plan is hashed)

Survival is unlocked only after this file's SHA-256 is recorded. The only outcome data reported are, for each group: the number of patients, the number of deaths, the median follow-up (reverse Kaplan–Meier), and the number treated with endocrine therapy. No hazard ratios, p values or Kaplan–Meier comparisons are reported, because the groups are too small to be informative. This was decided before any outcome data were seen.

## 7. Statistics and software

Python 3 (pandas, numpy, scipy, statsmodels, scikit-learn). Random seed 20261025. All CIs are 95%. Effect sizes and CIs take priority over p values. No external validation cohort is permitted under the data rule; internal validation is through replicates, the platform split and nested cross-validation. Code will be released on GitHub under the MohannadBanat organisation.

## 8. Deviations

Any change after commitment is logged with its date in deviations_log.md and labelled in the manuscript as a deviation or as exploratory.
