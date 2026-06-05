"""
ParlaMint Corpus Processor

merges ParlaMint metadata (*meta*.tsv) with corresponding .txt files
and exports one CSV per language folder.


to obtain the files: 
python process_parlamint.py
--root_dir /home/bersun/projects/DH/ParlaMint
--output_dir outputs 
--folders 2022tr
"""

import argparse
import glob
import os
import pandas as pd
from tqdm import tqdm
import openpyxl

# find TSV + TXT pairs

def find_file_pairs(input_dir: str):

    import re

    folder_name = os.path.basename(input_dir.rstrip("/"))

    tsv_files = sorted(
        glob.glob(os.path.join(input_dir, "*meta*.tsv"))
    )

    pairs = []

    for tsv_path in tsv_files:

        filename = os.path.basename(tsv_path)

        # extract base 
        base = re.sub(r"-meta(-en)?\.tsv$", "", filename)

        txt_path = os.path.join(input_dir, base + ".txt")

        if os.path.exists(txt_path):
            pairs.append((tsv_path, txt_path, folder_name))
        else:
            print(f"Missing TXT for {filename}")

    return pairs


# parse TXT corpus

def parse_txt(txt_path: str):
    rows = []

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:

            line = line.strip()
            if not line:
                continue

            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue

            rows.append({
                "ID": parts[0].strip(),   # KEEP FULL ID
                "Text": parts[1].strip()
            })

    return pd.DataFrame(rows)


# process one pair

def process_pair(tsv_path, txt_path, folder_name):

    df_meta = pd.read_csv(tsv_path, sep="\t", dtype=str)
    df_meta["ID"] = df_meta["ID"].astype(str).str.strip()

    df_txt = parse_txt(txt_path)
    df_txt["ID"] = df_txt["ID"].astype(str).str.strip()

    if df_meta.empty or df_txt.empty:
        return None

    merged = pd.merge(df_meta, df_txt, on="ID", how="left")

    merged["Source_folder"] = folder_name

    return merged


# main

DEFAULT_FOLDERS = ["2022en", "2022fr", "2022es", "2022tr"]


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", required=True)
    parser.add_argument("--folders", nargs="+", default=DEFAULT_FOLDERS)
    parser.add_argument("--output_dir", required=True)

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    for folder in args.folders:

        print("\n" + "=" * 60)
        print("Processing:", folder)
        print("=" * 60)

        folder_path = os.path.join(args.root_dir, folder)

        if not os.path.isdir(folder_path):
            print("[WARN] Missing folder:", folder_path)
            continue

        pairs = find_file_pairs(folder_path)

        print("Pairs found:", len(pairs))

        if not pairs:
            continue

        all_frames = []

        for tsv_path, txt_path, folder_name in tqdm(pairs, desc=folder):

            df = process_pair(tsv_path, txt_path, folder_name)

            if df is not None:
                print("Shape:", df.shape)
                all_frames.append(df)

        if not all_frames:
            print("[WARN] No data for:", folder)
            continue

        combined = pd.concat(all_frames, ignore_index=True)

        # reorder columns safely
        cols = list(combined.columns)

        if "Source_folder" in cols:
            cols.remove("Source_folder")
            cols.insert(0, "Source_folder")

        if "ID" in cols and "Text" in cols:
            cols.remove("Text")
            cols.insert(cols.index("ID") + 1, "Text")

        combined = combined[cols]

        
        out_base = os.path.join(args.output_dir, folder)

        out_tsv = out_base + ".tsv"
        out_xlsx = out_base + ".xlsx"        


        # TSV
        combined.to_csv(out_tsv, sep="\t", index=False, encoding="utf-8")
        print("Saved TSV:", out_tsv)
        # EXCEL
        combined.to_excel(out_xlsx, index=False, engine="openpyxl")
        print("📊 Saved Excel:", out_xlsx)

        print("Rows:", len(combined))


if __name__ == "__main__":
    main()