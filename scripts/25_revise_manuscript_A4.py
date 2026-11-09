"""Co-author revision of 10 Nov 2026: external cohort (A4), title, terminology, framing of the microRNA/cell-line
sections, data rule, provenance. Tokenises citations, edits, reorders sections, renumbers references by first appearance."""
import re, sys
SRC, T5, OUT = sys.argv[1:4]
md = open(SRC, encoding="utf8").read()
i_ref = md.index("## References"); i_end = md.index("## Before submission")
body, reftxt, tail = md[:i_ref], md[i_ref:i_end], md[i_end:]
refs = {}
for line in reftxt.splitlines():
    m = re.match(r"^(\d+)\.\s+(.*)$", line)
    if m: refs[f"R{m.group(1)}"] = m.group(2)
def expand(spec):
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "–" in part: a, b = part.split("–"); out += list(range(int(a), int(b) + 1))
        else: out.append(int(part))
    return out
body = re.sub(r"\\\[(\d+(?:\s*[–,]\s*\d+)*)\\\]", lambda m: "[" + ";".join(f"@R{n}" for n in expand(m.group(1))) + "]", body)
refs["Hatzis"] = "Hatzis, C.; Pusztai, L.; Valero, V.; Booser, D.J.; Esserman, L.; Lluch, A.; et al. A Genomic Predictor of Response and Survival Following Taxane-Anthracycline Chemotherapy for Invasive Breast Cancer. *JAMA* **2011**, *305*, 1873–1881. https://doi.org/10.1001/jama.2011.593"

def rep(a, b, n=1):
    global body
    assert body.count(a) >= 1, "NOT FOUND: " + a[:90]
    body = body.replace(a, b) if n == 0 else body.replace(a, b, n)
def para(start):                       # full paragraph (line) beginning with `start`
    i = body.index(start); return body[i:body.index("\n", i)]
def section(head):                     # from heading line to the next heading of the same or higher level
    i = body.index(head); lvl = head.split(" ")[0]
    m = re.search(r"\n(?:## |### )" if lvl == "###" else r"\n## ", body[i + 5:])
    return body[i:i + 5 + m.start() + 1]

# ---------------- title, summary, abstract, keywords
rep(body.splitlines()[0], "# Transcriptomic Hidden Oestrogen-Receptor Activity in ER-Negative Breast Cancer Is Technically Reproducible but Depends on Definition and Cohort")
rep(para("Breast cancers are labelled"),
"Breast cancers are labelled \"oestrogen-receptor negative\" when a tissue stain shows no receptor protein, and these patients are not offered hormone therapy. Gene-expression data sometimes suggest that a few of these tumours still use the receptor. We asked how reliable that hidden-activity label is, using public data from more than 3000 Swedish tumours and a second, independent set of 508 tumours. In the Swedish data, about one in twelve stain-negative tumours carried the label, and repeat sequencing of the same tumour gave the same answer. However, the label changed a great deal with the cut-off used, and in the second set it was more than twice as common. It also grouped together different things: tumours that look like ordinary hormone-sensitive cancers and samples that appear mixed with normal breast tissue. A hidden-activity label should therefore not guide treatment on its own.")
rep(para("**Methods:** Secondary analysis"),
"**Methods:** Secondary analysis of public data. In the population-based SCAN-B RNA-sequencing cohort (GSE96058; 3273 tumours, 136 technical replicates), IHC ER-negative tumours (n = 241) were classified by ESR1 expression and an ESR1-independent Hallmark oestrogen-response score, using thresholds anchored to IHC ER-positive tumours, under an internal analysis plan hashed before analysis. A post hoc external cohort (GSE25066; microarray; 205 IHC ER-negative tumours) was analysed with re-anchored thresholds and decision rules fixed in advance. MicroRNA and cell-line data provided exploratory context.")
rep(para("**Results:** HEA was called"),
"**Results:** In SCAN-B, HEA was called in 20/241 tumours (8.3%, 95% CI 5.4–12.5). Technical reproducibility was near-perfect (intraclass correlation ≥0.99, including across platforms), but prevalence ranged from 5.0% to 43.2% across thresholds and classifiers. The HEA group combined transcriptionally luminal tumours (10/20) and PAM50 Normal-like samples (6/20); a neighbouring group was androgen-receptor-high. A pre-specified technical-only model predicted the call (cross-validated AUC 0.67). In GSE25066, HEA was called in 39/205 tumours (19.0%, 14.2–24.9), so the SCAN-B prevalence was not replicated. Dependence on definition was replicated (11.2–58.0%). Composition was only partly replicated: 20/39 HEA tumours were luminal or Normal-like, but the androgen-receptor association was not seen.")
rep(para("**Conclusions:** HEA in IHC"),
"**Conclusions:** HEA in IHC ER-negative breast cancer is technically reproducible, but its prevalence depends on definition and cohort, and its composition is heterogeneous. It should not be used alone to guide endocrine therapy.")
rep("androgen receptor; microRNA; miR-18a; SCAN-B", "external validation; androgen receptor; microRNA; SCAN-B")

