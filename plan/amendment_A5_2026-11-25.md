# Amendment A5 to the internal analysis plan — analyses requested in peer review

**Date written:** 25 November 2026 (Amman time). **Status:** post hoc. Every analysis below was requested by, or follows directly from, the first-round reviewer reports for *Cancers* (three reviewers). None was in the plan of 25 October 2026 or in amendments A1–A4.

**What had been seen before this amendment was written.** All results of the plan and of amendments A1–A4 (the submitted manuscript). The reviewer reports. The saved results files and the analysis code, which were re-read on 25 November 2026 to check four factual statements made by Reviewer 1 (all four were correct; see section 1). No new computation on the expression data was made between the submission (10 November 2026) and the hashing of this file.

**Data.** No new dataset. GSE96058 (SCAN-B) and GSE25066 only. Outcome fields remain unread in GSE25066 and are not used in SCAN-B.

**General rules for this amendment.**
- Random seed 20261025 everywhere. Bootstrap B = 2000 unless stated.
- All results are reported whatever their direction, and all are labelled post hoc.
- No pass/fail threshold is attached to the new prevalence or definition analyses. Reviewer 1 pointed out that the threefold rule of amendment A4 had no justification; that rule is kept in the record as it was written, described as arbitrary, and not reused.
- An interval for a difference that contains zero will be reported as "difference not excluded/not shown", never as equivalence or consistency.
- Where a corrected method changes a published number, the corrected number replaces it in the manuscript and the change is listed in the deviations log with the old value.

## 1. Statements by Reviewer 1 checked against the saved code and results (no new analysis)

1. Of the 136 replicate pairs, 13 are IHC ER-negative; 10 are in the low/low group and 3 in the activity-without-ESR1 group; none is HEA. Confirmed (`results.json`, `P2.neg_pairs`). The stability of the 20 HEA calls therefore rests on simulation, not on observed replicates.
2. The manuscript wording "within two SDs of its threshold: 0.266 … and 0.0022" gives the values of one SD; the code uses a zone of two SDs (0.53 and 0.0044). Confirmed. Wording error, to be corrected; no number in Table S1 changes because the code is as intended.
3. `StandardScaler` is fitted on the whole outer training fold before the internal cross-validation of `LogisticRegressionCV`/`RidgeCV`. Confirmed (scripts 03, 08, 19).
4. The bootstrap for the adipose-proxy shift resamples only the HEA group. Confirmed (script 03, P7).

## 2. New analyses

### R1 — Observed replicate evidence for the joint call (Reviewer 1, comment 2)
For the 136 replicate pairs of any IHC status, using the unchanged SCAN-B 5th-percentile thresholds:
- a. agreement (%), Cohen's κ and bootstrap 95% CI of the joint "both high" call;
- b. the same, restricted to pairs whose original library lies inside the expression range of the 20 HEA tumours on both axes (ESR1 between the HEA minimum and maximum, and activity score between the HEA minimum and maximum). The number of such pairs is reported even if it is zero or too small for κ.
The manuscript will separate three kinds of evidence: observed agreement of the two measurements over the full range; observed agreement of calls in replicate pairs (none of them an IHC ER-negative HEA tumour); simulated stability of the 20 HEA calls.

### R2 — Technical model split by feature type, with scaling inside the inner folds (Reviewer 1, comments 3 and 8)
The 12 features of the technical-only model are split into (i) processing metadata: sequencing platform and the library/processing tokens of the SCAN-B external identifier; (ii) expression-derived summaries: fraction of genes detected, median ribosomal-protein expression, mean expression.
- Models: all features; metadata only; expression-derived only. Outcomes: HEA call; ESR1-high; activity-high; continuous activity score (R², ridge).
- Same outer scheme as before (5-fold, 20 repeats). Hyper-parameters are chosen by an inner 5-fold grid search over a pipeline, so the scaler is fitted inside each inner training fold. Grid: the same 10 values of C (logistic) and 13 values of alpha (ridge) as before.
- The composition-adjusted model of amendment A1 and the E7 models of amendment A2 are re-run the same way.
Whatever the result, the manuscript will no longer say that the model places an artefact on the ESR1 axis, because expression-derived summaries can carry tumour biology and composition. If the metadata-only AUC has a 2.5–97.5 percentile range over repeats that includes 0.5, the text will say that processing metadata alone did not predict the call.

