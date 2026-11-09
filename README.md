# Hidden oestrogen-receptor activity in IHC ER-negative breast cancer (SCAN-B, GSE96058)

Code for a measurement and reproducibility study: how stable is a transcriptomic "hidden ER activity" call among breast cancers classified ER-negative by immunohistochemistry (IHC)?

Study type: secondary analysis of public data; agreement and reproducibility study (GRRAS), with descriptive biology. There are no prognostic or predictive claims.

## Analysis plan

`plan/analysis_plan_2026-10-25.md` is an internal analysis plan committed on 25 October 2026. It is not registered on OSF. Its SHA-256 is in `plan/analysis_plan_2026-10-25.sha256`:

```
889f096c6bca879a381c9e06da8ff72e1df5bb837594300e90b379d9ecfbf843
```

Deviations and exploratory additions are logged in `plan/deviations_log.md`.

## Data

GSE96058 (Brueffer et al., JCO Precis Oncol 2018, doi:10.1200/PO.17.00135). The cloud workspace could not reach GEO, so the values were read from the GitHub package `12379monty/gse96058`. That package splits GEO's own files without changing any values. It was checked against GEO directly on 25 October 2026:

- The first five gene rows for five samples of `GSE96058_gene_expression_3273_samples_and_136_replicates_transformed.csv.gz` match to 4 decimal places.
- IHC ER counts in both series matrices (GPL11154 and GPL18573) match exactly.

Gene sets: MSigDB Hallmark v7.0 (`ref/h.all.v7.0.symbols.gmt`, SHA-256 `4803c09a…3516`).

## Run order

```
python3 -I scripts/01_load.py <gse96058>/data data      # load; survival columns locked in a separate file
python3 -I scripts/02_scores.py data ref out            # ESR1 axis and ER-activity scores
python3 -I scripts/03_analysis.py data out              # pre-specified analyses P1–P8
python3 -I scripts/04_exploratory.py data out           # exploratory E1–E3 (logged)
python3 -I scripts/05_outcomes_descriptive.py data out  # plan section 6: descriptive counts only
python3 -I scripts/06_figures.py data out               # figures
python3 -I scripts/07_verify.py data out ref/h.all.v7.0.symbols.gmt   # independent re-computation
# Amendment A1 (plan/amendment_A1_2026-10-25.md, SHA-256 3fa02b5b…ded8)
python3 -I scripts/08_A1_purity.py data out ref <tidyestimate repo>      # composition-adjusted HEA
python3 -I scripts/09_A2_GSE40049.py <GSE40049 RAW dir> <series matrix> out   # miRNA, tumour vs paired normal
# 10_A2_GSE38167_browser.js and 12_A3_atac_browser.js run in a browser tab on ftp.ncbi.nlm.nih.gov
python3 -I scripts/11_A2_GSE38167.py out                                # miRNA, IDC vs paired NAT
python3 -I scripts/13_A3_celllines.py out                               # cell-line expression and ESR1 locus accessibility
# Amendment A2 (plan/amendment_A2_2026-11-03.md, SHA-256 7f7c178b…ca31): post hoc checks requested by co-authors, exploratory
python3 -I scripts/19_A2_coauthor_checks.py data out                     # E5 HER2 split, E6 near-threshold stability, E7 technical model by component, E8 missing ER
# Amendment A3 (plan/amendment_A3_2026-11-03.md, SHA-256 29a65841…38c4): P2b with expression-dependent noise, exploratory
python3 -I scripts/21_A3_heteroscedastic_reclass.py data out             # reclassification sensitivity analysis
python3 -I scripts/20_A2_tableS1.py out out/TableS1_A2.md               # Supplementary Table S1 (A2 + A3 rows)
# Amendment A4 (plan/amendment_A4_2026-11-10.md, SHA-256 ffad9bcf…f1a8): external cohort, post hoc
python3 -I scripts/22_A4_external_GSE25066.py <GSE25066_series_matrix.txt.gz> <GPL96.annot.gz> ref/h.all.v7.0.symbols.gmt out
python3 -I scripts/24_A4_table.py out out/Table5_A4.md
# Full provenance check of the SCAN-B matrix against the GEO file
python3 -I scripts/23_provenance_full_check.py <GSE96058 gene expression csv.gz> data/expr.parquet out/provenance_full_check.json
```

Data used (GEO only): GSE96058, GSE40049, GSE38167, GSE337499, GSE337500 (original list) and GSE25066 (external cohort, added by amendment A4).

Python 3.13: pandas, numpy, scipy, statsmodels, scikit-learn, pyreadr, matplotlib, pyarrow (see `requirements.txt`). Random seed 20261025.

## Licence

MIT (see LICENSE).
