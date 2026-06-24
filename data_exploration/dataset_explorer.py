import os
import json
from pathlib import Path
from collections import defaultdict

DATASET_PATH = Path("D:/XAMPP/htdocs")

kit_folders = [f for f in DATASET_PATH.iterdir() if f.is_dir()]
print(f"Total kit instances found: {len(kit_folders)}")

# ── STEP 2: Understand the nested structure ──────────
# Each hash folder contains one subfolder — that subfolder name is the family
print("\n── Peeking at first 10 kits ──")

family_counts = defaultdict(int)
kits_with_no_subfolder = []
kits_with_multiple_subfolders = []

for kit_path in kit_folders:
    # Get all subdirectories inside this hash folder
    subfolders = [f for f in kit_path.iterdir() if f.is_dir()]
    
    if len(subfolders) == 0:
        kits_with_no_subfolder.append(kit_path.name)
    elif len(subfolders) > 1:
        kits_with_multiple_subfolders.append(kit_path.name)
    else:
        # Exactly one subfolder — this is the family name
        family_name = subfolders[0].name
        family_counts[family_name] += 1

# ── STEP 3: Print what we found ──────────────────────
print(f"\nKits with exactly 1 family subfolder: {len(family_counts)}")
print(f"Kits with NO subfolder: {len(kits_with_no_subfolder)}")
print(f"Kits with MULTIPLE subfolders: {len(kits_with_multiple_subfolders)}")

print(f"\nUnique family names found: {len(family_counts)}")

print("\n── Top 20 most common families ──")
sorted_families = sorted(family_counts.items(), key=lambda x: x[1], reverse=True)
for family, count in sorted_families[:20]:
    print(f"  {family:<30} {count} kits")

print("\n── Sample of rare families (appear only once) ──")
rare = [(f, c) for f, c in family_counts.items() if c == 1]
print(f"  Families with only 1 kit: {len(rare)}")
for family, count in rare[:10]:
    print(f"  {family}")

# ── STEP 4: File type breakdown across all kits ──────
print("\n── File type distribution across entire dataset ──")
file_type_counts = defaultdict(int)
total_files = 0

for kit_path in kit_folders:
    subfolders = [f for f in kit_path.iterdir() if f.is_dir()]
    if len(subfolders) == 1:
        kit_root = subfolders[0]  # e.g. the N26N folder
        for file in kit_root.rglob("*"):
            if file.is_file():
                ext = file.suffix.lower() if file.suffix else "(no extension)"
                file_type_counts[ext] += 1
                total_files += 1

print(f"  Total files across all kits: {total_files}")
print("\n  Extension breakdown:")
for ext, count in sorted(file_type_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
    pct = (count / total_files) * 100
    print(f"  {ext:<20} {count:>8} files  ({pct:.1f}%)")

# ── STEP 5: Save the manifest ────────────────────────
print("\n── Building and saving dataset manifest ──")
manifest = []

for kit_path in kit_folders:
    subfolders = [f for f in kit_path.iterdir() if f.is_dir()]
    if len(subfolders) == 1:
        family_name = subfolders[0].name
        kit_root = subfolders[0]
        
        files = list(kit_root.rglob("*"))
        file_list = [str(f.relative_to(kit_root)) for f in files if f.is_file()]
        
        manifest.append({
            "hash": kit_path.name,
            "family": family_name,
            "kit_root": str(kit_root),
            "file_count": len(file_list),
            "files": file_list
        })

with open("dataset_manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

print(f"  Manifest saved: {len(manifest)} kits → dataset_manifest.json")
print("\n✓ Day 1 complete. You now know your dataset.")