# ---------------- introduction aims
rep(para("We therefore performed a secondary analysis of public data with three aims"),
"We therefore performed a secondary analysis of public data. The main aim, fixed in an internal analysis plan before analysis, was to estimate the prevalence of HEA among IHC ER-negative tumours in the population-based SCAN-B cohort and to assess its technical reproducibility, its dependence on definition and its composition. After co-author review, we added a post hoc external cohort (GSE25066 [@Hatzis]) to test whether prevalence, dependence on definition and composition generalise. As exploratory context only, we also compared microRNAs with experimentally validated ESR1 targeting between TNBC and paired normal tissue, and described chromatin accessibility at the ESR1 promoter in eight TNBC cell lines. These two analyses do not test HEA tumours directly. This is not a prognostic or predictive marker study, and no survival or treatment-effect claims are made.")

# ---------------- 2.1 data rule, Table 1, amendments
rep("Only the five datasets listed in Table 1 were analysed. Other studies were consulted for context but their data were not used.",
"Only the six datasets listed in Table 1 were analysed.\n\nThe datasets were fixed in a list before analysis and restricted to the Gene Expression Omnibus (GEO). The purpose of this rule was to keep the choice of data from being influenced by results, and to use one open repository with stable accessions that any reader can retrieve without an access application. The original list had five datasets. On 10 November 2026 the authors added one external cohort, GSE25066, in a dated amendment (A4) that was hashed before any of its expression values were read. Resources outside GEO, such as TCGA-BRCA and METABRIC, were not used. Other studies were consulted for context but their data were not used.")
rep("| GSE40049 [@R49] | TNBC and adjacent normal tissue, Taiwan |",
"| GSE25066 [@Hatzis] | Pre-treatment biopsies of HER2-negative breast cancer from four contributing centres or trial groups | Affymetrix HG-U133A microarray (GPL96) | 508 tumours: 205 IHC ER-negative, 297 IHC ER-positive, 6 indeterminate or missing | External cohort (post hoc) |\n| GSE40049 [@R49] | TNBC and adjacent normal tissue, Taiwan |")
rep("| ESR1-targeting microRNAs |", "| Exploratory context: ESR1-targeting microRNAs |")
rep("| Replication of the microRNA layer |", "| Exploratory context: second microRNA dataset |")
rep("| Expression at the ESR1 locus |", "| Exploratory context: expression at the ESR1 locus |")
rep("| Chromatin accessibility at the ESR1 locus |", "| Exploratory context: chromatin accessibility at the ESR1 locus |")
rep("A dated amendment (A1; SHA-256 3fa02b5b…ded8) was committed before the composition-adjusted, microRNA and cell-line analyses. Neither document was registered on a public registry.",
"A dated amendment (A1; SHA-256 3fa02b5b…ded8) was committed before the composition-adjusted, microRNA and cell-line analyses. Three later amendments (A2–A4) cover post hoc analyses and are described below. None of these documents was registered on a public registry.")

# ---------------- 2.2 provenance
rep("The cloud computing environment used for analysis could not reach GEO directly. Values were therefore read from a public package that splits the GEO files without modification (github.com/12379monty/gse96058). On 25 October 2026 these values were checked against GEO: the first five gene rows of the original expression file matched to four decimal places for five samples, and the IHC ER counts in both series matrices matched exactly.",
"At the time of the main analysis, the computing environment could not reach GEO directly. Values were therefore read from a public package that splits the GEO files without modification (github.com/12379monty/gse96058). The IHC ER counts in both GEO series matrices matched exactly. On 10 November 2026 the full GEO expression file was downloaded (MD5 4362d1d9…a0ab) and every value was compared with the analysed matrix: all 30,865 genes and 3409 libraries were present in both, and all 105,218,785 values agreed (largest absolute difference 9.5 × 10⁻⁷, the precision of the stored values).")

