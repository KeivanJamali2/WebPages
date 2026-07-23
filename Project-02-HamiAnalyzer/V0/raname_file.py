import os
import re
import pandas as pd
import uuid
from collections import defaultdict

# === CONFIG ===
csv_path = "/mnt/Data1/Python_Projects/Datasets/Hami_Data/extra_data/people_index.csv"
files_dir = "/mnt/Data1/Python_Projects/Datasets/Hami_Data/hami_data"
dry_run = False   # <<< Set to False to actually perform renames

# === READ CSV and build first-number mapping ===
df = pd.read_csv(csv_path)

# try to find a column with values like "file_12"
ref_col = "reference_id" if "reference_id" in df.columns else None
if ref_col is None:
    for c in df.columns:
        if df[c].astype(str).str.contains(r'file_\d+', na=False).any():
            ref_col = c
            break
# if ref_col is None:
#     raise ValueError("Couldn't locate a column containing values like 'file_12' in the CSV. "
#                      "Set `ref_col` manually or check the CSV path/format.")

# mapping: old_first_int (like 12) -> new_first_str (the 6-digit ID from first column)
mapping = {}
for _, row in df.iterrows():
    ref_val = str(row[ref_col])
    m = re.search(r'file_(\d+)', ref_val)
    if not m:
        continue
    old_first = int(m.group(1))
    new_first = str(row.iloc[0])   # first column value (assumed the 6-digit code)
    mapping[old_first] = new_first

# === COLLECT files matching pattern file_{i}_{j} or workflow_{i}_{j} ===
pattern = re.compile(r'^(file|workflow)_(\d+)_(\d+)$')
entries = []  # list of dicts: {fname, prefix, firstnum, secondnum, ext}
for fname in os.listdir(files_dir):
    name, ext = os.path.splitext(fname)
    m = pattern.match(name)
    if not m:
        continue
    prefix = m.group(1)
    firstnum = int(m.group(2))
    secondnum = int(m.group(3))
    entries.append({
        "fname": fname,
        "prefix": prefix,
        "firstnum": firstnum,
        "secondnum": secondnum,
        "ext": ext
    })

if not entries:
    print("No matching files found (pattern: file_{i}_{j} or workflow_{i}_{j}). Exiting.")
    raise SystemExit(0)

# === GROUP BY firstnum and build second-number reverse mapping per firstnum ===
groups = defaultdict(list)
for e in entries:
    groups[e["firstnum"]].append(e)

rename_map = {}  # old filename -> new filename

for firstnum, items in groups.items():
    unique_js = sorted({it["secondnum"] for it in items})  # sorted ascending
    N = len(unique_js)
    # map: old_j -> reversed index (largest old_j -> 1, smallest -> N)
    second_map = {j: (N - idx) for idx, j in enumerate(unique_js)}

    if firstnum not in mapping:
        print(f"Warning: no mapping found for first-number {firstnum}. Skipping these files:")
        for it in items:
            print("  -", it["fname"])
        continue

    new_first = mapping[firstnum]
    for it in items:
        new_second = second_map[it["secondnum"]]
        new_name = f"{it['prefix']}_{new_first}_{new_second}{it['ext']}"
        if new_name in rename_map.values():
            raise ValueError(f"Duplicate target name detected: {new_name}. Aborting to avoid data loss.")
        rename_map[it["fname"]] = new_name

# === SAFETY CHECKS ===
existing_files = set(os.listdir(files_dir))
final_names = set(rename_map.values())

# If any final name already exists in directory but isn't one of the files we're renaming -> conflict
conflicts = [n for n in final_names if (n in existing_files and n not in rename_map.keys())]
if conflicts:
    raise ValueError("The following target filenames already exist and are not part of the rename set:\n"
                     + "\n".join(conflicts))

# === SHOW / EXECUTE ===
if dry_run:
    print("DRY RUN: the following renames would be performed:")
    for old, new in sorted(rename_map.items()):
        print(f"{old}  ->  {new}")
    print("\nNo files were changed (dry_run=True). Set dry_run=False to apply changes.")
else:
    # Two-phase rename to avoid collisions: old -> temp -> final
    temp_map = {}  # temp_name -> final_name
    for old in rename_map:
        old_path = os.path.join(files_dir, old)
        if not os.path.exists(old_path):
            raise FileNotFoundError(f"Expected file not found: {old_path}")
        temp_name = f"__tmp_rename_{uuid.uuid4().hex}__{old}"
        temp_path = os.path.join(files_dir, temp_name)
        os.rename(old_path, temp_path)
        temp_map[temp_name] = rename_map[old]

    # now rename temps to final names
    for temp_name, final in temp_map.items():
        os.rename(os.path.join(files_dir, temp_name), os.path.join(files_dir, final))

    print("Renaming completed successfully.")
