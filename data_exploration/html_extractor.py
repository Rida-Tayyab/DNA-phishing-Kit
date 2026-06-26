# html_extractor.py
# Day 2 — Extract features from HTML files in each phishing kit
# WRITE THIS YOURSELF — this is your research contribution

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict

# ── KNOWN BRAND KEYWORDS ─────────────────────────────
# We'll detect which brand each kit impersonates
BRAND_KEYWORDS = {
    "paypal":     ["paypal", "pay pal"],
    "microsoft":  ["microsoft", "outlook", "office 365", "onedrive", "hotmail"],
    "google":     ["google", "gmail", "google drive"],
    "apple":      ["apple", "icloud", "itunes", "apple id"],
    "amazon":     ["amazon", "aws", "prime"],
    "facebook":   ["facebook", "meta", "instagram"],
    "netflix":    ["netflix"],
    "bank_generic": ["bank", "banking", "secure login", "verify your account"],
    "chase":      ["chase", "jpmorgan"],
    "wellsfargo": ["wells fargo", "wellsfargo"],
    "crypto":     ["wallet", "metamask", "coinbase", "bitcoin", "ethereum", "crypto"],
    "dhl":        ["dhl", "delivery", "shipment", "parcel"],
    "docusign":   ["docusign", "sign document"],
    
    "mtb":        ["m&t bank", "mtb", "m&t", "mt bank"],
    "wellsfargo": ["wells fargo", "wellsfargo", "wf bank"],
    "dbs":        ["dbs bank", "dbs internet banking"],
    "hsbc":       ["hsbc"],
    "citi":       ["citibank", "citi bank", "citi"],
    "microsoft":  ["microsoft", "outlook", "office 365", "onedrive", 
                "hotmail", "office365"],  # expand this one
}