# ---------------- terminology
rep("and truly ER-negative (both low).", "and concordant ER-negative (ESR1 low, activity low; that is, negative by IHC and by both transcriptomic measures).")
rep("- **truly ER-negative:** 160", "- **concordant ER-negative:** 160")
rep("| Truly ER-negative |", "| Concordant ER-negative |")
body = body.replace("truly ER-negative", "concordant ER-negative")
assert "ruly ER-negative" not in body

# ---------------- methods: new section, reorder, retitle
s25, s26, s27, s28 = section("### 2.5. Composition-Adjusted"), section("### 2.6. ESR1-Targeting MicroRNAs"), section("### 2.7. TNBC Cell Lines"), section("### 2.8. Post Hoc Checks")
s29, s210 = section("### 2.9. Statistics"), section("### 2.10. Use of Generative AI")
new_ext_m = '''### 2.7. External Cohort (Amendment A4)

After co-author review, one external cohort was added in a fourth amendment (A4; SHA-256 ffad9bcf…f1a8; 10 November 2026). The amendment and its decision rules were hashed after reading only the sample annotation of the series, and before any expression value was read. The analysis is post hoc.

GSE25066 [@Hatzis] contains Affymetrix HG-U133A profiles (MAS5, log2) of 508 pre-treatment breast cancer biopsies from a neoadjuvant chemotherapy study of HER2-negative disease, with local IHC ER status. IHC ER-negative tumours (n = 205) were analysed, and IHC ER-positive tumours (n = 297) anchored the thresholds. Six tumours with indeterminate or missing ER status were excluded. The series has no technical replicates and no library-level technical variables, so the reproducibility analysis and the technical-only model could not be repeated. The outcome fields of the series were not used.

- **Measurements.** Probe sets were mapped to genes with the GEO platform annotation, taking for each gene the probe set with the highest mean across all samples (12,502 genes; ESR1 probe set 205225_at). The ESR1 axis, the primary activity score (292 Hallmark genes present, ESR1 removed) and the alternative scores were computed with the same code as in SCAN-B.
- **Thresholds.** Thresholds were re-anchored to the 5th percentile (1st and 10th as alternatives) of each measure among the cohort's own IHC ER-positive tumours. SCAN-B thresholds were not transferred, because the platforms differ.
- **Analyses.** These were the four-group prevalence with Wilson CIs; the HEA count under each alternative definition, including the single-gene ESR1 call deposited with the series; PAM50 subtype (as deposited) by group; AR and FOXA1 expression in the activity-without-ESR1 group against the concordant ER-negative group (Mann–Whitney U); and HEA prevalence by contributing centre (permutation test, 9999 permutations).
- **Decision rules, fixed in the amendment.** Prevalence was called consistent with SCAN-B if the Newcombe 95% CI for the difference from the SCAN-B HER2-negative stratum included zero. Dependence on definition was called replicated if the highest HEA count across definitions was at least three times the lowest. Composition was called replicated if at least half of the HEA tumours were PAM50 luminal or Normal-like and AR was higher in the activity-without-ESR1 group than in the concordant ER-negative group (p < 0.05).

'''
s28n = s28.replace("### 2.8. Post Hoc Checks", "### 2.6. Post Hoc Checks")
s26n = s26.replace("### 2.6. ESR1-Targeting MicroRNAs (Amendment A1)", "### 2.8. Exploratory Context: ESR1-Targeting MicroRNAs (Amendment A1)\n\nThis analysis and the next do not test HEA tumours. They use other samples and are reported as exploratory context for mechanisms that could separate ESR1 transcription from ER protein.")
s27n = s27.replace("### 2.7. TNBC Cell Lines (Amendment A1)", "### 2.9. Exploratory Context: TNBC Cell Lines (Amendment A1)")
s29n = s29.replace("### 2.9. Statistics", "### 2.10. Statistics")
s210n = s210.replace("### 2.10. Use of Generative AI", "### 2.11. Use of Generative AI")
old_block = s25 + s26 + s27 + s28 + s29 + s210
assert old_block in body
body = body.replace(old_block, s25 + s28n + new_ext_m + s26n + s27n + s29n + s210n)

