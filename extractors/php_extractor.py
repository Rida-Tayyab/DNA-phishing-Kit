import re
import json
from pathlib import Path


TELEGRAM_PATTERNS = [
    r'api\.telegram\.org',  
    r'sendMessage',                
    r'\$token\s*=',            
    r'\$chatid\s*=',         
    r'curl_init\(\)',                  
    r'CURLOPT_URL',     
]

EMAIL_PATTERNS = [
    r'mail\s*\(',               
    r'\$Receive_email\s*=',      
    r'\$receive_mail\s*=',
    r'\$email_to\s*=',
    r'\$to\s*=\s*["\']', 
    r'\$admin_email\s*=',
    r'\$hacker\s*=',                
    r'wp_mail\s*\(',       
]

FILE_EXFIL_PATTERNS = [
    r'file_put_contents\s*\(',        
    r'fwrite\s*\(',                   
    r'fopen\s*\(.+["\']w["\']',      
]

REDIRECT_PATTERNS = [
    r'\$redirect\s*=\s*["\'](.+?)["\']',     
    r'header\s*\(\s*["\']Location:\s*(.+?)["\']'
    r'window\.location\s*=',                   
]

# Anti-analysis patterns
BOT_DETECTION_PATTERNS = [
    r'HTTP_USER_AGENT',               
    r'bot|crawler|spider|curl',       
    r'getenv\s*\(\s*["\']HTTP_',     
    r'geoip_country',                 
    r'ip_address',            
    r'\$_SERVER\[.+USER_AGENT',
]

# IP logging patterns
IP_LOGGING_PATTERNS = [
    r'REMOTE_ADDR',                   
    r'HTTP_X_FORWARDED_FOR',           
    r'gethostbyaddr',                 
]

TOKEN_PATTERNS = {
    "md5_rand":     r'md5\s*\(\s*rand\s*\(',     
    "uniqid":       r'uniqid\s*\(',               
    "random_bytes": r'random_bytes\s*\(',          
    "sha1_time":    r'sha1\s*\(\s*time\s*\(',     
    "bin2hex":      r'bin2hex\s*\(',               
}

CREDENTIAL_PATTERNS = {
    "password":   r'\$(pass|password|passwd|pwd|contraseña)',
    "email":      r'\$(email|mail|correo|username|user)',
    "card_num":   r'\$(card|cardnum|cc_num|credit|debit|numero)',
    "cvv":        r'\$(cvv|cvc|cvn|security_code)',
    "dob":        r'\$(dob|birth|birthday|birthdate)',
    "ssn":        r'\$(ssn|social|sin_number)',
    "otp":        r'\$(otp|pin|code|token|sms_code)',
    "phone":      r'\$(phone|mobile|tel|celular)',
}


def count_pattern_hits(content: str, patterns: list) -> int:
    """Count how many patterns match in content."""
    hits = 0
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            hits += 1
    return hits