def extract_html_features(kit_root: Path, html_files: list) -> dict:
    """
    Given a kit's root folder and list of HTML file paths,
    extract structural and behavioural features.
    
    Returns a dict of features — these become part of the DNA fingerprint.
    """
    
    # ── Aggregate across all HTML files in this kit ───
    total_forms          = 0
    total_inputs         = 0
    password_fields      = 0
    email_fields         = 0
    text_fields          = 0
    hidden_fields        = 0
    tel_fields           = 0      # phone number fields
    card_fields          = 0      # credit card number fields (name hints)
    
    form_actions         = []     # where forms submit to
    external_scripts     = []     # external JS URLs loaded
    page_titles          = []     # <title> tags
    meta_descriptions    = []     # meta description content
    
    has_captcha          = False
    has_mobile_viewport  = False
    has_password_field   = False
    has_2fa_field        = False  # OTP, PIN, verification code fields
    
    brand_scores         = defaultdict(int)  # how many brand keyword hits
    
    pages_processed      = 0
    
    for rel_path in html_files:
        full_path = kit_root / rel_path
        
        if not full_path.exists():
            continue
            
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        
        # Skip tiny files — probably not real pages
        if len(content) < 200:
            continue
            
        soup = BeautifulSoup(content, "html.parser")
        pages_processed += 1
        
        # ── Page title ───────────────────────────────
        title_tag = soup.find("title")
        if title_tag and title_tag.text.strip():
            page_titles.append(title_tag.text.strip().lower())
        
        # ── Meta tags ────────────────────────────────
        viewport = soup.find("meta", attrs={"name": "viewport"})
        if viewport:
            has_mobile_viewport = True
            
        desc = soup.find("meta", attrs={"name": "description"})
        if desc and desc.get("content"):
            meta_descriptions.append(desc["content"].lower())
        
        # ── Forms ────────────────────────────────────
        forms = soup.find_all("form")
        total_forms += len(forms)
        
        for form in forms:
            # Where does this form submit to?
            action = form.get("action", "").strip()
            if action:
                form_actions.append(action)
            
            # What input fields does it have?
            inputs = form.find_all("input")
            total_inputs += len(inputs)
            
            for inp in inputs:
                inp_type  = inp.get("type",  "").lower()
                inp_name  = inp.get("name",  "").lower()
                inp_id    = inp.get("id",    "").lower()
                inp_place = inp.get("placeholder", "").lower()
                
                # Combine all identifiers to detect field purpose
                combined = f"{inp_type} {inp_name} {inp_id} {inp_place}"

                # Some kits use autocomplete hints instead of field names
                autocomplete = inp.get("autocomplete", "").lower()
                if "cc-number" in autocomplete or "cardnumber" in autocomplete:
                    card_fields += 1
                if "current-password" in autocomplete or "new-password" in autocomplete:
                    password_fields += 1
                    has_password_field = True
                
                if inp_type == "password":
                    password_fields += 1
                    has_password_field = True
                    
                elif inp_type == "hidden":
                    hidden_fields += 1
                    
                elif inp_type == "email" or "email" in combined:
                    email_fields += 1
                    
                elif inp_type == "tel" or "phone" in combined or "mobile" in combined:
                    tel_fields += 1
                    
                elif any(x in combined for x in [
                    "card", "cardnum", "cc-number", "credit", "debit"
                ]):
                    card_fields += 1
                    
                elif any(x in combined for x in [
                    "otp", "pin", "code", "verify", "2fa", "token", "sms"
                ]):
                    has_2fa_field = True
                    
                elif inp_type == "text":
                    text_fields += 1
                
        
        # ── External scripts ─────────────────────────
        scripts = soup.find_all("script", src=True)
        for script in scripts:
            src = script.get("src", "")
            # Only flag truly external (not relative paths)
            if src.startswith("http") or src.startswith("//"):
                external_scripts.append(src)
        
        # ── CAPTCHA detection ─────────────────────────
        content_lower = content.lower()
        if any(x in content_lower for x in [
            "recaptcha", "hcaptcha", "captcha", "g-recaptcha"
        ]):
            has_captcha = True
        
        # ── Brand detection ───────────────────────────
        for brand, keywords in BRAND_KEYWORDS.items():
            for kw in keywords:
                if kw in content_lower:
                    brand_scores[brand] += 1
    
    # ── Derive summary features ───────────────────────
    
    # What brand does this kit impersonate?
    detected_brand = "unknown"
    if brand_scores:
        detected_brand = max(brand_scores, key=brand_scores.get)
    
    # Form action analysis
    external_actions = sum(
        1 for a in form_actions 
        if a.startswith("http") and "localhost" not in a
    )
    internal_actions = sum(
        1 for a in form_actions
        if not a.startswith("http") and a.endswith(".php")
    )
    
    # External script domains
    ext_script_domains = set()
    for src in external_scripts:
        try:
            # Quick domain extract
            domain = src.split("/")[2] if "//" in src else ""
            if domain:
                ext_script_domains.add(domain)
        except Exception:
            pass
    
    return {
        # Form structure
        "form_count":            total_forms,
        "input_count":           total_inputs,
        "password_field_count":  password_fields,
        "email_field_count":     email_fields,
        "text_field_count":      text_fields,
        "hidden_field_count":    hidden_fields,
        "tel_field_count":       tel_fields,
        "card_field_count":      card_fields,
        
        # Boolean signals
        "has_password_field":    has_password_field,
        "has_2fa_field":         has_2fa_field,
        "has_captcha":           has_captcha,
        "has_mobile_viewport":   has_mobile_viewport,
        
        # Form submission analysis
        "external_form_actions": external_actions,
        "internal_form_actions": internal_actions,
        "form_action_php":       sum(1 for a in form_actions if ".php" in a),
        
        # External resources
        "external_script_count": len(external_scripts),
        "unique_script_domains": len(ext_script_domains),
        
        # Brand impersonation
        "detected_brand":        detected_brand,
        "brand_confidence":      brand_scores.get(detected_brand, 0),
        
        # Page metadata
        "page_count_processed":  pages_processed,
        "has_page_title":        len(page_titles) > 0,
    }


# ── TEST ON 5 KITS ────────────────────────────────────
if __name__ == "__main__":
    with open("data_exploration/dataset_manifest.json") as f:
        manifest = json.load(f)
    
    # Pick 5 kits with HTML files to test on
    test_kits = [
        k for k in manifest 
        if k["html_count"] >= 1 and k["useful_files"] >= 5
    ][:5]
    
    print("── Testing HTML extractor on 5 kits ──\n")
    
    for kit in test_kits:
        kit_root  = Path(kit["kit_root"])
        html_files = [
            f for f in kit["files"] 
            if f.endswith((".html", ".htm"))
        ]
        
        features = extract_html_features(kit_root, html_files)
        
        print(f"Family: {kit['family']}")
        print(f"  Brand detected:      {features['detected_brand']}")
        print(f"  Forms found:         {features['form_count']}")
        print(f"  Password fields:     {features['password_field_count']}")
        print(f"  Hidden fields:       {features['hidden_field_count']}")
        print(f"  Has 2FA field:       {features['has_2fa_field']}")
        print(f"  Has CAPTCHA:         {features['has_captcha']}")
        print(f"  External scripts:    {features['external_script_count']}")
        print(f"  Mobile viewport:     {features['has_mobile_viewport']}")
        print()
