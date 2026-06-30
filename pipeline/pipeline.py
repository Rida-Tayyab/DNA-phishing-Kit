import json
from pathlib import Path
from tqdm import tqdm
from bs4 import XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from html_extractor import extract_html_features
from php_extractor import extract_php_features
from structural_features_extract import extract_structural_features
from js_extractor import extract_js_features


def main():
    print("Loading dataset manifest...")
    with open("data/dataset_manifest.json") as f:
        manifest = json.load(f)
    
    # Filter kits with useful_files >= 5
    target_kits = [
        kit for kit in manifest 
        if kit.get("useful_files", 0) >= 5
    ]
    
    print(f"Found {len(target_kits)} kits with useful_files >= 5")
    
    all_features = {}

    for kit in tqdm(target_kits, desc="Processing kits"):
        kit_id = kit["hash"]
        kit_root = Path(kit["kit_root"])
        
        try:
            html_files = [
                f for f in kit.get("files", [])
                if f.lower().endswith((".html", ".htm"))
            ][:10]  # max 10 HTML files per kit
            
            php_files = [
                f for f in kit.get("files", [])
                if f.lower().endswith(".php")
            ]
            js_files = [
                f for f in kit.get("files", [])
                if f.lower().endswith(".js")
            ]

            js_features = extract_js_features(kit_root, js_files)
            html_features = extract_html_features(kit_root, html_files)
            php_features = extract_php_features(kit_root, php_files)
            structural_features = extract_structural_features(kit)
     
            combined_features = {
                **html_features,
                **php_features,
                **js_features, 
                **structural_features
            }

            combined_features["kit_family"] = kit["family"]  # actual family name
            combined_features["kit_hash"] = kit_id            # keep hash too
            combined_features["total_files"] = kit.get("total_files", 0)
            combined_features["useful_files"] = kit.get("useful_files", 0)
            
            all_features[kit_id] = combined_features
            
            # Save checkpoint every 500 kits
            if len(all_features) % 500 == 0:
                with open("features_checkpoint.json", "w") as f:
                    json.dump(all_features, f)
                tqdm.write(f"Checkpoint saved: {len(all_features)} kits")
        
        except Exception as e:
            tqdm.write(f"SKIP {kit['family']}: {e}")
    
    # Save to features.json
    print(f"Saving {len(all_features)} kit features to features.json...")
    with open("data/features.json", "w") as f:
        json.dump(all_features, f, indent=2)
    
    print("Pipeline complete!")
    print(f"Processed {len(all_features)} kits")
    print("Features saved to features.json")


if __name__ == "__main__":
    main()