def extract_php_features(kit_root: Path, php_files: list) -> dict:
    """Extract behavioural features from a phishing kit's PHP backend."""

    all_content = []
    sizes = []
    php_file_count = 0
    php_line_count = 0

    for rel_path in php_files:
        path = kit_root / rel_path

        if not path.exists():
            continue

        try:
            content = path.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except Exception:
            continue

        if len(content.strip()) < 10:
            continue

        if len(content) > 200_000:
            content = content[:200_000] 

        php_file_count += 1
        php_line_count += content.count("\n")
        sizes.append(len(content))
        all_content.append(content)

    if not all_content:
        return _empty_php_features()

    all_content = "\n".join(all_content)

    avg_file_length = (
        sum(sizes) / len(sizes)
        if sizes else 0
    )

    telegram_hits = count_pattern_hits(
        all_content,
        TELEGRAM_PATTERNS
    )

    email_hits = count_pattern_hits(
        all_content,
        EMAIL_PATTERNS
    )

    file_hits = count_pattern_hits(
        all_content,
        FILE_EXFIL_PATTERNS
    )

    uses_telegram = telegram_hits >= 2
    uses_email = email_hits >= 1
    uses_file_exfil = file_hits >= 1

    uses_curl = bool(
        re.search(
            r"curl_init\s*\(",
            all_content,
            re.IGNORECASE
        )
    )

    chatids_found = list(
        set(
            re.findall(
                r'\$chatid\s*=\s*["\'](\d+)["\']',
                all_content,
                re.IGNORECASE
            )
        )
    )

    token_style = "none"

    for style, pattern in TOKEN_PATTERNS.items():
        if re.search(pattern, all_content, re.IGNORECASE):
            token_style = style
            break

    has_bot_detection = (
        count_pattern_hits(
            all_content,
            BOT_DETECTION_PATTERNS
        ) > 0
    )

    has_ip_logging = (
        count_pattern_hits(
            all_content,
            IP_LOGGING_PATTERNS
        ) > 0
    )

    has_country_filter = bool(
        re.search(
            r"geoip|country_code|\$_country",
            all_content,
            re.IGNORECASE
        )
    )

    redirect_targets = []

    for pattern in REDIRECT_PATTERNS:
        redirect_targets.extend(
            re.findall(
                pattern,
                all_content,
                re.IGNORECASE
            )
        )

    has_redirect = len(redirect_targets) > 0

    redirects_to_legit = any(
        any(
            brand in target.lower()
            for brand in [
                "google",
                "paypal",
                "microsoft",
                "facebook",
                "amazon",
                "apple",
                "bankofamerica",
                "chase",
            ]
        )
        for target in redirect_targets
    )

    credential_types = set()

    for name, pattern in CREDENTIAL_PATTERNS.items():
        if re.search(
            pattern,
            all_content,
            re.IGNORECASE
        ):
            credential_types.add(name)

    sophistication = 0

    if uses_telegram:
        sophistication += 2

    if uses_curl:
        sophistication += 1

    if has_bot_detection:
        sophistication += 2

    if has_country_filter:
        sophistication += 2

    if has_ip_logging:
        sophistication += 1

    if token_style != "none":
        sophistication += 1

    if "cvv" in credential_types:
        sophistication += 1

    if uses_telegram:
        exfil_method = "telegram"
    elif uses_email:
        exfil_method = "email"
    elif uses_file_exfil:
        exfil_method = "file"
    else:
        exfil_method = "unknown"

    return {
        "uses_telegram": uses_telegram,
        "uses_email": uses_email,
        "uses_file_exfil": uses_file_exfil,
        "uses_curl": uses_curl,

        "telegram_chat_ids": chatids_found,
        "exfil_method": exfil_method,

        "has_bot_detection": has_bot_detection,
        "has_ip_logging": has_ip_logging,
        "has_country_filter": has_country_filter,

        "has_redirect": has_redirect,
        "redirects_to_legit": redirects_to_legit,

        "steals_password": "password" in credential_types,
        "steals_card": "card_num" in credential_types,
        "steals_cvv": "cvv" in credential_types,
        "steals_otp": "otp" in credential_types,
        "steals_dob": "dob" in credential_types,
        "steals_ssn": "ssn" in credential_types,

        "credential_type_count": len(
            credential_types
        ),

        "token_style": token_style,
        "sophistication_score": sophistication,

        "php_file_count": php_file_count,
        "php_line_count": php_line_count,
        "avg_php_file_length": round(
            avg_file_length,
            1
        ),
    }
def _empty_php_features() -> dict:
    """Return zeroed features for kits with no readable PHP."""
    return {
        "uses_telegram": False, "uses_email": False,
        "uses_file_exfil": False, "uses_curl": False,
        "telegram_chat_ids": [], "exfil_method": "unknown",
        "has_bot_detection": False, "has_ip_logging": False,
        "has_country_filter": False, "has_redirect": False,
        "redirects_to_legit": False,
        "steals_password": False, "steals_card": False,
        "steals_cvv": False, "steals_otp": False,
        "steals_dob": False, "steals_ssn": False,
        "credential_type_count": 0,
        "token_style": "none", "sophistication_score": 0,
        "php_file_count": 0, "php_line_count": 0,
        "avg_php_file_length": 0.0,
    }

if __name__ == "__main__":
    with open("data/dataset_manifest.json") as f:
        manifest = json.load(f)

    
    test_families = ["m1", "mtb.com-bank", "hjukiujyhgtrvfcdx", 
                     "volks", "raiffeisenbank"]
    test_kits = [
        k for k in manifest 
        if k["family"] in test_families
    ][:5]

    print("── Testing PHP extractor on known kits ──\n")

    for kit in test_kits:
        kit_root  = Path(kit["kit_root"])
        php_files = [f for f in kit["files"] if f.endswith(".php")]

        features = extract_php_features(kit_root, php_files)

        print(f"Family:          {kit['family']}")
        print(f"  Exfil method:  {features['exfil_method']}")
        print(f"  Uses telegram: {features['uses_telegram']}")
        print(f"  Chat IDs:      {features['telegram_chat_ids']}")
        print(f"  Bot detection: {features['has_bot_detection']}")
        print(f"  IP logging:    {features['has_ip_logging']}")
        print(f"  Steals card:   {features['steals_card']}")
        print(f"  Steals OTP:    {features['steals_otp']}")
        print(f"  Token style:   {features['token_style']}")
        print(f"  Sophistication:{features['sophistication_score']}/10")
        print(f"  PHP lines:     {features['php_line_count']}")
        print()

