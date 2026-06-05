import os
import glob
import pandas as pd

# Paths 
DATA_DIR   = "./data"
OUTPUT_DIR = "./output"
LANGUAGES  = ["en", "es", "fr", "tr"]

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load and combined
all_dfs = []

for lang in LANGUAGES:
    lang_dir = os.path.join(DATA_DIR, lang)

    if not os.path.exists(lang_dir):
        print(f"DIR not found: {lang_dir}")
        continue

    pattern = os.path.join(lang_dir, "*en.tsv")
    files   = glob.glob(pattern)

    if not files:
        print(f" No *en.tsv files at {lang_dir}")
        continue

    print(f"\n[{lang.upper()}] {len(files)} files founded")

    dfs = []
    for filepath in files:
        try:
            df = pd.read_csv(filepath, sep="\t", dtype=str, low_memory=False)
            dfs.append(df)
        except Exception as e:
            print(f"  Error reading {os.path.basename(filepath)}: {e}")

    if not dfs:
        continue

    combined = pd.concat(dfs, ignore_index=True)
    combined["parliament"] = lang.upper()
    all_dfs.append(combined)
    print(f"  Rows: {len(combined):,}")

if not all_dfs:
    print("\n Error: no file was found.")
    exit(1)

master = pd.concat(all_dfs, ignore_index=True)
print(f"\n{'='*60}")
print(f"MAIN DATASET: {len(master):,} rows | {len(master.columns)} columns")

# Normalize gender: strip, uppercase, then unify '-' and 'U' → 'U'
master["Speaker_gender"] = (
    master["Speaker_gender"]
    .str.strip()
    .str.upper()
    .replace("-", "U")
)

# Filter out 'mix' and 'others' from Topic (case-insensitive)
topics_to_remove = {"MIX", "OTHERS", "OTHER"}
master = master[~master["Topic"].str.strip().str.upper().isin(topics_to_remove)]

# fix "other" problem in speaker_birth columns
master = master[~master["Speaker_birth"].astype(str).str.upper().str.contains("OTHER", na=False)]

# gender distribution by parlament
summary = (
    master.groupby(["parliament", "Speaker_gender"])
    .size()
    .unstack(fill_value=0)
)
summary["TOTAL"] = summary.sum(axis=1)
if "F" in summary.columns:
    summary["pct_F"] = (summary["F"] / summary["TOTAL"] * 100).round(1)

print(f"\nGender distribution by parlament:\n{summary}")

# topics
print(f"\nTopics ({master['Topic'].nunique()} types):")
print(master["Topic"].value_counts().head(20).to_string())

# save output
master_path = os.path.join(OUTPUT_DIR, "master_all.tsv")
master.to_csv(master_path, sep="\t", index=False)
print(f"\nMain dataset: {master_path}  ({len(master):,} rows)")

women = master[master["Speaker_gender"] == "F"]
women_path = os.path.join(OUTPUT_DIR, "master_women.tsv")
women.to_csv(women_path, sep="\t", index=False)
print(f"Only women dataset:  {women_path}  ({len(women):,} rows)")