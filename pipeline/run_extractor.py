# run_html_extraction.py
# Runs html_extractor across ALL 8489 kits and saves results

import json
from pathlib import Path
from html_extractor import extract_html_features

print("Loading manifest...")
with open("data/dataset_manifest.json") as f:
    manifest = json.load(f)

# Filter out kits too sparse to be useful
usable = [k for k in manifest if k["useful_files"] >= 5]
print(f"Kits to process: {len(usable)} "
      f"(skipping {len(manifest) - len(usable)} sparse kits)\n")

results = []
errors  = []
brand_distribution = {}

from tqdm import tqdm

for kit in tqdm(usable, desc="Extracting HTML features", unit="kit"):
    kit_root   = Path(kit["kit_root"])
    html_files = [f for f in kit["files"] 
                  if f.endswith((".html", ".htm"))]

    try:
        html_feats = extract_html_features(kit_root, html_files)

        results.append({
            "hash":         kit["hash"],
            "family":       kit["family"],
            "kit_root":     kit["kit_root"],
            "php_count":    kit["php_count"],
            "html_count":   kit["html_count"],
            "js_count":     kit["js_count"],
            "css_count":    kit["css_count"],
            "total_files":  kit["useful_files"],
            "has_telegram": kit["has_telegram"],
            "has_htaccess": kit["has_htaccess"],
            **html_feats
        })

        brand = html_feats["detected_brand"]
        brand_distribution[brand] = brand_distribution.get(brand, 0) + 1

    except Exception as e:
        errors.append({
            "hash":   kit["hash"],
            "family": kit["family"],
            "error":  str(e)
        })
        
# ── Save results ─────────────────────────────────────
with open("html_features.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

with open("html_errors.json", "w", encoding="utf-8") as f:
    json.dump(errors, f, indent=2)

# ── Print summary ─────────────────────────────────────
print(f"\n{'='*50}")
print(f"  HTML EXTRACTION COMPLETE")
print(f"{'='*50}")
print(f"  Processed:  {len(results):,} kits")
print(f"  Errors:     {len(errors):,} kits")

print(f"\n── Brand distribution ──")
for brand, count in sorted(
    brand_distribution.items(), 
    key=lambda x: x[1], reverse=True
)[:12]:
    pct = count / len(results) * 100
    bar = "█" * int(pct / 2)
    print(f"  {brand:<20} {count:>5}  ({pct:.1f}%)  {bar}")

print(f"\n── Form signal summary ──")
has_forms     = sum(1 for r in results if r["form_count"] > 0)
has_password  = sum(1 for r in results if r["has_password_field"])
has_2fa       = sum(1 for r in results if r["has_2fa_field"])
has_captcha   = sum(1 for r in results if r["has_captcha"])
has_card      = sum(1 for r in results if r["card_field_count"] > 0)
has_telegram  = sum(1 for r in results if r["has_telegram"])
has_htaccess  = sum(1 for r in results if r["has_htaccess"])

print(f"  Kits with any form:      {has_forms:,}  "
      f"({has_forms/len(results)*100:.1f}%)")
print(f"  Kits with password field:{has_password:,}  "
      f"({has_password/len(results)*100:.1f}%)")
print(f"  Kits with 2FA field:     {has_2fa:,}  "
      f"({has_2fa/len(results)*100:.1f}%)")
print(f"  Kits with CAPTCHA:       {has_captcha:,}  "
      f"({has_captcha/len(results)*100:.1f}%)")
print(f"  Kits with card fields:   {has_card:,}  "
      f"({has_card/len(results)*100:.1f}%)")
print(f"  Kits with telegram.php:  {has_telegram:,}  "
      f"({has_telegram/len(results)*100:.1f}%)")
print(f"  Kits with .htaccess:     {has_htaccess:,}  "
      f"({has_htaccess/len(results)*100:.1f}%)")

print(f"\n✓ Saved → html_features.json")
print(f"✓ Day 2 complete. Commit this.\n")