rep("No external validation cohort was permitted under the study's data rule; internal validation relied on technical replicates, the platform split and nested cross-validation.",
"Internal validation relied on technical replicates, the platform split and nested cross-validation; external validation used GSE25066 (Section 2.7).")
rep("GSE38167 values, GSE337499 FPKM rows and GSE337500 bigWig windows were read in a web browser by HTTP range requests, because the computing environment could not reach GEO.",
"GSE38167 values, GSE337499 FPKM rows and GSE337500 bigWig windows were read in a web browser by HTTP range requests, because the computing environment could not reach GEO at that time. The GSE25066 series matrix and the full GSE96058 expression file were downloaded directly from GEO on 10 November 2026.")
rep("Code, the hashed analysis plan, the three amendments and the deviations log are available at github.com/MohannadBanat/er-negative-hidden-er-activity (private during review; public on submission).",
"Code, the hashed analysis plan, the four amendments and the deviations log are available at github.com/MohannadBanat/er-negative-hidden-er-activity and archived on Zenodo (https://doi.org/10.5281/zenodo.24039825).")

# ---------------- results: reorder, new section, renumber tables
r37, r38, r39 = section("### 3.7. ESR1-Targeting MicroRNAs in TNBC"), section("### 3.8. The ESR1 Locus in TNBC Cell Lines"), section("### 3.9. Post Hoc Checks")
t5 = open(T5, encoding="utf8").read().strip()
new_ext_r = '''### 3.8. External Cohort (GSE25066)

In GSE25066, the 5th-percentile ESR1 threshold among IHC ER-positive tumours was 9.34 log2 units. Among the 205 IHC ER-negative tumours, 39 were called HEA (19.0%, 95% CI 14.2–24.9; Table 5). Each of the three decision rules fixed in amendment A4 is reported below.

- **Prevalence: not consistent with SCAN-B.** HEA prevalence was 12.4 percentage points higher than in the SCAN-B HER2-negative stratum (95% CI 5.5–19.0) and 10.7 points higher than in all SCAN-B IHC ER-negative tumours (4.4–17.3). The activity-without-ESR1 group was also larger (37.6% against 24.1%), and the concordant ER-negative group was smaller (37.1% against 66.4%).
- **Dependence on definition: replicated.** The HEA count ranged from 23 (11.2%) at the 10th-percentile thresholds to 119 (58.0%) at the 1st-percentile thresholds, a 5.2-fold range. The single-gene ESR1 call deposited with the series classified 25 IHC ER-negative tumours (12.2%) as ESR1-positive; its agreement with the primary HEA call was κ 0.67. As in SCAN-B, the alternative activity scores changed the count little (39–43), and the threshold percentile changed it most.
- **Composition: not replicated in full.** The first condition was met: 20 of the 39 HEA tumours were PAM50 luminal (10) or Normal-like (10), against 3 of 76 concordant ER-negative tumours (none luminal, 3 Normal-like). However, 16 HEA tumours (41%) were Basal-like, against 2 of 20 in SCAN-B. The second condition was not met: AR expression was not clearly higher in the activity-without-ESR1 group than in the concordant ER-negative group (medians 7.85 and 7.73 log2 units; rank-biserial correlation 0.14; p = 0.13), and FOXA1 gave a similar result (p = 0.19). Only 13 of 77 tumours in this group were PAM50 HER2-enriched, against 38 of 58 in SCAN-B.

HEA prevalence varied between contributing centres, from 3 of 27 (11.1%) to 7 of 21 (33.3%), without clear evidence of heterogeneity (permutation p = 0.14).

''' + t5 + "\n\n"
r39n = r39.replace("### 3.9. Post Hoc Checks", "### 3.7. Post Hoc Checks")
r37n = r37.replace("### 3.7. ESR1-Targeting MicroRNAs in TNBC", "### 3.9. Exploratory Context: ESR1-Targeting MicroRNAs in TNBC").replace("Table 5", "Table 6")
r38n = r38.replace("### 3.8. The ESR1 Locus in TNBC Cell Lines", "### 3.10. Exploratory Context: The ESR1 Locus in TNBC Cell Lines").replace("Table 6", "Table 7")
r38n = r38n.replace("This mirrors the \"activity without ESR1\" group in tumours.", "This resembles the \"activity without ESR1\" group in SCAN-B tumours, although the cell lines cannot be linked to those tumours.")
old_block = r37 + r38 + r39
assert old_block in body
body = body.replace(old_block, r39n + new_ext_r + r37n + r38n)

