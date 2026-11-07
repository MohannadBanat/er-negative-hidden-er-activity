"""Step 1: load GSE96058 from the GitHub split of the GEO files.

Survival columns are moved to a separate locked file and are not
printed or summarised here (they stay unread until the analysis plan
is hashed).
"""
import sys, pathlib, hashlib
import pyreadr
import pandas as pd

SRC = pathlib.Path(sys.argv[1])          # .../gse96058/data
OUT = pathlib.Path(sys.argv[2])          # project data dir
OUT.mkdir(parents=True, exist_ok=True)

def load(name):
    r = pyreadr.read_r(str(SRC / f"{name}.rda"))
    return next(iter(r.values()))

samp = load("GSE96058_sampDesc")
OUTCOME_COLS = [c for c in samp.columns if c.lower().startswith("ovrallsurv")]
samp[["title"] + OUTCOME_COLS].to_parquet(OUT / "LOCKED_outcomes.parquet")
samp = samp.drop(columns=OUTCOME_COLS)
samp.to_parquet(OUT / "sampdesc.parquet")

genes = load("GSE96058_genes_annot")
parts = []
for n in ["sub1", "sub2", "sub3", "sub4", "sub5", "repl1", "repl2"]:
    df = load(f"GSE96058_geneExpression_{n}")
    parts.append(df)
    print(n, df.shape)
expr = pd.concat(parts, axis=1)
gene_ids = None
# pyreadr drops data.frame rownames from data.table objects; recover from annotation order
if expr.index.dtype != object or expr.index[0] == 0:
    gene_ids = genes["geneSymbol"].astype(str).values
    assert len(gene_ids) == expr.shape[0], (len(gene_ids), expr.shape)
    expr.index = gene_ids
expr.columns = expr.columns.astype(str)
expr.astype("float32").to_parquet(OUT / "expr.parquet")

print("expr", expr.shape, "| outcome cols locked:", OUTCOME_COLS)
print("sampdesc cols:", list(samp.columns))
for f in ["sampdesc.parquet", "expr.parquet", "LOCKED_outcomes.parquet"]:
    h = hashlib.sha256((OUT / f).read_bytes()).hexdigest()
    print(f, h)
