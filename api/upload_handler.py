import zipfile
import shutil
import hashlib
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.html_extractor import extract_html_features
from extractors.php_extractor import extract_php_features
from extractors.js_extractor import extract_js_features
from extractors.structural_features_extract import extract_structural_features
from m1.classifier import classify_kit

def process_uploaded_kit(zip_path: Path, extract_dir: Path) -> dict:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    kit_root = find_kit_root(extract_dir)
    manifest_entry = build_manifest_entry(kit_root)
    features = extract_all_features(kit_root, manifest_entry)
    
    import json
    features_file = Path(__file__).parent.parent / "data" / "features.json"
    with open(features_file) as f:
        features_data = json.load(f)
    
    kit_hash = manifest_entry["hash"]
    features_data[kit_hash] = features
    
    with open(features_file, "w") as f:
        json.dump(features_data, f)
    
    try:
        result = classify_kit(kit_root, manifest_entry)
        return result
    finally:
        del features_data[kit_hash]
        with open(features_file, "w") as f:
            json.dump(features_data, f)

def find_kit_root(extract_dir: Path) -> Path:
    macosx_dir = extract_dir / "__MACOSX"
    if macosx_dir.exists():
        shutil.rmtree(macosx_dir)
    
    items = [item for item in extract_dir.iterdir() if not item.name.startswith('.')]
    
    if len(items) == 1 and items[0].is_dir():
        return items[0]
    
    return extract_dir

def build_manifest_entry(kit_root: Path) -> dict:
    all_files = []
    for file_path in kit_root.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith('.'):
            rel_path = file_path.relative_to(kit_root)
            all_files.append(str(rel_path).replace('\\', '/'))
    
    php_count = sum(1 for f in all_files if f.lower().endswith('.php'))
    html_count = sum(1 for f in all_files if f.lower().endswith(('.html', '.htm')))
    js_count = sum(1 for f in all_files if f.lower().endswith('.js'))
    css_count = sum(1 for f in all_files if f.lower().endswith('.css'))
    
    useful_files = php_count + html_count + js_count + css_count
    total_files = len(all_files)
    
    file_list_str = '|'.join(sorted(all_files))
    kit_hash = hashlib.md5(file_list_str.encode()).hexdigest()
    
    has_htaccess = any('.htaccess' in f.lower() for f in all_files)
    has_telegram = any('telegram' in f.lower() for f in all_files)
    
    return {
        "hash": kit_hash,
        "files": all_files,
        "total_files": total_files,
        "useful_files": useful_files,
        "php_count": php_count,
        "html_count": html_count,
        "js_count": js_count,
        "css_count": css_count,
        "has_htaccess": has_htaccess,
        "has_telegram": has_telegram
    }

def extract_all_features(kit_root: Path, manifest_entry: dict) -> dict:
    html_files = [
        f for f in manifest_entry.get("files", [])
        if f.lower().endswith((".html", ".htm"))
    ][:10]
    
    php_files = [
        f for f in manifest_entry.get("files", [])
        if f.lower().endswith(".php")
    ]
    
    js_files = [
        f for f in manifest_entry.get("files", [])
        if f.lower().endswith(".js")
    ]
    
    html_features = extract_html_features(kit_root, html_files)
    php_features = extract_php_features(kit_root, php_files)
    js_features = extract_js_features(kit_root, js_files)
    structural_features = extract_structural_features(manifest_entry)
    
    combined_features = {
        **html_features,
        **php_features,
        **js_features,
        **structural_features
    }
    
    combined_features["kit_hash"] = manifest_entry["hash"]
    combined_features["total_files"] = manifest_entry.get("total_files", 0)
    combined_features["useful_files"] = manifest_entry.get("useful_files", 0)
    
    return combined_features