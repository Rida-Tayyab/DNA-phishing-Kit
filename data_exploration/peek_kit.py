# peek_kit.py
import json
from pathlib import Path

with open("data_exploration/dataset_manifest.json") as f:
    manifest = json.load(f)

# Find kits with decent HTML files and PHP files — good to study
good_kits = [
    k for k in manifest 
    if k["html_count"] >= 2 and k["php_count"] >= 2 and k["useful_files"] > 10
]

print(f"Good kits to study: {len(good_kits)}\n")
for kit in good_kits[:5]:
    print(f"Family: {kit['family']}")
    print(f"  Root: {kit['kit_root']}")
    print(f"  PHP:{kit['php_count']}  HTML:{kit['html_count']}  JS:{kit['js_count']}")
    print(f"  Files: {kit['files'][:8]}")
    print()