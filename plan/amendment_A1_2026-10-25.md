# Amendment A1 to the internal analysis plan (analysis_plan_2026-10-25.md, SHA-256 889f096c…f843)

Committed on 25 October 2026, before any value below was computed and before any tumour-versus-normal comparison in GSE40049 or GSE38167 was viewed. This is an internal amendment; nothing is registered on OSF.

## Why

1. **Purity.** The pre-specified technical-only control (P6) did not pass. Exploratory checks E1–E4 suggest the hidden-ER-activity (HEA) call partly tracks sample composition. A composition-adjusted re-call is needed before the HEA group can be interpreted.
2. **Supporting layers.** The author asked for the miRNA and cell-line layers in the Open_data.xlsx sheet to be added. They cannot be linked to individual SCAN-B tumours and are reported as plausibility evidence only.

All datasets are in Open_data.xlsx: GSE96058, GSE40049, GSE38167 and GSE337499/GSE337500.

## A1 — Composition-adjusted HEA (GSE96058)

**Scores**
- ESTIMATE stromal and immune scores, using the tidyestimate algorithm: single-sample GSEA on within-sample ranks, weight 0.25.
- Gene sets: the 141-gene stromal and 141-gene immune signatures from tidyestimate commit 7f98f860d333d04e81248ff0bb83852d0263bee4. Gene-set file SHA-256: 7d9ddedc4a743d7954b08db3eeebe7129ffdbbdde9b5a3e8375440c97071e451.
- The Affymetrix purity formula is not applied to RNA-seq data; the scores are used as continuous covariates.

**A1a.** HEA vs truly ER-negative on the stromal score, immune score and the adipose proxy. Effect size: Hodges–Lehmann shift with a bootstrap 95% CI (2,000 resamples).

**A1b. Composition-adjusted re-call**
- Among IHC ER-positive unique tumours, fit ordinary least squares models of ESR1 and of the primary activity score on stromal score + immune score + adipose proxy.
- For every tumour, compute residual = observed − predicted.
- Set the thresholds at the 5th percentile of the residuals among IHC ER-positive tumours, then re-call the four groups among the 241 IHC ER-negative tumours.
- Report: the HEA count with a Wilson CI, overlap with the original 20 HEA tumours, and the PAM50 make-up of the retained and dropped tumours.
- Pre-stated expectation: if HEA is mostly contamination, the Normal-like tumours drop out and the luminal tumours are retained.

**A1c.** Re-fit the P6 technical-only model, with the same features and the same nested cross-validation, against the adjusted HEA call. Report the AUC (mean and range over 20 repeats).

## A2 — ESR1-targeting miRNAs in triple-negative tumours

**Candidates (fixed).** Each has a primary experimental report of direct ESR1 3′UTR targeting:

| miRNA | Evidence (PMID) |
|---|---|
| miR-18a | 19027010 |
| miR-22 | 19414598 |
| miR-206 | 17312270 |
| miR-221 | 18790736 |
| miR-222 | 18790736 |

Five tests per dataset. Benjamini–Hochberg correction is applied within each dataset.

**GSE40049 (small RNA-seq, SOLiD)**
- Sum the read counts of every alignment assigned to each precursor ID (hsa-mir-18a, -22, -206, -221, -222) per library.
- Library size = all miRNA-assigned reads. Expression = log2(CPM + 1). Arms are not resolved; this is a limitation.
- Primary test: tumour vs adjacent normal in the 14 matched pairs. Paired Wilcoxon test; median paired log2 fold-change with a bootstrap 95% CI.
- Secondary (descriptive): recurrence (yes/no) among the 24 tumours, Mann–Whitney test.

**GSE38167 (Agilent miRNA array, FFPE)**
- Map probe features to mature miRNAs with the GEO platform annotation.
- Value per miRNA per sample = median over its features of log2(max(signal, 1)), minus that sample's 75th percentile of log2 signal across all features.
- Primary test: tumour (IDC) vs normal adjacent tissue (NAT) in patients with both. Paired Wilcoxon test; median paired difference with a bootstrap 95% CI.
- Secondary (descriptive): lymph-node metastasis vs IDC in patients with both.
- Mature names used: miR-18a-5p (or miR-18a), miR-22-3p (or miR-22), miR-206, miR-221-3p (or miR-221), miR-222-3p (or miR-222).

**Reading rule.** A miRNA counts as "higher in triple-negative tumour than normal" only if the paired difference is above 0 with BH-adjusted p < 0.05 in both datasets.

## A3 — ESR1 locus in eight triple-negative cell lines (GSE337499, GSE337500)

**RNA (GSE337499)**
- FPKM of ESR1, AR, FOXA1 and GATA3, averaged over the two replicates, on a log2(FPKM + 1) scale.

**ATAC (GSE337500)**
- Mean RPKM coverage from each replicate's bigWig over windows of the canonical TSS ±1 kb (hg38):

| Gene | Window |
|---|---|
| ESR1 | chr6:151,806,318–151,808,318 |
| AR | chrX:67,543,031–67,545,031 |
| FOXA1 (minus strand) | chr14:37,594,120–37,596,120 |
| GAPDH (reference) | chr12:6,533,404–6,535,404 |

- Coverage is reported relative to GAPDH, averaged over the two replicates.
- The bigWigs are read by HTTP range requests (the @gmod/bbi library) in a browser on the author's computer. Only these windows are fetched.

**Analysis.** Descriptive only: a per-line table and Spearman's rho between ESR1 expression and ESR1 TSS accessibility, n = 8 and no inference. There is no ER-positive comparator line (data rule).

## Reporting

The A1 results are reported beside the original pre-specified results, which are not replaced. A2 and A3 are reported as supporting, hypothesis-generating layers.
