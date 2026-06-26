import re
import json
from pathlib import Path

# ── PATTERNS WE'RE LOOKING FOR ───────────────────────
# These are the behavioural fingerprints we saw in real kit PHP

# Exfiltration method patterns
TELEGRAM_PATTERNS = [
    r'api\.telegram\.org',           # Telegram API URL
    r'sendMessage',                   # Telegram send function
    r'\$token\s*=',                   # bot token variable
    r'\$chatid\s*=',                  # chat ID variable
    r'curl_init\(\)',                  # curl usage (Telegram uses curl)
    r'CURLOPT_URL',                   # curl option
]

EMAIL_PATTERNS = [
    r'mail\s*\(',                     # PHP mail() function
    r'\$Receive_email\s*=',           # common variable name
    r'\$receive_mail\s*=',
    r'\$email_to\s*=',
    r'\$to\s*=\s*["\']',             # $to = "email"
    r'\$admin_email\s*=',
    r'\$hacker\s*=',                  # some kits literally name it this
    r'wp_mail\s*\(',                  # WordPress mail
]

FILE_EXFIL_PATTERNS = [
    r'file_put_contents\s*\(',        # write credentials to file
    r'fwrite\s*\(',                   # file write
    r'fopen\s*\(.+["\']w["\']',      # open file for writing
]

# Redirect patterns — where victim goes after submitting
REDIRECT_PATTERNS = [
    r'\$redirect\s*=\s*["\'](.+?)["\']',      # $redirect = "url"
    r'header\s*\(\s*["\']Location:\s*(.+?)["\']',  # header redirect
    r'window\.location\s*=',                   # JS redirect from PHP
]

# Anti-analysis patterns
BOT_DETECTION_PATTERNS = [
    r'HTTP_USER_AGENT',               # checking user agent
    r'bot|crawler|spider|curl',       # blocking bots by name
    r'getenv\s*\(\s*["\']HTTP_',     # reading HTTP headers
    r'geoip_country',                 # country-based filtering
    r'ip_address',                    # IP logging
    r'\$_SERVER\[.+USER_AGENT',      # user agent check
]

# IP logging patterns
IP_LOGGING_PATTERNS = [
    r'REMOTE_ADDR',                   # victim IP capture
    r'HTTP_X_FORWARDED_FOR',         # proxy IP capture  
    r'gethostbyaddr',                 # reverse DNS lookup on victim
]

# Session / token generation patterns — reveals coding style
TOKEN_PATTERNS = {
    "md5_rand":     r'md5\s*\(\s*rand\s*\(',     # md5(rand()) — m1 style
    "uniqid":       r'uniqid\s*\(',               # uniqid() 
    "random_bytes": r'random_bytes\s*\(',          # modern secure random
    "sha1_time":    r'sha1\s*\(\s*time\s*\(',     # sha1(time())
    "bin2hex":      r'bin2hex\s*\(',               # bin2hex approach
}