# ---------------- discussion
rep("In a population-based cohort of 241 IHC ER-negative breast cancers, a transcriptomic hidden-ER-activity call was present in about 1 in 12 tumours and was almost perfectly reproducible on re-sequencing. Its prevalence, however, varied about eight-fold with reasonable choices of threshold and classifier.",
"In a population-based cohort of 241 IHC ER-negative breast cancers, a transcriptomic hidden-ER-activity call was present in about 1 in 12 tumours and was almost perfectly reproducible on re-sequencing. Its prevalence, however, varied about eight-fold with reasonable choices of threshold and classifier. In an external microarray cohort it was more than twice as common (19%), which shows that the figure also depends on the cohort.")
rep("Both analyses agree that the borderline transcriptionally luminal subset is small.",
"Both analyses agree that the borderline transcriptionally luminal subset is small.\n\nThe external cohort did not reproduce this figure. With the same definition and thresholds re-anchored to its own IHC ER-positive tumours, 19.0% of IHC ER-negative tumours in GSE25066 were called HEA, against 6.7% of HER2-negative tumours in SCAN-B. We did not predict this, and by the rule fixed in advance the prevalence was not replicated. Several differences between the cohorts could contribute, and the data cannot separate them. GSE25066 is a multi-centre neoadjuvant series of pre-treatment biopsies, not a population-based cohort of surgical specimens. Its IHC was performed locally with the criteria of the time, so its ER-negative group may include tumours that would now be called ER-low. Its ESR1 values come from a single microarray probe set. Whatever the cause, the practical conclusion is the same as for the threshold: a prevalence of \"hidden ER activity\" is a property of the definition, the platform and the cohort together, and a single figure should not be carried from one setting to another.")
rep("They should be interpreted with that caveat in ER-negative disease, even though the same scores are informative in ER-positive tumours [@R33].",
"They should be interpreted with that caveat in ER-negative disease, even though the same scores are informative in ER-positive tumours [@R33]. The external cohort qualifies this explanation. In GSE25066, half of the HEA tumours were again luminal or Normal-like, but two-fifths were Basal-like, and the activity-without-ESR1 group was not clearly AR-high. That cohort was selected for HER2-negative disease, and in SCAN-B the AR-high tumours were mostly HER2-enriched, so the AR explanation may apply mainly where HER2-positive tumours are included. The composition of these groups therefore also varies between cohorts.")
rep(para("The supporting layers add plausibility, not proof."),
"The microRNA and cell-line analyses are exploratory context and do not test HEA tumours. miR-18a, which directly targets the ESR1 3′UTR [@R41], was higher in TNBC than in paired normal tissue in two small datasets. This is compatible with post-transcriptional repression of ER in TNBC, and with proposals to use microRNAs to refine the classification of ER-negative breast cancer [@R42], but it does not show that miR-18a explains HEA. miR-206, an established ER-repressing microRNA [@R38], gave discordant results, plausibly because it was near the array's detection limit. In the eight cell lines, the ESR1 promoter was accessible in some lines despite little or no transcription, so a closed promoter may not be the only explanation for ESR1 silence. This does not contradict reports that ESR1 promoter methylation is associated with ER negativity and is more frequent in TNBC [@R45;@R46]. Methylation and accessibility are distinct layers, and we did not measure methylation. Neither analysis can be linked to individual SCAN-B tumours, and both would need testing in tumours with matched IHC, RNA and microRNA data.")
rep("- **Single cohort.** Only one cohort with expression, IHC and treatment data was permitted, so there is no external validation of the main analysis.",
"- **External cohort.** The external cohort was added post hoc and differs from SCAN-B in platform, population, specimen type and IHC practice. It has no replicate pairs or technical variables, so reproducibility and the technical-only control were tested in SCAN-B only. Its disagreement on prevalence cannot be assigned to any one of these differences.")
rep("- **Data limitations of the supporting layers.**", "- **Data limitations of the exploratory analyses.**")
rep("- **Data access.** Some data were read from GEO through a browser rather than downloaded in full. The values were checked against the source.",
"- **Data access.** Some of the smaller datasets were read from GEO through a browser rather than downloaded in full, and those values were checked against the source. The SCAN-B matrix was verified in full against the GEO file.")
rep("Its hash and timestamp, the three dated amendments and the deviations log are, however, released with the code. The checks in amendments A2 and A3 were added after the main results were known and are reported as exploratory.",
"Its hash and timestamp, the four dated amendments and the deviations log are, however, released with the code. The analyses in amendments A2–A4 were added after the main results were known and are reported as post hoc.")
rep("Studies proposing RNA-based rescue of endocrine therapy for IHC ER-negative patients should establish definitional stability, test technical-only and composition controls,",
"Studies proposing RNA-based rescue of endocrine therapy for IHC ER-negative patients should establish definitional stability, show that the call transfers between cohorts and platforms, test technical-only and composition controls,")

