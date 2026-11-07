"""Merge new Introduction/Discussion into manuscript.md, convert all citations to keys,
renumber references by order of first appearance (MDPI rule), rebuild the reference list."""
import re, sys
MS, INTRO, DISC, OUT = sys.argv[1:5]
md = open(MS, encoding="utf8").read()

# ---- old reference list -> dict R1..R31
refs_start = md.index("## References")
refs_end = md.index("## Before submission")
old = {}
for line in md[refs_start:refs_end].splitlines():
    m = re.match(r"^(\d+)\.\s+(.*)$", line)
    if m: old[f"R{m.group(1)}"] = m.group(2)
assert len(old) == 31, len(old)

NEW = {
"Malainou": "Malainou, C.P.; Stachika, N.; Damianou, A.K.; Anastopoulos, A.; Ploumaki, I.; Triantafyllou, E.; et al. Estrogen-Receptor-Low-Positive Breast Cancer: Pathological and Clinical Perspectives. *Curr. Oncol.* **2023**, *30*, 9734–9745. https://doi.org/10.3390/curroncol30110706",
"Reinert": "Reinert, T.; Cascelli, F.; de Resende, C.A.A.; Gonçalves, A.C.; Godo, V.S.P.; Barrios, C.H. Clinical Implication of Low Estrogen Receptor (ER-Low) Expression in Breast Cancer. *Front. Endocrinol.* **2022**, *13*, 1015388. https://doi.org/10.3389/fendo.2022.1015388",
"Faa": "Faa, G.; Lai, E.; Ziranu, P.; Pretta, A.; Tiwari, E.; Dessì, M.; et al. Estrogen Receptor-Low Positive (ER-Low) Breast Cancer: A Unique Clinical and Pathological Entity. *Curr. Oncol.* **2026**, *33*, 122. https://doi.org/10.3390/curroncol33020122",
"Xia": "Xia, F.; Hu, X.; Zhang, L.; Peng, X.; Xie, M. Association between Endocrine Therapy and Survival Outcomes in Estrogen Receptor–Low Breast Cancer: A Systematic Review and Meta-Analysis. *Oncologist* **2026**, *31*, oyag230. https://doi.org/10.1093/oncolo/oyag230",
"Xie": "Xie, Y.; Yang, L.; Wu, Y.; Zheng, H.; Gou, Q. Adjuvant Endocrine Therapy in Patients with Estrogen Receptor-Low Positive Breast Cancer: A Prospective Cohort Study. *Breast* **2022**, *66*, 89–96. https://doi.org/10.1016/j.breast.2022.09.008",
"Yang": "Yang, Q.; Boyaci, C.; Zerdes, I.; Fredriksson, I.; Chen, X.; Hartman, J.; et al. Patient Characteristics, Treatment Patterns, and Survival across Estrogen Receptor Expression Subgroups in HER2-Negative Breast Cancer: A Population-Based Cohort Study. *Lancet Reg. Health Eur.* **2026**, *68*, 101826. https://doi.org/10.1016/j.lanepe.2026.101826",
"Kushnarev": "Kushnarev, V.; Stupichev, D.; Davitavyan, S.; Kriukov, K.; Shanthappa, B.U.; Butusova, A.; et al. RNA Sequencing and Immunohistochemistry Jointly Improve Tumor Biomarker Interpretation. *Sci. Rep.* **2025**, *15*, 28264. https://doi.org/10.1038/s41598-025-12780-3",
"Erber": "Erber, R.; Hartmann, A.; Fasching, P.A.; Ruebner, M.; Stöhr, R.; Beckmann, M.W.; et al. Reproducibility of mRNA-Based Testing of ESR1, PGR, ERBB2, and MKI67 Expression in Invasive Breast Cancer—A Europe-Wide External Quality Assessment. *Cancers* **2021**, *13*, 4718. https://doi.org/10.3390/cancers13184718",
"Engstrom": "Engström, T.; Ekholm, M.; Fernö, M.; Lundgren, C.; Nordenskjöld, B.; Stål, O.; et al. Hormone Receptor mRNA and Protein Levels as Predictors of Premenopausal Tamoxifen Benefit. *Acta Oncol.* **2024**, *63*, 125–136. https://doi.org/10.2340/1651-226X.2024.19655",
"Fakhri": "Fakhri, G.B.; Akel, R.S.; Khalil, M.K.; Mukherji, D.A.; Boulos, F.I.; Tfayli, A.H. Concordance between Immunohistochemistry and Microarray Gene Expression Profiling for Estrogen Receptor, Progesterone Receptor, and HER2 Receptor Statuses in Breast Cancer Patients in Lebanon. *Int. J. Breast Cancer* **2018**, *2018*, 8530318. https://doi.org/10.1155/2018/8530318",
"Holm": "Holm, J.; Yu, N.Y.; Johansson, A.; Ploner, A.; Hall, P.; Lindström, L.S.; et al. Concordance of Immunohistochemistry-Based and Gene Expression-Based Subtyping in Breast Cancer. *JNCI Cancer Spectr.* **2021**, *5*, pkaa087. https://doi.org/10.1093/jncics/pkaa087",
"Berg": "Berg, T.; Jensen, M.-B.; Celik, A.; Talman, M.-L.; Misiakou, M.A.; Knoop, A.S.; et al. Molecular Subtyping Improves Breast Cancer Diagnosis in the Copenhagen Breast Cancer Genomics Study. *JCI Insight* **2024**, *9*, e178114. https://doi.org/10.1172/jci.insight.178114",
"Hohmann": "Hohmann, L.; Nacer, D.F.; Aine, M.; Memari, Y.; Black, D.; Bowden, R.; et al. Molecular Profiling of the Basal-like Intrinsic Molecular Subtype in Primary ER-Positive HER2-Negative Breast Cancer. *Genome Med.* **2025**, *17*, 146. https://doi.org/10.1186/s13073-025-01576-9",
"Hurson": "Hurson, A.N.; Hamilton, A.M.; Olsson, L.T.; Kirk, E.L.; Sherman, M.E.; Calhoun, B.C.; et al. Reproducibility and Intratumoral Heterogeneity of the PAM50 Breast Cancer Assay. *Breast Cancer Res. Treat.* **2023**, *199*, 147–154. https://doi.org/10.1007/s10549-023-06888-1",
"Saghir": "Saghir, H.; Veerla, S.; Malmberg, M.; Rydén, L.; Ehinger, A.; Saal, L.H.; et al. How Reliable Are Gene Expression-Based and Immunohistochemical Biomarkers Assessed on a Core-Needle Biopsy? A Study of Paired Core-Needle Biopsies and Surgical Specimens in Early Breast Cancer. *Cancers* **2022**, *14*, 4000. https://doi.org/10.3390/cancers14164000",
"Lee": "Lee, M.; Yoo, T.-K.; Chae, B.J.; Lee, A.; Cha, Y.J.; Lee, J.; et al. Luminal Androgen Receptor Subtype and Tumor-Infiltrating Lymphocytes Groups Based on Triple-Negative Breast Cancer Molecular Subclassification. *Sci. Rep.* **2024**, *14*, 11278. https://doi.org/10.1038/s41598-024-61640-z",
"Bonnefoi": "Bonnefoi, H.; MacGrogan, G.; Poncet, C.; Iggo, R.; Pommeret, F.; Grellety, T.; et al. Molecular Apocrine Tumours in EORTC 10994/BIG 1-00 Phase III Study: Pathological Response after Neoadjuvant Chemotherapy and Clinical Outcomes. *Br. J. Cancer* **2019**, *120*, 913–921. https://doi.org/10.1038/s41416-019-0420-y",
"Dai": "Dai, C.; Ellisen, L.W. Revisiting Androgen Receptor Signaling in Breast Cancer. *Oncologist* **2023**, *28*, 383–391. https://doi.org/10.1093/oncolo/oyad049",
"Angus": "Angus, L.; Smid, M.; Wilting, S.M.; Bos, M.K.; Steeghs, N.; Konings, I.R.H.M.; et al. Genomic Alterations Associated with Estrogen Receptor Pathway Activity in Metastatic Breast Cancer Have a Differential Impact on Downstream ER Signaling. *Cancers* **2023**, *15*, 4416. https://doi.org/10.3390/cancers15174416",
"Tran": "Tran, K.A.; Addala, V.; Johnston, R.L.; Lovell, D.; Bradley, A.; Koufariotis, L.T.; et al. Performance of Tumour Microenvironment Deconvolution Methods in Breast Cancer Using Single-Cell Simulated Bulk Mixtures. *Nat. Commun.* **2023**, *14*, 5758. https://doi.org/10.1038/s41467-023-41385-5",
"Turova": "Turova, P.; Kushnarev, V.; Baranov, O.; Butusova, A.; Menshikova, S.; Yong, S.T.; et al. The Breast Cancer Classifier Refines Molecular Breast Cancer Classification to Delineate the HER2-Low Subtype. *NPJ Breast Cancer* **2025**, *11*, 19. https://doi.org/10.1038/s41523-025-00723-0",
"Barreca": "Barreca, M.; Dugo, M.; Galbardi, B.; Győrffy, B.; NA-PHER2 Consortium; NeoTRIP Consortium; et al. Development and Validation of a Gene Expression-Based Breast Cancer Purity Score. *NPJ Precis. Oncol.* **2024**, *8*, 242. https://doi.org/10.1038/s41698-024-00730-7",
"Chamandi": "Chamandi, G.; El-Hajjar, L.; El Kurdi, A.; Le Bras, M.; Nasr, R.; Lehmann-Che, J. ER Negative Breast Cancer and miRNA: There Is More to Decipher Than What the Pathologist Can See! *Biomedicines* **2023**, *11*, 2300. https://doi.org/10.3390/biomedicines11082300",
"MartinezGalan": "Martínez-Galán, J.; Torres-Torres, B.; Núñez, M.I.; López-Peñalver, J.; Del Moral, R.; Ruiz De Almodóvar, J.M.; et al. ESR1 Gene Promoter Region Methylation in Free Circulating DNA and Its Correlation with Estrogen Receptor Protein Expression in Tumor Tissue in Breast Cancer Patients. *BMC Cancer* **2014**, *14*, 59. https://doi.org/10.1186/1471-2407-14-59",
"Mohanad": "Mohanad, M.; Hamza, H.M.; Bahnassy, A.A.; Shaarawy, S.; Ahmed, O.; El-Mezayen, H.A.; et al. Molecular Profiling of Breast Cancer Methylation Pattern in Triple Negative versus Non-Triple Negative Breast Cancer. *Sci. Rep.* **2025**, *15*, 6894. https://doi.org/10.1038/s41598-025-90150-9",
}
assert len(NEW) == 25

