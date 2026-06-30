import re
import json
from pathlib import Path


def extract_js_features(kit_root: Path, js_files: list) -> dict:
    """Extract behavioral features from JavaScript files in a phishing kit."""
    
    all_content = []
    sizes = []
    js_file_count = 0
    js_line_count = 0
    
    for rel_path in js_files:
        path = kit_root / rel_path
        
        if not path.exists():
            continue
            
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
            
        if len(content.strip()) < 10:
            continue
            
        if len(content) > 200_000:
            content = content[:200_000]  
            
        js_file_count += 1
        js_line_count += content.count("\n")
        sizes.append(len(content))
        all_content.append(content)
    
    if not all_content:
        return _empty_js_features()
        
    all_content = "\n".join(all_content)
    
    # Check for obfuscation signals
    has_eval = bool(re.search(r'\beval\s*\(', all_content, re.IGNORECASE))
    has_atob = bool(re.search(r'\batob\s*\(', all_content, re.IGNORECASE))
    
    # Check for very long lines (minified/obfuscated)
    lines = all_content.split('\n')
    max_line_length = max(len(line) for line in lines) if lines else 0
    has_long_lines = max_line_length > 500
    long_line_count = sum(1 for line in lines if len(line) > 500)
    
    # Check for exfiltration signals  
    has_fetch = bool(re.search(r'\bfetch\s*\(', all_content, re.IGNORECASE))
    has_xmlhttprequest = bool(re.search(r'XMLHttpRequest', all_content, re.IGNORECASE))
    has_formdata = bool(re.search(r'\bFormData\s*\(', all_content, re.IGNORECASE))
    
    # Check for framework signals
    has_jquery = bool(re.search(r'\b(jquery|jQuery|\$\.)', all_content, re.IGNORECASE))
    has_vue = bool(re.search(r'\b(Vue|vue\.js)', all_content, re.IGNORECASE))
    has_webpack = bool(re.search(r'\bwebpack', all_content, re.IGNORECASE))
    
    # Check for credential targeting
    has_getelementbyid = bool(re.search(r'getElementById', all_content, re.IGNORECASE))
    has_queryselector = bool(re.search(r'querySelector', all_content, re.IGNORECASE))
    
    # Look for targeting of sensitive fields
    targets_password = bool(re.search(r'(getElementById|querySelector).*(password|pwd|pass)', all_content, re.IGNORECASE))
    targets_card = bool(re.search(r'(getElementById|querySelector).*(card|cvv|cc|credit)', all_content, re.IGNORECASE))
    targets_otp = bool(re.search(r'(getElementById|querySelector).*(otp|pin|code|sms)', all_content, re.IGNORECASE))
    
    # Check for form event listeners
    has_form_submit = bool(re.search(r'(addEventListener|on).*submit', all_content, re.IGNORECASE))
    has_form_validation = bool(re.search(r'validateForm|validation', all_content, re.IGNORECASE))
    
    # Count HTTP requests
    fetch_count = len(re.findall(r'\bfetch\s*\(', all_content, re.IGNORECASE))
    xhr_count = len(re.findall(r'XMLHttpRequest', all_content, re.IGNORECASE))
    
    # Calculate sophistication score
    sophistication = 0
    if has_webpack: sophistication += 3  # Modern build tools
    if has_vue: sophistication += 3     # Modern framework
    if has_fetch: sophistication += 2   # Modern HTTP
    if has_formdata: sophistication += 2
    if has_eval or has_atob: sophistication += 2  # Obation
    if has_long_lines: sophistication += 1
    if targets_card or targets_otp: sophistication += 2  # Advanced targeting
    if has_form_validation: sophistication += 1
    
    return {
        # Obfuscation signals
        "has_eval": has_eval,
        "has_atob": has_atob,
        "has_long_lines": has_long_lines,
        "max_line_length": max_line_length,
        "long_line_count": long_line_count,
        
        # Exfiltration signals
        "has_fetch": has_fetch,
        "has_xmlhttprequest": has_xmlhttprequest,
        "has_formdata": has_formdata,
        "fetch_count": fetch_count,
        "xhr_count": xhr_count,
        
        # Framework signals
        "has_jquery": has_jquery,
        "has_vue": has_vue,
        "has_webpack": has_webpack,
        
        # Credential targeting
        "has_getelementbyid": has_getelementbyid,
        "has_queryselector": has_queryselector,
        "targets_password": targets_password,
        "targets_card": targets_card,
        "targets_otp": targets_otp,
        
        # Form handling
        "has_form_submit": has_form_submit,
        "has_form_validation": has_form_validation,
        
        # File stats
        "js_file_count": js_file_count,
        "js_line_count": js_line_count,
        "avg_js_file_length": round(sum(sizes) / len(sizes), 1) if sizes else 0.0,
        
        # Overall sophistication
        "js_sophistication_score": sophistication,
    }


def _empty_js_features() -> dict:
    """Return zeroed features for kits with no readable JS."""
    return {
        "has_eval": False, "has_atob": False, "has_long_lines": False,
        "max_line_length": 0, "long_line_count": 0,
        "has_fetch": False, "has_xmlhttprequest": False, "has_formdata": False,
        "fetch_count": 0, "xhr_count": 0,
        "has_jquery": False, "has_vue": False, "has_webpack": False,
        "has_getelementbyid": False, "has_queryselector": False,
        "targets_password": False, "targets_card": False, "targets_otp": False,
        "has_form_submit": False, "has_form_validation": False,
        "js_file_count": 0, "js_line_count": 0, "avg_js_file_length": 0.0,
        "js_sophistication_score": 0,
    }


# Test on the 3 kits we examined
if __name__ == "__main__":
    with open("data/dataset_manifest.json") as f:
        manifest = json.load(f)
    
    # Find the specific kits we peeked at
    test_families = ["m1", "dhl-cryptre-news", "SEUR_ES"]
    test_kits = [
        k for k in manifest 
        if k["family"] in test_families
    ]
    
    print("── Testing JS extractor on 3 kits ──\n")
    
    for kit in test_kits:
        kit_root = Path(kit["kit_root"])
        js_files = [
            f for f in kit.get("files", [])
            if f.lower().endswith(".js")
        ]
        
        features = extract_js_features(kit_root, js_files)
        
        print(f"Family: {kit['family']}")
        print(f"  JS files: {features['js_file_count']}")
        print(f"  Max line length: {features['max_line_length']}")
        print(f"  Has jQuery: {features['has_jquery']}")
        print(f"  Has Vue: {features['has_vue']}")
        print(f"  Has webpack: {features['has_webpack']}")
        print(f"  Has fetch: {features['has_fetch']}")
        print(f"  Has XMLHttpRequest: {features['has_xmlhttprequest']}")
        print(f"  Targets password: {features['targets_password']}")
        print(f"  Targets card: {features['targets_card']}")
        print(f"  Has form validation: {features['has_form_validation']}")
        print(f"  Sophistication score: {features['js_sophistication_score']}")
        print()