# ---------------- conclusions, supplementary, back matter
rep(para("Hidden ER activity in IHC ER-negative breast cancer was found in about 8%"),
"Hidden ER activity in IHC ER-negative breast cancer was found in about 8% of tumours in a population-based RNA-sequencing cohort and in 19% in an external microarray cohort. The call was technically reproducible, but its prevalence depended strongly on its definition and on the cohort. In SCAN-B it combined luminal tumours discordant with IHC and likely normal-tissue admixture, a technical-only control predicted it beyond chance, and a neighbouring group showed AR-driven transcription. The composition was only partly reproduced in the external cohort. Transcriptomic ER calls in IHC ER-negative tumours should not be used alone to guide endocrine therapy, and future studies need quantitative IHC, outcome data, pre-specified technical controls and evidence that the call transfers between cohorts.")
rep("Supplementary Data: analysis plan, amendments A1–A3,", "Supplementary Data: analysis plan, amendments A1–A4,")
rep("under accessions GSE96058, GSE40049, GSE38167, GSE337499 and GSE337500. Analysis code, the hashed analysis plan, the three amendments and the deviations log are available at https://github.com/MohannadBanat/er-negative-hidden-er-activity and archived on Zenodo (version 1.0; https://doi.org/10.5281/zenodo.24039826).",
"under accessions GSE96058, GSE25066, GSE40049, GSE38167, GSE337499 and GSE337500. Analysis code, the hashed analysis plan, the four amendments and the deviations log are available at https://github.com/MohannadBanat/er-negative-hidden-er-activity and archived on Zenodo (https://doi.org/10.5281/zenodo.24039825).")
rep("and the authors of GSE40049, GSE38167, GSE337499 and GSE337500 for making their data public.", "and the authors of GSE25066, GSE40049, GSE38167, GSE337499 and GSE337500 for making their data public.")

# ---------------- renumber references by first appearance
order = []
for m in re.finditer(r"\[(@[A-Za-z0-9]+(?:;@[A-Za-z0-9]+)*)\]", body):
    for k in m.group(1).split(";"):
        if k[1:] not in order: order.append(k[1:])
num = {k: i + 1 for i, k in enumerate(order)}
def fmt(keys):
    ns = sorted(num[k[1:]] for k in keys.split(";")); groups, run = [], [ns[0]]
    for n in ns[1:]:
        if n == run[-1] + 1: run.append(n)
        else: groups.append(run); run = [n]
    groups.append(run)
    return "\\[" + ",".join(f"{g[0]}–{g[-1]}" if len(g) > 2 else ",".join(map(str, g)) for g in groups) + "\\]"
body = re.sub(r"\[(@[A-Za-z0-9]+(?:;@[A-Za-z0-9]+)*)\]", lambda m: fmt(m.group(1)), body)
unused = [k for k in refs if k not in num]; assert not [k for k in order if k not in refs]
open(OUT, "w", encoding="utf8").write(body + "## References\n\n" + "\n".join(f"{i}. {refs[k]}" for i, k in enumerate(order, 1)) + "\n\n" + tail)
print("refs:", len(order), "unused:", unused, "| Hatzis =", num["Hatzis"], "| GRRAS =", num["R47"], "REMARK =", num["R48"])
