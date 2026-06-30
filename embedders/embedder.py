import json
import numpy as np


def normalize_vector(raw_vector, col_min, col_max):
    """Normalize a single vector using saved min/max statistics."""
    raw = np.array(raw_vector, dtype=np.float32)
    col_range = np.array(col_max) - np.array(col_min)
    col_range[col_range == 0] = 1  # avoid divide by zero
    return (raw - np.array(col_min)) / col_range

def build_feature_vector(kit: dict) -> list:
    """
    Convert one kit's feature dict into a numerical vector.
    Returns a list of floats ready for embedding/FAISS.
    """
    
    # Boolean features (converted to 0/1)
    bool_features = [
        int(kit.get("uses_telegram", False)),
        int(kit.get("uses_email", False)),
        int(kit.get("uses_file_exfil", False)),
        int(kit.get("uses_curl", False)),
        int(kit.get("has_bot_detection", False)),
        int(kit.get("has_ip_logging", False)),
        int(kit.get("has_country_filter", False)),
        int(kit.get("has_redirect", False)),
        int(kit.get("redirects_to_legit", False)),
        int(kit.get("steals_password", False)),
        int(kit.get("steals_card", False)),
        int(kit.get("steals_cvv", False)),
        int(kit.get("steals_otp", False)),
        int(kit.get("steals_dob", False)),
        int(kit.get("steals_ssn", False)),
        int(kit.get("has_password_field", False)),
        int(kit.get("has_2fa_field", False)),
        int(kit.get("has_captcha", False)),
        int(kit.get("has_mobile_viewport", False)),
        int(kit.get("is_multipage", False)),
        int(kit.get("has_admin_panel", False)),
        int(kit.get("has_config_file", False)),
        int(kit.get("has_htaccess", False)),
        int(kit.get("has_telegram", False)),
        int(kit.get("has_page_title", False)),
    ]
    
    # Numerical features
    numerical_features = [
        kit.get("sophistication_score", 0),
        kit.get("form_count", 0),
        kit.get("input_count", 0),
        kit.get("password_field_count", 0),
        kit.get("email_field_count", 0),
        kit.get("text_field_count", 0),
        kit.get("hidden_field_count", 0),
        kit.get("tel_field_count", 0),
        kit.get("card_field_count", 0),
        kit.get("external_form_actions", 0),
        kit.get("internal_form_actions", 0),
        kit.get("form_action_php", 0),
        kit.get("external_script_count", 0),
        kit.get("unique_script_domains", 0),
        kit.get("brand_confidence", 0),
        kit.get("page_count_processed", 0),
        kit.get("credential_type_count", 0),
        kit.get("php_file_count", 0),
        kit.get("php_line_count", 0),
        kit.get("avg_php_file_length", 0),
        kit.get("php_ratio", 0),
        kit.get("js_ratio", 0),
        kit.get("max_directory_depth", 0),
        kit.get("total_files", 0),
        kit.get("useful_files", 0),
    ]

    # Exfiltration method mapping
    exfil_map = {"telegram": 1, "email": 2, "file": 3, "unknown": 0}
    exfil_encoded = exfil_map.get(kit.get("exfil_method", "unknown"), 0)
    
    # Brand mapping (top brands from EDA)
    brand_map = {
        "facebook": 1, "bank_generic": 2, "google": 3, "microsoft": 4,
        "amazon": 5, "crypto": 6, "apple": 7, "chase": 8, "paypal": 9,
        "unknown": 0
    }
    brand_encoded = brand_map.get(kit.get("detected_brand", "unknown"), 0)
    
    # Token style mapping
    token_map = {"md5_rand": 1, "uniqid": 2, "random_bytes": 3, "sha1_time": 4, "bin2hex": 5, "none": 0}
    token_encoded = token_map.get(kit.get("token_style", "none"), 0)
    
    categorical_features = [exfil_encoded, brand_encoded, token_encoded]
    
    # List features - convert to useful signals
    chat_ids = kit.get("telegram_chat_ids", [])
    list_features = [
        len(chat_ids),  # Number of chat IDs
        int(len(chat_ids) > 0),  # Has any chat IDs (boolean)
    ]

    vector = bool_features + numerical_features + categorical_features + list_features
    
    return vector

def build_all_vectors(features_path: str) -> tuple:
    """
    Returns:
        vectors: list of normalized 55-dim lists
        labels:  list of family names (same order)
        hashes:  list of kit hashes (same order)
        col_min: min values per feature (for saving)
        col_max: max values per feature (for saving)
    """
    # Load features data
    with open(features_path) as f:
        features_data = json.load(f)
    
    raw_vectors = []
    labels = []
    hashes = []
    
    # Step 1: Build all raw vectors first (unnormalized)
    for kit_hash, kit_data in features_data.items():
        raw_vector = build_feature_vector(kit_data)
        family = kit_data.get("kit_family", "unknown")
        
        raw_vectors.append(raw_vector)
        labels.append(family)
        hashes.append(kit_hash)

    vectors_np = np.array(raw_vectors, dtype=np.float32)

    # Step 2: Compute col_min, col_max from the full batch
    col_min = vectors_np.min(axis=0)
    col_max = vectors_np.max(axis=0)
    
    # Step 3: Normalize each vector using those stats
    normalized_vectors = []
    for raw_vector in raw_vectors:
        normalized_vector = normalize_vector(raw_vector, col_min, col_max)
        normalized_vectors.append(normalized_vector.tolist())

    return normalized_vectors, labels, hashes, col_min.tolist(), col_max.tolist()


def build_normalized_feature_vector(kit: dict) -> list:
    """
    Build and normalize a single feature vector using saved normalization parameters.
    """
    # Build raw vector
    raw_vector = build_feature_vector(kit)
    
    # Load normalization parameters
    with open("normalization_stats.json") as f:
        stats = json.load(f)
    
    col_min = stats["col_min"]
    col_max = stats["col_max"]
    
    # Apply same normalization as training data
    normalized_vector = normalize_vector(raw_vector, col_min, col_max)
    
    return normalized_vector.tolist()


def validate_vectors():
    """Validate the vector building process."""
    try:
        vectors, labels, hashes, col_min, col_max = build_all_vectors("data_exploration/data/features.json")
    except FileNotFoundError:
        vectors, labels, hashes, col_min, col_max = build_all_vectors("features_checkpoint.json")
    
    print("── Vector Building Validation ──")
    print(f"Total kits processed: {len(vectors)}")
    print(f"Vector dimensions: {len(vectors[0])}")
    print(f"Sample families: {labels[:5]}")
    print(f"Sample hashes: {hashes[:3]}")
    print()


if __name__ == "__main__":
    validate_vectors()