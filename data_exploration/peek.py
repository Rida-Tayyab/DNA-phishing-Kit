# peek_php2.py
import json
from pathlib import Path

with open("data_exploration/dataset_manifest.json") as f:
    manifest = json.load(f)

# Find kits with email.php — the mail() based credential senders
email_kits = [
    k for k in manifest
    if any("email.php" in f.lower() for f in k["files"])
    and k["php_count"] >= 2
]

print(f"Kits with email.php: {len(email_kits)}\n")

for kit in email_kits[:3]:
    print(f"Family: {kit['family']}")
    print(f"Root:   {kit['kit_root']}")
    php_files = [f for f in kit["files"] if f.endswith(".php")]
    print(f"PHP:    {php_files[:5]}")
    print()