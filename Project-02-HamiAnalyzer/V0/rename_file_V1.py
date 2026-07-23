import os
import re
import uuid
from collections import defaultdict

"""
Rename files so that within each group sharing the same first number, the second numbers are reversed.

Input filenames are expected to follow the pattern (extension optional):
  - file_{first}_{second}[.ext]
  - workflow_{first}_{second}[.ext]

This script DOES NOT change the first number. It only remaps the second number so that
the largest original second becomes 1, the next becomes 2, ..., and the smallest becomes N.

Safety features:
  - Dry run mode (default) to preview changes
  - Collision checks and two-phase renaming to avoid overwrite risks
"""

# === CONFIG ===
# files_dir = "/mnt/Data1/Python_Projects/Datasets/Hami_Data/hami_data"
# dry_run = False  # Set to False to actually perform renames


def main(files_dir, dry_run=False):
    # === COLLECT files matching pattern file_{i}_{j} or workflow_{i}_{j} ===
    pattern = re.compile(r"^(file|workflow)_(\d+)_(\d+)$")
    entries = []  # list of dicts: {fname, prefix, firstnum, secondnum, ext}

    try:
        dir_listing = os.listdir(files_dir)
    except FileNotFoundError:
        raise FileNotFoundError(f"Directory not found: {files_dir}")

    for fname in dir_listing:
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
        return

    # === GROUP BY firstnum and build second-number reverse mapping per firstnum ===
    groups = defaultdict(list)
    for e in entries:
        groups[e["firstnum"]].append(e)

    rename_map = {}  # old filename -> new filename

    for firstnum, items in groups.items():
        # Ascending unique seconds for stable mapping
        unique_js = sorted({it["secondnum"] for it in items})
        N = len(unique_js)
        # map: old_j -> reversed index (largest old_j -> 1, smallest -> N)
        second_map = {j: (N - idx) for idx, j in enumerate(unique_js)}

        for it in items:
            new_second = second_map[it["secondnum"]]
            # Keep the first number unchanged
            new_name = f"{it['prefix']}_{it['firstnum']}_{new_second}{it['ext']}"
            if new_name in rename_map.values():
                raise ValueError(f"Duplicate target name detected: {new_name}. Aborting to avoid data loss.")
            rename_map[it["fname"]] = new_name

    # === SAFETY CHECKS ===
    existing_files = set(os.listdir(files_dir))
    final_names = set(rename_map.values())

    # If any final name already exists in directory but isn't one of the files we're renaming -> conflict
    conflicts = [n for n in final_names if (n in existing_files and n not in rename_map.keys())]
    if conflicts:
        raise ValueError(
            "The following target filenames already exist and are not part of the rename set:\n"
            + "\n".join(conflicts)
        )

    # === SHOW / EXECUTE ===
    if dry_run:
        print("DRY RUN: the following renames would be performed:")
        for old, new in sorted(rename_map.items()):
            print(f"{old}  ->  {new}")
        print("\nNo files were changed (dry_run=True). Set dry_run=False to apply changes.")
        return

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


# main("/mnt/Data1/Python_Projects/Datasets/Hami_Data/hami_data", False)