# Credential variable names — reveals what data is being stolen
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
    """
    Extract behavioural features from all PHP files in a kit.
    This reveals HOW the kit works — the criminal's methodology.
    """

    # ── Aggregate across all PHP files ───────────────
    all_content = ""          # combined PHP source for pattern matching

    uses_telegram      = False
    uses_email         = False
    uses_file_exfil    = False
    uses_curl          = False

    has_bot_detection  = False
    has_ip_logging     = False
    has_country_filter = False
    has_redirect       = False

    redirect_targets   = []   # where victims get redirected
    chatids_found      = []   # Telegram chat IDs (author fingerprint)

    credential_types_stolen = set()   # what data is being harvested
    token_style             = "none"  # how session tokens are generated

    php_file_count     = 0
    php_line_count     = 0
    avg_file_length    = 0

    sizes = []

    for rel_path in php_files:
        full_path = kit_root / rel_path

        if not full_path.exists():
            continue

        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if len(content) < 10:
            continue

        php_file_count += 1
        php_line_count += content.count("\n")
        sizes.append(len(content))
        all_content += content + "\n"

    if not all_content:
        return _empty_php_features()

    avg_file_length = sum(sizes) / len(sizes) if sizes else 0
    content_lower   = all_content.lower()

    # ── Exfiltration method detection ────────────────
    telegram_hits = count_pattern_hits(all_content, TELEGRAM_PATTERNS)
    email_hits    = count_pattern_hits(all_content, EMAIL_PATTERNS)
    file_hits     = count_pattern_hits(all_content, FILE_EXFIL_PATTERNS)

    uses_telegram   = telegram_hits >= 2   # need 2+ signals to confirm
    uses_email      = email_hits    >= 1
    uses_file_exfil = file_hits     >= 1
    uses_curl       = bool(re.search(r'curl_init\s*\(', all_content, re.I))

    # ── Extract Telegram chat IDs ─────────────────────
    # These are author fingerprints left in the code
    chatid_matches = re.findall(
        r'\$chatid\s*=\s*["\'](\d+)["\']', 
        all_content, re.IGNORECASE
    )
    chatids_found = list(set(chatid_matches))

    # ── Anti-analysis detection ───────────────────────
    bot_hits     = count_pattern_hits(all_content, BOT_DETECTION_PATTERNS)
    ip_hits      = count_pattern_hits(all_content, IP_LOGGING_PATTERNS)

    has_bot_detection  = bot_hits >= 1
    has_ip_logging     = ip_hits  >= 1
    has_country_filter = bool(re.search(
        r'geoip|country_code|\$_country', all_content, re.IGNORECASE
    ))

    # ── Redirect target extraction ────────────────────
    for pattern in REDIRECT_PATTERNS:
        matches = re.findall(pattern, all_content, re.IGNORECASE)
        redirect_targets.extend(matches)

    has_redirect          = len(redirect_targets) > 0
    redirects_to_legit    = any(
        any(brand in r.lower() for brand in [
            "google", "paypal", "microsoft", "facebook",
            "amazon", "apple", "bankofamerica", "chase"
        ])
        for r in redirect_targets
    )

    # ── Token generation style ─────────────────────────
    # Reveals the author's coding habits
    for style_name, pattern in TOKEN_PATTERNS.items():
        if re.search(pattern, all_content, re.IGNORECASE):
            token_style = style_name
            break

    # ── What credentials are being stolen ─────────────
    for cred_type, pattern in CREDENTIAL_PATTERNS.items():
        if re.search(pattern, all_content, re.IGNORECASE):
            credential_types_stolen.add(cred_type)

    # ── Sophistication score (0-10) ───────────────────
    # Higher = more sophisticated kit author
    sophistication = 0
    if uses_telegram:        sophistication += 2   # tech-savvy exfil
    if uses_curl:            sophistication += 1   # knows curl
    if has_bot_detection:    sophistication += 2   # evasion awareness
    if has_country_filter:   sophistication += 2   # targeted attacks
    if has_ip_logging:       sophistication += 1   # operational security
    if token_style != "none": sophistication += 1  # session management
    if "cvv" in credential_types_stolen: sophistication += 1  # card fraud

    return {
        # Exfiltration method — most important feature
        "uses_telegram":        uses_telegram,
        "uses_email":           uses_email,
        "uses_file_exfil":      uses_file_exfil,
        "uses_curl":            uses_curl,
        "telegram_chat_ids":    chatids_found,
        "exfil_method":         (
            "telegram" if uses_telegram else
            "email"    if uses_email    else
            "file"     if uses_file_exfil else
            "unknown"
        ),

        # Anti-analysis
        "has_bot_detection":    has_bot_detection,
        "has_ip_logging":       has_ip_logging,
        "has_country_filter":   has_country_filter,
        "has_redirect":         has_redirect,
        "redirects_to_legit":   redirects_to_legit,

        # What's stolen
        "steals_password":      "password" in credential_types_stolen,
        "steals_card":          "card_num" in credential_types_stolen,
        "steals_cvv":           "cvv"      in credential_types_stolen,
        "steals_otp":           "otp"      in credential_types_stolen,
        "steals_dob":           "dob"      in credential_types_stolen,
        "steals_ssn":           "ssn"      in credential_types_stolen,
        "credential_type_count": len(credential_types_stolen),

        # Author style fingerprints
        "token_style":          token_style,
        "sophistication_score": sophistication,

        # File stats
        "php_file_count":       php_file_count,
        "php_line_count":       php_line_count,
        "avg_php_file_length":  round(avg_file_length, 1),
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


# ── TEST ON 5 KITS ────────────────────────────────────
if __name__ == "__main__":
    with open("data_exploration/dataset_manifest.json") as f:
        manifest = json.load(f)

    # Test on kits we already know about
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

