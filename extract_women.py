import os
import glob
import pandas as pd


# Paths
DATA_DIR = "./data"
OUTPUT_DIR = "./output"
LANGUAGES = ["en", "es", "fr", "tr"]


for lang in LANGUAGES:
    lang_dir = os.path.join(DATA_DIR, lang)
    
    if not os.path.exists(lang_dir):
        print(f"{lang_dir} not found")
        continue
 
    # Buscar todos los archivos que terminan en "en.tsv"
    pattern = os.path.join(lang_dir, "*en.tsv")
    files = glob.glob(pattern)
 
    if not files:
        print(f"File for {lang_dir} not found")
        continue
 
    print(f"\nLanguage: {lang} — {len(files)} files")
 
    dfs = []
    for filepath in files:
        try:
            df = pd.read_csv(filepath, sep="\t", dtype=str, low_memory=False)
            dfs.append(df)
        except Exception as e:
            print(f"  Error: {os.path.basename(filepath)}: {e}")
 
    if not dfs:
        print(f" Couldn't read the file {lang}")
        continue
 
    combined = pd.concat(dfs, ignore_index=True)
    total_rows = len(combined)

# filter
    if "Speaker_gender" not in combined.columns:
        print(f"Gender not found in {lang} files")
        continue

    women = combined[combined["Speaker_gender"].str.strip().str.upper().isin(["F", "FEMALE"])]
    women_rows = len(women)
 
    output_file = os.path.join(OUTPUT_DIR, f"women_{lang}.tsv")
    women.to_csv(output_file, sep="\t", index=False)
 
    print(f" Total files: {total_rows} | Women: {women_rows} | Save at: {output_file}")