### R3 — Bounds for the 200 tumours with missing IHC ER status (Reviewer 1, comment 4)
Arithmetic bounds on HEA prevalence among IHC ER-negative tumours under two extreme assumptions about the 200 tumours with missing status: (lower) every missing tumour with both measures high is ER-positive and every other missing tumour is ER-negative; (upper) every missing tumour with both measures high is ER-negative and every other missing tumour is ER-positive. Reported with the observed value. The sentence that exclusion "is unlikely to have changed the estimate materially" will be removed.

### R4 — External comparison on a common gene universe and a matched reference group (Reviewer 1, comment 5)
- Common universe: genes present in both the SCAN-B ranking background and the GSE25066 gene table. Within-sample ranks are recomputed on this universe in both cohorts. Primary signature: Hallmark early ∪ late genes present in the universe, ESR1 removed (one identical gene list for both cohorts).
- Reference group for thresholds (5th percentile; 1st and 10th as before): IHC ER-positive tumours. For the HER2-negative comparison the SCAN-B reference is restricted to HER2-negative ER-positive tumours, to match GSE25066, which is HER2-negative by design.
- Reported: HEA count and Wilson CI in SCAN-B HER2-negative ER-negative tumours and in GSE25066; difference with Newcombe CI; counts at the 1st and 10th percentiles; agreement (κ) between the common-universe call and the original call within each cohort.
- The manuscript will state that the external analysis evaluates a cohort-relative procedure (thresholds re-estimated in each cohort) and not the transport of a fixed classifier, which the change of platform does not allow.

### R5 — Threshold sensitivity within operating thresholds, and threshold uncertainty (Reviewer 1, comment 6; Reviewer 3)
- a. Primary definition at the 1st, 2.5th, 5th, 7.5th and 10th percentiles of the ER-positive reference, in both cohorts: HEA count and percentage. The 2.5th–10th range is reported separately from the 1st percentile.
- b. Definitions are presented in two families: the same construct at different thresholds or signatures (joint ESR1/activity definitions), and different constructs (ESR1 alone; deposited single-gene and multigene receptor classifiers).
- c. Bootstrap of the ER-positive reference distribution (resampling ER-positive tumours with replacement), thresholds re-estimated each time: percentile interval for both thresholds and for the HEA count among the fixed ER-negative tumours.
- d. Combined interval for prevalence: ER-positive and ER-negative tumours both resampled.
Both cohorts.

### R6 — Dependence between the two axes (Reviewer 1, comment 7)
Spearman correlation between ESR1 and the ESR1-removed activity score, with bootstrap CI, among IHC ER-negative, IHC ER-positive and all tumours, in both cohorts. Descriptive.

### R7 — Reclassification simulation with uncertain thresholds and noise (Reviewer 1, comment 8)
The simulation of the plan (P2b) and of amendment A3 (tertile model) is repeated inside a bootstrap (B = 500, 2000 draws each) in which (i) the replicate pairs are resampled, so the technical SDs and their correlation are re-estimated, and (ii) the ER-positive reference is resampled, so the thresholds are re-estimated. Reported: percentile intervals for the number of the 20 HEA tumours with reclassification probability below 10% and for the expected number of HEA calls that change. Estimand, to be stated in the manuscript: the probability that a tumour's call changes on re-measurement of the same RNA, conditional on its observed values, under additive Gaussian technical error; biological and sampling variation within a tumour are not included.

### R8 — Two-group bootstrap for the adipose-proxy shift (Reviewer 1, comment 8)
Hodges–Lehmann shift between HEA and low/low tumours with both groups resampled. Replaces the published interval.

## 3. Changes to wording that do not depend on results
Listed here so that they are on record before the analyses are run.
- "Pre-specified" is not independently verifiable, because the plan was hashed internally and not registered publicly (Reviewer 3). The manuscript will say "planned before analysis (internal, unregistered plan)" and will state this limit. From this amendment onward the amendment and its hash are pushed to the public repository before the analysis is run.
- The statement that HEA should not guide endocrine therapy is reworded as a caution about interpreting the assay, since the study has no outcome data (Reviewer 3).
- Mechanistic terms (functional ER signalling, AR-driven, contamination, artefact) are replaced by descriptive labels and kept as hypotheses (Reviewers 1 and 2). The lack of functional validation is stated as a limitation.
- The IHC ER cut-off of each cohort is documented from its source publications; ER-zero and ER-low cannot be separated in either cohort.
- The title claim of technical reproducibility is limited to the measurements.

## 4. Not done
- No outcome analysis. No new dataset. No fixed-classifier transport across platforms.