# ---- convert existing numeric citations anywhere outside the reference list to keys
def expand(spec):
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "–" in part or "-" in part:
            a, b = re.split("[–-]", part); out += list(range(int(a), int(b) + 1))
        else: out.append(int(part))
    return out
body = md[:refs_start]
body = re.sub(r"\\\[(\d+(?:\s*[–,-]\s*\d+)*)\\\]", lambda m: "[" + ";".join(f"@R{n}" for n in expand(m.group(1))) + "]", body)

# ---- swap in new Introduction and Discussion
def replace_section(text, head, new):
    i = text.index(head); j = text.index("\n## ", i + 3)
    return text[:i] + new.strip() + "\n\n" + text[j + 1:]
body = replace_section(body, "## 1. Introduction", open(INTRO, encoding="utf8").read())
body = replace_section(body, "## 4. Discussion", open(DISC, encoding="utf8").read())

# ---- renumber by first appearance
order = []
for m in re.finditer(r"\[(@[A-Za-z0-9]+(?:;@[A-Za-z0-9]+)*)\]", body):
    for k in m.group(1).split(";"):
        k = k[1:]
        if k not in order: order.append(k)
num = {k: i + 1 for i, k in enumerate(order)}
def fmt(keys):
    ns = sorted(num[k[1:]] for k in keys.split(";"))
    groups, run = [], [ns[0]]
    for n in ns[1:]:
        if n == run[-1] + 1: run.append(n)
        else: groups.append(run); run = [n]
    groups.append(run)
    parts = [f"{g[0]}–{g[-1]}" if len(g) > 2 else ",".join(map(str, g)) for g in groups]
    return "\\[" + ",".join(parts) + "\\]"
body = re.sub(r"\[(@[A-Za-z0-9]+(?:;@[A-Za-z0-9]+)*)\]", lambda m: fmt(m.group(1)), body)

allrefs = {**old, **NEW}
unused = [k for k in allrefs if k not in num]
missing = [k for k in order if k not in allrefs]
assert not missing, missing
reflist = "## References\n\n" + "\n".join(f"{i}. {allrefs[k]}" for i, k in enumerate(order, 1)) + "\n\n"
out = body + reflist + md[refs_end:]
open(OUT, "w", encoding="utf8").write(out)
print("references:", len(order), "| unused:", unused)
print("new refs cited:", sum(k in num for k in NEW), "/ 25")
print("order:", ", ".join(f"{num[k]}={k}" for k in order))
