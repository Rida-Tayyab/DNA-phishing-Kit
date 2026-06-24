# rebuild_manifest.py
import os
import json
from pathlib import Path
from collections import defaultdict

DATASET_PATH = Path("D:/XAMPP/htdocs")

# These are junk — never a real kit family
SKIP_FOLDERS = {"__MACOSX", "__pycache__", ".DS_Store"}

kit_folders = [f for f in DATASET_PATH.iterdir() if f.is_dir()]

manifest = []
skipped_no_valid_subfolder = []
family_counts = defaultdict(int)

for kit_path in kit_folders:
    subfolders = [
        f for f in kit_path.iterdir()
        if f.is_dir() and f.name not in SKIP_FOLDERS
    ]

    if len(subfolders) == 0:
        # No valid kit found inside this hash folder — skip
        skipped_no_valid_subfolder.append(kit_path.name)
        continue

    for kit_root in subfolders:
        # Each valid subfolder = one kit instance
        family_name = kit_root.name

        # Collect only useful file types — skip Mac junk and downloads
        SKIP_EXTENSIONS = {
            ".ds_store", ".download", ".bak",
            ".woff", ".woff2", ".ttf", ".eot",  # fonts — not useful
            ".gif", ".jpg", ".jpeg", ".png",     # images — not useful
            ".ico", ".svg",                       # icons — not useful
            ".pdf", ".zip"                        # archives — not useful
        }

        all_files = [f for f in kit_root.rglob("*") if f.is_file()]

        # Split into useful vs skipped
        useful_files = []
        for f in all_files:
            # Skip __MACOSX metadata files (start with ._)
            if f.name.startswith("._"):
                continue
            if "__MACOSX" in f.parts:
                continue
            if f.suffix.lower() in SKIP_EXTENSIONS:
                continue
            useful_files.append(str(f.relative_to(kit_root)))

        # Count by type for this kit
        php_files  = [f for f in useful_files if f.endswith(".php")]
        html_files = [f for f in useful_files if f.endswith((".html", ".htm"))]
        js_files   = [f for f in useful_files if f.endswith(".js")]
        css_files  = [f for f in useful_files if f.endswith(".css")]

        manifest.append({
            "hash":         kit_path.name,
            "family":       family_name,
            "kit_root":     str(kit_root),
            "total_files":  len(all_files),
            "useful_files": len(useful_files),
            "php_count":    len(php_files),
            "html_count":   len(html_files),
            "js_count":     len(js_files),
            "css_count":    len(css_files),
            "has_htaccess": any(".htaccess" in f for f in useful_files),
            "has_telegram": any("telegram" in f.lower() for f in useful_files),
            "files":        useful_files
        })

        family_counts[family_name] += 1

# ── Save manifest ────────────────────────────────────
with open("dataset_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

# ── Print summary ────────────────────────────────────
print("=" * 55)
print("  DATASET MANIFEST — FINAL SUMMARY")
print("=" * 55)
print(f"\n  Total kit instances:        {len(manifest)}")
print(f"  Unique family names:         {len(family_counts)}")
print(f"  Skipped (no valid subfolder):{len(skipped_no_valid_subfolder)}")

print(f"\n── File coverage ──")
total_php  = sum(k["php_count"]  for k in manifest)
total_html = sum(k["html_count"] for k in manifest)
total_js   = sum(k["js_count"]   for k in manifest)
total_css  = sum(k["css_count"]  for k in manifest)
print(f"  PHP files across all kits:  {total_php:,}")
print(f"  HTML files:                 {total_html:,}")
print(f"  JS files:                   {total_js:,}")
print(f"  CSS files:                  {total_css:,}")

print(f"\n── Kits with special signals ──")
telegram_kits = sum(1 for k in manifest if k["has_telegram"])
htaccess_kits = sum(1 for k in manifest if k["has_htaccess"])
print(f"  Kits with telegram.php:     {telegram_kits}")
print(f"  Kits with .htaccess:        {htaccess_kits}")

print(f"\n── Top 15 families ──")
for family, count in sorted(
    family_counts.items(), key=lambda x: x[1], reverse=True
)[:15]:
    bar = "█" * min(count // 5, 30)
    print(f"  {family:<40} {count:>4}  {bar}")

print(f"\n── Size distribution ──")
sizes = [k["useful_files"] for k in manifest]
sizes.sort()
print(f"  Smallest kit:  {sizes[0]} files")
print(f"  Median kit:    {sizes[len(sizes)//2]} files")
print(f"  Largest kit:   {sizes[-1]} files")
print(f"  Kits with <5 useful files: "
      f"{sum(1 for s in sizes if s < 5)}")

print("\n✓ Manifest saved → dataset_manifest.json")
print("✓ Day 1 complete.\n")